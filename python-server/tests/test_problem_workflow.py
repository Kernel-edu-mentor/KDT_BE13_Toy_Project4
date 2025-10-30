#!/usr/bin/env python3
"""테스트 프레임워크 없이 문제 워크플로우를 빠르게 검증하는 스크립트."""

from __future__ import annotations

import asyncio
import inspect
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def ensure_pydantic():
    try:
        from pydantic import BaseModel  # type: ignore  # noqa: F401
        return
    except Exception:
        pass

    import types

    module = types.ModuleType("pydantic")

    class BaseModel:  # type: ignore
        def __init__(self, **data):
            for key, value in data.items():
                setattr(self, key, value)

    module.BaseModel = BaseModel
    sys.modules["pydantic"] = module


ensure_pydantic()


def ensure_config():
    if "config" in sys.modules:
        return

    import types

    module = types.ModuleType("config")

    class StubSettings:
        def __init__(self):
            self.UPSTAGE_API_KEY = "stub-key"
            self.CHROMA_HOST = "localhost"
            self.CHROMA_PORT = 8001
            self.UPLOAD_DIR = str(PROJECT_ROOT / "uploads")
            self.CACHE_SIZE = 4

    module.settings = StubSettings()
    sys.modules["config"] = module


ensure_config()


def ensure_langgraph():
    try:
        from langgraph.graph import StateGraph  # type: ignore  # noqa: F401
        return
    except Exception:
        pass

    import types

    module = types.ModuleType("langgraph.graph")

    START = "__start__"
    END = "__end__"

    class CompiledGraph:
        def __init__(self, nodes, edges, conditionals):
            self._nodes = nodes
            self._edges = edges
            self._conditionals = conditionals

        async def ainvoke(self, state):
            data = dict(state)
            current = START
            while True:
                next_nodes = self._edges.get(current, [])
                if not next_nodes:
                    break
                next_node = next_nodes[0]
                if next_node == END:
                    break
                node_fn = self._nodes[next_node]
                result = node_fn(data)
                if inspect.isawaitable(result):
                    result = await result
                if not isinstance(result, dict):
                    raise ValueError(f"Node '{next_node}' returned non-dict result: {result!r}")
                data.update(result)
                conditional = self._conditionals.get(next_node)
                if conditional:
                    branch = conditional(data)
                    next_node = conditional.branches.get(branch, END)
                current = next_node
            return data

    class _Conditional:
        def __init__(self, selector, branches):
            self.selector = selector
            self.branches = branches

        def __call__(self, state):
            return self.selector(state)

    class StateGraph:
        def __init__(self, state_type):
            self.state_type = state_type
            self._nodes = {}
            self._edges = {}
            self._conditionals = {}

        def add_node(self, name, func):
            self._nodes[name] = func

        def add_edge(self, source, target):
            self._edges.setdefault(source, []).append(target)

        def add_conditional_edges(self, source, selector, branches):
            self._conditionals[source] = _Conditional(selector, branches)
            self._edges.setdefault(source, [])

        def compile(self):
            return CompiledGraph(self._nodes, self._edges, self._conditionals)

    module.StateGraph = StateGraph
    module.START = START
    module.END = END
    sys.modules["langgraph.graph"] = module


ensure_langgraph()


