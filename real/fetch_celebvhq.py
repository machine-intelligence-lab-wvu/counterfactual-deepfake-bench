"""Fetch CelebV-HQ segments from YouTube, in the order plan_pool.py chose.

Only the annotated shot is pulled, via yt-dlp's `--download-sections`, and only
the video stream. A 1080p segment of ~5 s costs about 1.5 MB that way; fetching
whole source videos instead would cost two orders of magnitude more for footage
that is then thrown away. None of the generators except LTX produce audio, and
the real half is never scored on audio, so the audio stream is skipped too.

Dead links are expected: CelebV-HQ was published in 2022 and YouTube attrition
is permanent. Failures are recorded with their reason and never retried blindly,
so a resumed run does not spend its budget re-requesting videos that are gone.

    python real/fetch_celebvhq.py --pool manifests/celebvhq_pool.json \
        --out-root ../celebvhq_raw --limit 8000 --workers 4
"""
import argparse, json, os, shutil, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

LOCK = threading.Lock()

MIN_BYTES = 10_000   # a real segment is >=100 KB; yt-dlp can leave a stub on failure

# Failures that will never succeed on retry. Everything else - timeouts, ffmpeg
# crashes, HTTP 403/429 - is transient and is retried on the next run.
PERMANENT = ("private video", "video unavailable", "has been removed",
             "account associated with this video", "terminated", "copyright",
             "not available in your country", "members-only", "is no longer available",
             "confirm your age")

# YouTube's datacenter-IP block. Not permanent: the same clip fetches fine from
# a residential IP or with --cookies, so it must never blacklist the clip.
BOT_CHECK = "not a bot"

MAX_ATTEMPTS = 3     # a transient failure that repeats this often is treated as dead


def is_permanent(reason):
    r = (reason or "").lower()
    return BOT_CHECK not in r and any(k in r for k in PERMANENT)


def invalid(path):
    """Reason a fetched file is unusable, or None. Catches stub outputs that a
    zero-exit yt-dlp run can still leave behind."""
    n = path.stat().st_size
    if n < MIN_BYTES:
        return f"empty output ({n} bytes)"
    import cv2
    cap = cv2.VideoCapture(str(path))
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) if cap.isOpened() else 0
    cap.release()
    return None if frames > 0 else "no decodable frames"

# 137 = 1080p h264 video-only. The fallbacks step down rather than fail, because
# plenty of older CelebV-HQ sources top out below 1080p; filter_real.py gates on
# the resulting face size anyway, so a small source is rejected there on the
# evidence instead of being guessed at here.
FORMAT = ("bv*[height<=1080][ext=mp4]/bv*[height<=1080]/"
          "bv*[height<=720][ext=mp4]/bv*[height<=720]/bv*")


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def js_runtime():
    """yt-dlp now needs a JavaScript runtime to solve YouTube's player
    challenges; without one it warns and some formats go missing. It finds deno
    on its own, so pass nothing then; otherwise fall back to node."""
    if shutil.which("deno"):
        return None
    return "node" if shutil.which("node") else None


def log_line(path, rec):
    with LOCK:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")


