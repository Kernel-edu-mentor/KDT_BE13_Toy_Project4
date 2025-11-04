# paper_problem/graders/short_answer_grader.py
from shared.upstage_client import upstage_client
from langchain.schema import HumanMessage
from paper_problem.models import Problem
from typing import Dict
import json
import logging

logger = logging.getLogger(__name__)


class ShortAnswerGrader:
    """단답형 문제 LLM 기반 채점"""

    def __init__(self):
        self.llm = upstage_client.get_chat_model(
            model="solar-1-mini-chat", temperature=0.3
        )

    async def grade(self, problem: Problem, user_answer: str) -> Dict:
        """
        LLM으로 답변의 의미적 유사도 평가

        Args:
            problem: 문제 객체 (정답 포함)
            user_answer: 사용자 답변

        Returns:
            {
                "is_correct": bool,
                "score": int (0-100),
                "feedback": str,
                "similarity_score": float (0.0-1.0)
            }
        """

        logger.info(f"Grading SHORT_ANSWER: {problem.question[:50]}...")

        # 빈 답변 체크
        if not user_answer or not user_answer.strip():
            logger.warning("Empty user answer")
            return {
                "is_correct": False,
                "score": 0,
                "feedback": "답변이 비어 있습니다. 답변을 입력해주세요.",
                "similarity_score": 0.0
            }

        prompt = f"""다음은 학습 문제의 정답과 학생 답변입니다. 학생 답변이 정답인지 평가하세요.

**문제**: {problem.question}

**정답**: {problem.answer}

**학생 답변**: {user_answer}

**힌트** (참고용): {', '.join(problem.hints)}

**평가 기준**:
1. 핵심 개념이 정확히 포함되어 있는가?
2. 의미가 정답과 일치하는가? (표현이 다르거나 영어/한글 혼용은 괜찮음)
3. 오개념이나 잘못된 정보가 있는가?
4. 부분적으로만 맞는 경우 부분 점수 부여

**점수 기준**:
- 100점: 핵심 개념을 모두 정확히 설명 (표현은 달라도 됨)
- 80-90점: 핵심 개념은 맞지만 일부 설명 부족
- 50-70점: 부분적으로만 정답 (일부 개념만 포함)
- 30-40점: 방향은 맞지만 구체성 부족
- 0-20점: 오답 또는 핵심 개념 누락

**출력 형식** (반드시 유효한 JSON):
{{
    "is_correct": true/false,
    "score": 0-100,
    "feedback": "평가 이유를 2-3문장으로 설명 (왜 정답/오답인지, 무엇이 부족한지)",
    "similarity_score": 0.0-1.0
}}

**중요**: 반드시 JSON만 출력하고, 다른 텍스트는 포함하지 마세요."""

        try:
            # JSON 모드로 LLM 호출
            response = await self.llm.ainvoke(
                [HumanMessage(content=prompt)],
                config={"response_format": {"type": "json_object"}}
            )

            # JSON 파싱
            result = json.loads(response.content)

            # 검증
            required_keys = ["is_correct", "score", "feedback", "similarity_score"]
            if not all(key in result for key in required_keys):
                raise ValueError(f"Missing required keys in LLM response: {result}")

            # 타입 변환 및 범위 체크
            result["is_correct"] = bool(result["is_correct"])
            result["score"] = max(0, min(100, int(result["score"])))
            result["similarity_score"] = max(0.0, min(1.0, float(result["similarity_score"])))

            logger.info(f"Grading result: score={result['score']}, is_correct={result['is_correct']}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}. Response: {response.content}")
            # Fallback: 단순 문자열 유사도 검사
            return self._fallback_grading(problem.answer, user_answer)

        except Exception as e:
            logger.error(f"Grading error: {e}")
            return self._fallback_grading(problem.answer, user_answer)

    def _fallback_grading(self, correct_answer: str, user_answer: str) -> Dict:
        """
        LLM 실패 시 폴백: 단순 문자열 유사도
        """

        # 정규화 (소문자, 공백 제거)
        normalized_correct = correct_answer.lower().replace(" ", "")
        normalized_user = user_answer.lower().replace(" ", "")

        # 정확히 일치
        if normalized_correct == normalized_user:
            return {
                "is_correct": True,
                "score": 100,
                "feedback": "정답입니다.",
                "similarity_score": 1.0
            }

        # 부분 일치 (정답이 사용자 답변에 포함)
        if normalized_correct in normalized_user or normalized_user in normalized_correct:
            return {
                "is_correct": True,
                "score": 80,
                "feedback": "정답입니다. (표현이 약간 다르지만 핵심 개념 포함)",
                "similarity_score": 0.8
            }

        # 불일치
        return {
            "is_correct": False,
            "score": 0,
            "feedback": "오답입니다. 정답을 다시 확인하세요.",
            "similarity_score": 0.0
        }


short_answer_grader = ShortAnswerGrader()