def ensure_langchain():
    import types

    schema_module = sys.modules.get("langchain.schema")
    if schema_module is None:
        schema_module = types.ModuleType("langchain.schema")
        sys.modules["langchain.schema"] = schema_module

    if not hasattr(schema_module, "HumanMessage"):
        class HumanMessage:
            def __init__(self, content: str):
                self.content = content

        schema_module.HumanMessage = HumanMessage  # type: ignore[attr-defined]

    module = types.ModuleType("langchain_upstage")

    class _StubLLMResponse:
        def __init__(self, content: str):
            self.content = content

    class ChatUpstage:
        def __init__(self, api_key: str, model: str, temperature: float = 0.3):
            self.api_key = api_key
            self.model = model
            self.temperature = temperature
            self._history: List[str] = []

        async def ainvoke(self, messages):
            prompt = messages[-1].content if messages else ""
            self._history.append(prompt)
            # 기본적으로 간단한 문제 한 세트를 돌려주도록 구성
            return _StubLLMResponse(
                """[
  {
    "question": "Stub question long enough to satisfy validation requirements about programming concepts and their explanations.",
    "answer": "Stub answer that exceeds the minimum character threshold for answers and references the context.",
    "hints": ["Consider stub logic", "Remember stub validation."],
    "difficulty_score": 2,
    "problem_type": "SHORT_ANSWER"
  }
]"""
            )

    class UpstageEmbeddings:
        def __init__(self, api_key: str, model: str):
            self.api_key = api_key
            self.model = model

        async def aembed_query(self, text: str):
            return [0.0]

        async def aembed_documents(self, texts: List[str]):
            return [[0.0] for _ in texts]

    class UpstageDocumentParseLoader:
        def __init__(self, file_path: str, api_key: str, split: str = "page"):
            self.file_path = file_path
            self.api_key = api_key
            self.split = split

        def load(self):
            return []

    module.ChatUpstage = ChatUpstage
    module.UpstageEmbeddings = UpstageEmbeddings
    module.UpstageDocumentParseLoader = UpstageDocumentParseLoader
    sys.modules["langchain_upstage"] = module


ensure_langchain()


import paper_problem.workflow as workflow  # noqa: E402
from paper_problem.models import Problem  # noqa: E402


def make_problem(**overrides: Any) -> Problem:
    payload: Dict[str, Any] = {
        "question": "워크플로우 검증이 어떻게 동작해야 하는지 50자 이상으로 충분히 설명하는 예시 질문입니다.",
        "answer": "이 답변은 최소 요구 글자 수 조건을 여유 있게 충족합니다.",
        "hints": [
            "검증 기준을 떠올려 보세요.",
            "힌트를 충분히 제공했는지 확인하세요.",
        ],
        "difficulty_score": overrides.pop("difficulty_score", 2),
        "problem_type": overrides.pop("problem_type", "SHORT_ANSWER"),
        "test_cases": overrides.pop("test_cases", []),
    }
    payload.update(overrides)
    return Problem(**payload)


class StubAnalyzer:
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    async def analyze_material(self, *, material_id: int, difficulty: str) -> Dict[str, Any]:
        self.calls.append({"material_id": material_id, "difficulty": difficulty})
        return {"documents": [{"content": "stub document", "page": 1}], "marker": "analyzer"}


class StubContextBuilder:
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def build_context(self, *, documents: List[Dict[str, Any]], difficulty: str, max_tokens: int = 3000) -> str:
        self.calls.append({"documents": documents, "difficulty": difficulty, "max_tokens": max_tokens})
        return f"ctx-{difficulty.lower()}-{len(documents)}"


class StubGenerator:
    def __init__(self, name: str):
        self.name = name
        self.calls: List[Dict[str, Any]] = []

    async def generate(self, context: str, problem_count: int) -> List[Problem]:
        self.calls.append({"context": context, "problem_count": problem_count})
        return [make_problem(question=f"{self.name}-{i}") for i in range(problem_count)]


@contextmanager
def patched_workflow(**attrs):
    originals = {}
    try:
        for key, value in attrs.items():
            originals[key] = getattr(workflow, key)
            setattr(workflow, key, value)
        yield
    finally:
        for key, value in originals.items():
            setattr(workflow, key, value)


validator = workflow.problem_validator
TESTS = []


def test(name):
    def decorator(func):
        TESTS.append((name, func))
        return func

    return decorator


@test("analyze_content_node가 분석 결과를 반환한다")
async def _():
    analyzer = StubAnalyzer()
    state = {
        "material_id": 101,
        "difficulty": "BEGINNER",
        "problem_count": 2,
        "learning_content": {},
        "context": "",
        "generated_problems": [],
        "validated_problems": [],
        "rejection_reasons": [],
    }
    with patched_workflow(content_analyzer=analyzer):
        result = await workflow.analyze_content_node(state)
    assert analyzer.calls == [{"material_id": 101, "difficulty": "BEGINNER"}]
    assert result["learning_content"]["marker"] == "analyzer"


