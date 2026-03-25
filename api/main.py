import uuid
from pathlib import Path
from typing import Optional
import shutil
from fastapi import FastAPI, File, Form, UploadFile,BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from services.cache import get_cache, set_cache
from services.generator import generate_answer
from services.ingest import ingest_pdf
from services.memory import add_message, summarize_history
from services.reranker import rerank
from services.retriever import hybrid_search
from services.router import detect_domain, route_query
from services.verifier import verify_answer
from services.web_search import web_search
from qdrant_client import QdrantClient
from config.settings import settings

q = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
print("DEBUG_COLLECTION:", settings.QDRANT_COLLECTION)
print("DEBUG_COUNT:", q.count(collection_name=settings.QDRANT_COLLECTION, exact=True))

app = FastAPI(title="AI Research Assistant (RAG-Based)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

def process_ingest(file_path: str, domain: str):
    try:
        print("🚀 Starting ingestion...")
        result = ingest_pdf(file_path, domain)
        print("✅ Ingestion completed:", result)

    except Exception as e:
        import traceback
        print("❌ FULL ERROR:")
        traceback.print_exc()

@app.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    domain: str = Form("general"),
) -> dict:
    save_path = UPLOAD_DIR / file.filename

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    background_tasks.add_task(process_ingest, str(save_path), domain)
    return ingest_pdf(str(save_path), domain)


@app.get("/query")
def query(
    q: str,
    domain: Optional[str] = None,
    session_id: Optional[str] = None,
) -> dict:
    session_id = session_id or str(uuid.uuid4())
    cache_key = f"{session_id}:{domain}:{q}"

    try:
        cached = get_cache(cache_key)
    except Exception as e:
        print("Cache error:", e)
        cached = None
    if cached:
        return cached

    chosen_domain = domain or detect_domain(q)
    route = route_query(q)
    history = summarize_history(session_id)

    if route == "web":
        docs = web_search(q)
    else:
        try:
            docs = hybrid_search(q, chosen_domain)
            docs = rerank(q, docs)
        except Exception as e:
            print("Search error:", e)
            docs = []

    generated = generate_answer(q, docs, history=history)
    # ONLY VERIFY IF SOURCES EXIST
    if generated["sources"]:
        verification = verify_answer(generated["answer"], docs)
    else:
        verification = {
            "confidence": 0.0,
            "is_valid": False,
            "reason": "Answer generated from LLM (no document support)",
        }

    result = {
        "session_id": session_id,
        "route": route,
        "domain": chosen_domain,
        "answer": generated["answer"],
        "sources": generated["sources"],
        "context_preview": generated["context"][:1200],
        "confidence": verification["confidence"],
        "verified": verification["is_valid"],
        "verification_reason": verification["reason"],
    }

    add_message(session_id, "user", q)
    add_message(session_id, "assistant", generated["answer"])
    set_cache(cache_key, result)

    return result
