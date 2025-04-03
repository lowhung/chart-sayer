from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from src.positions.models import (
    Position,
    PositionCreate,
    PositionStatus,
    PositionUpdate,
    PlatformType,
)
from src.positions.service import PositionService

router = APIRouter(prefix="/positions", tags=["positions"])


async def get_position_service() -> PositionService:
    """Dependency to get the position service."""
    return PositionService()


@router.post("/", response_model=Position, status_code=201)
async def create_position(
    position: PositionCreate,
    service: PositionService = Depends(get_position_service),
):
    """Create a new position."""
    return await service.create_position(position)


@router.get("/{position_id}", response_model=Position)
async def get_position(
    position_id: UUID = Path(..., title="The ID of the position to get"),
    service: PositionService = Depends(get_position_service),
):
    """Get a position by ID."""
    position = await service.get_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.patch("/{position_id}", response_model=Position)
async def update_position(
    position_update: PositionUpdate,
    position_id: UUID = Path(..., title="The ID of the position to update"),
    service: PositionService = Depends(get_position_service),
):
    """Update a position."""
    position = await service.update_position(position_id, position_update)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.delete("/{position_id}", response_model=Position)
async def stop_position(
    position_id: UUID = Path(..., title="The ID of the position to stop"),
    service: PositionService = Depends(get_position_service),
):
    """Stop a position (soft-delete)."""
    position = await service.stop_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.post("/{position_id}/close", response_model=Position)
async def close_position(
    position_id: UUID = Path(..., title="The ID of the position to close"),
    service: PositionService = Depends(get_position_service),
):
    """Close a position."""
    position = await service.close_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.get("/user/{platform}/{user_id}", response_model=List[Position])
async def get_user_positions(
    user_id: str = Path(..., title="The ID of the user"),
    platform: PlatformType = Path(..., title="The platform type"),
    include_stopped: bool = Query(False, title="Include stopped positions"),
    service: PositionService = Depends(get_position_service),
):
    """Get all positions for a user."""
    return await service.get_user_positions(user_id, platform, include_stopped)


@router.get("/user/{platform}/{user_id}/active", response_model=List[Position])
async def get_user_active_positions(
    user_id: str = Path(..., title="The ID of the user"),
    platform: PlatformType = Path(..., title="The platform type"),
    service: PositionService = Depends(get_position_service),
):
    """Get active positions for a user."""
    return await service.get_user_active_positions(user_id, platform)


@router.get("/user/{platform}/{user_id}/summary")
async def get_user_positions_summary(
    user_id: str = Path(..., title="The ID of the user"),
    platform: PlatformType = Path(..., title="The platform type"),
    service: PositionService = Depends(get_position_service),
):
    """Get a summary of positions for a user."""
    return await service.get_positions_summary(user_id, platform)
