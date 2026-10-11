#!/usr/bin/env python
"""FairDeep-Fake batch driver.

Drives ComfyUI headlessly over its HTTP API. One worker thread per ComfyUI
server (one server per GPU), pulling from a shared queue of prompt specs.

Guarantees
  - idempotent by prompt_id: an existing output file means skip (crash-safe resume)
  - every attempt appended to manifests/generation_log.jsonl, successes and failures
  - each clip gets a sidecar .json = full spec + generation record + provenance
  - ComfyUI core is never modified

Usage
  python run_batch.py --matrix ../manifests/prompt_matrix_ltx23.json \
      --hosts 127.0.0.1:8188,127.0.0.1:8189,127.0.0.1:8190,127.0.0.1:8192 \
      --out-root ../../fairdeep-bench/synthetic --steps 20 --cfg 3.0 [--limit N]
      [--only-ids id1,id2] [--dry-run]
"""
import argparse, hashlib, json, os, queue, shutil, sys, threading, time
import urllib.request, urllib.error, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(ROOT, "workflows"), os.path.join(ROOT, "renderers")]

import ltx23_graph                      # noqa: E402
import ltx23 as ltx23_renderer          # noqa: E402

# ComfyUI checkout location; override per cluster with FAIRDEEP_COMFY_ROOT or --comfy-root
COMFY_ROOT = os.environ.get("FAIRDEEP_COMFY_ROOT",
                            os.path.join(os.path.dirname(ROOT), "ComfyUI"))
RENDERERS = {"ltx23": ltx23_renderer.render}
GRAPHS = {"ltx23": ltx23_graph.build}

_log_lock = threading.Lock()
_hash_cache = {}


def sha256_head(path, nbytes=64 << 20):
    """Hash first 64 MiB - full hash of a 43 GiB checkpoint is not worth the I/O."""
    if path in _hash_cache:
        return _hash_cache[path]
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            h.update(fh.read(nbytes))
        v = f"sha256head64m:{h.hexdigest()}"
    except OSError:
        v = None
    _hash_cache[path] = v
    return v


def http_json(url, payload=None, timeout=120):
    if payload is None:
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def log_line(log_path, rec):
    with _log_lock:
        with open(log_path, "a") as fh:
            fh.write(json.dumps(rec) + "\n")


def cell_dir(spec):
    d = spec["demographic"]
    return f"{d['race']}_{d['gender']}_{d['age_band']}"


def out_paths(root, spec):
    base = os.path.join(root, spec["model"], cell_dir(spec))
    return os.path.join(base, spec["prompt_id"] + ".mp4"), \
           os.path.join(base, spec["prompt_id"] + ".json")


