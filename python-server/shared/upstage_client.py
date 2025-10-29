from langchain_upstage import UpstageEmbeddings, ChatUpstage, UpstageDocumentParseLoader
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

        self.embeddings = UpstageEmbeddings(
            api_key=settings.UPSTAGE_API_KEY,
            model="embedding-query"
        )
        self._initialized = True
        logger.info("Upstage client initialized")

    async def parse_pdf(self, file_path: str) -> dict:
        """PDF 파싱"""
        loader = UpstageDocumentParseLoader(
            file_path=file_path,
            api_key=settings.UPSTAGE_API_KEY,
            split="page"
        )
        docs = await asyncio.to_thread(loader.load)
        return {"documents": [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs]}

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
