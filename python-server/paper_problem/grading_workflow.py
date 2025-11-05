from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Dict
import logging, time

from paper_problem.models import Problem
from paper_problem.graders.short_answer_grader import short_answer_grader
from paper_problem.graders.coding_grader import coding_grader

logger = logging.getLogger(__name__)

class GradingState(TypedDict):
    problem: Problem
    user_answer: str
    grading_result: Dict
    is_verified: bool
    retry_count: int
    confidence_score: float

# 노드1: 입력 검증
async def validate_input_node(state: GradingState) -> dict:
    """입력 유효성 검사"""
    problem = state["problem"]
    user_answer = state["user_answer"]

    logger.info(f"Validating input for problem_type={problem.problem_type}")

    # 빈 답변 체크
    if not user_answer or not user_answer.strip():
        logger.warning("Empty user answer detected")
        return {
            "grading_result": {
                "is_correct": False,
                "score": 0,
                "feedback": "답변이 비어 있습니다. 답변을 입력해주세요.",
            },
            "is_verified": True,  # 검증 불필요
            "confidence_score": 1.0
        }

    # 문제 타입 검증
    if problem.problem_type not in ["SHORT_ANSWER", "CODING"]:
        logger.error(f"Unknown problem_type: {problem.problem_type}")
        return {
            "grading_result": {
                "is_correct": False,
                "score": 0,
                "feedback": f"지원하지 않는 문제 타입입니다: {problem.problem_type}",
            },
            "is_verified": True,
            "confidence_score": 1.0
        }

    return {}

# 노드2: 채점 실행
async def grade_answer_node(state: GradingState) -> dict:
    """문제 타입별 채점 실행"""
    problem = state["problem"]
    user_answer = state["user_answer"]
    retry_count = state.get("retry_count", 0)

    # 이미 검증된 결과가 있으면 스킵
    if state.get("is_verified", False):
        return {}

    if retry_count > 0:
        logger.info(f"Regrading (retry {retry_count})")

    logger.info(f"Grading problem_type={problem.problem_type}")

    try:
        # 문제 타입별 채점
        if problem.problem_type == "SHORT_ANSWER":
            result = await short_answer_grader.grade(problem, user_answer)
        elif problem.problem_type == "CODING":
            result = await coding_grader.grade(problem, user_answer)
        else:
            raise ValueError(f"Unknown problem_type: {problem.problem_type}")

        # confidence_score 계산 (LLM 응답 품질)
        confidence_score = result.get("similarity_score", 0.5)

        logger.info(f"Grading completed: score={result['score']}, confidence={confidence_score:.2f}")

        return {
            "grading_result": result,
            "confidence_score": confidence_score
        }

    except Exception as e:
        logger.error(f"Grading failed: {e}")
        return {
            "grading_result": {
                "is_correct": False,
                "score": 0,
                "feedback": f"채점 중 오류가 발생했습니다: {str(e)}",
            },
            "confidence_score": 0.0
        }

# 노드3: 결과 검증
async def verify_result_node(state: GradingState) -> dict:
    """채점 결과 검증"""
    grading_result = state["grading_result"]
    confidence_score = state.get("confidence_score", 0.5)
    retry_count = state.get("retry_count", 0)

    # 이미 검증된 경우 스킵
    if state.get("is_verified", False):
        return {}

    logger.info(f"Verifying result: confidence={confidence_score:.2f}")

    # 신뢰도 검증
    is_verified = True
    if confidence_score < 0.3:
        logger.warning(f"⚠️ Low confidence score: {confidence_score:.2f}")
        is_verified = False

    # 점수 범위 검증
    score = grading_result.get("score", 0)
    if not (0 <= score <= 100):
        logger.error(f"Invalid score: {score}")
        is_verified = False

    logger.info(f"Verification result: {is_verified}")

    return {
        "is_verified": is_verified,
        "retry_count": retry_count + 1
    }

# 노드4: 재시도 판단
def should_retry(state: GradingState) -> str:
    """불확실한 경우 재시도 (최대 2회)"""
    is_verified = state.get("is_verified", False)
    retry_count = state.get("retry_count", 0)
    confidence_score = state.get("confidence_score", 0.5)

    MAX_RETRIES = 2

    # 검증 통과
    if is_verified:
        logger.info(f"✅ Verification passed")
        return "end"

    # 재시도 횟수 초과
    if retry_count >= MAX_RETRIES:
        logger.warning(f"⚠️ Max retries ({MAX_RETRIES}) reached. Using current result.")
        return "end"

    # 재시도
    logger.warning(f"Retrying grading (confidence={confidence_score:.2f}, attempt {retry_count + 1}/{MAX_RETRIES})")
    return "retry"

# 워크플로우 생성
def create_grading_workflow():
    graph = StateGraph(GradingState)

    # 노드 추가
    graph.add_node("validate_input", validate_input_node)
    graph.add_node("grade", grade_answer_node)
    graph.add_node("verify", verify_result_node)

    # 엣지
    graph.add_edge(START, "validate_input")
    graph.add_edge("validate_input", "grade")
    graph.add_edge("grade", "verify")

    # 조건부 엣지 (재시도 판단)
    graph.add_conditional_edges(
        "verify",
        should_retry,
        {
            "retry": "grade",  # 재채점
            "end": END
        }
    )

    return graph.compile()

grading_workflow = create_grading_workflow()
