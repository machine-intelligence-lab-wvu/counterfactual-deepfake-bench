#!/usr/bin/env python
"""HunyuanVideo 1.5 720p T2V throughput bench (fp16, full quality).

Mirrors bundled `video_hunyuan_video_1.5_720p_t2v.json`:
  DualCLIPLoader(qwen2.5-vl-7b + byt5-glyphxl, type=hunyuan_video_15)
  ModelSamplingSD3 shift 7 -> BasicScheduler(simple, 20) -> CFGGuider(6) -> euler
  EmptyHunyuanVideo15Latent 1280x720x121, CreateVideo @ 24 fps
Template note: default 20 steps; Hunyuan's "original setting" is 50 steps.
EasyCache nodes are deliberately omitted - the template warns they cost quality.
"""
import json, time, urllib.request, uuid, argparse

POS = ("A photorealistic video of an East Asian woman in her late thirties with "
       "shoulder-length black hair, framed head-and-shoulders with her face centered, "
       "speaking casually to the camera with natural blinking and an occasional smile. "
       "Modern office with a softly blurred background, soft natural window light. "
       "Static camera with slight natural handheld sway. Single person in frame.")
NEG = "deformed face, multiple people, text, watermark, cartoon, low quality, blurry"


def build(w, h, length, seed, steps=20, cfg=6.0, shift=7.0, fps=24,
          te="qwen_2.5_vl_7b.safetensors", prefix="bench/hy15"):
    return {
      "1": {"class_type": "DualCLIPLoader",
            "inputs": {"clip_name1": te, "clip_name2": "byt5_small_glyphxl_fp16.safetensors",
                       "type": "hunyuan_video_15", "device": "default"}},
      "2": {"class_type": "UNETLoader",
            "inputs": {"unet_name": "hunyuanvideo1.5_720p_t2v_fp16.safetensors",
                       "weight_dtype": "default"}},
      "3": {"class_type": "VAELoader",
            "inputs": {"vae_name": "hunyuanvideo15_vae_fp16.safetensors"}},
      "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": POS}},
      "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": NEG}},
      "6": {"class_type": "EmptyHunyuanVideo15Latent",
            "inputs": {"width": w, "height": h, "length": length, "batch_size": 1}},
      "7": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["2", 0], "shift": shift}},
      "8": {"class_type": "BasicScheduler",
            "inputs": {"model": ["7", 0], "scheduler": "simple", "steps": steps, "denoise": 1.0}},
      "9": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
      "10": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
      "11": {"class_type": "CFGGuider",
             "inputs": {"model": ["7", 0], "positive": ["4", 0], "negative": ["5", 0], "cfg": cfg}},
      "12": {"class_type": "SamplerCustomAdvanced",
             "inputs": {"noise": ["9", 0], "guider": ["11", 0], "sampler": ["10", 0],
                        "sigmas": ["8", 0], "latent_image": ["6", 0]}},
      "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["3", 0]}},
      "14": {"class_type": "CreateVideo", "inputs": {"images": ["13", 0], "fps": fps}},
      "15": {"class_type": "SaveVideo",
             "inputs": {"video": ["14", 0], "filename_prefix": prefix,
                        "format": "auto", "codec": "h264"}},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1:8189")
    ap.add_argument("--configs", required=True, help="label,steps,cfg,w,h,len ; ...")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    def post(p, d):
        r = urllib.request.Request(f"http://{a.host}{p}", data=json.dumps(d).encode(),
                                   headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(r, timeout=60).read())

    def get(p):
        return json.loads(urllib.request.urlopen(f"http://{a.host}{p}", timeout=60).read())

    res = []
    for c in a.configs.split(";"):
        if not c.strip():
            continue
        lab, steps, cfg, w, h, ln = c.split(",")
        g = build(int(w), int(h), int(ln), 771234, steps=int(steps), cfg=float(cfg),
                  prefix=f"bench/{lab}")
        t0 = time.time()
        pid = post("/prompt", {"prompt": g, "client_id": str(uuid.uuid4())})["prompt_id"]
        print(f"[{lab}] submitted {pid}", flush=True)
        while True:
            h_ = get(f"/history/{pid}")
            if pid in h_:
                st = h_[pid].get("status", {}); dt = time.time() - t0
                ok = st.get("status_str") != "error"
                if not ok:
                    for m in st.get("messages", []):
                        if m and m[0] == "execution_error":
                            print(f"[{lab}] ERROR node={m[1].get('node_type')} "
                                  f"{str(m[1].get('exception_message'))[:400]}", flush=True)
                print(f"[{lab}] {'OK' if ok else 'FAIL'} {dt:.1f}s", flush=True)
                res.append({"label": lab, "ok": ok, "seconds": dt, "steps": int(steps),
                            "cfg": float(cfg), "w": int(w), "h": int(h), "len": int(ln)})
                break
            if time.time() - t0 > 21600:
                print(f"[{lab}] TIMEOUT", flush=True)
                res.append({"label": lab, "ok": False, "seconds": time.time() - t0})
                break
            time.sleep(3)
    print(json.dumps(res, indent=2))
    if a.out:
        json.dump(res, open(a.out, "w"), indent=2)


if __name__ == "__main__":
    main()
