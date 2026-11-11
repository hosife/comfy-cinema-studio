"""A small client for ComfyUI's HTTP API.

Works against a local ComfyUI (``http://host:8188``) and against Comfy Cloud
(``https://cloud.comfy.org/api``). The only differences are the base URL, the
optional credential header and the name of the history endpoint, which the
client discovers on first use.

Endpoints used: ``/prompt``, ``/history/<id>`` (or ``/history_v2/<id>``),
``/view``, ``/upload/image``, ``/system_stats``, ``/queue``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

log = logging.getLogger(__name__)


class ComfyError(RuntimeError):
    def __init__(
        self, message: str, status: int | None = None, body: str = "", retry_after: float | None = None
    ):
        super().__init__(message)
        self.status = status
        self.body = body
        self.retry_after = retry_after  # seconds, from a 429 or 503 Retry-After header


class ComfyClient:
    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        auth_token: str | None = None,
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        headers: dict[str, str] = {}
        if api_key:
            headers["X-API-Key"] = api_key
        elif auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        self._api_key = api_key
        # follow_redirects: Comfy Cloud answers /view with a redirect to signed storage.
        self._http = httpx.Client(
            base_url=self.base_url, headers=headers, timeout=timeout, follow_redirects=True
        )
        self._history_path = "history"

    # ----- helpers -------------------------------------------------------

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            resp = self._http.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise ComfyError(f"{method} {path} failed: {exc}") from exc
        if resp.status_code >= 400:
            retry_after = None
            if resp.status_code in (429, 503):
                try:
                    retry_after = float(resp.headers.get("Retry-After", ""))
                except ValueError:
                    retry_after = None
            raise ComfyError(
                f"{method} {path} returned {resp.status_code}",
                status=resp.status_code,
                body=resp.text[:2000],
                retry_after=retry_after,
            )
        return resp

    def _json(self, method: str, path: str, **kwargs: Any) -> Any:
        resp = self._request(method, path, **kwargs)
        try:
            return resp.json()
        except ValueError as exc:
            raise ComfyError(
                f"{method} {path} returned non-JSON", status=resp.status_code, body=resp.text[:500]
            ) from exc

    # ----- health --------------------------------------------------------

    def system_stats(self) -> dict:
        return self._json("GET", "/system_stats")

    def queue(self) -> dict:
        return self._json("GET", "/queue")

    # ----- uploads -------------------------------------------------------

    def upload_image(self, path: Path, *, subfolder: str = "") -> dict:
        """POST a local image to ``/upload/image``.

        Returns the server record ``{"name": ..., "subfolder": ..., "type": "input"}``.
        Comfy Cloud renames uploads to their content hash, so a LoadImage node
        must use ``name`` from this record, never the local filename.
        """
        with path.open("rb") as fh:
            files = {"image": (path.name, fh, _mime_for(path))}
            data = {"subfolder": subfolder, "type": "input", "overwrite": "true"}
            record = self._json("POST", "/upload/image", files=files, data=data)
        if not isinstance(record, dict) or "name" not in record:
            raise ComfyError("upload/image returned an unexpected body", body=str(record)[:500])
        return record

    # ----- prompts -------------------------------------------------------

    def submit(self, graph: dict, *, client_id: str | None = None) -> str:
        payload: dict[str, Any] = {"prompt": graph}
        if client_id:
            payload["client_id"] = client_id
        if self._api_key:
            # Partner API nodes read the workspace key from extra_data.
            payload["extra_data"] = {"api_key_comfy_org": self._api_key}
        body = self._json("POST", "/prompt", json=payload)
        prompt_id = body.get("prompt_id") if isinstance(body, dict) else None
        if not prompt_id:
            raise ComfyError("POST /prompt returned no prompt_id", body=str(body)[:1000])
        if isinstance(body, dict) and body.get("node_errors"):
            log.warning("node_errors on submit: %s", body["node_errors"])
        return prompt_id

    def history(self, prompt_id: str) -> dict | None:
        """Return the history record for a prompt, or None while it is not there yet."""
        try:
            body = self._json("GET", f"/{self._history_path}/{prompt_id}")
        except ComfyError as exc:
            cloud_hint = "history_v2" in (exc.body or "") or "not available on Comfy Cloud" in (exc.body or "")
            if exc.status == 404 and self._history_path == "history" and cloud_hint:
                self._history_path = "history_v2"
                return self.history(prompt_id)
            if exc.status == 404:
                return None
            raise
        if isinstance(body, dict) and prompt_id in body:
            return body[prompt_id]
        if isinstance(body, dict) and ("outputs" in body or "status" in body):
            return body
        return None

    def view_url(self, filename: str, subfolder: str = "", type_: str = "output") -> str:
        query = urlencode({"filename": filename, "subfolder": subfolder, "type": type_})
        return f"{self.base_url}/view?{query}"

    def download(self, filename: str, subfolder: str, type_: str, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        params = {"filename": filename, "subfolder": subfolder, "type": type_}
        with self._http.stream("GET", "/view", params=params) as resp:
            if resp.status_code >= 400:
                raise ComfyError(f"GET /view returned {resp.status_code}", status=resp.status_code)
            size = 0
            with tmp.open("wb") as fh:
                for chunk in resp.iter_bytes():
                    fh.write(chunk)
                    size += len(chunk)
        if size == 0:
            tmp.unlink(missing_ok=True)
            raise ComfyError(f"GET /view returned an empty body for {filename}", status=resp.status_code)
        tmp.replace(dest)
        return dest

    def close(self) -> None:
        self._http.close()


def extract_outputs(record: dict) -> list[dict]:
    """Flatten a history record to ``[{node, filename, subfolder, type, kind}]``."""
    found: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for node_id, outputs in (record.get("outputs") or {}).items():
        if not isinstance(outputs, dict):
            continue
        for key, items in outputs.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict) or "filename" not in item:
                    continue
                ident = (item.get("filename", ""), item.get("subfolder", ""), item.get("type", "output"))
                if ident in seen:
                    continue
                seen.add(ident)
                found.append(
                    {
                        "node": node_id,
                        "filename": ident[0],
                        "subfolder": ident[1],
                        "type": ident[2],
                        "kind": _kind_for(ident[0], key),
                    }
                )
    return found


def record_status(record: dict | None) -> tuple[str, str]:
    """Map a history record to ``(state, message)``; state is running, done or failed."""
    if not record:
        return "running", ""
    status = record.get("status") or {}
    if isinstance(status, dict):
        if status.get("status_str") == "error":
            return "failed", _error_message(status)
        if status.get("completed") or status.get("status_str") == "success":
            return "done", ""
    if record.get("outputs"):
        return "done", ""
    return "running", ""


def _error_message(status: dict) -> str:
    for entry in status.get("messages") or []:
        if isinstance(entry, list) and len(entry) == 2 and entry[0] == "execution_error":
            detail = entry[1] or {}
            node = detail.get("node_type") or detail.get("node_id") or ""
            msg = detail.get("exception_message") or ""
            return f"{node}: {msg}".strip(": ") or "execution error"
    return "execution error"


def _kind_for(filename: str, key: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in {".mp4", ".webm", ".mov", ".mkv"} or key in {"videos", "video", "gifs"}:
        return "video"
    if ext in {".wav", ".mp3", ".flac", ".ogg"} or key == "audio":
        return "audio"
    return "image"


def _mime_for(path: Path) -> str:
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "application/octet-stream")
