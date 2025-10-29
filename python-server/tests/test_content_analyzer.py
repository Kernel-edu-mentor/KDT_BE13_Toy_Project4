import asyncio
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from paper_problem.utils.content_analyzer import ContentAnalyzer
from paper_problem.utils import content_analyzer as content_analyzer_module


def _build_search_result(ids, documents, metadatas):
    return {
        "ids": [ids],
        "documents": [documents],
        "metadatas": [metadatas],
    }


def run_analyze_material_collects_unique_documents():
    analyzer = ContentAnalyzer()
    calls = []

    sample_results = {
        "기본": _build_search_result(
            ids=["doc-1", "doc-2"],
            documents=["Class Diagram basics", "Inheritance overview"],
            metadatas=[{"page": 1, "type": "text"}, {"page": 2, "type": "text"}],
        ),
        "개념": _build_search_result(
            ids=["doc-2", "doc-3"],
            documents=["Inheritance overview", "Polymorphism explained"],
            metadatas=[{"page": 2, "type": "text"}, {"page": 3, "type": "text"}],
        ),
        "정의": _build_search_result(
            ids=[],
            documents=[],
            metadatas=[],
        ),
        "예제": _build_search_result(
            ids=["doc-4"],
            documents=["Factory Method Example"],
            metadatas=[{"page": 4, "type": "code"}],
        ),
        "소개": _build_search_result(
            ids=["doc-1"],
            documents=["Class Diagram basics"],
            metadatas=[{"page": 1, "type": "text"}],
        ),
    }

    def fake_search(collection_name, query_texts, n_results, filter_dict):
        keyword = query_texts[0]
        calls.append(
            {
                "collection_name": collection_name,
                "keyword": keyword,
                "n_results": n_results,
                "filter_dict": filter_dict,
            }
        )
        return sample_results[keyword]

    original_search = content_analyzer_module.chroma_client.search
    try:
        content_analyzer_module.chroma_client.search = fake_search
        result = asyncio.run(analyzer.analyze_material(material_id=7, difficulty="BEGINNER"))
    finally:
        content_analyzer_module.chroma_client.search = original_search

    assert result["total_count"] == 4, "문서 총합이 예상과 다릅니다."
    assert {doc["content"] for doc in result["documents"]} == {
        "Class Diagram basics",
        "Inheritance overview",
        "Polymorphism explained",
        "Factory Method Example",
    }, "수집된 문서 내용이 기대와 다릅니다."

    assert len(calls) == len(sample_results), "검색 호출 횟수가 예상과 다릅니다."
    assert all(call["collection_name"] == "learning_materials" for call in calls), "컬렉션 이름이 잘못되었습니다."
    assert all(call["filter_dict"] == {"material_id": 7} for call in calls), "검색 필터가 잘못되었습니다."
    assert all(call["n_results"] == 5 for call in calls), "결과 수가 전략과 다릅니다."


def run_analyze_material_rejects_unknown_difficulty():
    analyzer = ContentAnalyzer()
    try:
        asyncio.run(analyzer.analyze_material(material_id=1, difficulty="novice"))
    except ValueError:
        return

    raise AssertionError("알 수 없는 난이도에서 ValueError가 발생하지 않았습니다.")


def run_extract_key_concepts_picks_capitalized_words():
    analyzer = ContentAnalyzer()
    documents = [
        {"content": "Graph Algorithms rely on Dijkstra and BellmanFord techniques."},
        {"content": "non matching text"},
        {"content": "Classes like UserProfile and SessionManager handle Auth."},
    ]

    concepts = analyzer.extract_key_concepts(documents)

    expected = {
        "Graph",
        "Algorithms",
        "Dijkstra",
        "BellmanFord",
        "Classes",
        "UserProfile",
        "SessionManager",
        "Auth",
    }

    assert expected.issuperset(set(concepts)), "추출된 개념이 기대 집합에 포함되지 않습니다."
    assert len(concepts) <= len(expected), "추출된 개념 수가 예상보다 많습니다."


def run_all():
    run_analyze_material_collects_unique_documents()
    run_analyze_material_rejects_unknown_difficulty()
    run_extract_key_concepts_picks_capitalized_words()
    print("모든 ContentAnalyzer 점검을 통과했습니다.")


if __name__ == "__main__":
    run_all()
