from shared.upstage_client import upstage_client
from langchain.schema import HumanMessage
from paper_problem.models import Problem
from typing import List
import json
import logging

logger = logging.getLogger(__name__)

class IntermediateProblemGenerator:
    async def generate(self, context: str, count: int = 3) -> List[Problem]:
        """중급 문제 생성"""

        llm = upstage_client.get_chat_model(temperature=0.8)

        prompt = f"""다음 학습 내용을 바탕으로 **중급** 실습 문제를 {count}개 생성하세요.

**학습 내용**:
{context}

**중급 문제 요구사항**:
1. 응용 능력 확인
2. 중급 난이도 코드 작성 (15-25줄)
3. 여러 개념을 조합한 문제

**출력 형식** (JSON):
[
    {{
        "question": "문제 내용",
        "answer": "정답 코드",
        "hints": ["힌트1", "힌트2", "힌트3"],
        "difficulty_score": 4-6,
        "problem_type": "CODING",
        "test_cases": [{{"input": "...", "expected": "..."}}]
    }}
]"""

        response = await llm.ainvoke([HumanMessage(content=prompt)])

        try:
            problems_data = json.loads(response.content)
            problems = [Problem(**p) for p in problems_data]
            logger.info(f"Generated {len(problems)} intermediate problems")
            return problems
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON")
            return []

intermediate_generator = IntermediateProblemGenerator()
