"""Utility functions for managing positions from Discord and Telegram bots."""

import logging
from typing import Any, Dict, Optional

from src.positions.models import (
    Position,
    PositionCreate,
    PositionStatus,
    PositionType,
    PlatformType,
)
from src.positions.service import PositionService

logger = logging.getLogger(__name__)

position_service = PositionService()

# Helper functions for interacting with positions


async def create_position_from_chart_data(
    user_id: str, platform: PlatformType, chart_data: Dict[str, Any]
) -> Optional[Position]:
    """Create a position from chart data extracted from an image."""
    try:
        # Extract relevant data from chart_data
        symbol = chart_data.get("symbol", "UNKNOWN")
        entry_price = float(chart_data.get("entry", 0))
        take_profit = chart_data.get("take_profit")
        stop_loss = chart_data.get("stop_loss")
        position_type = chart_data.get("position_type", "long").lower()

        # Convert take_profit and stop_loss to float if they exist
        if take_profit:
            take_profit = float(take_profit)
        if stop_loss:
            stop_loss = float(stop_loss)

        # Create position data
        position_data = PositionCreate(
            user_id=user_id,
            platform=platform,
            symbol=symbol,
            type=PositionType.LONG if position_type == "long" else PositionType.SHORT,
            entry_price=entry_price,
            take_profit=take_profit,
            stop_loss=stop_loss,
            metadata=chart_data,  # Store the original chart data
        )

        # Create the position
        position = await position_service.create_position(position_data)
        logger.info(f"Created position {position.id} for user {user_id} on {platform}")
        return position
    except Exception as e:
        logger.error(f"Error creating position: {e}")
        return None


async def list_user_positions(user_id: str, platform: PlatformType) -> str:
    """Get a formatted list of user positions."""
    try:
        positions = await position_service.get_user_active_positions(user_id, platform)

        if not positions:
            return "You don't have any active positions."

        result = "📊 Your active positions:\n\n"

        for i, pos in enumerate(positions, 1):
            profit_target = f"TP: {pos.take_profit}" if pos.take_profit else "No take profit set"
            stop = f"SL: {pos.stop_loss}" if pos.stop_loss else "No stop loss set"

            result += (
                f"{i}. {pos.symbol} ({pos.type.value.upper()})\n"
                f"   Entry: {pos.entry_price}\n"
                f"   {profit_target}\n"
                f"   {stop}\n"
                f"   ID: {pos.id}\n\n"
            )

        result += "Use /position <id> to see more details about a specific position."
        return result
    except Exception as e:
        logger.error(f"Error listing positions: {e}")
        return "Error getting positions. Please try again later."


async def get_position_details(position_id: str) -> str:
    """Get detailed information about a position."""
    try:
        position = await position_service.get_position(position_id)

        if not position:
            return "Position not found."

        # Calculate current duration
        from datetime import datetime

        duration = datetime.utcnow() - position.created_at
        days = duration.days
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        result = (
            f"📈 Position Details: {position.symbol} ({position.type.value.upper()})\n\n"
            f"Entry Price: {position.entry_price}\n"
        )

        if position.take_profit:
            result += f"Take Profit: {position.take_profit}\n"

        if position.stop_loss:
            result += f"Stop Loss: {position.stop_loss}\n"

        if position.quantity:
            result += f"Quantity: {position.quantity}\n"

        if position.leverage:
            result += f"Leverage: {position.leverage}x\n"

        result += (
            f"Status: {position.status.value.capitalize()}\n"
            f"Created: {position.created_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Duration: {days}d {hours}h {minutes}m\n"
        )

        if position.notes:
            result += f"\nNotes: {position.notes}\n"

        result += f"\nID: {position.id}"

        return result
    except Exception as e:
        logger.error(f"Error getting position details: {e}")
        return "Error getting position details. Please try again later."


async def close_user_position(position_id: str, user_id: str, platform: PlatformType) -> str:
    """Close a user's position."""
    try:
        position = await position_service.get_position(position_id)

        if not position:
            return "Position not found."

        # Verify the position belongs to the user
        if position.user_id != user_id or position.platform != platform:
            return "This position doesn't belong to you."

        # Check if position is already closed
        if position.status != PositionStatus.ACTIVE:
            return f"This position is already {position.status.value}."

        # Close the position
        closed_position = await position_service.close_position(position_id)

        return f"Position {closed_position.symbol} successfully closed."
    except Exception as e:
        logger.error(f"Error closing position: {e}")
        return "Error closing position. Please try again later."


async def update_user_position(
    position_id: str, user_id: str, platform: PlatformType, update_data: Dict[str, Any]
) -> str:
    """Update a user's position."""
    try:
        position = await position_service.get_position(position_id)

        if not position:
            return "Position not found."

        # Verify the position belongs to the user
        if position.user_id != user_id or position.platform != platform:
            return "This position doesn't belong to you."

        # Check if position is already closed
        if position.status != PositionStatus.ACTIVE:
            return f"Cannot update a {position.status.value} position."

        # Update the position
        updated_position = await position_service.update_position(position_id, update_data)

        return f"Position {updated_position.symbol} successfully updated."
    except Exception as e:
        logger.error(f"Error updating position: {e}")
        return "Error updating position. Please try again later."


async def stop_user_position(position_id: str, user_id: str, platform: PlatformType) -> str:
    """Stop (soft-delete) a user's position."""
    try:
        position = await position_service.get_position(position_id)

        if not position:
            return "Position not found."

        # Verify the position belongs to the user
        if position.user_id != user_id or position.platform != platform:
            return "This position doesn't belong to you."

        # Check if position is already stopped
        if position.status == PositionStatus.STOPPED:
            return "This position is already stopped."

        # Stop the position
        stopped_position = await position_service.stop_position(position_id)

        return f"Position {stopped_position.symbol} successfully stopped."
    except Exception as e:
        logger.error(f"Error stopping position: {e}")
        return "Error stopping position. Please try again later."


async def get_user_positions_summary(user_id: str, platform: PlatformType) -> str:
    """Get a summary of user positions."""
    try:
        summary = await position_service.get_positions_summary(user_id, platform)

        result = (
            f"📊 Positions Summary\n\n"
            f"Total Positions: {summary['total']}\n"
            f"Active Positions: {summary['active']}\n"
            f"Closed Positions: {summary['closed']}\n"
            f"Stopped Positions: {summary['stopped']}\n\n"
            f"Use /positions to see your active positions."
        )

        return result
    except Exception as e:
        logger.error(f"Error getting positions summary: {e}")
        return "Error getting positions summary. Please try again later."
