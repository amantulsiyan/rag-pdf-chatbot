# 🔍 Confidence Scoring Transparency Guide

## What Users See Now

### 1. Confidence Badge (Always Visible)
```
Confidence: 32% ⓘ
```
- Color-coded: Green (≥70%), Yellow (40-69%), Red (<40%)

### 2. Expandable Breakdown (Click to Expand)
```
📊 Confidence Breakdown ⓘ ▼

[When expanded:]
Mean Relevance (50% weight)    ████░░░░░░ 25%
Agreement (30% weight)         ████████░░ 85%
Dominance (20% weight)         █░░░░░░░░░ 10%

⚠️ Low confidence: No single chunk clearly dominates, 
evidence is distributed.

Final Calculation:
25.0% × 0.5 + 85.0% × 0.3 + 10.0% × 0.2 = 32%
```

### 3. Formula Modal (Click ⓘ Icon)
Full transparency modal explaining:
- **Core Formula**: `Confidence = 0.5 × Mean + 0.3 × Agreement + 0.2 × Dominance`
- **Component Definitions**:
  - Mean Relevance: Average cross-encoder reranking score
  - Agreement: `1 / (1 + variance)` - measures chunk consistency
  - Dominance: `Top Score - Second Score` - measures clear winner
- **Design Rationale**: Why retrieval-based > LLM self-assessment
- **Example Scenarios**: High vs Low confidence patterns

---

## Interview Talking Points

### "Why is confidence transparent?"

*"I made confidence scoring fully transparent because in production RAG systems, users need to understand WHY the system is confident or uncertain. The breakdown shows three metrics:*

1. **Mean Relevance (50%)**: Are retrieved chunks actually relevant?
2. **Agreement (30%)**: Do chunks provide consistent information?
3. **Dominance (20%)**: Is there a clear authoritative source?

*This helps users distinguish between 'weak retrieval' vs 'conflicting evidence' vs 'distributed information'—which is critical for debugging and trust."*

### "Why not use LLM confidence?"

*"LLMs are notoriously overconfident and hallucinate fluently. By computing confidence from cross-encoder reranking scores—before the LLM even sees the context—we get honest, retrieval-based uncertainty. If chunks score low, we decline to answer rather than hallucinate."*

### "What's the live calculation for?"

*"The yellow box shows the exact math: `25% × 0.5 + 85% × 0.3 + 10% × 0.2 = 32%`. This makes the system auditable—users can verify the score themselves. It's especially useful when explaining edge cases in interviews or production debugging."*

---

## Test Queries to Showcase Transparency

| Query | Expected Breakdown | What It Shows |
|-------|-------------------|---------------|
| `"Kohli's ICC awards"` | High mean, high agreement, high dominance | Perfect retrieval |
| `"Kohleee's wife"` (typo) | Low mean, high agreement, low dominance | Typo hurts retrieval but chunks agree |
| `"What did he win?"` (vague) | Low mean, low agreement, low dominance | Ambiguity → weak retrieval |
| `"Capital of France"` (out-of-context) | Very low mean, low agreement, low dominance | Correctly declines |
| `"[Exact PDF sentence]"` | High mean, high agreement, very high dominance | Single perfect match |

---

## Code Flow

```
User Query
    ↓
Hybrid Retrieval (FAISS + BM25) → Top 15 chunks
    ↓
Cross-Encoder Reranking → Top 5 chunks with scores
    ↓
Confidence Calculation (rag/confidence.py):
    - mean_score = average(rerank_scores)
    - variance = var(rerank_scores)
    - agreement = 1 / (1 + variance)
    - dominance = top_score - second_score
    - confidence = 0.5×mean + 0.3×agreement + 0.2×dominance
    ↓
API Response (api/models.py):
    {
      "answer": "...",
      "confidence": 0.32,
      "confidence_breakdown": {
        "mean_score": 0.25,
        "agreement": 0.85,
        "dominance": 0.10,
        "variance": 0.15
      }
    }
    ↓
Frontend Display (frontend/script.js):
    - Visual bars for each metric
    - Live calculation formula
    - Contextual explanation
    - Modal with full formula documentation
```

---

## Files Modified for Transparency

1. **Backend**:
   - `rag/confidence.py` - Returns breakdown dict
   - `rag/pipeline.py` - Passes breakdown to response
   - `api/models.py` - Includes `ConfidenceBreakdown` schema

2. **Frontend**:
   - `frontend/script.js` - Renders breakdown + modal
   - `frontend/styles.css` - Styles for bars, modal, calculation box

---

## Production Benefits

1. **User Trust**: Users see WHY confidence is low/high
2. **Debugging**: Developers can diagnose retrieval vs LLM issues
3. **Auditability**: Exact formula is documented and visible
4. **Interview Gold**: Shows deep understanding of RAG limitations
5. **Honest Uncertainty**: Prevents overconfident hallucinations

---

## Next Steps

- Test with adversarial queries (see main conversation)
- Log breakdown patterns for different query types
- Consider adding "Why this score?" tooltips on each metric
- Add export feature to save breakdown for analysis
