import json
from unittest.mock import patch, MagicMock

import fakeredis.aioredis
import pytest
import pytest_asyncio

from src.storage.redis_client import RedisClient, UUIDEncoder


@pytest.fixture
def uuid_encoder():
    """Fixture for UUID encoder instance."""
    return UUIDEncoder()


class TestUUIDEncoder:
    """Tests for UUIDEncoder class."""

    def test_encode_uuid(self, uuid_encoder):
        """Test encoding UUID to string."""
        from uuid import UUID

        test_uuid = UUID("12345678-1234-5678-1234-567812345678")

        # Test encoding with UUIDEncoder
        encoded = json.dumps(test_uuid, cls=UUIDEncoder)

        # Should be a JSON string with the UUID as string
        assert encoded == '"12345678-1234-5678-1234-567812345678"'

    def test_encode_dict_with_uuid(self, uuid_encoder):
        """Test encoding dictionary containing UUID."""
        from uuid import UUID

        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        test_dict = {"id": test_uuid, "name": "test"}

        # Test encoding with UUIDEncoder
        encoded = json.dumps(test_dict, cls=UUIDEncoder)

        # Should be a JSON string with UUID converted to string
        expected = '{"id": "12345678-1234-5678-1234-567812345678", "name": "test"}'
        assert json.loads(encoded) == json.loads(expected)


@pytest_asyncio.fixture
async def redis_client():
    """Fixture for RedisClient with fakeredis."""
    # Use fakeredis for testing
    fake_redis = fakeredis.aioredis.FakeRedis()

    with patch("redis.asyncio.Redis", return_value=fake_redis):
        with patch("redis.asyncio.ConnectionPool.from_url", return_value=MagicMock()):
            client = RedisClient("redis://fakehost:6380/0")
            # Override get_redis to return our fake redis
            client.get_redis = MagicMock(return_value=fake_redis)
            yield client

            # Clean up
            await fake_redis.flushall()


class TestRedisClient:
    """Tests for RedisClient class."""

    @pytest.mark.asyncio
    async def test_set_get_json(self, redis_client):
        """Test setting and getting JSON data."""
        # Test data
        key = "test_key"
        data = {"name": "Test", "value": 123}

        # Set the data
        result = await redis_client.set_json(key, data)
        assert result is True

        # Get the data
        retrieved = await redis_client.get_json(key)
        assert retrieved == data

    @pytest.mark.asyncio
    async def test_delete(self, redis_client):
        """Test deleting a key."""
        # Set up test data
        key = "test_delete"
        data = {"name": "DeleteMe"}

        # Set the data
        await redis_client.set_json(key, data)

        # Verify it exists
        assert await redis_client.exists(key) is True

        # Delete the key
        result = await redis_client.delete(key)
        assert result is True

        # Verify it's gone
        assert await redis_client.exists(key) is False

    @pytest.mark.asyncio
    async def test_keys(self, redis_client):
        """Test getting keys matching a pattern."""
        # Set up test data
        await redis_client.set_json("test:1", {"id": 1})
        await redis_client.set_json("test:2", {"id": 2})
        await redis_client.set_json("other:1", {"id": 3})

        # Get keys matching pattern
        keys = await redis_client.keys("test:*")

        # Verify we got the right keys
        assert len(keys) == 2
        assert "test:1" in keys
        assert "test:2" in keys
        assert "other:1" not in keys

    @pytest.mark.asyncio
    async def test_set_operations(self, redis_client):
        """Test Redis set operations."""
        # Test set key
        set_key = "test_set"

        # Add values to set
        result = await redis_client.add_to_set(set_key, "value1", "value2")
        assert result == 2

        # Get set members
        members = await redis_client.get_set_members(set_key)
        assert members == {"value1", "value2"}

        # Add more values
        result = await redis_client.add_to_set(set_key, "value3", "value1")  # value1 is a duplicate
        assert result == 1  # Only 1 new value added

        # Get updated members
        members = await redis_client.get_set_members(set_key)
        assert members == {"value1", "value2", "value3"}

        # Remove values
        result = await redis_client.remove_from_set(
            set_key, "value1", "value99"
        )  # value99 doesn't exist
        assert result == 1  # Only 1 value removed

        # Get final members
        members = await redis_client.get_set_members(set_key)
        assert members == {"value2", "value3"}
