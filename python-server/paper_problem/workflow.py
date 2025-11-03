from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict
import logging, time

from paper_problem.models import Problem
from paper_problem.utils.content_analyzer import content_analyzer
from paper_problem.utils.context_builder import context_builder
from paper_problem.utils.topic_extractor import topic_extractor
from paper_problem.generators.beginner import beginner_generator
from paper_problem.generators.intermediate import intermediate_generator
from paper_problem.generators.advanced import advanced_generator
from paper_problem.validators.problem_validator import problem_validator

logger = logging.getLogger(__name__)

class ProblemState(TypedDict):
    material_id: int
    difficulty: str
    problem_count: int
    learning_description: str
    learning_topics: List[str]
    learning_content: Dict
    context: str
    generated_problems: List[Problem]
    validated_problems: List[Problem]
    rejection_reasons: List[str]
    retry_count: int

#노드1: 학습 내용 분석
async def analyze_content_node(state: ProblemState) -> dict:
    """학습자료에서 핵심 내용 추출"""
    material_id = state["material_id"]
    difficulty = state["difficulty"]
    learning_topics = state.get("learning_topics")
    learning_description = state.get("learning_description")

    logger.info(f"Analyzing content for {difficulty} problems")

    # 자연어 설명이 있고 토픽이 없으면 LLM으로 추출
    if learning_description and not learning_topics:
        logger.info(f"Extracting topics from description: {learning_description}")
        learning_topics = await topic_extractor.extract_topics(learning_description)
        logger.info(f"Extracted topics: {learning_topics}")

    #학습 내용 분석
    analysis = await content_analyzer.analyze_material(
        material_id=material_id,
        difficulty=difficulty,
        learning_topics=learning_topics
    )

    return {"learning_content": analysis}

#노드2: 컨텍스트 구성
async def build_context_node(state: ProblemState) -> dict:
    """문제 생성을 위한 컨텍스트 구성"""
    learning_content = state["learning_content"]
    difficulty = state["difficulty"]

    documents = learning_content.get("documents", [])
    documents_by_topic = learning_content.get("documents_by_topic")
    topics = learning_content.get("topics")

    #컨텍스트 구성 (토픽별 균등 분배)
    context = context_builder.build_context(
        documents=documents,
        difficulty=difficulty,
        documents_by_topic=documents_by_topic,
        topics=topics
    )

    logger.info(f"Built context: {len(context)} characters")

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
    existing_validated = state.get("validated_problems", [])
    retry_count = state.get("retry_count", 0)

    logger.info(f"Validating {len(generated_problems)} problems (retry: {retry_count})")

    #검증
    validated_problems, rejection_reasons = problem_validator.filter_valid_problems(
        problems=generated_problems,
        difficulty=difficulty
    )

    # 기존 검증된 문제에 추가
    all_validated = existing_validated + validated_problems

    logger.info(f"Validated: {len(all_validated)}/{state['problem_count']} problems total")

    return {
        "validated_problems": all_validated,
        "rejection_reasons": rejection_reasons,
        "retry_count": retry_count + 1
    }

#노드5: 재생성 판단
def should_regenerate(state: ProblemState) -> str:
    """문제가 부족하면 재생성 (최대 5회)"""
    start_time = time.time()

    validated_count = len(state.get("validated_problems", []))
    required_count = state["problem_count"]
    retry_count = state.get("retry_count", 0)

    MAX_RETRIES = 5

    # 충분한 문제 생성됨
    if validated_count >= required_count:
        logger.info(f"✅ Successfully generated {validated_count} problems")
        return "end"

    # 재시도 횟수 초과
    if retry_count >= MAX_RETRIES:
        logger.warning(f"⚠️ Max retries ({MAX_RETRIES}) reached. Stopping with {validated_count} problems.")
        return "end"

    # 재생성
    logger.warning(f"Only {validated_count}/{required_count} problems valid. Regenerating... (attempt {retry_count + 1}/{MAX_RETRIES})")

    generate_time = time.time() - start_time
    logger.info(f"Generate time: {generate_time:.3f}s")

    return "regenerate"
    
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
