import hashlib
from pathlib import Path
from typing import List

import fitz  # PyMuPDF
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams, PayloadSchemaType
from sentence_transformers import SentenceTransformer


from config.settings import settings

# 🔥 Initialize embedding model
MODEL = SentenceTransformer(settings.EMBED_MODEL)

# 🔥 Qdrant Cloud connection (FINAL)
QDRANT = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
    timeout=60.0,  # 🔥 increase timeout
)


from qdrant_client.models import VectorParams, Distance, PayloadSchemaType


def ensure_collection():
    collections = QDRANT.get_collections().collections
    names = [c.name for c in collections]

    collections = QDRANT.get_collections().collections
    names = [c.name for c in collections]

    print("Existing collections:", names)

    if settings.QDRANT_COLLECTION not in names:
        print("Creating collection...")

        # ✅ Step 1: Create collection
        QDRANT.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE,
            ),
        )

        print("Collection created ✅")

        # ✅ Step 2: Create payload index (SAFE)
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
        separators=["\n\n", "\n", ".", " ", ""],  # 🔥 important
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

    for page_num, page in enumerate(doc):
        text = page.get_text()
        chunks = split_text(text)

        for i, chunk in enumerate(chunks):
            embedding = MODEL.encode(chunk).tolist()

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
    # 🚀 Upload to Qdrant
    import time

    BATCH_SIZE = 30  # 🔥 IMPORTANT

    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i : i + BATCH_SIZE]

        for attempt in range(3):  # retry logic
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
