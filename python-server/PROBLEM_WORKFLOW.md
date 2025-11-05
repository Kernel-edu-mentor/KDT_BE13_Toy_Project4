# Problem Generation System - LangGraph Workflow

LLM 기반 학습 문제 자동 생성 시스템의 LangGraph 워크플로우

---

## Problem Workflow (개선됨 ✨)

```mermaid
graph TD
    Start([START]) --> Analyze[analyze_content_node<br/>학습 내용 분석<br/><b>⏱️ 2~3초</b>]
    Analyze --> Build[build_context_node<br/>컨텍스트 구성<br/><b>⏱️ ~0.01초</b>]
    Build --> Generate[generate_problems_node<br/>문제 생성<br/><b>⏱️ 3~5초</b>]
    Generate --> Validate[validate_problems_node<br/>문제 검증<br/><b>⏱️ ~0.01초</b>]
    Validate --> Decision{should_regenerate<br/>재생성 판단<br/><b>⏱️ ~0.01초</b>}

    Decision -->|충분한 문제<br/>또는<br/>최대 재시도| End([END])
    Decision -->|문제 부족<br/>retry < 5| Refine[refine_context_node ✨<br/>컨텍스트 보강<br/><b>⏱️ 1초</b>]
    Refine --> Generate

    style Analyze fill:#e1f5ff
    style Build fill:#fff4e1
    style Generate fill:#ffe5e5
    style Validate fill:#e5f5e5
    style Decision fill:#ffe5f5
    style Refine fill:#ffe5ff
```

### 성능 지표

| 단계 | 평균 시간 | 주요 작업 | 비고 |
|------|---------|----------|------|
| **Analyze** | 2~3초 | LLM 토픽 추출 + ChromaDB 검색 | 토픽 제공시 ~0.2초 |
| **Build** | ~0.01초 | 라운드 로빈 컨텍스트 구성 | 빠른 텍스트 처리 |
| **Generate** | 3~5초 | Solar LLM 문제 생성 | 난이도/개수 영향 |
| **Validate** | ~0.01초 | 검증 로직 실행 | 빠른 규칙 검사 |
| **Decision** | ~0.01초 | 재생성 판단 | 조건 체크만 |
| **Total (1회)** | **5~8초** | 재시도 없이 성공 | |
| **Total (재시도)** | **10~25초** | 최대 5회 재시도 포함 | retry_count 영향 |

---

## State: ProblemState

```mermaid
classDiagram
    class ProblemState {
        +int material_id
        +str difficulty
        +int problem_count
        +str learning_description
        +List~str~ learning_topics
        +Dict learning_content
        +str context
        +List~Problem~ generated_problems
        +List~Problem~ validated_problems
        +List~str~ rejection_reasons
        +int retry_count
        +int needed_count ✨
    }

    class Problem {
        +str question
        +str answer
        +List~str~ hints
        +int difficulty_score
        +str problem_type
        +List~Dict~ test_cases
    }

    ProblemState --> Problem
```

---

## 노드 1: analyze_content_node (⏱️ 2~3초)

### 학습 내용 분석

```mermaid
flowchart TD
    A[입력] --> B{learning_topics<br/>있음?}
    B -->|No| C[TopicExtractor<br/>LLM 키워드 추출<br/><i>~2초</i>]
    B -->|Yes| D[키워드 사용<br/><i>~0초</i>]
    C --> D
    D --> E[ContentAnalyzer<br/>ChromaDB 검색<br/><i>~0.2초/토픽</i>]
    E --> F[난이도별<br/>검색 전략 적용<br/><i>~0.1초</i>]
    F --> G[토픽별<br/>문서 그룹화<br/><i>~0.1초</i>]
    G --> H[learning_content<br/>반환]

    style C fill:#ffe5e5
    style E fill:#e5f5e5
    style G fill:#fff4e1
```

**세부 처리 단계**:
1. **토픽 추출** (~2초 or ~0초): LLM으로 키워드 추출 (이미 제공되면 스킵)
2. **ChromaDB 검색** (~0.2초/토픽): 각 토픽별로 관련 문서 검색
3. **난이도별 전략 적용** (~0.1초): BEGINNER 5개, INTERMEDIATE 7개, ADVANCED 10개
4. **문서 그룹화** (~0.1초): 토픽별로 검색 결과 정리

