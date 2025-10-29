# paper_qa/api.py (Part 1: Upload)
from fastapi import APIRouter, HTTPException
from pathlib import Path
import logging
import time
from paper_qa.models import QARequest, QAResponse
import time
from paper_qa.models import MaterialUploadRequest, MaterialUploadResponse
from paper_qa.workflow import upload_workflow
from shared.chroma_client import chroma_client
from shared.upstage_client import upstage_client
from config import settings

router = APIRouter(prefix="/qa", tags=["QA"])
logger = logging.getLogger(__name__)

@router.post("/upload", response_model=MaterialUploadResponse)
async def upload_material(request: MaterialUploadRequest):
    """
    ✨ 학습 자료 업로드 및 파싱 (최적화 버전)

    - Spring Boot가 파일을 공유 볼륨에 저장
    - 이 API는 파일 경로를 받아 직접 읽어서 처리
    - 파일을 다시 전송받지 않음 (네트워크 최적화)
    """
    logger.info(f"📁 Received upload request: material_id={request.material_id}, path={request.file_path}")

    try:
        # 1. 파일 존재 확인
        file_path = Path(request.file_path)
        if not file_path.exists():
            logger.error(f"❌ File not found: {file_path}")
            raise HTTPException(
                status_code=404,
                detail=f"File not found at path: {request.file_path}"
            )

        logger.info(f"✅ File found: {file_path} ({file_path.stat().st_size} bytes)")

        # 2. 워크플로우 실행 (파일 경로 전달)
        result = await upload_workflow.ainvoke({
            "material_id": request.material_id,
            "file_path": str(file_path),
            "file_type": "pdf"
        })

        return MaterialUploadResponse(
            material_id=request.material_id,
            status="completed",
            page_count=len(result.get("parsed_blocks", [])),
            chunk_count=len(result.get("parsed_blocks", [])),
            message=f"Successfully processed {len(result.get('parsed_blocks', []))} blocks"
        )

    except Exception as e:
        logger.error(f"❌ Upload failed: {str(e)}", exc_info=True)
        return MaterialUploadResponse(
            material_id=request.material_id,
            status="failed",
            page_count=0,
            chunk_count=0,
            message=f"Processing failed: {str(e)}"
        )
        # paper_qa/api.py (Part 2: QA)


@router.post("/ask", response_model=QAResponse)
async def ask_question(request: QARequest):
    """학습자료 기반 질의응답"""
    start_time = time.time()

    # LangGraph 워크플로우 실행
    result = await qa_workflow.ainvoke({
        "question": request.question,
        "material_id": request.material_id
    })

    response_time = int((time.time() - start_time) * 1000)

    # 2초 초과 시 경고
    if response_time > 2000:
        logger.warning(f"⚠️ Slow response: {response_time}ms")
    else:
        logger.info(f"✅ Response time: {response_time}ms")

    return QAResponse(
        answer=result["answer"],
        sources=result["sources"],
        response_time_ms=response_time
    )