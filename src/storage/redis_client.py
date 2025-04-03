import json
import logging
import os
from typing import Any, Dict, List, Optional, Set, Union

from dotenv import load_dotenv

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

load_dotenv()

class RedisClient:
    """Redis client for managing positions and other data."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, redis_url: str = None):
        if self._initialized:
            return
        
        # Get Redis URL from environment variable or use default
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        self.pool = ConnectionPool.from_url(redis_url)
        self._initialized = True
        
        # Log a sanitized version of the URL (without credentials if any)
        sanitized_url = redis_url
        if "@" in redis_url:
            sanitized_url = redis_url.split("@")[-1]
            sanitized_url = f"redis://****:****@{sanitized_url}"
        
        logger.info(f"Redis client initialized with URL: {sanitized_url}")
    
    async def get_redis(self) -> redis.Redis:
        """Get a Redis connection from the pool."""
        return redis.Redis(connection_pool=self.pool)
    
    async def set_json(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Set a JSON value in Redis."""
        try:
            async with await self.get_redis() as conn:
                await conn.set(key, json.dumps(data))
                if ttl:
                    await conn.expire(key, ttl)
                return True
        except RedisError as e:
            logger.error(f"Error setting JSON in Redis: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get a JSON value from Redis."""
        try:
            async with await self.get_redis() as conn:
                data = await conn.get(key)
                if data:
                    return json.loads(data)
                return None
        except RedisError as e:
            logger.error(f"Error getting JSON from Redis: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        try:
            async with await self.get_redis() as conn:
                await conn.delete(key)
                return True
        except RedisError as e:
            logger.error(f"Error deleting key from Redis: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        try:
            async with await self.get_redis() as conn:
                return bool(await conn.exists(key))
        except RedisError as e:
            logger.error(f"Error checking key existence in Redis: {e}")
            return False
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching a pattern."""
        try:
            async with await self.get_redis() as conn:
                keys = await conn.keys(pattern)
                return [k.decode("utf-8") for k in keys]
        except RedisError as e:
            logger.error(f"Error getting keys from Redis: {e}")
            return []
    
    async def add_to_set(self, key: str, *values: str) -> int:
        """Add values to a Redis set."""
        try:
            async with await self.get_redis() as conn:
                return await conn.sadd(key, *values)
        except RedisError as e:
            logger.error(f"Error adding to set in Redis: {e}")
            return 0
    
    async def get_set_members(self, key: str) -> Set[str]:
        """Get all members of a Redis set."""
        try:
            async with await self.get_redis() as conn:
                members = await conn.smembers(key)
                return {m.decode("utf-8") for m in members}
        except RedisError as e:
            logger.error(f"Error getting set members from Redis: {e}")
            return set()
    
    async def remove_from_set(self, key: str, *values: str) -> int:
        """Remove values from a Redis set."""
        try:
            async with await self.get_redis() as conn:
                return await conn.srem(key, *values)
        except RedisError as e:
            logger.error(f"Error removing from set in Redis: {e}")
            return 0
