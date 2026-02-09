from rank_bm25 import BM25Okapi


def build_bm25_index(chunks):
    tokenised_corpus = []

    for chunk in chunks:
        tokens = chunk["text"].lower().split()
        tokenised_corpus.append([t for t in tokens if t.strip()])

    bm25 = BM25Okapi(tokenised_corpus)
    return bm25, tokenised_corpus


def search_bm25(query, bm25, tokenised_corpus, chunks, top_k):
    query_tokens = [t for t in query.lower().split() if t.strip()]
    scores = bm25.get_scores(query_tokens)

    ranked = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True
    )[:top_k]

    results, result_scores = [], []
    for idx, score in ranked:
        results.append(chunks[idx])
        result_scores.append(score)

    return results, result_scores
