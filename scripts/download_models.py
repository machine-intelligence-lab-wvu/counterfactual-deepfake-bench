#!/usr/bin/env python
"""Fetch the model weights a ComfyUI install needs, from Hugging Face.

Weights are never committed to git (~200 GiB). Each cluster pulls them once:
  python scripts/download_models.py --comfy-root ../ComfyUI --models ltx23
  python scripts/download_models.py --models all          # ltx23 + wan22 + hunyuan15
Existing files are skipped, so re-running is safe. Set HF_HUB_CACHE to a scratch
filesystem if home quota is tight.
"""
import argparse, os, shutil
from huggingface_hub import hf_hub_download

WAN = "Comfy-Org/Wan_2.2_ComfyUI_Repackaged"
WAN21 = "Comfy-Org/Wan_2.1_ComfyUI_repackaged"
HY = "Comfy-Org/HunyuanVideo_1.5_repackaged"

# (repo, path in repo, ComfyUI models/ subfolder)
MODELS = {
    "ltx23": [
        ("Lightricks/LTX-2.3", "ltx-2.3-22b-dev.safetensors", "checkpoints"),
        ("Lightricks/LTX-2.3", "ltx-2.3-spatial-upscaler-x2-1.1.safetensors", "latent_upscale_models"),
        ("Comfy-Org/ltx-2", "split_files/text_encoders/gemma_3_12B_it.safetensors", "text_encoders"),
    ],
    "wan22": [
        (WAN, "split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp16.safetensors", "diffusion_models"),
        (WAN, "split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp16.safetensors", "diffusion_models"),
        (WAN, "split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors", "diffusion_models"),
        (WAN, "split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors", "diffusion_models"),
        (WAN, "split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors", "loras"),
        (WAN, "split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors", "loras"),
        (WAN, "split_files/vae/wan_2.1_vae.safetensors", "vae"),
        (WAN, "split_files/vae/wan2.2_vae.safetensors", "vae"),
        (WAN21, "split_files/text_encoders/umt5_xxl_fp16.safetensors", "text_encoders"),
        (WAN21, "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors", "text_encoders"),
    ],
    "hunyuan15": [
        (HY, "split_files/diffusion_models/hunyuanvideo1.5_720p_t2v_fp16.safetensors", "diffusion_models"),
        (HY, "split_files/vae/hunyuanvideo15_vae_fp16.safetensors", "vae"),
        (HY, "split_files/text_encoders/byt5_small_glyphxl_fp16.safetensors", "text_encoders"),
        ("Comfy-Org/HunyuanImage_2.1_ComfyUI", "split_files/text_encoders/qwen_2.5_vl_7b.safetensors", "text_encoders"),
    ],
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--comfy-root", default=os.environ.get(
        "FAIRDEEP_COMFY_ROOT", os.path.join(os.path.dirname(here), "ComfyUI")))
    ap.add_argument("--models", default="ltx23",
                    help="comma list of " + ",".join(MODELS) + " or 'all'")
    args = ap.parse_args()

    groups = list(MODELS) if args.models == "all" else args.models.split(",")
    for g in groups:
        for repo, path, sub in MODELS[g]:
            dst = os.path.join(args.comfy_root, "models", sub, os.path.basename(path))
            if os.path.exists(dst):
                print(f"[skip] {sub}/{os.path.basename(path)}")
                continue
            print(f"[get ] {repo}/{path}", flush=True)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            src = hf_hub_download(repo, path)
            # move out of the HF cache rather than copy: these files are 10-43 GiB
            shutil.move(os.path.realpath(src), dst)
            if os.path.islink(src):
                os.remove(src)


if __name__ == "__main__":
    main()
