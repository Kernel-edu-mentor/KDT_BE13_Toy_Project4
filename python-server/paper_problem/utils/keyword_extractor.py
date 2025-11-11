from langchain_upstage import ChatUpstage
from langchain_core.prompts import ChatPromptTemplate
from typing import List
import logging

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """질문 목록에서 핵심 키워드를 추출하는 클래스"""

    def __init__(self):
        self.llm = ChatUpstage(model="solar-pro")

    async def extract_keywords(self, questions: List[str], max_keywords: int = 5) -> List[str]:
        """
        질문 목록에서 핵심 키워드를 추출합니다.

        Args:
            questions: 질문 목록
            max_keywords: 추출할 최대 키워드 수

        Returns:
            추출된 키워드 목록
        """
        if not questions:
            logger.warning("No questions provided for keyword extraction")
            return []

        # 질문들을 하나의 텍스트로 결합
        combined_questions = "\n".join([f"- {q}" for q in questions])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 학습 질문에서 핵심 키워드를 추출하는 전문가입니다.
주어진 질문들에서 가장 중요한 기술적 개념, 용어, 주제를 추출하세요.

규칙:
1. 명사 위주로 추출 (개념, 용어, 기술명)
2. 구체적이고 학습 가치가 있는 키워드만 선택
3. 중복 제거
4. 최대 {max_keywords}개까지만 추출
5. 한 단어 또는 2-3단어로 구성된 짧은 키워드
6. 쉼표로 구분하여 키워드만 출력 (설명 없이)

예시:
입력: "JPA Entity란 무엇인가요?", "영속성 컨텍스트는 어떻게 동작하나요?"
출력: JPA, Entity, 영속성 컨텍스트, ORM, 데이터베이스"""),
            ("human", "다음 질문들에서 핵심 키워드를 추출하세요:\n\n{questions}")
        ])

        chain = prompt | self.llm

        try:
            logger.info(f"Extracting keywords from {len(questions)} questions")
            response = await chain.ainvoke({
                "questions": combined_questions,
                "max_keywords": max_keywords
            })

            # 응답에서 키워드 추출 및 정리
            keywords_text = response.content.strip()
            keywords = [k.strip() for k in keywords_text.split(",")]

            # 빈 문자열 제거 및 최대 개수 제한
            keywords = [k for k in keywords if k][:max_keywords]

            logger.info(f"Extracted {len(keywords)} keywords: {keywords}")
            return keywords

        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []


# 싱글톤 인스턴스
keyword_extractor = KeywordExtractor()
