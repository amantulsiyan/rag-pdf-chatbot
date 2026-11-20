import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv(override=True)


class GroqLLM:
    """Synchronous Groq client.

    Calls are intentionally kept synchronous because the /ask_query route
    runs the complete blocking RAG pipeline in FastAPI's worker threadpool.
    """

    def __init__(self, model_name="openai/gpt-oss-120b"):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in environment variables")

        self.client = Groq(api_key=api_key)
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=800,
        )

        choice = response.choices[0]
        completion_tokens = getattr(response.usage, "completion_tokens", None)

        print("Generation finish reason:", choice.finish_reason)
        print("Completion tokens:", completion_tokens)

        content = choice.message.content
        return content.strip() if content else ""

    def rewrite_query(self, query: str) -> str:
        prompt = f"""
You are a query rewriting system for RAG retrieval.

Rewrite the user query for semantic document retrieval.

Rules:
- Return ONLY the rewritten query
- Do NOT explain anything
- Do NOT add notes
- Do NOT add bullet points
- Do NOT add quotation marks
- Keep it concise
- Preserve the original meaning

User Query:
{query}
"""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=50,
        )

        content = response.choices[0].message.content
        return content.strip() if content else query
