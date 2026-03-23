def detect_domain(query: str) -> str:
    q = query.lower()

    if any(word in q for word in ["stock", "market", "finance", "bank", "inflation"]):
        return "finance"
    if any(word in q for word in ["python", "llm", "rag", "database", "api", "model"]):
        return "tech"
    if any(
        word in q
        for word in ["security", "phishing", "xss", "sql injection", "malware"]
    ):
        return "security"

    return "general"


def route_query(query: str) -> str:
    q = query.lower()

    if any(word in q for word in ["latest", "today", "news", "current", "recent"]):
        return "web"

    return "rag"
