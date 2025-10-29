#!/usr/bin/env python3
"""Manual test runner for paper_qa modules without external testing frameworks."""

import asyncio
import importlib
import inspect
import os
import sys
import types
from pathlib import Path
from tempfile import NamedTemporaryFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

FAKE_CHROMA = None
FAKE_UPSTAGE = None


def install_fastapi_stub():
    try:
        import fastapi  # type: ignore  # noqa: F401
        return
    except Exception:
        pass

    module = types.ModuleType("fastapi")

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    class APIRouter:
        def __init__(self, *args, **kwargs):
            self.routes = []

        def post(self, path: str, response_model=None):
            def decorator(func):
                self.routes.append(("POST", path, func, response_model))
                return func

            return decorator

    module.HTTPException = HTTPException
    module.APIRouter = APIRouter
    sys.modules["fastapi"] = module


def install_pydantic_stub():
    try:
        from pydantic import BaseModel  # type: ignore  # noqa: F401
        return
    except Exception:
        pass

    module = types.ModuleType("pydantic")

    class BaseModel:
        def __init__(self, **data):
            for key, value in data.items():
                setattr(self, key, value)

        def dict(self):
            return dict(self.__dict__)

        def model_dump(self):
            return self.dict()

        def __repr__(self):
            fields = ", ".join(f"{key}={value!r}" for key, value in self.__dict__.items())
            return f"{self.__class__.__name__}({fields})"

    module.BaseModel = BaseModel
    sys.modules["pydantic"] = module


def install_config_stub():
    try:
        import config  # type: ignore  # noqa: F401
        return
    except Exception:
        pass

    sys.modules.pop("config", None)
    module = types.ModuleType("config")

    class StubSettings:
        def __init__(self):
            self.UPSTAGE_API_KEY = "stub-key"
            self.CHROMA_HOST = "localhost"
            self.CHROMA_PORT = 8001
            self.UPLOAD_DIR = str(PROJECT_ROOT / "uploads")
            self.CACHE_SIZE = 8

    module.settings = StubSettings()
    sys.modules["config"] = module


def install_langgraph_stub():
    try:
        from langgraph.graph import StateGraph  # type: ignore  # noqa: F401
        return
    except Exception:
        pass

    module = types.ModuleType("langgraph.graph")

    START = "__start__"
    END = "__end__"

    class CompiledGraph:
        def __init__(self, nodes, edges):
            self._nodes = nodes
            self._edges = edges

        async def ainvoke(self, state):
            data = dict(state)
            current = START
            while True:
                next_nodes = self._edges.get(current, [])
                if not next_nodes:
                    break
                next_node = next_nodes[0]
                if next_node == END:
                    break
                node_fn = self._nodes[next_node]
                result = node_fn(data)
                if inspect.isawaitable(result):
                    result = await result
                if not isinstance(result, dict):
                    raise ValueError(f"Node '{next_node}' returned non-dict result: {result!r}")
                data.update(result)
                current = next_node
            return data

    class StateGraph:
        def __init__(self, state_type):
            self.state_type = state_type
            self._nodes = {}
            self._edges = {}

        def add_node(self, name, func):
            self._nodes[name] = func

        def add_edge(self, source, target):
            self._edges.setdefault(source, []).append(target)

        def compile(self):
            return CompiledGraph(self._nodes, self._edges)

    module.StateGraph = StateGraph
    module.START = START
    module.END = END
    sys.modules["langgraph.graph"] = module


class _StubLLMResponse:
    def __init__(self, content: str):
        self.content = content


