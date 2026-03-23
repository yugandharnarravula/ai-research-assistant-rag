from typing import Dict, List

from sentence_transformers import CrossEncoder

from config.settings import settings

RERANKER = CrossEncoder(settings.RERANK_MODEL)


def rerank(query: str, docs: List[Dict], top_k: int = None) -> List[Dict]:
    if not docs:
        return []

    top_k = top_k or settings.FINAL_TOP_K
    pairs = [(query, d["text"]) for d in docs]
    scores = RERANKER.predict(pairs)

    ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)

    output = []
    for doc, score in ranked[:top_k]:
        item = dict(doc)
        item["rerank_score"] = float(score)
        output.append(item)

    return output
