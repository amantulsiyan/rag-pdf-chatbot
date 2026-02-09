def build_rag_prompt(context: str, question: str) -> str:
    """
    Builds a strict RAG prompt.
    """

    return f"""
You are a question-answering system.

Answer the question using ONLY the information provided in the context below.
Do NOT use any outside knowledge.
If the answer cannot be found in the context, say:
"I don't know based on the provided context."

Context:
{context}

Question:
{question}

Answer:
""".strip()