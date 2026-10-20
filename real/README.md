# Real half

The synthetic half of FairDeep-Fake Bench is 3,936 QC-passing clips at 1280x704,
one subject, head-and-shoulders, balanced over 56 FairFace-compatible cells. This
directory builds the real half it gets scored against.

The point is *comparability* on the properties a detector could cheat with. A
real set that differs from the synthetic set in resolution, framing or subject
count is not a control - a detector separates the halves on those and never
looks at a face. So these scripts do not only accept or reject real footage,
they conform it to the synthetic spec on those axes and record every conformance
applied.

## What is matched, and what is not

From the 3,936 passing synthetic clips (`manifests/qc_report_*.csv`):

| property | synthetic | real |
|---|---|---|
| resolution | 1280x704 | cropped + scaled to 1280x704 |
| face height / frame height | p10 0.54, med 0.68, p90 0.80 | crop solves for 0.68 |
| face centre x | p10 0.36, med 0.49, p90 0.57 | face centred |
| subjects | exactly one (YuNet gate) | same gate, same thresholds |
| length | 6.04 s (LTX, Hunyuan) / 6.06 s (Wan) | **not matched** - whole clean run kept |
| sharpness | - | **not gated** - blur is kept |
| brightness | black frames only (`qc/scan.py`) | black frames only |
| fps | 24 (LTX, Hunyuan), 16 (Wan) | **left at source rate** |

- **Length is not matched.** 6.04 s was a generation rule. Comparisons are run
  at several clip lengths, so each real clip keeps its longest clean run (at
  least `--min-dur`, default 2 s) and analysis trims it to whatever a comparison
  needs. `--max-dur` caps it if storage matters.
- **Blur is kept.** It is a property of real footage, not a defect. CelebV-HQ's
  own `blurry` flag is carried into the manifest for analysis but not used as a
  gate; `--min-sharpness` exists for a strict subset and is off by default.
- **Brightness is gated only against black frames**, exactly as `qc/scan.py`
  gates the synthetic half. The synthetic lighting bank deliberately includes
  low-light and backlit scenes; dropping dim real clips would remove the
  lighting x skin-tone conditions the benchmark exists to probe.
- **fps is not resampled.** P0 section 5.1 settled this for the generators -
  resampling introduces its own detectable artifacts - so fps is a declared
  per-source property. Report it.
- **Upscaling is allowed** up to `--max-upscale` (default 2.0). A 1280x720
  source typically needs 1.5-1.8x. `upscale` is a column in the report; pass
  `--max-upscale 1.3` for a strict subset, or 1.0 to forbid it.

The single-face gate imports its thresholds directly from `qc/faces.py`, so both
halves are judged by one detector at one calibration.

## Pipeline

```bash
# 0. metadata index (19 MB, 35,666 clips)
curl -LO https://raw.githubusercontent.com/CelebV-HQ/CelebV-HQ/main/celebvhq_info.json

# 1. ordered download manifest
python real/plan_pool.py --info celebvhq_info.json --out manifests/celebvhq_pool.json

# 2. fetch segments (video only, just the annotated shot)
python real/fetch_celebvhq.py --pool manifests/celebvhq_pool.json \
    --out-root ../celebvhq_raw --limit 10000 --workers 4

# 3. conform to the synthetic spec
python real/filter_real.py --videos ../celebvhq_raw --out-root ../fairdeep-bench/real

# 4. demographics, then stratified selection
python real/label_strata.py --stage label  --clips ../fairdeep-bench/real \
    --weights <fairface res34 7-race>.pth
python real/label_strata.py --stage select --clips ../fairdeep-bench/real --per-cell 90
```

`plan_pool.py` orders by predicted scarcity, not at random. CelebV-HQ ships 40
CelebA-style flags; `male`, `young` and `gray_hair` are weak priors on two of
the three taxonomy axes, and ordering by them front-loads the clips that fill
the cells which would otherwise end up empty. Race is not annotated and cannot
be prioritised; that imbalance has to be absorbed by over-fetching. The priors
are **download order only**. Every label comes from FairFace in
`label_strata.py`.

