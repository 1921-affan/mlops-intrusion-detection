import redis
import json
import hashlib
import logging
from typing import Optional

logger = logging.getLogger("redis_cache")

REDIS_HOST = "redis"   # docker-compose service name
REDIS_PORT = 6379
CACHE_TTL_SECONDS = 300  # 5 minutes

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
)

def _make_cache_key(feature_vector: list) -> str:
    """
    Stable hash for a numeric feature vector.
    """
    serialized = json.dumps(feature_vector, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode()).hexdigest()
    return f"cache:inference:{digest}"

def get_cached_prediction(feature_vector: list) -> Optional[int]:
    try:
        key = _make_cache_key(feature_vector)
        value = redis_client.get(key)
        if value is not None:
            logger.info("⚡ Redis cache HIT")
            return int(value)
    except Exception as e:
        logger.warning("Redis cache read failed: %s", e)
    return None

def set_cached_prediction(feature_vector: list, prediction: int) -> None:
    try:
        key = _make_cache_key(feature_vector)
        redis_client.setex(
            key,
            CACHE_TTL_SECONDS,
            int(prediction),
        )
    except Exception as e:
        logger.warning("Redis cache write failed: %s", e)
