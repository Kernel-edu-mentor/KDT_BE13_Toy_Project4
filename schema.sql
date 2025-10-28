-- 사용자 테이블
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 논문 메타데이터 테이블
CREATE TABLE papers (
    id BIGSERIAL PRIMARY KEY,
    paper_id VARCHAR(100) UNIQUE NOT NULL,  -- arxiv:2301.12345 or upload_1234567890
    title TEXT NOT NULL,
    authors TEXT[] NOT NULL,
    abstract TEXT,
    year INTEGER,
    citation_count INTEGER DEFAULT 0,
    pdf_url TEXT,  -- arXiv/외부 논문 원본 URL
    local_path VARCHAR(500),  -- Python 서버 로컬 저장 경로 (data/papers/paper_id.pdf)
    uploaded_by BIGINT REFERENCES users(id),
    source VARCHAR(50) DEFAULT 'uploaded',  -- uploaded | arxiv | semantic_scholar
    created_at TIMESTAMP DEFAULT NOW()
);

-- QA 이력 테이블
CREATE TABLE qa_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources JSONB,  -- [{"paper_id": "...", "page": 3, "score": 0.95}]
    confidence FLOAT,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 논문 작성 프로젝트 테이블
CREATE TABLE writing_projects (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    title VARCHAR(500) NOT NULL,
    research_topic TEXT NOT NULL,
    keywords TEXT[],
    abstract TEXT,
    full_content TEXT,  -- Markdown/LaTeX
    status VARCHAR(50) DEFAULT 'draft',  -- draft, reviewing, completed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_papers_paper_id ON papers(paper_id);
CREATE INDEX idx_qa_history_user_id ON qa_history(user_id);
CREATE INDEX idx_qa_history_created_at ON qa_history(created_at DESC);
CREATE INDEX idx_writing_projects_user_id ON writing_projects(user_id);