### 주제 추출 과정

```mermaid
sequenceDiagram
    participant U as User Input
    participant T as TopicExtractor
    participant L as Solar LLM
    participant K as Keywords

    U->>T: "iterator패턴과 composite패턴 공부했어"
    T->>L: 키워드 추출 프롬프트
    Note over L: 기술 용어, 개념명만 추출<br/>3~7개 압축
    L-->>K: ["iterator패턴", "composite패턴"]
    K-->>T: learning_topics
```

### 난이도별 검색 전략

```mermaid
graph TB
    subgraph "BEGINNER"
        B1[키워드:<br/>기본, 개념, 정의]
        B2[검색 수: 5개/토픽]
        B3[전략: 기본 개념]
    end

    subgraph "INTERMEDIATE"
        I1[키워드:<br/>구현, 응용, 실습]
        I2[검색 수: 7개/토픽]
        I3[전략: 실습 예제]
    end

    subgraph "ADVANCED"
        A1[키워드:<br/>최적화, 패턴, 설계]
        A2[검색 수: 10개/토픽]
        A3[전략: 고급 개념]
    end

    style B1 fill:#e1f5ff
    style I1 fill:#fff4e1
    style A1 fill:#ffe5e5
```

### 토픽별 문서 그룹화

```mermaid
graph LR
    A[ChromaDB 검색] --> B[documents_by_topic]

    B --> C[iterator패턴:<br/>doc1, doc2, doc3]
    B --> D[composite패턴:<br/>doc4, doc5, doc6]

    style C fill:#e5f5ff
    style D fill:#ffe5e5
```

---

## 노드 2: build_context_node

### 라운드 로빈 방식 균등 분배

```mermaid
flowchart TD
    A[documents_by_topic] --> B[토픽별 인덱스 초기화]
    B --> C{토큰 제한<br/>도달?}
    C -->|No| D[토픽1에서<br/>문서 1개 선택]
    D --> E[토픽2에서<br/>문서 1개 선택]
    E --> F[컨텍스트에 추가]
    F --> C
    C -->|Yes| G[context 반환]

    style D fill:#e5f5ff
    style E fill:#ffe5e5
    style F fill:#fff4e1
```

### 균등 분배 예시

```mermaid
sequenceDiagram
    participant C as ContextBuilder
    participant T1 as iterator패턴
    participant T2 as composite패턴
    participant Ctx as Context

    Note over C: 라운드 로빈 시작

    C->>T1: 문서 선택 (idx=0)
    T1-->>Ctx: [주제: iterator | 페이지 316]
    C->>T2: 문서 선택 (idx=0)
    T2-->>Ctx: [주제: composite | 페이지 214]

    C->>T1: 문서 선택 (idx=1)
    T1-->>Ctx: [주제: iterator | 페이지 320]
    C->>T2: 문서 선택 (idx=1)
    T2-->>Ctx: [주제: composite | 페이지 218]

    Note over Ctx: 토큰 제한 도달
```

### 토픽 편향 방지

```mermaid
graph LR
    subgraph "개선 전 (순차 처리)"
        A1[iterator 7개] --> A2[토큰 제한 도달]
        A3[composite 0개] -.포함 안됨.-> A2
    end

    subgraph "개선 후 (라운드 로빈)"
        B1[iterator 3개] --> B3[균등 분배]
        B2[composite 3개] --> B3
    end

    style A1 fill:#ffe5e5
    style A3 fill:#ffe5e5
    style B3 fill:#e5f5e5
```

---

## 노드 3: generate_problems_node (⏱️ 3~5초)

### 난이도별 생성기 선택

```mermaid
flowchart TD
    A[context + difficulty] --> B{난이도<br/><i>~0초</i>}
    B -->|BEGINNER| C[BeginnerGenerator]
    B -->|INTERMEDIATE| D[IntermediateGenerator]
    B -->|ADVANCED| E[AdvancedGenerator]

    C --> F[Solar LLM<br/>temperature=0.7<br/><i>~3~5초</i>]
    D --> F
    E --> F

    F --> G[JSON 파싱<br/><i>~0.01초</i>]
    G --> H{파싱 성공?}
    H -->|No| I[clean_and_parse_json<br/>에러 복구<br/><i>~0.01초</i>]
    H -->|Yes| J[Problem 모델 변환<br/><i>~0.01초</i>]
    I --> J
    J --> K[generated_problems]

    style C fill:#e1f5ff
    style D fill:#fff4e1
    style E fill:#ffe5e5
    style F fill:#ffe5e5
    style I fill:#ffe5f5
```

