import faiss
import numpy as np

def build_faiss_index(vectors: np.ndarray):
    dim=vectors.shape[1]
    index=faiss.IndexFlatIP(dim)
    index.add(vectors)
    return index

def save_faiss_index(index, path: str):
    faiss.write_index(index,path)

def load_faiss_index(path: str):
    return faiss.read_index(path)

def search_index(index,query_vector:np.ndarray, top_k: int=5):
    return index.search(query_vector, top_k)

