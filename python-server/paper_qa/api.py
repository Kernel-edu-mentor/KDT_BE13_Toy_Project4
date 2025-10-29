from fastapi import APIRouter, UploadFile, HTTPException
from paper_qa.models import UploadResponse, QARequest, QAResponse
from paper_qa.workflow import upload_workflow, qa_workflow
from config import settings
import shutil
import os
import time

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_material(file: UploadFile, material_id: int):
    """학습자료 업로드 및 파싱"""

    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ['pdf']:
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = await upload_workflow.ainvoke({
        "material_id": material_id,
        "file_path": file_path,
        "file_type": "pdf"
    })

    return UploadResponse(
        material_id=material_id,
        status=result["status"],
        blocks_count=len(result["parsed_blocks"])
    )

@router.post("/ask", response_model=QAResponse)
async def ask_question(request: QARequest):
    """질의응답 (1-2초 목표)"""
    start_time = time.time()

    result = await qa_workflow.ainvoke({
        "question": request.question,
        "material_id": request.material_id
    })

    response_time = int((time.time() - start_time) * 1000)

    if response_time > 2000:
        print(f"⚠️ Slow response: {response_time}ms")
    else:
        print(f"✅ Response time: {response_time}ms")

    return QAResponse(
        answer=result["answer"],
        sources=result["sources"],
        response_time_ms=response_time
    )
