"""
팀2: 문제 생성 모듈
난이도별 실습 문제 자동 생성 시스템을 제공합니다.
"""

try:
    from paper_problem.api import router as problem_router  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - 테스트 환경 대비
    problem_router = None

try:
    from paper_problem.workflow import problem_workflow  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - 테스트 환경 대비
    problem_workflow = None

__all__ = ['problem_router', 'problem_workflow']
