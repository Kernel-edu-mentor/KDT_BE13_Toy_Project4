### 📄 [프로젝트 설명서 다운로드 (PDF)](https://github.com/Kernel-edu-mentor/KDT_BE13_Toy_Project4/raw/dev/project-doc.pdf)

---

# EduMentor AI - 학습 자료 기반 AI 문제 생성 및 Q&A 시스템

학습 자료(PDF)를 업로드하면 AI가 자동으로 문제를 생성하고, RAG 기반 Q&A 기능을 제공하는 풀스택 교육 플랫폼입니다.

## 주요 기능

- **자료 업로드**: PDF 학습 자료 파싱 및 벡터 DB 저장
- **AI 문제 생성**: 난이도별(초급/중급/고급) 자동 문제 생성
- **RAG Q&A**: 업로드된 자료 기반 질의응답
- **OAuth 인증**: Kakao OAuth2 로그인 지원
- **자동 채점**: AI 기반 답안 평가 및 피드백

## 기술 스택

### Backend - Spring Boot
- Java 21, Spring Boot 3.5.7
- Spring Security + OAuth2 Client
- Spring Data JPA + PostgreSQL
- WebFlux (Python 서버 통신)

### AI Engine - Python FastAPI
- FastAPI + LangChain + LangGraph
- ChromaDB (벡터 DB)
- Upstage API (LLM + Embeddings + Document Parse)

### Frontend - React
- React 18 + TypeScript + Vite
- TailwindCSS + Radix UI + shadcn/ui
- TanStack Query (상태 관리)

## 프로젝트 구조

```
├── spring-server/          # Spring Boot 백엔드
│   └── paper/
│       ├── controller/     # REST API 엔드포인트
│       ├── service/        # 비즈니스 로직
│       ├── domain/         # JPA 엔티티
│       └── security/       # OAuth2 + Security 설정
├── python-server/          # Python AI 엔진
│   ├── paper_qa/          # RAG Q&A 모듈
│   ├── paper_problem/     # 문제 생성 모듈
│   └── shared/            # ChromaDB/Upstage 클라이언트
└── 404-NOT-FOUND-Frontend/ # React 프론트엔드
```

## 설치 및 실행

### 사전 요구사항
- Java 21
- Python 3.13
- Node.js 18+
- PostgreSQL
- ChromaDB (Docker)

### Python AI 서버
```bash
cd python-server
conda create -n edumentor python=3.13 -y
conda activate edumentor
pip install -r requirements.txt
python main.py
```

### Spring Boot 서버
```bash
cd spring-server/paper
./gradlew bootRun
```

### Frontend
```bash
cd 404-NOT-FOUND-Frontend
npm install
npm run dev
```

## API 엔드포인트

### 학습 자료
- `POST /api/materials/upload` - PDF 업로드
- `GET /api/materials/{id}` - 자료 조회

### 문제 생성
- `POST /api/problems/generate` - 난이도별 문제 생성
- `POST /api/problems/answer` - 답안 제출 및 채점

### Q&A
- `POST /api/qa/sessions` - Q&A 세션 생성
- `POST /api/qa/chat` - 질문 전송

### 인증
- `POST /api/auth/register` - 회원가입
- `POST /api/auth/login` - 로그인
- `GET /oauth2/authorization/kakao` - Kakao OAuth

## 환경 변수

### Python Server (.env)
```
UPSTAGE_API_KEY=<API_KEY>
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

### Spring Boot (application.yml)
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/edumentor
  security:
    oauth2:
      client:
        registration:
          kakao:
            client-id: <CLIENT_ID>
            client-secret: <CLIENT_SECRET>
```

## 팀 구성

- **Backend Team**: Spring Boot API, OAuth2, JPA
- **AI Team 1**: RAG Q&A 파이프라인
- **AI Team 2**: 문제 생성 파이프라인
- **Frontend Team**: React UI/UX

