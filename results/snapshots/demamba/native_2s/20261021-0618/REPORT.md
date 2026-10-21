# demamba / native_2s: snapshot 20261021-0618

> **Detector training data.** DeMamba weights are our own (GenVideo-100K, single-GPU adaptation of the authors' code), not an official release; the authors have published none. GenVideo-100K contains none of our generators. On GenVideo validation it flags 16.8% of real videos at 0.5.

> **Provisional threshold.** Every detection rate and flip rate below uses the detector's default threshold (0.5; sigmoid(logit) > 0.5 (training metrics and our standalone evaluator)). They will be replaced by the 5%-real-FPR threshold once reals exist (section 6.3).

## Settings

| setting           | value                                                                                  |
|:------------------|:---------------------------------------------------------------------------------------|
| detector          | demamba 1+504611ba                                                                     |
| checkpoint_sha256 | f89897c72b595aa85a524e59083919cebb0b92161d2a694a2cbffbdd8456ce17                       |
| view              | native_2s (view_hash f40f08a345fde671)                                                 |
| ffmpeg            | ffmpeg version 7.1.1 Copyright (c) 2000-2025 the FFmpeg developers                     |
| batches           | fake_b1, fake_b2, real_b1                                                              |
| inclusion set     | primary (technical QC pass AND face QC pass)                                           |
| bootstrap         | 1000 resamples of whole counterfactual groups, seed 20261020, 95% percentile intervals |
| git commit        | ac1140ab3053-dirty                                                                     |
| created           | 2026-10-21T06:19:03Z                                                                   |

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

| batch   | generator   |   clips |   primary |   rendered |   view_excluded |   render_failed |   scored |   score_failed |   included |
|:--------|:------------|--------:|----------:|-----------:|----------------:|----------------:|---------:|---------------:|-----------:|
| fake_b1 | hunyuan15   |     504 |       492 |        504 |               0 |               0 |      504 |              0 |        492 |
| fake_b1 | ltx23       |    2016 |      1878 |       2016 |               0 |               0 |     2016 |              0 |       1878 |
| fake_b1 | wan22       |    2016 |      1566 |       2016 |               0 |               0 |     2016 |              0 |       1566 |
| fake_b2 | hunyuan15   |     504 |       497 |        504 |               0 |               0 |      504 |              0 |        497 |
| real_b1 | real        |    1785 |      1684 |          0 |            1785 |               0 |        0 |              0 |          0 |

Reals scored: 0. Fakes included: 4433 of 5040 scored (0 scoring failures).

## Observations

- LTX 2.3: mean score 0.989 [0.978, 0.996], median 1.000, n = 1878.
- Wan 2.2: mean score 1.000 [1.000, 1.000], median 1.000, n = 1566.
- HunyuanVideo 1.5: mean score 0.999 [0.999, 1.000], median 1.000, n = 989.
- Provisional detection rate (score >= 0.5), LTX 2.3: 99.4% [98.8, 99.8].
- Provisional detection rate (score >= 0.5), Wan 2.2: 100.0% [100.0, 100.0].
- Provisional detection rate (score >= 0.5), HunyuanVideo 1.5: 100.0% [100.0, 100.0].
- Provisional detection rate (score >= 0.5), all: 99.8% [99.5, 99.9].
- Largest race score gap: LTX 2.3 0.037 [0.014, 0.066] (black 0.999 vs east_asian 0.962).
- Largest gender score gap: LTX 2.3 0.002 [0.000, 0.007] (m 0.990 vs f 0.987).
- Largest age band score gap: LTX 2.3 0.015 [0.005, 0.029] (60+ 0.998 vs 18-29 0.983).
- Largest cell score gap: LTX 2.3 0.075 [0.042, 0.153] (white__m__60+ 1.000 vs east_asian__f__18-29 0.925).
- Largest scene-factor gap (all generators): setting 0.021 [0.007, 0.053] (livingroom vs lobby).
- Largest partial eta squared: setting 0.022, lighting 0.022, race 0.017; residual holds 90.8% of total SS.
- CF spread, LTX 2.3: 0.030 [0.013, 0.049] over 36 groups (max 0.214).
- CF spread, Wan 2.2: 0.000 [0.000, 0.000] over 36 groups (max 0.001).
- CF spread, HunyuanVideo 1.5: 0.003 [0.000, 0.007] over 18 groups (max 0.031).
- Provisional flip rate, LTX 2.3: 16.7% of 36 groups [5.6, 30.6].
- Provisional flip rate, Wan 2.2: 0.0% of 36 groups [0.0, 0.0].
- Provisional flip rate, HunyuanVideo 1.5: 0.0% of 18 groups [0.0, 0.0].

## 6.1 Fakes only, no threshold

### Mean score by generator

| generator   |    n |   n_groups |   estimate |   ci_lo |   ci_hi |    sd |   median |   q05 |   q95 |
|:------------|-----:|-----------:|-----------:|--------:|--------:|------:|---------:|------:|------:|
| ltx23       | 1878 |         36 |      0.989 |   0.978 |   0.996 | 0.066 |        1 | 0.978 |     1 |
| wan22       | 1566 |         36 |      1     |   1     |   1     | 0.001 |        1 | 0.999 |     1 |
| hunyuan15   |  989 |         18 |      0.999 |   0.999 |   1     | 0.008 |        1 | 0.999 |     1 |
| all         | 4433 |         36 |      0.995 |   0.991 |   0.998 | 0.044 |        1 | 0.996 |     1 |

### Mean score by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:----------------|----:|-----------:|--------:|--------:|---------:|
| ltx23       | black           | 273 |      0.999 |   0.998 |   1     |    1     |
| ltx23       | east_asian      | 270 |      0.962 |   0.932 |   0.985 |    0.999 |
| ltx23       | indian          | 277 |      0.992 |   0.982 |   0.999 |    1     |
| ltx23       | latino          | 262 |      0.997 |   0.992 |   1     |    1     |
| ltx23       | mena            | 267 |      0.993 |   0.986 |   0.999 |    1     |
| ltx23       | southeast_asian | 271 |      0.982 |   0.962 |   0.995 |    1     |
| ltx23       | white           | 258 |      0.996 |   0.99  |   1     |    1     |
| wan22       | black           | 217 |      1     |   1     |   1     |    1     |
| wan22       | east_asian      | 226 |      0.999 |   0.999 |   1     |    1     |
| wan22       | indian          | 230 |      1     |   1     |   1     |    1     |
| wan22       | latino          | 219 |      1     |   1     |   1     |    1     |
| wan22       | mena            | 225 |      1     |   1     |   1     |    1     |
| wan22       | southeast_asian | 229 |      1     |   0.999 |   1     |    1     |
| wan22       | white           | 220 |      1     |   1     |   1     |    1     |
| hunyuan15   | black           | 141 |      1     |   1     |   1     |    1     |
| hunyuan15   | east_asian      | 141 |      0.997 |   0.993 |   0.999 |    1     |
| hunyuan15   | indian          | 142 |      1     |   1     |   1     |    1     |
| hunyuan15   | latino          | 142 |      1     |   1     |   1     |    1     |
| hunyuan15   | mena            | 139 |      1     |   1     |   1     |    1     |
| hunyuan15   | southeast_asian | 143 |      1     |   0.999 |   1     |    1     |
| hunyuan15   | white           | 141 |      1     |   1     |   1     |    1     |
| all         | black           | 631 |      0.999 |   0.999 |   1     |    1     |
| all         | east_asian      | 637 |      0.983 |   0.97  |   0.993 |    1     |
| all         | indian          | 649 |      0.997 |   0.992 |   1     |    1     |
| all         | latino          | 623 |      0.999 |   0.997 |   1     |    1     |
| all         | mena            | 631 |      0.997 |   0.994 |   1     |    1     |
| all         | southeast_asian | 643 |      0.992 |   0.984 |   0.998 |    1     |
| all         | white           | 619 |      0.998 |   0.996 |   1     |    1     |

### Mean score by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | f       |  931 |      0.987 |   0.976 |   0.996 |        1 |
| ltx23       | m       |  947 |      0.99  |   0.98  |   0.997 |        1 |
| wan22       | f       |  785 |      1     |   1     |   1     |        1 |
| wan22       | m       |  781 |      1     |   1     |   1     |        1 |
| hunyuan15   | f       |  495 |      1     |   1     |   1     |        1 |
| hunyuan15   | m       |  494 |      0.999 |   0.998 |   1     |        1 |
| all         | f       | 2211 |      0.995 |   0.99  |   0.998 |        1 |
| all         | m       | 2222 |      0.995 |   0.991 |   0.998 |        1 |

### Mean score by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | 18-29   |  469 |      0.983 |   0.969 |   0.995 |        1 |
| ltx23       | 30-44   |  471 |      0.986 |   0.969 |   0.997 |        1 |
| ltx23       | 45-59   |  478 |      0.987 |   0.976 |   0.996 |        1 |
| ltx23       | 60+     |  460 |      0.998 |   0.996 |   0.999 |        1 |
| wan22       | 18-29   |  388 |      1     |   1     |   1     |        1 |
| wan22       | 30-44   |  377 |      1     |   1     |   1     |        1 |
| wan22       | 45-59   |  398 |      1     |   1     |   1     |        1 |
| wan22       | 60+     |  403 |      1     |   1     |   1     |        1 |
| hunyuan15   | 18-29   |  242 |      0.999 |   0.998 |   1     |        1 |
| hunyuan15   | 30-44   |  248 |      0.999 |   0.996 |   1     |        1 |
| hunyuan15   | 45-59   |  250 |      1     |   1     |   1     |        1 |
| hunyuan15   | 60+     |  249 |      1     |   1     |   1     |        1 |
| all         | 18-29   | 1099 |      0.993 |   0.986 |   0.997 |        1 |
| all         | 30-44   | 1096 |      0.993 |   0.987 |   0.998 |        1 |
| all         | 45-59   | 1126 |      0.995 |   0.99  |   0.998 |        1 |
| all         | 60+     | 1112 |      0.999 |   0.998 |   1     |        1 |

### Mean score by scene factor (all generators pooled)

| factor           | level      |    n |   estimate |   ci_lo |   ci_hi |
|:-----------------|:-----------|-----:|-----------:|--------:|--------:|
| setting          | cafe       |  376 |      0.99  |   0.955 |   0.999 |
| setting          | classroom  |  373 |      1     |   1     |   1     |
| setting          | corridor   |  493 |      1     |   0.999 |   1     |
| setting          | kitchen    |  441 |      0.987 |   0.947 |   1     |
| setting          | library    |  534 |      0.993 |   0.985 |   1     |
| setting          | livingroom |  530 |      1     |   1     |   1     |
| setting          | lobby      |  345 |      0.979 |   0.952 |   1     |
| setting          | office     |  357 |      0.997 |   0.992 |   1     |
| setting          | plainwall  |  553 |      0.999 |   0.998 |   1     |
| setting          | studio     |  431 |      0.999 |   0.999 |   1     |
| lighting         | backlit    |  790 |      0.999 |   0.996 |   1     |
| lighting         | harsh      |  632 |      0.997 |   0.992 |   1     |
| lighting         | lowlight   |  784 |      0.98  |   0.96  |   0.996 |
| lighting         | overcast   |  692 |      0.997 |   0.987 |   1     |
| lighting         | softwindow |  821 |      1     |   1     |   1     |
| lighting         | warmlamp   |  714 |      0.999 |   0.997 |   1     |
| behavior         | laugh      |  500 |      0.997 |   0.988 |   1     |
| behavior         | listen     |  680 |      0.998 |   0.996 |   1     |
| behavior         | pause      |  520 |      0.998 |   0.987 |   1     |
| behavior         | read       |  576 |      0.998 |   0.994 |   0.999 |
| behavior         | smile      |  538 |      1     |   1     |   1     |
| behavior         | speak      |  530 |      0.994 |   0.979 |   1     |
| behavior         | think      |  509 |      0.986 |   0.952 |   1     |
| behavior         | turn       |  580 |      0.988 |   0.965 |   1     |
| camera           | slowsway   | 2225 |      0.995 |   0.989 |   0.999 |
| camera           | static     | 2208 |      0.995 |   0.988 |   0.999 |
| duration_nominal | 5.0        | 2227 |      0.997 |   0.994 |   0.999 |
| duration_nominal | 6.0        | 2206 |      0.993 |   0.984 |   0.999 |

Per-generator scene-factor and 56-cell rows: `tables/score_by_breakdown.csv`.

### Subgroup gap (max - min of level means)

A gap is max - min, so it is never negative and its interval cannot include 0; it is a size, not a test of a difference. Over many levels with few clips each (56 cells; HunyuanVideo has 9 groups per cell) the gap also grows with noise, so compare it with the per-level intervals in `tables/score_by_breakdown.csv`. Levels seen in a single counterfactual group have no interval.

| generator   | attribute        |   n_levels |   gap |   ci_lo |   ci_hi | max_level     | min_level            |
|:------------|:-----------------|-----------:|------:|--------:|--------:|:--------------|:---------------------|
| ltx23       | race             |          7 | 0.037 |   0.014 |   0.066 | black         | east_asian           |
| ltx23       | gender           |          2 | 0.002 |   0     |   0.007 | m             | f                    |
| ltx23       | age_band         |          4 | 0.015 |   0.005 |   0.029 | 60+           | 18-29                |
| ltx23       | cell             |         56 | 0.075 |   0.042 |   0.153 | white__m__60+ | east_asian__f__18-29 |
| ltx23       | setting          |         10 | 0.042 |   0.017 |   0.128 | livingroom    | lobby                |
| ltx23       | lighting         |          6 | 0.049 |   0.011 |   0.096 | softwindow    | lowlight             |
| ltx23       | behavior         |          8 | 0.032 |   0.01  |   0.128 | smile         | think                |
| ltx23       | camera           |          2 | 0.001 |   0     |   0.023 | slowsway      | static               |
| ltx23       | duration_nominal |          2 | 0.007 |   0     |   0.026 | 5.0           | 6.0                  |
| wan22       | race             |          7 | 0     |   0     |   0.001 | white         | east_asian           |
| wan22       | gender           |          2 | 0     |   0     |   0     | f             | m                    |
| wan22       | age_band         |          4 | 0     |   0     |   0     | 60+           | 18-29                |
| wan22       | cell             |         56 | 0.001 |   0.001 |   0.002 | white__f__60+ | east_asian__m__18-29 |
| wan22       | setting          |         10 | 0     |   0     |   0.001 | studio        | plainwall            |
| wan22       | lighting         |          6 | 0     |   0     |   0.001 | warmlamp      | overcast             |
| wan22       | behavior         |          8 | 0     |   0     |   0.001 | smile         | read                 |
| wan22       | camera           |          2 | 0     |   0     |   0     | static        | slowsway             |
| wan22       | duration_nominal |          2 | 0     |   0     |   0     | 5.0           | 6.0                  |
| hunyuan15   | race             |          7 | 0.003 |   0.001 |   0.007 | white         | east_asian           |
| hunyuan15   | gender           |          2 | 0.001 |   0     |   0.002 | f             | m                    |
| hunyuan15   | age_band         |          4 | 0.001 |   0     |   0.004 | 60+           | 30-44                |
| hunyuan15   | cell             |         56 | 0.017 |   0.002 |   0.047 | white__f__60+ | east_asian__m__30-44 |
| hunyuan15   | setting          |         10 | 0.002 |   0     |   0.004 | corridor      | plainwall            |
| hunyuan15   | lighting         |          6 | 0.002 |   0     |   0.004 | backlit       | overcast             |
| hunyuan15   | behavior         |          8 | 0.002 |   0     |   0.004 | smile         | read                 |
| hunyuan15   | camera           |          2 | 0     |   0     |   0.001 | slowsway      | static               |
| hunyuan15   | duration_nominal |          2 | 0.001 |   0     |   0.002 | 5.0           | 6.0                  |
| all         | race             |          7 | 0.017 |   0.007 |   0.03  | black         | east_asian           |
| all         | gender           |          2 | 0.001 |   0     |   0.003 | m             | f                    |
| all         | age_band         |          4 | 0.007 |   0.002 |   0.013 | 60+           | 18-29                |
| all         | cell             |         56 | 0.031 |   0.018 |   0.064 | white__m__60+ | east_asian__f__18-29 |
| all         | setting          |         10 | 0.021 |   0.007 |   0.053 | livingroom    | lobby                |
| all         | lighting         |          6 | 0.02  |   0.005 |   0.04  | softwindow    | lowlight             |
| all         | behavior         |          8 | 0.014 |   0.005 |   0.047 | smile         | think                |
| all         | camera           |          2 | 0.001 |   0     |   0.009 | slowsway      | static               |
| all         | duration_nominal |          2 | 0.004 |   0     |   0.013 | 5.0           | 6.0                  |

### CF spread (mean over groups of the std of score across the group's cells)

| generator   |   n_groups |   cf_spread |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.03  |   0.013 |   0.049 |    0.001 | 0.214 |
| wan22       |         36 |       0     |   0     |   0     |    0     | 0.001 |
| hunyuan15   |         18 |       0.003 |   0     |   0.007 |    0     | 0.031 |

### Factor attribution

OLS with every factor as a fixed effect, type-II ANOVA. `ss_share` is the factor's type-II sum of squares over the total sum of squares (type-II shares need not add to 1). Scene factors are constant within a counterfactual group, so their effects are estimated from between-group differences only. The OLS F tests treat clips as independent although clips are clustered in counterfactual groups, so their p values are optimistic; use the group-bootstrap intervals above for inference.

| factor           |   df |    sum_sq | F      | p         | partial_eta2   |   ss_share |
|:-----------------|-----:|----------:|:-------|:----------|:---------------|-----------:|
| race             |    6 | 0.1334    | 12.74  | 2.637e-14 | 0.01708        |  0.01579   |
| gender           |    1 | 0.0008712 | 0.4991 | 0.4799    | 0.0001135      |  0.0001031 |
| age_band         |    3 | 0.02762   | 5.274  | 0.001249  | 0.003585       |  0.003268  |
| setting          |    9 | 0.1732    | 11.02  | 3.656e-17 | 0.02207        |  0.0205    |
| lighting         |    5 | 0.1696    | 19.43  | 3.475e-19 | 0.02162        |  0.02007   |
| behavior         |    7 | 0.09629   | 7.881  | 1.593e-09 | 0.01239        |  0.0114    |
| camera           |    1 | 0.013     | 7.45   | 0.006369  | 0.001691       |  0.001539  |
| duration_nominal |    1 | 0.0009678 | 0.5544 | 0.4565    | 0.0001261      |  0.0001145 |
| generator        |    2 | 0.1235    | 35.37  | 5.777e-16 | 0.01583        |  0.01461   |
| Residual         | 4397 | 7.675     |        |           |                |  0.9083    |

Lighting x race interaction (added to the same OLS):

| term            |   df |   sum_sq |     F |         p |   partial_eta2 |
|:----------------|-----:|---------:|------:|----------:|---------------:|
| lighting x race |   30 |   0.2271 | 4.439 | 1.102e-14 |        0.02959 |

Mixed model `score ~ factors + (1 | counterfactual_group)` (REML) variance components (fixed effects: `tables/factor_mixed_fixed.csv`):

| component                               |   variance | converged   |
|:----------------------------------------|-----------:|:------------|
| counterfactual_group (random intercept) |   0        | True        |
| residual                                |   0.001704 | True        |
| ICC (group share of random variance)    |   0        | True        |

A group variance at or near 0 is a boundary estimate: setting, lighting, behavior, camera and duration are fixed per group and absorb most between-group variation, leaving little for the random intercept. It does not mean scenes do not matter.

## 6.2 Provisional (threshold 0.5, provisional)

### Detection rate by generator (provisional)

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1878 |      0.994 |   0.988 |   0.998 |
| wan22       | 1566 |      1     |   1     |   1     |
| hunyuan15   |  989 |      1     |   1     |   1     |
| all         | 4433 |      0.998 |   0.995 |   0.999 |

### Detection rate by race (provisional)

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 273 |      1     |   1     |   1     |
| ltx23       | east_asian      | 270 |      0.97  |   0.945 |   0.992 |
| ltx23       | indian          | 277 |      0.996 |   0.989 |   1     |
| ltx23       | latino          | 262 |      1     |   1     |   1     |
| ltx23       | mena            | 267 |      1     |   1     |   1     |
| ltx23       | southeast_asian | 271 |      0.993 |   0.981 |   1     |
| ltx23       | white           | 258 |      1     |   1     |   1     |
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
| all         | east_asian      | 637 |      0.987 |   0.976 |   0.997 |
| all         | indian          | 649 |      0.998 |   0.995 |   1     |
| all         | latino          | 623 |      1     |   1     |   1     |
| all         | mena            | 631 |      1     |   1     |   1     |
| all         | southeast_asian | 643 |      0.997 |   0.992 |   1     |
| all         | white           | 619 |      1     |   1     |   1     |

### Detection rate by gender (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.992 |   0.985 |   0.999 |
| ltx23       | m       |  947 |      0.996 |   0.99  |   1     |
| wan22       | f       |  785 |      1     |   1     |   1     |
| wan22       | m       |  781 |      1     |   1     |   1     |
| hunyuan15   | f       |  495 |      1     |   1     |   1     |
| hunyuan15   | m       |  494 |      1     |   1     |   1     |
| all         | f       | 2211 |      0.997 |   0.994 |   1     |
| all         | m       | 2222 |      0.998 |   0.996 |   1     |

### Detection rate by age band (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  469 |      0.991 |   0.983 |   0.998 |
| ltx23       | 30-44   |  471 |      0.992 |   0.979 |   1     |
| ltx23       | 45-59   |  478 |      0.994 |   0.986 |   1     |
| ltx23       | 60+     |  460 |      1     |   1     |   1     |
| wan22       | 18-29   |  388 |      1     |   1     |   1     |
| wan22       | 30-44   |  377 |      1     |   1     |   1     |
| wan22       | 45-59   |  398 |      1     |   1     |   1     |
| wan22       | 60+     |  403 |      1     |   1     |   1     |
| hunyuan15   | 18-29   |  242 |      1     |   1     |   1     |
| hunyuan15   | 30-44   |  248 |      1     |   1     |   1     |
| hunyuan15   | 45-59   |  250 |      1     |   1     |   1     |
| hunyuan15   | 60+     |  249 |      1     |   1     |   1     |
| all         | 18-29   | 1099 |      0.996 |   0.993 |   0.999 |
| all         | 30-44   | 1096 |      0.996 |   0.991 |   1     |
| all         | 45-59   | 1126 |      0.997 |   0.994 |   1     |
| all         | 60+     | 1112 |      1     |   1     |   1     |

### Detection-rate gap (provisional)

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level       | min_level            |
|:------------|:-----------------|------:|--------:|--------:|:----------------|:---------------------|
| ltx23       | race             | 0.03  |   0.008 |   0.055 | black           | east_asian           |
| ltx23       | gender           | 0.003 |   0     |   0.01  | m               | f                    |
| ltx23       | age_band         | 0.009 |   0.004 |   0.021 | 60+             | 18-29                |
| ltx23       | cell             | 0.088 |   0.029 |   0.2   | black__f__18-29 | east_asian__f__45-59 |
| ltx23       | setting          | 0.024 |   0.009 |   0.073 | classroom       | lobby                |
| ltx23       | lighting         | 0.025 |   0.006 |   0.052 | harsh           | lowlight             |
| ltx23       | behavior         | 0.018 |   0.006 |   0.073 | pause           | think                |
| ltx23       | camera           | 0.001 |   0     |   0.012 | static          | slowsway             |
| ltx23       | duration_nominal | 0.002 |   0     |   0.014 | 5.0             | 6.0                  |
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
| all         | race             | 0.013 |   0.003 |   0.024 | black           | east_asian           |
| all         | gender           | 0.001 |   0     |   0.004 | m               | f                    |
| all         | age_band         | 0.004 |   0.002 |   0.009 | 60+             | 30-44                |
| all         | cell             | 0.036 |   0.012 |   0.081 | black__f__18-29 | east_asian__f__45-59 |
| all         | setting          | 0.012 |   0.004 |   0.028 | classroom       | lobby                |
| all         | lighting         | 0.01  |   0.002 |   0.022 | harsh           | lowlight             |
| all         | behavior         | 0.008 |   0.003 |   0.027 | pause           | think                |
| all         | camera           | 0     |   0     |   0.005 | static          | slowsway             |
| all         | duration_nominal | 0.001 |   0     |   0.006 | 5.0             | 6.0                  |

### Flip rate (provisional): share of groups whose clips get different decisions

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.167 |   0.056 |   0.306 |        0 |     1 |
| wan22       |         36 |       0     |   0     |   0     |        0 |     0 |
| hunyuan15   |         18 |       0     |   0     |   0     |        0 |     0 |

### Sensitivity: inclusion set

| set     | generator   |    n |   mean_score |   provisional_detection_rate |
|:--------|:------------|-----:|-------------:|-----------------------------:|
| all     | hunyuan15   | 1008 |        0.999 |                        1     |
| all     | ltx23       | 2016 |        0.98  |                        0.988 |
| all     | wan22       | 2016 |        1     |                        1     |
| primary | hunyuan15   |  989 |        0.999 |                        1     |
| primary | ltx23       | 1878 |        0.989 |                        0.994 |
| primary | wan22       | 1566 |        1     |                        1     |

## 6.3 Pending until reals exist

| metric                                                      | status   | reason                |
|:------------------------------------------------------------|:---------|:----------------------|
| AUC, AP, EER, TPR@5%FPR (overall, per generator)            | pending  | needs reals (real_b1) |
| Calibrated threshold (5% FPR on fps-matched reals)          | pending  | needs reals (real_b1) |
| Real FPR by perceived race, gender, age band, race x gender | pending  | needs reals (real_b1) |
| Detection rate and flip rate at the calibrated threshold    | pending  | needs reals (real_b1) |
| Worst-subgroup AUC, subgroup AUC gap                        | pending  | needs reals (real_b1) |
| ROC curves per generator; real FPR by subgroup (figures)    | pending  | needs reals (real_b1) |

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

## Files

`manifest_used.csv` (every clip of the active batches with render/score/inclusion flags), `scores.csv` (score per scored clip), `tables/*.csv`, `figures/*`, `snapshot_meta.json`.

