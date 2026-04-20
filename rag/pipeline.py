from rag.prompt import build_rag_prompt
from rag.confidence import compute_confidence


def build_context(retrieved_chunks):
    """
    Converts retrieved chunks into a single context string.
    """
    context_parts = []

    for i, item in enumerate(retrieved_chunks, start=1):
        chunk_text = item["chunk"]["text"]
        context_parts.append(f"Chunk {i}:\n{chunk_text}")

    return "\n\n".join(context_parts)


def run_rag_pipeline(question, reranked_chunks, llm_client):
    if not reranked_chunks:
        return {
            "answer": "I don't know based on the provided context.",
            "confidence": 0.0,
            "sources": [],
            "confidence_breakdown": {
                "mean_score": 0.0,
                "agreement": 0.0,
                "dominance": 0.0,
                "variance": 0.0
            }
        }

    # Extract final scores safely
    re_rank_scores = [
        c.get("rerank_score", 0.0)
        for c in reranked_chunks
        if c.get("rerank_score") is not None
    ]

    confidence, breakdown = compute_confidence(re_rank_scores)

    context = build_context(reranked_chunks)
    prompt = build_rag_prompt(context=context, question=question)

    answer = llm_client.generate(prompt)

    return {
        "answer": answer,
        "confidence": confidence,
        "confidence_breakdown": breakdown,
        "sources": [
            {
                "chunk_id": c["chunk"]["metadata"]["chunk_id"],
                "score": c.get("rerank_score", 0.0),
                "text": c["chunk"]["text"]
            }
            for c in reranked_chunks
        ]
    }
