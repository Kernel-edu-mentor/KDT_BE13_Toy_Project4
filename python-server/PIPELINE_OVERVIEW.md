# EduMentor AI Pipeline Overview

전체 시스템의 파이프라인을 간단하게 시각화한 문서입니다.

---

## 1. File Upload Pipeline

학습 자료를 업로드하고 벡터 DB에 저장하는 파이프라인

```
┌─────────┐     ┌─────────┐     ┌──────────────┐     ┌─────┐
│  File   │ ──► │  Parse  │ ──► │ Embed & Store│ ──► │ END │
│ Upload  │     │  (Node) │     │    (Node)    │     │     │
└─────────┘     └─────────┘     └──────────────┘     └─────┘
```

**노드 설명:**
- **Parse Node**: PDF/PPT 파일 파싱 (Upstage Document Parse API)
- **Embed & Store Node**: 청킹(500자) → 임베딩 → ChromaDB 배치 저장

**데이터 흐름:**
```
Input: {material_id, file_path, file_type}
  → parsed_blocks (파싱 결과)
  → chunks (청크 분할)
  → embeddings (벡터 변환)
  → ChromaDB 저장
Output: {status, page_count, chunk_count}
```

---

## 2. QA (Question-Answer) Pipeline

학습 자료 기반 질의응답 파이프라인 (개선됨 ✨)

```
┌──────────┐     ┌──────────┐
│ Question │ ──► │ Retrieve │
│          │     │  (Node)  │
└──────────┘     └─────┬────┘
                       │
                       ├─ (관련 문서 있음?)
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
    ┌──────────┐            ┌───────────┐
    │ Generate │            │ Fallback  │
    │  (Node)  │            │  (Node)   │
    └────┬─────┘            └─────┬─────┘
         │                        │
         ▼                        │
    ┌────────┐                   │
    │ Verify │                   │
    │ (Node) │                   │
    └────┬───┘                   │
         │                       │
         └───────────┬───────────┘
                     ▼
                ┌────────┐
                │  END   │
                └────────┘
```

**노드 설명:**
- **Retrieve Node**: 질문 임베딩 → ChromaDB 검색 (Top 5) + 관련성 검증
- **Fallback Node**: 관련 문서 없을 때 안내 메시지 반환
- **Generate Node**: 검색 결과 기반 답변 생성 (Solar LLM)
- **Verify Node**: 답변 품질 검증

**조건부 분기:**
- 관련 문서 있음 (distance < 0.5) → Generate → Verify → END
- 관련 문서 없음 → Fallback → END

**데이터 흐름:**
```
Input: {material_id, question}
  → query_embedding (질문 벡터화)
  → retrieved_docs (검색 결과 5개)
  → has_relevant_docs (관련성 검증)
  → [분기]
    ├─ (관련 있음) → context → answer → quality check
    └─ (관련 없음) → fallback message
Output: {answer, sources, response_time_ms, answer_quality}
```

---

## 3. Problem Generation Pipeline

학습 자료 기반 난이도별 문제 생성 파이프라인 (개선됨 ✨)

```
┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Request │►  │ Analyze │►  │  Build   │►  │ Generate │►  │ Validate │
│         │   │ Content │   │ Context  │   │  (Node)  │   │  (Node)  │
└─────────┘   │ (Node)  │   │  (Node)  │   └──────────┘   └─────┬────┘
              └─────────┘   └──────────┘          ▲              │
                                                   │              │
                                                   │              ▼
                                              ┌────────┐    ┌──────────┐
                                              │ Refine │◄───│  Enough  │
                                              │Context │ No │ Problems?│
                                              │ (Node) │    └────┬─────┘
                                              └────────┘         │
                                                                 │ Yes
                                                                 ▼
                                                             ┌───────┐
                                                             │  END  │
                                                             └───────┘
```

**노드 설명:**
- **Analyze Content Node**: ChromaDB에서 학습 내용 검색 및 분석
- **Build Context Node**: 토픽별 균등 분배 컨텍스트 구성
- **Generate Node**: 난이도별 문제 생성 (필요한 개수만 생성)
- **Validate Node**: 문제 품질 검증 및 필터링
- **Refine Context Node** ✨: rejection_reasons 분석 + 새 문서 추가 (컨텍스트 보강)

**조건부 분기:**
- 충분한 문제 생성됨 → END
- 문제 부족 + 재시도 가능 (< 5회) → Refine Context → Generate 재실행

**개선 사항:**
1. **컨텍스트 보강**: 재생성 시 새로운 문서 추가 (기존 문제: 동일 context 재사용)
2. **필요 개수만 생성**: 3개 중 1개 통과 → 2개만 재생성 (기존: 항상 3개 생성)
3. **Rejection 활용**: 거절 사유를 로깅하여 품질 개선 피드백

**데이터 흐름:**
```
Input: {material_id, difficulty, problem_count}
  → learning_content (내용 분석)
  → context (컨텍스트 구성)
  → generated_problems (생성된 문제)
  → validated_problems (검증된 문제)
  → [부족 시]
    → rejection_reasons 분석
    → enhanced_context (보강된 컨텍스트)
    → needed_count (부족한 개수만 재생성)
Output: {problems: [Problem], total_count, difficulty}
```

---

## 4. Answer Grading Pipeline

학생 답변 채점 파이프라인 (개선됨 ✨)

