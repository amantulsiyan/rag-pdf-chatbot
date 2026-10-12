
import os
import uuid
from uuid import UUID
import shutil
import logging
import psycopg2
from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    File,
    UploadFile,
    HTTPException,
    Request,
    Depends,
)
from api.dependencies import get_current_user
from chunking.chunker import chunk_text
from loaders.loader import load_pdf
from embeddings.embedder import embed_chunks
from vectorstore.faiss_store import build_faiss_index
from retrieval.bm25_store import build_bm25_index


load_dotenv()

router = APIRouter()
upload_folder = "temp_uploads"
os.makedirs(upload_folder, exist_ok=True)
logger = logging.getLogger(__name__)

def get_db_connection():
    db_password = os.getenv("DB_PASSWORD")
    if not db_password:
        raise RuntimeError("DB_PASSWORD is missing from .env")

    return psycopg2.connect(
        dbname="rag_db",
        user="postgres",
        password=db_password,
        host="localhost",
        port="5432",
    )


@router.post("/upload_pdf", status_code=201)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files allowed",
        )

    document_id = uuid.uuid4()
    safe_filename = f"{document_id}.pdf"
    file_path = os.path.join(upload_folder, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        text, page_metadata = load_pdf(file_path)

        if not text or not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No extractable text found in PDF",
            )

        chunks, _ = chunk_text(
            text,
            document_id=str(document_id),
        )

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No chunks could be generated from PDF",
            )

        vectors = embed_chunks(chunks)
        faiss_index = build_faiss_index(vectors)
        bm25_index, tokenised_corpus = build_bm25_index(chunks)

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO documents (
                        id,
                        owner_user_id,
                        original_filename,
                        storage_path,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        str(document_id),
                        int(current_user["id"]),
                        file.filename,
                        file_path,
                        "ready",
                    ),
                )
            conn.commit()
        finally:
            conn.close()

        # Cache the indexes separately for this document.
        request.app.state.document_indexes[str(document_id)] = {
            "owner_user_id": str(current_user["id"]),
            "chunks": chunks,
            "faiss_index": faiss_index,
            "bm25_index": bm25_index,
            "tokenised_corpus": tokenised_corpus,
        }

        return {
            "message": "PDF Indexed Successfully",
            "document_id": str(document_id),
            "total_chunks": len(chunks),
        }

    except HTTPException:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

    except Exception as exc:
        logger.exception("PDF upload/indexing failed")

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail="PDF processing or indexing failed. Check the server terminal.",
        ) from exc

    finally:
        await file.close()

@router.get('/documents')
def list_documents(current_user : dict = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, original_filename,status, created_at
                FROM documents
                WHERE owner_user_id = %s
                ORDER BY created_at DESC
                """,
                (int(current_user["id"]),),
            )

            documents = cursor.fetchall()

        return{
            "documents":[
            {
                "document_id":str(doc[0]),
                "filename":doc[1],
                "status":doc[2],
                "created_at":doc[3],
            }
            for doc in documents
            ],
            "total":len(documents),
        }
    finally:
        conn.close()


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: UUID,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    conn = get_db_connection()

    try:
        with conn:
            with conn.cursor() as cursor:
                # Verify ownership and get the stored file path.
                cursor.execute(
                    """
                    SELECT storage_path
                    FROM documents
                    WHERE id = %s
                      AND owner_user_id = %s
                    """,
                    (str(document_id), int(current_user["id"])),
                )

                document = cursor.fetchone()

                if document is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Document not found",
                    )

                storage_path = document[0]

                # Delete the database record.
                cursor.execute(
                    """
                    DELETE FROM documents
                    WHERE id = %s
                      AND owner_user_id = %s
                    """,
                    (str(document_id), int(current_user["id"])),
                )

        # The database transaction has committed here.

    finally:
        conn.close()

    # Remove the cached retrieval indexes for this document.
    request.app.state.document_indexes.pop(str(document_id), None)

    # Remove the stored PDF.
    # Only delete files within the application's upload directory.
    upload_root = os.path.realpath(upload_folder)
    resolved_path = os.path.realpath(storage_path)

    if (
        os.path.commonpath([upload_root, resolved_path]) == upload_root
        and os.path.isfile(resolved_path)
    ):
        try:
            os.remove(resolved_path)
        except OSError:
            # The database deletion has already committed.
            # Log this for cleanup rather than reporting deletion as failed.
            import logging
            logging.getLogger(__name__).exception(
                "Document deleted from DB, but PDF cleanup failed: %s",
                resolved_path,
            )

    return {
        "message": "Document deleted successfully",
        "filename": document[1],
        "document_id": str(document_id),
    }