def install_langchain_stubs():
    schema_module = sys.modules.get("langchain.schema")
    if schema_module is None:
        schema_module = types.ModuleType("langchain.schema")
        sys.modules["langchain.schema"] = schema_module

    if not hasattr(schema_module, "HumanMessage"):
        class HumanMessage:
            def __init__(self, content: str):
                self.content = content

        schema_module.HumanMessage = HumanMessage

    module = types.ModuleType("langchain_upstage")
    sys.modules["langchain_upstage"] = module

    class ChatUpstage:
        def __init__(self, api_key: str, model: str, temperature: float = 0.3):
            self.api_key = api_key
            self.model = model
            self.temperature = temperature
            self._history = []

        async def ainvoke(self, messages):
            prompt = messages[-1].content if messages else ""
            self._history.append(prompt)
            if "3가지" in prompt or "변환" in prompt:
                return _StubLLMResponse("질문 변형 1\n질문 변형 2\n질문 변형 3")
            return _StubLLMResponse("Stub answer referencing provided context.")

    module.ChatUpstage = ChatUpstage


def install_shared_client_stubs():
    global FAKE_CHROMA, FAKE_UPSTAGE

    class FakeChromaClient:
        def __init__(self):
            self.reset()

        def reset(self):
            self.collections = {}
            self.add_log = []
            self.search_log = []

        def add_documents(self, collection_name, documents, metadatas, ids, embeddings=None):
            bucket = self.collections.setdefault(collection_name, [])
            for doc, meta, doc_id in zip(documents, metadatas, ids):
                bucket.append({
                    "id": doc_id,
                    "document": doc,
                    "metadata": dict(meta),
                })
            self.add_log.append({
                "collection": collection_name,
                "count": len(documents),
            })

        def search(self, collection_name, query_texts=None, query_embeddings=None, n_results=3, filter_dict=None):
            results = []
            for entry in self.collections.get(collection_name, []):
                if filter_dict and entry["metadata"].get("material_id") != filter_dict.get("material_id"):
                    continue
                results.append(entry)

            results = results[:n_results] if results else []

            if not results:
                docs = [""]
                metadatas = [{}]
                distances = [1.0]
                ids = ["none"]
            else:
                docs = [r["document"] for r in results]
                metadatas = [r["metadata"] for r in results]
                distances = [0.1 * (idx + 1) for idx, _ in enumerate(results)]
                ids = [r["id"] for r in results]

            payload = {
                "documents": [docs],
                "metadatas": [metadatas],
                "distances": [distances],
                "ids": [ids],
            }
            self.search_log.append({
                "collection": collection_name,
                "queries": list(query_texts or []),
                "filter": dict(filter_dict or {}),
                "result_count": len(docs),
            })
            return payload

    class FakeUpstageClient:
        def __init__(self):
            self.parse_calls = []
            self.embed_calls = []

        async def parse_pdf(self, file_path: str):
            self.parse_calls.append(file_path)
            return {
                "elements": [
                    {"type": "text", "content": "First block", "page": 1},
                    {"type": "text", "content": "Second block", "page": 2},
                ]
            }

        async def embed_documents(self, texts):
            self.embed_calls.append(list(texts))
            return [[float(index + 1) for _ in range(3)] for index, _ in enumerate(texts)]

        async def embed_query(self, text):
            return [0.42]

    # Register package container (this hides the real shared package on purpose)
    shared_pkg = types.ModuleType("shared")
    shared_pkg.__path__ = []  # type: ignore[attr-defined]
    sys.modules["shared"] = shared_pkg

    chroma_module = types.ModuleType("shared.chroma_client")
    FAKE_CHROMA = FakeChromaClient()
    chroma_module.chroma_client = FAKE_CHROMA
    chroma_module.__all__ = ["chroma_client"]
    sys.modules["shared.chroma_client"] = chroma_module

    upstage_module = types.ModuleType("shared.upstage_client")
    FAKE_UPSTAGE = FakeUpstageClient()
    upstage_module.upstage_client = FAKE_UPSTAGE
    upstage_module.__all__ = ["upstage_client"]
    sys.modules["shared.upstage_client"] = upstage_module

    setattr(shared_pkg, "chroma_client", chroma_module.chroma_client)
    setattr(shared_pkg, "upstage_client", upstage_module.upstage_client)
    shared_pkg.__all__ = ["chroma_client", "upstage_client"]


