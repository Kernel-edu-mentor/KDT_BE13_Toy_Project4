from fastapi import APIRouter, HTTPException
from paper_problem.models import ProblemRequest, ProblemResponse
from paper_problem.workflow import problem_workflow
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/problems", tags=["Problems"])


@router.post("/generate", response_model=ProblemResponse)
async def generate_problems(request: ProblemRequest):
    """난이도별 실습 문제 생성"""

    logger.info(
        f"Generating {request.problem_count} {request.difficulty} problems "
        f"for meterial {request.material_ide}"
    )

    try:
        # Lang Graph 워크플로우 실행
        result = await problem_workflow.ainvoke(
            {
                "material_id": request.material_id,
                "difficulty": request.difficulty,
                "problem_count": request.problem_count,
            }
        )

        validated_problems = result["validated_problems"]
        rejection_reasons = result["rejection_reasons"]

        if not validated_problems:
            raise HTTPException(
                status_code=500, detail="Failed to generate valid problems"
            )

        return ProblemResponse(
            problems=validated_problems,
            difficulty=request.difficulty,
            generated_count=len(validated_problems),
            rejected_count=len(rejection_reasons),
        )

    except Exception as e:
        logger.error(f"Error generating problems : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/difficulties")
async def get_difficulty_info():
    """난이도별 정보 조회"""
    return {
        "BEGINNER": {
            "score_range": "1-3",
            "description": "기본 개념 이해 확인",
            "example": "JPA Entity 클래스 작성하기",
        },
        "INTERMEDIATE": {
            "score_range": "4-6",
            "description": "실무 시나리오 기반 실습",
            "example": "게시판 CRUD API 구현하기",
        },
        "ADVANCED": {
            "score_range": "7-10",
            "description": "복잡한 설계 및 최적화",
            "example": "대용량 트래픽을 위한 캐싱 전략 설계",
        },
    }
