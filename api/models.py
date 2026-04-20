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

class AskResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[SourceModel]
    confidence_breakdown: ConfidenceBreakdown

class QuestionRequest(BaseModel):
    question: str
