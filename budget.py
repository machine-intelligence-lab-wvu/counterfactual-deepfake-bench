#!/usr/bin/env python
"""Budget solver: fit 5,750 clips across 3 generators into a 15-day / 4-GPU window."""

DAYS, GPUS = 15, 4
GPU_H = DAYS * 24 * GPUS                 # raw capacity
RESERVE = 0.15                           # QC, restarts, regen, ±12% timing variance
USABLE_S = GPU_H * 3600 * (1 - RESERVE)
CLIPS = 5750
CELLS = 56

# measured seconds/clip at 1280x704-720, 5s, full precision, reference sampling
FULL = {"wan": 1628.3, "hunyuan": 1447.3, "ltx": 198.3}
# Wan with 4-step lightx2v LoRA at fp16 (mean of 3 replicates: 177.2/192.2/189.3)
WAN_4STEP = 186.2

print(f"capacity: {GPU_H} GPU-h raw | usable after {RESERVE:.0%} reserve: "
      f"{USABLE_S/3600:.0f} GPU-h ({USABLE_S:,.0f} GPU-s)\n")


def report(name, alloc, cost):
    tot = sum(alloc[m] * cost[m] for m in alloc)
    print(f"--- {name}")
    for m in alloc:
        print(f"    {m:9s} n={alloc[m]:5d}  {cost[m]:7.1f}s/clip  "
              f"{alloc[m]*cost[m]/3600:7.0f} GPU-h  {alloc[m]/CELLS:5.1f} raw/cell")
    days = tot / 3600 / GPUS / 24
    verdict = "FITS" if tot <= USABLE_S else f"OVER by {tot/USABLE_S-1:.0%}"
    print(f"    TOTAL {tot/3600:.0f} GPU-h = {days:.1f} days on {GPUS} GPUs  -> {verdict}\n")
    return tot


# A: equal split, everything at full reference quality
eq = CLIPS // 3
report("A: equal split, full quality", {"wan": eq, "hunyuan": eq, "ltx": CLIPS - 2 * eq}, FULL)

# B: full quality, cost-weighted allocation (Wan=Hunyuan=x, LTX absorbs remainder)
# 1628.3x + 1447.3x + 198.3(CLIPS-2x) = USABLE_S
num = USABLE_S - FULL["ltx"] * CLIPS
den = FULL["wan"] + FULL["hunyuan"] - 2 * FULL["ltx"]
x = int(num / den)
report("B: full quality, cost-weighted N per model",
       {"wan": x, "hunyuan": x, "ltx": CLIPS - 2 * x}, FULL)

# C: Wan on 4-step LoRA (fp16 weights), others full
report("C: Wan 4-step LoRA, others full quality",
       {"wan": eq, "hunyuan": eq, "ltx": CLIPS - 2 * eq},
       {**FULL, "wan": WAN_4STEP})

# D: equal split at full quality, trim total clips to fit
avg = sum(FULL.values()) / 3
n_fit = int(USABLE_S / avg)
print(f"--- D: equal split full quality, trim total")
print(f"    max raw clips that fit: {n_fit:,} ({n_fit/CLIPS-1:+.0%} vs target)")
print(f"    ~{int(n_fit*0.85):,} accepted after 15% QC loss  "
      f"({n_fit/3/CELLS:.1f} raw/cell/model)\n")

# How many days would scenario A actually need?
totA = sum(eq * FULL[m] for m in ("wan", "hunyuan")) + (CLIPS - 2 * eq) * FULL["ltx"]
print(f"scenario A needs {totA/3600/GPUS/24:.1f} days of pure compute, or "
      f"{totA/3600/GPUS/24/(1-RESERVE):.1f} days with the {RESERVE:.0%} reserve "
      f"(vs {DAYS} available)")
print(f"scenario B per-cell after 15% QC loss: "
      f"{x/CELLS*0.85:.1f} accepted/cell for Wan & Hunyuan, "
      f"{(CLIPS-2*x)/CELLS*0.85:.1f} for LTX")
print(f"scenario B total accepted per intersectional cell (all models): "
      f"{CLIPS/CELLS*0.85:.1f}")
