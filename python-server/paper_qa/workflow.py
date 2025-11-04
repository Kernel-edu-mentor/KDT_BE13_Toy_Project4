from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict
from shared.chroma_client import chroma_client
from shared.upstage_client import upstage_client
from paper_qa.parsers.pdf_parser import pdf_parser
from paper_qa.parsers.ppt_parser import ppt_parser
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
    elif file_type == "ppt":
        parsed_blocks = ppt_parser.parse(file_path)
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


async def retrieve_node(state: QAState) -> dict:
    """ChromaDB에서 관련 문서 검색"""
    start_time = time.time()

    question = state["question"]
    material_id = state["material_id"]

    logger.info(f"Retrieving docs for: {question}")

    # 1. 질문 임베딩 (수정된 코드 적용 가정)
    query_embedding = (await upstage_client.embed_documents([question]))[0]

    # 검색 (k=3으로 제한 - 속도 최적화)
    results = chroma_client.search(
        collection_name="learning_materials",
        query_embeddings=[query_embedding],  # Upstage 임베딩 사용
        n_results=3,
        filter_dict={"material_id": material_id}
    )

    # 🌟🌟🌟 변수 초기화 추가 🌟🌟🌟
    retrieved_docs = []

    # 결과 구성
    for i in range(len(results['documents'][0])):
        retrieved_docs.append({
            'content': results['documents'][0][i],
            'page': results['metadatas'][0][i]['page'],
            'type': results['metadatas'][0][i]['type'],
            'distance': results['distances'][0][i]
        })

    retrieve_time = time.time() - start_time
    logger.info(f"⚡ Retrieve time: {retrieve_time:.3f}s")

    return {"retrieved_docs": retrieved_docs}  # 이제 retrieved_docs가 정의됨

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
upload_workflow = create_upload_workflow()
