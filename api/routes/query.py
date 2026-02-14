from fastapi import APIRouter, HTTPException
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
async def ask_question(request: QuestionRequest):

    if router.app.state.chunks is None:
        raise HTTPException(status_code=400, detail="PDF not uploaded yet")

    query_vector, _ = embed_chunks([{"text": request.question}])

    rows = retrieve_faiss_and_bm25(
        index=router.app.state.faiss_index,
        query_vector=query_vector,
        query=request.question,
        bm25=router.app.state.bm25_index,
        tokenised_corpus=router.app.state.tokenised_corpus,
        chunks=router.app.state.chunks,
        top_k=5
    )

    df = normalise_scores(rows)

    retrieved_chunks = calc_final_score(df, alpha=0.6, top_k=5)

    result = run_rag_pipeline(
        question=request.question,
        retrieved_chunks=retrieved_chunks,
        llm_client=router.app.state.llm
    )

    return result