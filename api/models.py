from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict
from uuid import UUID

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length =128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

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
    document_id: UUID