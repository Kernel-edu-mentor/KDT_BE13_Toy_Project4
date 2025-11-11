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

# 답변 검증 관련 모델
class AnswerCheckRequest(BaseModel):
    problem: Problem
    user_answer: str

class AnswerCheckResponse(BaseModel):
    is_correct: bool
    score: int  # 0-100 점수
    feedback: str  # 상세 피드백
    correct_answer: Optional[str] = None  # 오답일 경우만 표시
    similarity_score: Optional[float] = None  # SHORT_ANSWER용 의미 유사도
    rubric_scores: Optional[Dict] = None  # CODING용 루브릭 점수
    test_results: Optional[List[Dict]] = None  # CODING용 테스트 결과
    response_time_ms: int

# 키워드 추출 관련 모델
class KeywordRequest(BaseModel):
    questions: List[str]  # 최근 질문 목록
    max_keywords: int = 5  # 추출할 최대 키워드 수

class KeywordResponse(BaseModel):
    keywords: List[str]  # 추출된 키워드 목록
    response_time_ms: int