```
┌─────────────┐     ┌──────────┐     ┌───────┐     ┌────────┐
│ Student     │ ──► │ Validate │ ──► │ Grade │ ──► │ Verify │
│ Answer      │     │  Input   │     │(Node) │     │ (Node) │
└─────────────┘     │  (Node)  │     └───┬───┘     └────┬───┘
                    └──────────┘         │              │
                                         │              ▼
                                         │         ┌──────────┐
                                         │         │Confident?│
                                         │         └────┬─────┘
                                         │              │
                                         │    ┌─────────┴──────┐
                                         │    │                │
                                         │   No (retry < 2)   Yes
                                         │    │                │
                                         └────┘                ▼
                                                          ┌─────┐
                                                          │ END │
                                                          └─────┘
```

**노드 설명:**
- **Validate Input Node**: 빈 답변 체크 + 문제 타입 검증
- **Grade Node**: 문제 타입별 채점 실행 (SHORT_ANSWER/CODING)
- **Verify Node**: 채점 결과 신뢰도 검증 (confidence_score)

**채점자 선택:**
- **ShortAnswerGrader**: LLM 기반 의미적 유사도 평가
- **CodingGrader**: 코드 실행 + 테스트 케이스 검증

**조건부 분기:**
- 신뢰도 높음 (confidence > 0.3) → END
- 신뢰도 낮음 + 재시도 가능 (< 2회) → Grade 재실행

**개선 사항:**
1. **입력 검증**: 빈 답변이나 잘못된 문제 타입을 사전에 필터링
2. **신뢰도 기반 재시도**: LLM 응답이 불확실하면 자동 재채점
3. **품질 보장**: 점수 범위 검증 + confidence_score 추적

**데이터 흐름:**
```
Input: {problem, user_answer}
  → input_validation (빈 답변/타입 검증)
  → grader_selection (SHORT_ANSWER/CODING)
  → grading_execution (채점 실행)
  → confidence_score (신뢰도 계산)
  → [낮은 신뢰도] → 재채점 (최대 2회)
Output: {score, feedback, is_correct, confidence_score}
```

---

## System Architecture Overview

```
┌───────────────────────────────────────────────────────────────┐
│                      Spring Boot Backend                      │
│  (파일 업로드, 사용자 관리, 문제/답변 저장)                    │
└────────────────┬──────────────────────────────────────────────┘
                 │
                 │ HTTP API
                 │
┌────────────────▼──────────────────────────────────────────────┐
│                   Python FastAPI Server                       │
│                                                               │
│  ┌─────────────┐              ┌─────────────────┐           │
│  │  paper_qa   │              │ paper_problem   │           │
│  │  (Team 1)   │              │   (Team 2)      │           │
│  ├─────────────┤              ├─────────────────┤           │
│  │ • Upload    │              │ • Generate      │           │
│  │ • QA        │              │ • Validate      │           │
│  └──────┬──────┘              │ • Grade         │           │
│         │                     └────────┬────────┘           │
│         │                              │                     │
└─────────┼──────────────────────────────┼─────────────────────┘
          │                              │
          ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Shared Infrastructure                    │
│                                                             │
│  ┌────────────┐      ┌────────────┐      ┌──────────────┐ │
│  │ ChromaDB   │      │  Upstage   │      │  LangChain   │ │
│  │ Vector DB  │      │    API     │      │  LangGraph   │ │
│  │            │      │            │      │              │ │
│  │ • 임베딩    │      │ • 임베딩    │      │ • 워크플로우 │ │
│  │ • 검색     │      │ • LLM      │      │ • 상태 관리  │ │
│  │ • 저장     │      │ • 파싱     │      │              │ │
│  └────────────┘      └────────────┘      └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Pipeline Execution Times

| Pipeline | Average Time | Components | Notes |
|----------|--------------|------------|-------|
| **Upload** | 5~10분 (문서 크기 의존) | Parse (300초) + Embed (240초) + Store (27초) | 변화 없음 |
| **QA** | 1.0~1.5초 | Retrieve (0.2초) + Verify (0.1초) + Generate (0.8초) + Verify (0.1초) | +0.2초 (검증 추가) |
| **Problem Generation** | 12~20초 | Analyze (2초) + Build (1초) + Generate (8초) + Validate (2초) + Refine (1초, 재시도 시) | 재생성 시 +1~5초 |
| **Answer Grading** | 0.5~2.5초 | Validate (0.1초) + Grade (0.5초) + Verify (0.1초) | 재채점 시 +0.5초 |

---

## Key Technologies

```
┌─────────────────────────────────────────────────────────────┐
│ LangGraph: 워크플로우 오케스트레이션                          │
│  • StateGraph: 상태 기반 그래프 워크플로우                    │
│  • Node: 각 처리 단계를 비동기 함수로 구현                   │
│  • Edge: 노드 간 데이터 흐름 정의                            │
│  • Conditional Edge: 조건부 분기 (재생성 로직 등)            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ChromaDB: 벡터 데이터베이스                                   │
│  • Collection: learning_materials                           │
│  • Metadata: {material_id, page, type}                      │
│  • Search: 코사인 유사도 기반 검색                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Upstage API: AI 서비스                                       │
│  • Embedding: 4096차원 벡터 생성                             │
│  • Solar LLM: 답변/문제 생성                                 │
│  • Document Parse: PDF/PPT 파싱                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary

```
1. 파일 업로드 → 파싱 → 청킹 → 임베딩 → ChromaDB 저장
                                              │
                                              ▼
2. 질문 → 임베딩 → ChromaDB 검색 → LLM 답변 ───┘

3. 문제 요청 → ChromaDB 검색 → 컨텍스트 구성 → LLM 문제 생성 → 검증
                                                                │
                                                                ▼
4. 답변 제출 → 채점자 선택 → 채점 실행 → 루브릭 적용 → 점수/피드백
```