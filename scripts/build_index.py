from loaders.loader import load_pdf
from chunking.chunker import chunk_text
from embeddings.embedder import embed_chunks
from embeddings.re_ranker import reranker
from vectorstore.faiss_store import (
    build_faiss_index,
    save_faiss_index,
    load_faiss_index
)
from retrieval.bm25_store import build_bm25_index
from retrieval.hybrid_retriever import (
    retrieve_hybrid,
    normalise_scores,
    calc_final_score
)
from rag.latency import timed_step
from rag.pipeline import run_rag_pipeline
from llm.groq_llm import GroqLLM
import os


# ---------------- CONFIG ----------------
pdf_path = r"C:\Users\USER\Desktop\Engineering\ML Projects\RAG PDF Chatbot\Hello_world.pdf"
doc_id = "doc_1"
index_path = "vectorstore/index.faiss"
top_k = 15
reranked_k_chunks=5
llm_client=GroqLLM()

# ---------------- BUILD INDEX ----------------
text = timed_step("Loading PDF", load_pdf, pdf_path)

chunks, stats = timed_step("Chunking text", chunk_text, text, doc_id)
print("Total chunks:", len(chunks))

vectors = timed_step("Embedding chunks", embed_chunks, chunks)

faiss_index = timed_step("Building FAISS index", build_faiss_index, vectors)

os.makedirs("vectorstore", exist_ok=True)
timed_step("Making the vector store directory", save_faiss_index, faiss_index, index_path)

faiss_index = timed_step("Loading the FAISS Index", load_faiss_index, index_path)
print("FAISS index size:", faiss_index.ntotal)

bm25, tokenized_corpus = timed_step("Building BM25 index", build_bm25_index, chunks)

# ---------------- QUERY ----------------
actual_query = "How many centuries did Kohli score in 2018?"
print("Query:", actual_query)

#Query Rewriting
rewritten_query = timed_step("Rewriting Query", llm_client.rewrite_query, actual_query)
print("Rewritten Query is as follows:\n", rewritten_query)

#Embedding rewritten query
rewritten_query_vector = timed_step("Embedding rewritten query", embed_chunks, [{"text": rewritten_query}])

#Generate Multiple rewritten query vectors
multiple_rewritten_queries = timed_step("Multi Query Rewriting", llm_client.multi_query_rewriting, actual_query)
print("Multiple rewritten queries are as follows:\n", multiple_rewritten_queries)

# ---------------- HYBRID RETRIEVAL ----------------
rows = timed_step("Hybrid retrieval", retrieve_hybrid,
    faiss_index, rewritten_query_vector, rewritten_query, 
    bm25, tokenized_corpus, chunks, top_k
)

df = timed_step("Normalize scores", normalise_scores, rows)

retrieved_chunks = timed_step("Compute hybrid final score + rank", calc_final_score, 
    df, top_k=top_k, alpha=0.6
)

reranked_chunks = timed_step("Reranking chunks using cross encoder", reranker, 
    rewritten_query, retrieved_chunks, actual_top_k=reranked_k_chunks
)
print("\n=== RERANK SCORES ===")
for i, chunk in enumerate(reranked_chunks):
    print(f"Chunk {i+1}: {chunk.get('rerank_score', 0.0):.4f}")

# ---------------- RAG PIPELINE ----------------
from rag.pipeline import run_rag_pipeline

result = run_rag_pipeline(
    question=actual_query,
    reranked_chunks=reranked_chunks,
    llm_client=llm_client
)

print("\nFinal Answer:")
print(result["answer"])
print("Confidence:", result["confidence"])
