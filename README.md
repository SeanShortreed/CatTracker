# Cat Tracker

A lightweight FastAPI + vanilla JavaScript prototype for reviewing litter-robot
activity events alongside Blink camera clips. The application exposes a REST API
and a small dashboard for verifying which cat triggered an activity and for
persisting corrections.

## Features

- JSON-backed storage for litter-robot events with timestamps and tentative cat
  assignments.
- Mock Blink integration that loads clip metadata and resolves the clip closest
  to each event.
- REST endpoints to list events, retrieve the nearest clip for a specific event,
  and update the cat assigned to an activity.
- Simple web UI that lists events, displays clip thumbnails/links, and provides
  a dropdown to reassign the cat with inline persistence feedback.

## Getting started

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Start the development server:

   ```bash
   uvicorn app.main:app --reload
   ```

3. Open <http://127.0.0.1:8000/> to use the dashboard. The API is rooted at
   <http://127.0.0.1:8000/api/>.

## API overview

- `GET /api/events` – list all events enriched with the closest Blink clip
  (thumbnail, link, camera, etc.).
- `GET /api/events/{event_id}/clip?window_seconds=300` – retrieve the clip
  closest to a given event within the specified window.
- `PATCH /api/events/{event_id}` – update the `cat_id` for the event and persist
  it back to JSON storage.

All updates are stored in `app/data/events.json`, keeping corrections across
server restarts.

## Testing

Run the lightweight regression tests to confirm the API endpoints and JSON
persistence work as expected:

```bash
python -m unittest
```
