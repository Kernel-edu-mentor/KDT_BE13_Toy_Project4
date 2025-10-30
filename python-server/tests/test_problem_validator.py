#!/usr/bin/env python3
"""테스트 프레임워크 없이 ProblemValidator 동작을 살펴보는 스크립트."""

from __future__ import annotations

import sys
from pathlib import Path

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


from paper_problem.models import Problem  # noqa: E402
from paper_problem.validators.problem_validator import ProblemValidator  # noqa: E402


def make_problem(**overrides):
    """기본적으로 유효한 문제 데이터를 만들고 테스트용 수정값을 덮어쓴다."""
    base_payload = {
        "question": "이 질문은 예시 문제 설명을 50자 이상으로 충분히 풀어쓴 내용이며 학습 포인트를 자세히 묘사합니다.",
        "answer": "이 답변은 20자 제한을 넉넉하게 넘어서는 충분한 길이를 갖습니다.",
        "hints": [
            "첫 번째 힌트는 방향을 제시합니다.",
            "두 번째 힌트는 정답 범위를 좁혀 줍니다.",
        ],
        "difficulty_score": 2,
        "problem_type": "SHORT_ANSWER",
        "test_cases": [],
    }
    base_payload.update(overrides)
    return Problem(**base_payload)


validator = ProblemValidator()
TESTS = []


def test(name):
    def decorator(func):
        TESTS.append((name, func))
        return func

    return decorator


@test("BEGINNER 난이도 유효 문제는 통과한다")
def _():
    problem = make_problem()
    is_valid, reason = validator.validate(problem, "BEGINNER")
    assert is_valid, f"expected valid result, got: {reason}"


@test("질문 길이가 짧으면 거절된다")
def _():
    problem = make_problem(question="Too short?")
    is_valid, reason = validator.validate(problem, "BEGINNER")
    assert not is_valid and "Question too short" in reason, f"unexpected outcome: {is_valid}, {reason}"


@test("답변 길이가 짧으면 거절된다")
def _():
    problem = make_problem(answer="short answer")
    is_valid, reason = validator.validate(problem, "BEGINNER")
    assert not is_valid and "Answer too short" in reason, f"unexpected outcome: {is_valid}, {reason}"


@test("힌트가 부족하면 거절된다")
def _():
    problem = make_problem(hints=["Only hint"])
    is_valid, reason = validator.validate(problem, "BEGINNER")
    assert not is_valid and "Need at least 2 hints" in reason, f"unexpected outcome: {is_valid}, {reason}"


@test("난이도 점수가 범위보다 낮으면 거절된다")
def _():
    problem = make_problem(difficulty_score=0)
    is_valid, reason = validator.validate(problem, "BEGINNER")
    assert not is_valid and "Difficulty score must be between 1-3" in reason, f"unexpected outcome: {is_valid}, {reason}"


@test("난이도 점수가 범위보다 높으면 거절된다")
def _():
    problem = make_problem(difficulty_score=7)
    is_valid, reason = validator.validate(problem, "BEGINNER")
    assert not is_valid and "Difficulty score must be between 1-3" in reason, f"unexpected outcome: {is_valid}, {reason}"


@test("코딩 문제에 테스트 케이스가 없으면 거절된다")
def _():
    problem = make_problem(problem_type="CODING", difficulty_score=4, test_cases=[])
    is_valid, reason = validator.validate(problem, "INTERMEDIATE")
    assert not is_valid and "CODING problems need test cases" in reason, f"unexpected outcome: {is_valid}, {reason}"


@test("코딩 문제 테스트 케이스 구조가 틀리면 거절된다")
def _():
    problem = make_problem(
        problem_type="CODING",
        difficulty_score=5,
        test_cases=[{"input": "1 2", "output": "3"}],
    )
    is_valid, reason = validator.validate(problem, "INTERMEDIATE")
    assert not is_valid and "Test case needs 'input' and 'expected' fields" in reason, f"unexpected outcome: {is_valid}, {reason}"


@test("코딩 문제에 올바른 테스트 케이스가 있으면 통과한다")
def _():
    problem = make_problem(
        problem_type="CODING",
        difficulty_score=5,
        test_cases=[{"input": "1 2", "expected": "3"}],
    )
    is_valid, reason = validator.validate(problem, "INTERMEDIATE")
    assert is_valid, f"expected valid result, got: {reason}"


@test("답변에 placeholder가 있으면 거절된다")
def _():
    problem = make_problem(answer="TODO 나중에 채움... 충분히 길지만 TODO 표기 포함")
    is_valid, reason = validator.validate(problem, "BEGINNER")
    assert not is_valid and "Answer contains placeholder text" in reason, f"unexpected outcome: {is_valid}, {reason}"


def main():
    passed = 0
    failed = 0
    for name, func in TESTS:
        try:
            func()
            print(f"[PASS] {name}")
            passed += 1
        except AssertionError as exc:
            print(f"[FAIL] {name}: {exc}")
            failed += 1
        except Exception as exc:  # pragma: no cover - guardrail for unexpected errors
            print(f"[ERROR] {name}: {exc}")
            failed += 1
    total = passed + failed
    print(f"\nCompleted {total} checks -> {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
