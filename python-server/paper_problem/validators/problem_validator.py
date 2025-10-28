# team2_problem/validators/problem_validator.py
from team2_problem.models import Problem
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class ProblemValidator:
    def validate(self, problem: Problem, difficulty: str) -> Tuple[bool, str]:
        """문제 유효성 검증"""

        if not problem.question or len(problem.question) < 50:
            return False, "Question too short"

        if not problem.answer or len(problem.answer) < 20:
            return False, "Answer too short"

        if len(problem.hints) < 2:
            return False, "Need at least 2 hints"

        difficulty_ranges = {
            "BEGINNER": (1, 3),
            "INTERMEDIATE": (4, 6),
            "ADVANCED": (7, 10),
        }

        min_score, max_score = difficulty_ranges[difficulty]
        if not (min_score <= problem.difficulty_score <= max_score):
            return False, f"Difficulty score must be {min_score}-{max_score}"

        return True, "Valid"

    def filter_valid_problems(
        self, problems: List[Problem], difficulty: str
    ) -> Tuple[List[Problem], List[str]]:
        """유효한 문제만 필터링"""

        valid_problems = []
        rejection_reasons = []

        for problem in problems:
            is_valid, reason = self.validate(problem, difficulty)
            if is_valid:
                valid_problems.append(problem)
            else:
                rejection_reasons.append(reason)

        return valid_problems, rejection_reasons


problem_validator = ProblemValidator()
