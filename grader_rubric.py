"""Helper utilities for rubric-based scoring of code submissions.

The rubric covers five criteria:
- 정확성
- 효율성
- 코드 품질
- 예외 처리
- 논리적 사고

Each criterion is scored on a 0~2 scale (2 being best). The helpers here keep
all heuristics in one place so `grader.py` stays focused on running tests.
"""

from __future__ import annotations

from typing import Dict, Tuple

RubricScore = Tuple[int, str]

_MAX_RUBRIC_SCORE = 2

RUBRIC_PROMPT = """다음 다섯 가지 항목을 기준으로 파이썬 코드 제출물을 0~2점 범위에서 평가하라.\n- 정확성(Accuracy): 요구 기능이 완전히 동작하면 2점, 일부만 동작하면 1점, 실패하면 0점\n- 효율성(Efficiency): 실행 시간이 제한 대비 여유로우면 2점, 무난하면 1점, 비효율로 제한을 위협하면 0점\n- 코드 품질(Code Quality): 가독성·구조·안전성(위험한 빌트인 금지)을 종합적으로 평가\n- 예외 처리(Exception Handling): 오류 조건을 적절히 감지·처리하면 2점, 처리 문장은 없지만 실패가 없으면 1점, 실행 중 예외가 나면 0점\n- 논리적 사고(Logical Reasoning): 요구 분석과 해결 전략이 적절하면 2점, 일부만 충족하면 1점, 오답이면 0점\n평가는 항목별로 점수와 간단한 사유를 함께 제시하라."""


def _clamp_score(value: int) -> int:
    return max(0, min(_MAX_RUBRIC_SCORE, value))


def score_accuracy(pass_ratio: float) -> RubricScore:
    if pass_ratio >= 0.999:
        return 2, "모든 테스트 통과"
    if pass_ratio >= 0.5:
        return 1, "일부 테스트만 통과"
    if pass_ratio > 0.0:
        return 0, "대부분 테스트 실패"
    return 0, "테스트 실패"


def score_efficiency(runtime_sec: float, time_limit_sec: int) -> RubricScore:
    if time_limit_sec <= 0:
        return 2, "시간 제한 없음"
    ratio = runtime_sec / max(time_limit_sec, 1e-6)
    if ratio <= 0.5:
        return 2, "실행 시간이 여유롭습니다"
    if ratio <= 0.9:
        return 1, "실행 시간이 제한의 90% 이하"
    return 0, "실행 시간이 제한에 근접"


def score_code_quality(code: str) -> RubricScore:
    stripped = code.strip()
    if not stripped:
        return 0, "코드가 비어 있음"

    lines = stripped.splitlines()
    line_count = len(lines)
    long_lines = sum(1 for line in lines if len(line.rstrip()) > 120)
    uses_tabs = any(line.startswith("\t") for line in lines if line)
    contains_todo = "todo" in stripped.lower()
    contains_eval = any(token in code for token in ("eval(", "exec(", "globals()", "locals()"))

    if contains_eval:
        return 0, "위험한 빌트인 사용(eval/exec)"
    if contains_todo:
        return 1, "미완료 표기(TODO) 포함"
    if line_count > 400:
        return 0, "코드 길이가 과도함"

    score = 2
    reasons = []
    if line_count > 200:
        score = min(score, 1)
        reasons.append("라인 수가 많음")
    if long_lines:
        score = min(score, 1)
        reasons.append("120자 초과 라인 존재")
    if uses_tabs:
        score = min(score, 1)
        reasons.append("탭 들여쓰기 사용")

    if score == 2:
        reason = "가독성 양호"
    elif reasons:
        reason = ", ".join(reasons)
    else:
        reason = "가독성 저하 요인 발견"

    return _clamp_score(score), reason


def score_exception_handling(code: str, had_exception: bool) -> RubricScore:
    if had_exception:
        return 0, "테스트 중 예외 발생"

    lowered = code.lower()
    if "try:" in lowered or "except" in lowered or "raise" in lowered:
        return 2, "예외 상황을 명시적으로 처리"
    return 1, "예외 처리 문은 없지만 테스트를 통과"


def score_logical_reasoning(pass_ratio: float, quality_score: int) -> RubricScore:
    if pass_ratio >= 0.999 and quality_score == _MAX_RUBRIC_SCORE:
        return 2, "요구사항을 완전히 충족하는 논리"
    if pass_ratio > 0.0:
        return 1, "주요 논리는 작동하지만 개선 여지 있음"
    return 0, "논리 오류로 요구사항을 충족하지 못함"


def build_rubric_report(
    *,
    code: str,
    pass_ratio: float,
    runtime_sec: float,
    time_limit_sec: int,
    had_exception: bool,
) -> Dict[str, Dict[str, object]]:
    accuracy_score, accuracy_reason = score_accuracy(pass_ratio)
    efficiency_score, efficiency_reason = score_efficiency(runtime_sec, time_limit_sec)
    quality_score, quality_reason = score_code_quality(code)
    exception_score, exception_reason = score_exception_handling(code, had_exception)
    logical_score, logical_reason = score_logical_reasoning(pass_ratio, quality_score)

    report: Dict[str, Dict[str, object]] = {
        "accuracy": {
            "label": "정확성",
            "score": accuracy_score,
            "max_score": _MAX_RUBRIC_SCORE,
            "reason": accuracy_reason,
        },
        "efficiency": {
            "label": "효율성",
            "score": efficiency_score,
            "max_score": _MAX_RUBRIC_SCORE,
            "reason": efficiency_reason,
        },
        "code_quality": {
            "label": "코드 품질",
            "score": quality_score,
            "max_score": _MAX_RUBRIC_SCORE,
            "reason": quality_reason,
        },
        "exception_handling": {
            "label": "예외 처리",
            "score": exception_score,
            "max_score": _MAX_RUBRIC_SCORE,
            "reason": exception_reason,
        },
        "logical_reasoning": {
            "label": "논리적 사고",
            "score": logical_score,
            "max_score": _MAX_RUBRIC_SCORE,
            "reason": logical_reason,
        },
    }
    report["rubric_prompt"] = RUBRIC_PROMPT
    return report


__all__ = ["build_rubric_report", "RUBRIC_PROMPT"]
