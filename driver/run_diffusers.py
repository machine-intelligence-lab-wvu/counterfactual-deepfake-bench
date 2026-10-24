#!/usr/bin/env python
"""DeepFake Bench batch driver for generators that run in diffusers rather than ComfyUI.

Same guarantees and outputs as run_batch.py, so a clip looks the same whichever driver made it:
  - idempotent by prompt_id: an existing output file means skip (crash-safe resume)
  - every attempt appended to the log jsonl, successes and failures
  - each clip gets a sidecar .json = full spec + generation record + provenance
  - mp4 encoded the way ComfyUI's SaveVideo encodes the other generators: PyAV h264 at libx264
    defaults (CRF 23, B-frames on), yuv420p, AAC audio at the model's sample rate

One worker process per GPU, each loading the pipeline once and taking every n-th spec.

  python run_diffusers.py --model k6pro --matrix ../manifests/prompt_matrix_k6pro.json \
      --gpus 2,3 --out-root ../../deepfake-bench-data/synthetic [--recipe native720] [--limit N]
      [--only-ids id1,id2 | --only-ids-file ids.json] [--log ../manifests/generation_log_k6pro.jsonl]

Supported models
  k6pro  Kandinsky 6.0 Pro (kandinskylab/Kandinsky-6.0-Pro-5s-Diffusers), Kandinsky6TI2VAPipeline,
         text-to-audio-video. The 29B transformer (70 GB bf16) does not fit a 48 GB GPU, so every
         component runs with block-level group offloading on CUDA streams: full bf16 weights,
         nothing quantised. Recipes: native720 (1280x704, 50 steps, guidance 5.0, the
         checkpoint's flow-matching defaults), native480 (864x480, the README's example size).
"""
import argparse, functools, hashlib, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(ROOT, "renderers")]

DEEPFAKE = os.path.dirname(ROOT)
K6 = {   # Kandinsky 6.0 checkpoints: local dir, repo, pinned revision, scheduler (checkpoint config)
    "k6pro": {"dir": os.path.join(DEEPFAKE, "models", "kandinsky6", "Kandinsky-6.0-Pro-5s-Diffusers"),
              "repo": "kandinskylab/Kandinsky-6.0-Pro-5s-Diffusers",
              "rev": "7be18aed6fbd64653c0c4872fddfe4a3e3e109f5",
              "scheduler": "FlowMatchEulerDiscreteScheduler (shift 5.0)"},
    "k6prod": {"dir": os.path.join(DEEPFAKE, "models", "kandinsky6", "Kandinsky-6.0-Pro-distill-5s-Diffusers"),
               "repo": "kandinskylab/Kandinsky-6.0-Pro-distill-5s-Diffusers",
               "rev": "80d5e6c7f646c5f512b684e2da0765618d805894",
               "scheduler": "PiflowScheduler (shift 5.0)"},
}
RECIPES = {
    "k6pro": {
        "native720": {"width": 1280, "height": 704, "steps": 50, "cfg": 5.0},
        "native480": {"width": 864, "height": 480, "steps": 50, "cfg": 5.0},
    },
    # distilled: the card's 10 steps at guidance 1.0 (Piflow requires 1.0)
    "k6prod": {
        "native720": {"width": 1280, "height": 704, "steps": 10, "cfg": 1.0},
        "native480": {"width": 864, "height": 480, "steps": 10, "cfg": 1.0},
        # 928x512 (aspect of 1280x704, short side 512) comes out letterboxed: 66 px bars top and
        # bottom on every frame, so it is not offered. 768x512 is the pipeline's default size.
        "default512": {"width": 768, "height": 512, "steps": 10, "cfg": 1.0},
    },
}


def sha256_head(path, nbytes=64 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read(nbytes))
    return h.hexdigest()


def cell_dir(spec):                             # as run_batch.cell_dir
    d = spec["demographic"]
    return f"{d['race']}_{d['gender']}_{d['age_band']}"


def out_paths(root, spec):
    base = os.path.join(root, spec["model"], cell_dir(spec))
    return os.path.join(base, spec["prompt_id"] + ".mp4"), os.path.join(base, spec["prompt_id"] + ".json")


def log_line(path, rec):
    with open(path, "a") as f:                  # one short line per write: O_APPEND keeps it whole
        f.write(json.dumps(rec) + "\n")