@test("build_context_node가 context_builder에 의존한다")
async def _():
    builder = StubContextBuilder()
    state = {
        "material_id": 0,
        "difficulty": "ADVANCED",
        "problem_count": 1,
        "learning_content": {"documents": [{"content": "advanced doc"}]},
        "context": "",
        "generated_problems": [],
        "validated_problems": [],
        "rejection_reasons": [],
    }
    with patched_workflow(context_builder=builder):
        result = await workflow.build_context_node(state)
    assert builder.calls, "context_builder가 호출되어야 합니다."
    assert result["context"].startswith("ctx-advanced")


def generator_state(difficulty: str, context: str = "stub-context", problem_count: int = 2):
    return {
        "material_id": 0,
        "difficulty": difficulty,
        "problem_count": problem_count,
        "learning_content": {},
        "context": context,
        "generated_problems": [],
        "validated_problems": [],
        "rejection_reasons": [],
    }


@test("generate_problems_node가 초급 생성기를 호출한다")
async def _():
    gen = StubGenerator("beginner")
    with patched_workflow(beginner_generator=gen):
        result = await workflow.generate_problems_node(generator_state("BEGINNER"))
    assert gen.calls == [{"context": "stub-context", "problem_count": 2}]
    assert all(isinstance(p, Problem) for p in result["generated_problems"])


@test("generate_problems_node가 중급 생성기를 호출한다")
async def _():
    gen = StubGenerator("intermediate")
    with patched_workflow(intermediate_generator=gen):
        state = generator_state("INTERMEDIATE", problem_count=3)
        result = await workflow.generate_problems_node(state)
    assert gen.calls == [{"context": "stub-context", "problem_count": 3}]
    assert len(result["generated_problems"]) == 3


@test("generate_problems_node가 고급 생성기를 호출한다")
async def _():
    gen = StubGenerator("advanced")
    with patched_workflow(advanced_generator=gen):
        state = generator_state("ADVANCED")
        result = await workflow.generate_problems_node(state)
    assert gen.calls == [{"context": "stub-context", "problem_count": 2}]
    assert result["generated_problems"][0].question.startswith("advanced-")


@test("validate_problems_node가 유효/무효 문제를 구분한다")
async def _():
    valid = make_problem(
        question="허용 길이를 넉넉히 넘기는 유효한 질문 예시입니다. 학습 내용을 토대로 장황하게 설명하여 최소 길이를 확실하게 충족합니다."
    )
    invalid = make_problem(answer="너무 짧음")
    state = {
        "material_id": 0,
        "difficulty": "BEGINNER",
        "problem_count": 2,
        "learning_content": {},
        "context": "",
        "generated_problems": [valid, invalid],
        "validated_problems": [],
        "rejection_reasons": [],
    }
    result = await workflow.validate_problems_node(state)
    assert result["validated_problems"] == [valid]
    assert result["rejection_reasons"], "무효 문제에 대한 탈락 사유가 필요합니다."


@test("should_regenerate가 문제 수 부족 시 재생성을 요청한다")
def _():
    state = generator_state("BEGINNER")
    state["validated_problems"] = [make_problem()]
    state["problem_count"] = 3
    assert workflow.should_regenerate(state) == "regenerate"


@test("should_regenerate가 충분한 문제를 확보하면 종료한다")
def _():
    state = generator_state("BEGINNER")
    state["validated_problems"] = [make_problem(), make_problem()]
    state["problem_count"] = 2
    assert workflow.should_regenerate(state) == "end"


async def run_tests():
    passed = 0
    failed = 0
    for name, func in TESTS:
        try:
            result = func()
            if inspect.isawaitable(result):
                await result
            print(f"[PASS] {name}")
            passed += 1
        except AssertionError as exc:
            print(f"[FAIL] {name}: {exc}")
            failed += 1
        except Exception as exc:
            print(f"[ERROR] {name}: {exc}")
            failed += 1
    total = passed + failed
    print(f"\nCompleted {total} checks -> {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def main():
    return asyncio.run(run_tests())


if __name__ == "__main__":
    sys.exit(main())
