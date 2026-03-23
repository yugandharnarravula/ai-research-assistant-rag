from typing import Dict, List

_memory_store: Dict[str, List[dict]] = {}


def add_message(session_id: str, role: str, content: str) -> None:
    _memory_store.setdefault(session_id, []).append({"role": role, "content": content})


def get_history(session_id: str, limit: int = 8) -> List[dict]:
    return _memory_store.get(session_id, [])[-limit:]


def summarize_history(session_id: str) -> str:
    history = get_history(session_id)
    if not history:
        return ""
    return "\n".join(f"{m['role']}: {m['content']}" for m in history)
