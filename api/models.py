from pydantic import BaseModel
from typing import List

class SourceModel(BaseModel):
    chunk_id: str
    score: float

class AskResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[SourceModel]

class QuestionRequest(BaseModel):
    question: str
