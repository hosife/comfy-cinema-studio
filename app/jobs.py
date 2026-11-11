"""Shots: one submitted render each, tracked from submit to downloaded media.

State lives in memory and in ``<OUTPUT_DIR>/shots.json`` so a restart keeps the
board. A background thread polls the backend for running shots and downloads
their outputs into ``<OUTPUT_DIR>/shots/<shot_id>/``.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .comfy_client import ComfyClient, ComfyError, extract_outputs, record_status

log = logging.getLogger(__name__)

POLL_SECONDS = 2.0  # how often the loop wakes
STATUS_EVERY = 5.0  # how often one running shot is asked about
BACKOFF_SECONDS = 15.0  # after a 429 from the backend, unless it says otherwise


@dataclass
class Shot:
    id: str
    recipe: str
    title: str
    inputs: dict[str, Any]
    prompt_id: str
    created_at: float
    state: str = "running"  # running | done | failed
    message: str = ""
    finished_at: float | None = None
    media: list[dict] = field(default_factory=list)  # {kind, filename, path, url}

    def to_public(self) -> dict:
        data = asdict(self)
        data["elapsed"] = round((self.finished_at or time.time()) - self.created_at, 1)
        data["media"] = [
            {"kind": m["kind"], "filename": m["filename"], "url": m["url"]} for m in self.media
        ]
        return data


class ShotStore:
    def __init__(self, client: ComfyClient, output_dir: Path):
        self._client = client
        self._dir = output_dir
        self._shots_dir = output_dir / "shots"
        self._state_file = output_dir / "shots.json"
        self._shots: dict[str, Shot] = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._next_poll: dict[str, float] = {}  # shot id -> earliest time to ask again
        self._load()

    # ----- persistence ---------------------------------------------------

    def _load(self) -> None:
        if not self._state_file.is_file():
            return
        try:
            raw = json.loads(self._state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            log.warning("could not read %s: %s", self._state_file, exc)
            return
        for item in raw.get("shots", []):
            try:
                shot = Shot(**item)
            except TypeError:
                continue
            self._shots[shot.id] = shot

    def _save(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        payload = {"shots": [asdict(s) for s in self._shots.values()]}
        tmp = self._state_file.with_name("shots.json.tmp")
        tmp.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        tmp.replace(self._state_file)

    # ----- API -----------------------------------------------------------

    def list(self) -> list[Shot]:
        with self._lock:
            return sorted(self._shots.values(), key=lambda s: s.created_at, reverse=True)

    def get(self, shot_id: str) -> Shot | None:
        with self._lock:
            return self._shots.get(shot_id)

    def media_path(self, shot_id: str, filename: str) -> Path | None:
        shot = self.get(shot_id)
        if not shot:
            return None
        for m in shot.media:
            if m["filename"] == filename:
                return Path(m["path"])
        return None

    def submit(self, recipe_name: str, title: str, graph: dict, inputs: dict[str, Any]) -> Shot:
        prompt_id = self._client.submit(graph)
        shot = Shot(
            id=uuid.uuid4().hex[:12],
            recipe=recipe_name,
            title=title,
            inputs=inputs,
            prompt_id=prompt_id,
            created_at=time.time(),
        )
        with self._lock:
            self._shots[shot.id] = shot
            self._save()
        return shot

    def refetch(self, shot_id: str) -> Shot | None:
        """Ask the poller to read the backend record again and download outputs afresh."""
        with self._lock:
            shot = self._shots.get(shot_id)
            if shot is None:
                return None
            shot.state = "running"
            shot.message = ""
            shot.media = []  # finished_at is kept so the render time stays truthful
            self._save()
        return shot

    def delete(self, shot_id: str) -> bool:
        with self._lock:
            shot = self._shots.pop(shot_id, None)
            if shot is None:
                return False
            self._save()
        return True

    # ----- polling -------------------------------------------------------

    def start(self) -> None:
        if self._thread is None:
            self._thread = threading.Thread(target=self._loop, name="shot-poller", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._poll_once()
            except Exception:  # noqa: BLE001 - the poller must survive anything
                log.exception("poll failed")
            self._stop.wait(POLL_SECONDS)

    def _poll_once(self) -> None:
        running = [s for s in self.list() if s.state == "running"]
        now = time.time()
        for shot in running:
            if now < self._next_poll.get(shot.id, 0.0):
                continue
            self._next_poll[shot.id] = now + STATUS_EVERY
            try:
                record = self._client.history(shot.prompt_id)
            except ComfyError as exc:
                if exc.status in (429, 503):
                    delay = exc.retry_after or BACKOFF_SECONDS
                    self._next_poll[shot.id] = now + delay
                    log.info("backend asked to slow down; asking about %s again in %.0fs", shot.id, delay)
                else:
                    log.warning("history for %s failed: %s", shot.prompt_id, exc)
                continue
            state, message = record_status(record)
            if state == "running":
                continue
            if state == "failed":
                self._finish(shot, "failed", message)
                continue
            media = []
            for out in extract_outputs(record or {}):
                dest = self._shots_dir / shot.id / out["filename"]
                try:
                    self._client.download(out["filename"], out["subfolder"], out["type"], dest)
                except ComfyError as exc:
                    self._finish(shot, "failed", f"download failed: {exc}")
                    break
                media.append(
                    {
                        "kind": out["kind"],
                        "filename": out["filename"],
                        "path": str(dest),
                        "url": f"/api/shots/{shot.id}/media/{out['filename']}",
                    }
                )
            else:
                shot.media = media
                self._finish(shot, "done", "" if media else "finished without media outputs")

    def _finish(self, shot: Shot, state: str, message: str) -> None:
        self._next_poll.pop(shot.id, None)
        with self._lock:
            shot.state = state
            shot.message = message
            if shot.finished_at is None:
                shot.finished_at = time.time()
            self._save()
        log.info("shot %s %s %s", shot.id, state, message)