**세부 처리 단계**:
1. **Generator 선택** (~0초): 난이도에 따른 조건 분기
2. **프롬프트 구성** (~0.01초): 컨텍스트 + 난이도별 프롬프트 템플릿
3. **LLM 생성** (~3-5초): Solar-1-mini-chat으로 JSON 형태 문제 생성
4. **JSON 파싱** (~0.01초): 응답을 Python 딕셔너리로 변환 (에러 복구 포함)
5. **모델 변환** (~0.01초): Problem 모델 객체로 변환

### 난이도별 문제 유형

```mermaid
graph TB
    subgraph "BEGINNER (초급)"
        B1[용어 정의]
        B2[코드 읽기 1-3줄]
        B3[빈칸 채우기]
        B4[problem_type:<br/>SHORT_ANSWER만]
    end

    subgraph "INTERMEDIATE (중급)"
        I1[메소드 구현 5-10줄]
        I2[코드 수정/디버깅]
        I3[problem_type:<br/>CODING 포함]
        I4[test_cases 필수]
    end

    subgraph "ADVANCED (고급)"
        A1[클래스 설계 10-30줄]
        A2[복잡한 알고리즘]
        A3[디자인 패턴 적용]
        A4[test_cases 3개 이상]
    end

    style B4 fill:#e1f5ff
    style I3 fill:#fff4e1
    style A3 fill:#ffe5e5
```

### 문제 생성 과정

```mermaid
sequenceDiagram
    participant G as Generator
    participant P as Prompt Builder
    participant L as Solar LLM
    participant J as JSON Parser
    participant M as Problem Model

    G->>P: context + difficulty + count
    P->>L: 프롬프트 전송
    Note over L: 학습 내용 기반<br/>문제 3개 생성
    L-->>J: JSON 응답

    alt JSON 파싱 성공
        J->>M: Problem 모델 변환
    else JSON 파싱 실패
        J->>J: clean_and_parse_json()
        Note over J: 작은따옴표 → 큰따옴표<br/>trailing comma 제거
        J->>M: Problem 모델 변환
    end

    M-->>G: generated_problems
```

---

## 노드 4: validate_problems_node

### 검증 프로세스

```mermaid
flowchart TD
    A[generated_problems] --> B[난이도별<br/>검증 기준 로드]
    B --> C{각 문제 검증}

    C --> D{필수 필드<br/>존재?}
    D -->|No| E[❌ Reject:<br/>필수 필드 누락]
    D -->|Yes| F{질문 길이<br/>충족?}

    F -->|No| G[❌ Reject:<br/>질문 너무 짧음]
    F -->|Yes| H{답변 길이<br/>충족?}

    H -->|No| I[❌ Reject:<br/>답변 너무 짧음]
    H -->|Yes| J{힌트 개수<br/>>=2?}

    J -->|No| K[❌ Reject:<br/>힌트 부족]
    J -->|Yes| L{CODING 타입?}

    L -->|Yes| M{test_cases<br/>있음?}
    M -->|No| N[❌ Reject:<br/>test_cases 필요]
    M -->|Yes| O[✅ Valid]

    L -->|No| O

    O --> P[validated_problems에 추가]
    E --> Q[rejection_reasons에 추가]
    G --> Q
    I --> Q
    K --> Q
    N --> Q

    style O fill:#e5f5e5
    style E fill:#ffe5e5
    style G fill:#ffe5e5
    style I fill:#ffe5e5
    style K fill:#ffe5e5
    style N fill:#ffe5e5
```

### 난이도별 검증 기준

```mermaid
graph TB
    subgraph "검증 기준"
        A[난이도] --> B[질문 최소 길이]
        A --> C[답변 최소 길이]
    end

    subgraph "BEGINNER"
        B1[20자]
        C1[5자]
    end

    subgraph "INTERMEDIATE"
        B2[40자]
        C2[15자]
    end

    subgraph "ADVANCED"
        B3[50자]
        C3[30자]
    end

    B --> B1
    B --> B2
    B --> B3
    C --> C1
    C --> C2
    C --> C3

    style B1 fill:#e1f5ff
    style B2 fill:#fff4e1
    style B3 fill:#ffe5e5
```

