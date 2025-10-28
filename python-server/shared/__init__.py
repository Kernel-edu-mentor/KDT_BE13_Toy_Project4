# shared/__init__.py

# 다른 파일에서 'from shared import chroma_client, upstage_client' 처럼
# 싱글톤 인스턴스를 직접 임포트할 수 있도록 노출합니다.

from .chroma_client import chroma_client
from .upstage_client import upstage_client
