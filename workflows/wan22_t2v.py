#!/usr/bin/env python
"""Wan 2.2 T2V-A14B throughput bench: precision x steps x cfg x resolution.

Full-quality path per bundled template: 20 steps split 10/10 at the MoE
boundary, cfg 3.5, shift 5.0. Fast path: 4 steps split 2/2, cfg 1.0, lightx2v LoRAs.
"""
import json, time, urllib.request, uuid, argparse, sys

HOST = "127.0.0.1:8188"
POS = ("A photorealistic video of an East Asian woman in her late thirties with "
       "shoulder-length black hair, framed head-and-shoulders with her face centered, "
       "speaking casually to the camera with natural blinking and an occasional smile. "
       "Modern office with a softly blurred background, soft natural window light. "
       "Static camera with slight natural handheld sway. Single person in frame.")
NEG = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，"
       "最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，"
       "画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，"
       "杂乱的背景，三条腿，背景人很多，倒着走，裸露，NSFW")

UNET = {"fp8": ("wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors",
                "wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors"),
        "fp16": ("wan2.2_t2v_high_noise_14B_fp16.safetensors",
                 "wan2.2_t2v_low_noise_14B_fp16.safetensors")}
TE = {"fp8": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "fp16": "umt5_xxl_fp16.safetensors"}
HI_LORA = "wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors"
LO_LORA = "wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors"


def build(w, h, length, seed, precision="fp16", steps=20, boundary=10, cfg=3.5,
          shift=5.0, fps=16, lora=False, prefix="bench/wan22"):
    hi, lo = UNET[precision]
    g = {
      "1": {"class_type": "CLIPLoader", "inputs": {"clip_name": TE[precision],
            "type": "wan", "device": "default"}},
      "2": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
      "3": {"class_type": "UNETLoader", "inputs": {"unet_name": hi, "weight_dtype": "default"}},
      "4": {"class_type": "UNETLoader", "inputs": {"unet_name": lo, "weight_dtype": "default"}},
      "9": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": POS}},
      "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": NEG}},
      "11": {"class_type": "EmptyHunyuanLatentVideo",
             "inputs": {"width": w, "height": h, "length": length, "batch_size": 1}},
      "14": {"class_type": "VAEDecode", "inputs": {"samples": ["13", 0], "vae": ["2", 0]}},
      "15": {"class_type": "CreateVideo", "inputs": {"images": ["14", 0], "fps": fps}},
      "16": {"class_type": "SaveVideo", "inputs": {"video": ["15", 0],
             "filename_prefix": prefix, "format": "auto", "codec": "auto"}},
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
    g["12"] = {"class_type": "KSamplerAdvanced",
               "inputs": {"add_noise": "enable", "noise_seed": seed, "steps": steps, "cfg": cfg,
                          "sampler_name": "euler", "scheduler": "simple", "start_at_step": 0,
                          "end_at_step": boundary, "return_with_leftover_noise": "enable",
                          "model": ["7", 0], "positive": ["9", 0], "negative": ["10", 0],
                          "latent_image": ["11", 0]}}
    g["13"] = {"class_type": "KSamplerAdvanced",
               "inputs": {"add_noise": "disable", "noise_seed": 0, "steps": steps, "cfg": cfg,
                          "sampler_name": "euler", "scheduler": "simple",
                          "start_at_step": boundary, "end_at_step": steps,
                          "return_with_leftover_noise": "disable",
                          "model": ["8", 0], "positive": ["9", 0], "negative": ["10", 0],
                          "latent_image": ["12", 0]}}
    return g


def post(p, d):
    r = urllib.request.Request(f"http://{HOST}{p}", data=json.dumps(d).encode(),
                               headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=60).read())


def get(p):
    return json.loads(urllib.request.urlopen(f"http://{HOST}{p}", timeout=60).read())


def set_host(h):
    global HOST
    HOST = h


def run(label, timeout_s=14400, **kw):
    g = build(**kw)
    t0 = time.time()
    pid = post("/prompt", {"prompt": g, "client_id": str(uuid.uuid4())})["prompt_id"]
    print(f"[{label}] submitted {pid}", flush=True)
    while True:
        h = get(f"/history/{pid}")
        if pid in h:
            st = h[pid].get("status", {}); dt = time.time() - t0
            if st.get("status_str") == "error":
                for m in st.get("messages", []):
                    if m and m[0] == "execution_error":
                        print(f"[{label}] ERROR {dt:.1f}s node={m[1].get('node_type')} "
                              f"{str(m[1].get('exception_message'))[:300]}", flush=True)
                return {"label": label, "ok": False, "seconds": dt, **{k: v for k, v in kw.items()}}
            print(f"[{label}] OK {dt:.1f}s", flush=True)
            return {"label": label, "ok": True, "seconds": dt, **{k: v for k, v in kw.items()}}
        if time.time() - t0 > timeout_s:
            print(f"[{label}] TIMEOUT {timeout_s}s", flush=True)
            return {"label": label, "ok": False, "seconds": time.time() - t0}
        time.sleep(3)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", required=True,
                    help="semicolon list: label,precision,steps,boundary,cfg,lora,w,h,len")
    ap.add_argument("--out", default=None)
    ap.add_argument("--host", default=HOST)
    a = ap.parse_args()
    set_host(a.host)
    res = []
    for c in a.configs.split(";"):
        if not c.strip():
            continue
        lab, prec, steps, bnd, cfg, lora, w, h, ln = c.split(",")
        res.append(run(lab, precision=prec, steps=int(steps), boundary=int(bnd),
                       cfg=float(cfg), lora=(lora == "1"), w=int(w), h=int(h),
                       length=int(ln), seed=771234, prefix=f"bench/{lab}"))
    print(json.dumps(res, indent=2))
    if a.out:
        json.dump(res, open(a.out, "w"), indent=2)
