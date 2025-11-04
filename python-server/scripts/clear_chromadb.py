#!/usr/bin/env python3
"""ChromaDB의 모든 데이터를 삭제하는 스크립트"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.chroma_client import chroma_client

def clear_all_data():
    """ChromaDB의 learning_materials collection을 삭제"""

    if chroma_client.client is None:
        print("❌ ChromaDB 클라이언트가 초기화되지 않았습니다.")
        return

    collection_name = "learning_materials"

    try:
        # 기존 컬렉션 확인
        collections = chroma_client.client.list_collections()
        print(f"📋 현재 컬렉션: {[c.name for c in collections]}")

        # Collection 삭제
        chroma_client.client.delete_collection(name=collection_name)
        print(f"✅ Collection '{collection_name}' 삭제 완료")

        # 확인
        collections_after = chroma_client.client.list_collections()
        print(f"📋 삭제 후 컬렉션: {[c.name for c in collections_after]}")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    clear_all_data()
