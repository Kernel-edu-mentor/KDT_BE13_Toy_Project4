# team2_problem/models.py
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


class ProblemResponse(BaseModel):
    problems: List[Problem]
    difficulty: str
    generated_count: int
    rejected_count: int
