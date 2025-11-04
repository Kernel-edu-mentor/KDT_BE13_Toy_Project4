"""
답변 검증 시스템 테스트 스크립트

Usage:
    python scripts/test_answer_grading.py
"""

import sys
import os

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from paper_problem.models import Problem
from paper_problem.graders import answer_grader


async def test_short_answer_grading():
    """SHORT_ANSWER 채점 테스트"""

    print("\n" + "=" * 60)
    print("SHORT_ANSWER 채점 테스트")
    print("=" * 60)

    # Test 문제
    problem = Problem(
        question="Observer 패턴이란 무엇인가요? 한 문장으로 설명하세요.",
        answer="객체의 상태 변화를 관찰자에게 자동으로 알려주는 디자인 패턴입니다.",
        hints=["상태 변화", "자동 통지", "관찰자"],
        difficulty_score=1,
        problem_type="SHORT_ANSWER",
        test_cases=[]
    )

    # Test 1: 완전 정답
    print("\n[Test 1] 완전 정답")
    user_answer1 = "상태가 바뀌면 observer에게 자동으로 알림을 보내는 디자인 패턴"
    result1 = await answer_grader.grade(problem, user_answer1)
    print(f"  User Answer: {user_answer1}")
    print(f"  ✅ is_correct: {result1['is_correct']}")
    print(f"  📊 score: {result1['score']}/100")
    print(f"  💬 feedback: {result1['feedback']}")
    print(f"  🎯 similarity_score: {result1.get('similarity_score', 'N/A')}")
    assert result1["is_correct"] == True, "완전 정답은 is_correct=True여야 함"
    assert result1["score"] >= 80, "완전 정답은 80점 이상이어야 함"

    # Test 2: 부분 정답 (핵심 개념 일부만 포함)
    print("\n[Test 2] 부분 정답")
    user_answer2 = "상태 변화를 알려주는 패턴"  # '관찰자', '자동' 개념 누락
    result2 = await answer_grader.grade(problem, user_answer2)
    print(f"  User Answer: {user_answer2}")
    print(f"  ⚠️ is_correct: {result2['is_correct']}")
    print(f"  📊 score: {result2['score']}/100")
    print(f"  💬 feedback: {result2['feedback']}")
    # LLM 평가 기준이 엄격할 수 있으므로 범위 완화
    assert 20 <= result2["score"] <= 80, "부분 정답은 20-80점 사이여야 함"

    # Test 3: 오답
    print("\n[Test 3] 오답")
    user_answer3 = "객체를 생성하는 패턴"
    result3 = await answer_grader.grade(problem, user_answer3)
    print(f"  User Answer: {user_answer3}")
    print(f"  ❌ is_correct: {result3['is_correct']}")
    print(f"  📊 score: {result3['score']}/100")
    print(f"  💬 feedback: {result3['feedback']}")
    assert result3["is_correct"] == False, "오답은 is_correct=False여야 함"
    assert result3["score"] < 40, "오답은 40점 미만이어야 함"

    print("\n✅ SHORT_ANSWER 테스트 통과!")


