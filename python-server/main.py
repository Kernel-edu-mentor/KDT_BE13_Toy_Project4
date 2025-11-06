import sys
import os
from pathlib import Path
# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from config import settings

# LangSmith 환경 변수 설정
os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT

from fastapi import FastAPI
from paper_qa.api import router as qa_router
from paper_problem.api import router as problem_router
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="EduMentor AI Engine",
    description="QA 시스템 + 문제 생성 통합 API",
    version="1.0.0"
)

# 라우터 등록
app.include_router(qa_router, prefix="/qa", tags=["QA"])
app.include_router(problem_router, prefix="/problems", tags=["Problems"])

@app.get("/")
async def root():
    return {
        "service": "EduMentor AI Engine",
        "version": "1.0.0",
        "endpoints": {
            "qa": "/qa",
            "problems": "/problems",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": ["qa", "problems"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
