"""
ChromaDB에 실제로 저장된 내용 확인 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.chroma_client import chroma_client
from shared.upstage_client import upstage_client
import asyncio


async def verify_material_content(material_id: int, keywords: list):
    """특정 material_id의 내용과 키워드 검색 결과 확인"""

    print(f"\n{'='*80}")
    print(f"Material ID: {material_id}")
    print(f"검색 키워드: {keywords}")
    print(f"{'='*80}\n")

    for keyword in keywords:
        print(f"\n--- 키워드: '{keyword}' 검색 결과 ---\n")

        # 키워드를 임베딩으로 변환
        query_embedding = await upstage_client.embed_query(keyword)

        # ChromaDB 검색
        results = chroma_client.search(
            collection_name="learning_materials",
            query_embeddings=[query_embedding],
            n_results=5,
            filter_dict={"material_id": material_id}
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            print(f"❌ '{keyword}'에 대한 검색 결과 없음!")
            continue

        print(f"✅ {len(documents)}개 문서 발견\n")

        for i, (doc, meta) in enumerate(zip(documents, metadatas), 1):
            print(f"[문서 {i}]")
            print(f"페이지: {meta.get('page', '?')}")
            print(f"내용 미리보기 (처음 200자):")
            print(f"{doc[:200]}...\n")
            print("-" * 80)


async def main():
    # 테스트: material_id 30번의 observer패턴, prototype패턴 검색
    await verify_material_content(
        material_id=30,
        keywords=["observer패턴", "prototype패턴"]
    )


if __name__ == "__main__":
    asyncio.run(main())