## Measured on a live sample

Same 11 fetched segments under both rule sets:

| rules | conformed | rejections |
|---|---|---|
| 6.04 s fixed length, sharpness >= 40 | 4 / 11 (36%) | no clean 6.04 s run 3, background people 2, no face 1, too soft 1 |
| **current**: whole clean run >= 2 s, no sharpness gate | **8 / 11 (73%)** | no clean 2 s run 2, no face 1 |

Output: 1280x704, `face_frac` 0.68, lengths 3.5-20.8 s, upscale 0.98-1.83.

Budget: ~2.7 MB per fetched segment. With no length or blur exclusion the pool is
**35,664 clips, ~79 GB** for all of it. At the sampled 73% conform rate, 5,000
clips needs roughly 7,000 fetched (~19 GB) - but cell balance, not the total, is
what drives how far down the pool to go. The 73% comes from 11 clips; treat it as
an estimate.

## Cells CelebV-HQ cannot fill

This will not come out balanced, and the coverage report is the deliverable that
says so. CelebV-HQ is YouTube celebrity footage: it skews young, male and white,
and `gray_hair` - the only prior on the 60+ band, which is 14 of 56 cells - is
rare. Run `--stage select` and read `cell_coverage_real.csv` before promising a
balanced real half - then either accept unequal cells and weight in analysis, or
top up the starved cells from a second source.

## Label provenance differs between the halves

The synthetic half's demographics are *prompted and then verified*. The real
half's are *inferred only*, by FairFace, on people who never self-identified for
this dataset. Both are perceived-presentation labels, but they are not the same
kind of evidence, and a fairness result comparing them has to say so. FairFace's
own error profile - including its documented weakness on darker skin and older
faces, exactly the cells that are already scarce here - lands entirely on the
real half.

Two boundaries do not line up and are handled explicitly in `fairface.py`:

- FairFace `0-2`, `3-9`, `10-19` are **dropped**. The taxonomy starts at 18-29
  and `10-19` straddles the age of majority; no clip of a possible minor belongs
  in a deepfake benchmark, so the whole band goes rather than being split.
- FairFace `40-49` straddles the 44/45 cut between the taxonomy's `30-44` and
  `45-59`. Those clips are kept, assigned to `30-44`, and flagged
  `age_ambiguous` with the alternative band recorded, so they can be included or
  excluded at analysis time instead of being silently forced. Pass
  `--exclude-ambiguous` to drop them. In the live sample 2 of 4 labelled clips
  were `40-49`, so this is not a corner case.

## Fetching from a cluster

YouTube throttles and frequently blocks datacenter IP ranges, so `fetch_celebvhq.py`
may fail en masse on Bridges-2 or DeltaAI even though it works from a laptop.
Fetch from a residential connection and move the raw segments to the cluster, or
pass `--cookies cookies.txt`. Steps 3 and 4 have no network dependency and are
the parts worth running on a GPU node - see `slurm/filter_real.sbatch`.

Link attrition is permanent: CelebV-HQ is a 2022 release and some sources are
gone. Failures are logged with a reason and never retried, so a resumed run
spends its budget further down the pool instead of re-requesting dead videos.

## DFDC

`extract_dfdc.py` pulls only `label == "REAL"` rows out of DFDC train-part zips,
for using DFDC as the real half instead. Note the economics: DFDC is ~84% fakes,
so the full 50-part, ~472 GB train set holds only ~19,154 real clips. Its reals
are consented paid actors with deliberate demographic spread, which suits a
fairness benchmark - but per GB it is far more expensive than CelebV-HQ. Output
feeds `filter_real.py` unchanged.

## Dependencies

`yt-dlp`, `opencv-python`, `torch`, `torchvision`, `numpy`, and an ffmpeg binary
(`imageio-ffmpeg` supplies one). FairFace weights are the ResNet-34 7-race
checkpoint (`res34_fair_align_multi_7`, an 18-wide head: 7 race + 2 gender +
9 age). `fairface.py` checks that head width at load and refuses a 4-race
checkpoint rather than mis-slicing its logits.
