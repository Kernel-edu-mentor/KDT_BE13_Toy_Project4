from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ContextBuilder:
    """문제 생성을 위한 컨텍스트 구성"""

    def build_context(
        self,
        documents: List[Dict[str, Any]],
        difficulty: str,
        max_tokens: int = 3000,
        documents_by_topic: Dict[str, List[Dict[str, Any]]] = None,
        topics: List[str] = None
    ) -> str:
        """난이도에 맞는 컨텍스트 구성 (토픽별 균등 분배)"""

        # 토픽별 문서가 있으면 균등 분배, 없으면 기존 방식
        if documents_by_topic and topics and len(topics) > 1:
            return self._build_balanced_context(
                documents_by_topic, topics, max_tokens
            )
        else:
            return self._build_simple_context(documents, max_tokens)

    def _build_balanced_context(
        self,
        documents_by_topic: Dict[str, List[Dict[str, Any]]],
        topics: List[str],
        max_tokens: int
    ) -> str:
        """토픽별로 균등하게 문서를 분배"""

        context_parts: List[str] = []
        current_tokens = 0

        # 각 토픽의 인덱스
        topic_indices = {topic: 0 for topic in topics}

        # 라운드 로빈 방식으로 각 토픽에서 번갈아 선택
        while current_tokens < max_tokens:
            added_any = False

            for topic in topics:
                topic_docs = documents_by_topic.get(topic, [])
                idx = topic_indices[topic]

                # 이 토픽의 문서를 다 썼으면 스킵
                if idx >= len(topic_docs):
                    continue

                doc = topic_docs[idx]
                content = doc.get("content", "")

                if not content:
                    topic_indices[topic] += 1
                    continue

                page = doc.get("page", "알 수 없음")
                topic_name = doc.get("topic", topic)

                # 대략적인 토큰 계산 (4 chars ≈ 1 token)
                doc_tokens = max(1, len(content) // 4)

                if current_tokens + doc_tokens > max_tokens:
                    break

                context_parts.append(
                    f"[주제: {topic_name} | 페이지 {page}]\n{content}"
                )
                current_tokens += doc_tokens
                topic_indices[topic] += 1
                added_any = True

            # 모든 토픽에서 더 이상 추가할 문서가 없으면 종료
            if not added_any:
                break

        # 토픽별 포함된 문서 수 로깅
        for topic in topics:
            count = topic_indices[topic]
            logger.info(f"Topic '{topic}': included {count} documents in context")

        context = "\n\n---\n\n".join(context_parts)
        return context

    def _build_simple_context(
        self,
        documents: List[Dict[str, Any]],
        max_tokens: int
    ) -> str:
        """기존 방식: 순서대로 문서 선택"""

        context_parts: List[str] = []
        current_tokens = 0

        for doc in documents:
            content = doc.get("content", "")
            if not content:
                continue

            page = doc.get("page", "알 수 없음")

            # 대략적인 토큰 계산 (4 chars ≈ 1 token)
            doc_tokens = max(1, len(content) // 4)

            if current_tokens + doc_tokens > max_tokens:
                break

            context_parts.append(
                f"[페이지 {page}]\n{content}"
            )
            current_tokens += doc_tokens

        context = "\n\n---\n\n".join(context_parts)
        return context


context_builder = ContextBuilder()