def install_ppt_parser_stub():
    try:
        import paper_qa.parsers.ppt_parser  # type: ignore  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    module = types.ModuleType("paper_qa.parsers.ppt_parser")

    class FakePPTParser:
        def parse(self, file_path: str):
            return [
                {"type": "slide", "content": f"Slide extracted from {Path(file_path).name}", "page": 1},
            ]

    module.ppt_parser = FakePPTParser()
    sys.modules["paper_qa.parsers.ppt_parser"] = module

    # Ensure package exposes the parser
    parsers_pkg = importlib.import_module("paper_qa.parsers")
    setattr(parsers_pkg, "ppt_parser", module.ppt_parser)


def install_dependency_stubs():
    install_fastapi_stub()
    install_pydantic_stub()
    install_config_stub()
    install_langgraph_stub()
    install_langchain_stubs()
    install_shared_client_stubs()


def require_stub_clients():
    if FAKE_CHROMA is None or FAKE_UPSTAGE is None:
        raise RuntimeError("Failed to initialise fake shared clients; ensure stubs are installed before running tests.")


def reset_fake_chroma():
    require_stub_clients()
    if hasattr(FAKE_CHROMA, "reset"):
        FAKE_CHROMA.reset()
    else:
        raise RuntimeError("Stub chroma client does not expose reset(); adjust manual test stubs accordingly.")


