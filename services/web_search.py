from typing import Dict, List

from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 5) -> List[Dict]:
    docs = []

    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=max_results)

        for r in results:
            docs.append(
                {
                    "text": r.get("body", ""),
                    "source": r.get("href", "web"),
                    "page": "web",
                    "domain": "web",
                    "chunk_id": -1,
                }
            )

    return docs
