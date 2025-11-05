# paper_problem/generators/base_generator.py
from langchain.schema import HumanMessage
from paper_problem.models import Problem
from shared.upstage_client import upstage_client
from typing import List, Dict, Any
import json
import logging
import re

logger = logging.getLogger(__name__)


class BaseProblemGenerator:
    """문제 생성기 베이스 클래스 - 공통 로직 추출"""

    def __init__(self, temperature: float = 0.7):
        """
        Args:
            temperature: LLM temperature (0.0-1.0)
                - 0.7: 초급 (적당한 다양성)
                - 0.8: 중급 (더 다양한 문제)
                - 0.9: 고급 (창의적인 문제)
        """
        self.llm = upstage_client.get_chat_model(
            model="solar-1-mini-chat", temperature=temperature
        )

    @staticmethod
    def clean_and_parse_json(json_string: str) -> List[Dict[str, Any]]:
        """
        LLM 응답의 일반적인 JSON 파싱 오류를 수정하고 파싱

        Args:
            json_string: 파싱할 JSON 문자열

        Returns:
            파싱된 딕셔너리 리스트 (실패 시 빈 리스트)
        """
        try:
            # Step 1: Replace single-quoted strings with double quotes
            # Pattern: ([\[:]) - Array start or colon, \s* - whitespace, ' - single quote start,
            # ([^']*?) - capture non-single quote chars, ' - single quote end
            cleaned_string = re.sub(r"([\[:])\s*'([^']*?)'", r'\1"\2"', json_string)

            # Step 2: Fix trailing commas (e.g., {"key": "value",})
            cleaned_string = re.sub(r",\s*([}\]])", r'\1', cleaned_string)

            # Step 3: Attempt final parsing
            return json.loads(cleaned_string)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON even after cleaning: {e}")
            return []

    async def _invoke_llm_with_json_mode(self, prompt: str) -> str:
        """
        JSON 모드로 LLM 호출

        Args:
            prompt: 프롬프트 문자열

        Returns:
            LLM 응답 content
        """
        response = await self.llm.ainvoke(
            [HumanMessage(content=prompt)],
            config={"response_format": {"type": "json_object"}}
        )
        return response.content

    def _parse_llm_response(self, response_content: str) -> List[Dict[str, Any]]:
        """
        LLM 응답을 JSON으로 파싱 (2단계 시도)

        Args:
            response_content: LLM 응답 content

        Returns:
            파싱된 딕셔너리 리스트 (실패 시 빈 리스트)
        """
        problems_data = None

        try:
            # 1차 시도: 일반 JSON 파싱 (JSON 모드 강제로 대부분 성공 기대)
            problems_data = json.loads(response_content)
        except json.JSONDecodeError as e:
            # 2차 시도: 문자열 클렌징 후 재시도 (오류 복구 로직)
            logger.warning(f"Initial JSON parse failed: {e}. Attempting cleanup and re-parse.")
            try:
                problems_data = self.clean_and_parse_json(response_content)
            except Exception:
                logger.error("Final attempt to parse JSON failed after cleanup.")
                return []

        return problems_data if problems_data else []

    def _create_problems(self, problems_data: List[Dict[str, Any]], difficulty_level: str) -> List[Problem]:
        """
        파싱된 JSON 데이터를 Problem 모델 리스트로 변환

        Args:
            problems_data: 파싱된 딕셔너리 리스트
            difficulty_level: 난이도 레벨 (로깅용)

        Returns:
            Problem 모델 리스트 (실패 시 빈 리스트)
        """
        if not problems_data:
            logger.error("Response data was empty or invalid")
            return []

        try:
            problems = [Problem(**p) for p in problems_data]
            logger.info(f"Generated {len(problems)} {difficulty_level} problems")
            return problems
        except Exception as e:
            logger.error(f"Failed to validate problem structure after parsing: {e}")
            return []

    async def generate(self, context: str, count: int = 3) -> List[Problem]:
        """
        문제 생성 (서브클래스에서 구현 필요)

        Args:
            context: 학습 내용 컨텍스트
            count: 생성할 문제 개수

        Returns:
            생성된 Problem 리스트
        """
        raise NotImplementedError("Subclass must implement generate() method")
