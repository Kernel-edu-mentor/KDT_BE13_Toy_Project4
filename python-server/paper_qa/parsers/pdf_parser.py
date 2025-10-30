from shared.upstage_client import upstage_client
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class PDFParser:
    async def parse(self, file_path: str) -> List[Dict]:
        """PDF 파싱 및 요소별 분리"""
        logger.info(f"Parsing PDF: {file_path}")

        # Upstage Document Parse
        parsed = await upstage_client.parse_pdf(file_path)

        content_blocks = []

        # documents 순회
        for doc in parsed.get("documents", []):
            content = doc.get("page_content", "")
            metadata = doc.get("metadata") or {}

            # Upstage 메타데이터에서 페이지 번호 키 확인 (page, page_number 등)
            page = metadata.get("page") or metadata.get("page_number") or 1

            if content:
                content_blocks.append(
                    {
                        "type": "text",
                        "content": content,
                        "page": page,
                        "category": "paragraph",
                    }
                )

            elif metadata.get("type") == "table":
                # 표는 텍스트로 변환
                table_text = self._table_to_text(content)
                content_blocks.append(
                    {
                        "type": "table",
                        "content": table_text,
                        "page": page,
                    }
                )

        logger.info(f"Parsed {len(content_blocks)} blocks")
        return content_blocks

    def _table_to_text(self, table_data) -> str:
        """표 데이터를 텍스트로 변환"""
        # 간단한 변환 로직
        return str(table_data)


pdf_parser = PDFParser()
