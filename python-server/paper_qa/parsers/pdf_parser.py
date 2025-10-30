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

        # elements 순회
        for element in parsed.get("elements", []):
            element_type = element.get("type")

            if element_type == "text":
                content_blocks.append(
                    {
                        "type": "text",
                        "content": element.get("content", ""),
                        "page": element.get("page", 1),
                        "category": element.get("category", "paragraph"),
                    }
                )

            elif element_type == "table":
                # 표는 텍스트로 변환
                table_text = self._table_to_text(element.get("content"))
                content_blocks.append(
                    {
                        "type": "table",
                        "content": table_text,
                        "page": element.get("page", 1),
                    }
                )

        logger.info(f"Parsed {len(content_blocks)} blocks")
        return content_blocks

    def _table_to_text(self, table_data) -> str:
        """표 데이터를 텍스트로 변환"""
        # 간단한 변환 로직
        return str(table_data)


pdf_parser = PDFParser()