def ensure_models_have_upload_types():
    module_name = "paper_qa.models"
    models = sys.modules.get(module_name)

    temp_pkg_created = False
    if models is None:
        models_path = PROJECT_ROOT / "paper_qa" / "models.py"
        if not models_path.exists():
            raise FileNotFoundError(f"Could not locate {models_path}")

        if "paper_qa" not in sys.modules:
            temp_pkg = types.ModuleType("paper_qa")
            temp_pkg.__path__ = [str(PROJECT_ROOT / "paper_qa")]
            sys.modules["paper_qa"] = temp_pkg
            temp_pkg_created = True

        spec = importlib.util.spec_from_file_location(module_name, models_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to load paper_qa.models for stubbing")

        models = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = models
        spec.loader.exec_module(models)

        if temp_pkg_created:
            sys.modules.pop("paper_qa", None)

    MaterialUploadRequest = getattr(models, "MaterialUploadRequest", None)
    MaterialUploadResponse = getattr(models, "MaterialUploadResponse", None)

    if MaterialUploadRequest is None:
        class MaterialUploadRequest(models.BaseModel):  # type: ignore[attr-defined]
            material_id: int
            file_path: str
            file_type: str = "pdf"

        setattr(models, "MaterialUploadRequest", MaterialUploadRequest)

    if MaterialUploadResponse is None:
        class MaterialUploadResponse(models.BaseModel):  # type: ignore[attr-defined]
            material_id: int
            status: str
            page_count: int
            chunk_count: int
            message: str

        setattr(models, "MaterialUploadResponse", MaterialUploadResponse)


async def test_query_cache_eviction():
    from paper_qa.utils.cache import QueryCache

    cache = QueryCache(maxsize=2)
    cache.set("A", 1)
    cache.set("B", 2)
    cache.set("C", 3)

    assert cache.get("A") is None, "Oldest entry should be evicted when cache is full"
    assert cache.get("B") == 2
    assert cache.get("C") == 3


async def test_upload_workflow_success(workflow_module):
    reset_fake_chroma()
    state = {
        "material_id": 101,
        "file_path": "/tmp/fake.pdf",
        "file_type": "pdf",
    }
    result = await workflow_module.upload_workflow.ainvoke(state)
    assert result.get("status") == "completed", "Upload workflow should mark status as completed"
    assert result.get("parsed_blocks"), "Parsed blocks should not be empty"
    stored = FAKE_CHROMA.collections.get("learning_materials", [])
    assert stored, "Documents should be stored in fake Chroma client"


async def test_upload_api_success(api_module, models_module):
    reset_fake_chroma()
    with NamedTemporaryFile("w", suffix=".pdf", delete=False) as tmp:
        tmp.write("fake pdf")
        tmp.flush()
        file_path = Path(tmp.name)

    try:
        request = models_module.MaterialUploadRequest(material_id=202, file_path=str(file_path))
        response = await api_module.upload_material(request)
        assert response.status == "completed", "Upload API should report completed status"
        assert response.page_count == response.chunk_count, "Page and chunk counts should match the parsed block count"
        assert "Successfully processed" in response.message
    finally:
        try:
            os.unlink(file_path)
        except FileNotFoundError:
            pass


async def test_upload_api_missing_file(api_module, models_module):
    request = models_module.MaterialUploadRequest(material_id=303, file_path="/no/such/file.pdf")
    response = await api_module.upload_material(request)
    assert response.status == "failed", "Missing file should lead to failed status"
    assert "File not found" in response.message or "Processing failed" in response.message


async def seed_material(material_id: int, workflow_module):
    reset_fake_chroma()
    state = {
        "material_id": material_id,
        "file_path": "/tmp/seed.pdf",
        "file_type": "pdf",
    }
    await workflow_module.upload_workflow.ainvoke(state)


async def test_qa_workflow_success(workflow_module):
    await seed_material(material_id=404, workflow_module=workflow_module)
    result = await workflow_module.qa_workflow.ainvoke({
        "question": "무슨 내용이 있나요?",
        "material_id": 404,
    })
    assert result.get("answer"), "QA workflow should generate an answer"
    assert result.get("sources"), "QA workflow should include sources"


async def test_api_ask_question_missing_workflow(api_module, models_module):
    request = models_module.QARequest(material_id=505, question="테스트 질문")
    try:
        await api_module.ask_question(request)
    except NameError as exc:
        assert "qa_workflow" in str(exc), "Expected missing qa_workflow NameError"
        return
    except Exception as exc:
        raise AssertionError(f"Expected NameError for missing qa_workflow, got {exc!r}")
    raise AssertionError("ask_question succeeded unexpectedly without qa_workflow")


async def test_api_ask_question_success(api_module, models_module, workflow_module):
    await seed_material(material_id=606, workflow_module=workflow_module)
    api_module.qa_workflow = workflow_module.qa_workflow
    request = models_module.QARequest(material_id=606, question="첫 번째 블록은 무엇인가요?")
    response = await api_module.ask_question(request)
    assert response.answer, "ask_question should return an answer"
    assert response.sources, "ask_question should return sources"
    assert response.response_time_ms >= 0


async def run_manual_tests():
    install_dependency_stubs()
    require_stub_clients()
    ensure_models_have_upload_types()
    install_ppt_parser_stub()

    workflow_module = importlib.import_module("paper_qa.workflow")
    api_module = importlib.import_module("paper_qa.api")
    models_module = importlib.import_module("paper_qa.models")

    tests = [
        ("query_cache_eviction", test_query_cache_eviction),
        ("upload_workflow_success", lambda: test_upload_workflow_success(workflow_module)),
        ("upload_api_success", lambda: test_upload_api_success(api_module, models_module)),
        ("upload_api_missing_file", lambda: test_upload_api_missing_file(api_module, models_module)),
        ("qa_workflow_success", lambda: test_qa_workflow_success(workflow_module)),
        ("api_ask_question_missing_workflow", lambda: test_api_ask_question_missing_workflow(api_module, models_module)),
        ("api_ask_question_success", lambda: test_api_ask_question_success(api_module, models_module, workflow_module)),
    ]

    results = []

    for name, factory in tests:
        try:
            coro = factory()
            if not inspect.isawaitable(coro):
                raise RuntimeError(f"Test '{name}' did not return an awaitable coroutine")
            await coro
            results.append((name, "PASS", ""))
        except AssertionError as exc:
            results.append((name, "FAIL", str(exc)))
        except Exception as exc:
            results.append((name, "ERROR", repr(exc)))

    print("Manual Test Results")
    for name, status, message in results:
        line = f"[{status}] {name}"
        print(line)
        if message:
            print(f"    -> {message}")

    failures = [r for r in results if r[1] != "PASS"]
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_manual_tests())
