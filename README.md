# 📄 RAG PDF Question Answering System (Hybrid Retrieval)

A **production-grade Retrieval-Augmented Generation (RAG)** system that answers questions from PDF documents using **hybrid retrieval (FAISS + BM25)**, **strict grounding**, and **retrieval-based confidence scoring**.

This project is built **from scratch** (no LangChain / LlamaIndex) to ensure full control, explainability, and interview defensibility.

---

## 🚀 Key Features

- 📑 **PDF ingestion & cleaning**
- ✂️ **Token-aware chunking with overlap**
- 🔎 **Hybrid retrieval**
  - Dense semantic search (FAISS)
  - Sparse lexical search (BM25)
- ⚖️ **Score normalization & hybrid ranking**
- 🧠 **LLM-agnostic generation layer** (tested with Groq)
- 📊 **Retrieval-based confidence scoring**
- 🛑 **Hallucination control** via strict prompting

---

## 🧠 Why Hybrid RAG?

| Problem | Solution |
|------|--------|
| Dense embeddings miss exact keywords | BM25 handles lexical matches |
| Keyword search lacks semantics | FAISS handles semantic similarity |
| LLMs hallucinate confidently | Context-only prompting + confidence |
| Black-box frameworks | Transparent, modular architecture |

---

## 🏗️ Architecture Overview

```text
PDF
 ↓
Text Extraction
 ↓
Chunking (size + overlap)
 ↓
Embeddings
 ↓
FAISS Index ─┐
             ├─ Hybrid Retriever ─→ Final Ranked Chunks
BM25 Index ──┘
 ↓
RAG Prompt Builder
 ↓
LLM (Groq / OpenAI / Gemini*)
 ↓
Answer + Confidence Score
```

**📂 Project Structure**
```text
rag-pdf-chatbot/
│
├── loaders/
│   └── loader.py           # PDF → raw text
│
├── chunking/
│   └── chunker.py          # Text → overlapping chunks + metadata
│
├── embeddings/
│   └── embedder.py         # Chunks → dense vectors
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
│   ├── pipeline.py         # Retrieval → generation orchestration
│   └── confidence.py       # Retrieval-based confidence scoring
│
├── llm/
│   └── groq_llm.py         # Groq LLaMA-3 integration (LLM-agnostic)
│
├── scripts/
│   └── build_index.py      # End-to-end runner (index + query)
│
├── requirements.txt
└── README.md
```
## 🔍 Retrieval Strategy

1. FAISS (Dense Semantic Search)

Captures semantic similarity

Effective for paraphrased or abstract queries

2. BM25 (Sparse Lexical Search)

Captures exact keyword matches (years, names, entities)

Improves recall for factual queries

3. Hybrid Scoring

Scores are normalized and combined as:
```text
final_score = α · faiss_score_norm + (1 − α) · bm25_score_norm
```
This ensures neither retriever dominates unfairly.

## 📊 Confidence Scoring

Confidence is not taken from the LLM.

It is computed using retrieval signals:

    * Mean hybrid score (strength)

    * Score variance (agreement)

    * Dominance gap (top vs second chunk)

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
1. Install dependencies

    ```bash
    pip install -r requirements.txt
    ```
2. Set API key (Groq example)

    ```powershell
    setx GROQ_API_KEY "your_api_key_here"
    ```
3. Run the pipeline

    ```bash
    python -m scripts.build_index
    ```