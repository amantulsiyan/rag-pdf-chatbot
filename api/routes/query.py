from fastapi import APIRouter, HTTPException, Request
from embeddings.embedder import embed_chunks
from embeddings.re_ranker import reranker
from retrieval.hybrid_retriever import (
    retrieve_hybrid,
    normalise_scores,
    calc_final_score
)
from rag.pipeline import run_rag_pipeline
from api.models import AskResponse, QuestionRequest
from rag.latency import timed_step
from logger.logger import log_query, log_timings, log_scores, log_retrievals
import time
import uuid

router = APIRouter()

@router.post("/ask_query", response_model=AskResponse)
async def ask_question(request: Request, question_req: QuestionRequest):
    timings = {}
    id = uuid.uuid4()
    start_time = time.time()

    llm_client = request.app.state.llm

    if request.app.state.chunks is None:
        raise HTTPException(status_code=400, detail = "PDF not uploaded yet")
    
    """# TEMPORARY: Disable query rewriting for testing to save tokens
    rewritten_query = question_req.question
    timings["query_rewriting_ms"] = 0.0
    # TODO: Re-enable after testing"""
    rewritten_query, timings["query_rewriting_ms"] = timed_step("Query Rewriting", llm_client.rewrite_query, question_req.question)

    query_vector, timings["embedding_ms"] = timed_step("Embedding", embed_chunks, [{"text": rewritten_query}])

    rows, timings["hybrid_retrieval_ms"] = timed_step("Hybrid Retrieval", retrieve_hybrid, 
        faiss_index=request.app.state.faiss_index,
        query_vector=query_vector,
        query=rewritten_query,
        bm25=request.app.state.bm25_index,
        tokenised_corpus=request.app.state.tokenised_corpus,
        chunks=request.app.state.chunks,
        top_k=request.app.state.top_k
    )

    df, timings["normalisation_ms"] = timed_step("Normalisation", normalise_scores, rows)

    retrieved_chunks, timings["calculation_ms"] = timed_step("Calculation", calc_final_score, df, alpha=0.6, top_k=request.app.state.top_k)

    try:
        reranked_chunks, timings["reranking_ms"] = timed_step("Reranking", reranker, question_req.question, retrieved_chunks, actual_top_k=request.app.state.reranked_k_chunks)
    except Exception as e:
        print(f"Reranking failed: {e}, falling back to hybrid retrieval")
        reranked_chunks = retrieved_chunks[:request.app.state.reranked_k_chunks]
        timings["reranking_ms"] = 0.0

    result, timings["generation_ms"] = timed_step("Generation", run_rag_pipeline, 
        question=question_req.question,
        reranked_chunks = reranked_chunks,
        llm_client = llm_client
    )
    
    total_ms = (time.time()-start_time)*1000
    timings["total_ms"] = total_ms 
    result["latency_breakdown"] = timings
    log_query(str(id), "user_1", question_req.question, int(total_ms), rewritten_query, result["answer"])
    log_timings(str(id), timings)
    log_scores(str(id), retrieved_chunks, reranked_chunks)
    log_retrievals(str(id), retrieved_chunks, reranked_chunks)
    return result