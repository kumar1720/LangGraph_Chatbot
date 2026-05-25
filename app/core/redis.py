# app/core/redis.py
import redis
from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

redis_client = None

if settings.REDIS_URL:
    try:
        logger.info("Initializing Upstash Redis client...")
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        # Verify connection
        redis_client.ping()
        logger.info("Upstash Redis connection successful!")
    except Exception as e:
        logger.error(f"Failed to connect to Upstash Redis: {e}")
        redis_client = None
else:
    logger.warning("REDIS_URL not configured. Caching is disabled.")
