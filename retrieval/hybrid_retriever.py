from vectorstore.faiss_store import search_index
from retrieval.bm25_store import search_bm25
import numpy as np
import pandas as pd
def retrieve_faiss_and_bm25(index, query_vector, query, bm25, tokenised_corpus, chunks, top_k=top_k):
    faiss_scores,faiss_indices=search_index(index, query_vector, top_k=top_k)
    faiss_scores=faiss_scores[0]
    faiss_indices=faiss_indices[0]
    faiss_score_map={}
    for i in range (len(faiss_indices)):
        faiss_score_map[faiss_indices[i]]=float(faiss_scores[i])
        
    bm25_chunks, bm25_scores=search_bm25(query, bm25, tokenised_corpus, chunks, top_k=top_k)
    bm25_score_map={}
    for chunk,score in zip(bm25_chunks,bm25_scores):
        chunk_id=chunk['metadata']['chunk_id']
        bm25_score_map[chunk_id]=float(score)

    all_chunk_ids=set(faiss_score_map.keys())|set(bm25_score_map.keys())
    aligned_results={}
    for chunk_id in all_chunk_ids:
        aligned_results[chunk_id]={
            "chunk":chunks[chunk_id],
            "faiss_score":faiss_score_map.get(chunk_id,0.0),
            "bm25_score":bm25_score_map.get(chunk_id,0.0)
        }
    rows=[]
    for chunk_id,data in aligned_results.items():
        rows.append({
            "chunk_id":chunk_id,
            "faiss_score":data["faiss_score"],
            "bm25_score":data["bm25_score"],
            "chunk":data["chunk"]
        })
    return rows
def normalise_scores(rows):
    df=pd.DataFrame(rows)
    df["faiss_score_norm"]=(df["faiss_score"]-df["faiss_score"].min())/(df["faiss_score"].max()-df["faiss_score"].min())
    df["bm25_score_norm"]=(df["bm25_score"]-df["bm25_score"].min())/(df["bm25_score"].max()-df["bm25_score"].min())
    return df
def calc_final_score(df,alpha,top_k=top_k):
    df["final_score"]=df["faiss_score_norm"]*alpha +((1-alpha)*df["bm25_score_norm"])
    df.sort_values(by="final_score",inplace=True,ascending=False)
    results = []

    for _, row in df.head(top_k).iterrows():
        results.append({
            "chunk": row["chunk"],
            "faiss_score": float(row["faiss_score"]),
            "bm25_score": float(row["bm25_score"]),
            "final_score": float(row["final_score"])
        })

    return results