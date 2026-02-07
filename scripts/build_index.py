from loaders.loader import load_pdf
from chunking.chunker import chunk_text
from embeddings.embedder import embed_chunks
from vectorstore.faiss_store import (
    build_faiss_index,
    save_faiss_index,
    load_faiss_index
)
from retrieval.bm25_store import build_bm25_index
from retrieval.hybrid_retriever import retrieve_faiss_and_bm25
from rag.pipeline import run_rag_pipeline
from llm.dummy_llm import DummyLLM
import os


# ---------------- CONFIG ----------------
pdf_path = r"C:\Users\USER\Desktop\Engineering\ML Projects\RAG PDF Chatbot\Hello_world.pdf"
doc_id = "doc_1"
index_path = "vectorstore/index.faiss"
top_k = 5


# ---------------- BUILD INDEX ----------------
print("Loading PDF...")
text = load_pdf(pdf_path)

print("Chunking text...")
chunks, stats = chunk_text(text, doc_id)
print("Total chunks:", len(chunks))

print("Embedding chunks...")
vectors, _ = embed_chunks(chunks)

print("Building FAISS index...")
index = build_faiss_index(vectors)

os.makedirs("vectorstore", exist_ok=True)
save_faiss_index(index, index_path)

index = load_faiss_index(index_path)
print("FAISS index size:", index.ntotal)

print("Building BM25 index...")
bm25, tokenized_corpus = build_bm25_index(chunks)

print("Index build complete.")
print("-" * 60)


# ---------------- QUERY ----------------
query = "What awards has Virat Kohli won?"
print("Query:", query)

query_vector, _ = embed_chunks([{"text": query}])


# ---------------- HYBRID RETRIEVAL ----------------
aligned_results = retrieve_faiss_and_bm25(
    index=index,
    query_vector=query_vector,
    query=query,
    bm25=bm25,
    tokenised_corpus=tokenized_corpus,
    chunks=chunks,
    top_k=top_k
)

# Convert dict → list (simple)
retrieved_chunks = list(aligned_results.values())


# ---------------- RAG PIPELINE ----------------
answer = run_rag_pipeline(
    question=query,
    retrieved_chunks=retrieved_chunks,
    llm_client=DummyLLM()
)

print("\nFinal Answer:")
print(answer)
