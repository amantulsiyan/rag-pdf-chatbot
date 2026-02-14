from loaders.loader import load_pdf
from chunking.chunker import chunk_text
from embeddings.embedder import embed_chunks
from vectorstore.faiss_store import (
    build_faiss_index,
    save_faiss_index,
    load_faiss_index
)
from retrieval.bm25_store import build_bm25_index
from retrieval.hybrid_retriever import (
    retrieve_faiss_and_bm25,
    normalise_scores,
    calc_final_score
)
from rag.pipeline import run_rag_pipeline
from llm.groq_llm import GroqLLM
import os


# ---------------- CONFIG ----------------
pdf_path = r"C:\Users\USER\Desktop\Engineering\ML Projects\RAG PDF Chatbot\Hello_world.pdf"
doc_id = "doc_1"
index_path = "vectorstore/index.faiss"
top_k = 7


# ---------------- BUILD INDEX ----------------
print("Loading PDF...")
text = load_pdf(pdf_path)

print("Chunking text...")
chunks, stats = chunk_text(text, doc_id)
print("Total chunks:", len(chunks))

print("Embedding chunks...")
vectors, _ = embed_chunks(chunks)

print("Building FAISS index...")
faiss_index = build_faiss_index(vectors)

os.makedirs("vectorstore", exist_ok=True)
save_faiss_index(faiss_index, index_path)

faiss_index = load_faiss_index(index_path)
print("FAISS index size:", faiss_index.ntotal)

print("Building BM25 index...")
bm25, tokenized_corpus = build_bm25_index(chunks)

print("Index build complete.")
print("-" * 60)


# ---------------- QUERY ----------------
query = "In which season of the IPL, did Virat Kohli win the orange cap?"
print("Query:", query)

query_vector, _ = embed_chunks([{"text": query}])


# ---------------- HYBRID RETRIEVAL ----------------
# 1. Align FAISS + BM25
rows = retrieve_faiss_and_bm25(
    index=faiss_index,
    query_vector=query_vector,
    query=query,
    bm25=bm25,
    tokenised_corpus=tokenized_corpus,
    chunks=chunks,
    top_k=top_k
)

# 2. Normalize scores
df = normalise_scores(rows)

# 3. Compute hybrid final score + rank
retrieved_chunks = calc_final_score(
    df,
    alpha=0.6,
    top_k=top_k
)


# ---------------- RAG PIPELINE ----------------
result = run_rag_pipeline(
    question=query,
    retrieved_chunks=retrieved_chunks,
    llm_client=GroqLLM()
)

print("\nFinal Answer:")
print(result["answer"])
print("Confidence:", result["confidence"])