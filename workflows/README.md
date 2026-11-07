# Workflows

Each folder is one recipe the app can run:

```
workflows/<name>/
  workflow.api.json   the ComfyUI graph in API format, exactly as POSTed to /prompt
  recipe.json         friendly inputs (prompt, image, seconds, ...) and the node fields they write
  README.md           purpose, inputs, outputs, every model with its source, every custom node pinned
```

The app loads every `recipe.json` at start. It never edits the graph's
structure; it only writes the declared input values into the declared fields,
then submits the graph.

| Recipe | What it does | Backend tested |
| --- | --- | --- |
| `ltx25_t2v` | Text to video, 1 to 10 s, with sound | Comfy Cloud, 2026-11-07 |
| `ltx25_i2v` | Image to video from a still you own | Comfy Cloud, 2026-11-07 |

## Adding a recipe

1. Build or fetch the workflow in ComfyUI and export it in API format
   (`comfy run --print-prompt --workflow x.json` converts a UI-format file).
2. Put placeholder values in the fields you want to expose, find their node
   ids in the API JSON, and write `recipe.json` with one entry per input.
   Supported types: `string`, `int`, `float`, `choice`, `image`, `seed`.
3. Write the README with model provenance (source URL and sha256) and custom
   node pins. No weights, no media, no credentials in the folder.
