# team2_problem/api.py
from fastapi import APIRouter, HTTPException
from paper_problem.models import ProblemRequest, ProblemResponse
from paper_problem.workflow import problem_workflow

router = APIRouter()


@router.post("/generate", response_model=ProblemResponse)
async def generate_problems(request: ProblemRequest):
    """난이도별 문제 생성"""

    try: 
        result = await problem_workflow.ainvoke(
            {
                "material_id": request.material_id,
                "difficulty": request.difficulty,
                "problem_count": request.problem_count,
            }
        )

        validated_problems = result["validated_problems"]

        if not validated_problems:
            raise HTTPException(
                status_code=500, detail="Failed to generate valid problems"
            )

        return ProblemResponse(
            problems=validated_problems,
            difficulty=request.difficulty,
            generated_count=len(validated_problems),
            rejected_count=len(result["rejection_reasons"]),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
