from typing import List, Dict, Any
from shared.chroma_client import chroma_client
import logging
import re

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """학습자료 분석 및 핵심 개념 추출"""

    async def analyze_material(
        self,
        material_id: int,
        difficulty: str
    ) -> Dict[str, Any]:
        """난이도에 맞는 학습 내용 추출"""

        # 난이도별 검색 전략
        search_strategies = {
            "BEGINNER": {
                "keywords": ["기본", "개념", "정의", "예제", "소개"],
                "k": 5,
                "focus": "fundamental"
            },
            "INTERMEDIATE": {
                "keywords": ["실습", "구현", "활용", "응용", "예제"],
                "k": 7,
                "focus": "practical"
            },
            "ADVANCED": {
                "keywords": ["심화", "최적화", "설계", "복잡한", "고급"],
                "k": 10,
                "focus": "advanced"
            }
        }

        difficulty_key = difficulty.upper()

        if difficulty_key not in search_strategies:
            raise ValueError(f"지원하지 않는 난이도입니다: {difficulty}")

        strategy = search_strategies[difficulty_key]

        # 키워드별 검색
        all_docs: List[Dict[str, Any]] = []
        seen_ids = set()

        for keyword in strategy["keywords"]:
            results = chroma_client.search(
                collection_name="learning_materials",
                query_texts=[keyword],
                n_results=strategy["k"],
                filter_dict={"material_id": material_id}
            )

            ids = results.get("ids", [[]])
            documents = results.get("documents", [[]])
            metadatas = results.get("metadatas", [[]])

            # 중복 제거하며 수집
            for i, doc_id in enumerate(ids[0]):
                if doc_id in seen_ids:
                    continue

                seen_ids.add(doc_id)
                metadata = metadatas[0][i] if i < len(metadatas[0]) else {}

                all_docs.append({
                    "content": documents[0][i] if i < len(documents[0]) else "",
                    "page": metadata.get("page"),
                    "type": metadata.get("type")
                })

        logger.info("Extracted %s content blocks for %s", len(all_docs), difficulty_key)

        return {
            "documents": all_docs,
            "strategy": strategy,
            "total_count": len(all_docs)
        }

    def extract_key_concepts(self, documents: List[Dict[str, Any]]) -> List[str]:
        """핵심 개념 추출"""
        concepts = set()

        for doc in documents:
            content = doc.get("content", "")
            # 대문자로 시작하는 단어 추출(클래스명, 개념명 등)
            for word in re.findall(r"\b[A-Z][A-Za-z0-9_]{3,}\b", content):
                concepts.add(word)

        return list(concepts)[:10]


content_analyzer = ContentAnalyzer()
