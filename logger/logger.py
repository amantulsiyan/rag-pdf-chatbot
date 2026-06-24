import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

db_password = os.getenv("DB_PASSWORD")

conn = psycopg2.connect(
    dbname="rag_db",
    user="postgres",
    password=db_password,
    host="localhost",
    port="5432"
)


def log_query(
    request_id,
    user_id,
    original_query,
    latency_ms,
    rewritten_query,
    response
):
    cursor = None

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO rag_requests(
                request_id,
                user_id,
                original_query,
                latency_ms,
                rewritten_query,
                final_response
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                str(request_id),
                user_id,
                original_query,
                latency_ms,
                rewritten_query,
                response
            )
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Database Error in log_query: {e}")

    finally:
        if cursor:
            cursor.close()


def log_timings(request_id, timings_dict):
    cursor = None

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO rag_timings(
                request_id,
                query_rewriting_ms,
                embedding_ms,
                hybrid_retrieval_ms,
                normalisation_ms,
                calculation_ms,
                reranking_ms,
                generation_ms,
                total_ms
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(request_id),
                timings_dict.get("query_rewriting_ms"),
                timings_dict.get("embedding_ms"),
                timings_dict.get("hybrid_retrieval_ms"),
                timings_dict.get("normalisation_ms"),
                timings_dict.get("calculation_ms"),
                timings_dict.get("reranking_ms"),
                timings_dict.get("generation_ms"),
                timings_dict.get("total_ms")
            )
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Database Error in log_timings: {e}")

    finally:
        if cursor:
            cursor.close()


def log_scores(request_id, retrieved_chunks, reranked_chunks):
    cursor = None

    try:
        cursor = conn.cursor()

        for rank, chunk in enumerate(retrieved_chunks[:8], start=1):

            cursor.execute(
                """
                INSERT INTO rag_scores(
                    request_id,
                    retrieval_stage,
                    chunk_rank,
                    faiss_score,
                    bm25_score,
                    hybrid_score,
                    rerank_score
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(request_id),
                    "initial",
                    rank,
                    float(chunk.get("faiss_score")),
                    float(chunk.get("bm25_score")),
                    float(chunk.get("final_score")),
                    None
                )
            )

        # Reranked scores
        for rank, chunk in enumerate(reranked_chunks[:5], start=1):

            cursor.execute(
                """
                INSERT INTO rag_scores(
                    request_id,
                    retrieval_stage,
                    chunk_rank,
                    faiss_score,
                    bm25_score,
                    hybrid_score,
                    rerank_score
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(request_id),
                    "reranked",
                    rank,
                    float(chunk.get("faiss_score")),
                    float(chunk.get("bm25_score")),
                    float(chunk.get("final_score")),
                    float(chunk.get("rerank_score"))
                )
            )

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Database Error in log_scores: {e}")

    finally:
        if cursor:
            cursor.close()

def log_retrievals(request_id, retrieved_chunks, reranked_chunks):
    cursor = None
    try:
        cursor = conn.cursor()
        #hybrid retrieval
        for rank, chunk in enumerate(retrieved_chunks[:8], start=1):
            cursor.execute(
                """
                INSERT INTO rag_retrievals(
                request_id, 
                retrieval_stage,
                chunk_rank,
                chunk_text
                )
                VALUES(%s,%s,%s,%s)
                """,
                (
                    str(request_id),
                    "hybrid_retrieval",
                    rank, 
                    chunk['chunk']['text']
                )
            )
        #reranked retrievals
        for rank, chunk in enumerate(reranked_chunks[:5], start=1):
            cursor.execute(
                """
                INSERT INTO rag_retrievals(
                request_id, 
                retrieval_stage,
                chunk_rank,
                chunk_text
                )
                VALUES(%s,%s,%s,%s)
                """,
                (
                    str(request_id),
                    "reranked",
                    rank, 
                    chunk['chunk']['text']
                )
            )
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Database Error in log_retrievals: {e}")

    finally:
        if cursor:
            cursor.close()