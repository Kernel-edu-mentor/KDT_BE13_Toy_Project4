from pydantic import BaseModel
from typing import List, Dict, Literal, Optional

class Problem(BaseModel):
    question: str
    answer: str
    hints: List[str]
    difficulty_score: int
    problem_type: Literal["CODING", "SHORT_ANSWER"]
    test_cases: Optional[List[Dict]] = []

class ProblemRequest(BaseModel):
    material_id: int
    difficulty: Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"]
    problem_count: int = 3
    learning_description: Optional[str] = None  # "JPA를 학습하고 Entity 클래스 개념을 학습했다"
    learning_topics: Optional[List[str]] = None  # 또는 직접 토픽 배열 전달

class ProblemResponse(BaseModel):
    problems: List[Problem]
    difficulty: str
    generated_count: int
    rejected_count: int
    response_time_ms: int
