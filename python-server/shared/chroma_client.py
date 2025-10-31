import logging
from typing import List, Dict

try:
    import chromadb  # type: ignore
    from chromadb.config import Settings as ChromaSettings  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - 테스트 환경 대비
    chromadb = None
    ChromaSettings = None

from config import settings

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

        if chromadb is None:
            logger.warning("ChromaDB not available; using stub client")
            self.client = None
            self._initialized = True
            return

        self.client = chromadb.HttpClient(  # type: ignore[union-attr]
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            settings=ChromaSettings(  # type: ignore[misc]
                anonymized_telemetry=False
            )
        )
        self._initialized = True
        logger.info("ChromaDB client initialized")

    def get_or_create_collection(self, name: str):
        """컬렉션 생성 또는 가져오기"""
        if self.client is None:
            raise RuntimeError("ChromaDB 클라이언트가 초기화되지 않았습니다.")

        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=None
        )

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str],
        embeddings: List[List[float]] = None
    ):
        """문서 추가"""
        if self.client is None:
            raise RuntimeError("ChromaDB 클라이언트가 초기화되지 않았습니다.")

        collection = self.get_or_create_collection(collection_name)

        if embeddings:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
        else:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

    def search(
        self,
        collection_name: str,
        query_texts: List[str] = None,
        query_embeddings: List[List[float]] = None,
        n_results: int = 3,
        filter_dict: Dict = None
    ):
        """유사도 검색"""
        if self.client is None:
            raise RuntimeError("ChromaDB 클라이언트가 초기화되지 않았습니다.")

        collection = self.get_or_create_collection(collection_name)

        return collection.query(
            query_texts=query_texts,
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=filter_dict
        )

# 싱글톤 인스턴스
chroma_client = ChromaClient()
