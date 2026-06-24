from pydantic import BaseModel
from typing import List, Dict

class SourceModel(BaseModel):
    chunk_id: str
    score: float
    text: str

class ConfidenceBreakdown(BaseModel):
    mean_score: float
    agreement: float
    dominance: float
    variance: float

class LatencyBreakdown(BaseModel):
    query_rewriting_ms: float
    embedding_ms: float
    hybrid_retrieval_ms: float
    normalisation_ms: float
    calculation_ms: float
    reranking_ms: float
    generation_ms: float
    total_ms: float
class AskResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[SourceModel]
    confidence_breakdown: ConfidenceBreakdown
    latency_breakdown: LatencyBreakdown

class QuestionRequest(BaseModel):
    question: str
