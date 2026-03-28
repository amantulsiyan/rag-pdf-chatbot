from fastapi import APIRouter, HTTPException, Request
from embeddings.embedder import embed_chunks
from embeddings.re_ranker import reranker
from retrieval.hybrid_retriever import (
    retrieve_faiss_and_bm25,
    normalise_scores,
    calc_final_score
)
from rag.pipeline import run_rag_pipeline
from api.models import AskResponse, QuestionRequest

router = APIRouter()

@router.post("/ask_query", response_model=AskResponse)
async def ask_question(request: Request, question_req: QuestionRequest):

    llm_client=request.app.state.llm

    if request.app.state.chunks is None:
        raise HTTPException(status_code=400, detail="PDF not uploaded yet")
    
    rewritten_query = llm_client.rewrite_query(question_req.question)

    query_vector, _ = embed_chunks([{"text": rewritten_query}])

    rows = retrieve_faiss_and_bm25(
        index=request.app.state.faiss_index,
        query_vector=query_vector,
        query=rewritten_query,
        bm25=request.app.state.bm25_index,
        tokenised_corpus=request.app.state.tokenised_corpus,
        chunks=request.app.state.chunks,
        top_k=request.app.state.top_k
    )

    df = normalise_scores(rows)

    retrieved_chunks = calc_final_score(df, alpha=0.6, top_k=request.app.state.top_k)

    try:
        reranked_chunks = reranker(question_req.question, retrieved_chunks, actual_top_k=request.app.state.reranked_k_chunks)
    except Exception as e:
        print(f"Reranking failed: {e}, falling back to hybrid retrieval")
        reranked_chunks = retrieved_chunks[:request.app.state.reranked_k_chunks]

    result = run_rag_pipeline(
        question=question_req.question,
        reranked_chunks=reranked_chunks,
        llm_client=llm_client
    )

    return result