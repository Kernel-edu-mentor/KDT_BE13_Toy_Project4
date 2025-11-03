from fastapi import APIRouter, HTTPException
from paper_problem.models import ProblemRequest, ProblemResponse
from paper_problem.workflow import problem_workflow
import logging, time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/problems", tags=["Problems"])


@router.post("/generate", response_model=ProblemResponse)
async def generate_problems(request: ProblemRequest):
    """난이도별 실습 문제 생성"""
    start_time = time.time()

    logger.info(
        f"Generating {request.problem_count} {request.difficulty} problems "
        f"for material {request.material_id}"
    )

    try:
        # Lang Graph 워크플로우 실행
        result = await problem_workflow.ainvoke(
            {
                "material_id": request.material_id,
                "difficulty": request.difficulty,
                "problem_count": request.problem_count,
                "learning_description": request.learning_description,
                "learning_topics": request.learning_topics,
                "retry_count": 0,
            }
        )

        validated_problems = result["validated_problems"]
        rejection_reasons = result["rejection_reasons"]

        response_time = int((time.time() - start_time) * 1000)
        logger.info("response_time : {response_time} ms")
        if not validated_problems:
            raise HTTPException(
                status_code=500, detail="Failed to generate valid problems"
            )

        return ProblemResponse(
            problems=validated_problems,
            difficulty=request.difficulty,
            generated_count=len(validated_problems),
            rejected_count=len(rejection_reasons),
            response_time_ms=response_time
        )

    except Exception as e:
        logger.error(f"Error generating problems : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/difficulties")
async def get_difficulty_info():
    """난이도별 정보 조회 (비전공자 기준)"""
    return {
        "BEGINNER": {
            "score_range": "1-3",
            "description": "용어 이해 & 개념 설명 (입문)",
            "code_length": "1-3줄 읽기/빈칸 채우기",
            "example": "Observer 패턴이란? / 다음 코드의 빈칸 채우기",
            "target": "비전공자 처음 학습",
        },
        "INTERMEDIATE": {
            "score_range": "4-6",
            "description": "기본 개념 구현 (기본 응용)",
            "code_length": "5-15줄 메소드 작성",
            "example": "Observer 클래스 작성하기 / update() 메소드 구현",
            "target": "개념 이해 후 코드 작성 연습",
        },
        "ADVANCED": {
            "score_range": "7-10",
            "description": "실무 시나리오 구현 (실무 응용)",
            "code_length": "20-40줄 전체 프로그램",
            "example": "Observer 패턴 전체 구현 / 실무 적용 사례 설명",
            "target": "여러 개념 결합한 실무 프로젝트",
        },
    }
