
import time

from loaders.loader import load_pdf
from chunking.chunker import chunk_text

from embeddings.embedder import embed_chunks
from embeddings.re_ranker import reranker

from vectorstore.faiss_store import build_faiss_index

from retrieval.bm25_store import build_bm25_index

from retrieval.hybrid_retriever import (
    retrieve_hybrid,
    normalise_scores,
    calc_final_score
)

from rag.pipeline import run_rag_pipeline

from llm.groq_llm import GroqLLM


# =========================================================
# EVALUATION DATASET
# =========================================================

eval_dataset = {

    # ================= BASELINE =================

    "baseline": [

        {
            "query": "What is Virat Kohli's full name?",
            "expected_answer": "Virat Kohli"
        },

        {
            "query": "When was Virat Kohli born?",
            "expected_answer": "5 November 1988"
        },

        {
            "query": "Which team does Virat Kohli play for?",
            "expected_answer": "India"
        },

        {
            "query": "What is Virat Kohli's batting style?",
            "expected_answer": "Right-handed"
        },

        {
            "query": "Who is Virat Kohli's spouse?",
            "expected_answer": "Anushka Sharma"
        }
    ],

    # ================= NUMERICAL =================

    "numerical": [

        {
            "query": "How many centuries did Kohli score in 2018?",
            "expected_answer": "11"
        },

        {
            "query": "What is Kohli's highest ODI score?",
            "expected_answer": "183"
        },

        {
            "query": "In which year did Kohli make his international debut?",
            "expected_answer": "2008"
        },

        {
            "query": "How many runs did Kohli score in 2016?",
            "expected_answer": "2595"
        },

        {
            "query": "What is Kohli's test batting average?",
            "expected_answer": "49"
        }
    ],

    # ================= CHUNK BOUNDARY =================

    "chunk_boundary": [

        {
            "query": "List all of Kohli's awards and achievements",
            "expected_answer": [
                "Arjuna Award",
                "Padma Shri",
                "Rajiv Gandhi Khel Ratna",
                "ICC"
            ]
        },

        {
            "query": "What is Kohli's complete career statistics?",
            "expected_answer": [
                "centuries",
                "runs",
                "matches",
                "average"
            ]
        },

        {
            "query": "Describe Kohli's entire international career",
            "expected_answer": [
                "debut",
                "captain",
                "World Cup",
                "centuries"
            ]
        },

        {
            "query": "What are all the records Kohli has broken?",
            "expected_answer": [
                "ODI",
                "records",
                "centuries"
            ]
        },

        {
            "query": "Tell me about Kohli's personal and professional life",
            "expected_answer": [
                "Anushka Sharma",
                "India",
                "captain",
                "IPL"
            ]
        }
    ],

    # ================= PARAPHRASE =================

    "paraphrase": [

        {
            "query": "What is Kohli's batting average?",
            "expected_answer": "average"
        },

        {
            "query": "What is Kohli's mean runs per innings?",
            "expected_answer": "average"
        },

        {
            "query": "How many runs does Kohli average per match?",
            "expected_answer": "average"
        },

        {
            "query": "What is Kohli's run rate per game?",
            "expected_answer": "average"
        },

        {
            "query": "Kohli's average scoring rate?",
            "expected_answer": "average"
        }
    ]
}


# =========================================================
# CONFIG
# =========================================================

pdf_path = r"C:\Users\USER\Desktop\Engineering\ML Projects\RAG PDF Chatbot\Hello_world.pdf"

doc_id = "doc_1"

top_k = 15

reranked_k_chunks = 5

llm_client = GroqLLM()


# =========================================================
# BUILD INDEX
# =========================================================

print("\n" + "=" * 80)
print("BUILDING INDEX")
print("=" * 80)

(text, page_metadata) = load_pdf(pdf_path)

chunks, stats = chunk_text(text, doc_id)

print(f"Total Chunks: {len(chunks)}")

vectors = embed_chunks(chunks)

faiss_index = build_faiss_index(vectors)

bm25, tokenized_corpus = build_bm25_index(chunks)

print("Index Built Successfully")


# =========================================================
# METRIC FUNCTIONS
# =========================================================

def check_relevance(text, expected_answer):

    # LIST TYPE ANSWERS

    if isinstance(expected_answer, list):

        matches = 0

        for ans in expected_answer:

            if ans.lower() in text.lower():
                matches += 1

        return matches > 0

    # STRING TYPE ANSWERS

    return expected_answer.lower() in text.lower()


def compute_recall_at_k(retrieved_chunks, expected_answer):

    for chunk in retrieved_chunks:

        chunk_text = chunk["chunk"]["text"]

        if check_relevance(chunk_text, expected_answer):
            return 1

    return 0