### 누적 검증 방식

```mermaid
stateDiagram-v2
    [*] --> Attempt1: 3개 생성
    Attempt1 --> Validated1: 1개 통과

    state Validated1 {
        [*] --> Problem1
    }

    Validated1 --> Attempt2: 재생성 (부족)
    Attempt2 --> Validated2: 1개 통과

    state Validated2 {
        [*] --> Problem1_copy
        Problem1_copy --> Problem2
    }

    Validated2 --> Attempt3: 재생성 (부족)
    Attempt3 --> Validated3: 1개 통과

    state Validated3 {
        [*] --> Problem1_copy2
        Problem1_copy2 --> Problem2_copy
        Problem2_copy --> Problem3
    }

    Validated3 --> [*]: 성공 (3개)

    note right of Validated1
        누적: 1개
    end note

    note right of Validated2
        누적: 2개
    end note

    note right of Validated3
        누적: 3개
    end note
```

---

## 노드 5: should_regenerate (조건부 엣지)

### 재생성 판단 로직

```mermaid
flowchart TD
    A[validated_problems] --> B{validated >= required?}
    B -->|Yes| C[✅ END<br/>성공]
    B -->|No| D{retry_count >= 5?}
    D -->|Yes| E[⚠️ END<br/>최대 재시도]
    D -->|No| F[🔄 REGENERATE<br/>generate 노드로]

    style C fill:#e5f5e5
    style E fill:#fff4e1
    style F fill:#e1f5ff
```

### 재생성 흐름 예시

```mermaid
sequenceDiagram
    participant G as Generate
    participant V as Validate
    participant D as Decision
    participant E as END

    Note over G: 시도 1
    G->>V: 3개 생성
    V->>D: 1개 통과 (누적: 1)
    D->>D: 1 < 3, retry=1 < 5
    D->>G: 재생성

    Note over G: 시도 2
    G->>V: 3개 생성
    V->>D: 1개 통과 (누적: 2)
    D->>D: 2 < 3, retry=2 < 5
    D->>G: 재생성

    Note over G: 시도 3
    G->>V: 3개 생성
    V->>D: 1개 통과 (누적: 3)
    D->>D: 3 >= 3
    D->>E: 성공 종료
```

### 최대 재시도 예시

```mermaid
graph TD
    A[시도 1: 0개 통과] --> B[시도 2: 0개 통과]
    B --> C[시도 3: 1개 통과]
    C --> D[시도 4: 0개 통과]
    D --> E[시도 5: 1개 통과]
    E --> F{retry_count >= 5}
    F -->|Yes| G[⚠️ 종료<br/>누적 2개만 반환]

    style A fill:#ffe5e5
    style B fill:#ffe5e5
    style G fill:#fff4e1
```

---

## 노드 6: refine_context_node (⏱️ 1초) ✨

### 컨텍스트 보강 과정

```mermaid
flowchart TD
    A[rejection_reasons] --> B[거절 사유 분석<br/><i>~0.01초</i>]
    B --> C[사용하지 않은<br/>페이지 추출<br/><i>~0.1초</i>]
    C --> D[새 문서 추가<br/>max_tokens=4000<br/><i>~0.1초</i>]
    D --> E[needed_count 계산<br/><i>~0.01초</i>]
    E --> F[enhanced_context +<br/>needed_count 반환]

    style B fill:#ffe5ff
    style C fill:#e5f5ff
    style D fill:#fff4e1
```

**처리 내용:**
1. **거절 사유 분석**: rejection_reasons 로깅 (처음 3개)
2. **사용하지 않은 페이지 추출**: 기존 context에서 이미 사용한 페이지 제외
3. **컨텍스트 보강**: 새 문서를 추가하여 enhanced_context 생성 (max 4000 토큰)
4. **필요 개수 계산**: `needed_count = problem_count - len(validated_problems)`

**개선 효과:**
- **다양성**: 매번 같은 context 재사용 X → 새 문서로 다양한 문제 생성
- **효율성**: 필요한 개수만 생성 (3개 중 1개 통과 → 2개만 생성)
- **품질**: rejection_reasons 로깅으로 개선 방향 파악

