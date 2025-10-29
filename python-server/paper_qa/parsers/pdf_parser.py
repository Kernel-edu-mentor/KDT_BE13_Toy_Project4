from shared.upstage_client import upstage_client
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class PDFParser:
    async def parse(self, file_path: str) -> List[Dict]:
        """PDF 파싱"""
        logger.info(f"Parsing PDF: {file_path}")

        parsed = await upstage_client.parse_pdf(file_path)
        content_blocks = []

        for element in parsed.get('elements', []):
            element_type = element.get('type')

            if element_type == 'text':
                content_blocks.append({
                    'type': 'text',
                    'content': element.get('content', ''),
                    'page': element.get('page', 1)
                })

        logger.info(f"Parsed {len(content_blocks)} blocks")
        return content_blocks

pdf_parser = PDFParser()
