# Phase 1 — Baseline, audit and reproducible local test

## Objective

Measure the existing application before changing its architecture. The first
milestone is a repeatable baseline, not a claim that the current application
supports 25,000 sessions.

## Repository audit (based on the supplied ZIP)

Confirmed in the current source:

1. `api/dependencies.py` creates `app.state.document_indexes = {}`. This cache
   is local to one Python process and is not shared between replicas.
2. `api/routes/upload.py` performs PDF extraction, chunking, embedding, FAISS
   construction and BM25 construction inside the upload request, then writes
   indexes into that process-local dictionary.
3. `api/routes/query.py:get_document_indexes()` rebuilds extraction, chunks,
   embeddings and both indexes when a document is not in that process's cache.
4. The query endpoint is declared `async`, but it calls synchronous
   `psycopg2`, synchronous Groq SDK methods, embedding inference, reranking and
   synchronous logging functions.
5. Database connection functions in `api/routes/query.py`,
   `api/routes/upload.py`, `api/routes/auth_routes.py` and `logger/logger.py`
   create a fresh `psycopg2.connect()` connection for each operation. They
   hardcode database name/user/host/port and only read the password from env.
6. `logger/logger.py` runs `init_logging_tables()` at import time and the query
   path performs four separate logging operations/connections.
7. The repository has functional test/evaluation reports, but no Locust/k6
   load-test suite was present in the supplied source tree.
8. All Python source files passed `py_compile` in the audit environment.

## Test semantics

- One Locust user = one logical simulated client session.
- The default test periodically calls `/health`; it measures API/session
  overhead, not authenticated RAG throughput.
- Set `TEST_AUTH_TOKEN` to also exercise `/me` and `/documents`.
- Set `TEST_DOCUMENT_ID` and `RUN_RAG_QUERIES=true` to include expensive
  end-to-end queries. Use this only at low concurrency initially because every
  query can call the external LLM provider.
- Do not run 25,000 users against the current application as the first test.
  Ramp gradually and watch API, database, CPU, memory and provider limits.

## Install and run (Windows PowerShell)

From the project root:

```powershell
python -m venv .venv-loadtest
.\.venv-loadtest\Scripts\Activate.ps1
python -m pip install -r requirements-loadtest.txt
```

Start the existing API in a separate terminal using its normal environment:

```powershell
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Run a small health/session baseline first:

```powershell
locust -f loadtests/locustfile.py --host http://127.0.0.1:8000 --users 25 --spawn-rate 5 --run-time 2m --headless --csv=baseline_25
```

Then repeat at 50, 100 and 250 users, changing `--users` and saving a distinct
CSV prefix for each run. Do not jump straight to 25,000.

For authenticated endpoint coverage, set a valid test JWT and run:

```powershell
$env:TEST_AUTH_TOKEN = "<test-user-access-token>"
locust -f loadtests/locustfile.py --host http://127.0.0.1:8000 --users 50 --spawn-rate 5 --run-time 2m --headless --csv=baseline_auth_50
```

For a low-rate RAG test:

```powershell
$env:TEST_DOCUMENT_ID = "<owned-document-uuid>"
$env:RUN_RAG_QUERIES = "true"
locust -f loadtests/locustfile.py --host http://127.0.0.1:8000 --users 5 --spawn-rate 1 --run-time 2m --headless --csv=baseline_rag_5
```

## Record for every run

- User count and spawn rate
- Requests/sec
- Total requests and failures
- p50, p95 and p99 response times
- CPU and RAM of API/database processes
- PostgreSQL active connections
- Groq rate-limit/timeout errors (for RAG runs)
- Whether the load generator itself reached CPU/RAM limits

## Phase 1 exit criteria

- API starts reliably from a clean environment.
- `/health` and authenticated routes have known baseline behavior.
- Baseline CSVs exist for 25, 50, 100 and 250 sessions.
- A low-concurrency end-to-end RAG baseline exists, or the exact blocker is
  documented.
- No scalability claim is made from a health-only test.

## Next phase

After baseline results are captured, centralize configuration and database
connection management, then containerize the application and its dependencies.
Only after that should we migrate the document index out of process memory.
