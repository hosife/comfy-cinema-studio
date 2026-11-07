# Decisions

| Date | Decision | Why |
| --- | --- | --- |
| 2026-11-07 | Repository created as an empty scaffold; no prior code existed anywhere. | Both collaborators start from the same, inspected state. |
| 2026-11-07 | Apache License 2.0. | Permissive, patent grant, compatible with Apache-licensed model weights. |
| 2026-11-07 | Separate branches `claude/*` and `hermes/*`; `main` by pull request only. | Two agents, no write collisions, Eric reviews merges. |
| 2026-11-07 | Credentials and generated media are excluded from Git by policy and `.gitignore`. | Eric's rule. |
| 2026-11-07 | No claim of hackathon entry or eligibility, ever. | The advertised deadline had passed before work started. |
| 2026-11-07 | Working name `comfy-cinema-studio`, a placeholder. | A real name is Eric's call. |
| 2026-11-07 | Backend in Python 3.10 with FastAPI; frontend is one static HTML/JS page served by the same process, no Node build step. | Python is already on Eric's machine and in Hermes's harness; one `python -m app` command runs the whole thing. A richer frontend can replace the page later without touching the backend. |
| 2026-11-07 | The backend speaks ComfyUI's HTTP API directly (`/prompt`, `/history`, `/view`, `/upload/image`), with a base URL, an optional `/api` path prefix and an optional `X-API-Key` header. | Comfy Cloud exposes the same API at `https://cloud.comfy.org/api/*` behind an API key; a local or rented ComfyUI exposes it at the root without one. One client covers both. |
| 2026-11-07 | Workflows are committed in API format with a sidecar "recipe" JSON that names the friendly inputs (prompt, image, seconds, size, fps, seed) and the node fields they bind to. | Filmmakers set shots, not node ids. Recipes keep the graph untouched and make a workflow swappable. |
| 2026-11-07 | First two recipes: LTX-2.5 text-to-video and image-to-video, as shipped in Comfy's own template gallery. | Both were rendered on Comfy Cloud on 2026-11-07 for a few credits each; LTX-2.5 weights are hosted there, so no download is needed. |