def compute_precision_at_k(retrieved_chunks, expected_answer):

    relevant = 0

    for chunk in retrieved_chunks:

        chunk_text = chunk["chunk"]["text"]

        if check_relevance(chunk_text, expected_answer):
            relevant += 1

    return relevant / len(retrieved_chunks)


def compute_mrr(retrieved_chunks, expected_answer):

    for idx, chunk in enumerate(retrieved_chunks):

        chunk_text = chunk["chunk"]["text"]

        if check_relevance(chunk_text, expected_answer):
            return 1 / (idx + 1)

    return 0


def compute_accuracy(generated_answer, expected_answer):

    # LIST TYPE ANSWERS

    if isinstance(expected_answer, list):

        matches = 0

        for ans in expected_answer:

            if ans.lower() in generated_answer.lower():
                matches += 1

        return matches > 0

    # STRING TYPE ANSWERS

    return expected_answer.lower() in generated_answer.lower()


def compute_p95(latencies):

    sorted_latencies = sorted(latencies)

    index = int(0.95 * len(sorted_latencies))

    return sorted_latencies[index]


# =========================================================
# METRIC STORAGE
# =========================================================

all_recalls = []

all_precisions = []

all_mrrs = []

all_accuracies = []

all_latencies = []

query_results = []


# =========================================================
# EVALUATION LOOP
# =========================================================

for category, samples in eval_dataset.items():

    print("\n" + "=" * 80)
    print(f"CATEGORY: {category.upper()}")
    print("=" * 80)

    for sample in samples:

        start_time = time.time()

        query = sample["query"]

        expected_answer = sample["expected_answer"]

        print(f"\nQUERY: {query}")

        # =========================================
        # QUERY REWRITE
        # =========================================

        rewritten_query = llm_client.rewrite_query(query)

        print(f"Rewritten Query: {rewritten_query}")

        # =========================================
        # EMBED QUERY
        # =========================================

        query_vector = embed_chunks([
            {"text": rewritten_query}
        ])

        # =========================================
        # HYBRID RETRIEVAL
        # =========================================

        rows = retrieve_hybrid(
            faiss_index,
            query_vector,
            rewritten_query,
            bm25,
            tokenized_corpus,
            chunks,
            top_k
        )

        df = normalise_scores(rows)

        retrieved_chunks = calc_final_score(
            df,
            top_k=top_k,
            alpha=0.6
        )

        # =========================================
        # RERANKING
        # =========================================

        reranked_chunks = reranker(
            rewritten_query,
            retrieved_chunks,
            actual_top_k=reranked_k_chunks
        )

        # =========================================
        # RETRIEVAL METRICS
        # =========================================

        recall = compute_recall_at_k(
            reranked_chunks,
            expected_answer
        )

        precision = compute_precision_at_k(
            reranked_chunks,
            expected_answer
        )

        mrr = compute_mrr(
            reranked_chunks,
            expected_answer
        )

        # =========================================
        # GENERATION
        # =========================================

        result = run_rag_pipeline(
            question=query,
            reranked_chunks=reranked_chunks,
            llm_client=llm_client
        )

        answer = result["answer"]

        # =========================================
        # ACCURACY
        # =========================================

        accuracy = compute_accuracy(
            answer,
            expected_answer
        )

        # =========================================
        # TOTAL LATENCY
        # =========================================

        total_latency = (time.time() - start_time) * 1000

        # =========================================
        # STORE METRICS
        # =========================================

        all_recalls.append(recall)

        all_precisions.append(precision)

        all_mrrs.append(mrr)

        all_accuracies.append(accuracy)

        all_latencies.append(total_latency)

        query_results.append({

            "category": category,

            "query": query,

            "recall": recall,

            "precision": precision,

            "mrr": mrr,

            "accuracy": accuracy,

            "latency_ms": total_latency
        })

        # =========================================
        # PRINT RESULTS
        # =========================================

        print(f"Recall@k: {recall:.4f}")

        print(f"Precision@k: {precision:.4f}")

        print(f"MRR: {mrr:.4f}")

        print(f"Accuracy: {accuracy}")

        print(f"Latency: {total_latency:.2f} ms")

        print(f"Generated Answer: {answer}")


# =========================================================
# FINAL RESULTS
# =========================================================

avg_recall = sum(all_recalls) / len(all_recalls)

avg_precision = sum(all_precisions) / len(all_precisions)

avg_mrr = sum(all_mrrs) / len(all_mrrs)

avg_accuracy = sum(all_accuracies) / len(all_accuracies)

p95_latency = compute_p95(all_latencies)

print("\n" + "=" * 80)
print("FINAL EVALUATION RESULTS")
print("=" * 80)

print(f"Average Recall@k: {avg_recall:.4f}")

print(f"Average Precision@k: {avg_precision:.4f}")

print(f"Average MRR: {avg_mrr:.4f}")

print(f"Average Accuracy: {avg_accuracy:.4f}")

print(f"P95 Latency: {p95_latency:.2f} ms")
