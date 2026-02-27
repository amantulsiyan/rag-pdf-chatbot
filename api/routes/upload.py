from fastapi import APIRouter, File, UploadFile, HTTPException, Request
import shutil
import os
from chunking.chunker import chunk_text
from loaders.loader import load_pdf
from embeddings.embedder import embed_chunks
from vectorstore.faiss_store import build_faiss_index
from retrieval.bm25_store import build_bm25_index

router = APIRouter()

upload_folder = "temp_uploads"
os.makedirs(upload_folder, exist_ok=True)

@router.post("/upload_pdf")
async def upload_file(request: Request, file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    file_path = os.path.join(upload_folder, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = load_pdf(file_path)

    doc_id = "uploaded_doc"
    chunks, _ = chunk_text(text, document_id=doc_id)

    vectors, _ = embed_chunks(chunks)

    faiss_index = build_faiss_index(vectors)
    bm25_index, tokenised_corpus = build_bm25_index(chunks)

    request.app.state.chunks = chunks
    request.app.state.faiss_index = faiss_index
    request.app.state.bm25_index = bm25_index
    request.app.state.tokenised_corpus = tokenised_corpus

    return {
        "message": "PDF Indexed Successfully",
        "total_chunks": len(chunks)
    }