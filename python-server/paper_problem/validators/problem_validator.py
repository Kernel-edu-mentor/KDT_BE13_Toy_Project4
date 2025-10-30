from paper_problem.models import Problem
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class ProblemValidator:
    """생성된 문제 검증"""

    def validate(self, problem: Problem, difficulty: str) -> Tuple[bool, str]:
        """문제 유효성 검증"""

        #1. 필수 필드 검증
        if not problem.question or len(problem.question) < 50:
            return False, "Question too short(minimum 50 characters)"

        if not problem.answer or len(problem.answer) < 20:
            return False, "Answer too short(minimum 20 characters)"

        if len(problem.hints) < 2:
            return False, "Need at least 2 hints"

        #2. 난이도 점수 검증
        difficulty_ranges = {
            "BEGINNER": (1, 3),
            "INTERMEDIATE": (4, 6),
            "ADVANCED": (7, 10)
        }

        min_score, max_score = difficulty_ranges[difficulty]
        if not (min_score <= problem.difficulty_score <= max_score):
            return False, f"Difficulty score must be between {min_score}-{max_score}"

        #3. 코딩 문제 검증
        if problem.problem_type == "CODING":
            if not problem.test_cases or len(problem.test_cases) == 0:
                return False, "CODING problems need test cases"
            
            #테스트 케이스 구조 검증
            for tc in problem.test_cases:
                if 'input' not in tc or 'expected' not in tc:
                    return False, "Test case needs 'input' and 'expected' fields"
                
        #4. 답변 품질 검증
        if "TODO" in problem.answer or "..." in problem.answer:
            return False, "Answer contains placeholder text"

        return True, "Valid"

    def filter_valid_problems(
        self,
        problems: List[Problem],
        difficulty: str
    ) -> Tuple[List[Problem], List[str]]:
        """유효한 문제만 필터링"""

        valid_problems = []
        rejection_reasons = []

        for problem in problems:
            is_valid, reason = self.validate(problem, difficulty)
            
            if is_valid:
               valid_problems.append(problem)
               logger.info(f"✅Valid problem: {problem.question[:50]}...")
            else:
                rejection_reasons.append(reason)
                logger.warning(f"❌ Rejected: {reason}")

        return valid_problems, rejection_reasons

problem_validator = ProblemValidator()