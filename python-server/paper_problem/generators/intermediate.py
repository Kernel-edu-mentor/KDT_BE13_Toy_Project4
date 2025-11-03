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

        prompt = f"""다음 학습 내용을 바탕으로 **중급(기본 응용)** 실습 문제를 {count}개 생성하시오.

**학습 내용**:
{context}

**중급 문제 요구사항 (비전공자 기준)**:
1. **단일 개념 구현**: 배운 개념을 실제로 코드로 작성 (5-15줄)
2. **간단한 메소드 작성**: 기본적인 기능을 가진 메소드 구현
3. **예제 수정**: 제시된 예제 코드를 일부 수정하거나 확장
4. **실습 중심**: 따라할 수 있는 명확한 구현 문제
5. 학습 내용에서 다룬 개념만 사용 (초급보다 약간 긴 코드)

**출력 형식** (반드시 유효한 JSON 배열):
[
    {{
        "question": "Observer 패턴을 사용하여 간단한 Observer 클래스를 작성하세요. update() 메소드를 포함하고, Subject의 상태를 출력하는 기능을 구현하세요.",
        "answer": "```java\\nclass DigitObserver implements Observer {{\\n    private NumberGenerator generator;\\n    \\n    public DigitObserver(NumberGenerator generator) {{\\n        this.generator = generator;\\n    }}\\n    \\n    public void update() {{\\n        int number = generator.getNumber();\\n        System.out.println(\\\"Current number: \\\" + number);\\n    }}\\n}}\\n```",
        "hints": ["Observer 인터페이스를 구현하세요", "update() 메소드에서 Subject의 상태를 가져오세요", "가져온 상태를 출력하세요"],
        "difficulty_score": 4,
        "problem_type": "CODING",
        "test_cases": [{{"input": "DigitObserver observer = new DigitObserver(generator); observer.update();", "expected": "Current number: [숫자]"}}]
    }},
    {{
        "question": "Observer 패턴에서 Subject 클래스의 notifyObservers() 메소드는 어떤 역할을 하나요? 구체적으로 설명하세요.",
        "answer": "notifyObservers() 메소드는 Subject의 상태가 변경되었을 때, 등록된 모든 Observer들의 update() 메소드를 순서대로 호출하여 상태 변화를 알려주는 역할을 합니다.",
        "hints": ["상태 변경 시 호출", "등록된 Observer들에게 알림", "update() 메소드 호출"],
        "difficulty_score": 5,
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
