# 🔍 PostgreSQL Observability Guide

## Overview

This RAG system implements **comprehensive observability** using PostgreSQL to track every request, enabling performance analysis, debugging, and system monitoring. All telemetry data is persisted in a relational database for historical analysis and auditing.

---

## 📊 What is Being Monitored?

### 1. Request Metadata (rag_requests)
Captures high-level information about each query:
- **request_id** (UUID) - Unique identifier for tracking across tables
- **user_id** - User who made the request (default: "user_1")
- **original_query** - Exact user question
- **rewritten_query** - LLM-optimized version for retrieval
- **final_response** - Generated answer
- **latency_ms** - Total end-to-end response time
- **timestamp** - When the request was made

**Use Case:** Answer questions like "What queries are taking longest?" or "What did the system return for this question?"

---

### 2. Latency Breakdown (rag_timings)
Tracks millisecond-level timing for each pipeline stage:
- **query_rewriting_ms** - Time to rewrite query with LLM
- **embedding_ms** - Time to generate query embeddings
- **hybrid_retrieval_ms** - Time for FAISS + BM25 search
- **normalisation_ms** - Time to normalize scores
- **calculation_ms** - Time to compute hybrid scores
- **reranking_ms** - Time for cross-encoder reranking
- **generation_ms** - Time for LLM to generate answer
- **total_ms** - Sum of all stages

**Use Case:** Identify bottlenecks - "Is reranking slow?" or "Which stage is the performance issue?"

---

### 3. Retrieval Scores (rag_scores)
Logs scores at two stages: initial hybrid retrieval and after reranking:

**Initial Retrieval (top-8 chunks):**
- FAISS score (semantic similarity)
- BM25 score (keyword matching)
- Hybrid score (weighted combination)
- Chunk rank before reranking

**After Reranking (top-5 chunks):**
- All above scores PLUS rerank_score from cross-encoder
- Final rank after reranking

**Use Case:** Debug retrieval quality - "Did reranking fix the ordering?" or "Are FAISS and BM25 agreeing?"

---

### 4. Retrieved Chunks (rag_retrievals)
Stores actual chunk text at both retrieval stages:
- **retrieval_stage** - "hybrid_retrieval" or "reranked"
- **chunk_rank** - Position in ranking (1-8 for hybrid, 1-5 for reranked)
- **chunk_text** - Full text of the retrieved chunk

**Use Case:** Manual inspection - "What chunks were retrieved?" or "Is the right context being passed to the LLM?"

---

## 🗄️ Database Schema

```sql
-- Main request tracking
CREATE TABLE rag_requests (
    request_id UUID PRIMARY KEY,
    user_id VARCHAR(255),
    original_query TEXT,
    rewritten_query TEXT,
    final_response TEXT,
    latency_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Latency telemetry
CREATE TABLE rag_timings (
    id SERIAL PRIMARY KEY,
    request_id UUID REFERENCES rag_requests(request_id) ON DELETE CASCADE,
    query_rewriting_ms FLOAT,
    embedding_ms FLOAT,
    hybrid_retrieval_ms FLOAT,
    normalisation_ms FLOAT,
    calculation_ms FLOAT,
    reranking_ms FLOAT,
    generation_ms FLOAT,
    total_ms FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Score tracking
CREATE TABLE rag_scores (
    id SERIAL PRIMARY KEY,
    request_id UUID REFERENCES rag_requests(request_id) ON DELETE CASCADE,
    retrieval_stage VARCHAR(50),  -- 'initial' or 'reranked'
    chunk_rank INTEGER,
    faiss_score FLOAT,
    bm25_score FLOAT,
    hybrid_score FLOAT,
    rerank_score FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chunk text logging
CREATE TABLE rag_retrievals (
    id SERIAL PRIMARY KEY,
    request_id UUID REFERENCES rag_requests(request_id) ON DELETE CASCADE,
    retrieval_stage VARCHAR(50),  -- 'hybrid_retrieval' or 'reranked'
    chunk_rank INTEGER,
    chunk_text TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔌 How to Access the Data

### Prerequisites

1. **PostgreSQL Running**
   ```bash
   # Check if PostgreSQL is running (Windows)
   pg_ctl status
   
   # Start PostgreSQL service
   net start postgresql-x64-15
   ```

2. **Database Credentials**
   
   Set in `.env` file:
   ```env
   DB_PASSWORD=your_postgres_password
   ```

---

### Method 1: Command Line (psql)

```bash
# Connect to database
psql -U postgres -d rag_db

