from pydantic import BaseModel
from typing import List, Dict

class UploadResponse(BaseModel):
    material_id: int
    status: str
    blocks_count: int

class QARequest(BaseModel):
    material_id: int
    question: str

class QAResponse(BaseModel):
    answer: str
    sources: List[Dict]
    response_time_ms: int
