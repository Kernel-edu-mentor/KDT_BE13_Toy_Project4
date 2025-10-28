# shared/chroma_client.py
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict
from config import settings
import logging

logger = logging.getLogger(__name__)


class ChromaClient:
    """ChromaDB 클라이언트 (팀1, 팀2 공유)"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._initialized = True
        logger.info("ChromaDB client initialized")

    def get_or_create_collection(self, name: str):
        """컬렉션 생성 또는 가져오기"""
        return self.client.get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}
        )

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str],
        embeddings: List[List[float]] = None,
    ):
        """문서 추가"""
        collection = self.get_or_create_collection(collection_name)

        if embeddings:
            collection.add(
                documents=documents, metadatas=metadatas, ids=ids, embeddings=embeddings
            )
        else:
            collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def search(
        self,
        collection_name: str,
        query_texts: List[str] = None,
        query_embeddings: List[List[float]] = None,
        n_results: int = 3,
        filter_dict: Dict = None,
    ):
        """유사도 검색"""
        collection = self.get_or_create_collection(collection_name)

        return collection.query(
            query_texts=query_texts,
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=filter_dict,
        )


# 싱글톤 인스턴스
chroma_client = ChromaClient()
