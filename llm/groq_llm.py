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
        prompt=f"""Rewrite the following query to be more clear and specific for document search:
        Original query:{query}
        Rewritten Query: """
        response=self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role":"user",
                 "content":prompt
                }
            ],
            temperature=0.3,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    
    def multi_query_rewriting(self,query: str) -> list[str]:
        prompt=f"""You are an AI assistant specialized in query expansion for hybrid retrieval systems (FAISS + BM25).

Generate exactly 3 diverse search queries from the user's question. Each query should:
- Target different aspects or perspectives of the topic
- Use varied vocabulary and synonyms (avoid word repetition)
- Be concise and keyword-rich (5-12 words)
- Optimize for both semantic similarity and lexical matching

Rules:
- NO simple rephrasings
- NO full sentences
- NO explanations

Output ONLY a valid JSON array:
["query1", "query2", "query3"]

User Query: {query}

JSON Output:
        """
        response=self.client.chat.completions.create( 
            model=self.model_name,
            messages=[
                    {
                    "role":"user",
                    "content":prompt
                    }
                    ],
            temperature=0.7,
            max_tokens=120
        )
        result = response.choices[0].message.content.strip()
        try:
            queries = json.loads(result)
            if isinstance(queries, list) and len(queries) >= 3:
                return queries[:3]  # Ensure exactly 3
            return [query]
        except json.JSONDecodeError:
            return [query]