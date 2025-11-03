# -*- coding: utf-8 -*-
"""Simple grading engine for MCQ, short answers, and Python coding tasks.

This module keeps the public API (`grade`, `grade_mcq`, `grade_short`,
`grade_code_python`) compatible with the baseline version provided by the
user, but adds guardrails and small quality-of-life improvements:

- safer numeric detection with graceful fallbacks
- similarity threshold configurable via item metadata
- explicit handling for timeouts and malformed grader output
- capped feedback size for failing tests and stderr output
- rubric-style scoring details (정확성/효율성/코드 품질/예외 처리/논리적 사고)

The goal is to deliver the requested functionality without breaking the
original interface while making the implementation a bit more robust.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
import textwrap
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Sequence, TypedDict

from grader_rubric import build_rubric_report

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_SIMILARITY_THRESHOLD = 0.9
_DEFAULT_MAX_SCORE = 1.0
_MAX_STDERR_PREVIEW = 600
_MAX_TEXT_PREVIEW = 160
_MAX_FAILURE_DETAILS = 5


class GradeResult(TypedDict, total=False):
    score: float
    max_score: float
    passed: bool
    feedback: str
    details: Dict[str, Any]


# ---------------------------------------------------------------------------
# Common utilities
# ---------------------------------------------------------------------------

def _bool_meta(meta: Mapping[str, Any], key: str, default: bool) -> bool:
    value = meta.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return default


def _norm(value: Any, *, case_insensitive: bool, strip_whitespace: bool) -> str:
    if value is None:
        return ""
    text = str(value)
    if strip_whitespace:
        text = " ".join(text.split())
    if case_insensitive:
        text = text.lower()
    return text


def _is_number(value: Any) -> bool:
    if value is None:
        return False
    try:
        float(str(value).replace(",", ""))
        return True
    except (TypeError, ValueError):
        return False


def _as_number(value: Any) -> float:
    return float(str(value).replace(",", ""))


def _preview(text: Any, limit: int = _MAX_TEXT_PREVIEW) -> Any:
    if isinstance(text, str) and len(text) > limit:
        return text[: limit - 3] + "..."
    return text


# ---------------------------------------------------------------------------
# 1) Multiple choice grading
# ---------------------------------------------------------------------------

def grade_mcq(item: Mapping[str, Any], submission: Mapping[str, Any]) -> GradeResult:
    meta = item.get("meta", {}) if isinstance(item, Mapping) else {}
    case_insensitive = _bool_meta(meta, "case_insensitive", True)
    strip_whitespace = _bool_meta(meta, "strip_whitespace", True)

    gt = _norm(item.get("answer_key", ""), case_insensitive=case_insensitive, strip_whitespace=strip_whitespace)
    ans = _norm(submission.get("answer", ""), case_insensitive=case_insensitive, strip_whitespace=strip_whitespace)

    passed = gt == ans
    return {
        "score": _DEFAULT_MAX_SCORE if passed else 0.0,
        "max_score": _DEFAULT_MAX_SCORE,
        "passed": passed,
        "feedback": "정답입니다." if passed else f"오답입니다. 정답: {item.get('answer_key', '')}"
    }


# ---------------------------------------------------------------------------
# 2) Short answer grading (numbers with tolerance or string similarity)
# ---------------------------------------------------------------------------

def grade_short(item: Mapping[str, Any], submission: Mapping[str, Any], threshold: float = _DEFAULT_SIMILARITY_THRESHOLD) -> GradeResult:
    meta = item.get("meta", {}) if isinstance(item, Mapping) else {}
    try:
        threshold = float(meta.get("similarity_threshold", threshold))
    except (TypeError, ValueError):
        threshold = float(threshold)

    gt_raw = item.get("answer_key", "")
    ans_raw = submission.get("answer", "")

    if _is_number(gt_raw) and _is_number(ans_raw):
        try:
            tol = float(meta.get("numeric_tolerance", 0.0))
        except (TypeError, ValueError):
            tol = 0.0
        try:
            ok = math.isclose(_as_number(gt_raw), _as_number(ans_raw), rel_tol=tol, abs_tol=tol)
        except ValueError:
            ok = False
        return {
            "score": _DEFAULT_MAX_SCORE if ok else 0.0,
            "max_score": _DEFAULT_MAX_SCORE,
            "passed": ok,
            "feedback": "정답입니다." if ok else f"오답입니다. 정답: {gt_raw}"
        }

    case_insensitive = _bool_meta(meta, "case_insensitive", True)
    strip_whitespace = _bool_meta(meta, "strip_whitespace", True)

    gt = _norm(gt_raw, case_insensitive=case_insensitive, strip_whitespace=strip_whitespace)
    ans = _norm(ans_raw, case_insensitive=case_insensitive, strip_whitespace=strip_whitespace)

    similarity = SequenceMatcher(None, gt, ans).ratio() if gt or ans else 1.0
    passed = similarity >= threshold
    feedback = "정답입니다." if passed else f"유사도 {similarity:.2f}. 정답: {gt_raw}"

    return {
        "score": _DEFAULT_MAX_SCORE if passed else 0.0,
        "max_score": _DEFAULT_MAX_SCORE,
        "passed": passed,
        "feedback": feedback,
    }


# ---------------------------------------------------------------------------
# 3) Coding question grading (Python)
# ---------------------------------------------------------------------------

_RUNNERS: Dict[str, str] = {
    "func": textwrap.dedent(
        r"""
        import importlib.util
        import json
        import sys
        import traceback


        def load_user(path, func_name):
            spec = importlib.util.spec_from_file_location("user_code", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return getattr(mod, func_name)


        def main():
            user_path = sys.argv[1]
            func_name = sys.argv[2]
            tests = json.loads(sys.argv[3])
            function = load_user(user_path, func_name)
            results = []
            for test in tests:
                try:
                    args = test.get("input", [])
                    output = function(*args)
                    ok = output == test.get("output")
                    results.append({"ok": ok, "expected": test.get("output"), "got": output})
                except Exception as exc:  # pragma: no cover - user code failure path
                    results.append({"ok": False, "error": repr(exc)})
            print(json.dumps(results, ensure_ascii=False))


        if __name__ == "__main__":
            main()
        """
    ).strip(),
    "stdin": textwrap.dedent(
        r"""
        import json
        import subprocess
        import sys


        def normalize(text):
            text = text.strip("\n")
            lines = [line.rstrip() for line in text.splitlines()]
            return "\n".join(lines)


        def run_case(py_path, stdin_str, timeout_sec):
            return subprocess.run(
                [sys.executable, py_path],
                input=stdin_str,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_sec,
            )


        def main():
            user_path = sys.argv[1]
            tests = json.loads(sys.argv[2])
            timeout_sec = int(sys.argv[3])
            results = []
            for test in tests:
                try:
                    completed = run_case(user_path, test.get("stdin", ""), timeout_sec)
                    expected = test.get("stdout", "")
                    ok = normalize(completed.stdout) == normalize(expected)
                    case_result = {"ok": ok, "expected": expected, "got": completed.stdout}
                    if completed.stderr.strip():
                        case_result["stderr"] = completed.stderr
                    results.append(case_result)
                except subprocess.TimeoutExpired:  # pragma: no cover - runtime guardrail
                    results.append({"ok": False, "error": "TIMEOUT"})
                except Exception as exc:  # pragma: no cover - runtime guardrail
                    results.append({"ok": False, "error": repr(exc)})
            print(json.dumps(results, ensure_ascii=False))


        if __name__ == "__main__":
            main()
        """
    ).strip(),
}


def _write_temp_file(dir_path: Path, name: str, content: str) -> Path:
    path = dir_path / name
    path.write_text(content, encoding="utf-8")
    return path


def grade_code_python(item: Mapping[str, Any], submission: Mapping[str, Any]) -> GradeResult:
    meta = item.get("meta", {}) if isinstance(item, Mapping) else {}
    mode = meta.get("mode", "func")
    try:
        time_limit = int(meta.get("time_limit_sec", 2))
    except (TypeError, ValueError):
        time_limit = 2
    time_limit = max(time_limit, 1)
    func_name = meta.get("function_name", "solve")
    tests = item.get("tests", [])
    code = submission.get("answer", "")

    if not isinstance(tests, Sequence) or isinstance(tests, (str, bytes)) or not tests:
        return {
            "score": 0.0,
            "max_score": _DEFAULT_MAX_SCORE,
            "passed": False,
            "feedback": "테스트 케이스가 없습니다.",
        }

    if not isinstance(code, str) or not code.strip():
        return {
            "score": 0.0,
            "max_score": _DEFAULT_MAX_SCORE,
            "passed": False,
            "feedback": "제출된 코드가 비어 있습니다.",
        }

    runner_source = _RUNNERS.get(mode)
    if runner_source is None:
        return {
            "score": 0.0,
            "max_score": _DEFAULT_MAX_SCORE,
            "passed": False,
            "feedback": f"지원하지 않는 실행 모드: {mode}",
        }

    runtime_sec = 0.0

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        user_py = _write_temp_file(tmp_path, "user.py", code)
        runner_py = _write_temp_file(tmp_path, "runner.py", runner_source)

        if mode == "func":
            runner_args = [
                sys.executable,
                str(runner_py),
                str(user_py),
                func_name,
                json.dumps(tests, ensure_ascii=False),
            ]
        else:  # stdin
            runner_args = [
                sys.executable,
                str(runner_py),
                str(user_py),
                json.dumps(tests, ensure_ascii=False),
                str(time_limit),
            ]

        try:
            start = time.perf_counter()
            proc = subprocess.run(
                runner_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=time_limit,
                check=False,
            )
            runtime_sec = time.perf_counter() - start
        except subprocess.TimeoutExpired:
            return {
                "score": 0.0,
                "max_score": _DEFAULT_MAX_SCORE,
                "passed": False,
                "feedback": "채점기 실행 시간 초과",
            }

    if proc.returncode != 0:
        stderr_preview = _preview(proc.stderr, _MAX_STDERR_PREVIEW)
        feedback = "런타임 에러/타임아웃"
        if stderr_preview:
            feedback += f"\nSTDERR:\n{stderr_preview}"
        return {
            "score": 0.0,
            "max_score": _DEFAULT_MAX_SCORE,
            "passed": False,
            "feedback": feedback,
        }

    try:
        results = json.loads(proc.stdout.strip() or "[]")
    except json.JSONDecodeError:
        return {
            "score": 0.0,
            "max_score": _DEFAULT_MAX_SCORE,
            "passed": False,
            "feedback": "채점기 결과 파싱 실패",
        }

    if not isinstance(results, Sequence):
        return {
            "score": 0.0,
            "max_score": _DEFAULT_MAX_SCORE,
            "passed": False,
            "feedback": "채점기 결과 형식 오류",
        }

    total = len(results)
    passed_count = sum(1 for r in results if isinstance(r, Mapping) and r.get("ok"))
    score = passed_count / total if total else 0.0

    failures: List[str] = []
    for idx, case in enumerate(results, 1):
        if not isinstance(case, Mapping) or case.get("ok"):
            continue
        if "error" in case:
            failures.append(f"TC#{idx}: 예외 {case['error']}")
        else:
            expected = _preview(case.get("expected"))
            got = _preview(case.get("got"))
            failures.append(f"TC#{idx}: 기대={expected} / 실제={got}")
        if len(failures) >= _MAX_FAILURE_DETAILS:
            break

    feedback = "모든 테스트 통과" if passed_count == total else (" | ".join(failures) if failures else "일부 실패")

    had_exception = any(
        isinstance(case, Mapping) and ("error" in case)
        for case in results
    )

    rubric_details = build_rubric_report(
        code=code,
        pass_ratio=score,
        runtime_sec=runtime_sec,
        time_limit_sec=time_limit,
        had_exception=had_exception,
    )

    return {
        "score": round(score, 4),
        "max_score": _DEFAULT_MAX_SCORE,
        "passed": passed_count == total,
        "feedback": feedback,
        "details": {
            "criteria": rubric_details,
            "pass_ratio": round(score, 4),
            "runtime_sec": round(runtime_sec, 6),
        },
    }


# ---------------------------------------------------------------------------
# 4) Router
# ---------------------------------------------------------------------------

_HANDLER_MAP: Dict[str, Callable[[Mapping[str, Any], Mapping[str, Any]], GradeResult]] = {
    "mcq": grade_mcq,
    "short": grade_short,
    "code-python": grade_code_python,
}


def grade(item: Mapping[str, Any], submission: Mapping[str, Any]) -> GradeResult:
    handler = _HANDLER_MAP.get(item.get("type"))
    if handler is None:
        return {
            "score": 0.0,
            "max_score": _DEFAULT_MAX_SCORE,
            "passed": False,
            "feedback": f"지원하지 않는 유형: {item.get('type')}",
        }
    return handler(item, submission)


__all__ = [
    "grade",
    "grade_mcq",
    "grade_short",
    "grade_code_python",
]
