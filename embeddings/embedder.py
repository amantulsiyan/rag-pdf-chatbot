import time
import numpy as np
from sentence_transformers import SentenceTransformer
_model=None
def _get_model():
    global _model
    if _model is None:
        _model=SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model

def embed_chunks(chunks):
    texts=[chunk["text"] for chunk in chunks]
    model=_get_model()
    start_time = time.time()
    vectors = model.encode(texts, normalize_embeddings=True)
    end_time = time.time()
    return np.array(vectors, dtype="float32"),end_time-start_time