def worker(host, q, args, log_path, stats, provenance):
    render = RENDERERS[args.model]
    build = GRAPHS[args.model]
    while True:
        try:
            spec = q.get_nowait()
        except queue.Empty:
            return
        pid = spec["prompt_id"]
        mp4_path, json_path = out_paths(args.out_root, spec)
        if os.path.exists(mp4_path):
            stats["skipped"] += 1
            q.task_done()
            continue

        pos, neg = render(spec)
        graph = build(pos, neg, spec["width"], spec["height"], spec["length"],
                      spec["seed"], steps=args.steps, cfg=args.cfg,
                      fps=spec["fps"], prefix=f"fairdeep/{args.model}/{pid}")
        t0 = time.time()
        rec = {"prompt_id": pid, "cell": spec["cell"], "host": host,
               "group": spec["counterfactual_group"], "seed": spec["seed"],
               "steps": args.steps, "cfg": args.cfg,
               "length": spec["length"], "fps": spec["fps"],
               "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0))}
        try:
            r = http_json(f"http://{host}/prompt",
                          {"prompt": graph, "client_id": str(uuid.uuid4())})
            comfy_id = r["prompt_id"]
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode()[:600]
            except Exception:
                pass
            rec.update(ok=False, error=f"submit HTTP {e.code}: {body}",
                       seconds=round(time.time() - t0, 1))
            log_line(log_path, rec); stats["failed"] += 1; q.task_done(); continue
        except Exception as e:
            rec.update(ok=False, error=f"submit: {e}", seconds=round(time.time()-t0, 1))
            log_line(log_path, rec); stats["failed"] += 1; q.task_done(); continue

        produced, err = None, None
        while True:
            if time.time() - t0 > args.clip_timeout:
                err = f"timeout after {args.clip_timeout}s"
                break
            try:
                hist = http_json(f"http://{host}/history/{comfy_id}")
            except Exception:
                time.sleep(3); continue
            if comfy_id not in hist:
                time.sleep(3); continue
            entry = hist[comfy_id]
            st = entry.get("status", {})
            if st.get("status_str") == "error":
                for m in st.get("messages", []):
                    if m and m[0] == "execution_error":
                        err = (f"{m[1].get('node_type')}: "
                               f"{str(m[1].get('exception_message'))[:300]}")
                err = err or "execution_error"
                break
            for o in entry.get("outputs", {}).values():
                for k in ("videos", "gifs", "images"):
                    for f in o.get(k, []) or []:
                        produced = f
            if produced is None:
                err = "completed but produced no video output"
            break

        dt = round(time.time() - t0, 1)
        if err or not produced:
            rec.update(ok=False, error=err or "no output", seconds=dt)
            log_line(log_path, rec); stats["failed"] += 1; q.task_done(); continue

        src = os.path.join(args.comfy_root, "output", produced.get("subfolder", ""),
                           produced["filename"])
        os.makedirs(os.path.dirname(mp4_path), exist_ok=True)
        try:
            shutil.move(src, mp4_path)
        except OSError as e:
            rec.update(ok=False, error=f"move {src}: {e}", seconds=dt)
            log_line(log_path, rec); stats["failed"] += 1; q.task_done(); continue

        sidecar = dict(spec)
        sidecar["prompt_rendered"] = {"positive": pos, "negative": neg}
        sidecar["generation"] = {
            "steps": args.steps, "cfg": args.cfg, "sampler": "euler",
            "scheduler": "simple", "wall_seconds": dt, "host": host,
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **provenance,
        }
        sidecar["provenance"] = {
            "ai_generated": True,
            "synthetic_identity": True,
            "real_person_depicted": False,
            "project": "FairDeep-Fake Bench",
            "purpose": "deepfake detector fairness evaluation (research only)",
        }
        sidecar["qc"] = {"status": "pending"}
        json.dump(sidecar, open(json_path, "w"), indent=1)

        rec.update(ok=True, seconds=dt, output=os.path.relpath(mp4_path, args.out_root))
        log_line(log_path, rec)
        stats["done"] += 1
        n = stats["done"] + stats["failed"]
        if n % 10 == 0 or args.verbose:
            print(f"  [{n}] {pid} {dt}s ({host})", flush=True)
        q.task_done()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--model", default="ltx23")
    ap.add_argument("--hosts", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--cfg", type=float, default=3.0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only-ids", default=None)
    ap.add_argument("--clip-timeout", type=int, default=3600)
    ap.add_argument("--log", default=None)
    ap.add_argument("--comfy-root", default=COMFY_ROOT,
                    help="ComfyUI checkout whose output/ and models/ the servers use")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    specs = json.load(open(args.matrix))
    if args.only_ids:
        want = set(args.only_ids.split(","))
        specs = [s for s in specs if s["prompt_id"] in want]
    if args.limit:
        specs = specs[:args.limit]

    args.out_root = os.path.abspath(args.out_root)
    args.comfy_root = os.path.abspath(args.comfy_root)
    log_path = args.log or os.path.join(ROOT, "manifests", "generation_log.jsonl")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    if args.dry_run:
        render = RENDERERS[args.model]
        for s in specs:
            pos, neg = render(s)
            print(f"\n=== {s['prompt_id']}  (cell {s['cell']}, group "
                  f"{s['counterfactual_group']}, seed {s['seed']}, "
                  f"{s['length']}f/{s['duration_s']}s)\n{pos}")
        print(f"\n[dry-run] {len(specs)} specs, nothing submitted")
        return

    hosts = args.hosts.split(",")
    mdir = os.path.join(args.comfy_root, "models")
    provenance = {
        "comfyui_version": "0.30.0",
        "checkpoint": ltx23_graph.CKPT,
        "checkpoint_hash": sha256_head(os.path.join(mdir, "checkpoints",
                                                    ltx23_graph.CKPT)),
        "text_encoder": ltx23_graph.GEMMA,
        "precision": "bf16",
    }

    q = queue.Queue()
    for s in specs:
        q.put(s)
    stats = {"done": 0, "failed": 0, "skipped": 0}
    print(f"{len(specs)} specs -> {len(hosts)} workers "
          f"(steps={args.steps} cfg={args.cfg}) -> {args.out_root}", flush=True)

    t0 = time.time()
    threads = [threading.Thread(target=worker,
                                args=(h, q, args, log_path, stats, provenance),
                                daemon=True) for h in hosts]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    el = time.time() - t0
    print(f"\ndone={stats['done']} failed={stats['failed']} "
          f"skipped={stats['skipped']} in {el/60:.1f} min")
    if stats["done"]:
        print(f"mean {el/stats['done']:.1f}s/clip wall "
              f"({el/stats['done']*len(hosts):.1f}s/clip per GPU)")
    print(f"log: {log_path}")


if __name__ == "__main__":
    main()
