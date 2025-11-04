from __future__ import annotations

import json
import threading
from datetime import timezone
from pathlib import Path
from typing import Iterable, List

from .models import Event

DATA_DIR = Path(__file__).resolve().parent / "data"
EVENTS_FILE = DATA_DIR / "events.json"

_LOCK = threading.Lock()


def _ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not EVENTS_FILE.exists():
        EVENTS_FILE.write_text("[]", encoding="utf-8")


def _event_to_dict(event: Event) -> dict:
    serializer = event.model_dump if hasattr(event, "model_dump") else event.dict  # type: ignore[attr-defined]
    data = serializer()
    timestamp = event.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    data["timestamp"] = timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return data


def _copy_event(event: Event, **updates) -> Event:
    if hasattr(event, "model_copy"):
        return event.model_copy(update=updates)  # type: ignore[attr-defined]
    data = event.dict()
    data.update(updates)
    return Event(**data)


def load_events() -> List[Event]:
    _ensure_storage()
    raw = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
    validate = Event.model_validate if hasattr(Event, "model_validate") else Event.parse_obj  # type: ignore[attr-defined]
    return [validate(item) for item in raw]


def save_events(events: Iterable[Event]) -> None:
    _ensure_storage()
    payload = [_event_to_dict(event) for event in events]
    EVENTS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def update_event_cat(event_id: int, cat_id: str) -> Event:
    """Persist a cat assignment update and return the updated event."""

    with _LOCK:
        events = load_events()
        for idx, event in enumerate(events):
            if event.id == event_id:
                updated_event = _copy_event(event, cat_id=cat_id)
                events[idx] = updated_event
                save_events(events)
                return updated_event
        raise KeyError(f"Event {event_id} not found")
