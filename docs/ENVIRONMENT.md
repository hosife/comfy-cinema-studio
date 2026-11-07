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

## RunPod (reported by Hermes, 7 November 2026, unverified here)

- A stopped Pod named "Sun Sun Studio" (id wo8ouig7ed7ooa) with one RTX 4090 in EUR-IS-2 and about
  49 USD of account credit exists on Eric's RunPod account. Its ComfyUI service, image, port and
  authentication are not verified; a read-only probe of the conventional proxy URL answered 403.
- Starting the Pod costs GPU time and needs Eric's separate approval. Storage may bill while stopped.
- No RunPod management API key is available to either agent; browser login does not supply one.

## Hermes's production harness v0.1.0

Hermes delivered `production-harness-v0.1.0.zip` on 7 November 2026: a stdlib-only Python CLI that
plans a ComfyUI job, requires one recorded human cost approval, submits once, resumes by remote id
and archives outputs with SHA-256 checksums, against either Comfy Cloud API v2 or a native ComfyUI
Pod. Both backends ship disabled; its manifest hashes verify; its 46 tests were not run from here.
It is the natural execution layer for this app. Where it lives in the repository is decided on the
dev branches.

## Design consequence

The app must speak only to ComfyUI's HTTP API (`/prompt`, `/history`, `/view`, websocket
progress). The backend URL is configuration (`COMFYUI_URL`), never code.

## Model licensing

Prefer open-weights models with permissive licences (for example Wan 2.x under Apache 2.0).
Record every model's source URL and sha256 in the workflow README that uses it.
