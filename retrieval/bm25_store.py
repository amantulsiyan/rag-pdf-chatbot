from rank_bm25 import BM25Okapi

def build_bm25_index(chunks):
    tokenised_corpus=[]

    for chunk in chunks:
        text=chunk["text"]
        tokens=text.lower().split()
        tokens=[t for t in tokens if t.strip()]
        tokenised_corpus.append(tokens)

    bm25=BM25Okapi(tokenised_corpus)
    
    return bm25, tokenised_corpus
def search_bm25(query, bm25, tokenised_corpus, chunks, top_k=5):
    query_tokens=query.lower().split()
    query_tokens=[t for t in query_tokens if t.strip()]

    scores=bm25.get_scores(query_tokens)

    scored_chunks=list(enumerate(scores))
    scored_chunks.sort(key=lambda x:x[1], reverse=True)

    top_results=scored_chunks[:top_k]

    results=[]
    result_scores=[]

    for idx,score in top_results:
        results.append(chunks[idx])
        result_scores.append(score)

    return results,result_scores
