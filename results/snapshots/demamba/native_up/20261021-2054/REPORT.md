# demamba / native_up: snapshot 20261021-2054

> **Detector training data.** DeMamba weights are our own (GenVideo-100K, single-GPU adaptation of the authors' code), not an official release; the authors have published none. GenVideo-100K contains none of our generators. On GenVideo validation it flags 16.8% of real videos at 0.5.

> **Provisional threshold.** Every detection rate and flip rate below uses the detector's default threshold (0.5; sigmoid(logit) > 0.5 (training metrics and our standalone evaluator)). They will be replaced by the 5%-real-FPR threshold once reals exist (section 6.3).

## Settings

| setting           | value                                                                                  |
|:------------------|:---------------------------------------------------------------------------------------|
| detector          | demamba 1+504611ba                                                                     |
| checkpoint_sha256 | f89897c72b595aa85a524e59083919cebb0b92161d2a694a2cbffbdd8456ce17                       |
| view              | native_up (view_hash 4db0c07a46c4b8d9)                                                 |
| ffmpeg            | ffmpeg version 7.1.1 Copyright (c) 2000-2025 the FFmpeg developers                     |
| batches           | fake_b1, fake_b2, real_all                                                             |
| inclusion set     | primary (technical QC pass AND face QC pass)                                           |
| bootstrap         | 1000 resamples of whole counterfactual groups, seed 20261020, 95% percentile intervals |
| git commit        | 4e41a35865f4-dirty                                                                     |
| created           | 2026-10-21T20:55:00Z                                                                   |

Detector preprocessing on top of the view:

| field     | value                                                                                 |
|:----------|:--------------------------------------------------------------------------------------|
| source    | DeMamba Preprocess/video2frame.py + dataloader.py (val) + our standalone evaluator    |
| sampling  | every round(fps/target)-th frame, target 2 fps (>= 4 s) else ceil(8/dur); max 32 kept |
| window    | centre 8 consecutive sampled frames; zero-pad if fewer than 8                         |
| crop      | centre, trim 10% each side of the longer dimension                                    |
| resize    | [224, 224, 'cv2.INTER_LINEAR']                                                        |
| channels  | RGB                                                                                   |
| normalize | {'mean': [0.485, 0.456, 0.406], 'std': [0.229, 0.224, 0.225], 'max_pixel_value': 255} |
| model     | XCLIP_DeMamba (X-CLIP-B/16 vision, fine-tuned) + bidirectional Mamba, 1 logit         |
| score     | sigmoid(logit)                                                                        |
| precision | fp32, TF32 off                                                                        |
| weights   | Ahsanz/DeMamba-GenVideo100K@27468b8201fc55978bbce51450949345867de184                  |

## Coverage

| batch    | generator   |   clips |   primary |   rendered |   view_excluded |   render_failed |   scored |   score_failed |   included |
|:---------|:------------|--------:|----------:|-----------:|----------------:|----------------:|---------:|---------------:|-----------:|
| fake_b1  | hunyuan15   |     504 |       492 |        504 |               0 |               0 |      504 |              0 |        492 |
| fake_b1  | ltx23       |    2016 |      1878 |       2016 |               0 |               0 |     2016 |              0 |       1878 |
| fake_b1  | wan22       |    2016 |      1566 |       2016 |               0 |               0 |     2016 |              0 |       1566 |
| fake_b2  | hunyuan15   |     504 |       497 |        504 |               0 |               0 |      504 |              0 |        497 |
| real_all | real        |    2221 |      2221 |        923 |            1275 |              23 |      932 |              0 |        932 |

Reals scored: 1855. Fakes included: 4433 of 6895 scored (0 scoring failures).

## Observations

- LTX 2.3: mean score 0.986 [0.972, 0.997], median 1.000, n = 1878.
- Wan 2.2: mean score 1.000 [1.000, 1.000], median 1.000, n = 1566.
- HunyuanVideo 1.5: mean score 1.000 [0.999, 1.000], median 1.000, n = 989.
- Provisional detection rate (score >= 0.5), LTX 2.3: 99.0% [98.0, 99.9].
- Provisional detection rate (score >= 0.5), Wan 2.2: 100.0% [100.0, 100.0].
- Provisional detection rate (score >= 0.5), HunyuanVideo 1.5: 100.0% [100.0, 100.0].
- Provisional detection rate (score >= 0.5), all: 99.6% [99.2, 100.0].
- Largest race score gap: LTX 2.3 0.045 [0.012, 0.086] (black 0.998 vs east_asian 0.953).
- Largest gender score gap: LTX 2.3 0.000 [0.000, 0.006] (m 0.986 vs f 0.985).
- Largest age band score gap: LTX 2.3 0.019 [0.005, 0.039] (60+ 0.998 vs 18-29 0.979).
- Largest cell score gap: LTX 2.3 0.073 [0.032, 0.162] (mena__m__60+ 1.000 vs east_asian__f__18-29 0.927).
- Largest scene-factor gap (all generators): lighting 0.030 [0.006, 0.059] (softwindow vs lowlight).
- Largest partial eta squared: lighting 0.038, setting 0.034, behavior 0.030; residual holds 87.9% of total SS.
- CF spread, LTX 2.3: 0.032 [0.011, 0.057] over 36 groups (max 0.275).
- CF spread, Wan 2.2: 0.000 [0.000, 0.000] over 36 groups (max 0.001).
- CF spread, HunyuanVideo 1.5: 0.002 [0.000, 0.004] over 18 groups (max 0.014).
- Provisional flip rate, LTX 2.3: 13.9% of 36 groups [2.8, 25.0].
- Provisional flip rate, Wan 2.2: 0.0% of 36 groups [0.0, 0.0].
- Provisional flip rate, HunyuanVideo 1.5: 0.0% of 18 groups [0.0, 0.0].

## 6.1 Fakes only, no threshold

### Mean score by generator

| generator   |    n |   n_groups |   estimate |   ci_lo |   ci_hi |    sd |   median |   q05 |   q95 |
|:------------|-----:|-----------:|-----------:|--------:|--------:|------:|---------:|------:|------:|
| ltx23       | 1878 |         36 |      0.986 |   0.972 |   0.997 | 0.082 |        1 | 0.959 |     1 |
| wan22       | 1566 |         36 |      1     |   1     |   1     | 0     |        1 | 0.999 |     1 |
| hunyuan15   |  989 |         18 |      1     |   0.999 |   1     | 0.004 |        1 | 0.999 |     1 |
| all         | 4433 |         36 |      0.994 |   0.988 |   0.998 | 0.054 |        1 | 0.996 |     1 |

### Mean score by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:----------------|----:|-----------:|--------:|--------:|---------:|
| ltx23       | black           | 273 |      0.998 |   0.995 |   1     |        1 |
| ltx23       | east_asian      | 270 |      0.953 |   0.91  |   0.987 |        1 |
| ltx23       | indian          | 277 |      0.991 |   0.979 |   0.999 |        1 |
| ltx23       | latino          | 262 |      0.996 |   0.989 |   1     |        1 |
| ltx23       | mena            | 267 |      0.994 |   0.988 |   0.999 |        1 |
| ltx23       | southeast_asian | 271 |      0.971 |   0.943 |   0.995 |        1 |
| ltx23       | white           | 258 |      0.996 |   0.989 |   1     |        1 |
| wan22       | black           | 217 |      1     |   1     |   1     |        1 |
| wan22       | east_asian      | 226 |      1     |   0.999 |   1     |        1 |
| wan22       | indian          | 230 |      1     |   1     |   1     |        1 |
| wan22       | latino          | 219 |      1     |   1     |   1     |        1 |
| wan22       | mena            | 225 |      1     |   1     |   1     |        1 |
| wan22       | southeast_asian | 229 |      1     |   0.999 |   1     |        1 |
| wan22       | white           | 220 |      1     |   1     |   1     |        1 |
| hunyuan15   | black           | 141 |      1     |   1     |   1     |        1 |
| hunyuan15   | east_asian      | 141 |      0.998 |   0.996 |   0.999 |        1 |
| hunyuan15   | indian          | 142 |      1     |   1     |   1     |        1 |
| hunyuan15   | latino          | 142 |      1     |   1     |   1     |        1 |
| hunyuan15   | mena            | 139 |      1     |   1     |   1     |        1 |
| hunyuan15   | southeast_asian | 143 |      1     |   0.999 |   1     |        1 |
| hunyuan15   | white           | 141 |      1     |   1     |   1     |        1 |
| all         | black           | 631 |      0.999 |   0.998 |   1     |        1 |
| all         | east_asian      | 637 |      0.979 |   0.961 |   0.994 |        1 |
| all         | indian          | 649 |      0.996 |   0.991 |   1     |        1 |
| all         | latino          | 623 |      0.998 |   0.995 |   1     |        1 |
| all         | mena            | 631 |      0.998 |   0.995 |   1     |        1 |
| all         | southeast_asian | 643 |      0.988 |   0.976 |   0.998 |        1 |
| all         | white           | 619 |      0.998 |   0.995 |   1     |        1 |

### Mean score by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | f       |  931 |      0.985 |   0.972 |   0.996 |        1 |
| ltx23       | m       |  947 |      0.986 |   0.972 |   0.997 |        1 |
| wan22       | f       |  785 |      1     |   1     |   1     |        1 |
| wan22       | m       |  781 |      1     |   1     |   1     |        1 |
| hunyuan15   | f       |  495 |      1     |   1     |   1     |        1 |
| hunyuan15   | m       |  494 |      0.999 |   0.999 |   1     |        1 |
| all         | f       | 2211 |      0.994 |   0.988 |   0.998 |        1 |
| all         | m       | 2222 |      0.994 |   0.988 |   0.998 |        1 |

### Mean score by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | 18-29   |  469 |      0.979 |   0.958 |   0.997 |        1 |
| ltx23       | 30-44   |  471 |      0.984 |   0.968 |   0.996 |        1 |
| ltx23       | 45-59   |  478 |      0.981 |   0.965 |   0.995 |        1 |
| ltx23       | 60+     |  460 |      0.998 |   0.996 |   0.999 |        1 |
| wan22       | 18-29   |  388 |      1     |   1     |   1     |        1 |
| wan22       | 30-44   |  377 |      1     |   1     |   1     |        1 |
| wan22       | 45-59   |  398 |      1     |   1     |   1     |        1 |
| wan22       | 60+     |  403 |      1     |   1     |   1     |        1 |
| hunyuan15   | 18-29   |  242 |      0.999 |   0.999 |   1     |        1 |
| hunyuan15   | 30-44   |  248 |      0.999 |   0.998 |   1     |        1 |
| hunyuan15   | 45-59   |  250 |      1     |   1     |   1     |        1 |
| hunyuan15   | 60+     |  249 |      1     |   1     |   1     |        1 |
| all         | 18-29   | 1099 |      0.991 |   0.982 |   0.998 |        1 |
| all         | 30-44   | 1096 |      0.993 |   0.986 |   0.998 |        1 |
| all         | 45-59   | 1126 |      0.992 |   0.985 |   0.998 |        1 |
| all         | 60+     | 1112 |      0.999 |   0.998 |   1     |        1 |

### Mean score by scene factor (all generators pooled)

| factor           | level      |    n |   estimate |   ci_lo |   ci_hi |
|:-----------------|:-----------|-----:|-----------:|--------:|--------:|
| setting          | cafe       |  376 |      0.993 |   0.955 |   0.998 |
| setting          | classroom  |  373 |      1     |   1     |   1     |
| setting          | corridor   |  493 |      1     |   0.999 |   1     |
| setting          | kitchen    |  441 |      0.981 |   0.924 |   1     |
| setting          | library    |  534 |      0.983 |   0.936 |   1     |
| setting          | livingroom |  530 |      1     |   1     |   1     |
| setting          | lobby      |  345 |      0.98  |   0.955 |   1     |
| setting          | office     |  357 |      0.999 |   0.996 |   1     |
| setting          | plainwall  |  553 |      0.999 |   0.999 |   1     |
| setting          | studio     |  431 |      1     |   0.999 |   1     |
| lighting         | backlit    |  790 |      0.999 |   0.998 |   1     |
| lighting         | harsh      |  632 |      0.999 |   0.997 |   1     |
| lighting         | lowlight   |  784 |      0.97  |   0.941 |   0.995 |
| lighting         | overcast   |  692 |      0.997 |   0.987 |   1     |
| lighting         | softwindow |  821 |      1     |   1     |   1     |
| lighting         | warmlamp   |  714 |      0.999 |   0.998 |   1     |
| behavior         | laugh      |  500 |      0.986 |   0.951 |   1     |
| behavior         | listen     |  680 |      0.999 |   0.998 |   1     |
| behavior         | pause      |  520 |      1     |   0.998 |   1     |
| behavior         | read       |  576 |      0.998 |   0.997 |   0.999 |
| behavior         | smile      |  538 |      1     |   1     |   1     |
| behavior         | speak      |  530 |      0.993 |   0.979 |   1     |
| behavior         | think      |  509 |      0.987 |   0.955 |   1     |
| behavior         | turn       |  580 |      0.985 |   0.949 |   1     |
| camera           | slowsway   | 2225 |      0.992 |   0.982 |   0.999 |
| camera           | static     | 2208 |      0.995 |   0.989 |   1     |
| duration_nominal | 5.0        | 2227 |      0.995 |   0.987 |   0.999 |
| duration_nominal | 6.0        | 2206 |      0.993 |   0.983 |   0.999 |

Per-generator scene-factor and 56-cell rows: `tables/score_by_breakdown.csv`.

### Subgroup gap (max - min of level means)

A gap is max - min, so it is never negative and its interval cannot include 0; it is a size, not a test of a difference. Over many levels with few clips each (56 cells; HunyuanVideo has 9 groups per cell) the gap also grows with noise, so compare it with the per-level intervals in `tables/score_by_breakdown.csv`. Levels seen in a single counterfactual group have no interval.

| generator   | attribute        |   n_levels |   gap |   ci_lo |   ci_hi | max_level     | min_level            |
|:------------|:-----------------|-----------:|------:|--------:|--------:|:--------------|:---------------------|
| ltx23       | race             |          7 | 0.045 |   0.012 |   0.086 | black         | east_asian           |
| ltx23       | gender           |          2 | 0     |   0     |   0.006 | m             | f                    |
| ltx23       | age_band         |          4 | 0.019 |   0.005 |   0.039 | 60+           | 18-29                |
| ltx23       | cell             |         56 | 0.073 |   0.032 |   0.162 | mena__m__60+  | east_asian__f__18-29 |
| ltx23       | setting          |         10 | 0.049 |   0.019 |   0.146 | livingroom    | kitchen              |
| ltx23       | lighting         |          6 | 0.073 |   0.014 |   0.127 | softwindow    | lowlight             |
| ltx23       | behavior         |          8 | 0.039 |   0.015 |   0.126 | smile         | laugh                |
| ltx23       | camera           |          2 | 0.007 |   0     |   0.033 | static        | slowsway             |
| ltx23       | duration_nominal |          2 | 0.003 |   0     |   0.03  | 5.0           | 6.0                  |
| wan22       | race             |          7 | 0     |   0     |   0.001 | white         | east_asian           |
| wan22       | gender           |          2 | 0     |   0     |   0     | f             | m                    |
| wan22       | age_band         |          4 | 0     |   0     |   0     | 60+           | 18-29                |
| wan22       | cell             |         56 | 0.001 |   0.001 |   0.002 | white__f__60+ | east_asian__m__18-29 |
| wan22       | setting          |         10 | 0     |   0     |   0.001 | studio        | plainwall            |
| wan22       | lighting         |          6 | 0     |   0     |   0     | warmlamp      | overcast             |
| wan22       | behavior         |          8 | 0     |   0     |   0.001 | smile         | read                 |
| wan22       | camera           |          2 | 0     |   0     |   0     | static        | slowsway             |
| wan22       | duration_nominal |          2 | 0     |   0     |   0     | 5.0           | 6.0                  |
| hunyuan15   | race             |          7 | 0.002 |   0.001 |   0.004 | white         | east_asian           |
| hunyuan15   | gender           |          2 | 0     |   0     |   0.001 | f             | m                    |
| hunyuan15   | age_band         |          4 | 0.001 |   0     |   0.002 | 60+           | 30-44                |
| hunyuan15   | cell             |         56 | 0.01  |   0.002 |   0.023 | white__f__60+ | east_asian__m__30-44 |
| hunyuan15   | setting          |         10 | 0.001 |   0     |   0.002 | corridor      | plainwall            |
| hunyuan15   | lighting         |          6 | 0.001 |   0     |   0.002 | backlit       | harsh                |
| hunyuan15   | behavior         |          8 | 0.001 |   0     |   0.002 | smile         | turn                 |
| hunyuan15   | camera           |          2 | 0     |   0     |   0.001 | static        | slowsway             |
| hunyuan15   | duration_nominal |          2 | 0     |   0     |   0.001 | 5.0           | 6.0                  |
| all         | race             |          7 | 0.02  |   0.006 |   0.037 | black         | east_asian           |
| all         | gender           |          2 | 0     |   0     |   0.002 | f             | m                    |
| all         | age_band         |          4 | 0.008 |   0.002 |   0.017 | 60+           | 18-29                |
| all         | cell             |         56 | 0.031 |   0.015 |   0.069 | mena__m__60+  | east_asian__f__18-29 |
| all         | setting          |         10 | 0.019 |   0.008 |   0.076 | livingroom    | lobby                |
| all         | lighting         |          6 | 0.03  |   0.006 |   0.059 | softwindow    | lowlight             |
| all         | behavior         |          8 | 0.015 |   0.006 |   0.064 | smile         | turn                 |
| all         | camera           |          2 | 0.003 |   0     |   0.014 | static        | slowsway             |
| all         | duration_nominal |          2 | 0.002 |   0     |   0.014 | 5.0           | 6.0                  |

### CF spread (mean over groups of the std of score across the group's cells)

| generator   |   n_groups |   cf_spread |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.032 |   0.011 |   0.057 |    0.001 | 0.275 |
| wan22       |         36 |       0     |   0     |   0     |    0     | 0.001 |
| hunyuan15   |         18 |       0.002 |   0     |   0.004 |    0     | 0.014 |

### Factor attribution

OLS with every factor as a fixed effect, type-II ANOVA. `ss_share` is the factor's type-II sum of squares over the total sum of squares (type-II shares need not add to 1). Scene factors are constant within a counterfactual group, so their effects are estimated from between-group differences only. The OLS F tests treat clips as independent although clips are clustered in counterfactual groups, so their p values are optimistic; use the group-bootstrap intervals above for inference.

| factor           |   df |     sum_sq | F         | p         | partial_eta2   |   ss_share |
|:-----------------|-----:|-----------:|:----------|:----------|:---------------|-----------:|
| race             |    6 |  0.212     | 13.59     | 2.374e-15 | 0.01821        |  0.01631   |
| gender           |    1 |  3.466e-05 | 0.01333   | 0.9081    | 3.032e-06      |  2.666e-06 |
| age_band         |    3 |  0.04381   | 5.617     | 0.0007689 | 0.003818       |  0.00337   |
| setting          |    9 |  0.399     | 17.06     | 5.463e-28 | 0.03373        |  0.0307    |
| lighting         |    5 |  0.4501    | 34.63     | 7.672e-35 | 0.03789        |  0.03463   |
| behavior         |    7 |  0.3586    | 19.71     | 3.667e-26 | 0.03042        |  0.02759   |
| camera           |    1 |  1.973e-06 | 0.0007588 | 0.978     | 1.726e-07      |  1.518e-07 |
| duration_nominal |    1 |  0.002805  | 1.079     | 0.2989    | 0.0002454      |  0.0002158 |
| generator        |    2 |  0.2316    | 44.55     | 7.008e-20 | 0.01986        |  0.01782   |
| Residual         | 4397 | 11.43      |           |           |                |  0.8794    |

Lighting x race interaction (added to the same OLS):

| term            |   df |   sum_sq |    F |         p |   partial_eta2 |
|:----------------|-----:|---------:|-----:|----------:|---------------:|
| lighting x race |   30 |   0.6628 | 8.96 | 8.289e-39 |        0.05798 |

Mixed model `score ~ factors + (1 | counterfactual_group)` (REML) variance components (fixed effects: `tables/factor_mixed_fixed.csv`):

| component                               |   variance | converged   |
|:----------------------------------------|-----------:|:------------|
| counterfactual_group (random intercept) |   0        | True        |
| residual                                |   0.002559 | True        |
| ICC (group share of random variance)    |   0        | True        |

A group variance at or near 0 is a boundary estimate: setting, lighting, behavior, camera and duration are fixed per group and absorb most between-group variation, leaving little for the random intercept. It does not mean scenes do not matter.

## 6.2 Provisional (threshold 0.5, provisional)

### Detection rate by generator (provisional)

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1878 |      0.99  |   0.98  |   0.999 |
| wan22       | 1566 |      1     |   1     |   1     |
| hunyuan15   |  989 |      1     |   1     |   1     |
| all         | 4433 |      0.996 |   0.992 |   1     |

### Detection rate by race (provisional)

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 273 |      1     |   1     |   1     |
| ltx23       | east_asian      | 270 |      0.959 |   0.917 |   0.993 |
| ltx23       | indian          | 277 |      0.996 |   0.989 |   1     |
| ltx23       | latino          | 262 |      0.996 |   0.988 |   1     |
| ltx23       | mena            | 267 |      1     |   1     |   1     |
| ltx23       | southeast_asian | 271 |      0.985 |   0.96  |   1     |
| ltx23       | white           | 258 |      0.996 |   0.988 |   1     |
| wan22       | black           | 217 |      1     |   1     |   1     |
| wan22       | east_asian      | 226 |      1     |   1     |   1     |
| wan22       | indian          | 230 |      1     |   1     |   1     |
| wan22       | latino          | 219 |      1     |   1     |   1     |
| wan22       | mena            | 225 |      1     |   1     |   1     |
| wan22       | southeast_asian | 229 |      1     |   1     |   1     |
| wan22       | white           | 220 |      1     |   1     |   1     |
| hunyuan15   | black           | 141 |      1     |   1     |   1     |
| hunyuan15   | east_asian      | 141 |      1     |   1     |   1     |
| hunyuan15   | indian          | 142 |      1     |   1     |   1     |
| hunyuan15   | latino          | 142 |      1     |   1     |   1     |
| hunyuan15   | mena            | 139 |      1     |   1     |   1     |
| hunyuan15   | southeast_asian | 143 |      1     |   1     |   1     |
| hunyuan15   | white           | 141 |      1     |   1     |   1     |
| all         | black           | 631 |      1     |   1     |   1     |
| all         | east_asian      | 637 |      0.983 |   0.965 |   0.997 |
| all         | indian          | 649 |      0.998 |   0.995 |   1     |
| all         | latino          | 623 |      0.998 |   0.995 |   1     |
| all         | mena            | 631 |      1     |   1     |   1     |
| all         | southeast_asian | 643 |      0.994 |   0.983 |   1     |
| all         | white           | 619 |      0.998 |   0.995 |   1     |

### Detection rate by gender (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.989 |   0.978 |   0.999 |
| ltx23       | m       |  947 |      0.992 |   0.98  |   1     |
| wan22       | f       |  785 |      1     |   1     |   1     |
| wan22       | m       |  781 |      1     |   1     |   1     |
| hunyuan15   | f       |  495 |      1     |   1     |   1     |
| hunyuan15   | m       |  494 |      1     |   1     |   1     |
| all         | f       | 2211 |      0.995 |   0.991 |   1     |
| all         | m       | 2222 |      0.996 |   0.992 |   1     |

### Detection rate by age band (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  469 |      0.985 |   0.964 |   1     |
| ltx23       | 30-44   |  471 |      0.989 |   0.978 |   0.998 |
| ltx23       | 45-59   |  478 |      0.987 |   0.974 |   0.998 |
| ltx23       | 60+     |  460 |      1     |   1     |   1     |
| wan22       | 18-29   |  388 |      1     |   1     |   1     |
| wan22       | 30-44   |  377 |      1     |   1     |   1     |
| wan22       | 45-59   |  398 |      1     |   1     |   1     |
| wan22       | 60+     |  403 |      1     |   1     |   1     |
| hunyuan15   | 18-29   |  242 |      1     |   1     |   1     |
| hunyuan15   | 30-44   |  248 |      1     |   1     |   1     |
| hunyuan15   | 45-59   |  250 |      1     |   1     |   1     |
| hunyuan15   | 60+     |  249 |      1     |   1     |   1     |
| all         | 18-29   | 1099 |      0.994 |   0.985 |   1     |
| all         | 30-44   | 1096 |      0.995 |   0.99  |   0.999 |
| all         | 45-59   | 1126 |      0.995 |   0.989 |   0.999 |
| all         | 60+     | 1112 |      1     |   1     |   1     |

### Detection-rate gap (provisional)

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level       | min_level            |
|:------------|:-----------------|------:|--------:|--------:|:----------------|:---------------------|
| ltx23       | race             | 0.041 |   0.007 |   0.083 | black           | east_asian           |
| ltx23       | gender           | 0.002 |   0     |   0.01  | m               | f                    |
| ltx23       | age_band         | 0.015 |   0.002 |   0.036 | 60+             | 18-29                |
| ltx23       | cell             | 0.062 |   0.029 |   0.179 | black__f__18-29 | east_asian__f__18-29 |
| ltx23       | setting          | 0.038 |   0.01  |   0.127 | classroom       | library              |
| ltx23       | lighting         | 0.053 |   0.008 |   0.098 | backlit         | lowlight             |
| ltx23       | behavior         | 0.04  |   0.008 |   0.121 | listen          | laugh                |
| ltx23       | camera           | 0.008 |   0     |   0.029 | static          | slowsway             |
| ltx23       | duration_nominal | 0.001 |   0     |   0.025 | 6.0             | 5.0                  |
| wan22       | race             | 0     |   0     |   0     | black           | black                |
| wan22       | gender           | 0     |   0     |   0     | f               | f                    |
| wan22       | age_band         | 0     |   0     |   0     | 18-29           | 18-29                |
| wan22       | cell             | 0     |   0     |   0     | black__f__18-29 | black__f__18-29      |
| wan22       | setting          | 0     |   0     |   0     | cafe            | cafe                 |
| wan22       | lighting         | 0     |   0     |   0     | backlit         | backlit              |
| wan22       | behavior         | 0     |   0     |   0     | laugh           | laugh                |
| wan22       | camera           | 0     |   0     |   0     | slowsway        | slowsway             |
| wan22       | duration_nominal | 0     |   0     |   0     | 5.0             | 5.0                  |
| hunyuan15   | race             | 0     |   0     |   0     | black           | black                |
| hunyuan15   | gender           | 0     |   0     |   0     | f               | f                    |
| hunyuan15   | age_band         | 0     |   0     |   0     | 18-29           | 18-29                |
| hunyuan15   | cell             | 0     |   0     |   0     | black__f__18-29 | black__f__18-29      |
| hunyuan15   | setting          | 0     |   0     |   0     | cafe            | cafe                 |
| hunyuan15   | lighting         | 0     |   0     |   0     | backlit         | backlit              |
| hunyuan15   | behavior         | 0     |   0     |   0     | laugh           | laugh                |
| hunyuan15   | camera           | 0     |   0     |   0     | slowsway        | slowsway             |
| hunyuan15   | duration_nominal | 0     |   0     |   0     | 5.0             | 5.0                  |
| all         | race             | 0.017 |   0.003 |   0.035 | black           | east_asian           |
| all         | gender           | 0.001 |   0     |   0.004 | m               | f                    |
| all         | age_band         | 0.006 |   0.001 |   0.015 | 60+             | 18-29                |
| all         | cell             | 0.026 |   0.012 |   0.078 | black__f__18-29 | east_asian__m__45-59 |
| all         | setting          | 0.015 |   0.004 |   0.064 | classroom       | library              |
| all         | lighting         | 0.022 |   0.003 |   0.046 | backlit         | lowlight             |
| all         | behavior         | 0.014 |   0.004 |   0.057 | listen          | laugh                |
| all         | camera           | 0.004 |   0     |   0.013 | static          | slowsway             |
| all         | duration_nominal | 0     |   0     |   0.011 | 5.0             | 6.0                  |

### Flip rate (provisional): share of groups whose clips get different decisions

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.139 |   0.028 |    0.25 |        0 |     1 |
| wan22       |         36 |       0     |   0     |    0    |        0 |     0 |
| hunyuan15   |         18 |       0     |   0     |    0    |        0 |     0 |

### Sensitivity: inclusion set

| set     | generator   |    n |   mean_score |   provisional_detection_rate |
|:--------|:------------|-----:|-------------:|-----------------------------:|
| all     | hunyuan15   | 1008 |        1     |                        1     |
| all     | ltx23       | 2016 |        0.977 |                        0.984 |
| all     | wan22       | 2016 |        1     |                        1     |
| primary | hunyuan15   |  989 |        1     |                        1     |
| primary | ltx23       | 1878 |        0.986 |                        0.99  |
| primary | wan22       | 1566 |        1     |                        1     |

## 6.3 Real vs generated (calibrated threshold 0.9998)

The threshold is the score at which 5% of primary real renders (24 and 16 fps pooled) are flagged; one per detector and view, never per subgroup. Each generator is compared with reals rendered at its own fps. Intervals: fakes resample counterfactual groups, reals resample identity clusters (source video). Real labels are perceived (FairFace), not self-reported.

### Calibration

| scope            |   n_renders |   n_sources |   n_identities |   threshold |    fpr |
|:-----------------|------------:|------------:|---------------:|------------:|-------:|
| all real renders |        1855 |         932 |            811 |      0.9998 | 0.0501 |
| 16 fps renders   |         932 |         932 |            811 |      0.9998 | 0.0536 |
| 24 fps renders   |         923 |         923 |            802 |      0.9998 | 0.0466 |

### AUC, AP, EER, TPR at 5% FPR

| generator   | real_fps   |   n_fake |   n_real |   auc |   auc_ci_lo |   auc_ci_hi |    ap |   eer |   tpr_at_5fpr |   detection_rate_global_thr |   det_ci_lo |   det_ci_hi |
|:------------|:-----------|---------:|---------:|------:|------------:|------------:|------:|------:|--------------:|----------------------------:|------------:|------------:|
| ltx23       | 24         |     1878 |      923 | 0.904 |       0.867 |       0.937 | 0.942 | 0.17  |         0.586 |                       0.576 |       0.48  |       0.675 |
| wan22       | 16         |     1566 |      932 | 0.961 |       0.949 |       0.971 | 0.966 | 0.103 |         0.738 |                       0.751 |       0.693 |       0.809 |
| hunyuan15   | 24         |      989 |      923 | 0.967 |       0.956 |       0.977 | 0.962 | 0.096 |         0.824 |                       0.81  |       0.748 |       0.868 |
| all         | 24+16      |     4433 |     1855 | 0.938 |       0.919 |       0.954 | 0.967 | 0.129 |         0.69  |                       0.69  |       0.633 |       0.749 |

### Real FPR by perceived subgroup

| attribute   | level              |   n_renders |   n_identities |   fpr |   ci_lo |   ci_hi |
|:------------|:-------------------|------------:|---------------:|------:|--------:|--------:|
| race        | black              |         123 |             59 | 0.049 |   0     |   0.108 |
| race        | east_asian         |         163 |             75 | 0.043 |   0.006 |   0.089 |
| race        | indian             |          46 |             23 | 0.043 |   0     |   0.136 |
| race        | latino             |         115 |             55 | 0.009 |   0     |   0.032 |
| race        | mena               |         120 |             59 | 0.017 |   0     |   0.055 |
| race        | southeast_asian    |          70 |             34 | 0     |   0     |   0     |
| race        | white              |        1204 |            523 | 0.061 |   0.041 |   0.08  |
| gender      | f                  |         587 |            266 | 0.092 |   0.062 |   0.127 |
| gender      | m                  |        1254 |            553 | 0.03  |   0.018 |   0.043 |
| age_band    | 18-29              |         594 |            275 | 0.084 |   0.056 |   0.117 |
| age_band    | 30-44              |         626 |            290 | 0.043 |   0.021 |   0.068 |
| age_band    | 45-59              |         300 |            134 | 0.03  |   0.007 |   0.06  |
| age_band    | 60+                |         241 |            112 | 0.017 |   0     |   0.043 |
| race_gender | black__f           |          20 |             10 | 0.1   |   0     |   0.333 |
| race_gender | black__m           |         103 |             50 | 0.039 |   0     |   0.108 |
| race_gender | east_asian__f      |          76 |             35 | 0.066 |   0     |   0.153 |
| race_gender | east_asian__m      |          87 |             41 | 0.023 |   0     |   0.078 |
| race_gender | indian__f          |          12 |              6 | 0     |   0     |   0     |
| race_gender | indian__m          |          34 |             17 | 0.059 |   0     |   0.185 |
| race_gender | latino__f          |          20 |             10 | 0     |   0     |   0     |
| race_gender | latino__m          |          95 |             45 | 0.011 |   0     |   0.038 |
| race_gender | mena__f            |          34 |             17 | 0     |   0     |   0     |
| race_gender | mena__m            |          86 |             42 | 0.023 |   0     |   0.079 |
| race_gender | southeast_asian__f |          20 |              9 | 0     |   0     |   0     |
| race_gender | southeast_asian__m |          50 |             25 | 0     |   0     |   0     |
| race_gender | white__f           |         405 |            183 | 0.116 |   0.075 |   0.162 |
| race_gender | white__m           |         799 |            350 | 0.033 |   0.017 |   0.05  |

### Real FPR gap (max - min across levels; non-negative by construction)

| attribute   |   n_levels |   fpr_gap |   ci_lo |   ci_hi | max_level   |   max_fpr | min_level       |   min_fpr |
|:------------|-----------:|----------:|--------:|--------:|:------------|----------:|:----------------|----------:|
| race        |          7 |     0.061 |   0.05  |   0.143 | white       |     0.061 | southeast_asian |     0     |
| gender      |          2 |     0.062 |   0.03  |   0.099 | f           |     0.092 | m               |     0.03  |
| age_band    |          4 |     0.068 |   0.033 |   0.107 | 18-29       |     0.084 | 60+             |     0.017 |
| race_gender |         14 |     0.116 |   0.09  |   0.333 | white__f    |     0.116 | indian__f       |     0     |

### Worst-subgroup AUC and AUC gap

| generator   | attribute   |   n_levels | worst_level   |   worst_auc |   worst_ci_lo |   worst_ci_hi | best_level   |   best_auc |   auc_gap |   gap_ci_lo |   gap_ci_hi |
|:------------|:------------|-----------:|:--------------|------------:|--------------:|--------------:|:-------------|-----------:|----------:|------------:|------------:|
| ltx23       | race        |          6 | east_asian    |       0.882 |         0.806 |         0.926 | latino       |      0.963 |     0.08  |       0.051 |       0.159 |
| ltx23       | gender      |          2 | f             |       0.865 |         0.813 |         0.911 | m            |      0.924 |     0.06  |       0.027 |       0.091 |
| ltx23       | age_band    |          4 | 18-29         |       0.862 |         0.815 |         0.905 | 60+          |      0.939 |     0.077 |       0.045 |       0.117 |
| ltx23       | race_gender |          7 | east_asian__f |       0.85  |         0.748 |         0.91  | white__m     |      0.968 |     0.118 |       0.069 |       0.226 |
| wan22       | race        |          6 | east_asian    |       0.946 |         0.899 |         0.969 | latino       |      0.996 |     0.051 |       0.029 |       0.098 |
| wan22       | gender      |          2 | f             |       0.937 |         0.913 |         0.958 | m            |      0.972 |     0.035 |       0.015 |       0.059 |
| wan22       | age_band    |          4 | 18-29         |       0.928 |         0.902 |         0.951 | 60+          |      0.984 |     0.055 |       0.033 |       0.083 |
| wan22       | race_gender |          7 | east_asian__f |       0.928 |         0.866 |         0.967 | latino__m    |      0.996 |     0.068 |       0.032 |       0.131 |
| hunyuan15   | race        |          6 | east_asian    |       0.951 |         0.915 |         0.975 | latino       |      0.995 |     0.044 |       0.021 |       0.08  |
| hunyuan15   | gender      |          2 | f             |       0.95  |         0.927 |         0.97  | m            |      0.975 |     0.025 |       0.006 |       0.045 |
| hunyuan15   | age_band    |          4 | 18-29         |       0.926 |         0.898 |         0.951 | 60+          |      0.992 |     0.066 |       0.043 |       0.097 |
| hunyuan15   | race_gender |          7 | east_asian__f |       0.946 |         0.895 |         0.972 | latino__m    |      0.999 |     0.053 |       0.028 |       0.104 |
| all         | race        |          7 | east_asian    |       0.92  |         0.866 |         0.946 | latino       |      0.982 |     0.062 |       0.04  |       0.119 |
| all         | gender      |          2 | f             |       0.909 |         0.879 |         0.936 | m            |      0.952 |     0.043 |       0.02  |       0.067 |
| all         | age_band    |          4 | 18-29         |       0.899 |         0.869 |         0.926 | 60+          |      0.967 |     0.068 |       0.043 |       0.098 |
| all         | race_gender |         10 | east_asian__f |       0.899 |         0.819 |         0.935 | white__m     |      0.983 |     0.084 |       0.055 |       0.173 |

### Detection rate at the calibrated threshold

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1878 |      0.576 |   0.48  |   0.675 |
| wan22       | 1566 |      0.751 |   0.693 |   0.809 |
| hunyuan15   |  989 |      0.81  |   0.748 |   0.868 |
| all         | 4433 |      0.69  |   0.633 |   0.749 |

#### by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 273 |      0.707 |   0.599 |   0.804 |
| ltx23       | east_asian      | 270 |      0.285 |   0.183 |   0.4   |
| ltx23       | indian          | 277 |      0.542 |   0.426 |   0.664 |
| ltx23       | latino          | 262 |      0.706 |   0.591 |   0.818 |
| ltx23       | mena            | 267 |      0.659 |   0.551 |   0.763 |
| ltx23       | southeast_asian | 271 |      0.38  |   0.271 |   0.496 |
| ltx23       | white           | 258 |      0.767 |   0.668 |   0.858 |
| wan22       | black           | 217 |      0.756 |   0.675 |   0.835 |
| wan22       | east_asian      | 226 |      0.425 |   0.303 |   0.552 |
| wan22       | indian          | 230 |      0.77  |   0.683 |   0.852 |
| wan22       | latino          | 219 |      0.927 |   0.871 |   0.97  |
| wan22       | mena            | 225 |      0.916 |   0.871 |   0.96  |
| wan22       | southeast_asian | 229 |      0.498 |   0.388 |   0.62  |
| wan22       | white           | 220 |      0.982 |   0.954 |   1     |
| hunyuan15   | black           | 141 |      0.823 |   0.714 |   0.918 |
| hunyuan15   | east_asian      | 141 |      0.596 |   0.51  |   0.692 |
| hunyuan15   | indian          | 142 |      0.824 |   0.718 |   0.911 |
| hunyuan15   | latino          | 142 |      0.908 |   0.848 |   0.964 |
| hunyuan15   | mena            | 139 |      0.892 |   0.83  |   0.949 |
| hunyuan15   | southeast_asian | 143 |      0.671 |   0.545 |   0.788 |
| hunyuan15   | white           | 141 |      0.957 |   0.907 |   0.993 |
| all         | black           | 631 |      0.75  |   0.684 |   0.812 |
| all         | east_asian      | 637 |      0.403 |   0.329 |   0.491 |
| all         | indian          | 649 |      0.684 |   0.608 |   0.761 |
| all         | latino          | 623 |      0.83  |   0.768 |   0.888 |
| all         | mena            | 631 |      0.802 |   0.75  |   0.853 |
| all         | southeast_asian | 643 |      0.487 |   0.404 |   0.574 |
| all         | white           | 619 |      0.887 |   0.843 |   0.929 |

#### by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.58  |   0.48  |   0.689 |
| ltx23       | m       |  947 |      0.572 |   0.473 |   0.666 |
| wan22       | f       |  785 |      0.764 |   0.694 |   0.831 |
| wan22       | m       |  781 |      0.738 |   0.682 |   0.797 |
| hunyuan15   | f       |  495 |      0.822 |   0.743 |   0.896 |
| hunyuan15   | m       |  494 |      0.798 |   0.744 |   0.852 |
| all         | f       | 2211 |      0.7   |   0.637 |   0.765 |
| all         | m       | 2222 |      0.68  |   0.626 |   0.739 |

#### by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  469 |      0.471 |   0.368 |   0.588 |
| ltx23       | 30-44   |  471 |      0.544 |   0.44  |   0.652 |
| ltx23       | 45-59   |  478 |      0.621 |   0.516 |   0.721 |
| ltx23       | 60+     |  460 |      0.67  |   0.567 |   0.768 |
| wan22       | 18-29   |  388 |      0.66  |   0.571 |   0.746 |
| wan22       | 30-44   |  377 |      0.679 |   0.59  |   0.764 |
| wan22       | 45-59   |  398 |      0.807 |   0.758 |   0.856 |
| wan22       | 60+     |  403 |      0.851 |   0.805 |   0.897 |
| hunyuan15   | 18-29   |  242 |      0.657 |   0.554 |   0.756 |
| hunyuan15   | 30-44   |  248 |      0.718 |   0.622 |   0.816 |
| hunyuan15   | 45-59   |  250 |      0.896 |   0.848 |   0.943 |
| hunyuan15   | 60+     |  249 |      0.964 |   0.908 |   0.996 |
| all         | 18-29   | 1099 |      0.579 |   0.509 |   0.656 |
| all         | 30-44   | 1096 |      0.63  |   0.56  |   0.699 |
| all         | 45-59   | 1126 |      0.748 |   0.692 |   0.802 |
| all         | 60+     | 1112 |      0.801 |   0.753 |   0.85  |

### Detection-rate gap at the calibrated threshold

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level        | min_level            |
|:------------|:-----------------|------:|--------:|--------:|:-----------------|:---------------------|
| ltx23       | race             | 0.482 |   0.386 |   0.574 | white            | east_asian           |
| ltx23       | gender           | 0.008 |   0.001 |   0.058 | f                | m                    |
| ltx23       | age_band         | 0.198 |   0.133 |   0.27  | 60+              | 18-29                |
| ltx23       | cell             | 0.712 |   0.635 |   0.886 | black__m__60+    | east_asian__m__18-29 |
| ltx23       | setting          | 0.563 |   0.47  |   0.982 | livingroom       | library              |
| ltx23       | lighting         | 0.687 |   0.573 |   0.905 | warmlamp         | lowlight             |
| ltx23       | behavior         | 0.504 |   0.385 |   0.904 | smile            | turn                 |
| ltx23       | camera           | 0.177 |   0.017 |   0.359 | static           | slowsway             |
| ltx23       | duration_nominal | 0.083 |   0.004 |   0.272 | 5.0              | 6.0                  |
| wan22       | race             | 0.557 |   0.433 |   0.675 | white            | east_asian           |
| wan22       | gender           | 0.027 |   0.001 |   0.074 | f                | m                    |
| wan22       | age_band         | 0.191 |   0.13  |   0.271 | 60+              | 18-29                |
| wan22       | cell             | 0.75  |   0.652 |   0.926 | latino__f__45-59 | east_asian__m__45-59 |
| wan22       | setting          | 0.334 |   0.289 |   0.512 | studio           | plainwall            |
| wan22       | lighting         | 0.242 |   0.145 |   0.439 | warmlamp         | overcast             |
| wan22       | behavior         | 0.379 |   0.307 |   0.513 | smile            | read                 |
| wan22       | camera           | 0.066 |   0.005 |   0.192 | static           | slowsway             |
| wan22       | duration_nominal | 0.123 |   0.017 |   0.233 | 5.0              | 6.0                  |
| hunyuan15   | race             | 0.362 |   0.282 |   0.451 | white            | east_asian           |
| hunyuan15   | gender           | 0.025 |   0.001 |   0.079 | f                | m                    |
| hunyuan15   | age_band         | 0.307 |   0.213 |   0.404 | 60+              | 18-29                |
| hunyuan15   | cell             | 0.833 |   0.714 |   1     | black__f__60+    | east_asian__m__30-44 |
| hunyuan15   | setting          | 0.246 |   0.196 |   0.429 | corridor         | kitchen              |
| hunyuan15   | lighting         | 0.172 |   0.124 |   0.402 | backlit          | lowlight             |
| hunyuan15   | behavior         | 0.277 |   0.212 |   0.429 | smile            | speak                |
| hunyuan15   | camera           | 0.019 |   0.003 |   0.149 | static           | slowsway             |
| hunyuan15   | duration_nominal | 0.023 |   0.003 |   0.157 | 6.0              | 5.0                  |
| all         | race             | 0.483 |   0.409 |   0.552 | white            | east_asian           |
| all         | gender           | 0.019 |   0.001 |   0.053 | f                | m                    |
| all         | age_band         | 0.223 |   0.166 |   0.285 | 60+              | 18-29                |
| all         | cell             | 0.736 |   0.661 |   0.857 | white__m__60+    | east_asian__m__30-44 |
| all         | setting          | 0.331 |   0.295 |   0.552 | livingroom       | lobby                |
| all         | lighting         | 0.358 |   0.241 |   0.514 | warmlamp         | lowlight             |
| all         | behavior         | 0.386 |   0.317 |   0.56  | smile            | turn                 |
| all         | camera           | 0.105 |   0.012 |   0.216 | static           | slowsway             |
| all         | duration_nominal | 0.083 |   0.007 |   0.197 | 5.0              | 6.0                  |

### Flip rate at the calibrated threshold

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.861 |   0.75  |   0.972 |        1 |     1 |
| wan22       |         36 |       0.889 |   0.778 |   0.972 |        1 |     1 |
| hunyuan15   |         18 |       1     |   1     |   1     |        1 |     1 |

## Figures

**Score distribution by generator.** (`figures/score_distribution_by_generator.pdf`)

![score_distribution_by_generator](figures/score_distribution_by_generator.png)

**Mean score, 56 cells x generator.** (`figures/heatmap_mean_score_cells.pdf`)

![heatmap_mean_score_cells](figures/heatmap_mean_score_cells.png)

**Detection rate, 56 cells x generator (provisional threshold).** (`figures/heatmap_detection_rate_cells_provisional.pdf`)

![heatmap_detection_rate_cells_provisional](figures/heatmap_detection_rate_cells_provisional.png)

**Mean score by race, gender, age band with 95% CI.** (`figures/subgroup_mean_score.pdf`)

![subgroup_mean_score](figures/subgroup_mean_score.png)

**Mean score by scene factor with 95% CI.** (`figures/scene_factor_mean_score.pdf`)

![scene_factor_mean_score](figures/scene_factor_mean_score.png)

**Detection rate by subgroup (provisional threshold).** (`figures/subgroup_detection_rate_provisional.pdf`)

![subgroup_detection_rate_provisional](figures/subgroup_detection_rate_provisional.png)

**Distribution of per-group CF spread.** (`figures/cf_spread_distribution.pdf`)

![cf_spread_distribution](figures/cf_spread_distribution.png)

**Flip rate by generator (provisional threshold).** (`figures/flip_rate_by_generator_provisional.pdf`)

![flip_rate_by_generator_provisional](figures/flip_rate_by_generator_provisional.png)

**Partial eta squared by factor.** (`figures/factor_attribution_variance_share.pdf`)

![factor_attribution_variance_share](figures/factor_attribution_variance_share.png)

**Highest- and lowest-scoring included clips.** (`figures/example_strip.pdf`)

![example_strip](figures/example_strip.png)

**ROC per generator against fps-matched reals.** (`figures/roc_per_generator.pdf`)

![roc_per_generator](figures/roc_per_generator.png)

**Real FPR by perceived subgroup at the calibrated threshold.** (`figures/real_fpr_by_subgroup.pdf`)

![real_fpr_by_subgroup](figures/real_fpr_by_subgroup.png)

**AUC by subgroup: each subgroup's fakes vs same-subgroup reals.** (`figures/subgroup_auc.pdf`)

![subgroup_auc](figures/subgroup_auc.png)

## Files

`manifest_used.csv` (every clip of the active batches with render/score/inclusion flags), `scores.csv` (score per scored clip), `tables/*.csv`, `figures/*`, `snapshot_meta.json`.

