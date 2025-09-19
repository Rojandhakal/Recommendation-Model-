import redis
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger("redis")

redis_client = None

def get_redis():
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            redis_client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            redis_client = None
    return redis_client