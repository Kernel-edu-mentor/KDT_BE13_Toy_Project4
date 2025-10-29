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

**출력 형식** (반드시 유효한 JSON 배열):
[
    {{
        "question": "변수 name에 '홍길동'을 저장하는 코드를 작성하시오",
        "answer": "name = '홍길동'",
        "hints": ["변수명 = 값 형식으로 작성", "문자열은 따옴표로 감싸기"],
        "difficulty_score": 1,
        "problem_type": "CODING",
        "test_cases": [{{"input": "", "expected": "name = '홍길동'"}}]
    }},
    {{
        "question": "정수형 변수와 실수형 변수의 차이를 설명하시오",
        "answer": "정수형(int)은 소수점이 없는 숫자, 실수형(float)은 소수점이 있는 숫자",
        "hints": ["int와 float의 차이", "예시를 들어 설명"],
        "difficulty_score": 2,
        "problem_type": "SHORT_ANSWER"
    }}
]

**중요 규칙**:
1. 반드시 [ 로 시작하는 JSON 배열 형태로만 출력
2. difficulty_score는 1, 2, 3 중 하나의 숫자만 (1이 가장 쉬움)
3. problem_type은 "CODING" 또는 "SHORT_ANSWER" 중 하나만
4. test_cases는 CODING 타입일 때만 포함 (SHORT_ANSWER는 생략)
5. 주석이나 설명 없이 순수 JSON만 출력"""

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
