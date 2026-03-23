import json
from typing import Any, Optional
import redis
from config.settings import settings

# ✅ Use URL (for cloud like Upstash)
if settings.REDIS_URL:
    redis_client = redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True
    )
else:
    # ✅ fallback (local only)
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=getattr(settings, "REDIS_PASSWORD", None),
        decode_responses=True,
    )


def get_cache(key: str) -> Optional[Any]:
    try:
        value = redis_client.get(key)
    except Exception:
        return None

    if value is None:
        return None

    try:
        return json.loads(value)
    except:
        return value


def set_cache(key: str, value: Any, ttl_seconds: int = 3600) -> None:
    try:
        redis_client.set(key, json.dumps(value), ex=ttl_seconds)
    except Exception:
        pass