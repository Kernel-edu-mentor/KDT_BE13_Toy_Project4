# team2_problem/generators/beginner.py
from shared.upstage_client import upstage_client
from langchain.schema import HumanMessage
from team2_problem.models import Problem
from typing import List
import json
import logging

logger = logging.getLogger(__name__)


class BeginnerProblemGenerator:
    async def generate(self, context: str, count: int = 3) -> List[Problem]:
        """초급 문제 생성"""

        llm = upstage_client.get_chat_model(temperature=0.7)

        prompt = f"""다음 학습 내용을 바탕으로 **초급** 실습 문제를 {count}개 생성하세요.

**학습 내용**:
{context}

**초급 문제 요구사항**:
1. 기본 개념 이해 확인
2. 단순한 코드 작성 (5-10줄)
3. 명확한 정답

**출력 형식** (JSON):
[
    {{
        "question": "문제 내용",
        "answer": "정답 코드",
        "hints": ["힌트1", "힌트2"],
        "difficulty_score": 1-3,
        "problem_type": "CODING",
        "test_cases": [{{"input": "...", "expected": "..."}}]
    }}
]"""

        response = await llm.ainvoke([HumanMessage(content=prompt)])

        try:
            problems_data = json.loads(response.content)
            problems = [Problem(**p) for p in problems_data]
            logger.info(f"Generated {len(problems)} beginner problems")
            return problems
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON")
            return []


beginner_generator = BeginnerProblemGenerator()
