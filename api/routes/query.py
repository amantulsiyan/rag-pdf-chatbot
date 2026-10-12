
import os
import time
import uuid

import psycopg2
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request, Depends

from api.dependencies import get_current_user
from api.models import AskResponse, QuestionRequest
from chunking.chunker import chunk_text
from loaders.loader import load_pdf
from embeddings.embedder import embed_chunks
from embeddings.re_ranker import reranker
from vectorstore.faiss_store import build_faiss_index
from retrieval.bm25_store import build_bm25_index
from retrieval.hybrid_retriever import (
    retrieve_hybrid,
    normalise_scores,
    calc_final_score,
)
from rag.pipeline import run_rag_pipeline
from rag.latency import timed_step
from logger.logger import (
    log_query,
    log_timings,
    log_scores,
    log_retrievals,
)


load_dotenv()
router = APIRouter()


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


def get_owned_document(document_id, user_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT storage_path, status
                FROM documents
                WHERE id = %s
                  AND owner_user_id = %s
                """,
                (str(document_id), int(user_id)),
            )
            return cursor.fetchone()
    finally:
        conn.close()


def get_document_indexes(request, document_id, storage_path, user_id):
    cache_key = str(document_id)
    cached = request.app.state.document_indexes.get(cache_key)

    if cached is not None:
        # Defense in depth: verify cached ownership too.
        if cached["owner_user_id"] != str(user_id):
            raise HTTPException(
                status_code=404,
                detail="Document not found",
            )
        return cached

    if not os.path.isfile(storage_path):
        raise HTTPException(
            status_code=500,
            detail="Stored PDF is missing",
        )

    text, page_metadata = load_pdf(storage_path)

    if not text or not text.strip():
        raise HTTPException(
            status_code=500,
            detail="Could not extract text from stored PDF",
        )

    chunks, _ = chunk_text(
        text,
        document_id=cache_key,
    )

    if not chunks:
        raise HTTPException(
            status_code=500,
            detail="Could not rebuild document chunks",
        )

    vectors = embed_chunks(chunks)
    faiss_index = build_faiss_index(vectors)
    bm25_index, tokenised_corpus = build_bm25_index(chunks)

    cached = {
        "owner_user_id": str(user_id),
        "chunks": chunks,
        "faiss_index": faiss_index,
        "bm25_index": bm25_index,
        "tokenised_corpus": tokenised_corpus,
    }

    request.app.state.document_indexes[cache_key] = cached
    return cached


@router.post("/ask_query", response_model=AskResponse)
async def ask_question(
    request: Request,
    question_req: QuestionRequest,
    current_user: dict = Depends(get_current_user),
):
    # Check ownership before accessing the PDF or its indexes.
    document = get_owned_document(
        question_req.document_id,
        current_user["id"],
    )

    if document is None:
        # Do not reveal whether another user's document exists.
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    storage_path, document_status = document

    if document_status != "ready":
        raise HTTPException(
            status_code=409,
            detail="Document is not ready for querying",
        )

    document_indexes = get_document_indexes(
        request,
        question_req.document_id,
        storage_path,
        current_user["id"],
    )

    timings = {}
    request_id = uuid.uuid4()
    start_time = time.time()
    llm_client = request.app.state.llm

    rewritten_query, timings["query_rewriting_ms"] = timed_step(
        "Query Rewriting",
        llm_client.rewrite_query,
        question_req.question,
    )

    query_vector, timings["embedding_ms"] = timed_step(
        "Embedding",
        embed_chunks,
        [{"text": rewritten_query}],
    )

    rows, timings["hybrid_retrieval_ms"] = timed_step(
        "Hybrid Retrieval",
        retrieve_hybrid,
        faiss_index=document_indexes["faiss_index"],
        query_vector=query_vector,
        query=rewritten_query,
        bm25=document_indexes["bm25_index"],
        tokenised_corpus=document_indexes["tokenised_corpus"],
        chunks=document_indexes["chunks"],
        top_k=request.app.state.top_k,
    )

    df, timings["normalisation_ms"] = timed_step(
        "Normalisation",
        normalise_scores,
        rows,
    )

    retrieved_chunks, timings["calculation_ms"] = timed_step(
        "Calculation",
        calc_final_score,
        df,
        alpha=0.6,
        top_k=request.app.state.top_k,
    )

    try:
        reranked_chunks, timings["reranking_ms"] = timed_step(
            "Reranking",
            reranker,
            question_req.question,
            retrieved_chunks,
            actual_top_k=request.app.state.reranked_k_chunks,
        )
    except Exception as exc:
        print(f"Reranking failed: {exc}; using hybrid results")
        reranked_chunks = retrieved_chunks[
            :request.app.state.reranked_k_chunks
        ]
        timings["reranking_ms"] = 0.0

    result, timings["generation_ms"] = timed_step(
        "Generation",
        run_rag_pipeline,
        question=question_req.question,
        reranked_chunks=reranked_chunks,
        llm_client=llm_client,
    )

    total_ms = (time.time() - start_time) * 1000
    timings["total_ms"] = total_ms
    result["latency_breakdown"] = timings

    log_query(
        str(request_id),
        str(current_user["id"]),
        question_req.question,
        int(total_ms),
        rewritten_query,
        result["answer"],
    )
    log_timings(str(request_id), timings)
    log_scores(str(request_id), retrieved_chunks, reranked_chunks)
    log_retrievals(str(request_id), retrieved_chunks, reranked_chunks)

    return result
