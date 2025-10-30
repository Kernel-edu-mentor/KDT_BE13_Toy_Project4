# paper_qa/workflow.py (Part 1: Upload)
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict
from paper_qa.parsers.pdf_parser import pdf_parser
from paper_qa.parsers.ppt_parser import ppt_parser
from shared.upstage_client import upstage_client
from shared.chroma_client import chroma_client
import logging
from langchain_upstage import ChatUpstage
from config import settings
from langchain_upstage import ChatUpstage
from langchain.schema import HumanMessage
from config import settings
from paper_qa.utils.cache import query_cache
import time

logger = logging.getLogger(__name__)

class UploadState(TypedDict):
    material_id: int
    file_path: str
    file_type: str  # "pdf" or "ppt"
    parsed_blocks: List[Dict]
    embeddings: List[List[float]]
    status: str

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
        raise ValueError(f"Unsupported file type: {file_type}")

    return {"parsed_blocks": parsed_blocks}

async def embed_and_store_node(state: UploadState) -> dict:
    """2단계: 임베딩 및 ChromaDB 저장"""
    material_id = state["material_id"]
    parsed_blocks = state["parsed_blocks"]

    logger.info(f"Embedding {len(parsed_blocks)} blocks")

    # 배치 임베딩 (효율성)
    texts = [block['content'] for block in parsed_blocks]
    embeddings = await upstage_client.embed_documents(texts)

    logger.info("Storing in ChromaDB")

    # ChromaDB에 저장
    documents = []
    metadatas = []
    ids = []

    for idx, block in enumerate(parsed_blocks):
        documents.append(block['content'])
        metadatas.append({
            'material_id': material_id,
            'page': block['page'],
            'type': block['type']
        })
        ids.append(f"material_{material_id}_block_{idx}")

    chroma_client.add_documents(
        collection_name="learning_materials",
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    return {
        "embeddings": embeddings,
        "status": "completed"
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
# paper_qa/workflow.py (Part 2: QA)
class QAState(TypedDict):
    question: str
    material_id: int
    retrieved_docs: List[Dict]
    answer: str
    sources: List[Dict]
    response_time: float
    
    # paper_qa/workflow.py (Part 2: QA - Retrieve)


async def retrieve_node(state: QAState) -> dict:
    """ChromaDB에서 관련 문서 검색"""
    start_time = time.time()

    question = state["question"]
    material_id = state["material_id"]

    logger.info(f"Retrieving docs for: {question}")

    # 검색 (k=3으로 제한 - 속도 최적화)
    results = chroma_client.search(
        collection_name="learning_materials",
        query_texts=[question],
        n_results=3,
        filter_dict={"material_id": material_id}
    )

    # 결과 구성
    retrieved_docs = []
    for i in range(len(results['documents'][0])):
        retrieved_docs.append({
            'content': results['documents'][0][i],
            'page': results['metadatas'][0][i]['page'],
            'type': results['metadatas'][0][i]['type'],
            'distance': results['distances'][0][i]
        })

    retrieve_time = time.time() - start_time
    logger.info(f"⚡ Retrieve time: {retrieve_time:.3f}s")

    return {"retrieved_docs": retrieved_docs}

# paper_qa/workflow.py (Part 2: QA - Generate)


async def generate_answer_node(state: QAState) -> dict:
    """Upstage Solar로 답변 생성"""
    start_time = time.time()

    question = state["question"]
    retrieved_docs = state["retrieved_docs"]

    # 컨텍스트 구성
    context_parts = []
    for doc in retrieved_docs:
        context_parts.append(
            f"[페이지 {doc['page']}]\n{doc['content']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # Upstage Solar Mini (빠른 응답)
    llm = ChatUpstage(
        api_key=settings.UPSTAGE_API_KEY,
        model="solar-1-mini-chat",
        temperature=0.3
    )

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

    # 출처 정보
    sources = [
        {
            "page": doc["page"],
            "excerpt": doc["content"][:100] + "..."
        }
        for doc in retrieved_docs
    ]

    generate_time = time.time() - start_time
    logger.info(f"⚡ Generate time: {generate_time:.3f}s")

    return {
        "answer": answer,
        "sources": sources
    }
    
    # paper_qa/workflow.py (Part 2: QA - Complete)
def create_qa_workflow():
    """QA LangGraph 워크플로우"""
    graph = StateGraph(QAState)

    # 노드 추가
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_answer_node)

    # 엣지 (순차 실행)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph.compile()

qa_workflow = create_qa_workflow()

# paper_qa/workflow.py (캐싱 추가)

async def retrieve_node(state: QAState) -> dict:
    question = state["question"]
    material_id = state["material_id"]

    # 캐시 키 생성
    cache_key = f"{material_id}:{question}"

    # 캐시 확인
    cached = query_cache.get(cache_key)
    if cached:
        logger.info("✅ Cache hit!")
        return {"retrieved_docs": cached}

    # 캐시 미스 - 검색 수행
    results = chroma_client.search(...)

    retrieved_docs = [...]

    # 캐시 저장
    query_cache.set(cache_key, retrieved_docs)

    return {"retrieved_docs": retrieved_docs}
# paper_qa/workflow.py (멀티 쿼리)

async def generate_multi_queries(question: str) -> List[str]:
    """질문을 다양한 형태로 변환"""
    llm = ChatUpstage(
        api_key=settings.UPSTAGE_API_KEY,
        model="solar-1-mini-chat"
    )

    prompt = f"""다음 질문을 3가지 다른 형태로 변환하세요:

질문: {question}

변환된 질문들 (줄바꿈으로 구분):"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    queries = response.content.strip().split('\n')

    return [question] + queries[:2]  # 원본 + 2개 변환

async def retrieve_node(state: QAState) -> dict:
    question = state["question"]
    material_id = state["material_id"]

    # 멀티 쿼리 생성
    queries = await generate_multi_queries(question)

    all_docs = []
    seen_ids = set()

    # 각 쿼리로 검색
    for query in queries:
        results = chroma_client.search(
            collection_name="learning_materials",
            query_texts=[query],
            n_results=2,
            filter_dict={"material_id": material_id}
        )

        # 중복 제거
        for i, doc_id in enumerate(results['ids'][0]):
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                all_docs.append({
                    'content': results['documents'][0][i],
                    'page': results['metadatas'][0][i]['page'],
                    'distance': results['distances'][0][i]
                })

    # 거리 기준 정렬 (가장 관련성 높은 3개)
    all_docs.sort(key=lambda x: x['distance'])
    retrieved_docs = all_docs[:3]

    return {"retrieved_docs": retrieved_docs}