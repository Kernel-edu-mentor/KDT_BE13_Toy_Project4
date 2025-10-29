from typing import List, Dict, Any


class ContextBuilder:
    """문제 생성을 위한 컨텍스트 구성"""

    def build_context(
        self,
        documents: List[Dict[str, Any]],
        difficulty: str,
        max_tokens: int = 3000
    ) -> str:
        """난이도에 맞는 컨텍스트 구성"""

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
