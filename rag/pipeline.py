from rag.prompt import build_rag_prompt


def build_context(retrieved_chunks):
    """
    Converts retrieved chunks into a single context string.
    """

    context_parts = []

    for i, item in enumerate(retrieved_chunks, start=1):
        chunk_text = item["chunk"]["text"]
        context_parts.append(f"Chunk {i}:\n{chunk_text}")

    context = "\n\n".join(context_parts)
    return context


def run_rag_pipeline(
    question: str,
    retrieved_chunks,
    llm_client
):
    """
    Runs the RAG pipeline:
    retrieval output -> context -> prompt -> LLM -> answer
    """

    # 1. Handle empty retrieval
    if not retrieved_chunks:
        return "No relevant information found in the documents."

    # 2. Build context
    context = build_context(retrieved_chunks)

    # 3. Build prompt
    prompt = build_rag_prompt(context, question)

    # 4. Call LLM
    answer = llm_client.generate(prompt)

    # 5. Handle refusal / empty answers
    if not answer or "i don't know" in answer.lower():
        return "I don't know based on the provided context."

    return answer
