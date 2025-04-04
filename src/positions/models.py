from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class PlatformType(str, Enum):
    """Types of supported platforms."""

    DISCORD = "discord"
    TELEGRAM = "telegram"


class PositionStatus(str, Enum):
    """Status of a trading position."""

    ACTIVE = "active"
    CLOSED = "closed"
    STOPPED = "stopped"  # Soft-deleted


class PositionType(str, Enum):
    """Types of positions."""

    LONG = "long"
    SHORT = "short"


class Position(BaseModel):
    """Model representing a trading position."""

    model_config = ConfigDict(json_encoders={UUID: str, datetime: lambda dt: dt.isoformat()})

    id: UUID = Field(default_factory=uuid4)
    user_id: str  # Either discord_id or telegram_id
    platform: PlatformType
    symbol: str
    type: PositionType
    entry_price: float
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    quantity: Optional[float] = None
    leverage: Optional[float] = None
    status: PositionStatus = PositionStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)

    def update(self, **kwargs) -> None:
        """Update the position with the given values and update the updated_at timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self.updated_at = datetime.utcnow()

        # Set closed_at if status is changed to CLOSED
        if self.status == PositionStatus.CLOSED and not self.closed_at:
            self.closed_at = datetime.utcnow()

    def close(self, **kwargs) -> None:
        """Close the position."""
        self.status = PositionStatus.CLOSED
        self.closed_at = datetime.utcnow()
        self.update(**kwargs)

    def stop(self) -> None:
        """Soft-delete the position."""
        self.status = PositionStatus.STOPPED
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert the position to a dictionary."""
        return self.model_dump(mode="json")


class PositionCreate(BaseModel):
    """Model for creating a new position."""

    user_id: str
    platform: PlatformType
    symbol: str
    type: PositionType
    entry_price: float
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    quantity: Optional[float] = None
    leverage: Optional[float] = None
    notes: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)


class PositionUpdate(BaseModel):
    """Model for updating an existing position."""

    symbol: Optional[str] = None
    type: Optional[PositionType] = None
    entry_price: Optional[float] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    quantity: Optional[float] = None
    leverage: Optional[float] = None
    status: Optional[PositionStatus] = None
    notes: Optional[str] = None
    metadata: Optional[Dict] = None
