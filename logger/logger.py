
import os
import logging
import psycopg2
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def get_db_connection():
    db_password = os.getenv("DB_PASSWORD")

    if not db_password:
        raise RuntimeError("DB_PASSWORD is missing from .env")

    return psycopg2.connect(
        dbname="rag_db",
        user="postgres",
        password=db_password,
        host="localhost",
        port="5432",
    )


def init_logging_tables():
    """Create logging tables if they do not exist."""
    conn = get_db_connection()

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS rag_requests (
                        request_id UUID PRIMARY KEY,
                        user_id BIGINT NOT NULL
                            REFERENCES users(id) ON DELETE CASCADE,
                        original_query TEXT NOT NULL,
                        latency_ms DOUBLE PRECISION NOT NULL,
                        rewritten_query TEXT,
                        final_response TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );

                    CREATE INDEX IF NOT EXISTS idx_rag_requests_user_id
                        ON rag_requests(user_id);

                    CREATE INDEX IF NOT EXISTS idx_rag_requests_created_at
                        ON rag_requests(created_at);

                    CREATE TABLE IF NOT EXISTS rag_timings (
                        request_id UUID PRIMARY KEY
                            REFERENCES rag_requests(request_id)
                            ON DELETE CASCADE,
                        query_rewriting_ms DOUBLE PRECISION,
                        embedding_ms DOUBLE PRECISION,
                        hybrid_retrieval_ms DOUBLE PRECISION,
                        normalisation_ms DOUBLE PRECISION,
                        calculation_ms DOUBLE PRECISION,
                        reranking_ms DOUBLE PRECISION,
                        generation_ms DOUBLE PRECISION,
                        total_ms DOUBLE PRECISION
                    );

                    CREATE TABLE IF NOT EXISTS rag_scores (
                        id BIGSERIAL PRIMARY KEY,
                        request_id UUID NOT NULL
                            REFERENCES rag_requests(request_id)
                            ON DELETE CASCADE,
                        retrieval_stage VARCHAR(30) NOT NULL,
                        chunk_rank INTEGER NOT NULL,
                        faiss_score DOUBLE PRECISION,
                        bm25_score DOUBLE PRECISION,
                        hybrid_score DOUBLE PRECISION,
                        rerank_score DOUBLE PRECISION,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );

                    CREATE INDEX IF NOT EXISTS idx_rag_scores_request_id
                        ON rag_scores(request_id);

                    CREATE TABLE IF NOT EXISTS rag_retrievals (
                        id BIGSERIAL PRIMARY KEY,
                        request_id UUID NOT NULL
                            REFERENCES rag_requests(request_id)
                            ON DELETE CASCADE,
                        retrieval_stage VARCHAR(30) NOT NULL,
                        chunk_rank INTEGER NOT NULL,
                        chunk_text TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );

                    CREATE INDEX IF NOT EXISTS idx_rag_retrievals_request_id
                        ON rag_retrievals(request_id);
                """)

        logger.info("Logging tables initialized successfully.")

    finally:
        conn.close()


def log_query(
    request_id,
    user_id,
    original_query,
    latency_ms,
    rewritten_query,
    response,
):
    conn = get_db_connection()

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO rag_requests (
                        request_id, user_id, original_query,
                        latency_ms, rewritten_query, final_response
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(request_id),
                        int(user_id),
                        original_query,
                        latency_ms,
                        rewritten_query,
                        response,
                    ),
                )
    except Exception:
        logger.exception("Database error in log_query")
    finally:
        conn.close()


def log_timings(request_id, timings_dict):
    conn = get_db_connection()

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO rag_timings (
                        request_id, query_rewriting_ms, embedding_ms,
                        hybrid_retrieval_ms, normalisation_ms,
                        calculation_ms, reranking_ms, generation_ms,
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
                        timings_dict.get("total_ms"),
                    ),
                )
    except Exception:
        logger.exception("Database error in log_timings")
    finally:
        conn.close()


def log_scores(request_id, retrieved_chunks, reranked_chunks):
    conn = get_db_connection()

    try:
        with conn:
            with conn.cursor() as cursor:
                for rank, chunk in enumerate(retrieved_chunks[:8], start=1):
                    cursor.execute(
                        """
                        INSERT INTO rag_scores (
                            request_id, retrieval_stage, chunk_rank,
                            faiss_score, bm25_score, hybrid_score, rerank_score
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            str(request_id),
                            "initial",
                            rank,
                            float(chunk["faiss_score"]) if chunk.get("faiss_score") is not None else None,
                            float(chunk["bm25_score"]) if chunk.get("bm25_score") is not None else None,
                            float(chunk["final_score"]) if chunk.get("final_score") is not None else None,
                            None,
                        ),
                    )

                for rank, chunk in enumerate(reranked_chunks[:5], start=1):
                    cursor.execute(
                        """
                        INSERT INTO rag_scores (
                            request_id, retrieval_stage, chunk_rank,
                            faiss_score, bm25_score, hybrid_score, rerank_score
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            str(request_id),
                            "reranked",
                            rank,
                            float(chunk["faiss_score"]) if chunk.get("faiss_score") is not None else None,
                            float(chunk["bm25_score"]) if chunk.get("bm25_score") is not None else None,
                            float(chunk["final_score"]) if chunk.get("final_score") is not None else None,
                            float(chunk["rerank_score"]) if chunk.get("rerank_score") is not None else None,
                        ),
                    )
    except Exception:
        logger.exception("Database error in log_scores")
    finally:
        conn.close()


def log_retrievals(request_id, retrieved_chunks, reranked_chunks):
    conn = get_db_connection()

    try:
        with conn:
            with conn.cursor() as cursor:
                for stage, chunks, limit in (
                    ("hybrid_retrieval", retrieved_chunks, 8),
                    ("reranked", reranked_chunks, 5),
                ):
                    for rank, chunk in enumerate(chunks[:limit], start=1):
                        cursor.execute(
                            """
                            INSERT INTO rag_retrievals (
                                request_id, retrieval_stage,
                                chunk_rank, chunk_text
                            )
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                str(request_id),
                                stage,
                                rank,
                                chunk["chunk"]["text"],
                            ),
                        )
    except Exception:
        logger.exception("Database error in log_retrievals")
    finally:
        conn.close()


# Initialize the logging tables when this module is imported.
init_logging_tables()
