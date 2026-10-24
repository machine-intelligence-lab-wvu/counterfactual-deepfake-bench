"""Production LTX 2.3 T2V API graph builder (bf16 dev, audio-video).

LTX 2.3 is an AV model: video and audio latents are concatenated, sampled
jointly, then split. Mirrors the bundled `video_ltx2_3_t2v.json` single-stage
path with the non-distilled `dev` checkpoint.
"""

CKPT = "ltx-2.3-22b-dev.safetensors"
GEMMA = "gemma_3_12B_it.safetensors"

# Identity LoRAs shipped in Comfy-Org/ltx-2.3 are trained on CelebV-HQ / TalkVid,
# i.e. real people including public figures. Loading one would violate plan 3.1
# (synthetic identities only) and poison the 7.4 identity-leakage gate at source.
DENYLIST = {
    "ltx-2.3-id-lora-celebvhq-3k.safetensors",
    "ltx-2.3-id-lora-talkvid-3k.safetensors",
}


def build(positive, negative, width, height, length, seed, steps=20, cfg=3.0,
          fps=24, audio_fps=25, with_audio=True, prefix="dfbench/ltx23"):
    for node in (CKPT, GEMMA):
        if node in DENYLIST:
            raise ValueError(f"denylisted real-person model: {node}")

    g = {
        "1":  {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "2":  {"class_type": "LTXAVTextEncoderLoader",
               "inputs": {"text_encoder": GEMMA, "ckpt_name": CKPT, "device": "default"}},
        "3":  {"class_type": "LTXVAudioVAELoader", "inputs": {"ckpt_name": CKPT}},
        "4":  {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": positive}},
        "5":  {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": negative}},
        "6":  {"class_type": "LTXVConditioning",
               "inputs": {"positive": ["4", 0], "negative": ["5", 0],
                          "frame_rate": float(fps)}},
        "7":  {"class_type": "EmptyLTXVLatentVideo",
               "inputs": {"width": width, "height": height,
                          "length": length, "batch_size": 1}},
        "10": {"class_type": "BasicScheduler",
               "inputs": {"model": ["1", 0], "scheduler": "simple",
                          "steps": steps, "denoise": 1.0}},
        "11": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "12": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "13": {"class_type": "CFGGuider",
               "inputs": {"model": ["1", 0], "positive": ["6", 0],
                          "negative": ["6", 1], "cfg": cfg}},
    }
    if with_audio:
        g["8"] = {"class_type": "LTXVEmptyLatentAudio",
                  "inputs": {"frames_number": length, "frame_rate": float(audio_fps),
                             "batch_size": 1, "audio_vae": ["3", 0]}}
        g["9"] = {"class_type": "LTXVConcatAVLatent",
                  "inputs": {"video_latent": ["7", 0], "audio_latent": ["8", 0]}}
        latent = ["9", 0]
    else:
        latent = ["7", 0]

    g["14"] = {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["11", 0], "guider": ["13", 0], "sampler": ["12", 0],
                          "sigmas": ["10", 0], "latent_image": latent}}
    if with_audio:
        g["15"] = {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["14", 0]}}
        g["16"] = {"class_type": "VAEDecode", "inputs": {"samples": ["15", 0], "vae": ["1", 2]}}
        g["17"] = {"class_type": "LTXVAudioVAEDecode",
                   "inputs": {"samples": ["15", 1], "audio_vae": ["3", 0]}}
        g["18"] = {"class_type": "CreateVideo",
                   "inputs": {"images": ["16", 0], "fps": float(fps), "audio": ["17", 0]}}
    else:
        g["16"] = {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["1", 2]}}
        g["18"] = {"class_type": "CreateVideo",
                   "inputs": {"images": ["16", 0], "fps": float(fps)}}
    g["19"] = {"class_type": "SaveVideo",
               "inputs": {"video": ["18", 0], "filename_prefix": prefix,
                          "format": "auto", "codec": "h264"}}
    return g
