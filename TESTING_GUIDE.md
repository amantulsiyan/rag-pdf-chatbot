# RAG System Testing Guide

## 🎯 Quick Start

### 1. View All Test Queries
```bash
python test_queries.py
```

### 2. Run Quick Test (3 queries per category)
```bash
python test_runner.py
```

### 3. Run Full Test (All queries)
```bash
python test_runner.py all
```

### 4. Test Specific Categories
```bash
# Test only baseline queries
python test_runner.py baseline

# Test multiple categories
python test_runner.py baseline,numerical,semantic

# Test with limit
python test_runner.py adversarial 5
```

---

## 📋 Test Categories

### ✅ Should Work Well
- **baseline**: Simple factual questions
- **numerical**: Specific numbers/dates (tests BM25)
- **semantic**: Conceptual questions (tests FAISS)

### ⚠️ Moderate Difficulty
- **ambiguous**: Vague queries (tests query rewriting)
- **temporal**: Time-based questions
- **paraphrase**: Same question, different words
- **confidence_test**: Varying difficulty levels

### ❌ Expected to Struggle
- **multi_hop**: Requires reasoning across multiple facts
- **negation**: "What does NOT..." questions
- **chunk_boundary**: Information split across chunks
- **out_of_scope**: Questions not in document

### 🔥 Stress Tests
- **adversarial**: Prompt injection, hallucination attempts
- **edge_cases**: Empty queries, special characters
- **retrieval_stress**: Keyword stuffing, single words

---

## 🔍 What to Look For

### High Confidence Issues
- **High confidence + wrong answer** = Retrieval failure
- **High confidence + "I don't know"** = Over-cautious system
- **High confidence + short answer** = Incomplete retrieval

### Low Confidence Issues
- **Low confidence + correct answer** = Confidence scoring problem
- **Low confidence + long answer** = System unsure but verbose
- **Low confidence + "I don't know"** = Good behavior (honest)

### Retrieval Issues
- Check rerank scores in console output
- Low scores (<0.3) = Poor retrieval
- High variance = Inconsistent chunks
- Low dominance = No clear best match

### Query Rewriting Issues
- Compare original vs rewritten query
- Rewritten should be MORE specific
- Should preserve intent

---

## 📊 Expected Results by Category

| Category | Expected Confidence | Expected Behavior |
|----------|-------------------|-------------------|
| baseline | >0.7 | Accurate, direct answers |
| numerical | >0.6 | Exact numbers if present |
| semantic | 0.5-0.8 | Contextual explanations |
| ambiguous | 0.4-0.7 | Query rewriting helps |
| multi_hop | <0.4 | "I don't know" (limitation) |
| negation | <0.5 | May struggle with logic |
| out_of_scope | <0.3 | "I don't know" |
| adversarial | <0.3 | Resist manipulation |

---

## 🐛 Common Failure Modes

### 1. Hallucination
**Symptom**: Answer contains info not in document
**Check**: Compare answer with source chunks
**Fix**: Strengthen prompt, lower temperature

### 2. Retrieval Failure
**Symptom**: Low rerank scores, wrong chunks retrieved
**Check**: Console output for chunk scores
**Fix**: Adjust alpha, increase top_k, improve embeddings

### 3. Query Rewriting Failure
**Symptom**: Rewritten query is worse than original
**Check**: Console output for rewritten query
**Fix**: Improve rewriting prompt, adjust temperature

### 4. Chunk Boundary Loss
**Symptom**: Incomplete answers for broad questions
**Check**: Are relevant chunks split?
**Fix**: Adjust chunk size/overlap, increase reranked_k

### 5. Confidence Miscalibration
**Symptom**: Confidence doesn't match answer quality
**Check**: Breakdown scores (mean, agreement, dominance)
**Fix**: Adjust confidence formula weights

---

## 🧪 Manual Testing Checklist

### Before Testing
- [ ] Backend running (`uvicorn api.main:app --reload`)
- [ ] PDF uploaded and indexed
- [ ] Check console for errors

### During Testing
- [ ] Monitor rerank scores
- [ ] Check query rewriting output
- [ ] Watch confidence breakdown
- [ ] Note response times

### After Testing
- [ ] Review test_results_*.json
- [ ] Read test_report_*.txt
- [ ] Identify patterns in failures
- [ ] Document edge cases

---

## 💡 Testing Tips

1. **Start Small**: Test baseline queries first
2. **Check Console**: Rerank scores reveal retrieval quality
3. **Compare Categories**: Which types work best?
4. **Test Edge Cases**: Empty queries, special chars
5. **Try Adversarial**: Can you break it?
6. **Monitor Confidence**: Does it correlate with quality?
7. **Check Sources**: Are the right chunks retrieved?
8. **Time Responses**: Identify slow queries

---

## 🎯 Success Criteria

### Minimum Viable
- ✅ Baseline queries: >80% correct, >0.7 confidence
- ✅ Out-of-scope: Returns "I don't know"
- ✅ No crashes on edge cases
- ✅ Response time: <5s average

### Good Performance
- ✅ Numerical queries: >70% correct
- ✅ Semantic queries: >60% correct
- ✅ Adversarial: Resists prompt injection
- ✅ Confidence calibrated (high conf = correct)

### Excellent Performance
- ✅ Multi-hop: Attempts reasoning
- ✅ Negation: Handles correctly
- ✅ Chunk boundary: Aggregates info
- ✅ Paraphrase: Consistent answers

---

## 📝 Example Test Session

```bash
# 1. Start backend
uvicorn api.main:app --reload

# 2. In new terminal, run quick test
python test_runner.py

# 3. Review results
cat test_report_*.txt

# 4. Test specific problem areas
python test_runner.py adversarial,edge_cases

# 5. Manual testing via frontend
# Open http://localhost:8080
# Try queries from test_queries.py
```

---

## 🔧 Debugging Commands

```bash
# Check if API is running
curl http://localhost:8000/docs

# Test single query via API
curl -X POST http://localhost:8000/ask_query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Virat Kohli?"}'

# View test queries
python test_queries.py

# Run specific category
python test_runner.py baseline 5
```

---

## 📈 Improvement Tracking

After each test session, document:
1. **What broke?** (failure modes)
2. **Why?** (root cause)
3. **Fix applied** (code changes)
4. **Result** (improvement metrics)

Keep a testing log to track progress over time.
