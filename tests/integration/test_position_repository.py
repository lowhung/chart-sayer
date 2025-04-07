"""
Integration tests for position repository.
"""

from unittest.mock import patch, MagicMock
from uuid import UUID

import fakeredis.aioredis
import pytest
import pytest_asyncio

from src.positions.models import (
    Position,
    PositionCreate,
    PositionStatus,
    PlatformType,
    PositionType,
)
from src.positions.repository import PositionRepository
from src.storage.redis_client import RedisClient


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


@pytest_asyncio.fixture
async def position_repository(redis_client):
    """Fixture for PositionRepository with fake Redis."""
    return PositionRepository(redis_client)


@pytest_asyncio.fixture
async def sample_position_data():
    """Fixture for sample position data."""
    return PositionCreate(
        user_id="123456789",
        platform=PlatformType.DISCORD,
        symbol="BTCUSDT",
        type=PositionType.LONG,
        entry_price=50000.0,
        take_profit=55000.0,
        stop_loss=48000.0,
    )


class TestPositionRepository:
    """Integration tests for PositionRepository."""

    @pytest.mark.asyncio
    async def test_create_position(self, position_repository, sample_position_data):
        """Test creating a position."""
        # Create position
        position = await position_repository.create_position(sample_position_data)

        # Verify position was created
        assert isinstance(position, Position)
        assert position.user_id == sample_position_data.user_id
        assert position.platform == sample_position_data.platform
        assert position.symbol == sample_position_data.symbol
        assert position.type == sample_position_data.type
        assert position.entry_price == sample_position_data.entry_price
        assert position.take_profit == sample_position_data.take_profit
        assert position.stop_loss == sample_position_data.stop_loss
        assert position.status == PositionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_position(self, position_repository, sample_position_data):
        """Test getting a position by ID."""
        # Create position
        created_position = await position_repository.create_position(sample_position_data)

        # Get position by ID
        position = await position_repository.get_position(created_position.id)

        # Verify position
        assert position is not None
        assert position.id == created_position.id
        assert position.user_id == sample_position_data.user_id
        assert position.symbol == sample_position_data.symbol

        # Test non-existent position
        position = await position_repository.get_position(
            UUID("00000000-0000-0000-0000-000000000000")
        )
        assert position is None

    @pytest.mark.asyncio
    async def test_update_position(self, position_repository, sample_position_data):
        """Test updating a position."""
        # Create position
        created_position = await position_repository.create_position(sample_position_data)

        # Update position
        from src.positions.models import PositionUpdate

        update_data = PositionUpdate(
            entry_price=51000.0,
            take_profit=56000.0,
            stop_loss=49000.0,
        )

        updated_position = await position_repository.update_position(
            created_position.id, update_data
        )

        # Verify updates
        assert updated_position is not None
        assert updated_position.entry_price == 51000.0
        assert updated_position.take_profit == 56000.0
        assert updated_position.stop_loss == 49000.0
        assert updated_position.status == PositionStatus.ACTIVE

        # Fetch position again to ensure persistence
        position = await position_repository.get_position(created_position.id)
        assert position.entry_price == 51000.0

    @pytest.mark.asyncio
    async def test_stop_position(self, position_repository, sample_position_data):
        """Test stopping a position."""
        # Create position
        created_position = await position_repository.create_position(sample_position_data)

        # Stop position
        stopped_position = await position_repository.stop_position(created_position.id)

        # Verify it's stopped
        assert stopped_position is not None
        assert stopped_position.status == PositionStatus.STOPPED

        # Fetch position again to ensure persistence
        position = await position_repository.get_position(created_position.id)
        assert position.status == PositionStatus.STOPPED

    @pytest.mark.asyncio
    async def test_close_position(self, position_repository, sample_position_data):
        """Test closing a position."""
        # Create position
        created_position = await position_repository.create_position(sample_position_data)

        # Close position
        closed_position = await position_repository.close_position(created_position.id)

        # Verify it's closed
        assert closed_position is not None
        assert closed_position.status == PositionStatus.CLOSED
        assert closed_position.closed_at is not None

        # Fetch position again to ensure persistence
        position = await position_repository.get_position(created_position.id)
        assert position.status == PositionStatus.CLOSED
        assert position.closed_at is not None

    @pytest.mark.asyncio
    async def test_get_user_positions(self, position_repository, sample_position_data):
        """Test getting all positions for a user."""
        # Create multiple positions for the same user
        position1 = await position_repository.create_position(sample_position_data)

        position2_data = PositionCreate(
            user_id=sample_position_data.user_id,
            platform=sample_position_data.platform,
            symbol="ETHUSDT",
            type=PositionType.SHORT,
            entry_price=2000.0,
            take_profit=1800.0,
            stop_loss=2200.0,
        )
        position2 = await position_repository.create_position(position2_data)

        # Create a position for a different user
        different_user_data = PositionCreate(
            user_id="987654321",
            platform=sample_position_data.platform,
            symbol="SOLUSDT",
            type=PositionType.LONG,
            entry_price=100.0,
        )
        await position_repository.create_position(different_user_data)

        # Get positions for our test user
        positions = await position_repository.get_user_positions(
            sample_position_data.user_id, sample_position_data.platform
        )

        # Verify we got the correct positions
        assert len(positions) == 2
        position_ids = {str(p.id) for p in positions}
        assert str(position1.id) in position_ids
        assert str(position2.id) in position_ids

        # Stop one position
        await position_repository.stop_position(position1.id)

        # Get active positions
        active_positions = await position_repository.get_user_active_positions(
            sample_position_data.user_id, sample_position_data.platform
        )

        # Verify we only get the active position
        assert len(active_positions) == 1
        assert active_positions[0].id == position2.id
