# paper_qa/api.py (Part 1: Upload)
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pathlib import Path
import logging
import time
import shutil
from paper_qa.models import MaterialUploadRequest, MaterialUploadResponse, QARequest, QAResponse
from paper_qa.workflow import upload_workflow, qa_workflow
from shared.chroma_client import chroma_client
from shared.upstage_client import upstage_client
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=MaterialUploadResponse)
async def upload_material(request: MaterialUploadRequest):
    """
    ✨ 학습 자료 업로드 및 파싱 (최적화 버전)

    - Spring Boot가 파일을 공유 볼륨에 저장
    - 이 API는 파일 경로를 받아 직접 읽어서 처리
    - 파일을 다시 전송받지 않음 (네트워크 최적화)
    """
    logger.info(
        f"📁 Received upload request: material_id={request.material_id}, path={request.file_path}"
    )

    try:
        # 1. 파일 존재 확인
        file_path = Path(request.file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise HTTPException(
                status_code=404, detail=f"File not found at path: {request.file_path}"
            )

        logger.info(f"✅ File found: {file_path} ({file_path.stat().st_size} bytes)")

        # 2. 워크플로우 실행 (파일 경로 전달)
        result = await upload_workflow.ainvoke(
            {
                "material_id": request.material_id,
                "file_path": str(file_path),
                #"file_type": "pdf",
                "file_type": request.file_type,
            }
        )

        return MaterialUploadResponse(
            material_id=request.material_id,
            status="completed",
            page_count=len(result.get("parsed_blocks", [])),
            chunk_count=len(result.get("parsed_blocks", [])),
            message=f"Successfully processed {len(result.get('parsed_blocks', []))} blocks",
        )

    except Exception as e:
        logger.error(f"❌ Upload failed: {str(e)}", exc_info=True)
        return MaterialUploadResponse(
            material_id=request.material_id,
            status="failed",
            page_count=0,
            chunk_count=0,
            message=f"Processing failed: {str(e)}",
        )


@router.post("/upload-file", response_model=MaterialUploadResponse)
async def upload_material_file(
    file: UploadFile = File(...),
    material_id: int = Form(...)
):
    """
    📤 파일 직접 업로드 API

    - 클라이언트가 파일을 직접 전송
    - 서버가 파일을 UPLOAD_DIR에 저장 후 처리
    - multipart/form-data 형식
    """
    logger.info(
        f"📤 Received file upload: material_id={material_id}, filename={file.filename}"
    )

    try:
        # 1. 업로드 디렉토리 생성
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 2. 파일 저장 (material_id를 파일명에 포함)
        file_extension = Path(file.filename).suffix
        saved_filename = f"material_{material_id}{file_extension}"
        file_path = upload_dir / saved_filename

        logger.info(f"💾 Saving file to: {file_path}")

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"✅ File saved: {file_path} ({file_path.stat().st_size} bytes)")

        # 3. 워크플로우 실행
        result = await upload_workflow.ainvoke(
            {
                "material_id": material_id,
                "file_path": str(file_path),
                "file_type": "pdf",
            }
        )

        return MaterialUploadResponse(
            material_id=material_id,
            status="completed",
            page_count=len(result.get("parsed_blocks", [])),
            chunk_count=len(result.get("parsed_blocks", [])),
            message=f"Successfully processed {len(result.get('parsed_blocks', []))} blocks from {file.filename}",
        )

    except Exception as e:
        logger.error(f"❌ File upload failed: {str(e)}", exc_info=True)
        return MaterialUploadResponse(
            material_id=material_id,
            status="failed",
            page_count=0,
            chunk_count=0,
            message=f"Processing failed: {str(e)}",
        )

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


@router.get("/data/{material_id}")
async def get_stored_data(material_id: int, limit: int = 10):
    """
    🔍 ChromaDB에 저장된 데이터 확인

    - material_id별로 저장된 문서 조회
    - limit: 반환할 최대 문서 수
    """
    logger.info(f"🔍 Querying stored data for material_id={material_id}, limit={limit}")

    try:
        collection = chroma_client.get_or_create_collection("learning_materials")

        # material_id로 필터링하여 데이터 가져오기
        results = collection.get(
            where={"material_id": material_id},
            limit=limit
        )

        return {
            "material_id": material_id,
            "total_count": len(results["ids"]),
            "limit": limit,
            "documents": [
                {
                    "id": results["ids"][i],
                    "content": results["documents"][i][:200] + "..." if len(results["documents"][i]) > 200 else results["documents"][i],
                    "metadata": results["metadatas"][i]
                }
                for i in range(len(results["ids"]))
            ]
        }

    except Exception as e:
        logger.error(f"❌ Failed to get stored data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve data: {str(e)}")


@router.get("/data")
async def get_all_stored_data(limit: int = 20):
    """
    🔍 ChromaDB에 저장된 모든 데이터 확인

    - 모든 material_id의 데이터 조회
    - limit: 반환할 최대 문서 수
    """
    logger.info(f"🔍 Querying all stored data, limit={limit}")

    try:
        collection = chroma_client.get_or_create_collection("learning_materials")

        # 모든 데이터 가져오기
        results = collection.get(
            limit=limit
        )

        # material_id별로 그룹화
        materials = {}
        for i in range(len(results["ids"])):
            mat_id = results["metadatas"][i].get("material_id", "unknown")
            if mat_id not in materials:
                materials[mat_id] = []
            materials[mat_id].append({
                "id": results["ids"][i],
                "content": results["documents"][i][:200] + "..." if len(results["documents"][i]) > 200 else results["documents"][i],
                "metadata": results["metadatas"][i]
            })

        return {
            "total_count": len(results["ids"]),
            "limit": limit,
            "materials": materials,
            "material_ids": list(materials.keys())
        }

    except Exception as e:
        logger.error(f"❌ Failed to get all stored data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve data: {str(e)}")
