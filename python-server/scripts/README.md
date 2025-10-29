# Scripts 디렉터리

팀별 개발/테스트를 위한 유틸리티 스크립트 모음

---

## 📁 파일 목록

### `seed_test_data.py`
팀2 문제 생성 개발/테스트용 샘플 데이터 삽입 스크립트

**용도:**
- 팀1 없이 팀2가 독립적으로 문제 생성 기능 테스트
- ChromaDB에 학습 자료 샘플 데이터 직접 삽입

**포함된 샘플 데이터:**
- Material 1: Spring Boot JPA (5개 블록, 상세한 예제 포함)
- Material 2: Python FastAPI (2개 블록)

**실행 방법:**
```bash
# 1. ChromaDB 실행 확인
docker ps | grep chromadb

# 2. Python 서버가 꺼져있어야 함 (포트 충돌 방지)
# 또는 서버가 실행 중이어도 됨

# 3. 스크립트 실행
python scripts/seed_test_data.py
```

**출력 예시:**
```
============================================================
🌱 팀2 테스트용 샘플 데이터 삽입 시작
============================================================

📦 Material 1 샘플 데이터 삽입 중...
🔄 5개 블록 임베딩 생성 중...
✅ Material 1: 5개 블록 저장 완료

📦 Material 2 샘플 데이터 삽입 중...
🔄 2개 블록 임베딩 생성 중...
✅ Material 2: 2개 블록 저장 완료

============================================================
✅ 모든 샘플 데이터 삽입 완료!
============================================================
```

**이후 테스트:**
```bash
# 서버 실행
python main.py

# 문제 생성 API 테스트
curl -X POST http://localhost:8000/problems/generate \
  -H "Content-Type: application/json" \
  -d '{
    "material_id": 1,
    "difficulty": "BEGINNER",
    "problem_count": 3
  }'
```

---

## 🎯 팀별 개발 워크플로우

### 팀1 (QA 시스템) 개발
```bash
# 1. 서버 실행
python main.py

# 2. PDF 업로드 테스트
curl -X POST http://localhost:8000/qa/upload \
  -F "file=@test.pdf" \
  -F "material_id=1"

# 3. 질문 테스트
curl -X POST http://localhost:8000/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"material_id": 1, "question": "JPA란?"}'
```

### 팀2 (문제 생성) 개발
```bash
# 1. 샘플 데이터 삽입 (최초 1회만)
python scripts/seed_test_data.py

# 2. 서버 실행
python main.py

# 3. 문제 생성 테스트
curl -X POST http://localhost:8000/problems/generate \
  -H "Content-Type: application/json" \
  -d '{
    "material_id": 1,
    "difficulty": "BEGINNER",
    "problem_count": 3
  }'
```

---

## 🔧 샘플 데이터 수정

`seed_test_data.py`의 `SAMPLE_MATERIALS` 딕셔너리를 수정하여 원하는 학습 자료 추가 가능:

```python
SAMPLE_MATERIALS = {
    1: [
        {
            "content": "여기에 학습 내용 작성",
            "page": 1
        },
        # ... 더 많은 블록
    ],
    # 새로운 material_id 추가 가능
    3: [
        {
            "content": "새로운 주제의 학습 자료",
            "page": 1
        }
    ]
}
```

---

## 🧹 데이터 초기화

ChromaDB 데이터를 완전히 초기화하려면:

```bash
# ChromaDB 컨테이너 재시작 (데이터 삭제)
docker stop chromadb
docker rm chromadb
docker run -d -p 8001:8000 --name chromadb chromadb/chroma:latest

# 샘플 데이터 재삽입
python scripts/seed_test_data.py
```

---

## 📝 참고사항

- 샘플 데이터는 Upstage Embedding API를 사용하므로 `.env`에 `UPSTAGE_API_KEY` 필요
- ChromaDB가 실행 중이어야 함 (`localhost:8001`)
- 스크립트 실행 시 Python 서버가 꺼져있어도 됨 (공유 ChromaDB 사용)
