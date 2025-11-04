# paper_problem/generators/beginner.py
from langchain_upstage import ChatUpstage
from shared.upstage_client import upstage_client
from langchain.schema import HumanMessage
from paper_problem.models import Problem
from typing import List, Dict, Any
import json
import logging, re

logger = logging.getLogger(__name__)

def clean_and_parse_json(json_string: str) -> List[Dict[str, Any]]:
    """
    Solves common JSON parsing errors (like single quotes) in LLM responses before parsing.
    """
    try:
        # Step 1: Replace single-quoted strings within objects/arrays with double quotes
        # Pattern: ([\[:]) - Array start or colon, \s* - whitespace, ' - single quote start,
        # ([^']*?) - capture non-single quote chars, ' - single quote end
        cleaned_string = re.sub(r"([\[:])\s*'([^']*?)'", r'\1"\2"', json_string)

        # Step 2: Fix trailing commas (e.g., {"key": "value",})
        cleaned_string = re.sub(r",\s*([}\]])", r'\1', cleaned_string)

        # Step 3: Attempt final parsing
        return json.loads(cleaned_string)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON even after cleaning: {e}")
        # Return empty list on final failure
        return []

class BeginnerProblemGenerator:
    """초급 실습 문제 생성"""

    def __init__(self):
        self.llm = upstage_client.get_chat_model(
            model="solar-1-mini-chat", temperature=0.7
        )

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

        # 1. Json 출력 강제 (LangChain을 통헤 response_format 설정을 config로 전달.
        response = await self.llm.ainvoke([HumanMessage(content=prompt)],
                                          config={"response_format":{"type":"json_object"}}
                                          )

        problems_data = None

        try:
            # 2. 1차 시도 : 일반 JSON 파싱 (JSON 모드 강제로 대부분 성공 기대)
            problems_data = json.loads(response.content)
            #problems = [Problem(**p) for p in problems_data]
            #logger.info(f"Generated {len(problems)} beginner problems")
            #return problems
        except json.JSONDecodeError as e:
            # 3. 1차 실패 시 : 문자열 클렌징 후 2차 시도 (오류 복구 로직)
            logger.warning(f"Initial JSON parse failed: {e}. Attempting cleanup and re-parse.")
            try:
                problems_data = clean_and_parse_json(response.content)
            except Exception:
                # 클렌징 후에도 실패하면 최종 실패
                logger.error("Final attempt to parse JSON failed after cleanup.")
                return []

        # 4. 파싱된 데이터가 유효한지 확인
        if problems_data:
            try:
                # 파싱된 JSON 데이터를 Problem 모델 리스트로 변환
                problems = [Problem(**p) for p in problems_data]
                logger.info(f"Generated {len(problems)} beginner problems")
                return problems
            except Exception as e:
                # 모델 구조와 맞지 않는 필드 등이 있을 경우의 에러 처리
                logger.error(f"Failed to validate problem structure after parsing: {e}")
                return []
        else:
            logger.error(f"Response data was empty or invalid: {response.content}")
            return []


beginner_generator = BeginnerProblemGenerator()
