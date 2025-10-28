# team1_qa/workflow.py
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict
from shared.chroma_client import chroma_client
from shared.upstage_client import upstage_client
from team1_qa.parsers.pdf_parser import pdf_parser
from langchain.schema import HumanMessage
import logging
import time

logger = logging.getLogger(__name__)


# 업로드 State
class UploadState(TypedDict):
    material_id: int
    file_path: str
    file_type: str
    parsed_blocks: List[Dict]
    status: str


# QA State
class QAState(TypedDict):
    question: str
    material_id: int
    retrieved_docs: List[Dict]
    answer: str
    sources: List[Dict]


# ============ 업로드 워크플로우 ============
async def parse_document_node(state: UploadState) -> dict:
    """문서 파싱"""
    file_path = state["file_path"]
    parsed_blocks = await pdf_parser.parse(file_path)
    return {"parsed_blocks": parsed_blocks}


async def embed_and_store_node(state: UploadState) -> dict:
    """임베딩 및 ChromaDB 저장"""
    material_id = state["material_id"]
    parsed_blocks = state["parsed_blocks"]

    texts = [block["content"] for block in parsed_blocks]
    embeddings = await upstage_client.embed_documents(texts)

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
        embeddings=embeddings,
    )

    return {"status": "completed"}


def create_upload_workflow():
    graph = StateGraph(UploadState)
    graph.add_node("parse", parse_document_node)
    graph.add_node("embed_store", embed_and_store_node)
    graph.add_edge(START, "parse")
    graph.add_edge("parse", "embed_store")
    graph.add_edge("embed_store", END)
    return graph.compile()


# ============ QA 워크플로우 ============
async def retrieve_node(state: QAState) -> dict:
    """ChromaDB에서 문서 검색 (0.2-0.3초 목표)"""
    start_time = time.time()

    question = state["question"]
    material_id = state["material_id"]

    # 질문 임베딩
    query_embedding = await upstage_client.embed_query(question)

    # ChromaDB 검색
    results = chroma_client.search(
        collection_name="learning_materials",
        query_embeddings=[query_embedding],
        n_results=3,
        filter_dict={"material_id": material_id},
    )

    retrieved_docs = []
    for i in range(len(results["documents"][0])):
        retrieved_docs.append(
            {
                "content": results["documents"][0][i],
                "page": results["metadatas"][0][i]["page"],
                "distance": results["distances"][0][i],
            }
        )

    elapsed = time.time() - start_time
    logger.info(f"⚡ Retrieve time: {elapsed:.3f}s")

    return {"retrieved_docs": retrieved_docs}


async def generate_answer_node(state: QAState) -> dict:
    """답변 생성 (0.8-1.0초 목표)"""
    start_time = time.time()

    question = state["question"]
    retrieved_docs = state["retrieved_docs"]

    context = "\n\n---\n\n".join(
        [f"[페이지 {doc['page']}]\n{doc['content']}" for doc in retrieved_docs]
    )

    llm = upstage_client.get_chat_model(model="solar-1-mini-chat", temperature=0.3)

    prompt = f"""당신은 학습자료 기반 QA 봇입니다.

**학습자료 내용**:
{context}

**학생 질문**: {question}

**답변 규칙**:
1. 학습자료에 있는 내용만 사용하세요
2. 명확하고 간결하게 답변하세요 (3-5문장)
3. 관련 페이지 번호를 명시하세요

답변:"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    answer = response.content

    sources = [
        {"page": doc["page"], "excerpt": doc["content"][:100] + "..."}
        for doc in retrieved_docs
    ]

    elapsed = time.time() - start_time
    logger.info(f"⚡ Generate time: {elapsed:.3f}s")

    return {"answer": answer, "sources": sources}


def create_qa_workflow():
    graph = StateGraph(QAState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_answer_node)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


# 워크플로우 인스턴스
upload_workflow = create_upload_workflow()
qa_workflow = create_qa_workflow()
