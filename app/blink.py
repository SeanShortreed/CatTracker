from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from .models import BlinkClip

DATA_DIR = Path(__file__).resolve().parent / "data"
CLIPS_FILE = DATA_DIR / "blink_clips.json"


def _load_clip_payload() -> Iterable[dict]:
    if not CLIPS_FILE.exists():
        return []
    return json.loads(CLIPS_FILE.read_text(encoding="utf-8"))


def load_clips() -> List[BlinkClip]:
    validate = BlinkClip.model_validate if hasattr(BlinkClip, "model_validate") else BlinkClip.parse_obj  # type: ignore[attr-defined]
    return [validate(payload) for payload in _load_clip_payload()]


def get_clip_by_id(clip_id: str) -> Optional[BlinkClip]:
    for clip in load_clips():
        if clip.id == clip_id:
            return clip
    return None


def find_closest_clip(timestamp: datetime, window_seconds: int = 300) -> Optional[BlinkClip]:
    """Return the closest clip to ``timestamp`` within ``window_seconds``."""

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    clips = load_clips()
    closest: Optional[BlinkClip] = None
    closest_delta: Optional[timedelta] = None
    for clip in clips:
        clip_ts = clip.timestamp
        if clip_ts.tzinfo is None:
            clip_ts = clip_ts.replace(tzinfo=timezone.utc)
        delta = abs(clip_ts - timestamp)
        if closest_delta is None or delta < closest_delta:
            closest = clip
            closest_delta = delta
    if closest is None:
        return None
    if closest_delta is not None and closest_delta > timedelta(seconds=window_seconds):
        return None
    return closest
