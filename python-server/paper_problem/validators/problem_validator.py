from paper_problem.models import Problem
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class ProblemValidator:
    """생성된 문제 검증"""

    def validate(self, problem: Problem, difficulty: str) -> Tuple[bool, str]:
        """문제 유효성 검증 (난이도별 기준)"""

        # 난이도별 최소 길이 기준
        min_lengths = {
            "BEGINNER": {"question": 20, "answer": 5},      # 초급: 짧아도 OK
            "INTERMEDIATE": {"question": 40, "answer": 15},  # 중급: 보통
            "ADVANCED": {"question": 50, "answer": 30}       # 고급: 상세
        }

        min_q = min_lengths[difficulty]["question"]
        min_a = min_lengths[difficulty]["answer"]

        #1. 필수 필드 검증 (난이도별)
        if not problem.question or len(problem.question) < min_q:
            return False, f"Question too short(minimum {min_q} characters for {difficulty})"

        if not problem.answer or len(problem.answer) < min_a:
            return False, f"Answer too short(minimum {min_a} characters for {difficulty})"

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