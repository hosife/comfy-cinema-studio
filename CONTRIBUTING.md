# Contributing

Two collaborators work here, Claude and Hermes, coordinated by Eric.

## Branch protocol

- `main` is protected by convention: nobody commits to it directly.
- Claude works on `claude/dev` and `claude/<topic>`; Hermes on `hermes/dev`
  and `hermes/<topic>`.
- A change reaches `main` through a pull request that Eric approves.
- Never force-push a branch you do not own. Never rewrite `main`.

## What may not be committed

- Secrets of any kind: `.env`, tokens, API keys, cookies, account exports.
- Generated media: images, video, audio renders, previews, thumbnails.
- Model weights or large binaries. Reference them by URL and digest instead.
- Code, assets, names or copy taken from a proprietary product.

`.gitignore` enforces the common cases. If `git status` shows a media or
secret file, stop and move it out before committing.

## Commit messages

Short imperative subject line, body explaining why. Name the agent that
authored the change in a trailer, for example
`Co-Authored-By: Hermes <hermes@local>`.

## Workflows

ComfyUI workflows go in `workflows/` in **API format** (File → Export (API)),
one JSON per workflow, each with a short README naming the models and custom
node packs it needs and where they come from.
