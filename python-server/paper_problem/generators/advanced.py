# paper_problem/generators/advanced.py
from langchain_upstage import ChatUpstage
from langchain.schema import HumanMessage
from typing import List
from paper_problem.models import Problem
from shared.upstage_client import upstage_client
import json
import logging

logger = logging.getLogger(__name__)


class AdvancedProblemGenerator:
    """고급 실습 문제 생성"""

    def __init__(self):
        self.llm = upstage_client.get_chat_model(
            model="solar-1-mini-chat", temperature=0.9  # 창의적인 문제 생성
        )

    async def generate(self, context: str, count: int = 3) -> List[Problem]:
        """고급 문제 생성"""

        prompt = f"""다음 학습 내용을 바탕으로 **고급** 실습 문제를 {count}개 생성하세요.

**학습 내용**:
{context}

**고급 문제 요구사항**:
1. 복잡한 실무 시나리오
2. 최적화 또는 설계 문제
3. 여러 파일/클래스 구성 필요
4. 엣지 케이스 고려
5. 성능 및 확장성 고려

**출력 형식** (반드시 유효한 JSON 배열):
[
    {{
        "question": "학습 내용의 고급 개념을 활용한 복잡한 실무 시나리오 문제 (최적화, 설계, 확장성 고려)",
        "answer": "예시 정답 코드 또는 아키텍처 설계 설명 (여러 파일/클래스 구성)",
        "hints": ["아키텍처 설계 힌트", "최적화 접근 방법", "엣지 케이스 처리 힌트"],
        "difficulty_score": 8,
        "problem_type": "CODING",
        "test_cases": [
            {{"input": "일반 케이스 입력", "expected": "예상 출력"}},
            {{"input": "엣지 케이스 입력", "expected": "엣지 케이스 출력"}},
            {{"input": "성능 테스트 입력", "expected": "성능 기준 출력"}}
        ]
    }},
    {{
        "question": "학습 내용의 고급 개념에 대한 설계 또는 최적화 방법을 설명하는 문제",
        "answer": "심층적인 설계 설명 또는 최적화 전략 답변",
        "hints": ["설계 원칙", "성능 고려사항", "확장성 전략"],
        "difficulty_score": 7,
        "problem_type": "SHORT_ANSWER"
    }}
]

**중요 규칙**:
1. 반드시 [ 로 시작하는 JSON 배열 형태로만 출력
2. difficulty_score는 7, 8, 9, 10 중 하나의 숫자만 (고급 수준)
3. problem_type은 "CODING" 또는 "SHORT_ANSWER" 중 하나만
4. test_cases는 CODING 타입일 때만 포함 (SHORT_ANSWER는 생략)
5. CODING 문제는 일반 케이스, 엣지 케이스, 성능 테스트 케이스 포함
6. 주석이나 설명 없이 순수 JSON만 출력

**필수**: 위 예시는 JSON 구조만 참고하고, 실제 문제 내용은 반드시 제공된 학습 내용에서만 생성할 것!"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])

        try:
            problems_data = json.loads(response.content)
            problems = [Problem(**p) for p in problems_data]
            logger.info(f"Generated {len(problems)} advanced problems")
            return problems
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return []


advanced_generator = AdvancedProblemGenerator()
