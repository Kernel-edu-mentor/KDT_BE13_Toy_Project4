# paper_problem/generators/beginner.py
from langchain_upstage import ChatUpstage
from shared.upstage_client import upstage_client
from langchain.schema import HumanMessage
from paper_problem.models import Problem
from typing import List
import json
import logging

logger = logging.getLogger(__name__)


class BeginnerProblemGenerator:
    """초급 실습 문제 생성"""

    def __init__(self):
        self.llm = upstage_client.get_chat_model(
            model="solar-1-mini-chat", temperature=0.7
        )

    async def generate(self, context: str, count: int = 3) -> List[Problem]:
        """초급 문제 생성"""

        prompt = f"""다음 학습 내용을 바탕으로 **초급** 실습 문제를 {count}개 생성하시오.

**학습 내용**:
{context}

**초급 문제 요구사항**:
1. 기본 개념 이해 확인
2. 단순한 코드 작성 (5~10줄)
3. 명확한 정답이 있는 문제
4. 실제 학습 내용에서 다룬 내용만 사용

**출력 형식** (JSON):
[
    {{
        "question" : "문제 내용 (구체적으로)",
        "answer" : "정답 혹은 예시 코드",
        "hints" : ["힌트1", "힌트2"],
        "difficulty_score": 1-3 (1이 가장 쉬움),
        "problem_type": "CODING" 또는 "SHORT_ANSWER",
        "test_cases": [{{"input": "...", "expected": "..."}}]  // CODING인 경우만
    }},
    ...
]

**중요**: 반드시 유효한 JSON 배열로 출력하시오. """

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])

        try:
            problems_data = json.loads(response.content)
            problems = [Problem(**p) for p in problems_data]
            logger.info(f"Generated {len(problems)} beginner problems")
            return problems
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON : {e}")
            logger.error(f"Response : {response.content}")
            return []


beginner_generator = BeginnerProblemGenerator()