# Or from any directory
psql postgresql://postgres:your_password@localhost:5432/rag_db
```

**Useful Queries:**

```sql
-- 1. View all requests
SELECT request_id, user_id, original_query, latency_ms, timestamp 
FROM rag_requests 
ORDER BY timestamp DESC 
LIMIT 10;

-- 2. Find slowest queries
SELECT original_query, latency_ms 
FROM rag_requests 
ORDER BY latency_ms DESC 
LIMIT 10;

-- 3. View latency breakdown for a specific request
SELECT * 
FROM rag_timings 
WHERE request_id = 'your-uuid-here';

-- 4. Average latency by pipeline stage
SELECT 
    AVG(query_rewriting_ms) as avg_rewriting,
    AVG(embedding_ms) as avg_embedding,
    AVG(hybrid_retrieval_ms) as avg_retrieval,
    AVG(reranking_ms) as avg_reranking,
    AVG(generation_ms) as avg_generation
FROM rag_timings;

-- 5. View retrieval scores for a request
SELECT retrieval_stage, chunk_rank, faiss_score, bm25_score, hybrid_score, rerank_score
FROM rag_scores
WHERE request_id = 'your-uuid-here'
ORDER BY retrieval_stage, chunk_rank;

-- 6. Compare scores before and after reranking
SELECT 
    'Initial' as stage,
    chunk_rank,
    hybrid_score as score
FROM rag_scores
WHERE request_id = 'your-uuid-here' AND retrieval_stage = 'initial'
UNION ALL
SELECT 
    'Reranked' as stage,
    chunk_rank,
    rerank_score as score
FROM rag_scores
WHERE request_id = 'your-uuid-here' AND retrieval_stage = 'reranked'
ORDER BY stage, chunk_rank;

-- 7. View retrieved chunks
SELECT retrieval_stage, chunk_rank, LEFT(chunk_text, 100) as chunk_preview
FROM rag_retrievals
WHERE request_id = 'your-uuid-here'
ORDER BY retrieval_stage, chunk_rank;

-- 8. Full request reconstruction
SELECT 
    r.request_id,
    r.original_query,
    r.rewritten_query,
    r.final_response,
    t.total_ms,
    t.generation_ms,
    t.reranking_ms
FROM rag_requests r
JOIN rag_timings t ON r.request_id = t.request_id
WHERE r.request_id = 'your-uuid-here';

