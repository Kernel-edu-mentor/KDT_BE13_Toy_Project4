# paper_problem/graders/coding_grader.py
from paper_problem.models import Problem
from paper_problem.graders.grader_rubric import build_rubric_report
from typing import Dict, List
import logging
import time
import signal
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """코드 실행 타임아웃 예외"""
    pass


@contextmanager
def time_limit(seconds: int):
    """코드 실행 시간 제한"""
    def signal_handler(signum, frame):
        raise TimeoutException(f"Code execution timed out after {seconds} seconds")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


class CodingGrader:
    """코딩 문제 루브릭 기반 채점"""

    def __init__(self):
        self.default_timeout = 5  # 5초 제한

    async def grade(self, problem: Problem, user_code: str) -> Dict:
        """
        코딩 문제 채점

        1. test_cases 실행 (정확성 검증)
        2. grader_rubric 기반 5가지 기준 평가
        3. 종합 점수 계산 (0-100)

        Args:
            problem: 문제 객체 (test_cases 포함)
            user_code: 사용자 제출 코드

        Returns:
            {
                "is_correct": bool,
                "score": int (0-100),
                "feedback": str,
                "rubric_scores": dict,
                "test_results": list
            }
        """

        logger.info(f"Grading CODING: {problem.question[:50]}...")

        # 1단계: test_cases 실행
        test_results, pass_ratio, total_runtime, had_exception = self._run_test_cases(
            user_code, problem.test_cases
        )

        # 2단계: 루브릭 평가
        rubric_report = build_rubric_report(
            code=user_code,
            pass_ratio=pass_ratio,
            runtime_sec=total_runtime,
            time_limit_sec=self.default_timeout,
            had_exception=had_exception
        )

        # 3단계: 점수 계산 (루브릭 총점 10점 만점 → 100점 만점)
        rubric_total = sum(
            rubric_report[key]["score"]
            for key in ["accuracy", "efficiency", "code_quality", "exception_handling", "logical_reasoning"]
        )
        max_rubric_score = 10  # 5개 항목 × 2점
        final_score = int((rubric_total / max_rubric_score) * 100)

        # 4단계: 정답 여부 판단 (모든 테스트 통과 + 품질 기준 충족)
        is_correct = (pass_ratio >= 0.999 and rubric_total >= 8)  # 80% 이상

        # 5단계: 피드백 생성
        feedback = self._generate_feedback(rubric_report, test_results, is_correct)

        logger.info(f"Grading result: score={final_score}, is_correct={is_correct}, rubric_total={rubric_total}/10")

        return {
            "is_correct": is_correct,
            "score": final_score,
            "feedback": feedback,
            "rubric_scores": rubric_report,
            "test_results": test_results
        }

    def _run_test_cases(self, code: str, test_cases: List[Dict]) -> tuple:
        """
        test_cases 실행

        Returns:
            (test_results, pass_ratio, total_runtime, had_exception)
        """

        if not test_cases:
            logger.warning("No test cases provided")
            return [], 0.0, 0.0, False

        results = []
        total_runtime = 0.0
        had_exception = False

        for idx, test in enumerate(test_cases):
            try:
                start_time = time.time()

                # 코드 실행 (제한된 환경)
                output = self._execute_code_safely(
                    code=code,
                    input_data=test.get("input", {}),
                    timeout=self.default_timeout
                )

                runtime = time.time() - start_time
                total_runtime += runtime

                expected = test.get("expected_output")
                passed = (output == expected)

                results.append({
                    "test_id": idx + 1,
                    "input": test.get("input"),
                    "expected": expected,
                    "actual": output,
                    "passed": passed,
                    "runtime_sec": round(runtime, 3)
                })

            except TimeoutException as e:
                logger.warning(f"Test {idx+1} timeout: {e}")
                had_exception = True
                results.append({
                    "test_id": idx + 1,
                    "input": test.get("input"),
                    "error": str(e),
                    "passed": False
                })

            except Exception as e:
                logger.warning(f"Test {idx+1} error: {e}")
                had_exception = True
                results.append({
                    "test_id": idx + 1,
                    "input": test.get("input"),
                    "error": str(e),
                    "passed": False
                })

        # 통과율 계산
        passed_count = sum(1 for r in results if r.get("passed", False))
        pass_ratio = passed_count / len(results) if results else 0.0

        return results, pass_ratio, total_runtime, had_exception

    def _execute_code_safely(self, code: str, input_data: Dict, timeout: int) -> any:
        """
        코드 안전 실행 (제한된 환경)

        보안 고려사항:
        - 위험한 빌트인 함수 차단 (eval, exec, open, import 등)
        - timeout 설정
        - globals/locals 제한
        """

        # 안전한 빌트인 함수만 허용
        safe_builtins = {
            "abs": abs, "all": all, "any": any, "bool": bool,
            "dict": dict, "enumerate": enumerate, "filter": filter,
            "float": float, "int": int, "len": len, "list": list,
            "map": map, "max": max, "min": min, "range": range,
            "reversed": reversed, "round": round, "set": set,
            "sorted": sorted, "str": str, "sum": sum, "tuple": tuple,
            "zip": zip, "True": True, "False": False, "None": None
        }

        # 코드 실행 환경
        exec_globals = {"__builtins__": safe_builtins}
        exec_locals = {}

        try:
            # 타임아웃과 함께 코드 실행
            with time_limit(timeout):
                # 1. 사용자 코드 실행 (함수 정의)
                exec(code, exec_globals, exec_locals)

                # 2. 정의된 함수 찾기 (첫 번째 함수 가정)
                func_name = None
                for name, obj in exec_locals.items():
                    if callable(obj) and not name.startswith("_"):
                        func_name = name
                        break

                if not func_name:
                    raise ValueError("No function defined in code")

                # 3. 함수 호출
                user_func = exec_locals[func_name]

                # input_data가 딕셔너리면 키워드 인자로, 리스트면 위치 인자로
                if isinstance(input_data, dict):
                    result = user_func(**input_data)
                elif isinstance(input_data, list):
                    result = user_func(*input_data)
                else:
                    result = user_func(input_data)

                return result

        except TimeoutException:
            raise
        except Exception as e:
            raise RuntimeError(f"Execution error: {str(e)}")

    def _generate_feedback(self, rubric_report: Dict, test_results: List[Dict], is_correct: bool) -> str:
        """종합 피드백 생성"""

        feedback_parts = []

        # 정답 여부
        if is_correct:
            feedback_parts.append("✅ 정답입니다!")
        else:
            feedback_parts.append("❌ 코드에 개선이 필요합니다.")

        # 테스트 결과
        passed = sum(1 for r in test_results if r.get("passed", False))
        total = len(test_results)
        feedback_parts.append(f"\n📊 테스트 통과: {passed}/{total}")

        # 루브릭 피드백
        feedback_parts.append("\n📝 평가 기준:")
        for key in ["accuracy", "efficiency", "code_quality", "exception_handling", "logical_reasoning"]:
            item = rubric_report[key]
            score = item["score"]
            max_score = item["max_score"]
            label = item["label"]
            reason = item["reason"]
            feedback_parts.append(f"  - {label}: {score}/{max_score}점 - {reason}")

        # 실패한 테스트 케이스 상세
        failed_tests = [r for r in test_results if not r.get("passed", False)]
        if failed_tests:
            feedback_parts.append("\n⚠️ 실패한 테스트:")
            for test in failed_tests[:3]:  # 최대 3개만 표시
                if "error" in test:
                    feedback_parts.append(f"  - Test {test['test_id']}: {test['error']}")
                else:
                    feedback_parts.append(
                        f"  - Test {test['test_id']}: "
                        f"입력={test.get('input')}, "
                        f"기대값={test.get('expected')}, "
                        f"실제값={test.get('actual')}"
                    )

        return "\n".join(feedback_parts)


coding_grader = CodingGrader()