def encode_mp4(path, frames, fps, audio=None, sample_rate=None):
    """frames: list of PIL RGB images; audio: 1-D or (channels, samples) float in [-1, 1]."""
    import av
    import numpy as np
    out = av.open(path, mode="w")
    vs = out.add_stream("h264", rate=int(fps))
    vs.width, vs.height = frames[0].size
    vs.pix_fmt = "yuv420p"
    aus, layout = None, None
    if audio is not None:
        a = np.asarray(audio, dtype=np.float32)
        a = a[None] if a.ndim == 1 else a
        layout = {1: "mono", 2: "stereo"}.get(a.shape[0], "stereo")
        aus = out.add_stream("aac", rate=int(sample_rate), layout=layout)
    for im in frames:
        for p in vs.encode(av.VideoFrame.from_ndarray(np.asarray(im.convert("RGB")), format="rgb24")):
            out.mux(p)
    for p in vs.encode():
        out.mux(p)
    if aus is not None:
        af = av.AudioFrame.from_ndarray(np.ascontiguousarray(a), format="fltp", layout=layout)
        af.sample_rate = int(sample_rate)
        for p in aus.encode(af):
            out.mux(p)
        for p in aus.encode():
            out.mux(p)
    out.close()


# ------------------------------------------------------------------ k6pro
MEMORY = {
    "fp8": "transformer weights stored fp8 e4m3 (diffusers layerwise casting), bf16 compute; "
           "model-level CPU offload (each component whole on the GPU while it runs)",
    "group": "diffusers group offload, block_level, 1 block/group, CUDA streams; bf16",
}


def k6_load(model, device, memory):
    import torch
    from diffusers import Kandinsky6TI2VAPipeline
    pipe = Kandinsky6TI2VAPipeline.from_pretrained(K6[model]["dir"], torch_dtype=torch.bfloat16)
    if memory == "fp8":
        # 29B params: 70 GB in bf16 does not fit a 48 GB GPU, ~29 GB in fp8 does
        pipe.transformer.enable_layerwise_casting(storage_dtype=torch.float8_e4m3fn,
                                                  compute_dtype=torch.bfloat16)
        pipe.enable_model_cpu_offload(device=device)
    else:
        # streams the transformer block by block: ~51 min/clip at 864x480, ~2.7 h at 1280x704
        pipe.enable_group_offload(onload_device=torch.device(device), offload_device=torch.device("cpu"),
                                  offload_type="block_level", num_blocks_per_group=1, use_stream=True)
    pipe.vae.enable_tiling()
    pipe.set_progress_bar_config(disable=True)
    return pipe


def k6_generate(pipe, pos, neg, spec, rc, device):
    import torch
    g = torch.Generator(device=device).manual_seed(int(spec["seed"]))
    out = pipe(prompt=pos, negative_prompt=neg, height=rc["height"], width=rc["width"],
               num_frames=spec["length"], frame_rate=float(spec["fps"]),
               num_inference_steps=rc["steps"], guidance_scale=rc["cfg"], generator=g,
               sample_audio=True, expand_prompts=False)
    audio = out.audio[0]
    audio = audio.float().cpu().numpy() if hasattr(audio, "cpu") else audio
    return out.frames[0], audio, pipe.audio_sample_rate


def k6_provenance(model, recipe, memory):
    import diffusers, torch, transformers
    c = K6[model]
    t = os.path.join(c["dir"], "transformer", "diffusion_pytorch_model.safetensors")
    return {"checkpoint": f"{c['repo']}@{c['rev']}", "checkpoint_hash": sha256_head(t),
            "pipeline": "Kandinsky6TI2VAPipeline", "recipe": recipe,
            "scheduler": f"{c['scheduler']}, checkpoint config",
            "memory": memory, "offload": MEMORY[memory],
            "prompt_enhancer": False, "audio": True,
            "precision": "fp8 e4m3 weights, bf16 compute" if memory == "fp8" else "bf16",
            "diffusers": diffusers.__version__, "torch": torch.__version__, "cuda": torch.version.cuda,
            "transformers": transformers.__version__}


MODELS = {m: (functools.partial(k6_load, m), k6_generate, functools.partial(k6_provenance, m)) for m in K6}


