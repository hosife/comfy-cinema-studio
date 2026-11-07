# comfy-cinema-studio

An open-source cinematic creation app powered by ComfyUI. The working name is a
placeholder.

**Status: empty scaffold, 7 November 2026.** There is no application code yet.
This repository exists so that two collaborators, Claude and Hermes, can start
from the same place with the same rules.

## What it is meant to become

A self-hostable studio for short cinematic clips: reference images and a
written brief in, storyboards and video shots out, with ComfyUI doing the
generation behind an HTTP API. The product category is the one popularised by
Higgsfield. Nothing here copies that product's code, assets, names or
branding, and the project makes no claim about any competition or hackathon.

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

## Generation backend

The development machine has no NVIDIA GPU, so local ComfyUI is not an option
for rendering. Two backends are on the table and recorded in
`docs/ENVIRONMENT.md`:

1. **Comfy Cloud** through `comfy-cli`: a packaged ComfyUI build served as a
   paid serverless endpoint.
2. **Any reachable ComfyUI** over its standard HTTP API (a rented GPU box, a
   collaborator's machine).

The application code should talk to ComfyUI's HTTP API only, so that either
backend works unchanged.

## Layout

```
app/          application code (empty)
workflows/    ComfyUI workflow JSON in API format, with a README per workflow
docs/         decisions, environment notes, collaboration protocol
```

## Licence

Apache License 2.0. See `LICENSE`.
