from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BlinkClip(BaseModel):
    """Metadata for a Blink camera clip."""

    id: str
    timestamp: datetime
    camera: str
    duration_seconds: int
    thumbnail_url: str
    video_url: str


class Event(BaseModel):
    """Litter-robot activity event."""

    id: int
    timestamp: datetime
    cat_id: str = Field(default="Unknown", description="Tentative or confirmed cat identifier")
    blink_clip_id: Optional[str] = Field(
        default=None, description="Identifier of the Blink clip most closely associated with the event"
    )


class EventWithClip(Event):
    clip: Optional[BlinkClip] = None


class CatUpdate(BaseModel):
    cat_id: str = Field(..., min_length=1, description="Updated cat identifier for the event")
