from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict
from shared.chroma_client import chroma_client
from shared.upstage_client import upstage_client
from paper_qa.parsers.pdf_parser import pdf_parser
from langchain_upstage import ChatUpstage
from langchain.schema import HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import settings
import logging, time

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
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    return {"parsed_blocks": parsed_blocks}


async def embed_and_store_node(state: UploadState) -> dict:
    """2단계: 임베딩 및 ChromaDB 저장 (청크 기반)"""
    material_id = state["material_id"]
    parsed_blocks = state["parsed_blocks"]

    logger.info(f"Chunking {len(parsed_blocks)} blocks")

    # RecursiveCharacterTextSplitter 초기화
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,        # 1-2 단락 크기
        chunk_overlap=50,      # 문맥 유지 (10%)
        separators=["\n\n", "\n", ". ", " ", ""],  # 문단 → 문장 → 단어 순 분할
        length_function=len,
    )

    # 청킹 처리
    all_chunks = []
    for block in parsed_blocks:
        content = block["content"]
        page = block["page"]
        block_type = block["type"]

        # 텍스트를 청크로 분할
        chunks = text_splitter.split_text(content)

        for chunk in chunks:
            all_chunks.append({
                "content": chunk,
                "page": page,
                "type": block_type,
            })

    logger.info(f"Created {len(all_chunks)} chunks from {len(parsed_blocks)} blocks")

    # 배치 임베딩 (효율성)
    texts = [chunk["content"] for chunk in all_chunks]
    embeddings = await upstage_client.embed_documents(texts)

    # ChromaDB에 배치로 저장 (Payload Too Large 방지)
    logger.info(f"Storing {len(all_chunks)} chunks in ChromaDB (batch mode)")

    BATCH_SIZE = 100  # 한 번에 100개씩 저장
    total_stored = 0

    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch_chunks = all_chunks[i:i + BATCH_SIZE]
        batch_embeddings = embeddings[i:i + BATCH_SIZE]

        documents = []
        metadatas = []
        ids = []

        for idx, chunk in enumerate(batch_chunks):
            global_idx = i + idx
            documents.append(chunk["content"])
            metadatas.append(
                {"material_id": material_id, "page": chunk["page"], "type": chunk["type"]}
            )
            ids.append(f"material_{material_id}_chunk_{global_idx}")

        chroma_client.add_documents(
            collection_name="learning_materials",
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=batch_embeddings,
        )

        total_stored += len(documents)
        logger.info(f"Stored batch {i // BATCH_SIZE + 1}: {total_stored}/{len(all_chunks)} chunks")

    logger.info(f"✅ Successfully stored all {total_stored} chunks in ChromaDB")

    return {
        "embeddings": embeddings,
        "parsed_blocks": all_chunks,
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

class QAState(TypedDict):
    question: str
    material_id: int
    retrieved_docs: List[Dict]
    answer: str
    sources: List[Dict]
    response_time: float
    has_relevant_docs: bool  # 관련 문서 존재 여부
    answer_quality: str  # "good", "needs_review", "fallback"


async def retrieve_node(state: QAState) -> dict:
    """ChromaDB에서 관련 문서 검색"""
    start_time = time.time()

    question = state["question"]
    material_id = state["material_id"]

    logger.info(f"Retrieving docs for: {question}")

    # 1. 질문 임베딩
    query_embedding = (await upstage_client.embed_documents([question]))[0]

    # 검색 (k=5로 증가 - 더 많은 후보 확보)
    results = chroma_client.search(
        collection_name="learning_materials",
        query_embeddings=[query_embedding],
        n_results=5,
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

    # 검색 결과 품질 평가
    has_relevant_docs = len(retrieved_docs) > 0 and retrieved_docs[0]['distance'] < 0.5

    retrieve_time = time.time() - start_time
    logger.info(f"⚡ Retrieve time: {retrieve_time:.3f}s, found {len(retrieved_docs)} docs")

    if not has_relevant_docs:
        logger.warning(f"⚠️ No relevant documents found (best distance: {retrieved_docs[0]['distance'] if retrieved_docs else 'N/A'})")

    return {
        "retrieved_docs": retrieved_docs,
        "has_relevant_docs": has_relevant_docs
    }

async def fallback_response_node(state: QAState) -> dict:
    """관련 문서가 없을 때 대체 응답"""
    question = state["question"]

    logger.info("Generating fallback response (no relevant docs)")

    answer = f"죄송합니다. 업로드하신 학습자료에서 '{question}'에 대한 관련 내용을 찾을 수 없습니다.\n\n다른 질문을 해주시거나, 질문을 더 구체적으로 작성해주시면 도움이 될 것 같습니다."

    return {
        "answer": answer,
        "sources": [],
        "answer_quality": "fallback"
    }

async def generate_answer_node(state: QAState) -> dict:
    """Upstage Solar로 답변 생성"""
    start_time = time.time()

    question = state["question"]
    retrieved_docs = state["retrieved_docs"][:3]  # 상위 3개만 사용

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
4. 학습자료에 답이 없으면 "학습자료에서 해당 내용을 찾을 수 없습니다"라고 명시하세요

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
        "sources": sources,
        "answer_quality": "good"
    }

async def verify_answer_node(state: QAState) -> dict:
    """답변 품질 검증"""
    answer = state["answer"]

    # 간단한 품질 검사
    quality_issues = []

    if "찾을 수 없습니다" in answer or "없습니다" in answer.lower():
        quality_issues.append("답변이 불확실함")

    if len(answer) < 30:
        quality_issues.append("답변이 너무 짧음")

    if quality_issues:
        logger.warning(f"⚠️ Answer quality issues: {quality_issues}")
        answer_quality = "needs_review"
    else:
        answer_quality = "good"

    logger.info(f"✅ Answer quality: {answer_quality}")

    return {"answer_quality": answer_quality}

def should_use_fallback(state: QAState) -> str:
    """검색 결과에 따라 분기"""
    if state.get("has_relevant_docs", False):
        return "generate"
    else:
        return "fallback"

def create_qa_workflow():
    """QA LangGraph 워크플로우"""
    graph = StateGraph(QAState)

    # 노드 추가
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("fallback", fallback_response_node)
    graph.add_node("generate", generate_answer_node)
    graph.add_node("verify", verify_answer_node)

    # 엣지
    graph.add_edge(START, "retrieve")

    # 조건부 엣지: 검색 결과에 따라 분기
    graph.add_conditional_edges(
        "retrieve",
        should_use_fallback,
        {
            "generate": "generate",
            "fallback": "fallback"
        }
    )

    # fallback은 검증 없이 바로 종료
    graph.add_edge("fallback", END)

    # generate는 검증 후 종료
    graph.add_edge("generate", "verify")
    graph.add_edge("verify", END)

    return graph.compile()

qa_workflow = create_qa_workflow()
upload_workflow = create_upload_workflow()
