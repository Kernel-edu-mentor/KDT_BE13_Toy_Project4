# paper_problem/generators/intermediate.py
from langchain_upstage import ChatUpstage
from langchain.schema import HumanMessage
from typing import List
from paper_problem.models import Problem
from shared.upstage_client import upstage_client
import json
import logging

logger = logging.getLogger(__name__)


class IntermediateProblemGenerator:
    """중급 실습 문제 생성"""

    def __init__(self):
        self.llm = upstage_client.get_chat_model(
            model="solar-1-mini-chat", temperature=0.8  # 더 다양한 문제 생성
        )

    async def generate(self, context: str, count: int = 3) -> List[Problem]:
        """중급 문제 생성"""

        prompt = f"""다음 학습 내용을 바탕으로 **중급** 실습 문제를 {count}개 생성하시오.

**학습 내용**:
{context}

**중급 문제 요구사항**:
1. 여러 개념을 결합
2. 실무 시나리오 기반
3. 코드 작성 (20-30줄)
4. 테스트 케이스 포함
5. 학습 내용에서 다룬 개념만 사용

**출력 형식** (반드시 유효한 JSON 배열):
[
    {{
        "question": "학습 내용에서 다룬 여러 개념을 결합한 실무 기반 코딩 문제",
        "answer": "예시 정답 코드 (20-30줄 수준)",
        "hints": ["첫 번째 접근 힌트", "두 번째 구현 힌트", "최적화 힌트"],
        "difficulty_score": 5,
        "problem_type": "CODING",
        "test_cases": [{{"input": "테스트 입력값", "expected": "예상 출력값"}}, {{"input": "추가 입력", "expected": "추가 출력"}}]
    }},
    {{
        "question": "학습 내용의 심화 개념이나 실무 적용 방법을 설명하는 문제",
        "answer": "개념에 대한 심층적 설명 답변",
        "hints": ["개념 이해 힌트", "실무 활용 예시"],
        "difficulty_score": 4,
        "problem_type": "SHORT_ANSWER"
    }}
]

**중요 규칙**:
1. 반드시 [ 로 시작하는 JSON 배열 형태로만 출력
2. difficulty_score는 4, 5, 6 중 하나의 숫자만 (중급 수준)
3. problem_type은 "CODING" 또는 "SHORT_ANSWER" 중 하나만
4. test_cases는 CODING 타입일 때만 포함 (SHORT_ANSWER는 생략)
5. 주석이나 설명 없이 순수 JSON만 출력

**필수**: 위 예시는 JSON 구조만 참고하고, 실제 문제 내용은 반드시 제공된 학습 내용에서만 생성할 것!"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])

        try:
            problems_data = json.loads(response.content)
            problems = [Problem(**p) for p in problems_data]
            logger.info(f"Generated {len(problems)} intermediate problems")
            return problems
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON : {e}")
            logger.error(f"Response : {response.content}")
            return []


intermediate_generator = IntermediateProblemGenerator()
