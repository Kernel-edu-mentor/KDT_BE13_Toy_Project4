# paper_problem/graders/answer_grader.py
from paper_problem.graders.short_answer_grader import short_answer_grader
from paper_problem.graders.coding_grader import coding_grader
from paper_problem.models import Problem
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class AnswerGrader:
    """문제 타입에 따라 적절한 채점기 선택"""

    def __init__(self):
        self.short_grader = short_answer_grader
        self.coding_grader = coding_grader

    async def grade(self, problem: Problem, user_answer: str) -> Dict:
        """
        문제 타입에 따라 채점

        Args:
            problem: 문제 객체
            user_answer: 사용자 답변 (SHORT_ANSWER) 또는 코드 (CODING)

        Returns:
            채점 결과 딕셔너리
        """

        logger.info(f"Grading problem_type={problem.problem_type}")

        if problem.problem_type == "SHORT_ANSWER":
            return await self.short_grader.grade(problem, user_answer)
        elif problem.problem_type == "CODING":
            return await self.coding_grader.grade(problem, user_answer)
        else:
            raise ValueError(f"Unknown problem_type: {problem.problem_type}")


# Singleton instance
answer_grader = AnswerGrader()