-- 9. Requests with low reranking effectiveness (reranking didn't change order much)
SELECT 
    r.request_id,
    r.original_query,
    COUNT(DISTINCT s.chunk_rank) as unique_ranks
FROM rag_requests r
JOIN rag_scores s ON r.request_id = s.request_id
WHERE s.retrieval_stage = 'reranked'
GROUP BY r.request_id, r.original_query
HAVING COUNT(DISTINCT s.chunk_rank) < 3;

-- 10. Recent queries with their performance
SELECT 
    r.original_query,
    r.latency_ms,
    t.reranking_ms,
    t.generation_ms,
    r.timestamp
FROM rag_requests r
JOIN rag_timings t ON r.request_id = t.request_id
ORDER BY r.timestamp DESC
LIMIT 20;
```

---

### Method 2: Python Script

```python
import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# Connect
conn = psycopg2.connect(
    dbname="rag_db",
    user="postgres",
    password=os.getenv("DB_PASSWORD"),
    host="localhost",
    port="5432"
)

# Query recent requests
query = """
SELECT 
    r.request_id,
    r.original_query,
    r.latency_ms,
    t.reranking_ms,
    t.generation_ms
FROM rag_requests r
JOIN rag_timings t ON r.request_id = t.request_id
ORDER BY r.timestamp DESC
LIMIT 10;
"""

df = pd.read_sql(query, conn)
print(df)

conn.close()
```

---

### Method 3: GUI Tool (pgAdmin or DBeaver)

**Using pgAdmin:**
1. Open pgAdmin
2. Connect to localhost
3. Navigate: Servers → PostgreSQL 15 → Databases → rag_db → Schemas → public → Tables
4. Right-click on table → View/Edit Data → All Rows

**Using DBeaver (recommended):**
1. Download DBeaver Community Edition
2. Create new PostgreSQL connection
3. Host: localhost, Port: 5432, Database: rag_db
4. Run queries in SQL Editor

---

## 📈 Common Analysis Patterns

### 1. Performance Bottleneck Analysis

```sql
-- Find which stage is slowest on average
SELECT 
    'Query Rewriting' as stage, AVG(query_rewriting_ms) as avg_ms FROM rag_timings
UNION ALL
SELECT 'Embedding', AVG(embedding_ms) FROM rag_timings
UNION ALL
SELECT 'Hybrid Retrieval', AVG(hybrid_retrieval_ms) FROM rag_timings
UNION ALL
SELECT 'Reranking', AVG(reranking_ms) FROM rag_timings
UNION ALL
SELECT 'Generation', AVG(generation_ms) FROM rag_timings
ORDER BY avg_ms DESC;
```

### 2. Retrieval Quality Check

```sql
-- Check if reranking is improving results (comparing rank changes)
WITH initial_ranks AS (
    SELECT request_id, chunk_rank, hybrid_score
    FROM rag_scores
    WHERE retrieval_stage = 'initial'
),
reranked_ranks AS (
    SELECT request_id, chunk_rank, rerank_score
    FROM rag_scores
    WHERE retrieval_stage = 'reranked'
)
SELECT 
    r.original_query,
    AVG(rr.rerank_score - ir.hybrid_score) as avg_score_improvement
FROM rag_requests r
JOIN initial_ranks ir ON r.request_id = ir.request_id
JOIN reranked_ranks rr ON r.request_id = rr.request_id 
    AND ir.chunk_rank = rr.chunk_rank
GROUP BY r.original_query
ORDER BY avg_score_improvement DESC;
```

### 3. Query Pattern Analysis

```sql
-- Most common query patterns
SELECT 
    LEFT(original_query, 50) as query_pattern,
    COUNT(*) as frequency,
    AVG(latency_ms) as avg_latency
FROM rag_requests
GROUP BY LEFT(original_query, 50)
ORDER BY frequency DESC
LIMIT 10;
```

---

## 🧹 Database Maintenance

### Clear Old Data

```sql
-- Delete requests older than 30 days
DELETE FROM rag_requests 
WHERE timestamp < NOW() - INTERVAL '30 days';

-- Clear all data (CAUTION!)
TRUNCATE TABLE rag_requests CASCADE;
```

### Check Database Size

```sql
-- Size of each table
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 🔧 Troubleshooting

### Connection Issues

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check if database exists
psql -U postgres -l | grep rag_db

# Create database if missing
psql -U postgres -c "CREATE DATABASE rag_db;"
```

### Schema Setup

Run this SQL to create all tables:

```sql
-- Copy the full schema from the "Database Schema" section above
-- and run it in psql or pgAdmin
```

### No Data Being Logged?

1. Check `.env` has correct `DB_PASSWORD`
2. Verify logger is being called in `api/routes/query.py`
3. Check console for database errors
4. Verify tables exist: `\dt` in psql

---

## 📊 Sample Dashboard Queries

### Real-time Performance Monitor

```sql
-- Last 10 requests with performance metrics
SELECT 
    r.timestamp,
    r.original_query,
    r.latency_ms,
    ROUND((t.reranking_ms / t.total_ms * 100)::numeric, 1) as rerank_pct,
    ROUND((t.generation_ms / t.total_ms * 100)::numeric, 1) as generation_pct
FROM rag_requests r
JOIN rag_timings t ON r.request_id = t.request_id
ORDER BY r.timestamp DESC
LIMIT 10;
```

### Success Rate (assuming empty responses indicate failures)

```sql
SELECT 
    COUNT(*) as total_requests,
    COUNT(CASE WHEN final_response != '' THEN 1 END) as successful,
    ROUND(COUNT(CASE WHEN final_response != '' THEN 1 END)::numeric / COUNT(*)::numeric * 100, 2) as success_rate
FROM rag_requests;
```

---

## 🎯 Best Practices

1. **Regular Monitoring**: Check performance weekly to catch degradation
2. **Index Key Columns**: Add indexes on `request_id` and `timestamp` for faster queries
3. **Archive Old Data**: Move data older than 90 days to archival storage
4. **Alert on Slow Queries**: Set up alerts when `latency_ms > 10000`
5. **Track Trends**: Monitor average latency over time to detect issues

---

## 🚀 Future Enhancements

Potential additions to observability:
- Confidence score tracking per request
- User feedback loop (thumbs up/down)
- A/B testing support (track different reranking models)
- Real-time dashboard with Grafana
- Automated anomaly detection
- Cost tracking (LLM API token usage)

---

## 📝 Notes

- All timestamps are in UTC
- `CASCADE DELETE` ensures deleting a request removes all related telemetry
- UUID-based tracking allows correlation across all 4 tables
- Logging happens synchronously in the request path (consider async for production scale)
