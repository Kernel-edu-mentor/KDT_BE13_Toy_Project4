"""
공통 모듈 패키지
ChromaDB 클라이언트와 Upstage API 클라이언트를 제공합니다.
"""

from shared.chroma_client import chroma_client

try:
    from shared.upstage_client import upstage_client  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - 테스트 환경 대비
    upstage_client = None

__all__ = ['chroma_client', 'upstage_client']
