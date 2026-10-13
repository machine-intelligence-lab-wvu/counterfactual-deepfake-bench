"""Production HunyuanVideo 1.5 720p T2V API graph builder (fp16, video only).

Mirrors the bundled `video_hunyuan_video_1.5_720p_t2v.json` and the benchmark in
hunyuan15_t2v.py: Qwen2.5-VL-7B + byT5 text encoders, shift 7, euler/simple,
CFGGuider. Reference-quality defaults are 20 steps at cfg 6.0 (THROUGHPUT_REPORT.md).
EasyCache nodes are deliberately omitted - the template warns they cost quality.
"""

UNET = "hunyuanvideo1.5_720p_t2v_fp16.safetensors"
TE = "qwen_2.5_vl_7b.safetensors"
TE2 = "byt5_small_glyphxl_fp16.safetensors"
VAE = "hunyuanvideo15_vae_fp16.safetensors"
CKPT = UNET                       # provenance hook, mirrors ltx23_graph.CKPT


def build(positive, negative, width, height, length, seed, steps=20, cfg=6.0,
          fps=24, shift=7.0, prefix="fairdeep/hunyuan15"):
    if (length - 1) % 4:
        raise ValueError(f"HunyuanVideo 1.5 length must be 4k+1, got {length}")
    return {
        "1": {"class_type": "DualCLIPLoader",
              "inputs": {"clip_name1": TE, "clip_name2": TE2,
                         "type": "hunyuan_video_15", "device": "default"}},
        "2": {"class_type": "UNETLoader",
              "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": positive}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": negative}},
        "6": {"class_type": "EmptyHunyuanVideo15Latent",
              "inputs": {"width": width, "height": height, "length": length,
                         "batch_size": 1}},
        "7": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["2", 0], "shift": shift}},
        "8": {"class_type": "BasicScheduler",
              "inputs": {"model": ["7", 0], "scheduler": "simple", "steps": steps,
                         "denoise": 1.0}},
        "9": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "10": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "11": {"class_type": "CFGGuider",
               "inputs": {"model": ["7", 0], "positive": ["4", 0], "negative": ["5", 0],
                          "cfg": cfg}},
        "12": {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["9", 0], "guider": ["11", 0], "sampler": ["10", 0],
                          "sigmas": ["8", 0], "latent_image": ["6", 0]}},
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["3", 0]}},
        "14": {"class_type": "CreateVideo", "inputs": {"images": ["13", 0], "fps": float(fps)}},
        "15": {"class_type": "SaveVideo",
               "inputs": {"video": ["14", 0], "filename_prefix": prefix,
                          "format": "auto", "codec": "h264"}},
    }
