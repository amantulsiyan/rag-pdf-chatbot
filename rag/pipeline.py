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


def run_rag_pipeline(question, retrieved_chunks, llm_client):
    if not retrieved_chunks:
        return {
            "answer": "I don't know based on the provided context.",
            "confidence": 0.0,
            "sources": []
        }

    # Extract final scores safely
    final_scores = [
        c.get("final_score", 0.0)
        for c in retrieved_chunks
        if c.get("final_score") is not None
    ]

    confidence = compute_confidence(final_scores)

    context = build_context(retrieved_chunks)
    prompt = build_rag_prompt(context=context, question=question)

    answer = llm_client.generate(prompt)

    return {
        "answer": answer,
        "confidence": confidence,
        "sources": [
            {
                "chunk_id": c["chunk"]["metadata"]["chunk_id"],
                "score": c.get("final_score", 0.0)
            }
            for c in retrieved_chunks
        ]
    }
