"""FastAPI application: a one-page shot studio in front of any ComfyUI backend."""

from __future__ import annotations

import logging
import re
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .comfy_client import ComfyClient, ComfyError
from .config import Settings, load_settings
from .jobs import ShotStore
from .recipes import Recipe, RecipeError, load_recipes

log = logging.getLogger("app")

STATIC_DIR = Path(__file__).resolve().parent / "static"
ALLOWED_UPLOADS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_UPLOAD_BYTES = 40 * 1024 * 1024


class ShotRequest(BaseModel):
    recipe: str
    title: str = ""
    inputs: dict[str, Any] = Field(default_factory=dict)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    client = ComfyClient(settings.comfyui_url, api_key=settings.api_key, auth_token=settings.auth_token)
    recipes: dict[str, Recipe] = load_recipes(settings.workflows_dir)
    store = ShotStore(client, settings.output_dir)
    uploads_dir = settings.output_dir / "uploads"

    app = FastAPI(title="comfy-cinema-studio", version="0.1.0")
    app.state.settings = settings
    app.state.client = client
    app.state.store = store

    @app.on_event("startup")
    def _startup() -> None:
        store.start()
        log.info("backend %s at %s, %d recipes", settings.backend_label, settings.comfyui_url, len(recipes))

    @app.on_event("shutdown")
    def _shutdown() -> None:
        store.stop()
        client.close()

    # ----- info -----------------------------------------------------------

    @app.get("/api/backend")
    def backend() -> dict:
        info: dict[str, Any] = {
            "label": settings.backend_label,
            "url": settings.comfyui_url,
            "authenticated": bool(settings.api_key or settings.auth_token),
            "reachable": False,
            "version": None,
            "queue_running": None,
            "queue_pending": None,
            "error": None,
        }
        try:
            stats = client.system_stats()
            info["reachable"] = True
            system = stats.get("system") or {}
            info["version"] = system.get("comfyui_version") or system.get("cloud_version")
            queue = client.queue()
            info["queue_running"] = len(queue.get("queue_running") or [])
            info["queue_pending"] = len(queue.get("queue_pending") or [])
        except ComfyError as exc:
            info["error"] = str(exc)
        return info

    @app.get("/api/recipes")
    def list_recipes() -> list[dict]:
        return [r.to_public() for r in recipes.values()]

    # ----- uploads --------------------------------------------------------

    @app.post("/api/uploads")
    async def upload(file: UploadFile = File(...)) -> dict:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in ALLOWED_UPLOADS:
            raise HTTPException(400, f"unsupported image type {suffix or '(none)'}; use PNG, JPG or WebP")
        data = await file.read()
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "image larger than 40 MB")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        local = uploads_dir / f"{uuid.uuid4().hex[:12]}{suffix}"
        local.write_bytes(data)
        try:
            record = client.upload_image(local)
        except ComfyError as exc:
            raise HTTPException(502, f"backend refused the upload: {exc}") from exc
        return {
            "name": record["name"],
            "subfolder": record.get("subfolder", ""),
            "original": file.filename,
            "local": local.name,
            "preview_url": f"/api/uploads/{local.name}",
        }

    @app.get("/api/uploads/{name}")
    def upload_preview(name: str) -> FileResponse:
        if not re.fullmatch(r"[0-9a-f]{12}\.[a-z]+", name):
            raise HTTPException(404)
        path = uploads_dir / name
        if not path.is_file():
            raise HTTPException(404)
        return FileResponse(path)

    # ----- shots ----------------------------------------------------------

    @app.post("/api/shots")
    def create_shot(req: ShotRequest) -> dict:
        recipe = recipes.get(req.recipe)
        if recipe is None:
            raise HTTPException(404, f"no recipe named {req.recipe}")
        try:
            graph, resolved = recipe.build(req.inputs)
        except RecipeError as exc:
            raise HTTPException(400, str(exc)) from exc
        title = req.title.strip() or _title_from(resolved)
        try:
            shot = store.submit(recipe.name, title, graph, resolved)
        except ComfyError as exc:
            detail = exc.body[:500] if exc.body else str(exc)
            raise HTTPException(502, f"backend refused the shot: {detail}") from exc
        return shot.to_public()

    @app.get("/api/shots")
    def list_shots() -> list[dict]:
        return [s.to_public() for s in store.list()]

    @app.get("/api/shots/{shot_id}")
    def get_shot(shot_id: str) -> dict:
        shot = store.get(shot_id)
        if shot is None:
            raise HTTPException(404)
        return shot.to_public()

    @app.post("/api/shots/{shot_id}/refetch")
    def refetch_shot(shot_id: str) -> dict:
        shot = store.refetch(shot_id)
        if shot is None:
            raise HTTPException(404)
        return shot.to_public()

    @app.delete("/api/shots/{shot_id}")
    def delete_shot(shot_id: str) -> JSONResponse:
        if not store.delete(shot_id):
            raise HTTPException(404)
        return JSONResponse({"deleted": shot_id})

    @app.get("/api/shots/{shot_id}/media/{filename}")
    def shot_media(shot_id: str, filename: str) -> FileResponse:
        path = store.media_path(shot_id, filename)
        if path is None or not path.is_file():
            raise HTTPException(404)
        return FileResponse(path)

    # ----- page -----------------------------------------------------------

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


def _title_from(inputs: dict[str, Any]) -> str:
    prompt = str(inputs.get("prompt") or "").strip()
    words = re.sub(r"\s+", " ", prompt).split(" ")
    short = " ".join(words[:7])
    return short or time.strftime("Shot %H:%M:%S")
