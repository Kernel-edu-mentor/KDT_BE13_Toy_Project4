from pydantic import BaseModel
from typing import List, Dict, Literal


class MaterialUploadRequest(BaseModel):
    material_id: int
    file_path: str
    file_type: str = "pdf"

class MaterialUploadResponse(BaseModel):
    material_id: int
    status: str
    page_count: int
    chunk_count: int
    message: str

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


class MaterialUploadRequest(BaseModel):
    material_id: int
    file_path: str
    file_type: Literal["pdf", "ppt"]


class MaterialUploadResponse(BaseModel):
    material_id: int
    status: Literal["completed", "failed"]
    page_count: int
    chunk_count: int
    message: str
