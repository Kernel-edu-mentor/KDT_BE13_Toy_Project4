import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from paper_problem.utils.context_builder import ContextBuilder


def run_build_context_respects_token_limit():
    builder = ContextBuilder()
    documents = [
        {"page": 1, "content": "A" * 200},  # about 50 tokens
        {"page": 2, "content": "B" * 200},  # about 50 tokens
        {"page": 3, "content": "C" * 200},  # about 50 tokens
    ]

    context = builder.build_context(documents, difficulty="BEGINNER", max_tokens=120)

    lines = context.split("\n\n---\n\n")
    assert len(lines) == 2, "토큰 제한을 초과하여 문서를 추가했습니다."
    assert "[페이지 1]" in lines[0]
    assert "[페이지 2]" in lines[1]


def run_build_context_handles_missing_fields():
    builder = ContextBuilder()
    documents = [
        {"content": "Introduction to Algorithms"},
        {"page": 5},  # missing content, should be skipped
        {"page": 6, "content": ""},
    ]

    context = builder.build_context(documents, difficulty="INTERMEDIATE", max_tokens=500)

    assert "[페이지 알 수 없음]" in context, "페이지 정보가 없을 때 기본 문구가 누락되었습니다."
    assert "Introduction to Algorithms" in context, "콘텐츠가 누락되었습니다."
    assert "[페이지 5]" not in context, "비어 있는 문서는 포함되지 않아야 합니다."
    assert context.count("[페이지") == 1, "빈 콘텐츠 필터링 결과가 예상과 다릅니다."


def run_all():
    run_build_context_respects_token_limit()
    run_build_context_handles_missing_fields()
    print("ContextBuilder 점검을 통과했습니다.")


if __name__ == "__main__":
    run_all()
