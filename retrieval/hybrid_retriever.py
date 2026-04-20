from vectorstore.faiss_store import search_index
from retrieval.bm25_store import search_bm25
import numpy as np
import pandas as pd

def retrieve_hybrid(faiss_index, query_vector, query, bm25, tokenised_corpus, chunks, top_k):
    # FAISS retrieval
    faiss_scores, faiss_indices = search_index(faiss_index, query_vector, top_k)
    faiss_score_map = {
        int(idx): float(score)
        for idx, score in zip(faiss_indices[0], faiss_scores[0])
    }
    
    # BM25 retrieval
    bm25_chunks, bm25_scores = search_bm25(query, bm25, tokenised_corpus, chunks, top_k)
    bm25_score_map = {
        chunk["metadata"]["chunk_index"]: float(score)
        for chunk, score in zip(bm25_chunks, bm25_scores)
    }
    
    # Combine
    all_chunk_ids = set(faiss_score_map) | set(bm25_score_map)
    
    rows = []
    for cid in all_chunk_ids:
        rows.append({
            "chunk_id": cid,
            "faiss_scores": faiss_score_map.get(cid, 0.0),
            "bm25_scores": bm25_score_map.get(cid, 0.0),
            "chunk": chunks[cid]
        })
    
    return rows

def _safe_normalize(series: pd.Series):
    if series.max() == series.min():
        return np.ones(len(series))
    return (series - series.min()) / (series.max() - series.min())


def normalise_scores(rows):
    df = pd.DataFrame(rows)

    df["faiss_score_norm"] = _safe_normalize(df["faiss_scores"])
    df["bm25_score_norm"] = _safe_normalize(df["bm25_scores"])

    return df


def calc_final_score(df, top_k, alpha=0.6):
    df["final_score"] = (
        alpha * df["faiss_score_norm"]
        + (1 - alpha) * df["bm25_score_norm"]
    )

    df.sort_values(by="final_score", ascending=False, inplace=True)

    results = []
    for _, row in df.head(top_k).iterrows():
        results.append({
            "chunk": row["chunk"],
            "faiss_score": float(row["faiss_scores"]),
            "bm25_score": float(row["bm25_scores"]),
            "final_score": float(row["final_score"])
        })

    return results