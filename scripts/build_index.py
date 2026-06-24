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
(text, page_metadata), load_time = timed_step("Loading PDF", load_pdf, pdf_path)

(chunks, stats), chunk_time = timed_step("Chunking text", chunk_text, text, doc_id)
print("Total chunks:", len(chunks))

vectors, embed_time = timed_step("Embedding chunks", embed_chunks, chunks)

faiss_index, faiss_time = timed_step("Building FAISS index", build_faiss_index, vectors)

os.makedirs("vectorstore", exist_ok=True)
_, save_time = timed_step("Saving FAISS index", save_faiss_index, faiss_index, index_path)
"""
faiss_index, load_time = timed_step("Loading the FAISS Index", load_faiss_index, index_path)
print("FAISS index size:", faiss_index.ntotal)

(bm25, tokenized_corpus), bm25_time = timed_step("Building BM25 index", build_bm25_index, chunks)

# ---------------- QUERY ----------------
actual_query = "How many centuries did Kohli score in 2018?"
print("\n" + "="*80)
print("Query:", actual_query)
print("="*80)

#Query Rewriting
rewritten_query, rewrite_time = timed_step("Rewriting Query", llm_client.rewrite_query, actual_query)
print("Rewritten Query:", rewritten_query)

#Embedding rewritten query
rewritten_query_vector, query_embed_time = timed_step("Embedding rewritten query", embed_chunks, [{"text": rewritten_query}])

# ---------------- HYBRID RETRIEVAL ----------------
rows, hybrid_time = timed_step("Hybrid retrieval", retrieve_hybrid,
    faiss_index, rewritten_query_vector, rewritten_query, 
    bm25, tokenized_corpus, chunks, top_k
)

df, norm_time = timed_step("Normalize scores", normalise_scores, rows)

retrieved_chunks, calc_time = timed_step("Compute hybrid final score + rank", calc_final_score, 
    df, top_k=top_k, alpha=0.6
)

reranked_chunks, rerank_time = timed_step("Reranking chunks using cross encoder", reranker, 
    rewritten_query, retrieved_chunks, actual_top_k=reranked_k_chunks
)

print("\n" + "="*80)
print("RERANKED CHUNKS (Top 5)")
print("="*80)
for i, chunk in enumerate(reranked_chunks, 1):
    page = chunk['chunk']['metadata'].get('page_number', 'N/A')
    score = chunk.get('rerank_score', 0.0)
    text_preview = chunk['chunk']['text'][:100].replace('\n', ' ')
    print(f"\n[{i}] Page {page} | Score: {score:.4f}")
    print(f"    {text_preview}...")

# ---------------- RAG PIPELINE ----------------
result, gen_time = timed_step("RAG Pipeline", run_rag_pipeline,
    question=actual_query,
    reranked_chunks=reranked_chunks,
    llm_client=llm_client
)

print("\n" + "="*80)
print("FINAL ANSWER")
print("="*80)
print(result["answer"])
print("\n" + "-"*80)
print(f"Confidence: {result['confidence']:.2%}")
print("-"*80)
print(f"  Mean Score:  {result['confidence_breakdown']['mean_score']:.4f}")
print(f"  Agreement:   {result['confidence_breakdown']['agreement']:.4f}")
print(f"  Dominance:   {result['confidence_breakdown']['dominance']:.4f}")
print(f"  Variance:    {result['confidence_breakdown']['variance']:.4f}")
print("="*80)
"""