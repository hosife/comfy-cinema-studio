"""Run the studio: ``python -m app``."""

from __future__ import annotations

import logging

import uvicorn

from .config import load_settings
from .main import create_app


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = load_settings()
    app = create_app(settings)
    print(f"\n  comfy-cinema-studio  ->  http://{settings.host}:{settings.port}\n"
          f"  backend: {settings.backend_label} ({settings.comfyui_url})\n"
          f"  outputs: {settings.output_dir}\n")
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
