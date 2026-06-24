# RAG System Architecture Evaluation and Insights

## Introduction

This document summarizes the experimental findings and engineering insights obtained while improving a Retrieval-Augmented Generation (RAG) PDF Question Answering System. Multiple architectural variants were tested involving changes in chunking strategy, document loader, query rewriting prompts, and reranking mechanisms.

The goal was to understand how each component impacts retrieval quality, ranking quality, answer accuracy, and latency.

---

# Experimental Configurations

The following architectures were evaluated:

1. Old Chunker + Old Loader
2. New Chunker + Old Loader
3. New Chunker + Old Loader + Improved Query Rewriting Prompt
4. New Chunker + New Loader + Improved Query Rewriting Prompt
5. New Chunker + New Loader + Improved Query Rewriting Prompt + BGE Cross-Encoder Reranker

---

# Evaluation Metrics Used

The system was evaluated using:

* Recall@k
* Precision@k
* Mean Reciprocal Rank (MRR)
* Accuracy
* P95 Latency

The evaluation dataset included:

* Baseline factual queries
* Numerical queries
* Chunk-boundary queries
* Paraphrased queries

---

# Major Findings

## 1. Sentence-Aware Chunking Improved Retrieval Quality

The transition from the old token-based chunker to the new sentence-aware chunker significantly improved retrieval quality.

### Observations

* Recall improved from 0.85 to 0.90.
* Retrieval became more semantically stable.
* Long-form and paraphrased queries showed noticeable improvement.
* Chunk-boundary failures reduced.

### Insight

Sentence-aware chunking preserves semantic continuity better than fixed token slicing. This helps the embedding model understand context more effectively and improves retrieval consistency.

---

# 2. Query Rewriting Prompt Simplification Improved Performance

The original rewriting prompt generated verbose and unnatural rewritten queries such as:

* “What is the birth date of Indian cricketer Virat Kohli?”

The improved prompt generated concise retrieval-friendly queries such as:

* “Virat Kohli birthdate”

### Observations

* Latency reduced significantly.
* Retrieval precision improved.
* MRR improved from 0.7167 to 0.7583.
* Accuracy improved from 0.50 to 0.65.

### Insight

Short, keyword-oriented rewritten queries work better for hybrid retrieval systems involving BM25 and dense vector search. Excessively verbose rewritten queries introduce unnecessary noise.

---

# 3. Loader Changes Produced Mixed Results

Replacing the original loader with the new loader produced inconsistent gains.

### Observations

* Recall remained unchanged at 0.90.
* MRR improved slightly.
* Accuracy decreased from 0.65 to 0.60.
* Latency increased in some cases.

### Insight

Loader improvements alone do not guarantee downstream QA improvement. Better text extraction quality must meaningfully change chunk semantics to improve retrieval and generation.

---

# 4. BGE Cross-Encoder Reranker Significantly Improved Ranking Quality

Introducing the BGE cross-encoder reranker produced the largest improvement in ranking quality.

### Observations

* MRR improved from 0.7833 to 0.8250.
* Precision improved from 0.53 to 0.55.
* Relevant chunks consistently appeared earlier in rankings.
* Many queries achieved MRR = 1.0.

### Insight

Cross-encoder rerankers are highly effective at semantic relevance estimation. They substantially improve chunk ordering, especially for:

* paraphrased queries,
* long-context retrieval,
* semantic similarity tasks.

This demonstrates that reranking is a critical component in high-quality RAG systems.

---

# 5. Retrieval Became Stronger Than Generation

An important system-level insight emerged after reranking improvements.

### Observations

* Recall remained high.
* MRR became very strong.
* Accuracy did not improve proportionally.

### Insight

The bottleneck shifted from retrieval to generation.

The system was successfully retrieving relevant evidence, but the generator still:

* refused valid answers,
* produced partial answers,
* failed numerical reasoning,
* or returned “I don’t know” despite sufficient evidence.

This demonstrates a common production RAG issue:
Better retrieval alone does not guarantee better final answers.

---

# 6. Evaluation Metric Limitations Became Visible

As retrieval quality improved, weaknesses in the evaluation methodology became more obvious.

### Observations

Several semantically correct answers were marked incorrect because:

* wording differed,
* answers were partially grounded,
* or the evaluation relied on exact string matching.

### Insight

Simple substring-based accuracy metrics are insufficient for advanced RAG evaluation.

Future improvements should include:

* semantic similarity scoring,
* LLM-as-a-judge evaluation,
* or frameworks such as RAGAS.

---

# 7. Latency Improvements Through Architectural Optimization

The system originally showed very high P95 latency values (~16.9s).

### Improvements

* Better chunking reduced retrieval overhead.
* Improved rewriting prompts reduced token generation latency.
* Optimized reranking pipelines reduced unnecessary computation.

### Final Result

P95 latency improved to approximately 9 seconds while simultaneously improving retrieval quality.

---

# Final Comparative Results

| Architecture                          | Recall | Precision | MRR   | Accuracy | P95 Latency |
| ------------------------------------- | ------ | --------- | ----- | -------- | ----------- |
| Old Chunker + Old Loader              | 0.85   | 0.57      | 0.74  | 0.55     | 16.9s       |
| New Chunker + Old Loader              | 0.90   | 0.51      | 0.71  | 0.50     | 9.3s        |
| New Chunker + Old Loader + New Prompt | 0.90   | 0.54      | 0.76  | 0.65     | 8.7s        |
| New Chunker + New Loader + New Prompt | 0.90   | 0.53      | 0.78  | 0.60     | 11.0s       |
| + BGE Reranker                        | 0.90   | 0.55      | 0.825 | 0.55     | 9.3s        |

---

# Key Engineering Learnings

## Retrieval and Generation Are Independent Bottlenecks

Improving retrieval quality does not automatically improve answer quality. RAG systems are multi-stage pipelines where bottlenecks shift dynamically.

---

## Reranking Is Extremely Important

Cross-encoder rerankers produced the largest ranking quality improvement across all experiments.

---

## Query Rewriting Matters More Than Expected

Prompt engineering for query rewriting had a surprisingly large effect on both latency and retrieval quality.

---

## Evaluation Methodology Must Evolve With System Quality

As the system becomes more advanced, exact-match accuracy metrics become increasingly inadequate.

---

# Recommended Final Architecture

The recommended architecture is:

* Sentence-aware chunking
* Improved document loader
* Strict keyword-oriented query rewriting
* BGE cross-encoder reranker
* Hybrid retrieval (BM25 + FAISS)

This architecture provides the best balance between:

* retrieval quality,
* ranking quality,
* semantic robustness,
* and production realism.

---

# Future Improvements

## High Priority

* Semantic evaluation metrics
* RAGAS integration
* LLM-as-a-judge evaluation
* Better generation prompting

## Medium Priority

* Dynamic top-k retrieval
* Confidence thresholding
* Query classification
* Adaptive reranking depth

## Low Priority

* Additional retrieval architecture changes

At this stage, generation quality and evaluation quality are larger bottlenecks than retrieval.

---

# Conclusion

These experiments demonstrate the evolution of the system from a basic RAG chatbot into a more production-oriented retrieval pipeline.

The project now incorporates:

* Hybrid retrieval,
* sentence-aware chunking,
* query rewriting,
* cross-encoder reranking,
* retrieval evaluation metrics,
* latency instrumentation,
* and architectural ablation studies.

The experiments also highlight a critical real-world lesson in RAG engineering:

“Improving retrieval quality is necessary, but not sufficient. End-to-end RAG performance depends on retrieval, reranking, generation, prompting, and evaluation working together as a complete system.”
