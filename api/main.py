import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
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

app = FastAPI(title="AI Research Assistant (RAG-Based)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    domain: str = Form("general"),
) -> dict:
    save_path = UPLOAD_DIR / file.filename

    with open(save_path, "wb") as f:
        f.write(await file.read())

    return ingest_pdf(str(save_path), domain)


@app.get("/query")
def query(
    q: str,
    domain: Optional[str] = None,
    session_id: Optional[str] = None,
) -> dict:
    session_id = session_id or str(uuid.uuid4())
    cache_key = f"{session_id}:{domain}:{q}"

    cached = get_cache(cache_key)
    if cached:
        return cached

    chosen_domain = domain or detect_domain(q)
    route = route_query(q)
    history = summarize_history(session_id)

    if route == "web":
        docs = web_search(q)
    else:
        docs = hybrid_search(q, chosen_domain)
        docs = rerank(q, docs)

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
