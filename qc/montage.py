#!/usr/bin/env python
"""Build a labelled review montage from generated clips.

One row per clip: 4 frames sampled across the clip, captioned with the intended
demographic cell and lighting condition so prompt compliance can be eyeballed
before committing GPU time to a full run.
"""
import argparse, glob, json, os
import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def strip(path, n_frames=4, tile_w=320):
    c = av.open(path)
    vs = c.streams.video[0]
    fr = [f.to_ndarray(format="rgb24") for f in c.decode(video=0)]
    has_audio = any(s.type == "audio" for s in c.streams)
    n = len(fr)
    idx = [int(i * (n - 1) / (n_frames - 1)) for i in range(n_frames)]
    tiles = []
    for i in idx:
        im = Image.fromarray(fr[i])
        im = im.resize((tile_w, int(tile_w * im.height / im.width)))
        tiles.append(np.asarray(im))
    row = np.concatenate(tiles, axis=1)
    motion = float(np.mean([np.abs(fr[i].astype(int) - fr[i - 1].astype(int)).mean()
                            for i in range(1, n)]))
    return row, {"frames": n, "w": vs.width, "h": vs.height,
                 "fps": float(vs.average_rate), "audio": has_audio,
                 "motion": round(motion, 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tile-w", type=int, default=320)
    ap.add_argument("--cols", type=int, default=1)
    a = ap.parse_args()

    paths = sorted(glob.glob(os.path.join(a.root, "**", "*.mp4"), recursive=True))
    if not paths:
        raise SystemExit(f"no clips under {a.root}")

    cap_h = 30
    rows, caps = [], []
    for p in paths:
        row, meta = strip(p, tile_w=a.tile_w)
        side = os.path.splitext(p)[0] + ".json"
        cell, lit, dur = "?", "?", "?"
        if os.path.exists(side):
            s = json.load(open(side))
            d = s["demographic"]
            cell = f"{d['race']}/{d['gender']}/{d['age_band']}"
            lit = s["scene"]["lighting_key"]
            dur = f"{s['duration_s']}s"
        rows.append(row)
        caps.append(f"{cell}   |   {lit}   |   {dur}  {meta['w']}x{meta['h']}"
                    f"@{meta['fps']:.0f}  motion {meta['motion']}"
                    f"{'  +audio' if meta['audio'] else ''}")

    w = max(r.shape[1] for r in rows)
    total_h = sum(r.shape[0] + cap_h for r in rows)
    sheet = Image.new("RGB", (w, total_h), (18, 18, 18))
    dr = ImageDraw.Draw(sheet)
    f = font(17)
    y = 0
    for row, cap in zip(rows, caps):
        dr.text((8, y + 7), cap, fill=(235, 235, 235), font=f)
        y += cap_h
        sheet.paste(Image.fromarray(row), (0, y))
        y += row.shape[0]
    sheet.save(a.out)
    print(f"{len(paths)} clips -> {a.out}  ({sheet.width}x{sheet.height})")
    for c in caps:
        print("  " + c)


if __name__ == "__main__":
    main()