---

## 전체 시스템 아키텍처

```mermaid
graph TB
    subgraph "Problem Generation Pipeline"
        P1[학습 설명/토픽] --> P2[주제 추출<br/>LLM]
        P2 --> P3[ChromaDB<br/>검색]
        P3 --> P4[컨텍스트<br/>구성]
        P4 --> P5[문제 생성<br/>LLM]
        P5 --> P6[검증]
        P6 --> P7{재생성?}
        P7 -->|Yes| P5
        P7 -->|No| P8[완료]
    end

    subgraph "Quality Control Loop"
        P6 -.검증 실패.-> P7
        P7 -.retry < 5.-> P5
    end

    style P2 fill:#ffe5e5
    style P3 fill:#e5f5e5
    style P5 fill:#ffe5e5
    style P6 fill:#fff4e1
    style P7 fill:#ffe5f5
```

---

## 성능 최적화

### 토픽 균등 분배 효과

```mermaid
graph LR
    subgraph "개선 전"
        A1[Context 구성] --> A2[Iterator 7개<br/>Composite 0개]
        A2 --> A3[생성된 문제<br/>Iterator 3개<br/>Composite 0개]
    end

    subgraph "개선 후"
        B1[Context 구성<br/>라운드 로빈] --> B2[Iterator 3개<br/>Composite 3개]
        B2 --> B3[생성된 문제<br/>Iterator 1-2개<br/>Composite 1-2개]
    end

    style A2 fill:#ffe5e5
    style A3 fill:#ffe5e5
    style B2 fill:#e5f5ff
    style B3 fill:#e5f5e5
```

### 검증 기준 차등 효과

```mermaid
graph TB
    subgraph "개선 전 (동일 기준)"
        A1[모든 난이도<br/>질문 50자 이상]
        A1 --> A2[초급 용어 정의<br/>12자]
        A2 --> A3[❌ Reject]
        A3 --> A4[무한 재생성]
    end

    subgraph "개선 후 (차등 기준)"
        B1[BEGINNER: 20자<br/>INTERMEDIATE: 40자<br/>ADVANCED: 50자]
        B1 --> B2[초급 용어 정의<br/>25자]
        B2 --> B3[✅ Valid]
        B3 --> B4[성공 생성]
    end

    style A3 fill:#ffe5e5
    style A4 fill:#ffe5e5
    style B3 fill:#e5f5e5
    style B4 fill:#e5f5e5
```

---

## 데이터 흐름

```mermaid
stateDiagram-v2
    [*] --> Input: learning_description
    Input --> TopicExtract: "iterator패턴 공부"
    TopicExtract --> Search: ["iterator패턴"]
    Search --> Context: documents_by_topic
    Context --> Generate: context (2000자)
    Generate --> Validate: 3 problems

    state Validate {
        [*] --> Check1
        Check1 --> Check2
        Check2 --> [*]
    }

    Validate --> Decision: validated + rejected

    state Decision <<choice>>
    Decision --> Generate: retry < 5 && valid < required
    Decision --> [*]: valid >= required || retry >= 5

    note right of TopicExtract
        LLM 키워드 추출
    end note

    note right of Context
        라운드 로빈 분배
    end note

    note right of Validate
        난이도별 검증
    end note
```

---

## 컴포넌트 다이어그램

```mermaid
graph TB
    subgraph "External Services"
        US[Upstage API<br/>- Solar LLM<br/>- Embedding]
        CH[ChromaDB<br/>Vector Store]
    end

    subgraph "paper_problem Module"
        WF[workflow.py<br/>LangGraph]
        GEN[generators/<br/>beginner.py<br/>intermediate.py<br/>advanced.py]
        UTL[utils/<br/>topic_extractor.py<br/>content_analyzer.py<br/>context_builder.py]
        VAL[validators/<br/>problem_validator.py]
        API[api.py<br/>FastAPI Routes]
    end

    subgraph "shared Module"
        UC[upstage_client.py]
        CC[chroma_client.py]
    end

    API --> WF
    WF --> GEN
    WF --> UTL
    WF --> VAL
    GEN --> UC
    UTL --> UC
    UTL --> CC
    UC --> US
    CC --> CH

    style US fill:#ffe5e5
    style CH fill:#e5f5e5
    style WF fill:#fff4e1
    style GEN fill:#e1f5ff
```

