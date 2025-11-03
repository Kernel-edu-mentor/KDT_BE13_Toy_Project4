from langchain_upstage import ChatUpstage
from shared.upstage_client import upstage_client
from langchain.schema import HumanMessage
from typing import List
import json
import logging

logger = logging.getLogger(__name__)


class TopicExtractor:
    """자연어 학습 내용에서 주제 추출"""

    def __init__(self):
        self.llm = upstage_client.get_chat_model(
            model="solar-1-mini-chat", temperature=0.3
        )

    async def extract_topics(self, learning_description: str) -> List[str]:
        """LLM으로 학습 주제 추출"""

        prompt = f"""사용자가 학습한 내용 설명에서 핵심 주제/개념 키워드만 추출하시오.

**학습 내용 설명**:
{learning_description}

**추출 규칙**:
1. 기술 용어, 프레임워크 이름, 개념명만 추출
2. 어노테이션(@Entity 등)도 포함
3. 3~7개의 핵심 키워드로 압축
4. 검색에 유용한 형태로 (조사 제거)

**출력 형식** (반드시 유효한 JSON 배열):
["키워드1", "키워드2", "키워드3"]

**예시**:
입력: "JPA를 학습하고 Entity 클래스의 개념과 @Entity 어노테이션을 학습했다"
출력: ["JPA", "Entity", "@Entity", "영속성"]

입력: "Spring Boot에서 RESTful API를 만드는 방법과 @RestController를 배웠어요"
출력: ["Spring Boot", "REST API", "@RestController", "HTTP"]

**중요**: 반드시 JSON 배열 형태로만 출력하고, 추가 설명이나 주석은 포함하지 마시오."""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            topics = json.loads(response.content)

            if not isinstance(topics, list):
                logger.error(f"Invalid topic format: {response.content}")
                return []

            logger.info(f"Extracted {len(topics)} topics from description: {topics}")
            return topics

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse topics JSON: {e}")
            logger.error(f"Response: {response.content}")
            return []
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []


topic_extractor = TopicExtractor()
