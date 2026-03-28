from sentence_transformers import CrossEncoder
import numpy as np
_model=None
def _get_model():
    global _model
    if _model is None:
        _model=CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _model
def reranker(query, hits, actual_top_k):
    model=_get_model()
    sentence_pairs = [(query, hit["chunk"]["text"]) for hit in hits]
    similarity_scores = model.predict(sentence_pairs, batch_size=16)
    similarity_scores = 1 / (1 + np.exp(-similarity_scores))
    for hit, score in zip(hits, similarity_scores):
        hit["rerank_score"] = score
    sorted_chunks = sorted(hits, key=lambda x: x["rerank_score"], reverse=True)
    top_k_chunks=sorted_chunks[:actual_top_k]
    return top_k_chunks