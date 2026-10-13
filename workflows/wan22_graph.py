"""Production Wan 2.2 T2V-A14B API graph builder (fp16 MoE, video only).

Two experts sample one schedule: high-noise expert for the first `boundary`
steps, low-noise expert for the rest. Default is the lightx2v 4-step LoRA path
(4 steps split 2/2, cfg 1.0); pass lora=False, steps=20, cfg=3.5 for the
reference-quality path benchmarked in THROUGHPUT_REPORT.md.
"""

UNET_HI = "wan2.2_t2v_high_noise_14B_fp16.safetensors"
UNET_LO = "wan2.2_t2v_low_noise_14B_fp16.safetensors"
TE = "umt5_xxl_fp16.safetensors"
VAE = "wan_2.1_vae.safetensors"   # the 14B MoE uses the 2.1 VAE, not wan2.2_vae
HI_LORA = "wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors"
LO_LORA = "wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors"
CKPT = UNET_HI                    # provenance hook, mirrors ltx23_graph.CKPT


def build(positive, negative, width, height, length, seed, steps=4, cfg=1.0,
          fps=16, shift=5.0, lora=True, boundary=None, prefix="fairdeep/wan22"):
    if (length - 1) % 4:
        raise ValueError(f"Wan length must be 4k+1, got {length}")
    boundary = steps // 2 if boundary is None else boundary
    g = {
        "1": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": TE, "type": "wan", "device": "default"}},
        "2": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "3": {"class_type": "UNETLoader",
              "inputs": {"unet_name": UNET_HI, "weight_dtype": "default"}},
        "4": {"class_type": "UNETLoader",
              "inputs": {"unet_name": UNET_LO, "weight_dtype": "default"}},
        "9": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": positive}},
        "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": negative}},
        "11": {"class_type": "EmptyHunyuanLatentVideo",
               "inputs": {"width": width, "height": height, "length": length,
                          "batch_size": 1}},
        "14": {"class_type": "VAEDecode", "inputs": {"samples": ["13", 0], "vae": ["2", 0]}},
        "15": {"class_type": "CreateVideo", "inputs": {"images": ["14", 0], "fps": float(fps)}},
        "16": {"class_type": "SaveVideo",
               "inputs": {"video": ["15", 0], "filename_prefix": prefix,
                          "format": "auto", "codec": "h264"}},
    }
    hi_src, lo_src = ["3", 0], ["4", 0]
    if lora:
        g["5"] = {"class_type": "LoraLoaderModelOnly",
                  "inputs": {"model": ["3", 0], "lora_name": HI_LORA, "strength_model": 1.0}}
        g["6"] = {"class_type": "LoraLoaderModelOnly",
                  "inputs": {"model": ["4", 0], "lora_name": LO_LORA, "strength_model": 1.0}}
        hi_src, lo_src = ["5", 0], ["6", 0]
    g["7"] = {"class_type": "ModelSamplingSD3", "inputs": {"model": hi_src, "shift": shift}}
    g["8"] = {"class_type": "ModelSamplingSD3", "inputs": {"model": lo_src, "shift": shift}}
    common = {"cfg": cfg, "sampler_name": "euler", "scheduler": "simple", "steps": steps,
              "positive": ["9", 0], "negative": ["10", 0]}
    g["12"] = {"class_type": "KSamplerAdvanced",
               "inputs": {**common, "add_noise": "enable", "noise_seed": seed,
                          "start_at_step": 0, "end_at_step": boundary,
                          "return_with_leftover_noise": "enable",
                          "model": ["7", 0], "latent_image": ["11", 0]}}
    g["13"] = {"class_type": "KSamplerAdvanced",
               "inputs": {**common, "add_noise": "disable", "noise_seed": 0,
                          "start_at_step": boundary, "end_at_step": steps,
                          "return_with_leftover_noise": "disable",
                          "model": ["8", 0], "latent_image": ["12", 0]}}
    return g
