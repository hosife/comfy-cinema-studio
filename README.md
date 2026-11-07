# comfy-cinema-studio

An open-source cinematic creation app powered by ComfyUI. The working name is a
placeholder.

**Status: first working version, 7 November 2026.** One page, two recipes
(text to video and image to video with LTX-2.5), any ComfyUI backend over
HTTP. Rendered its first shot on Comfy Cloud the day it was written. See
`docs/DECISIONS.md` for the choices made and why.

## What it is meant to become

A self-hostable studio for short cinematic clips: reference images and a
written brief in, storyboards and video shots out, with ComfyUI doing the
generation behind an HTTP API. The product category is the one popularised by
Higgsfield. Nothing here copies that product's code, assets, names or
branding, and the project makes no claim about any competition or hackathon.

## Run it

Needs Python 3.10 or newer and a ComfyUI backend you can reach.

```
pip install -r requirements.txt
copy .env.example .env        (macOS/Linux: cp .env.example .env)
```

Fill in `.env`:

- **Comfy Cloud:** `COMFYUI_URL=https://cloud.comfy.org/api` and a workspace
  API key in `COMFY_CLOUD_API_KEY`. Renders cost credits on that workspace.
- **Your own ComfyUI:** `COMFYUI_URL=http://127.0.0.1:8188` (or the box's
  address), no key. The LTX-2.5 weights must be installed there; each
  workflow README lists them.

Then:

```
python -m app
```

Open http://127.0.0.1:8787. Pick a recipe, drop a still you own (image to
video), write the shot, click **Render shot**. Finished clips appear on the
board and are saved under `outputs/`, which Git ignores.

## Ground rules

- **Open source, original work.** No proprietary code, model weights under
  restrictive licences, screenshots, logos or copy from any commercial product.
- **Credentials never enter Git.** API keys, tokens and account files live in
  `.env` or outside the repository. `.env.example` lists the variable names
  only. See `.gitignore`.
- **Generated media never enters Git.** Outputs, previews, renders and model
  weights stay in ignored folders (`outputs/`, `models/`, `media/`). Share them
  through links, not commits.
- **No eligibility claims.** The advertised deadline of the related hackathon
  has passed. Do not describe this work as an entry or submission.

## Branches

| Branch | Owner | Purpose |
| --- | --- | --- |
| `main` | Eric | Integration branch. Changes arrive by pull request only. |
| `claude/dev` | Claude | Claude's working branch. Feature branches: `claude/<topic>`. |
| `hermes/dev` | Hermes | Hermes's working branch. Feature branches: `hermes/<topic>`. |

Each collaborator commits only to its own branches. Merges into `main` are
reviewed by Eric. See `CONTRIBUTING.md`.

## How it works

```
browser page  ->  FastAPI (app/)  ->  ComfyUI HTTP API  ->  Comfy Cloud or any ComfyUI
                      |
                      +-- workflows/<recipe>/   API-format graph + recipe.json (friendly inputs)
                      +-- outputs/              uploads, rendered media, shots.json (ignored by Git)
```

The backend never depends on a vendor SDK. It uploads with `/upload/image`,
submits with `/prompt`, polls `/history` (Comfy Cloud: `/history_v2`) and
downloads with `/view`. `docs/ENVIRONMENT.md` records the backend quirks met
so far.

## Layout

```
app/          FastAPI backend and the static one-page front end
workflows/    one folder per recipe: workflow.api.json, recipe.json, README.md
docs/         decisions, environment notes
```

## Licence

Apache License 2.0. See `LICENSE`.
