import hashlib
from pathlib import Path
from typing import List

import fitz  # PyMuPDF
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams, PayloadSchemaType

from config.settings import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 🔥 Lazy + cached model loading (FIXED)
@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings.EMBED_MODEL)


# 🔥 Qdrant Cloud connection
QDRANT = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
    timeout=300.0,
)


def ensure_collection():
    collections = QDRANT.get_collections().collections
    names = [c.name for c in collections]

    collections = QDRANT.get_collections().collections
    names = [c.name for c in collections]

    print("Existing collections:", names)

    if settings.QDRANT_COLLECTION not in names:
        print("Creating collection...")

        QDRANT.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE,
            ),
        )

        print("Collection created ✅")

        try:
            QDRANT.create_payload_index(
                collection_name=settings.QDRANT_COLLECTION,
                field_name="domain",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            print("Payload index created ✅")
        except Exception as e:
            print("Payload index warning:", e)


# 🧠 Text chunking
def split_text(text: str, chunk_size: int = 800, chunk_overlap: int = 120) -> List[str]:
    text = text.strip()
    if not text:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    return splitter.split_text(text)


# 🔑 Stable ID generator
def generate_id(source: str, page: int, chunk_index: int) -> int:
    raw = f"{source}-{page}-{chunk_index}".encode("utf-8")
    return int(hashlib.md5(raw).hexdigest()[:12], 16)


# 🚀 MAIN FUNCTION
def ingest_pdf(file_path: str, domain: str = "general") -> dict:
    ensure_collection()

    file_path = Path(file_path)
    doc = fitz.open(file_path)

    points = []
    total_chunks = 0
    model = get_model()
    # 🔥 Load model ONCE (IMPORTANT FIX)

    for page_num, page in enumerate(doc):
        text = page.get_text()
        chunks = split_text(text)

        # 🔥 ADD THIS BLOCK HERE
        print("Chunks before limit:", len(chunks))
        chunks = chunks[:50]  # 🔥 LIMIT PER PAGE (VERY IMPORTANT)
        print("Chunks after limit:", len(chunks))

        for i, chunk in enumerate(chunks):
            embedding = model.encode(chunk).tolist()
            point = PointStruct(
                id=generate_id(file_path.name, page_num, i),
                vector=embedding,
                payload={
                    "text": chunk,
                    "source": file_path.name,
                    "page": page_num + 1,
                    "domain": domain,
                    "document_id": file_path.stem,
                    "chunk_id": i,
                },
            )

            points.append(point)
            total_chunks += 1

    if len(points) > 3000:
        print("⚠️ Large file detected, may take time...")

    # 🚀 Upload to Qdrant (batched + retry)
    import time

    BATCH_SIZE = 10

    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i : i + BATCH_SIZE]
        print(f"🚀 Uploading batch {i} to {i + BATCH_SIZE}")
        for attempt in range(3):
            try:
                QDRANT.upsert(
                    collection_name=settings.QDRANT_COLLECTION,
                    points=batch,
                )
                break
            except Exception as e:
                print(f"Retry {attempt + 1} due to error: {e}")
                time.sleep(2)

    return {
        "status": "success",
        "file": file_path.name,
        "domain": domain,
        "pages": len(doc),
        "chunks": total_chunks,
    }