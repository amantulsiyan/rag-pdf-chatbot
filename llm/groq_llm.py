import os
from groq import Groq
from dotenv import load_dotenv
import json

load_dotenv(override=True)


class GroqLLM:
    def __init__(self, model_name="llama-3.3-70b-versatile"):
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
            temperature=0.0,  # good for RAG
            max_tokens=300
        )

        return response.choices[0].message.content.strip()
    
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
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.0,

            max_tokens=50
        )

        rewritten_query = response.choices[0].message.content.strip()

        return rewritten_query
