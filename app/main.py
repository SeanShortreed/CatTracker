from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import blink, storage
from .models import BlinkClip, CatUpdate, Event, EventWithClip

app = FastAPI(title="Cat Tracker", description="Track litter-robot events with Blink clips")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _serialize_event(event: Event) -> EventWithClip:
    clip: BlinkClip | None = None
    if event.blink_clip_id:
        clip = blink.get_clip_by_id(event.blink_clip_id)
    if clip is None:
        clip = blink.find_closest_clip(event.timestamp)
    payload = event.model_dump() if hasattr(event, "model_dump") else event.dict()
    payload["clip"] = clip
    validator = EventWithClip.model_validate if hasattr(EventWithClip, "model_validate") else EventWithClip.parse_obj  # type: ignore[attr-defined]
    return validator(payload)


def _get_event(event_id: int) -> Event:
    for event in storage.load_events():
        if event.id == event_id:
            return event
    raise HTTPException(status_code=404, detail=f"Event {event_id} not found")


@app.get("/api/events", response_model=List[EventWithClip])
async def list_events() -> List[EventWithClip]:
    events = storage.load_events()
    return [_serialize_event(event) for event in events]


@app.get("/api/events/{event_id}/clip", response_model=BlinkClip)
async def get_event_clip(event_id: int, window_seconds: int = 300) -> BlinkClip:
    event = _get_event(event_id)
    clip: BlinkClip | None = None
    if event.blink_clip_id:
        clip = blink.get_clip_by_id(event.blink_clip_id)
    if clip is None:
        clip = blink.find_closest_clip(event.timestamp, window_seconds=window_seconds)
    if clip is None:
        raise HTTPException(status_code=404, detail="No clip found within the specified window")
    return clip


@app.patch("/api/events/{event_id}", response_model=EventWithClip)
async def update_cat(event_id: int, payload: CatUpdate) -> EventWithClip:
    try:
        updated_event = storage.update_event_cat(event_id, payload.cat_id)
    except KeyError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _serialize_event(updated_event)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})
