#!/usr/bin/env python3
"""ProblemValidator behavior checks without relying on a testing framework."""

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
    """Create a baseline valid problem and apply any overrides used in tests."""
    base_payload = {
        "question": "What is the detailed explanation for the sample problem statement that easily exceeds fifty characters?",
        "answer": "This is a fully fleshed out answer that easily clears twenty characters.",
        "hints": [
            "Hint number one provides direction.",
            "Hint number two narrows down the answer.",
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


@test("valid BEGINNER problem passes")
def _():
    problem = make_problem()
    is_valid, reason = validator.validate(problem, "BEGINNER")
    assert is_valid, f"expected valid result, got: {reason}"


@test("short question rejected")
def _():
    problem = make_problem(question="Too short?")
    is_valid, reason = validator.validate(problem, "BEGINNER")
    assert not is_valid and "Question too short" in reason, f"unexpected outcome: {is_valid}, {reason}"


@test("short answer rejected")
def _():
    problem = make_problem(answer="short answer")
    is_valid, reason = validator.validate(problem, "BEGINNER")
    assert not is_valid and "Answer too short" in reason, f"unexpected outcome: {is_valid}, {reason}"


@test("insufficient hints rejected")
def _():
    problem = make_problem(hints=["Only hint"])
    is_valid, reason = validator.validate(problem, "BEGINNER")
    assert not is_valid and "Need at least 2 hints" in reason, f"unexpected outcome: {is_valid}, {reason}"


@test("difficulty score below range rejected")
def _():
    problem = make_problem(difficulty_score=0)
    is_valid, reason = validator.validate(problem, "BEGINNER")
    assert not is_valid and "Difficulty score must be between 1-3" in reason, f"unexpected outcome: {is_valid}, {reason}"


@test("difficulty score above range rejected")
def _():
    problem = make_problem(difficulty_score=7)
    is_valid, reason = validator.validate(problem, "BEGINNER")
    assert not is_valid and "Difficulty score must be between 1-3" in reason, f"unexpected outcome: {is_valid}, {reason}"


@test("coding problem missing test cases rejected")
def _():
    problem = make_problem(problem_type="CODING", difficulty_score=4, test_cases=[])
    is_valid, reason = validator.validate(problem, "INTERMEDIATE")
    assert not is_valid and "CODING problems need test cases" in reason, f"unexpected outcome: {is_valid}, {reason}"


@test("coding problem with malformed test case rejected")
def _():
    problem = make_problem(
        problem_type="CODING",
        difficulty_score=5,
        test_cases=[{"input": "1 2", "output": "3"}],
    )
    is_valid, reason = validator.validate(problem, "INTERMEDIATE")
    assert not is_valid and "Test case needs 'input' and 'expected' fields" in reason, f"unexpected outcome: {is_valid}, {reason}"


@test("coding problem with valid test cases passes")
def _():
    problem = make_problem(
        problem_type="CODING",
        difficulty_score=5,
        test_cases=[{"input": "1 2", "expected": "3"}],
    )
    is_valid, reason = validator.validate(problem, "INTERMEDIATE")
    assert is_valid, f"expected valid result, got: {reason}"


@test("placeholder answer rejected")
def _():
    problem = make_problem(answer="TODO fill in later...")
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
