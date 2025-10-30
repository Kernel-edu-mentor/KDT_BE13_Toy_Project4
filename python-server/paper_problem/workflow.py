from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict
import logging

from paper_problem.models import Problem
from paper_problem.utils.content_analyzer import content_analyzer
from paper_problem.utils.context_builder import context_builder
from paper_problem.generators.beginner import beginner_generator
from paper_problem.generators.intermediate import intermediate_generator
from paper_problem.generators.advanced import advanced_generator
from paper_problem.validators.problem_validator import problem_validator

logger = logging.getLogger(__name__)

class ProblemState(TypedDict):
    material_id: int
    difficulty: str
    problem_count: int
    learning_content: Dict
    context: str
    generated_problems: List[Problem]
    validated_problems: List[Problem]
    rejection_reasons: List[str]

#노드1: 학습 내용 분석
async def analyze_content_node(state: ProblemState) -> dict:
    """학습자료에서 핵심 내용 추출"""
    material_id = state["material_id"]
    difficulty = state["difficulty"]

    logger.info(f"Analyzing content for {difficulty} problems")

    #학습 내용 분석
    analysis = await content_analyzer.analyze_material(
        material_id=material_id,
        difficulty=difficulty
    )

    return {"learning_content": analysis}

#노드2: 컨텍스트 구성
async def build_context_node(state: ProblemState) -> dict:
    """문제 생성을 위한 컨텍스트 구성"""
    learning_content = state["learning_content"]
    difficulty = state["difficulty"]

    documents = learning_content.get("documents", [])

    #컨텍스트 구성
    context = context_builder.build_context(
        documents=documents,
        difficulty=difficulty
    )

    logger.info(f"Built context: {len(context)} chatacters")

    return {"context": context}

#노드3: 문제 생성
async def generate_problems_node(state: ProblemState) -> dict:
    """난이도별 문제 생성"""
    difficulty = state["difficulty"]
    context = state["context"]
    problem_count = state["problem_count"]

    logger.info(f"Generating {problem_count} {difficulty} problems")

    #난이도별 생성기 선택
    if difficulty == "BEGINNER":
        problems = await beginner_generator.generate(context, problem_count)
    elif difficulty == "INTERMEDIATE":
        problems = await intermediate_generator.generate(context, problem_count)
    else:  #ADVANCED
        problems = await advanced_generator.generate(context, problem_count)

    return {"generated_problems": problems}

#노드4: 문제 검증
async def validate_problems_node(state: ProblemState) -> dict:
    """생성된 문제 검증 및 필터링"""
    generated_problems = state["generated_problems"]
    difficulty = state["difficulty"]

    logger.info(f"Validating {len(generated_problems)} problems")

    #검증
    validated_problems, rejection_reasons = problem_validator.filter_valid_problems(
        problems=generated_problems,
        difficulty=difficulty
    )

    logger.info(f"Validated: {len(validated_problems)}/{len(generated_problems)} problems")

    return {
        "validated_problems": validated_problems,
        "rejection_reasons": rejection_reasons
    }

#노드5: 재생성 판단
def should_regenerate(state: ProblemState) -> str:
    """문제가 부족하면 재생성"""
    validated_count = len(state["validated_problems"])
    required_count = state["problem_count"]

    if validated_count < required_count:
        logger.warning(f"Only {validated_count}/{required_count} problems valid. Regenerating...")
        return "regenerate"
    else:
        return "end"
    
#워크플로우 생성
def create_problem_workflow():
    graph = StateGraph(ProblemState)

    #노드 추가
    graph.add_node("analyze", analyze_content_node)
    graph.add_node("build_context", build_context_node)
    graph.add_node("generate", generate_problems_node)
    graph.add_node("validate", validate_problems_node)

    #엣지
    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "build_context")
    graph.add_edge("build_context", "generate")
    graph.add_edge("generate", "validate")

    #조건부 엣지(재생성 판단)
    graph.add_conditional_edges(
        "validate",
        should_regenerate,
        {
            "regenerate": "generate",   #다시 생성
            "end": END
        }
    )

    return graph.compile()

problem_workflow = create_problem_workflow()
