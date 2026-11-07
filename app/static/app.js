/* Home Hollywood Toolbox front end: plain JavaScript, no build step. */

const CAMERA_MOVES = [
  "slow dolly in",
  "slow dolly out",
  "gentle push forward and down",
  "lateral tracking shot, left to right",
  "slow crane up, revealing the landscape",
  "handheld, barely moving",
  "locked-off tripod, only the light changes",
  "slow orbit around the subject",
  "low mist drifting, soft 35mm film grain",
  "golden hour backlight",
];

const el = (id) => document.getElementById(id);
const state = {
  recipes: [],
  recipe: null,
  upload: null, // {name, subfolder, preview_url}
  shots: [],
};

async function api(path, options = {}) {
  const resp = await fetch(path, options);
  let body = null;
  try { body = await resp.json(); } catch (_) { /* no body */ }
  if (!resp.ok) {
    const detail = body && body.detail ? body.detail : `${resp.status} ${resp.statusText}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return body;
}

/* ---------- backend status ---------- */

async function refreshBackend() {
  const box = el("backend");
  const text = el("backend-text");
  try {
    const info = await api("/api/backend");
    box.classList.toggle("ok", info.reachable);
    box.classList.toggle("bad", !info.reachable);
    if (info.reachable) {
      const q = info.queue_running != null ? ` · ${info.queue_running} running, ${info.queue_pending} queued` : "";
      text.textContent = `${info.label} ${info.version || ""}${q}`;
    } else {
      text.textContent = `${info.label} unreachable: ${info.error || "unknown error"}`;
    }
  } catch (err) {
    box.classList.add("bad");
    text.textContent = `studio backend error: ${err.message}`;
  }
}

/* ---------- recipes and form ---------- */

function specOf(name) {
  return state.recipe ? state.recipe.inputs.find((i) => i.name === name) : null;
}

function applyRecipe(recipe) {
  state.recipe = recipe;
  el("recipe-help").textContent = recipe.description || "";
  const needsImage = !!specOf("image");
  el("image-field").hidden = !needsImage;
  el("motion-row").hidden = !specOf("motion");

  const aspect = specOf("aspect");
  const aspectSel = el("aspect");
  aspectSel.innerHTML = "";
  (aspect ? aspect.choices : ["16:9 (Widescreen)"]).forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c; opt.textContent = c.replace(/\s*\(.*\)/, "");
    if (aspect && c === aspect.default) opt.selected = true;
    aspectSel.appendChild(opt);
  });

  const seconds = specOf("seconds");
  if (seconds) {
    el("seconds").min = seconds.min ?? 1;
    el("seconds").max = seconds.max ?? 10;
    el("seconds").value = seconds.default ?? 5;
  }
  const fps = specOf("fps");
  if (fps) el("fps").value = fps.default ?? 24;
  const negative = specOf("negative");
  el("negative").value = negative && negative.default ? negative.default : "";
  const motion = specOf("motion");
  if (motion) {
    el("motion").min = motion.min ?? 0.3;
    el("motion").max = motion.max ?? 1;
    el("motion").step = motion.step ?? 0.05;
    el("motion").value = motion.default ?? 0.7;
    el("motion-value").textContent = el("motion").value;
  }
}

async function loadRecipes() {
  state.recipes = await api("/api/recipes");
  const sel = el("recipe");
  sel.innerHTML = "";
  state.recipes.forEach((r) => {
    const opt = document.createElement("option");
    opt.value = r.name; opt.textContent = r.title;
    sel.appendChild(opt);
  });
  if (state.recipes.length) applyRecipe(state.recipes[0]);
  sel.addEventListener("change", () => {
    applyRecipe(state.recipes.find((r) => r.name === sel.value));
  });
}

function buildChips() {
  const box = el("chips");
  CAMERA_MOVES.forEach((move) => {
    const chip = document.createElement("button");
    chip.type = "button"; chip.className = "chip"; chip.textContent = move;
    chip.addEventListener("click", () => {
      const ta = el("prompt");
      const sep = ta.value.trim() ? (ta.value.trim().endsWith(",") ? " " : ", ") : "";
      ta.value = ta.value.trim() + sep + move;
      ta.focus();
    });
    box.appendChild(chip);
  });
}

/* ---------- uploads ---------- */

async function uploadFile(file) {
  const text = el("dropzone-text");
  text.textContent = `Uploading ${file.name}…`;
  const form = new FormData();
  form.append("file", file);
  try {
    const rec = await api("/api/uploads", { method: "POST", body: form });
    state.upload = rec;
    const img = el("image-preview");
    img.src = rec.preview_url; img.hidden = false;
    text.innerHTML = "";
    text.hidden = true;
  } catch (err) {
    state.upload = null;
    text.hidden = false;
    text.textContent = `Upload failed: ${err.message}`;
  }
}

function wireDropzone() {
  const zone = el("dropzone");
  const input = el("image-input");
  el("image-browse").addEventListener("click", () => input.click());
  zone.addEventListener("click", (e) => { if (e.target === zone || e.target.id === "image-preview") input.click(); });
  input.addEventListener("change", () => { if (input.files[0]) uploadFile(input.files[0]); });
  ["dragenter", "dragover"].forEach((ev) => zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) => zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.remove("over"); }));
  zone.addEventListener("drop", (e) => { const f = e.dataTransfer.files[0]; if (f) uploadFile(f); });
}

/* ---------- render ---------- */

function collectInputs() {
  const inputs = {};
  const has = (n) => !!specOf(n);
  if (has("prompt")) inputs.prompt = el("prompt").value.trim();
  if (has("negative") && el("negative").value.trim()) inputs.negative = el("negative").value.trim();
  if (has("seconds")) inputs.seconds = Number(el("seconds").value);
  if (has("fps")) inputs.fps = Number(el("fps").value);
  if (has("aspect")) inputs.aspect = el("aspect").value;
  if (has("seed") && el("seed").value.trim()) inputs.seed = el("seed").value.trim();
  if (has("motion")) inputs.motion = Number(el("motion").value);
  if (has("image")) inputs.image = state.upload ? state.upload.name : "";
  return inputs;
}

async function render() {
  const btn = el("render");
  const errBox = el("form-error");
  errBox.hidden = true;
  if (!state.recipe) return;
  const inputs = collectInputs();
  if (!inputs.prompt) { errBox.textContent = "Write a prompt first."; errBox.hidden = false; return; }
  if (specOf("image") && !inputs.image) { errBox.textContent = "This recipe needs a start frame."; errBox.hidden = false; return; }
  btn.disabled = true; btn.textContent = "Submitting…";
  try {
    await api("/api/shots", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipe: state.recipe.name, inputs }),
    });
    await refreshShots();
  } catch (err) {
    errBox.textContent = err.message; errBox.hidden = false;
  } finally {
    btn.disabled = false; btn.textContent = "Render shot";
  }
}

/* ---------- board ---------- */

function fmtElapsed(s) {
  if (s < 60) return `${Math.round(s)} s`;
  return `${Math.floor(s / 60)} min ${Math.round(s % 60)} s`;
}

function renderCard(shot) {
  const tpl = el("shot-card").content.cloneNode(true);
  const card = tpl.querySelector(".card");
  card.dataset.id = shot.id;
  const media = tpl.querySelector(".card-media");
  const dl = tpl.querySelector(".card-download");
  if (shot.state === "running") {
    media.innerHTML = `<div class="pending"><div class="spinner"></div><span>rendering · ${fmtElapsed(shot.elapsed)}</span></div>`;
  } else if (shot.state === "failed") {
    media.innerHTML = `<div class="failed">failed\n${shot.message || ""}</div>`;
  } else if (shot.media.length) {
    const m = shot.media.find((x) => x.kind === "video") || shot.media[0];
    if (m.kind === "video") {
      media.innerHTML = `<video src="${m.url}" controls loop playsinline preload="metadata"></video>`;
    } else {
      media.innerHTML = `<img src="${m.url}" alt="" />`;
    }
    dl.href = m.url; dl.download = m.filename; dl.hidden = false;
  } else {
    media.innerHTML = `<div class="failed">${shot.message || "no media"}</div>`;
  }
  tpl.querySelector(".card-title").textContent = shot.title;
  const i = shot.inputs || {};
  const bits = [shot.recipe];
  if (i.seconds) bits.push(`${i.seconds} s`);
  if (i.aspect) bits.push(i.aspect.replace(/\s*\(.*\)/, ""));
  if (i.seed != null) bits.push(`seed ${i.seed}`);
  if (shot.state !== "running") bits.push(fmtElapsed(shot.elapsed));
  tpl.querySelector(".card-meta").textContent = bits.join(" · ");
  tpl.querySelector(".card-prompt").textContent = i.prompt || "";
  tpl.querySelector(".card-reuse").addEventListener("click", () => {
    el("prompt").value = i.prompt || "";
    if (i.seed != null) el("seed").value = i.seed;
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  tpl.querySelector(".card-delete").addEventListener("click", async () => {
    if (!confirm("Remove this shot from the board? Files stay in the outputs folder.")) return;
    await api(`/api/shots/${shot.id}`, { method: "DELETE" });
    await refreshShots();
  });
  return tpl;
}

async function refreshShots() {
  const shots = await api("/api/shots");
  const board = el("board");
  const empty = el("board-empty");
  el("board-count").textContent = shots.length ? `${shots.length} shot${shots.length > 1 ? "s" : ""}` : "";
  // Rebuild only when something changed, so a playing video is not interrupted.
  const signature = JSON.stringify(shots.map((s) => [s.id, s.state, s.media.length, s.state === "running" ? Math.floor(s.elapsed / 5) : 0]));
  if (signature === state.signature) return;
  state.signature = signature;
  state.shots = shots;
  board.querySelectorAll(".card").forEach((c) => c.remove());
  empty.hidden = shots.length > 0;
  shots.forEach((s) => board.appendChild(renderCard(s)));
}

/* ---------- boot ---------- */

async function boot() {
  buildChips();
  wireDropzone();
  el("render").addEventListener("click", render);
  el("motion").addEventListener("input", () => { el("motion-value").textContent = el("motion").value; });
  try {
    await loadRecipes();
  } catch (err) {
    el("form-error").textContent = `Could not load recipes: ${err.message}`;
    el("form-error").hidden = false;
  }
  await refreshBackend();
  await refreshShots();
  setInterval(refreshShots, 3000);
  setInterval(refreshBackend, 20000);
}

boot();
