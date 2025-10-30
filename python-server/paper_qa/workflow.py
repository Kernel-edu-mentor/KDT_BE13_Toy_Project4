from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict
from shared.chroma_client import chroma_client
from shared.upstage_client import upstage_client
from paper_qa.parsers.pdf_parser import pdf_parser
from paper_qa.parsers.ppt_parser import ppt_parser
import logging

logger = logging.getLogger(__name__)


# 업로드 State
class UploadState(TypedDict):
    material_id: int
    file_path: str
    file_type: str
    parsed_blocks: List[Dict]
    embeddings: List[List[float]]
    status: str


# ============ 업로드 워크플로우 ============
async def parse_document_node(state: UploadState) -> dict:
    """1단계: 문서 파싱"""
    file_path = state["file_path"]
    file_type = state["file_type"]

    logger.info(f"Parsing {file_type}: {file_path}")

    if file_type == "pdf":
        parsed_blocks = await pdf_parser.parse(file_path)
    elif file_type == "ppt":
        parsed_blocks = ppt_parser.parse(file_path)
    else:
        raise ValueError(f"Unsupported file_type: {file_type}")

    return {"parsed_blocks": parsed_blocks}


async def embed_and_store_node(state: UploadState) -> dict:
    """2단계: 임베딩 및 ChromaDB 저장"""
    material_id = state["material_id"]
    parsed_blocks = state["parsed_blocks"]

    logger.info(f"Embedding {len(parsed_blocks)} blocks")

    # 배치 임베딩 (효율성)
    texts = [block["content"] for block in parsed_blocks]
    embeddings = await upstage_client.embed_documents(texts)

    # ChromaDB에 저장
    logger.info("Storing in ChromaDB")
    documents = []
    metadatas = []
    ids = []

    for idx, block in enumerate(parsed_blocks):
        documents.append(block["content"])
        metadatas.append(
            {"material_id": material_id, "page": block["page"], "type": block["type"]}
        )
        ids.append(f"material_{material_id}_block_{idx}")

    chroma_client.add_documents(
        collection_name="learning_materials",
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings,  # embeddings을 직접 계산했으니 명시적으로 직접 전달
    )

    logger.info(f"Stored {len(documents)} blocks in ChromaDB")

    return {
        "embeddings": embeddings,
        "parsed_blocks": parsed_blocks,
        "status": "completed",
    }


# 업로드 워크플로우 생성
def create_upload_workflow():
    graph = StateGraph(UploadState)

    graph.add_node("parse", parse_document_node)
    graph.add_node("embed_store", embed_and_store_node)

    graph.add_edge(START, "parse")
    graph.add_edge("parse", "embed_store")
    graph.add_edge("embed_store", END)

    return graph.compile()


upload_workflow = create_upload_workflow()
