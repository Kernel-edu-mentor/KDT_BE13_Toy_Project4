# team2_problem/workflow.py
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict
from team2_problem.models import Problem
from shared.chroma_client import chroma_client
from team2_problem.generators.beginner import beginner_generator
from team2_problem.validators.problem_validator import problem_validator
import logging

logger = logging.getLogger(__name__)


class ProblemState(TypedDict):
    material_id: int
    difficulty: str
    problem_count: int
    learning_content: List[Dict]
    context: str
    generated_problems: List[Problem]
    validated_problems: List[Problem]
    rejection_reasons: List[str]


async def analyze_content_node(state: ProblemState) -> dict:
    """학습 내용 추출"""
    material_id = state["material_id"]
    difficulty = state["difficulty"]

    results = chroma_client.search(
        collection_name="learning_materials",
        query_texts=["기본 개념 예제"],
        n_results=5,
        filter_dict={"material_id": material_id},
    )

    learning_content = []
    for i in range(len(results["documents"][0])):
        learning_content.append(
            {
                "content": results["documents"][0][i],
                "page": results["metadatas"][0][i]["page"],
            }
        )

    return {"learning_content": learning_content}


async def build_context_node(state: ProblemState) -> dict:
    """컨텍스트 구성"""
    learning_content = state["learning_content"]

    context = "\n\n---\n\n".join(
        [f"[페이지 {c['page']}]\n{c['content']}" for c in learning_content]
    )

    return {"context": context}


async def generate_problems_node(state: ProblemState) -> dict:
    """문제 생성"""
    difficulty = state["difficulty"]
    context = state["context"]
    problem_count = state["problem_count"]

    if difficulty == "BEGINNER":
        problems = await beginner_generator.generate(context, problem_count)
    # elif INTERMEDIATE, ADVANCED...

    return {"generated_problems": problems}


async def validate_problems_node(state: ProblemState) -> dict:
    """문제 검증"""
    problems = state["generated_problems"]
    difficulty = state["difficulty"]

    validated, rejected = problem_validator.filter_valid_problems(problems, difficulty)

    return {"validated_problems": validated, "rejection_reasons": rejected}


def create_problem_workflow():
    graph = StateGraph(ProblemState)

    graph.add_node("analyze", analyze_content_node)
    graph.add_node("build_context", build_context_node)
    graph.add_node("generate", generate_problems_node)
    graph.add_node("validate", validate_problems_node)

    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "build_context")
    graph.add_edge("build_context", "generate")
    graph.add_edge("generate", "validate")
    graph.add_edge("validate", END)

    return graph.compile()


problem_workflow = create_problem_workflow()
