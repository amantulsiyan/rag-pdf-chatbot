# 📄 RAG PDF Question Answering System (Hybrid Retrieval + Reranking)

A **production-grade Retrieval-Augmented Generation (RAG)** system that answers questions from PDF documents using **query rewriting**, **hybrid retrieval (FAISS + BM25)**, **cross-encoder reranking**, **strict grounding**, and **retrieval-based confidence scoring**.

This project is built **from scratch** (no LangChain / LlamaIndex) to ensure full control, explainability, and interview defensibility. I am planning to introduce LangChain prompt templates in the next iteration.

---

## 🚀 Key Features

- 📑 **PDF ingestion & cleaning**
- ✂️ **Token-aware chunking with overlap**
- 🔄 **Query rewriting** for improved retrieval
- 🔎 **Hybrid retrieval**
  - Dense semantic search (FAISS)
  - Sparse lexical search (BM25)
- ⚖️ **Score normalization & hybrid ranking**
- 🎯 **Cross-encoder reranking** for precision
- 🧠 **LLM-agnostic generation layer** (tested with Groq)
- 📊 **Retrieval-based confidence scoring**
- 🛑 **Hallucination control** via strict prompting
- 🌐 **FastAPI backend** with REST endpoints
- 💻 **Web frontend** for interactive querying

---

## 🧠 Why Hybrid RAG + Reranking?

| Problem | Solution |
|------|--------|
| Dense embeddings miss exact keywords | BM25 handles lexical matches |
| Keyword search lacks semantics | FAISS handles semantic similarity |
| Ambiguous user queries | LLM-based query rewriting |
| Hybrid retrieval lacks precision | Cross-encoder reranking refines results |
| LLMs hallucinate confidently | Context-only prompting + confidence |
| Black-box frameworks | Transparent, modular architecture |

---

## 🏗️ Architecture Overview

```text
PDF
 ↓
Text Extraction (PyMuPDF)
 ↓
Chunking (TikToken, size=500, overlap=50)
 ↓
Embeddings (all-MiniLM-L6-v2)
 ↓
User Query → Query Rewriting (LLM)
 ↓
FAISS Index ─┐
             ├─ Hybrid Retriever (α=0.6) ─→ Top-15 Chunks
BM25 Index ──┘
 ↓
Cross-Encoder Reranking (ms-marco-MiniLM-L-6-v2) → Top-5 Chunks
 ↓
RAG Prompt Builder (Strict Context-Only)
 ↓
LLM Generation (Groq LLaMA-3.3-70B)
 ↓
Answer + Confidence Score (based on rerank scores)
```

**📂 Project Structure**
```text
rag-pdf-chatbot/
│
├── api/
│   ├── routes/
│   │   ├── query.py        # Query endpoint with reranking
│   │   └── upload.py       # PDF upload endpoint
│   ├── main.py             # FastAPI application
│   ├── dependencies.py     # App state initialization
│   └── models.py           # Request/response schemas
│
├── frontend/
│   ├── index.html          # Web interface
│   ├── script.js           # Frontend logic
│   └── styles.css          # UI styling
│
├── loaders/
│   └── loader.py           # PDF → raw text (PyMuPDF)
│
├── chunking/
│   └── chunker.py          # Text → overlapping chunks + metadata
│
├── embeddings/
│   ├── embedder.py         # Chunks → dense vectors (all-MiniLM-L6-v2)
│   └── re_ranker.py        # Cross-encoder reranking (ms-marco-MiniLM)
│
├── vectorstore/
│   └── faiss_store.py      # FAISS index build / load / search
│
├── retrieval/
│   ├── bm25_store.py       # BM25 index + search
│   └── hybrid_retriever.py # Alignment, normalization, hybrid scoring
│
├── rag/
│   ├── prompt.py           # Strict RAG prompt
│   ├── pipeline.py         # Retrieval → reranking → generation
│   └── confidence.py       # Rerank-based confidence scoring
│
├── llm/
│   └── groq_llm.py         # Groq LLaMA-3 + query rewriting
│
├── scripts/
│   └── build_index.py      # End-to-end runner (index + query)
│
├── requirements.txt
└── README.md
```
## 🔍 Retrieval Strategy

### 1. Query Rewriting

User queries are rewritten by the LLM to be more specific and search-friendly before retrieval.

### 2. FAISS (Dense Semantic Search)

Captures semantic similarity using `all-MiniLM-L6-v2` embeddings

Effective for paraphrased or abstract queries

### 3. BM25 (Sparse Lexical Search)

Captures exact keyword matches (years, names, entities)

Improves recall for factual queries

### 4. Hybrid Scoring

Scores are normalized and combined as:
```text
final_score = α · faiss_score_norm + (1 − α) · bm25_score_norm
```
Default: α = 0.6, retrieves top-15 chunks

### 5. Cross-Encoder Reranking

Hybrid results are reranked using `cross-encoder/ms-marco-MiniLM-L-6-v2`

Computes query-chunk relevance scores with sigmoid normalization

Selects top-5 most relevant chunks for generation

## 📊 Confidence Scoring

Confidence is not taken from the LLM.

It is computed using **reranking scores** from the cross-encoder:

    * Mean rerank score (strength)

    * Score variance (agreement)

    * Dominance gap (top vs second chunk)

Formula:
```text
confidence = 0.5 × mean_score + 0.3 × agreement + 0.2 × dominance
```

This design prioritizes honest uncertainty over fluent hallucinations.

**Example Output:**

```json
{
"answer": "Virat Kohli won the ICC Cricketer of the Year, ODI Player of the Year, and Test Player of the Year in 2018.",
"confidence": 0.65
}
```

If evidence is weak or distributed ambiguously:
```text
"I don't know based on the provided context."
```
## ⚙️ How to Run

### Option 1: Script Mode (Testing)

1. Install dependencies

    ```bash
    pip install -r requirements.txt
    ```

2. Set API key (Groq)

    ```powershell
    setx GROQ_API_KEY "your_api_key_here"
    ```

3. Run the pipeline

    ```bash
    python -m scripts.build_index
    ```

### Option 2: API Mode (Production)

1. Start FastAPI server

    ```bash
    uvicorn api.main:app --reload
    ```

2. Open frontend

    Navigate to `frontend/index.html` in your browser

3. Upload PDF and ask questions via the web interface

### API Endpoints

- `POST /upload_pdf` - Upload and index a PDF
- `POST /ask_query` - Ask questions about the uploaded PDF