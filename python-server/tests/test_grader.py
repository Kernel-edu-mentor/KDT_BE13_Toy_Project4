import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import grader


def test_grade_mcq_correct():
    item = {
        "type": "mcq",
        "answer_key": "B",
        "meta": {"case_insensitive": True, "strip_whitespace": True},
    }
    submission = {"answer": " b "}

    result = grader.grade_mcq(item, submission)

    assert result["passed"]
    assert result["score"] == 1.0


def test_grade_short_numeric_tolerance():
    item = {
        "type": "short",
        "answer_key": "3.1415",
        "meta": {"numeric_tolerance": 0.01},
    }
    submission = {"answer": "3.14"}

    result = grader.grade_short(item, submission)

    assert result["passed"]
    assert result["score"] == 1.0


def test_grade_short_similarity_threshold():
    item = {
        "type": "short",
        "answer_key": "Machine Learning",
        "meta": {"case_insensitive": True, "strip_whitespace": True, "similarity_threshold": 0.8},
    }
    submission = {"answer": "machine  learn"}

    result = grader.grade_short(item, submission)

    assert result["passed"]
    assert result["score"] == 1.0


def test_grade_code_python_func_mode_pass():
    item = {
        "type": "code-python",
        "meta": {"mode": "func", "function_name": "solve", "time_limit_sec": 5},
        "tests": [
            {"input": [2, 3], "output": 5},
            {"input": [10, -4], "output": 6},
        ],
    }
    submission = {
        "answer": "def solve(a, b):\n    return a + b\n",
    }

    result = grader.grade_code_python(item, submission)

    assert result["passed"]
    assert result["score"] == 1.0
    assert "details" in result
    criteria = result["details"]["criteria"]
    assert criteria["accuracy"]["score"] == 2
    assert criteria["efficiency"]["score"] >= 1
    assert isinstance(criteria["rubric_prompt"], str)
    assert "정확성" in criteria["rubric_prompt"]


def test_grade_code_python_func_mode_partial_fail():
    item = {
        "type": "code-python",
        "meta": {"mode": "func", "function_name": "solve", "time_limit_sec": 5},
        "tests": [
            {"input": [2, 2], "output": 4},
            {"input": [2, 3], "output": 5},
        ],
    }
    submission = {
        "answer": "def solve(a, b):\n    return a * b\n",
    }

    result = grader.grade_code_python(item, submission)

    assert not result["passed"]
    assert 0.0 < result["score"] < 1.0
    assert "TC#" in result["feedback"]
    criteria = result["details"]["criteria"]
    assert criteria["accuracy"]["score"] == 1
    assert criteria["logical_reasoning"]["score"] == 1


def test_grade_code_python_exception_rubric():
    item = {
        "type": "code-python",
        "meta": {"mode": "func", "function_name": "solve", "time_limit_sec": 3},
        "tests": [
            {"input": [10], "output": 5},
        ],
    }
    submission = {
        "answer": "def solve(x):\n    return 10 / 0\n",
    }

    result = grader.grade_code_python(item, submission)

    assert not result["passed"]
    criteria = result["details"]["criteria"]
    assert criteria["exception_handling"]["score"] == 0
    assert criteria["accuracy"]["score"] == 0
