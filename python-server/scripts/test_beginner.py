import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from paper_problem.generators.beginner import beginner_generator

async def test_beginner_generator():
    # 주의: 실제 운영환경에서는 사용자가 업로드한 PDF에서 추출한 내용이 context로 들어옵니다.
    # 이 테스트에서는 예시 학습 내용을 하드코딩했습니다.
    context = """
    Python 변수와 자료형
    - 변수는 데이터를 저장하는 공간
    - 정수(int), 실수(float), 문자열(str) 등의 자료형
    - 변수명 = 값 으로 할당
    - 예시: name = "홍길동", age = 25, height = 175.5
    """

    print("🧪 초급 문제 생성 테스트 시작...")
    print("📄 (실제 운영: PDF 기반, 테스트: 하드코딩된 내용)")
    print(f"📝 학습 내용:\n{context}\n")

    try:
        problems = await beginner_generator.generate(context, count=2)

        print(f"✅ 생성된 문제 수: {len(problems)}\n")

        for i, problem in enumerate(problems, 1):
            print(f"{'='*60}")
            print(f"문제 {i}")
            print(f"{'='*60}")
            print(f"📌 질문: {problem.question}")
            print(f"💡 정답: {problem.answer}")
            print(f"🎯 난이도: {problem.difficulty_score}/3")
            print(f"📂 타입: {problem.problem_type}")
            print(f"💭 힌트: {', '.join(problem.hints) if problem.hints else '없음'}")
            if problem.test_cases:
                print(f"🧪 테스트케이스: {len(problem.test_cases)}개")
            print()

        print("🎉 테스트 완료!")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_beginner_generator())
