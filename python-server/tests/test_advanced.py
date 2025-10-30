import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from paper_problem.generators.advanced import advanced_generator

async def test_advanced_generator():
    # 주의: 실제 운영환경에서는 사용자가 업로드한 PDF에서 추출한 내용이 context로 들어옵니다.
    # 이 테스트에서는 예시 학습 내용을 하드코딩했습니다.
    context = """
    Python 고급 프로그래밍
    - 데코레이터: 함수를 감싸서 기능 확장 @decorator
    - 제너레이터: yield로 메모리 효율적 반복 처리
    - 컨텍스트 매니저: with 문으로 리소스 자동 관리
    - 멀티스레딩/멀티프로세싱: concurrent.futures, asyncio
    - 메타클래스: 클래스 생성 과정 제어
    - 디자인 패턴: Singleton, Factory, Observer, Strategy
    - 성능 최적화: 프로파일링, 메모이제이션, 알고리즘 복잡도
    - 타입 힌팅: typing 모듈, Generics, Protocol
    """

    print("🧪 고급 문제 생성 테스트 시작...")
    print("📄 (실제 운영: PDF 기반, 테스트: 하드코딩된 내용)")
    print(f"📝 학습 내용:\n{context}\n")

    try:
        problems = await advanced_generator.generate(context, count=2)

        print(f"✅ 생성된 문제 수: {len(problems)}\n")

        for i, problem in enumerate(problems, 1):
            print(f"{'='*60}")
            print(f"문제 {i}")
            print(f"{'='*60}")
            print(f"📌 질문: {problem.question}")
            print(f"💡 정답:\n{problem.answer}")
            print(f"🎯 난이도: {problem.difficulty_score}/10 (고급)")
            print(f"📂 타입: {problem.problem_type}")
            print(f"💭 힌트: {', '.join(problem.hints) if problem.hints else '없음'}")
            if problem.test_cases:
                print(f"🧪 테스트케이스: {len(problem.test_cases)}개")
                for j, tc in enumerate(problem.test_cases[:3], 1):  # 최대 3개 출력
                    tc_input = tc.get('input', 'N/A')
                    tc_expected = tc.get('expected', 'N/A')
                    print(f"   Case {j}: {tc_input[:40]}... → {tc_expected[:40]}...")
            print()

        print("🎉 테스트 완료!")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_advanced_generator())
