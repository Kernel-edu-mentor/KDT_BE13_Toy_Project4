from fastapi import APIRouter, HTTPException
from pathlib import Path
import logging
from typing import Any

from paper_qa.models import MaterialUploadRequest, MaterialUploadResponse
from paper_qa.workflow import upload_workflow

router = APIRouter(prefix="/qa", tags=["QA"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=MaterialUploadResponse)
async def upload_material(request: MaterialUploadRequest):
    """
    ✨ 학습자료 업로드 및 파싱

    - Spring Boot가 파일을 공유 볼륨에 저장
    - 이 API는 파일 경로를 받아 직접 읽어서 처리
    - 파일을 다시 전송밪지 않음 (네트워크 최적화)
    """

    logger.info(
        f"Received upload request: material_id={request.material_id}, path={request.file_path}"
    )

    try:
        # 1. 파일 존재 확인
        file_path = Path(request.file_path)
        if not file_path.exists():
            logger.info(f"File not found: {file_path}")
            raise HTTPException(
                status_code=404, detail=f"File not found at path: {request.file_path}"
            )

        logger.info(f"File found: {file_path} ({file_path.stat().st_size} bytes)")

        # 2. 워크플로우 실행 (파일 경로 전달)
        result: Any = await upload_workflow.ainvoke(
            {
                "material_id": request.material_id,
                "file_path": str(file_path),
                "file_type": request.file_type,
            }
        )

        parsed_blocks = result.get("parsed_blocks", [])

        return MaterialUploadResponse(
            material_id=request.material_id,
            status="completed",
            page_count=len({block.get("page") for block in parsed_blocks if block}),
            chunk_count=len(parsed_blocks),
            message=f"Processing completed: {len(parsed_blocks)} blocks stored.",
        )

    except Exception as e:
        logger.error("Upload failed: %s", str(e), exc_info=True)
        return MaterialUploadResponse(
            material_id=request.material_id,
            status="failed",
            page_count=0,
            chunk_count=0,
            message=f"Processing failed: {str(e)}",
        )
