# ltx25_t2v: text to video with LTX-2.5

**Purpose.** A 1 to 10 second clip with generated sound from a written prompt.
No input image, so nothing but the prompt enters the render.

**Origin.** Comfy's own template `video_ltx2_5_t2v` (ComfyUI v0.44.2 template
gallery), fetched with `comfy templates fetch video_ltx2_5_t2v` on 7 November
2026 and converted to API format with `comfy run --print-prompt`. The graph is
unchanged apart from neutral default values in the fields the recipe binds.

**Inputs** (see `recipe.json` for the node bindings): prompt, negative prompt,
seconds, frame rate, aspect ratio, megapixels, seed, output name.

**Output.** Node `75` (SaveVideo), MP4 with audio, 24 fps by default, about
1280x704 at 16:9 and 0.9 megapixels. The optional x2 latent upscaler in the
template stays switched off.

**First render.** Comfy Cloud, 7 November 2026: 5 seconds at 1280x704 took
23 seconds of wall clock and cost 7 credits.

## Models

All weights are hosted on Comfy Cloud, so nothing is downloaded for the cloud
backend. For a self-hosted ComfyUI, fetch them from the sources below into the
listed folders. sha256 values are not recorded yet: fill them in from the
Hugging Face file pages when a self-hosted backend is set up.

| File | Folder | Source |
| --- | --- | --- |
| ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors | diffusion_models | https://huggingface.co/Lightricks/LTX-2.5/resolve/main/diffusion_models/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors |
| ltx-2.5-video-vae-bf16.safetensors | vae | https://huggingface.co/Lightricks/LTX-2.5/resolve/main/vae/ltx-2.5-video-vae-bf16.safetensors |
| ltx-2.5-audio-vae-bf16.safetensors | vae | https://huggingface.co/Lightricks/LTX-2.5/resolve/main/vae/ltx-2.5-audio-vae-bf16.safetensors |
| gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors | text_encoders | https://huggingface.co/Lightricks/LTX-2.5/resolve/main/text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors |
| gemma4_e2b_it_int8_convrot.safetensors | text_encoders | https://huggingface.co/Comfy-Org/gemma-4/resolve/main/text_encoders/gemma4_e2b_it_int8_convrot.safetensors |
| ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors | latent_upscale_models | https://huggingface.co/Lightricks/LTX-2.5/resolve/main/latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors |

Check the licence on the Lightricks model card before shipping anything
commercial with these weights.

## Custom nodes

None. Every node is in ComfyUI core v0.44.2.
