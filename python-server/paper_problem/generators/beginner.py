# paper_problem/generators/beginner.py
from paper_problem.generators.base_generator import BaseProblemGenerator
from paper_problem.models import Problem
from typing import List
import logging

logger = logging.getLogger(__name__)


class BeginnerProblemGenerator(BaseProblemGenerator):
    """초급 실습 문제 생성"""

    def __init__(self):
        super().__init__(temperature=0.7)

    async def generate(self, context: str, count: int = 3) -> List[Problem]:
        """초급 문제 생성"""

        prompt = f"""다음 학습 내용을 바탕으로 **초급(비전공자 입문)** 실습 문제를 {count}개 생성하시오.

**학습 내용**:
{context}

**초급 문제 요구사항 (비전공자 기준)**:
1. **용어 이해**: 개념 정의, 용어 설명 위주 (SHORT_ANSWER 타입)
2. **코드 읽기**: 간단한 코드(1-3줄) 읽고 이해하기 (SHORT_ANSWER 타입)
3. **빈칸 채우기**: 제시된 코드의 빈칸 완성 (SHORT_ANSWER 타입)
4. **단답형 문제**: 명확한 정답이 있는 개념 확인 문제 (SHORT_ANSWER 타입)
5. 실제 학습 내용에서 다룬 기본 개념만 사용
6. **중요**: problem_type은 반드시 "SHORT_ANSWER"만 사용 (선택형, CHOICE 등 사용 금지)

**출력 형식** (반드시 유효한 JSON 배열):
[
    {{
        "question": "Observer 패턴이란 무엇인가요? 한 문장으로 설명하세요.",
        "answer": "관찰 대상의 상태 변화를 관찰자에게 자동으로 알려주는 디자인 패턴입니다.",
        "hints": ["상태 변화", "자동 통지"],
        "difficulty_score": 1,
        "problem_type": "SHORT_ANSWER"
    }},
    {{
        "question": "다음 코드의 빈칸을 채우세요:\\n```java\\nclass Observer {{\\n    void ___() {{ }}  // 상태 변화 통지 받는 메소드\\n}}\\n```",
        "answer": "update",
        "hints": ["Observer 패턴의 핵심 메소드", "상태 변화를 알려받는 메소드 이름"],
        "difficulty_score": 2,
        "problem_type": "SHORT_ANSWER"
    }},
    {{
        "question": "다음 코드를 보고 Subject와 Observer 중 어느 역할인지 답하세요:\\n```java\\nvoid notifyObservers() {{ }}\\n```",
        "answer": "Subject (관찰 대상자)",
        "hints": ["Observer에게 알림을 보내는 역할", "상태를 관리하는 쪽"],
        "difficulty_score": 1,
        "problem_type": "SHORT_ANSWER"
    }}
]

**중요 규칙**:
1. 반드시 [ 로 시작하는 JSON 배열 형태로만 출력
2. difficulty_score는 1, 2, 3 중 하나의 숫자만 (1이 가장 쉬움)
3. **problem_type은 반드시 "SHORT_ANSWER"만 사용** (초급은 코딩 문제 없음)
4. "CHOICE", "MULTIPLE_CHOICE" 등 다른 타입 절대 사용 금지
5. SHORT_ANSWER 타입은 test_cases 생략
6. question은 최소 20자 이상 작성 (간결하게)
7. answer는 최소 5자 이상 작성
8. 주석이나 설명 없이 순수 JSON만 출력
9. 반드시 2개 이상의 힌트를 생성할 것

**필수**:
- 위 예시는 JSON 구조만 참고하고, 실제 문제 내용은 반드시 제공된 학습 내용에서만 생성할 것!
- **초급은 SHORT_ANSWER 타입만 사용**: 코딩 문제, 선택형 문제 생성 금지!"""

        # LLM 호출 및 JSON 파싱 (베이스 클래스 메서드 사용)
        response_content = await self._invoke_llm_with_json_mode(prompt)
        problems_data = self._parse_llm_response(response_content)
        return self._create_problems(problems_data, "beginner")


beginner_generator = BeginnerProblemGenerator()
