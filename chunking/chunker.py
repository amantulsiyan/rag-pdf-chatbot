import nltk
import tiktoken

nltk.download('punkt')

def chunk_text(
    text,
    document_id,
    chunk_size=250,
    overlap=30,
    model="gpt-4o"
):
    enc = tiktoken.encoding_for_model(model)

    def token_count(txt):
        return len(enc.encode(txt))

    # STEP 1: Split into sentences
    sentences = nltk.sent_tokenize(text)

    chunks = []
    current_chunk = []
    current_tokens = 0
    chunk_index = 0

    for sentence in sentences:

        sentence_tokens = token_count(sentence)

        # STEP 2: If adding sentence exceeds limit → finalize chunk
        if current_tokens + sentence_tokens > chunk_size:

            chunk_text = " ".join(current_chunk)

            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "document_id": document_id,
                    "chunk_id": f"{document_id}_{chunk_index}",
                    "chunk_index": chunk_index,
                    "token_length": token_count(chunk_text)
                }
            })

            # STEP 3: Sentence-level overlap
            overlap_sentences = []
            overlap_tokens = 0

            for s in reversed(current_chunk):

                t = token_count(s)

                if overlap_tokens + t > overlap:
                    break

                overlap_sentences.insert(0, s)
                overlap_tokens += t

            current_chunk = overlap_sentences
            current_tokens = overlap_tokens
            chunk_index += 1

        # STEP 4: Add current sentence
        current_chunk.append(sentence)
        current_tokens += sentence_tokens

    # STEP 5: Add final chunk
    if current_chunk:

        chunk_text = " ".join(current_chunk)

        chunks.append({
            "text": chunk_text,
            "metadata": {
                "document_id": document_id,
                "chunk_id": f"{document_id}_{chunk_index}",
                "chunk_index": chunk_index,
                "token_length": token_count(chunk_text)
            }
        })

    # STEP 6: Stats
    total_chunks = len(chunks)

    avg_chunk_length = (
        sum(chunk["metadata"]["token_length"] for chunk in chunks)
        / total_chunks
        if total_chunks > 0 else 0
    )

    stats = {
        "total_chunks": total_chunks,
        "avg_chunk_length": avg_chunk_length
    }

    return chunks, stats
