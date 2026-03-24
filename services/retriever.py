from typing import Dict, List, Optional
from functools import lru_cache
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue
from rank_bm25 import BM25Okapi


from config.settings import settings

@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings.EMBED_MODEL)

QDRANT = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
)


def vector_search(
    query: str, domain: Optional[str] = None, limit: Optional[int] = None
) -> List[Dict]:
    vector = MODEL.encode(query).tolist()
    limit = limit or settings.DEFAULT_K

    query_filter = None
    if domain and domain != "all":
        query_filter = Filter(
            must=[FieldCondition(key="domain", match=MatchValue(value=domain))]
        )

    results = QDRANT.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=vector,
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
    )

    docs = []
    for r in results:
        # 🔥 LOWER threshold
        if r.score < 0.35:
            continue

        payload = dict(r.payload)
        payload["score"] = float(r.score)

        docs.append(payload)

    return docs


def bm25_search(query: str, docs: List[Dict], limit: int = 10) -> List[Dict]:
    if not docs:
        return []

    tokenized = [d["text"].split() for d in docs]
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(query.split())

    ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)

    output = []
    for doc, score in ranked[:limit]:
        item = dict(doc)
        item["bm25_score"] = float(score)
        output.append(item)

    return output


def hybrid_search(query: str, domain: Optional[str] = None) -> List[Dict]:
    vector_docs = vector_search(query, domain=domain, limit=settings.DEFAULT_K)
    bm25_docs = bm25_search(query, vector_docs, limit=10)

    merged = {}
    for doc in vector_docs + bm25_docs:
        key = (doc["source"], doc["page"], doc["chunk_id"])
        if key not in merged:
            merged[key] = doc

    return list(merged.values())
