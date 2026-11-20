"""Baseline load test for the RAG PDF Chatbot.

Each Locust user represents one logical client session. By default, users
periodically call /health. Set TEST_AUTH_TOKEN to exercise authenticated
endpoints and TEST_DOCUMENT_ID to include occasional RAG queries.

This is a session/API baseline, not proof of 25,000 simultaneous LLM generations.
"""

import json
import os
import random

from locust import HttpUser, between, task

AUTH_TOKEN = os.getenv("TEST_AUTH_TOKEN", "").strip()
DOCUMENT_ID = os.getenv("TEST_DOCUMENT_ID", "").strip()
RUN_RAG_QUERIES = os.getenv("RUN_RAG_QUERIES", "false").lower() == "true"
QUESTION = os.getenv(
    "TEST_QUESTION",
    "What are the main points discussed in this document?",
)


class RAGSessionUser(HttpUser):
    # Represents an interactive user who returns periodically.
    wait_time = between(10, 30)

    def on_start(self):
        self.headers = {}
        if AUTH_TOKEN:
            self.headers["Authorization"] = f"Bearer {AUTH_TOKEN}"

    @task(8)
    def health_check(self):
        with self.client.get("/health", name="GET /health", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"health returned {r.status_code}")
            else:
                r.success()

    @task(3)
    def current_user(self):
        if not AUTH_TOKEN:
            return
        with self.client.get("/me", headers=self.headers, name="GET /me", catch_response=True) as r:
            if r.status_code not in (200, 401, 403):
                r.failure(f"/me returned unexpected status {r.status_code}")
            elif r.status_code != 200:
                r.failure("authentication token rejected; check TEST_AUTH_TOKEN")
            else:
                r.success()

    @task(3)
    def list_documents(self):
        if not AUTH_TOKEN:
            return
        with self.client.get(
            "/documents", headers=self.headers,
            name="GET /documents", catch_response=True,
        ) as r:
            if r.status_code != 200:
                r.failure(f"/documents returned {r.status_code}")
            else:
                r.success()

    @task(1)
    def ask_question(self):
        if not (AUTH_TOKEN and DOCUMENT_ID and RUN_RAG_QUERIES):
            return
        payload = {"question": QUESTION, "document_id": DOCUMENT_ID}
        with self.client.post(
            "/ask_query",
            data=json.dumps(payload),
            headers={**self.headers, "Content-Type": "application/json"},
            name="POST /ask_query",
            timeout=90,
            catch_response=True,
        ) as r:
            if r.status_code != 200:
                r.failure(f"/ask_query returned {r.status_code}: {r.text[:200]}")
            else:
                r.success()
