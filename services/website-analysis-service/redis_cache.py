# services/website-analysis-service/redis_cache.py
"""
Redis 캐시 클라이언트 (웹사이트 AI 분석 결과 캐싱용)
- 비동기 redis.asyncio 사용
- Redis 장애 시 서비스는 정상 동작 (Fallback to API)
"""
from __future__ import annotations

import hashlib
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

_redis_client: Optional[Any] = None

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
WEBSITE_ANALYSIS_CACHE_TTL = 86400  # 24시간


def _make_website_cache_key(url: str) -> str:
    """URL 기반 캐시 키 생성 (website_analysis:{hashed_url})"""
    normalized = url.strip().lower()
    h = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"website_analysis:{h}"


async def get_redis() -> Optional[Any]:
    """Redis 클라이언트 반환 (없으면 None)"""
    return _redis_client


async def connect_redis() -> bool:
    """Redis 연결 초기화. 실패 시 False 반환 (서비스는 계속 동작)"""
    global _redis_client
    try:
        import redis.asyncio as redis  # type: ignore[import-untyped]

        client = redis.from_url(REDIS_URL, decode_responses=True)
        await client.ping()
        _redis_client = client
        logger.info("✅ Redis connected successfully (website analysis cache)")
        return True
    except Exception as e:
        logger.warning("⚠️ Redis connection failed - caching disabled: %s", e)
        _redis_client = None
        return False


async def disconnect_redis() -> None:
    """Redis 연결 종료"""
    global _redis_client
    if _redis_client:
        try:
            await _redis_client.aclose()
        except Exception as e:
            logger.warning("Redis disconnect error: %s", e)
        _redis_client = None


async def get_cached_website_analysis(url: str) -> Optional[str]:
    """
    캐시에서 웹사이트 분석 결과 조회.
    Cache Hit: JSON 문자열 반환, Cache Miss: None 반환
    """
    redis_client = await get_redis()
    if not redis_client:
        return None
    try:
        cache_key = _make_website_cache_key(url)
        value = await redis_client.get(cache_key)
        return value
    except Exception as e:
        logger.warning("Redis GET error (url=%s): %s", url[:50], e)
        return None


async def set_cached_website_analysis(
    url: str, value: str, ttl: int = WEBSITE_ANALYSIS_CACHE_TTL
) -> bool:
    """
    웹사이트 분석 결과를 캐시에 저장.
    성공 시 True, 실패 시 False
    """
    redis_client = await get_redis()
    if not redis_client:
        return False
    try:
        cache_key = _make_website_cache_key(url)
        await redis_client.setex(cache_key, ttl, value)
        return True
    except Exception as e:
        logger.warning("Redis SET error (url=%s): %s", url[:50], e)
        return False
