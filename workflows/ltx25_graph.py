"""LTX 2.5 (22B) T2V API graph builder, audio-video. Needs ComfyUI >= 57ce8e1a.

Three recipes, chosen per run with run_batch.py --recipe:

  dev1        dev transformer, single stage at full resolution, 20 steps,
              BasicScheduler(simple) + CFGGuider(3.0) + euler. Same recipe as
              the LTX 2.3 run, so 2.3 vs 2.5 differ only in the model.
  distilled2  Lightricks' bundled ComfyUI template (video_ltx2_5_t2v.json):
              distilled transformer, 8 sigmas at half resolution, x2 latent
              upscale, 3 refine sigmas, euler_ancestral, cfg 1.
  dev2        dev stage 1 at half resolution (LTXVScheduler, 20 steps,
              LTXVDualCFGGuider video 3 / audio 7), then the template's upscale
              + refine stage on dev + the distilled LoRA, cfg 1.

The template's prompt enhancer (TextGenerateLTX2Prompt) is deliberately not
used: it rewrites each prompt with an LLM, which would break the controlled
counterfactual design.
"""

DEV = "ltx-2.5-22b-dev-transformer-bf16.safetensors"
DISTILLED = "ltx-2.5-22b-distilled-transformer-bf16.safetensors"
TE = "gemma4-12b-with-proj-ltx-2.5-bf16.safetensors"
VIDEO_VAE = "ltx-2.5-video-vae-bf16.safetensors"
AUDIO_VAE = "ltx-2.5-audio-vae-bf16.safetensors"
UPSCALER = "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors"
DISTILLED_LORA = "ltx-2.5-22b-distilled-lora-450-bf16.safetensors"
CKPT = DEV  # provenance hook, mirrors ltx23_graph.CKPT

# sigma schedules copied from the bundled template
STAGE1_DISTILLED = "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"
STAGE2_REFINE = "0.85, 0.7250, 0.4219, 0.0"
RECIPES = ("dev1", "distilled2", "dev2")


def build(positive, negative, width, height, length, seed, steps=20, cfg=3.0,
          fps=24, recipe="dev1", prefix="dfbench/ltx25"):
    if recipe not in RECIPES:
        raise ValueError(f"recipe must be one of {RECIPES}")
    if (length - 1) % 8 or width % 64 or height % 64:
        raise ValueError("length must be 8k+1; width/height multiples of 64 (half-res stage)")
    two_stage = recipe != "dev1"
    w1, h1 = (width // 2, height // 2) if two_stage else (width, height)
    unet1 = DISTILLED if recipe == "distilled2" else DEV

    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": unet1, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": TE, "type": "ltxv", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VIDEO_VAE}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": AUDIO_VAE}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": positive}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": negative}},
        "7": {"class_type": "LTXVConditioning",
              "inputs": {"positive": ["5", 0], "negative": ["6", 0], "frame_rate": float(fps)}},
        "8": {"class_type": "EmptyLTXVLatentVideo",
              "inputs": {"width": w1, "height": h1, "length": length, "batch_size": 1}},
        "9": {"class_type": "LTXVEmptyLatentAudio",
              "inputs": {"frames_number": length, "frame_rate": fps, "batch_size": 1,
                         "audio_vae": ["4", 0]}},
        "10": {"class_type": "LTXVConcatAVLatent",
               "inputs": {"video_latent": ["8", 0], "audio_latent": ["9", 0]}},
        "11": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
    }
    if recipe == "dev1":
        g["12"] = {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}}
        g["13"] = {"class_type": "BasicScheduler",
                   "inputs": {"model": ["1", 0], "scheduler": "simple", "steps": steps,
                              "denoise": 1.0}}
        g["14"] = {"class_type": "CFGGuider",
                   "inputs": {"model": ["1", 0], "positive": ["7", 0], "negative": ["7", 1],
                              "cfg": cfg}}
    elif recipe == "distilled2":
        g["12"] = {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_ancestral"}}
        g["13"] = {"class_type": "ManualSigmas", "inputs": {"sigmas": STAGE1_DISTILLED}}
        g["14"] = {"class_type": "LTXVDualCFGGuider",
                   "inputs": {"model": ["1", 0], "positive": ["7", 0], "negative": ["7", 1],
                              "video_cfg": 1.0, "audio_cfg": 1.0}}
    else:  # dev2
        g["12"] = {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}}
        g["13"] = {"class_type": "LTXVScheduler",
                   "inputs": {"steps": steps, "max_shift": 2.05, "base_shift": 0.95,
                              "stretch": True, "terminal": 0.1, "latent": ["10", 0]}}
        g["14"] = {"class_type": "LTXVDualCFGGuider",
                   "inputs": {"model": ["1", 0], "positive": ["7", 0], "negative": ["7", 1],
                              "video_cfg": cfg, "audio_cfg": 7.0}}
    g["15"] = {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["11", 0], "guider": ["14", 0], "sampler": ["12", 0],
                          "sigmas": ["13", 0], "latent_image": ["10", 0]}}
    g["16"] = {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["15", 0]}}
    final = "16"

    if two_stage:
        model2 = ["1", 0]
        if recipe == "dev2":
            g["17"] = {"class_type": "LoraLoaderModelOnly",
                       "inputs": {"model": ["1", 0], "lora_name": DISTILLED_LORA,
                                  "strength_model": 1.0}}
            model2 = ["17", 0]
        g["18"] = {"class_type": "LatentUpscaleModelLoader", "inputs": {"model_name": UPSCALER}}
        g["19"] = {"class_type": "LTXVLatentUpsampler",
                   "inputs": {"samples": ["16", 0], "upscale_model": ["18", 0], "vae": ["3", 0]}}
        g["20"] = {"class_type": "LTXVConcatAVLatent",
                   "inputs": {"video_latent": ["19", 0], "audio_latent": ["16", 1]}}
        g["21"] = {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_ancestral"}}
        g["22"] = {"class_type": "ManualSigmas", "inputs": {"sigmas": STAGE2_REFINE}}
        g["23"] = {"class_type": "LTXVDualCFGGuider",
                   "inputs": {"model": model2, "positive": ["7", 0], "negative": ["7", 1],
                              "video_cfg": 1.0, "audio_cfg": 1.0}}
        g["24"] = {"class_type": "SamplerCustomAdvanced",
                   "inputs": {"noise": ["11", 0], "guider": ["23", 0], "sampler": ["21", 0],
                              "sigmas": ["22", 0], "latent_image": ["20", 0]}}
        g["25"] = {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["24", 0]}}
        final = "25"

    g["30"] = {"class_type": "VAEDecodeTiled",
               "inputs": {"samples": [final, 0], "vae": ["3", 0], "tile_size": 512,
                          "overlap": 64, "temporal_size": 64, "temporal_overlap": 16}}
    g["31"] = {"class_type": "LTXVAudioVAEDecode",
               "inputs": {"samples": [final, 1], "audio_vae": ["4", 0]}}
    g["32"] = {"class_type": "CreateVideo",
               "inputs": {"images": ["30", 0], "fps": float(fps), "audio": ["31", 0]}}
    g["33"] = {"class_type": "SaveVideo",
               "inputs": {"video": ["32", 0], "filename_prefix": prefix,
                          "format": "mp4", "format.codec": "h264"}}
    return g
