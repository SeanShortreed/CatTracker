import importlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import List

try:  # pragma: no cover - exercised through unit tests
    from fastapi.testclient import TestClient as FastAPITestClient
except Exception:  # pragma: no cover - FastAPI always available in the app runtime
    FastAPITestClient = None

from app import storage
from app.main import app


class TempEventStorage:
    """Context manager that redirects event storage to a temporary file."""

    def __init__(self) -> None:
        self._temp_dir = Path(tempfile.mkdtemp())
        self.events_file = self._temp_dir / "events.json"
        self._original_data_dir = storage.DATA_DIR
        self._original_events_file = storage.EVENTS_FILE

    def __enter__(self) -> "TempEventStorage":
        storage.DATA_DIR = self._temp_dir
        storage.EVENTS_FILE = self.events_file
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        storage.DATA_DIR = self._original_data_dir
        storage.EVENTS_FILE = self._original_events_file
        shutil.rmtree(self._temp_dir)

    def write_events(self, payload: List[dict]) -> None:
        self.events_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class TestEventApi(unittest.TestCase):
    def setUp(self) -> None:
        self._storage_ctx = TempEventStorage()
        self.storage = self._storage_ctx.__enter__()

    def tearDown(self) -> None:
        self._storage_ctx.__exit__(None, None, None)

    def test_list_events_includes_clips(self) -> None:
        seed_events = [
            {"id": 1, "timestamp": "2024-03-19T08:15:00Z", "cat_id": "Mittens", "blink_clip_id": None},
            {"id": 2, "timestamp": "2024-03-19T12:42:30Z", "cat_id": "Shadow", "blink_clip_id": None},
            {"id": 3, "timestamp": "2024-03-19T21:05:12Z", "cat_id": "Unknown", "blink_clip_id": None},
        ]
        self.storage.write_events(seed_events)

        with create_test_client(app) as client:
            response = client.get("/api/events")

        self.assertEqual(response.status_code, 200)
        events = response.json()
        self.assertEqual(len(events), 3)
        self.assertTrue(all(event["clip"] for event in events))
        self.assertEqual(events[0]["clip"]["id"], "clip-101")

    def test_update_event_cat_persists_to_disk(self) -> None:
        seed_events = [
            {"id": 1, "timestamp": "2024-03-19T08:15:00Z", "cat_id": "Mittens", "blink_clip_id": None},
            {"id": 2, "timestamp": "2024-03-19T12:42:30Z", "cat_id": "Shadow", "blink_clip_id": None},
        ]
        self.storage.write_events(seed_events)

        with create_test_client(app) as client:
            response = client.patch("/api/events/2", json={"cat_id": "Pumpkin"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["cat_id"], "Pumpkin")

        written = json.loads(self.storage.events_file.read_text(encoding="utf-8"))
        self.assertEqual(written[1]["cat_id"], "Pumpkin")


def create_test_client(app_instance):
    """Return a test client compatible with multiple httpx versions."""

    if FastAPITestClient is not None:
        try:
            return FastAPITestClient(app_instance)
        except TypeError:
            # httpx 0.28 removed the ``app`` keyword argument, which breaks the
            # Starlette/FastAPI TestClient. In that case, fall back to an httpx
            # client powered by ASGITransport so the tests remain runnable
            # without requiring a global dependency downgrade.
            pass

    httpx = importlib.import_module("httpx")
    transport = httpx.ASGITransport(app=app_instance)
    return httpx.Client(transport=transport, base_url="http://testserver")


if __name__ == "__main__":
    unittest.main()
