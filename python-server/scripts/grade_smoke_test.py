#!/usr/bin/env python3
"""Quick smoke tests for the custom grader module.

Usage:
  python grade_smoke_test.py           # run built-in demo cases
  python grade_smoke_test.py -i cases.json  # run cases from JSON file

JSON file format (single object or list of objects):
[
  {
    "name": "optional label",
    "item": {...},
    "submission": {...}
  }
]

Each `item`/`submission` object mirrors the structure consumed by `grader.grade`.
This script outputs scoring details, including the rubric breakdown for
code-evaluation items. It is intended for manual verification rather than for
use in automated tests.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from grader import grade  # type: ignore

Case = Dict[str, Any]


def _load_cases(path: Path) -> List[Case]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, Mapping):
        return [dict(data)]
    if isinstance(data, Sequence):
        return [dict(item) for item in data]
    raise ValueError("JSON must describe an object or list of objects")


def _builtin_cases() -> List[Case]:
    return [
        {
            "name": "mcq-correct",
            "item": {
                "id": "demo-mcq",
                "type": "mcq",
                "answer_key": "C",
                "meta": {"case_insensitive": True, "strip_whitespace": True},
            },
            "submission": {
                "question_id": "demo-mcq",
                "answer": " c ",
            },
        },
        {
            "name": "short-similarity",
            "item": {
                "id": "demo-short",
                "type": "short",
                "prompt": "머신러닝 모델 과적합을 방지하는 방법을 한 가지 서술하시오.",
                "answer_key": "정규화",
                "meta": {
                    "case_insensitive": True,
                    "strip_whitespace": True,
                    "similarity_threshold": 0.8,
                },
            },
            "submission": {
                "question_id": "demo-short",
                "answer": "정규화 기법",
            },
        },
        {
            "name": "code-func-pass",
            "item": {
                "id": "demo-code",
                "type": "code-python",
                "prompt": "두 정수의 합을 반환하는 함수를 작성하시오.",
                "meta": {
                    "mode": "func",
                    "function_name": "solve",
                    "time_limit_sec": 3,
                },
                "tests": [
                    {"input": [2, 3], "output": 5},
                    {"input": [-10, 15], "output": 5},
                ],
            },
            "submission": {
                "question_id": "demo-code",
                "answer": "def solve(a, b):\n    return a + b\n",
                "language": "python",
            },
        },
        {
            "name": "code-func-fail",
            "item": {
                "id": "demo-code-fail",
                "type": "code-python",
                "prompt": "두 정수의 차를 반환하는 함수를 작성하시오.",
                "meta": {
                    "mode": "func",
                    "function_name": "solve",
                    "time_limit_sec": 3,
                },
                "tests": [
                    {"input": [5, 2], "output": 3},
                    {"input": [0, 7], "output": -7},
                ],
            },
            "submission": {
                "question_id": "demo-code-fail",
                "answer": "def solve(a, b):\n    return a + b\n",
                "language": "python",
            },
        },
    ]


def _print_rubric(details: Mapping[str, Any]) -> None:
    criteria = details.get("criteria")
    if not isinstance(criteria, Mapping):
        return

    prompt = criteria.get("rubric_prompt")
    if isinstance(prompt, str):
        print("    ─ Rubric Prompt ─")
        for line in prompt.splitlines():
            print(f"      {line}")

    print("    ─ Rubric Scores ─")
    for key, info in criteria.items():
        if key == "rubric_prompt":
            continue
        if not isinstance(info, Mapping):
            continue
        label = info.get("label", key)
        score = info.get("score")
        max_score = info.get("max_score")
        reason = info.get("reason", "")
        print(f"      {label}: {score}/{max_score} - {reason}")


def _run_case(case: Case) -> None:
    name = case.get("name", "unnamed-case")
    item = case.get("item")
    submission = case.get("submission")

    if not isinstance(item, Mapping) or not isinstance(submission, Mapping):
        raise ValueError(f"Case '{name}' must provide 'item' and 'submission' mappings")

    print(f"[CASE] {name}")
    result = grade(item, submission)
    print(f"  Passed: {result.get('passed')}")
    print(f"  Score : {result.get('score')} / {result.get('max_score')}")
    print(f"  Feedback: {result.get('feedback')}")

    details = result.get("details")
    if isinstance(details, Mapping):
        pass_ratio = details.get("pass_ratio")
        runtime_sec = details.get("runtime_sec")
        if pass_ratio is not None:
            print(f"  Pass ratio: {pass_ratio}")
        if runtime_sec is not None:
            print(f"  Runtime  : {runtime_sec} sec")
        _print_rubric(details)

    print()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run ad-hoc tests against grader.py")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        help="Optional path to JSON file containing test cases",
    )
    args = parser.parse_args(argv)

    if args.input:
        cases = _load_cases(args.input)
    else:
        cases = _builtin_cases()

    for case in cases:
        _run_case(case)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
