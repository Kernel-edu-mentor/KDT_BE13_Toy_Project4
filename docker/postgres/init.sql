-- 사용자 테이블
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'STUDENT',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 학습자료 테이블
CREATE TABLE learning_materials (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    page_count INTEGER,
    uploaded_by BIGINT REFERENCES users(id),
    parse_status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT NOW()
);

-- QA 세션 테이블
CREATE TABLE qa_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    material_id BIGINT REFERENCES learning_materials(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources JSONB,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 실습 문제 테이블
CREATE TABLE practice_problems (
    id BIGSERIAL PRIMARY KEY,
    material_id BIGINT REFERENCES learning_materials(id),
    difficulty VARCHAR(20) NOT NULL,
    problem_type VARCHAR(50),
    question TEXT NOT NULL,
    answer TEXT,
    hints JSONB,
    test_cases JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);