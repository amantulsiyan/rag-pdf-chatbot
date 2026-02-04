from loaders.loader import load_pdf
from chunking.chunker import chunk_text
from embeddings.embedder import embed_chunks
from vectorstore.faiss_store import (
    build_faiss_index,
    save_faiss_index,
    search_index,
    load_faiss_index    
)
from retrieval.bm25_store import build_bm25_index, search_bm25
import os
import numpy as np 

pdf_path=r"C:\Users\USER\Desktop\Engineering\ML Projects\RAG PDF Chatbot\Hello_world.pdf"
doc_id="doc_1"
index_path="vectorstore\index.faiss"
top_k=5

print("Building RAG Started")
#Load Text
print("Loading Text:\n")
text= load_pdf(pdf_path)

#Chunk Text
print("Chunking Text:\n")
chunks,stats=chunk_text(text, doc_id)

print("Chunking Stats: ", stats)
print("Chunks: ",chunks)
print("Total chunk size: ",len(chunks))

#Embed Chunks
print("Embedding Chunks...")
vectors,embedding_time=embed_chunks(chunks)
print("Embedding Time: ",embedding_time)
print("Vector shape: ",vectors.shape)

#Build FAISS Index
print("Building FAISS Index...")
index=build_faiss_index(vectors)

print("FAISS Index size",index.ntotal)

#Save Index
os.makedirs('vectorstore',exist_ok=True)
save_faiss_index(index, index_path)
print("FAISS saved to:",index_path)

#Load Index
index=load_faiss_index(index_path)
print("FAISS Index loaded. Size:",index.ntotal)

#Manual Query Test
query = "What awards has Virat Kohli won?"
print("\nQuery:", query)

query_chunks = [{"text": query}]
query_vector, _ = embed_chunks(query_chunks)

scores, indices = search_index(index, query_vector, top_k=top_k)

print("\nTop-k results:\n")

for rank, (idx, score) in enumerate(zip(indices[0], scores[0]), start=1):
    print(f"Rank {rank}")
    print("Score:", round(float(score), 4))
    print("Chunk ID:", chunks[idx]["metadata"]["chunk_id"])
    print("Text:", chunks[idx]["text"], "...")
    print("-" * 50)

bm25, corpus = build_bm25_index(chunks)

results, scores = search_bm25(
    "Virat Kohli ICC awards 2018",
    bm25,
    corpus,
    chunks,
    top_k=5
)

for i, (chunk, score) in enumerate(zip(results, scores), 1):
    print(i, round(score, 3), chunk["text"])
    print("-"*50)