---

## Grading Workflow (새로 추가 ✨)

답변 채점을 위한 LangGraph 워크플로우

```mermaid
graph TD
    Start([START]) --> ValidateInput[validate_input_node<br/>입력 검증<br/><b>⏱️ 0.1초</b>]
    ValidateInput --> Grade[grade_answer_node<br/>채점 실행<br/><b>⏱️ 0.5~2초</b>]
    Grade --> Verify[verify_result_node<br/>결과 검증<br/><b>⏱️ 0.1초</b>]

    Verify --> Decision{신뢰도<br/>충분?}
    Decision -->|Yes| End([END])
    Decision -->|No<br/>retry < 2| Grade

    style ValidateInput fill:#e1f5ff
    style Grade fill:#ffe5e5
    style Verify fill:#e5f5e5
    style Decision fill:#ffe5f5
```

### 성능 지표

| 단계 | 평균 시간 | 주요 작업 |
|------|---------|----------|
| **Validate Input** | 0.1초 | 빈 답변 체크 + 문제 타입 검증 |
| **Grade** | 0.5~2초 | SHORT_ANSWER (LLM) / CODING (실행) |
| **Verify** | 0.1초 | confidence_score 검증 (≥ 0.3) |
| **Total** | **0.5~2.5초** | 초기 채점 + 재채점 시 +0.5초 |

---

### State: GradingState

```mermaid
classDiagram
    class GradingState {
        +Problem problem
        +str user_answer
        +Dict grading_result
        +bool is_verified
        +int retry_count
        +float confidence_score ✨
    }
```

**핵심 필드:**
- `confidence_score`: LLM 채점 신뢰도 (0.0~1.0, similarity_score 기반)
- `is_verified`: 검증 통과 여부 (confidence ≥ 0.3 and 점수 범위 유효)

---

### 노드 1: validate_input_node

```mermaid
flowchart TD
    A[problem + user_answer] --> B{빈 답변?}
    B -->|Yes| C[score=0<br/>is_verified=True]
    B -->|No| D{유효한<br/>problem_type?}
    D -->|No| E[에러 메시지<br/>is_verified=True]
    D -->|Yes| F[검증 통과]

    style C fill:#ffe5e5
    style E fill:#ffe5e5
    style F fill:#e5f5e5
```

**처리 내용:**
- 빈 답변 조기 필터링 (LLM 호출 방지)
- 문제 타입 검증 (SHORT_ANSWER/CODING)
- is_verified=True 설정 시 grade 노드 스킵

---

### 노드 2: grade_answer_node

```mermaid
flowchart TD
    A[problem + user_answer] --> B{problem_type}
    B -->|SHORT_ANSWER| C[ShortAnswerGrader<br/>LLM 의미 유사도]
    B -->|CODING| D[CodingGrader<br/>코드 실행]
    C --> E[grading_result +<br/>confidence_score]
    D --> E

    style C fill:#e1f5ff
    style D fill:#ffe5e5
```

**채점자:**
- **ShortAnswerGrader**: LLM으로 similarity_score 계산
- **CodingGrader**: 실제 코드 실행 + 테스트 케이스 검증

---

### 노드 3: verify_result_node

```mermaid
flowchart TD
    A[grading_result] --> B{confidence<br/>< 0.3?}
    B -->|Yes| C[is_verified=False<br/>재채점 필요]
    B -->|No| D{점수 범위<br/>0~100?}
    D -->|No| E[is_verified=False]
    D -->|Yes| F[is_verified=True]

    style C fill:#ffe5e5
    style E fill:#ffe5e5
    style F fill:#e5f5e5
```

**검증 항목:**
1. confidence_score ≥ 0.3
2. 0 ≤ score ≤ 100
3. 필수 필드 존재

---

### 조건부 분기

```python
def should_retry(state: GradingState) -> str:
    if state["is_verified"]:
        return "end"

    if state["retry_count"] >= 2:
        return "end"  # 최대 재시도

    return "retry"  # 재채점
```

**재채점 조건:**
- 신뢰도 낮음 (< 0.3)
- 점수 범위 오류
- 최대 2회까지 재시도

