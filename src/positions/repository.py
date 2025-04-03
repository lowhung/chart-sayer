import json
import logging
from typing import Dict, List, Optional, Set, Union
from uuid import UUID

from src.positions.models import (
    Position,
    PositionCreate,
    PositionStatus,
    PositionUpdate,
    PlatformType,
)
from src.storage.redis_client import RedisClient

logger = logging.getLogger(__name__)


class PositionRepository:
    """Repository for managing positions in Redis."""
    
    def __init__(self, redis_client: Optional[RedisClient] = None, prefix: str = "position"):
        """Initialize the repository with Redis client."""
        self.redis = redis_client or RedisClient()
        self.prefix = prefix
    
    def _get_position_key(self, position_id: Union[UUID, str]) -> str:
        """Get the Redis key for a position."""
        return f"{self.prefix}:{position_id}"
    
    def _get_user_positions_key(self, user_id: str, platform: PlatformType) -> str:
        """Get the Redis key for a user's positions set."""
        return f"{self.prefix}:user:{platform}:{user_id}"
    
    async def create_position(self, position_data: PositionCreate) -> Position:
        """Create a new position."""
        position = Position(**position_data.model_dump())
        
        # Save the position
        position_key = self._get_position_key(position.id)
        await self.redis.set_json(position_key, position.model_dump(mode='json'))
        
        # Add the position to the user's positions set
        user_positions_key = self._get_user_positions_key(position.user_id, position.platform)
        await self.redis.add_to_set(user_positions_key, str(position.id))
        
        logger.info(f"Created position {position.id} for user {position.user_id} on {position.platform}")
        return position
    
    async def get_position(self, position_id: Union[UUID, str]) -> Optional[Position]:
        """Get a position by ID."""
        position_key = self._get_position_key(position_id)
        position_data = await self.redis.get_json(position_key)
        
        if not position_data:
            return None
        
        return Position(**position_data)
    
    async def update_position(
        self, position_id: Union[UUID, str], update_data: PositionUpdate
    ) -> Optional[Position]:
        """Update a position."""
        position = await self.get_position(position_id)
        
        if not position:
            return None
        
        # Update the position
        position.update(**update_data.model_dump(exclude_unset=True))
        
        # Save the updated position
        position_key = self._get_position_key(position.id)
        await self.redis.set_json(position_key, position.model_dump(mode='json'))
        
        logger.info(f"Updated position {position.id} for user {position.user_id}")
        return position
    
    async def stop_position(self, position_id: Union[UUID, str]) -> Optional[Position]:
        """Soft-delete a position (mark as stopped)."""
        position = await self.get_position(position_id)
        
        if not position:
            return None
        
        # Stop the position
        position.stop()
        
        # Save the updated position
        position_key = self._get_position_key(position.id)
        await self.redis.set_json(position_key, position.model_dump(mode='json'))
        
        logger.info(f"Stopped position {position.id} for user {position.user_id}")
        return position
    
    async def close_position(
        self, position_id: Union[UUID, str], **kwargs
    ) -> Optional[Position]:
        """Close a position."""
        position = await self.get_position(position_id)
        
        if not position:
            return None
        
        # Close the position
        position.close(**kwargs)
        
        # Save the updated position
        position_key = self._get_position_key(position.id)
        await self.redis.set_json(position_key, position.model_dump(mode='json'))
        
        logger.info(f"Closed position {position.id} for user {position.user_id}")
        return position
    
    async def delete_position(self, position_id: Union[UUID, str]) -> bool:
        """Delete a position permanently."""
        position = await self.get_position(position_id)
        
        if not position:
            return False
        
        # Delete the position
        position_key = self._get_position_key(position.id)
        await self.redis.delete(position_key)
        
        # Remove from user's positions set
        user_positions_key = self._get_user_positions_key(position.user_id, position.platform)
        await self.redis.remove_from_set(user_positions_key, str(position.id))
        
        logger.info(f"Deleted position {position.id} for user {position.user_id}")
        return True
    
    async def get_user_positions(
        self, user_id: str, platform: PlatformType, include_stopped: bool = False
    ) -> List[Position]:
        """Get all positions for a user."""
        user_positions_key = self._get_user_positions_key(user_id, platform)
        position_ids = await self.redis.get_set_members(user_positions_key)
        
        positions = []
        for position_id in position_ids:
            position = await self.get_position(position_id)
            if position and (include_stopped or position.status != PositionStatus.STOPPED):
                positions.append(position)
        
        return positions
    
    async def get_user_active_positions(
        self, user_id: str, platform: PlatformType
    ) -> List[Position]:
        """Get active positions for a user."""
        positions = await self.get_user_positions(user_id, platform)
        return [p for p in positions if p.status == PositionStatus.ACTIVE]
