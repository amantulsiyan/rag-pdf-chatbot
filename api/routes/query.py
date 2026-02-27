from fastapi import APIRouter, HTTPException, Request
from embeddings.embedder import embed_chunks
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

    if request.app.state.chunks is None:
        raise HTTPException(status_code=400, detail="PDF not uploaded yet")

    query_vector, _ = embed_chunks([{"text": question_req.question}])

    rows = retrieve_faiss_and_bm25(
        index=request.app.state.faiss_index,
        query_vector=query_vector,
        query=question_req.question,
        bm25=request.app.state.bm25_index,
        tokenised_corpus=request.app.state.tokenised_corpus,
        chunks=request.app.state.chunks,
        top_k=5
    )

    df = normalise_scores(rows)

    retrieved_chunks = calc_final_score(df, alpha=0.6, top_k=5)

    result = run_rag_pipeline(
        question=question_req.question,
        retrieved_chunks=retrieved_chunks,
        llm_client=request.app.state.llm
    )

    return result