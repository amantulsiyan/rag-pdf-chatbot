from fastapi import FastAPI
from llm.groq_llm import GroqLLM

def initialize_app(app: FastAPI):   
    app.state.chunks = None
    app.state.faiss_index = None
    app.state.bm25_index = None
    app.state.tokenised_corpus = None
    app.state.llm = GroqLLM()