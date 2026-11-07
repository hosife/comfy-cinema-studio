# app

A one-page shot studio in front of any ComfyUI backend.

```
app/
  __main__.py       python -m app  (reads .env, starts the server)
  config.py         settings from the environment
  comfy_client.py   ComfyUI HTTP API: /prompt, /history, /view, /upload/image
  recipes.py        loads workflows/*/recipe.json and fills the graph
  jobs.py           shots: submit, poll, download outputs, persist shots.json
  main.py           FastAPI routes and the static page
  static/           index.html, app.js, style.css (no build step)
```

## HTTP routes

| Route | Purpose |
| --- | --- |
| `GET /api/backend` | backend label, version, reachability, queue size |
| `GET /api/recipes` | the recipes and their inputs |
| `POST /api/uploads` | upload a still; returns the backend's name for it |
| `POST /api/shots` | `{recipe, title?, inputs}` submits a render |
| `GET /api/shots` | the board, newest first |
| `GET /api/shots/{id}/media/{file}` | a rendered file from the outputs folder |
| `DELETE /api/shots/{id}` | remove from the board (files stay on disk) |
