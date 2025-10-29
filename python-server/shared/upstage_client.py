from upstage import Upstage
from langchain_upstage import UpstageEmbeddings, ChatUpstage
from config import settings
from typing import List
import asyncio
import logging

logger = logging.getLogger(__name__)

class UpstageClient:
    """Upstage API 클라이언트 (팀1, 팀2 공유)"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.client = Upstage(api_key=settings.UPSTAGE_API_KEY)
        self.embeddings = UpstageEmbeddings(
            api_key=settings.UPSTAGE_API_KEY,
            model="embedding-query"
        )
        self._initialized = True
        logger.info("Upstage client initialized")

    async def parse_pdf(self, file_path: str) -> dict:
        """PDF 파싱"""
        result = await asyncio.to_thread(
            self.client.document_parse,
            file=file_path
        )
        return result

    async def embed_query(self, text: str) -> List[float]:
        """쿼리 임베딩"""
        return await self.embeddings.aembed_query(text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서 리스트 임베딩"""
        embeddings = UpstageEmbeddings(
            api_key=settings.UPSTAGE_API_KEY,
            model="embedding-passage"
        )
        return await embeddings.aembed_documents(texts)

    def get_chat_model(self, model: str = "solar-1-mini-chat", temperature: float = 0.3):
        """Chat 모델 반환"""
        return ChatUpstage(
            api_key=settings.UPSTAGE_API_KEY,
            model=model,
            temperature=temperature
        )

# 싱글톤 인스턴스
upstage_client = UpstageClient()
