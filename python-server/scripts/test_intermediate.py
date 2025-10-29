import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from paper_problem.generators.intermediate import intermediate_generator

async def test_intermediate_generator():
    # 주의: 실제 운영환경에서는 사용자가 업로드한 PDF에서 추출한 내용이 context로 들어옵니다.
    # 이 테스트에서는 예시 학습 내용을 하드코딩했습니다.
    context = """
    Python 함수와 자료구조
    - 함수 정의: def 함수명(매개변수):
    - 리스트: 순서가 있는 데이터 집합 [1, 2, 3]
    - 딕셔너리: 키-값 쌍으로 데이터 저장 {'name': '홍길동', 'age': 25}
    - 리스트 컴프리헨션: [x*2 for x in range(10)]
    - 조건문: if, elif, else
    - 반복문: for, while
    - 내장 함수: sum(), len(), max(), min()
    """

    print("🧪 중급 문제 생성 테스트 시작...")
    print("📄 (실제 운영: PDF 기반, 테스트: 하드코딩된 내용)")
    print(f"📝 학습 내용:\n{context}\n")

    try:
        problems = await intermediate_generator.generate(context, count=2)

        print(f"✅ 생성된 문제 수: {len(problems)}\n")

        for i, problem in enumerate(problems, 1):
            print(f"{'='*60}")
            print(f"문제 {i}")
            print(f"{'='*60}")
            print(f"📌 질문: {problem.question}")
            print(f"💡 정답:\n{problem.answer}")
            print(f"🎯 난이도: {problem.difficulty_score}/6 (중급)")
            print(f"📂 타입: {problem.problem_type}")
            print(f"💭 힌트: {', '.join(problem.hints) if problem.hints else '없음'}")
            if problem.test_cases:
                print(f"🧪 테스트케이스: {len(problem.test_cases)}개")
                for j, tc in enumerate(problem.test_cases[:2], 1):  # 최대 2개만 출력
                    print(f"   Case {j}: input={tc.get('input', 'N/A')[:50]}... → expected={tc.get('expected', 'N/A')[:50]}")
            print()

        print("🎉 테스트 완료!")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_intermediate_generator())