def fetch_one(rec, out_root, log_path, ff, timeout, cookies, js):
    dest = Path(out_root) / f"{rec['clip_id']}.mp4"
    if dest.exists() and dest.stat().st_size >= MIN_BYTES:
        return "skip"

    tmp = Path(out_root) / f"_{rec['clip_id']}"
    cmd = [sys.executable, "-m", "yt_dlp",
           "-f", FORMAT,
           "--download-sections", f"*{rec['start_sec']}-{rec['end_sec']}",
           "--force-keyframes-at-cuts",
           "-o", f"{tmp}.%(ext)s",
           "--no-playlist", "--no-warnings", "--quiet",
           "--no-progress", "--retries", "2", "--socket-timeout", "30",
           f"https://www.youtube.com/watch?v={rec['ytb_id']}"]
    # insert after "-m yt_dlp", never between them
    if ff:
        cmd[3:3] = ["--ffmpeg-location", ff]
    if cookies:
        cmd[3:3] = ["--cookies", cookies]
    if js:
        cmd[3:3] = ["--js-runtimes", js]

    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        log_line(log_path, {"clip_id": rec["clip_id"], "ytb_id": rec["ytb_id"],
                            "ok": False, "reason": "timeout"})
        return "fail"

    produced = sorted(Path(out_root).glob(f"_{rec['clip_id']}.*"))
    if p.returncode != 0 or not produced:
        err = (p.stderr or "").strip().splitlines()
        reason = err[-1][:200] if err else f"exit {p.returncode}"
        for q in produced:
            q.unlink(missing_ok=True)
        log_line(log_path, {"clip_id": rec["clip_id"], "ytb_id": rec["ytb_id"],
                            "ok": False, "reason": reason})
        return "bot" if BOT_CHECK in reason.lower() else "fail"

    produced[0].replace(dest)
    for q in produced[1:]:
        q.unlink(missing_ok=True)
    bad = invalid(dest)
    if bad:
        dest.unlink(missing_ok=True)
        log_line(log_path, {"clip_id": rec["clip_id"], "ytb_id": rec["ytb_id"],
                            "ok": False, "reason": bad})
        return "fail"
    log_line(log_path, {"clip_id": rec["clip_id"], "ytb_id": rec["ytb_id"], "ok": True,
                        "bytes": dest.stat().st_size, "seconds": round(time.time() - t0, 1)})
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", required=True, help="output of plan_pool.py")
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--limit", type=int, default=0, help="0 = whole pool")
    ap.add_argument("--workers", type=int, default=4,
                    help="keep this modest; YouTube throttles aggressive parallelism")
    ap.add_argument("--timeout", type=int, default=60,
                    help="per clip; healthy fetches took 3-21 s in testing, a hung one never finishes")
    ap.add_argument("--cookies", default=None,
                    help="cookies.txt, if age-gated sources need to be reachable")
    ap.add_argument("--max-gb", type=float, default=0.0, help="stop after this much data")
    ap.add_argument("--js-runtimes", default=None,
                    help="passed to yt-dlp, e.g. node or node:/path/to/node; "
                         "default: deno if installed, else node if on PATH")
    a = ap.parse_args()

    pool = json.load(open(a.pool, encoding="utf-8"))["clips"]
    if a.limit:
        pool = pool[:a.limit]
    out_root = Path(a.out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    log_path = out_root / "fetch_log.jsonl"

    # Never re-request a link that is permanently gone (private, removed, ...):
    # that attrition does not heal. Transient failures are retried, up to
    # MAX_ATTEMPTS - some segments hang on every attempt, and each hang costs a
    # full --timeout. Bot-check failures never count: they say nothing about the
    # clip, only about the IP.
    seen_fail, attempts = set(), {}
    if log_path.exists():
        for line in open(log_path, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("ok"):
                continue
            cid, reason = r.get("clip_id"), r.get("reason") or ""
            if is_permanent(reason):
                seen_fail.add(cid)
            elif BOT_CHECK not in reason.lower():
                attempts[cid] = attempts.get(cid, 0) + 1
                if attempts[cid] >= MAX_ATTEMPTS:
                    seen_fail.add(cid)
    pool = [r for r in pool if r["clip_id"] not in seen_fail]

    ff = ffmpeg_exe()
    js = a.js_runtimes or js_runtime()
    if not js and not shutil.which("deno"):
        print("  ! no JavaScript runtime (deno or node) found - yt-dlp will warn and "
              "may miss formats. Install deno: curl -fsSL https://deno.land/install.sh | sh",
              flush=True)
    print(f"fetching up to {len(pool)} segments -> {out_root} "
          f"({a.workers} workers, ffmpeg={'bundled' if ff else 'system'}, "
          f"js={js or ('deno' if shutil.which('deno') else 'none')})")

    stats = {"ok": 0, "fail": 0, "skip": 0, "bot": 0}
    stop = threading.Event()

    def work(rec):
        if stop.is_set():
            return
        r = fetch_one(rec, out_root, log_path, ff, a.timeout, a.cookies, js)
        with LOCK:
            stats[r] += 1
            if r == "bot" and stats["bot"] == 1:
                print("  ! YouTube is asking this IP to prove it is not a bot - the usual "
                      "block on datacenter/cluster IPs. Pass --cookies cookies.txt "
                      "(exported from a logged-in browser) or fetch from a residential "
                      "connection. These clips are NOT blacklisted and will retry.",
                      flush=True)
            n = sum(stats.values())
            if n % 25 == 0:
                gb = sum(f.stat().st_size for f in out_root.glob("*.mp4")) / 1e9
                print(f"  {n}/{len(pool)}  ok={stats['ok']} fail={stats['fail']} "
                      f"bot={stats['bot']} skip={stats['skip']}  {gb:.1f} GB", flush=True)
                if a.max_gb and gb >= a.max_gb:
                    print(f"  reached --max-gb {a.max_gb}, stopping")
                    stop.set()

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(work, pool))

    gb = sum(f.stat().st_size for f in out_root.glob("*.mp4")) / 1e9
    print(f"\ndone: ok={stats['ok']} fail={stats['fail']} bot={stats['bot']} "
          f"skip={stats['skip']}  {gb:.2f} GB")
    if stats["bot"] and stats["bot"] >= stats["ok"]:
        print("most requests hit YouTube's bot check: see the --cookies note above")
    print(f"log: {log_path}")


if __name__ == "__main__":
    main()
