import logging
from typing import Dict, List, Optional, Union
from uuid import UUID

from src.positions.models import (
    Position,
    PositionCreate,
    PositionStatus,
    PositionUpdate,
    PlatformType,
)
from src.positions.repository import PositionRepository

logger = logging.getLogger(__name__)


class PositionService:
    """Service for managing positions."""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PositionService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, repository: Optional[PositionRepository] = None):
        if self._initialized:
            return

        self.repository = repository or PositionRepository()
        self._initialized = True

    async def create_position(self, data: Union[Dict, PositionCreate]) -> Position:
        """Create a new position."""
        if isinstance(data, dict):
            position_data = PositionCreate(**data)
        else:
            position_data = data

        return await self.repository.create_position(position_data)

    async def get_position(self, position_id: Union[UUID, str]) -> Optional[Position]:
        """Get a position by ID."""
        return await self.repository.get_position(position_id)

    async def update_position(
        self, position_id: Union[UUID, str], data: Union[Dict, PositionUpdate]
    ) -> Optional[Position]:
        """Update a position."""
        if isinstance(data, dict):
            update_data = PositionUpdate(**data)
        else:
            update_data = data

        return await self.repository.update_position(position_id, update_data)

    async def stop_position(self, position_id: Union[UUID, str]) -> Optional[Position]:
        """Stop a position (soft-delete)."""
        return await self.repository.stop_position(position_id)

    async def close_position(self, position_id: Union[UUID, str], **kwargs) -> Optional[Position]:
        """Close a position."""
        return await self.repository.close_position(position_id, **kwargs)

    async def delete_position(self, position_id: Union[UUID, str]) -> bool:
        """Delete a position permanently."""
        return await self.repository.delete_position(position_id)

    async def get_user_positions(
        self, user_id: str, platform: PlatformType, include_stopped: bool = False
    ) -> List[Position]:
        """Get all positions for a user."""
        return await self.repository.get_user_positions(user_id, platform, include_stopped)

    async def get_user_active_positions(
        self, user_id: str, platform: PlatformType
    ) -> List[Position]:
        """Get active positions for a user."""
        return await self.repository.get_user_active_positions(user_id, platform)

    async def get_position_by_symbol_for_user(
        self,
        user_id: str,
        platform: PlatformType,
        symbol: str,
        status: PositionStatus = PositionStatus.ACTIVE,
    ) -> Optional[Position]:
        """Get a position for a user by symbol and status."""
        positions = await self.get_user_positions(user_id, platform)

        for position in positions:
            if position.symbol.upper() == symbol.upper() and position.status == status:
                return position

        return None

    async def get_positions_summary(self, user_id: str, platform: PlatformType) -> Dict:
        """Get a summary of positions for a user."""
        positions = await self.get_user_positions(user_id, platform, include_stopped=True)

        active_count = sum(1 for p in positions if p.status == PositionStatus.ACTIVE)
        closed_count = sum(1 for p in positions if p.status == PositionStatus.CLOSED)
        stopped_count = sum(1 for p in positions if p.status == PositionStatus.STOPPED)

        return {
            "total": len(positions),
            "active": active_count,
            "closed": closed_count,
            "stopped": stopped_count,
        }