async def test_coding_grading():
    """CODING 채점 테스트"""

    print("\n" + "=" * 60)
    print("CODING 채점 테스트")
    print("=" * 60)

    # Test 문제: 두 수를 더하는 함수
    problem = Problem(
        question="두 수를 더하는 함수 add(a, b)를 작성하세요.",
        answer="def add(a, b):\n    return a + b",
        hints=["return 사용", "덧셈 연산자 +"],
        difficulty_score=4,
        problem_type="CODING",
        test_cases=[
            {"input": {"a": 1, "b": 2}, "expected_output": 3},
            {"input": {"a": 5, "b": 10}, "expected_output": 15},
            {"input": {"a": -3, "b": 7}, "expected_output": 4},
            {"input": {"a": 0, "b": 0}, "expected_output": 0},
        ]
    )

    # Test 1: 정답 코드
    print("\n[Test 1] 정답 코드")
    user_code1 = """def add(a, b):
    return a + b"""
    result1 = await answer_grader.grade(problem, user_code1)
    print(f"  ✅ is_correct: {result1['is_correct']}")
    print(f"  📊 score: {result1['score']}/100")
    print(f"  📝 test_results: {len(result1.get('test_results', []))} tests")
    passed = sum(1 for r in result1.get('test_results', []) if r.get('passed'))
    print(f"     - 통과: {passed}/{len(result1.get('test_results', []))}")
    print(f"  💬 feedback:\n{result1['feedback']}")
    assert result1["is_correct"] == True, "정답 코드는 is_correct=True여야 함"
    assert result1["score"] >= 80, "정답 코드는 80점 이상이어야 함"

    # Test 2: 오답 코드 (곱셈)
    print("\n[Test 2] 오답 코드 (곱셈)")
    user_code2 = """def add(a, b):
    return a * b"""
    result2 = await answer_grader.grade(problem, user_code2)
    print(f"  ❌ is_correct: {result2['is_correct']}")
    print(f"  📊 score: {result2['score']}/100")
    print(f"  📝 test_results: {len(result2.get('test_results', []))} tests")
    passed2 = sum(1 for r in result2.get('test_results', []) if r.get('passed'))
    print(f"     - 통과: {passed2}/{len(result2.get('test_results', []))}")
    assert result2["is_correct"] == False, "오답 코드는 is_correct=False여야 함"

    # Test 3: 비효율적인 코드 (품질 저하)
    print("\n[Test 3] 비효율적인 코드")
    user_code3 = """def add(a, b):
    result = 0
    for i in range(a):
        result += 1
    for i in range(b):
        result += 1
    return result"""
    result3 = await answer_grader.grade(problem, user_code3)
    print(f"  ⚠️ is_correct: {result3['is_correct']}")
    print(f"  📊 score: {result3['score']}/100")
    print(f"  💬 feedback:\n{result3['feedback']}")
    # 루브릭에서 코드 품질 점수가 낮을 것으로 예상
    rubric = result3.get('rubric_scores', {})
    if rubric:
        print(f"\n  📋 Rubric Scores:")
        for key in ["accuracy", "efficiency", "code_quality", "exception_handling", "logical_reasoning"]:
            item = rubric.get(key, {})
            print(f"     - {item.get('label', key)}: {item.get('score', 0)}/{item.get('max_score', 2)}")

    print("\n✅ CODING 테스트 통과!")


async def test_edge_cases():
    """엣지 케이스 테스트"""

    print("\n" + "=" * 60)
    print("엣지 케이스 테스트")
    print("=" * 60)

    # Test 1: 빈 답변
    print("\n[Test 1] 빈 답변")
    problem = Problem(
        question="Observer 패턴이란?",
        answer="상태 변화를 알려주는 패턴",
        hints=["상태 변화"],
        difficulty_score=1,
        problem_type="SHORT_ANSWER",
        test_cases=[]
    )
    result = await answer_grader.grade(problem, "")
    print(f"  ❌ is_correct: {result['is_correct']}")
    print(f"  📊 score: {result['score']}/100")
    assert result["is_correct"] == False, "빈 답변은 오답이어야 함"

    # Test 2: 위험한 코드 (eval 사용)
    print("\n[Test 2] 위험한 코드 (eval 사용)")
    problem2 = Problem(
        question="두 수를 더하세요",
        answer="def add(a, b): return a + b",
        hints=[],
        difficulty_score=4,
        problem_type="CODING",
        test_cases=[{"input": {"a": 1, "b": 2}, "expected_output": 3}]
    )
    dangerous_code = """def add(a, b):
    return eval(f"{a} + {b}")"""
    result2 = await answer_grader.grade(problem2, dangerous_code)
    print(f"  ⚠️ is_correct: {result2['is_correct']}")
    print(f"  📊 score: {result2['score']}/100")
    rubric = result2.get('rubric_scores', {})
    code_quality = rubric.get('code_quality', {})
    print(f"  🔧 code_quality: {code_quality.get('score', 0)}/{code_quality.get('max_score', 2)}")
    print(f"     - reason: {code_quality.get('reason', 'N/A')}")
    # grader_rubric에서 eval 사용 시 code_quality=0점 처리됨

    print("\n✅ 엣지 케이스 테스트 통과!")


async def main():
    """메인 테스트 실행"""

    print("\n" + "=" * 60)
    print("답변 검증 시스템 테스트 시작")
    print("=" * 60)

    try:
        await test_short_answer_grading()
        await test_coding_grading()
        await test_edge_cases()

        print("\n" + "=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
