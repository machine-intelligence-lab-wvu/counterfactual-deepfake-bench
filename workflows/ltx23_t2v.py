#!/usr/bin/env python
"""LTX 2.3 (22B dev, bf16) audio-video T2V throughput bench.

LTX 2.3 is an AV model: the sampled latent is a concatenation of video + audio
latents, split again after sampling. Graph follows the bundled
`video_ltx2_3_t2v.json` single-stage path (no spatial upscaler stage), using the
non-distilled `dev` checkpoint with standard N-step sampling for full quality.

NOTE: bf16 dev is a ~43 GiB checkpoint. On a 48.9 GiB card this may OOM at 720p;
the bench reports that outcome rather than silently degrading.
"""
import json, time, urllib.request, uuid, argparse

CKPT = "ltx-2.3-22b-dev.safetensors"
GEMMA = "gemma_3_12B_it.safetensors"
POS = ("A photorealistic video of an East Asian woman in her late thirties with "
       "shoulder-length black hair, framed head-and-shoulders with her face centered, "
       "speaking casually to the camera with natural blinking and an occasional smile. "
       "Modern office with a softly blurred background, soft natural window light. "
       "Static camera with slight natural handheld sway. Single person in frame.")
NEG = "pc game, console game, video game, cartoon, childish, ugly"


def build(w, h, length, seed, steps=30, cfg=1.0, fps=24, audio_fps=25,
          with_audio=True, prefix="bench/ltx23"):
    g = {
      "1":  {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
      "2":  {"class_type": "LTXAVTextEncoderLoader",
             "inputs": {"text_encoder": GEMMA, "ckpt_name": CKPT, "device": "default"}},
      "4":  {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": POS}},
      "5":  {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": NEG}},
      "6":  {"class_type": "LTXVConditioning",
             "inputs": {"positive": ["4", 0], "negative": ["5", 0], "frame_rate": float(fps)}},
      "7":  {"class_type": "EmptyLTXVLatentVideo",
             "inputs": {"width": w, "height": h, "length": length, "batch_size": 1}},
      "10": {"class_type": "BasicScheduler",
             "inputs": {"model": ["1", 0], "scheduler": "simple",
                        "steps": steps, "denoise": 1.0}},
      "11": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
      "12": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
      "13": {"class_type": "CFGGuider",
             "inputs": {"model": ["1", 0], "positive": ["6", 0], "negative": ["6", 1],
                        "cfg": cfg}},
    }
    if with_audio:
        # AV path: concat video+audio latents, sample jointly, then split
        g["3"] = {"class_type": "LTXVAudioVAELoader", "inputs": {"ckpt_name": CKPT}}
        g["8"] = {"class_type": "LTXVEmptyLatentAudio",
                  "inputs": {"frames_number": length, "frame_rate": float(audio_fps),
                             "batch_size": 1, "audio_vae": ["3", 0]}}
        g["9"] = {"class_type": "LTXVConcatAVLatent",
                  "inputs": {"video_latent": ["7", 0], "audio_latent": ["8", 0]}}
        sampler_latent = ["9", 0]
    else:
        sampler_latent = ["7", 0]

    g["14"] = {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["11", 0], "guider": ["13", 0], "sampler": ["12", 0],
                          "sigmas": ["10", 0], "latent_image": sampler_latent}}
    if with_audio:
        g["15"] = {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["14", 0]}}
        g["16"] = {"class_type": "VAEDecode",
                   "inputs": {"samples": ["15", 0], "vae": ["1", 2]}}
        g["17"] = {"class_type": "LTXVAudioVAEDecode",
                   "inputs": {"samples": ["15", 1], "audio_vae": ["3", 0]}}
        g["18"] = {"class_type": "CreateVideo",
                   "inputs": {"images": ["16", 0], "fps": float(fps), "audio": ["17", 0]}}
    else:
        g["16"] = {"class_type": "VAEDecode",
                   "inputs": {"samples": ["14", 0], "vae": ["1", 2]}}
        g["18"] = {"class_type": "CreateVideo",
                   "inputs": {"images": ["16", 0], "fps": float(fps)}}
    g["19"] = {"class_type": "SaveVideo",
               "inputs": {"video": ["18", 0], "filename_prefix": prefix,
                          "format": "auto", "codec": "h264"}}
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1:8192")
    ap.add_argument("--configs", required=True,
                    help="label,steps,cfg,w,h,len,audio(0|1) ; ...")
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
        lab, steps, cfg, w, h, ln, aud = c.split(",")
        g = build(int(w), int(h), int(ln), 771234, steps=int(steps), cfg=float(cfg),
                  with_audio=(aud == "1"), prefix=f"bench/{lab}")
        t0 = time.time()
        try:
            pid = post("/prompt", {"prompt": g, "client_id": str(uuid.uuid4())})["prompt_id"]
        except Exception as e:
            body = ""
            if hasattr(e, "read"):
                try:
                    body = e.read().decode()[:800]
                except Exception:
                    pass
            print(f"[{lab}] SUBMIT-REJECTED {e} {body}", flush=True)
            res.append({"label": lab, "ok": False, "seconds": 0, "error": f"{e} {body}"})
            continue
        print(f"[{lab}] submitted {pid}", flush=True)
        while True:
            hh = get(f"/history/{pid}")
            if pid in hh:
                st = hh[pid].get("status", {}); dt = time.time() - t0
                ok = st.get("status_str") != "error"
                err = None
                if not ok:
                    for m in st.get("messages", []):
                        if m and m[0] == "execution_error":
                            err = f"{m[1].get('node_type')}: {str(m[1].get('exception_message'))[:400]}"
                            print(f"[{lab}] ERROR {err}", flush=True)
                print(f"[{lab}] {'OK' if ok else 'FAIL'} {dt:.1f}s", flush=True)
                res.append({"label": lab, "ok": ok, "seconds": dt, "steps": int(steps),
                            "w": int(w), "h": int(h), "len": int(ln),
                            "audio": aud == "1", "error": err})
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
