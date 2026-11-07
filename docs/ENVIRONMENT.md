# Environment notes (7 November 2026)

## Development machine (Eric, Windows 11)

- No NVIDIA GPU, no Docker, no WSL, no local ComfyUI install.
- Python 3.10 on PATH; Node.js available; Git 2.54; GitHub Desktop installed; no GitHub CLI.
- `comfy-cli` 1.25.0 installed and signed in to Comfy Cloud (Personal Workspace, Creator plan).
- **Keep this repository outside synced folders** (Proton Drive, OneDrive). The sync client renames
  files it sees changing with a "Name clash" suffix, which destroys `.git`. `C:\Users\<you>\code` is safe.

## Comfy Cloud, what it offers

- `comfy build`: package a ComfyUI version, custom node packs and model references into a
  reproducible build and cut a release for `linux/nvidia`.
- `comfy deploy`: run a release as a serverless endpoint. **Billing is continuous while a
  deployment holds compute**, so deployments are created and stopped deliberately, by Eric.
- The Creator plan does not accept governance/policy blocks in a build definition.
- Read `comfy skills show comfy-build` and `comfy skills show comfy-deploy` before touching either.

## Design consequence

The app must speak only to ComfyUI's HTTP API (`/prompt`, `/history`, `/view`, websocket
progress). The backend URL is configuration (`COMFYUI_URL`), never code.

## Model licensing

Prefer open-weights models with permissive licences (for example Wan 2.x under Apache 2.0).
Record every model's source URL and sha256 in the workflow README that uses it.
