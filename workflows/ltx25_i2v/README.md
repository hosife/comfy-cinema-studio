# ltx25_i2v: image to video with LTX-2.5

**Purpose.** Animate a still into a 1 to 10 second clip with generated sound.
The still becomes the first frame and the prompt describes the camera move.
Use only images you own or have the right to use.

**Origin.** Comfy's own template `video_ltx2_5_i2v` (ComfyUI v0.44.2 template
gallery), fetched with `comfy templates fetch video_ltx2_5_i2v` on 7 November
2026 and converted to API format with `comfy run --print-prompt`. The graph is
unchanged apart from neutral default values in the fields the recipe binds.

**Inputs** (see `recipe.json`): start frame (the name returned by the backend's
`/upload/image`), prompt, negative prompt, seconds, frame rate, aspect ratio,
megapixels, motion strength, seed, output name.

**Output.** Node `75` (SaveVideo), MP4 with audio. The still is resized to
1536 px on its longer side for conditioning; the clip itself is about
1280x704 at 16:9 and 0.9 megapixels.

**Backend note.** Comfy Cloud renames uploads to their content hash. The
LoadImage field must carry the name the upload call returned; the original
filename fails with a missing-file error.

**First render.** Comfy Cloud, 7 November 2026: a 1920x1080 drone still,
5 seconds out, 25 seconds of wall clock, 4 credits.

## Models

Same set as `ltx25_t2v`; see that README for the table of files, folders and
sources. sha256 values are still to be filled in for a self-hosted backend.

## Custom nodes

None. Every node is in ComfyUI core v0.44.2.
