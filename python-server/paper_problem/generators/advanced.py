# paper_problem/generators/advanced.py
from paper_problem.generators.base_generator import BaseProblemGenerator
from paper_problem.models import Problem
from typing import List
import logging

logger = logging.getLogger(__name__)


class AdvancedProblemGenerator(BaseProblemGenerator):
    """고급 실습 문제 생성"""

    def __init__(self):
        super().__init__(temperature=0.9)  # 창의적인 문제 생성

    async def generate(self, context: str, count: int = 3) -> List[Problem]:
        """고급 문제 생성"""

        prompt = f"""다음 학습 내용을 바탕으로 **고급(실무 응용)** 실습 문제를 {count}개 생성하세요.

**학습 내용**:
{context}

**고급 문제 요구사항 (비전공자 기준)**:
1. **여러 개념 결합**: 2-3개의 관련 개념을 함께 사용 (20-40줄)
2. **실무 시나리오**: 실제 프로젝트에서 사용할 수 있는 기능 구현
3. **완성도**: 전체 기능이 동작하는 코드 작성 (여러 메소드 포함)
4. **설계 고려**: 간단한 구조 설계나 최적화 고려
5. 학습 내용에서 다룬 개념들을 실무적으로 활용

**출력 형식** (반드시 유효한 JSON 배열):
[
    {{
        "question": "Observer 패턴을 사용하여 간단한 숫자 생성기와 2개의 Observer(숫자 출력, 그래프 출력)를 포함한 완전한 프로그램을 작성하세요. Subject, Observer 인터페이스, 구체 클래스들을 모두 구현하세요.",
        "answer": "```java\\ninterface Observer {{\\n    void update(NumberGenerator generator);\\n}}\\n\\nabstract class NumberGenerator {{\\n    private List<Observer> observers = new ArrayList<>();\\n    \\n    public void addObserver(Observer observer) {{\\n        observers.add(observer);\\n    }}\\n    \\n    public void notifyObservers() {{\\n        for (Observer o : observers) {{\\n            o.update(this);\\n        }}\\n    }}\\n    \\n    public abstract int getNumber();\\n    public abstract void execute();\\n}}\\n\\nclass RandomNumberGenerator extends NumberGenerator {{\\n    private int number;\\n    \\n    public int getNumber() {{ return number; }}\\n    \\n    public void execute() {{\\n        for (int i = 0; i < 5; i++) {{\\n            number = new Random().nextInt(50);\\n            notifyObservers();\\n        }}\\n    }}\\n}}\\n\\nclass DigitObserver implements Observer {{\\n    public void update(NumberGenerator generator) {{\\n        System.out.println(\\\"Digit: \\\" + generator.getNumber());\\n    }}\\n}}\\n```",
        "hints": ["Observer 인터페이스 정의부터 시작하세요", "Subject는 Observer 목록을 관리합니다", "구체 Observer들은 각자의 방식으로 상태를 출력합니다"],
        "difficulty_score": 7,
        "problem_type": "CODING",
        "test_cases": [{{"input": "generator.execute();", "expected": "Digit: [숫자]\\nDigit: [숫자]\\n..."}}]
    }},
    {{
        "question": "Observer 패턴을 실제 웹 애플리케이션에 적용한다면 어떤 상황에서 유용할까요? 구체적인 예시 2가지와 장점을 설명하세요.",
        "answer": "1) 실시간 알림 시스템: 게시판에 새 글이 올라오면 구독자들에게 자동 알림을 보낼 수 있습니다. 2) 데이터 동기화: 하나의 데이터가 변경되면 여러 화면(대시보드, 리포트 등)이 자동으로 업데이트됩니다. 장점은 Subject와 Observer가 느슨하게 결합되어 새로운 Observer 추가가 쉽고, 코드 수정 없이 기능 확장이 가능합니다.",
        "hints": ["실시간 업데이트가 필요한 상황", "여러 곳에서 같은 데이터를 보여주는 경우", "느슨한 결합의 장점"],
        "difficulty_score": 8,
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
7. 반드시 2개 이상의 힌트를 생성할 것

**필수**: 위 예시는 JSON 구조만 참고하고, 실제 문제 내용은 반드시 제공된 학습 내용에서만 생성할 것!"""

        # LLM 호출 및 JSON 파싱 (베이스 클래스 메서드 사용)
        response_content = await self._invoke_llm_with_json_mode(prompt)
        problems_data = self._parse_llm_response(response_content)
        return self._create_problems(problems_data, "advanced")

advanced_generator = AdvancedProblemGenerator()
