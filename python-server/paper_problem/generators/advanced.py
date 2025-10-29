from shared.upstage_client import upstage_client
from langchain.schema import HumanMessage
from paper_problem.models import Problem
from typing import List
import json
import logging

logger = logging.getLogger(__name__)

class AdvancedProblemGenerator:
    async def generate(self, context: str, count: int = 3) -> List[Problem]:
        """고급 문제 생성"""

        llm = upstage_client.get_chat_model(temperature=0.9)

        prompt = f"""다음 학습 내용을 바탕으로 **고급** 실습 문제를 {count}개 생성하세요.

**학습 내용**:
{context}

**고급 문제 요구사항**:
1. 창의적 문제 해결 능력 확인
2. 복잡한 코드 작성 (30줄 이상)
3. 최적화 및 설계 패턴 적용

**출력 형식** (JSON):
[
    {{
        "question": "문제 내용",
        "answer": "정답 코드",
        "hints": ["힌트1", "힌트2", "힌트3", "힌트4"],
        "difficulty_score": 7-10,
        "problem_type": "CODING",
        "test_cases": [{{"input": "...", "expected": "..."}}]
    }}
]"""

        response = await llm.ainvoke([HumanMessage(content=prompt)])

        try:
            problems_data = json.loads(response.content)
            problems = [Problem(**p) for p in problems_data]
            logger.info(f"Generated {len(problems)} advanced problems")
            return problems
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON")
            return []

advanced_generator = AdvancedProblemGenerator()