# ------------------------------------------------------------------ worker
def worker(a):
    import importlib
    load, generate, prov_fn = MODELS[a.model]
    render = importlib.import_module(a.model).render
    rc = RECIPES[a.model][a.recipe]
    specs = select(a)[a.shard::a.nshards]
    todo = [s for s in specs if not os.path.exists(out_paths(a.out_root, s)[0])]
    host = f"{os.uname().nodename}:gpu{a.gpu}"
    print(f"[gpu{a.gpu}] {len(todo)} to generate of {len(specs)} in shard {a.shard}/{a.nshards}", flush=True)
    if not todo:
        return
    device = "cuda:0"                            # CUDA_VISIBLE_DEVICES is set per worker
    t_load = time.time()
    pipe = load(device, a.memory)
    provenance = prov_fn(a.recipe, a.memory)
    print(f"[gpu{a.gpu}] pipeline loaded in {time.time() - t_load:.0f}s", flush=True)
    done = 0
    for spec in todo:
        mp4_path, json_path = out_paths(a.out_root, spec)
        if os.path.exists(mp4_path):
            continue
        pos, neg = render(spec)
        t0 = time.time()
        rec = {"prompt_id": spec["prompt_id"], "cell": spec["cell"], "host": host,
               "group": spec["counterfactual_group"], "seed": spec["seed"], "recipe": a.recipe,
               "steps": rc["steps"], "cfg": rc["cfg"], "length": spec["length"], "fps": spec["fps"],
               "memory": a.memory,
               "width": rc["width"], "height": rc["height"],
               "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0))}
        try:
            frames, audio, sr = generate(pipe, pos, neg, spec, rc, device)
            os.makedirs(os.path.dirname(mp4_path), exist_ok=True)
            tmp = mp4_path + ".tmp.mp4"
            encode_mp4(tmp, frames, spec["fps"], audio, sr)
            os.replace(tmp, mp4_path)
        except Exception as e:
            rec.update(ok=False, error=f"{type(e).__name__}: {e}"[:600], seconds=round(time.time() - t0, 1))
            log_line(a.log, rec)
            print(f"[gpu{a.gpu}] FAILED {spec['prompt_id']}: {rec['error'][:200]}", flush=True)
            continue
        dt = round(time.time() - t0, 1)
        sidecar = dict(spec)
        sidecar.update(width=rc["width"], height=rc["height"])
        sidecar["prompt_rendered"] = {"positive": pos, "negative": neg}
        sidecar["generation"] = {"steps": rc["steps"], "cfg": rc["cfg"], "wall_seconds": dt,
                                 "host": host, "audio_sample_rate": sr,
                                 "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                 **provenance}
        sidecar["provenance"] = {"ai_generated": True, "synthetic_identity": True,
                                 "real_person_depicted": False, "project": "DeepFake Bench",
                                 "purpose": "deepfake detector evaluation by demographic subgroup (research only)"}
        sidecar["qc"] = {"status": "pending"}
        json.dump(sidecar, open(json_path, "w"), indent=1)
        rec.update(ok=True, seconds=dt, output=os.path.relpath(mp4_path, a.out_root))
        log_line(a.log, rec)
        done += 1
        print(f"[gpu{a.gpu}] [{done}/{len(todo)}] {spec['prompt_id']} {dt}s", flush=True)


def select(a):
    specs = json.load(open(a.matrix))
    bad = {s["model"] for s in specs} - {a.model}
    if bad:
        raise SystemExit(f"matrix holds models {bad}, not {a.model}")
    ids = None
    if a.only_ids:
        ids = set(a.only_ids.split(","))
    if a.only_ids_file:
        ids = set(json.load(open(a.only_ids_file)))
    if ids is not None:
        specs = [s for s in specs if s["prompt_id"] in ids]
    return specs[:a.limit] if a.limit else specs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=list(MODELS))
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--recipe", default="native720")
    ap.add_argument("--memory", default="fp8", choices=list(MEMORY))
    ap.add_argument("--gpus", default="0")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only-ids", default=None)
    ap.add_argument("--only-ids-file", default=None)
    ap.add_argument("--log", default=None)
    ap.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--gpu", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--shard", type=int, default=0, help=argparse.SUPPRESS)
    ap.add_argument("--nshards", type=int, default=1, help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.recipe not in RECIPES[a.model]:
        raise SystemExit(f"unknown recipe {a.recipe}; known: {sorted(RECIPES[a.model])}")
    a.out_root = os.path.abspath(a.out_root)
    a.log = os.path.abspath(a.log or os.path.join(ROOT, "manifests", f"generation_log_{a.model}.jsonl"))
    if a.worker:
        return worker(a)

    specs = select(a)
    gpus = a.gpus.split(",")
    print(f"{len(specs)} specs -> {len(gpus)} GPU workers ({a.model}, recipe {a.recipe}) -> {a.out_root}",
          flush=True)
    t0 = time.time()
    procs = []
    for i, g in enumerate(gpus):
        cmd = [sys.executable, os.path.abspath(__file__), "--worker", "--gpu", g, "--shard", str(i),
               "--nshards", str(len(gpus))] + [x for x in sys.argv[1:]]
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=g)
        procs.append(subprocess.Popen(cmd, env=env))
    rc = [p.wait() for p in procs]
    print(f"workers exited {rc} after {(time.time() - t0) / 60:.1f} min; log: {a.log}", flush=True)
    return max(rc)


if __name__ == "__main__":
    sys.exit(main() or 0)
