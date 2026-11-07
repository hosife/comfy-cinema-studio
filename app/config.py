"""Configuration from environment variables (and an optional .env file).

Nothing here holds a secret value. Secrets come from the environment at run
time and are never written to disk by the app.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader: KEY=VALUE lines, no quoting rules, no overrides."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class Settings:
    comfyui_url: str
    api_key: str | None
    auth_token: str | None
    output_dir: Path
    workflows_dir: Path
    host: str
    port: int

    @property
    def backend_label(self) -> str:
        return "Comfy Cloud" if "cloud.comfy.org" in self.comfyui_url else "ComfyUI"


def load_settings() -> Settings:
    _load_dotenv(REPO_ROOT / ".env")
    url = os.environ.get("COMFYUI_URL", "").strip().rstrip("/")
    if not url:
        raise SystemExit(
            "COMFYUI_URL is not set. Copy .env.example to .env and fill it in: "
            "https://cloud.comfy.org/api for Comfy Cloud, or http://127.0.0.1:8188 for a local ComfyUI."
        )
    output_dir = Path(os.environ.get("OUTPUT_DIR", "./outputs")).expanduser()
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    workflows_dir = Path(os.environ.get("WORKFLOWS_DIR", str(REPO_ROOT / "workflows")))
    return Settings(
        comfyui_url=url,
        api_key=os.environ.get("COMFY_CLOUD_API_KEY") or None,
        auth_token=os.environ.get("COMFY_CLOUD_AUTH_TOKEN") or None,
        output_dir=output_dir,
        workflows_dir=workflows_dir,
        host=os.environ.get("APP_HOST", "127.0.0.1"),
        port=int(os.environ.get("APP_PORT", "8787")),
    )
