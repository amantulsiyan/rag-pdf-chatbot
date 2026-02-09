import tiktoken
def chunk_text(text,document_id,chunk_size=700,overlap=50,model="gpt-4o"):
    enc=tiktoken.encoding_for_model(model)
    tokens=enc.encode(text)
    chunks=[]
    i=0
    chunk_index=0
    length=len(tokens)
    if overlap>=chunk_size:
        raise ValueError("Overlap must be smaller than the chunk size.")
    while i <length:
        chunk_tokens=tokens[i:i+chunk_size]
        chunk_text=enc.decode(chunk_tokens)
        chunk={
            "text":chunk_text,
            "metadata":{
                "document_id":document_id,
                "chunk_id":f"{document_id}_{chunk_index}",
                "chunk_index":chunk_index,
                "token_length": len(chunk_tokens)
            }  
        }
        chunks.append(chunk)
        i+=chunk_size-overlap
        chunk_index+=1
    total_chunks=len(chunks)
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
