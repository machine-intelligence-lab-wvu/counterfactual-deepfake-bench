# d3 / native_up: snapshot 20261021-2056

> **Detector training data.** D3 is training-free: a statistic of frozen X-CLIP-B/16 features, no detector weights. Its score is 1/(1+std) of the second-order feature; only rank metrics and the calibrated threshold are meaningful, the provisional 0.5 threshold is not.

> **Provisional threshold.** Every detection rate and flip rate below uses the detector's default threshold (0.5; none official (training-free statistic); 0.5 on 1/(1+std) is arbitrary - use the calibrated threshold). They will be replaced by the 5%-real-FPR threshold once reals exist (section 6.3).

## Settings

| setting           | value                                                                                  |
|:------------------|:---------------------------------------------------------------------------------------|
| detector          | d3 1+efab2602                                                                          |
| checkpoint_sha256 | b5db836d57b7e22001cb2bab581719e910b4c571d926fe839b5d07bc0ba2d03e                       |
| view              | native_up (view_hash 4db0c07a46c4b8d9)                                                 |
| ffmpeg            | ffmpeg version 7.1.1 Copyright (c) 2000-2025 the FFmpeg developers                     |
| batches           | fake_b1, fake_b2, real_all                                                             |
| inclusion set     | primary (technical QC pass AND face QC pass)                                           |
| bootstrap         | 1000 resamples of whole counterfactual groups, seed 20261020, 95% percentile intervals |
| git commit        | 4e41a35865f4-dirty                                                                     |
| created           | 2026-10-21T20:56:50Z                                                                   |

Detector preprocessing on top of the view:

| field       | value                                                                                                           |
|:------------|:----------------------------------------------------------------------------------------------------------------|
| source      | Zig-HS/D3@c798fbc57fe0c4198d63a73732c2c0f9e4b4816c utils/video2frame.py + data/datasets.py + models/D3_model.py |
| frames      | ffmpeg -t 3 -vf fps=8 -> JPEG (ffmpeg default mjpeg), from view start                                           |
| frames_used | first 16 (8 if 8-15 available)                                                                                  |
| channels    | BGR (cv2.imread, as in the official dataset)                                                                    |
| crop        | centre, trim 10% each side of the longer dimension                                                              |
| resize      | [224, 224, 'cv2.INTER_LINEAR']                                                                                  |
| normalize   | {'mean': [0.485, 0.456, 0.406], 'std': [0.229, 0.224, 0.225], 'max_pixel_value': 255}                           |
| encoder     | microsoft/xclip-base-patch16@d6184e3fd8780d04c85d0f1eabe5f94bf44d98f6 vision tower, pooler_output               |
| statistic   | std of first differences of consecutive-frame L2 distances (loss l2)                                            |
| score       | 1 / (1 + std)                                                                                                   |
| precision   | fp32, TF32 off                                                                                                  |

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

- LTX 2.3: mean score 0.303 [0.288, 0.319], median 0.295, n = 1878.
- Wan 2.2: mean score 0.341 [0.324, 0.359], median 0.339, n = 1566.
- HunyuanVideo 1.5: mean score 0.344 [0.314, 0.373], median 0.344, n = 989.
- Provisional detection rate (score >= 0.5), LTX 2.3: 3.1% [1.7, 4.7].
- Provisional detection rate (score >= 0.5), Wan 2.2: 4.5% [2.5, 6.9].
- Provisional detection rate (score >= 0.5), HunyuanVideo 1.5: 6.7% [2.9, 11.5].
- Provisional detection rate (score >= 0.5), all: 4.4% [2.6, 6.1].
- Largest race score gap: Wan 2.2 0.049 [0.034, 0.068] (black 0.374 vs east_asian 0.325).
- Largest gender score gap: LTX 2.3 0.015 [0.004, 0.026] (m 0.310 vs f 0.296).
- Largest age band score gap: Wan 2.2 0.056 [0.037, 0.071] (60+ 0.369 vs 18-29 0.313).
- Largest cell score gap: HunyuanVideo 1.5 0.124 [0.116, 0.196] (white__m__60+ 0.409 vs east_asian__f__30-44 0.285).
- Largest scene-factor gap (all generators): behavior 0.132 [0.102, 0.167] (laugh vs speak).
- Largest partial eta squared: behavior 0.109, age_band 0.059, generator 0.056; residual holds 68.7% of total SS.
- CF spread, LTX 2.3: 0.075 [0.071, 0.080] over 36 groups (max 0.114).
- CF spread, Wan 2.2: 0.073 [0.068, 0.077] over 36 groups (max 0.106).
- CF spread, HunyuanVideo 1.5: 0.082 [0.077, 0.087] over 18 groups (max 0.106).
- Provisional flip rate, LTX 2.3: 52.8% of 36 groups [36.1, 69.4].
- Provisional flip rate, Wan 2.2: 58.3% of 36 groups [41.7, 72.2].
- Provisional flip rate, HunyuanVideo 1.5: 72.2% of 18 groups [50.0, 92.9].

## 6.1 Fakes only, no threshold

### Mean score by generator

| generator   |    n |   n_groups |   estimate |   ci_lo |   ci_hi |    sd |   median |   q05 |   q95 |
|:------------|-----:|-----------:|-----------:|--------:|--------:|------:|---------:|------:|------:|
| ltx23       | 1878 |         36 |      0.303 |   0.288 |   0.319 | 0.091 |    0.295 | 0.166 | 0.467 |
| wan22       | 1566 |         36 |      0.341 |   0.324 |   0.359 | 0.091 |    0.339 | 0.194 | 0.493 |
| hunyuan15   |  989 |         18 |      0.344 |   0.314 |   0.373 | 0.104 |    0.344 | 0.18  | 0.517 |
| all         | 4433 |         36 |      0.326 |   0.31  |   0.341 | 0.096 |    0.321 | 0.176 | 0.493 |

### Mean score by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:----------------|----:|-----------:|--------:|--------:|---------:|
| ltx23       | black           | 273 |      0.323 |   0.306 |   0.34  |    0.32  |
| ltx23       | east_asian      | 270 |      0.286 |   0.27  |   0.304 |    0.273 |
| ltx23       | indian          | 277 |      0.298 |   0.28  |   0.316 |    0.29  |
| ltx23       | latino          | 262 |      0.306 |   0.289 |   0.324 |    0.296 |
| ltx23       | mena            | 267 |      0.309 |   0.29  |   0.328 |    0.299 |
| ltx23       | southeast_asian | 271 |      0.289 |   0.273 |   0.304 |    0.288 |
| ltx23       | white           | 258 |      0.31  |   0.292 |   0.328 |    0.305 |
| wan22       | black           | 217 |      0.374 |   0.356 |   0.392 |    0.371 |
| wan22       | east_asian      | 226 |      0.325 |   0.303 |   0.347 |    0.323 |
| wan22       | indian          | 230 |      0.343 |   0.323 |   0.363 |    0.337 |
| wan22       | latino          | 219 |      0.348 |   0.327 |   0.368 |    0.345 |
| wan22       | mena            | 225 |      0.327 |   0.308 |   0.344 |    0.324 |
| wan22       | southeast_asian | 229 |      0.334 |   0.312 |   0.358 |    0.328 |
| wan22       | white           | 220 |      0.341 |   0.322 |   0.358 |    0.34  |
| hunyuan15   | black           | 141 |      0.357 |   0.328 |   0.387 |    0.361 |
| hunyuan15   | east_asian      | 141 |      0.342 |   0.308 |   0.375 |    0.339 |
| hunyuan15   | indian          | 142 |      0.337 |   0.309 |   0.363 |    0.345 |
| hunyuan15   | latino          | 142 |      0.342 |   0.309 |   0.377 |    0.332 |
| hunyuan15   | mena            | 139 |      0.35  |   0.316 |   0.382 |    0.35  |
| hunyuan15   | southeast_asian | 143 |      0.333 |   0.301 |   0.366 |    0.34  |
| hunyuan15   | white           | 141 |      0.346 |   0.317 |   0.375 |    0.342 |
| all         | black           | 631 |      0.348 |   0.335 |   0.361 |    0.344 |
| all         | east_asian      | 637 |      0.312 |   0.295 |   0.33  |    0.301 |
| all         | indian          | 649 |      0.322 |   0.307 |   0.337 |    0.318 |
| all         | latino          | 623 |      0.329 |   0.312 |   0.346 |    0.323 |
| all         | mena            | 631 |      0.324 |   0.306 |   0.341 |    0.317 |
| all         | southeast_asian | 643 |      0.315 |   0.298 |   0.332 |    0.314 |
| all         | white           | 619 |      0.329 |   0.313 |   0.345 |    0.326 |

### Mean score by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | f       |  931 |      0.296 |   0.278 |   0.313 |    0.284 |
| ltx23       | m       |  947 |      0.31  |   0.294 |   0.326 |    0.306 |
| wan22       | f       |  785 |      0.336 |   0.318 |   0.353 |    0.334 |
| wan22       | m       |  781 |      0.347 |   0.327 |   0.365 |    0.345 |
| hunyuan15   | f       |  495 |      0.34  |   0.309 |   0.37  |    0.342 |
| hunyuan15   | m       |  494 |      0.347 |   0.319 |   0.376 |    0.347 |
| all         | f       | 2211 |      0.32  |   0.305 |   0.335 |    0.314 |
| all         | m       | 2222 |      0.331 |   0.316 |   0.347 |    0.326 |

### Mean score by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | 18-29   |  469 |      0.276 |   0.26  |   0.294 |    0.264 |
| ltx23       | 30-44   |  471 |      0.293 |   0.279 |   0.311 |    0.286 |
| ltx23       | 45-59   |  478 |      0.312 |   0.295 |   0.329 |    0.299 |
| ltx23       | 60+     |  460 |      0.331 |   0.311 |   0.349 |    0.324 |
| wan22       | 18-29   |  388 |      0.313 |   0.294 |   0.332 |    0.308 |
| wan22       | 30-44   |  377 |      0.329 |   0.309 |   0.35  |    0.329 |
| wan22       | 45-59   |  398 |      0.353 |   0.335 |   0.372 |    0.351 |
| wan22       | 60+     |  403 |      0.369 |   0.347 |   0.388 |    0.372 |
| hunyuan15   | 18-29   |  242 |      0.325 |   0.293 |   0.358 |    0.323 |
| hunyuan15   | 30-44   |  248 |      0.339 |   0.308 |   0.37  |    0.337 |
| hunyuan15   | 45-59   |  250 |      0.332 |   0.299 |   0.366 |    0.32  |
| hunyuan15   | 60+     |  249 |      0.379 |   0.353 |   0.404 |    0.378 |
| all         | 18-29   | 1099 |      0.3   |   0.285 |   0.315 |    0.291 |
| all         | 30-44   | 1096 |      0.316 |   0.3   |   0.332 |    0.31  |
| all         | 45-59   | 1126 |      0.331 |   0.313 |   0.347 |    0.324 |
| all         | 60+     | 1112 |      0.356 |   0.338 |   0.372 |    0.357 |

### Mean score by scene factor (all generators pooled)

| factor           | level      |    n |   estimate |   ci_lo |   ci_hi |
|:-----------------|:-----------|-----:|-----------:|--------:|--------:|
| setting          | cafe       |  376 |      0.276 |   0.232 |   0.311 |
| setting          | classroom  |  373 |      0.322 |   0.258 |   0.428 |
| setting          | corridor   |  493 |      0.327 |   0.245 |   0.36  |
| setting          | kitchen    |  441 |      0.298 |   0.274 |   0.314 |
| setting          | library    |  534 |      0.355 |   0.275 |   0.404 |
| setting          | livingroom |  530 |      0.343 |   0.315 |   0.377 |
| setting          | lobby      |  345 |      0.382 |   0.365 |   0.399 |
| setting          | office     |  357 |      0.318 |   0.275 |   0.333 |
| setting          | plainwall  |  553 |      0.293 |   0.27  |   0.307 |
| setting          | studio     |  431 |      0.343 |   0.317 |   0.371 |
| lighting         | backlit    |  790 |      0.353 |   0.323 |   0.38  |
| lighting         | harsh      |  632 |      0.323 |   0.274 |   0.383 |
| lighting         | lowlight   |  784 |      0.334 |   0.294 |   0.381 |
| lighting         | overcast   |  692 |      0.309 |   0.274 |   0.342 |
| lighting         | softwindow |  821 |      0.293 |   0.262 |   0.319 |
| lighting         | warmlamp   |  714 |      0.342 |   0.305 |   0.369 |
| behavior         | laugh      |  500 |      0.393 |   0.338 |   0.425 |
| behavior         | listen     |  680 |      0.326 |   0.313 |   0.35  |
| behavior         | pause      |  520 |      0.299 |   0.252 |   0.314 |
| behavior         | read       |  576 |      0.277 |   0.267 |   0.303 |
| behavior         | smile      |  538 |      0.351 |   0.331 |   0.368 |
| behavior         | speak      |  530 |      0.261 |   0.243 |   0.275 |
| behavior         | think      |  509 |      0.37  |   0.322 |   0.399 |
| behavior         | turn       |  580 |      0.336 |   0.311 |   0.362 |
| camera           | slowsway   | 2225 |      0.321 |   0.301 |   0.343 |
| camera           | static     | 2208 |      0.33  |   0.307 |   0.352 |
| duration_nominal | 5.0        | 2227 |      0.326 |   0.305 |   0.348 |
| duration_nominal | 6.0        | 2206 |      0.325 |   0.302 |   0.348 |

Per-generator scene-factor and 56-cell rows: `tables/score_by_breakdown.csv`.

### Subgroup gap (max - min of level means)

A gap is max - min, so it is never negative and its interval cannot include 0; it is a size, not a test of a difference. Over many levels with few clips each (56 cells; HunyuanVideo has 9 groups per cell) the gap also grows with noise, so compare it with the per-level intervals in `tables/score_by_breakdown.csv`. Levels seen in a single counterfactual group have no interval.

| generator   | attribute        |   n_levels |   gap |   ci_lo |   ci_hi | max_level     | min_level            |
|:------------|:-----------------|-----------:|------:|--------:|--------:|:--------------|:---------------------|
| ltx23       | race             |          7 | 0.037 |   0.023 |   0.053 | black         | east_asian           |
| ltx23       | gender           |          2 | 0.015 |   0.004 |   0.026 | m             | f                    |
| ltx23       | age_band         |          4 | 0.055 |   0.036 |   0.073 | 60+           | 18-29                |
| ltx23       | cell             |         56 | 0.117 |   0.103 |   0.161 | white__m__60+ | east_asian__f__18-29 |
| ltx23       | setting          |         10 | 0.103 |   0.083 |   0.166 | lobby         | classroom            |
| ltx23       | lighting         |          6 | 0.083 |   0.062 |   0.14  | warmlamp      | softwindow           |
| ltx23       | behavior         |          8 | 0.121 |   0.089 |   0.172 | laugh         | speak                |
| ltx23       | camera           |          2 | 0.007 |   0.001 |   0.041 | slowsway      | static               |
| ltx23       | duration_nominal |          2 | 0.009 |   0.001 |   0.042 | 5.0           | 6.0                  |
| wan22       | race             |          7 | 0.049 |   0.034 |   0.068 | black         | east_asian           |
| wan22       | gender           |          2 | 0.011 |   0.001 |   0.022 | m             | f                    |
| wan22       | age_band         |          4 | 0.056 |   0.037 |   0.071 | 60+           | 18-29                |
| wan22       | cell             |         56 | 0.117 |   0.11  |   0.165 | black__m__60+ | mena__m__18-29       |
| wan22       | setting          |         10 | 0.109 |   0.088 |   0.199 | lobby         | cafe                 |
| wan22       | lighting         |          6 | 0.05  |   0.037 |   0.137 | backlit       | softwindow           |
| wan22       | behavior         |          8 | 0.118 |   0.102 |   0.178 | laugh         | speak                |
| wan22       | camera           |          2 | 0.015 |   0.001 |   0.049 | static        | slowsway             |
| wan22       | duration_nominal |          2 | 0.002 |   0.001 |   0.042 | 6.0           | 5.0                  |
| hunyuan15   | race             |          7 | 0.024 |   0.016 |   0.044 | black         | southeast_asian      |
| hunyuan15   | gender           |          2 | 0.007 |   0     |   0.017 | m             | f                    |
| hunyuan15   | age_band         |          4 | 0.054 |   0.039 |   0.07  | 60+           | 18-29                |
| hunyuan15   | cell             |         56 | 0.124 |   0.116 |   0.196 | white__m__60+ | east_asian__f__30-44 |
| hunyuan15   | setting          |         10 | 0.163 |   0.096 |   0.193 | lobby         | cafe                 |
| hunyuan15   | lighting         |          6 | 0.06  |   0.044 |   0.188 | backlit       | softwindow           |
| hunyuan15   | behavior         |          8 | 0.179 |   0.122 |   0.192 | laugh         | read                 |
| hunyuan15   | camera           |          2 | 0.029 |   0.003 |   0.085 | static        | slowsway             |
| hunyuan15   | duration_nominal |          2 | 0.018 |   0.001 |   0.076 | 6.0           | 5.0                  |
| all         | race             |          7 | 0.036 |   0.027 |   0.045 | black         | east_asian           |
| all         | gender           |          2 | 0.011 |   0.006 |   0.017 | m             | f                    |
| all         | age_band         |          4 | 0.056 |   0.042 |   0.068 | 60+           | 18-29                |
| all         | cell             |         56 | 0.1   |   0.092 |   0.131 | black__m__60+ | east_asian__f__18-29 |
| all         | setting          |         10 | 0.107 |   0.081 |   0.164 | lobby         | cafe                 |
| all         | lighting         |          6 | 0.059 |   0.041 |   0.114 | backlit       | softwindow           |
| all         | behavior         |          8 | 0.132 |   0.102 |   0.167 | laugh         | speak                |
| all         | camera           |          2 | 0.009 |   0     |   0.038 | static        | slowsway             |
| all         | duration_nominal |          2 | 0.001 |   0.001 |   0.034 | 5.0           | 6.0                  |

### CF spread (mean over groups of the std of score across the group's cells)

| generator   |   n_groups |   cf_spread |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.075 |   0.071 |   0.08  |    0.074 | 0.114 |
| wan22       |         36 |       0.073 |   0.068 |   0.077 |    0.072 | 0.106 |
| hunyuan15   |         18 |       0.082 |   0.077 |   0.087 |    0.079 | 0.106 |

### Factor attribution

OLS with every factor as a fixed effect, type-II ANOVA. `ss_share` is the factor's type-II sum of squares over the total sum of squares (type-II shares need not add to 1). Scene factors are constant within a counterfactual group, so their effects are estimated from between-group differences only. The OLS F tests treat clips as independent although clips are clustered in counterfactual groups, so their p values are optimistic; use the group-bootstrap intervals above for inference.

| factor           |   df |   sum_sq | F     | p          | partial_eta2   |   ss_share |
|:-----------------|-----:|---------:|:------|:-----------|:---------------|-----------:|
| race             |    6 |  0.5152  | 13.45 | 3.559e-15  | 0.01802        |  0.01261   |
| gender           |    1 |  0.1672  | 26.19 | 3.222e-07  | 0.005922       |  0.004092  |
| age_band         |    3 |  1.75    | 91.39 | 2.26e-57   | 0.0587         |  0.04284   |
| setting          |    9 |  0.6567  | 11.43 | 6.927e-18  | 0.02286        |  0.01607   |
| lighting         |    5 |  0.2059  | 6.449 | 5.572e-06  | 0.007281       |  0.005038  |
| behavior         |    7 |  3.419   | 76.52 | 4.761e-105 | 0.1086         |  0.08368   |
| camera           |    1 |  0.01445 | 2.264 | 0.1325     | 0.0005147      |  0.0003537 |
| duration_nominal |    1 |  0.01249 | 1.956 | 0.162      | 0.0004446      |  0.0003056 |
| generator        |    2 |  1.656   | 129.7 | 1.837e-55  | 0.05571        |  0.04053   |
| Residual         | 4397 | 28.07    |       |            |                |  0.687     |

Lighting x race interaction (added to the same OLS):

| term            |   df |   sum_sq |     F |      p |   partial_eta2 |
|:----------------|-----:|---------:|------:|-------:|---------------:|
| lighting x race |   30 |   0.2507 | 1.312 | 0.1191 |       0.008931 |

Mixed model `score ~ factors + (1 | counterfactual_group)` (REML) variance components (fixed effects: `tables/factor_mixed_fixed.csv`):

| component                               |   variance | converged   |
|:----------------------------------------|-----------:|:------------|
| counterfactual_group (random intercept) |   0.00052  | True        |
| residual                                |   0.006216 | True        |
| ICC (group share of random variance)    |   0.07719  | True        |

A group variance at or near 0 is a boundary estimate: setting, lighting, behavior, camera and duration are fixed per group and absorb most between-group variation, leaving little for the random intercept. It does not mean scenes do not matter.

## 6.2 Provisional (threshold 0.5, provisional)

### Detection rate by generator (provisional)

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1878 |      0.031 |   0.017 |   0.047 |
| wan22       | 1566 |      0.045 |   0.025 |   0.069 |
| hunyuan15   |  989 |      0.067 |   0.029 |   0.115 |
| all         | 4433 |      0.044 |   0.026 |   0.061 |

### Detection rate by race (provisional)

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 273 |      0.048 |   0.022 |   0.078 |
| ltx23       | east_asian      | 270 |      0.015 |   0     |   0.034 |
| ltx23       | indian          | 277 |      0.018 |   0.003 |   0.037 |
| ltx23       | latino          | 262 |      0.027 |   0.008 |   0.051 |
| ltx23       | mena            | 267 |      0.041 |   0.015 |   0.069 |
| ltx23       | southeast_asian | 271 |      0.026 |   0.008 |   0.048 |
| ltx23       | white           | 258 |      0.043 |   0.018 |   0.073 |
| wan22       | black           | 217 |      0.078 |   0.032 |   0.134 |
| wan22       | east_asian      | 226 |      0.027 |   0.008 |   0.053 |
| wan22       | indian          | 230 |      0.057 |   0.023 |   0.098 |
| wan22       | latino          | 219 |      0.064 |   0.031 |   0.104 |
| wan22       | mena            | 225 |      0.022 |   0.004 |   0.048 |
| wan22       | southeast_asian | 229 |      0.044 |   0.009 |   0.096 |
| wan22       | white           | 220 |      0.023 |   0.004 |   0.049 |
| hunyuan15   | black           | 141 |      0.057 |   0.015 |   0.105 |
| hunyuan15   | east_asian      | 141 |      0.099 |   0.032 |   0.173 |
| hunyuan15   | indian          | 142 |      0.049 |   0     |   0.117 |
| hunyuan15   | latino          | 142 |      0.092 |   0.036 |   0.153 |
| hunyuan15   | mena            | 139 |      0.079 |   0.036 |   0.125 |
| hunyuan15   | southeast_asian | 143 |      0.028 |   0     |   0.077 |
| hunyuan15   | white           | 141 |      0.064 |   0.019 |   0.11  |
| all         | black           | 631 |      0.06  |   0.032 |   0.094 |
| all         | east_asian      | 637 |      0.038 |   0.017 |   0.06  |
| all         | indian          | 649 |      0.039 |   0.018 |   0.061 |
| all         | latino          | 623 |      0.055 |   0.032 |   0.077 |
| all         | mena            | 631 |      0.043 |   0.023 |   0.062 |
| all         | southeast_asian | 643 |      0.033 |   0.011 |   0.059 |
| all         | white           | 619 |      0.04  |   0.022 |   0.059 |

### Detection rate by gender (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.031 |   0.015 |   0.053 |
| ltx23       | m       |  947 |      0.031 |   0.017 |   0.046 |
| wan22       | f       |  785 |      0.041 |   0.022 |   0.067 |
| wan22       | m       |  781 |      0.049 |   0.023 |   0.077 |
| hunyuan15   | f       |  495 |      0.055 |   0.02  |   0.102 |
| hunyuan15   | m       |  494 |      0.079 |   0.032 |   0.132 |
| all         | f       | 2211 |      0.04  |   0.024 |   0.057 |
| all         | m       | 2222 |      0.048 |   0.028 |   0.069 |

### Detection rate by age band (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  469 |      0.013 |   0.004 |   0.025 |
| ltx23       | 30-44   |  471 |      0.034 |   0.017 |   0.057 |
| ltx23       | 45-59   |  478 |      0.029 |   0.012 |   0.051 |
| ltx23       | 60+     |  460 |      0.048 |   0.024 |   0.074 |
| wan22       | 18-29   |  388 |      0.021 |   0.007 |   0.039 |
| wan22       | 30-44   |  377 |      0.04  |   0.016 |   0.07  |
| wan22       | 45-59   |  398 |      0.045 |   0.016 |   0.084 |
| wan22       | 60+     |  403 |      0.072 |   0.038 |   0.109 |
| hunyuan15   | 18-29   |  242 |      0.033 |   0     |   0.079 |
| hunyuan15   | 30-44   |  248 |      0.081 |   0.034 |   0.137 |
| hunyuan15   | 45-59   |  250 |      0.064 |   0.025 |   0.106 |
| hunyuan15   | 60+     |  249 |      0.088 |   0.031 |   0.155 |
| all         | 18-29   | 1099 |      0.02  |   0.01  |   0.032 |
| all         | 30-44   | 1096 |      0.047 |   0.025 |   0.07  |
| all         | 45-59   | 1126 |      0.043 |   0.023 |   0.062 |
| all         | 60+     | 1112 |      0.066 |   0.038 |   0.093 |

### Detection-rate gap (provisional)

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level            | min_level            |
|:------------|:-----------------|------:|--------:|--------:|:---------------------|:---------------------|
| ltx23       | race             | 0.033 |   0.022 |   0.066 | black                | east_asian           |
| ltx23       | gender           | 0.001 |   0     |   0.018 | f                    | m                    |
| ltx23       | age_band         | 0.035 |   0.017 |   0.06  | 60+                  | 18-29                |
| ltx23       | cell             | 0.1   |   0.091 |   0.242 | white__m__60+        | black__m__30-44      |
| ltx23       | setting          | 0.083 |   0.047 |   0.333 | livingroom           | cafe                 |
| ltx23       | lighting         | 0.076 |   0.037 |   0.147 | warmlamp             | softwindow           |
| ltx23       | behavior         | 0.097 |   0.065 |   0.211 | laugh                | pause                |
| ltx23       | camera           | 0.022 |   0.002 |   0.052 | static               | slowsway             |
| ltx23       | duration_nominal | 0.011 |   0.001 |   0.043 | 5.0                  | 6.0                  |
| wan22       | race             | 0.056 |   0.035 |   0.117 | black                | mena                 |
| wan22       | gender           | 0.008 |   0     |   0.031 | m                    | f                    |
| wan22       | age_band         | 0.051 |   0.021 |   0.082 | 60+                  | 18-29                |
| wan22       | cell             | 0.167 |   0.13  |   0.323 | black__m__60+        | black__f__18-29      |
| wan22       | setting          | 0.094 |   0.075 |   0.429 | office               | kitchen              |
| wan22       | lighting         | 0.067 |   0.037 |   0.183 | backlit              | warmlamp             |
| wan22       | behavior         | 0.127 |   0.057 |   0.226 | laugh                | speak                |
| wan22       | camera           | 0.021 |   0.001 |   0.07  | static               | slowsway             |
| wan22       | duration_nominal | 0.003 |   0.001 |   0.05  | 6.0                  | 5.0                  |
| hunyuan15   | race             | 0.071 |   0.041 |   0.145 | east_asian           | southeast_asian      |
| hunyuan15   | gender           | 0.024 |   0.002 |   0.056 | m                    | f                    |
| hunyuan15   | age_band         | 0.055 |   0.021 |   0.115 | 60+                  | 18-29                |
| hunyuan15   | cell             | 0.222 |   0.167 |   0.471 | east_asian__m__30-44 | black__f__18-29      |
| hunyuan15   | setting          | 0.321 |   0.093 |   0.321 | lobby                | cafe                 |
| hunyuan15   | lighting         | 0.106 |   0.05  |   0.321 | lowlight             | overcast             |
| hunyuan15   | behavior         | 0.208 |   0.082 |   0.321 | laugh                | read                 |
| hunyuan15   | camera           | 0.058 |   0.003 |   0.14  | static               | slowsway             |
| hunyuan15   | duration_nominal | 0.013 |   0.002 |   0.107 | 6.0                  | 5.0                  |
| all         | race             | 0.028 |   0.014 |   0.066 | black                | southeast_asian      |
| all         | gender           | 0.008 |   0     |   0.022 | m                    | f                    |
| all         | age_band         | 0.046 |   0.022 |   0.069 | 60+                  | 18-29                |
| all         | cell             | 0.111 |   0.089 |   0.2   | black__m__60+        | east_asian__f__18-29 |
| all         | setting          | 0.087 |   0.058 |   0.202 | library              | cafe                 |
| all         | lighting         | 0.054 |   0.035 |   0.13  | backlit              | softwindow           |
| all         | behavior         | 0.134 |   0.07  |   0.196 | laugh                | speak                |
| all         | camera           | 0.03  |   0.004 |   0.065 | static               | slowsway             |
| all         | duration_nominal | 0.001 |   0     |   0.041 | 5.0                  | 6.0                  |

### Flip rate (provisional): share of groups whose clips get different decisions

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.528 |   0.361 |   0.694 |        1 |     1 |
| wan22       |         36 |       0.583 |   0.417 |   0.722 |        1 |     1 |
| hunyuan15   |         18 |       0.722 |   0.5   |   0.929 |        1 |     1 |

### Sensitivity: inclusion set

| set     | generator   |    n |   mean_score |   provisional_detection_rate |
|:--------|:------------|-----:|-------------:|-----------------------------:|
| all     | hunyuan15   | 1008 |        0.344 |                        0.065 |
| all     | ltx23       | 2016 |        0.302 |                        0.029 |
| all     | wan22       | 2016 |        0.346 |                        0.058 |
| primary | hunyuan15   |  989 |        0.344 |                        0.067 |
| primary | ltx23       | 1878 |        0.303 |                        0.031 |
| primary | wan22       | 1566 |        0.341 |                        0.045 |

## 6.3 Real vs generated (calibrated threshold 0.5042)

The threshold is the score at which 5% of primary real renders (24 and 16 fps pooled) are flagged; one per detector and view, never per subgroup. Each generator is compared with reals rendered at its own fps. Intervals: fakes resample counterfactual groups, reals resample identity clusters (source video). Real labels are perceived (FairFace), not self-reported.

### Calibration

| scope            |   n_renders |   n_sources |   n_identities |   threshold |    fpr |
|:-----------------|------------:|------------:|---------------:|------------:|-------:|
| all real renders |        1855 |         932 |            811 |      0.5042 | 0.0501 |
| 16 fps renders   |         932 |         932 |            811 |      0.5042 | 0.0451 |
| 24 fps renders   |         923 |         923 |            802 |      0.5042 | 0.0553 |

### AUC, AP, EER, TPR at 5% FPR

| generator   | real_fps   |   n_fake |   n_real |   auc |   auc_ci_lo |   auc_ci_hi |    ap |   eer |   tpr_at_5fpr |   detection_rate_global_thr |   det_ci_lo |   det_ci_hi |
|:------------|:-----------|---------:|---------:|------:|------------:|------------:|------:|------:|--------------:|----------------------------:|------------:|------------:|
| ltx23       | 24         |     1878 |      923 | 0.398 |       0.349 |       0.452 | 0.602 | 0.575 |         0.024 |                       0.029 |       0.016 |       0.044 |
| wan22       | 16         |     1566 |      932 | 0.53  |       0.474 |       0.588 | 0.639 | 0.478 |         0.047 |                       0.041 |       0.022 |       0.063 |
| hunyuan15   | 24         |      989 |      923 | 0.523 |       0.438 |       0.613 | 0.543 | 0.48  |         0.059 |                       0.065 |       0.027 |       0.112 |
| all         | 24+16      |     4433 |     1855 | 0.474 |       0.428 |       0.522 | 0.687 | 0.519 |         0.041 |                       0.041 |       0.024 |       0.058 |

### Real FPR by perceived subgroup

| attribute   | level              |   n_renders |   n_identities |   fpr |   ci_lo |   ci_hi |
|:------------|:-------------------|------------:|---------------:|------:|--------:|--------:|
| race        | black              |         123 |             59 | 0.073 |   0.025 |   0.134 |
| race        | east_asian         |         163 |             75 | 0.025 |   0     |   0.058 |
| race        | indian             |          46 |             23 | 0.152 |   0.045 |   0.275 |
| race        | latino             |         115 |             55 | 0.07  |   0.019 |   0.132 |
| race        | mena               |         120 |             59 | 0.058 |   0.011 |   0.123 |
| race        | southeast_asian    |          70 |             34 | 0.043 |   0     |   0.095 |
| race        | white              |        1204 |            523 | 0.045 |   0.032 |   0.059 |
| gender      | f                  |         587 |            266 | 0.043 |   0.023 |   0.065 |
| gender      | m                  |        1254 |            553 | 0.053 |   0.039 |   0.069 |
| age_band    | 18-29              |         594 |            275 | 0.042 |   0.023 |   0.063 |
| age_band    | 30-44              |         626 |            290 | 0.051 |   0.031 |   0.073 |
| age_band    | 45-59              |         300 |            134 | 0.05  |   0.021 |   0.083 |
| age_band    | 60+                |         241 |            112 | 0.058 |   0.029 |   0.094 |
| race_gender | black__f           |          20 |             10 | 0     |   0     |   0     |
| race_gender | black__m           |         103 |             50 | 0.087 |   0.03  |   0.156 |
| race_gender | east_asian__f      |          76 |             35 | 0     |   0     |   0     |
| race_gender | east_asian__m      |          87 |             41 | 0.046 |   0     |   0.104 |
| race_gender | indian__f          |          12 |              6 | 0.167 |   0     |   0.5   |
| race_gender | indian__m          |          34 |             17 | 0.147 |   0.042 |   0.25  |
| race_gender | latino__f          |          20 |             10 | 0     |   0     |   0     |
| race_gender | latino__m          |          95 |             45 | 0.084 |   0.023 |   0.156 |
| race_gender | mena__f            |          34 |             17 | 0.029 |   0     |   0.1   |
| race_gender | mena__m            |          86 |             42 | 0.07  |   0.011 |   0.16  |
| race_gender | southeast_asian__f |          20 |              9 | 0.05  |   0     |   0.167 |
| race_gender | southeast_asian__m |          50 |             25 | 0.04  |   0     |   0.1   |
| race_gender | white__f           |         405 |            183 | 0.052 |   0.027 |   0.08  |
| race_gender | white__m           |         799 |            350 | 0.041 |   0.025 |   0.06  |

### Real FPR gap (max - min across levels; non-negative by construction)

| attribute   |   n_levels |   fpr_gap |   ci_lo |   ci_hi | max_level   |   max_fpr | min_level   |   min_fpr |
|:------------|-----------:|----------:|--------:|--------:|:------------|----------:|:------------|----------:|
| race        |          7 |     0.128 |   0.056 |   0.253 | indian      |     0.152 | east_asian  |     0.025 |
| gender      |          2 |     0.011 |   0.001 |   0.036 | m           |     0.053 | f           |     0.043 |
| age_band    |          4 |     0.016 |   0.009 |   0.063 | 60+         |     0.058 | 18-29       |     0.042 |
| race_gender |         14 |     0.167 |   0.1   |   0.5   | indian__f   |     0.167 | black__f    |     0     |

### Worst-subgroup AUC and AUC gap

| generator   | attribute   |   n_levels | worst_level   |   worst_auc |   worst_ci_lo |   worst_ci_hi | best_level    |   best_auc |   auc_gap |   gap_ci_lo |   gap_ci_hi |
|:------------|:------------|-----------:|:--------------|------------:|--------------:|--------------:|:--------------|-----------:|----------:|------------:|------------:|
| ltx23       | race        |          6 | latino        |       0.351 |         0.254 |         0.398 | east_asian    |      0.428 |     0.077 |       0.055 |       0.218 |
| ltx23       | gender      |          2 | m             |       0.401 |         0.344 |         0.451 | f             |      0.416 |     0.014 |       0.001 |       0.069 |
| ltx23       | age_band    |          4 | 30-44         |       0.356 |         0.3   |         0.405 | 60+           |      0.415 |     0.059 |       0.024 |       0.141 |
| ltx23       | race_gender |          7 | latino__m     |       0.338 |         0.249 |         0.392 | white__m      |      0.447 |     0.109 |       0.083 |       0.249 |
| wan22       | race        |          6 | latino        |       0.46  |         0.355 |         0.523 | east_asian    |      0.577 |     0.117 |       0.081 |       0.246 |
| wan22       | gender      |          2 | m             |       0.535 |         0.463 |         0.588 | f             |      0.541 |     0.006 |       0.001 |       0.062 |
| wan22       | age_band    |          4 | 30-44         |       0.467 |         0.394 |         0.539 | 45-59         |      0.562 |     0.095 |       0.04  |       0.178 |
| wan22       | race_gender |          7 | latino__m     |       0.453 |         0.336 |         0.524 | east_asian__f |      0.601 |     0.148 |       0.104 |       0.307 |
| hunyuan15   | race        |          6 | latino        |       0.46  |         0.336 |         0.552 | east_asian    |      0.588 |     0.128 |       0.075 |       0.25  |
| hunyuan15   | gender      |          2 | m             |       0.512 |         0.428 |         0.603 | f             |      0.559 |     0.047 |       0.004 |       0.1   |
| hunyuan15   | age_band    |          4 | 45-59         |       0.454 |         0.346 |         0.557 | 60+           |      0.568 |     0.114 |       0.04  |       0.205 |
| hunyuan15   | race_gender |          7 | latino__m     |       0.426 |         0.295 |         0.522 | east_asian__f |      0.611 |     0.185 |       0.114 |       0.343 |
| all         | race        |          7 | indian        |       0.389 |         0.266 |         0.452 | east_asian    |      0.518 |     0.129 |       0.079 |       0.266 |
| all         | gender      |          2 | m             |       0.475 |         0.423 |         0.522 | f             |      0.492 |     0.017 |       0.001 |       0.061 |
| all         | age_band    |          4 | 30-44         |       0.425 |         0.372 |         0.479 | 60+           |      0.492 |     0.066 |       0.025 |       0.134 |
| all         | race_gender |         10 | indian__m     |       0.354 |         0.219 |         0.424 | east_asian__f |      0.541 |     0.187 |       0.135 |       0.365 |

### Detection rate at the calibrated threshold

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1878 |      0.029 |   0.016 |   0.044 |
| wan22       | 1566 |      0.041 |   0.022 |   0.063 |
| hunyuan15   |  989 |      0.065 |   0.027 |   0.112 |
| all         | 4433 |      0.041 |   0.024 |   0.058 |

#### by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 273 |      0.044 |   0.019 |   0.073 |
| ltx23       | east_asian      | 270 |      0.015 |   0     |   0.034 |
| ltx23       | indian          | 277 |      0.018 |   0.003 |   0.037 |
| ltx23       | latino          | 262 |      0.023 |   0.007 |   0.045 |
| ltx23       | mena            | 267 |      0.041 |   0.015 |   0.069 |
| ltx23       | southeast_asian | 271 |      0.022 |   0.007 |   0.045 |
| ltx23       | white           | 258 |      0.039 |   0.018 |   0.062 |
| wan22       | black           | 217 |      0.078 |   0.032 |   0.134 |
| wan22       | east_asian      | 226 |      0.027 |   0.008 |   0.053 |
| wan22       | indian          | 230 |      0.057 |   0.023 |   0.098 |
| wan22       | latino          | 219 |      0.05  |   0.02  |   0.093 |
| wan22       | mena            | 225 |      0.013 |   0     |   0.028 |
| wan22       | southeast_asian | 229 |      0.039 |   0.005 |   0.09  |
| wan22       | white           | 220 |      0.023 |   0.004 |   0.049 |
| hunyuan15   | black           | 141 |      0.057 |   0.015 |   0.105 |
| hunyuan15   | east_asian      | 141 |      0.099 |   0.032 |   0.173 |
| hunyuan15   | indian          | 142 |      0.049 |   0     |   0.117 |
| hunyuan15   | latino          | 142 |      0.085 |   0.03  |   0.148 |
| hunyuan15   | mena            | 139 |      0.072 |   0.029 |   0.118 |
| hunyuan15   | southeast_asian | 143 |      0.028 |   0     |   0.077 |
| hunyuan15   | white           | 141 |      0.064 |   0.019 |   0.11  |
| all         | black           | 631 |      0.059 |   0.03  |   0.093 |
| all         | east_asian      | 637 |      0.038 |   0.017 |   0.06  |
| all         | indian          | 649 |      0.039 |   0.018 |   0.061 |
| all         | latino          | 623 |      0.047 |   0.025 |   0.068 |
| all         | mena            | 631 |      0.038 |   0.02  |   0.055 |
| all         | southeast_asian | 643 |      0.03  |   0.009 |   0.055 |
| all         | white           | 619 |      0.039 |   0.021 |   0.055 |

#### by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.029 |   0.015 |   0.049 |
| ltx23       | m       |  947 |      0.029 |   0.015 |   0.044 |
| wan22       | f       |  785 |      0.036 |   0.019 |   0.057 |
| wan22       | m       |  781 |      0.046 |   0.02  |   0.075 |
| hunyuan15   | f       |  495 |      0.051 |   0.017 |   0.096 |
| hunyuan15   | m       |  494 |      0.079 |   0.032 |   0.132 |
| all         | f       | 2211 |      0.036 |   0.021 |   0.052 |
| all         | m       | 2222 |      0.046 |   0.026 |   0.067 |

#### by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  469 |      0.011 |   0.002 |   0.023 |
| ltx23       | 30-44   |  471 |      0.028 |   0.012 |   0.047 |
| ltx23       | 45-59   |  478 |      0.029 |   0.012 |   0.051 |
| ltx23       | 60+     |  460 |      0.048 |   0.024 |   0.074 |
| wan22       | 18-29   |  388 |      0.021 |   0.007 |   0.039 |
| wan22       | 30-44   |  377 |      0.037 |   0.013 |   0.068 |
| wan22       | 45-59   |  398 |      0.038 |   0.013 |   0.069 |
| wan22       | 60+     |  403 |      0.067 |   0.034 |   0.103 |
| hunyuan15   | 18-29   |  242 |      0.033 |   0     |   0.079 |
| hunyuan15   | 30-44   |  248 |      0.073 |   0.027 |   0.126 |
| hunyuan15   | 45-59   |  250 |      0.064 |   0.025 |   0.106 |
| hunyuan15   | 60+     |  249 |      0.088 |   0.031 |   0.155 |
| all         | 18-29   | 1099 |      0.019 |   0.009 |   0.031 |
| all         | 30-44   | 1096 |      0.041 |   0.022 |   0.062 |
| all         | 45-59   | 1126 |      0.04  |   0.02  |   0.059 |
| all         | 60+     | 1112 |      0.064 |   0.036 |   0.091 |

### Detection-rate gap at the calibrated threshold

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level            | min_level            |
|:------------|:-----------------|------:|--------:|--------:|:---------------------|:---------------------|
| ltx23       | race             | 0.029 |   0.022 |   0.063 | black                | east_asian           |
| ltx23       | gender           | 0     |   0     |   0.017 | f                    | m                    |
| ltx23       | age_band         | 0.037 |   0.018 |   0.061 | 60+                  | 18-29                |
| ltx23       | cell             | 0.1   |   0.088 |   0.235 | white__m__60+        | black__m__18-29      |
| ltx23       | setting          | 0.078 |   0.046 |   0.333 | livingroom           | cafe                 |
| ltx23       | lighting         | 0.072 |   0.038 |   0.138 | warmlamp             | softwindow           |
| ltx23       | behavior         | 0.091 |   0.062 |   0.201 | laugh                | pause                |
| ltx23       | camera           | 0.02  |   0.001 |   0.048 | static               | slowsway             |
| ltx23       | duration_nominal | 0.01  |   0.001 |   0.042 | 5.0                  | 6.0                  |
| wan22       | race             | 0.065 |   0.035 |   0.123 | black                | mena                 |
| wan22       | gender           | 0.01  |   0     |   0.033 | m                    | f                    |
| wan22       | age_band         | 0.046 |   0.02  |   0.079 | 60+                  | 18-29                |
| wan22       | cell             | 0.167 |   0.129 |   0.323 | black__m__60+        | black__f__18-29      |
| wan22       | setting          | 0.092 |   0.073 |   0.286 | classroom            | cafe                 |
| wan22       | lighting         | 0.056 |   0.032 |   0.169 | backlit              | warmlamp             |
| wan22       | behavior         | 0.122 |   0.054 |   0.223 | laugh                | speak                |
| wan22       | camera           | 0.023 |   0.002 |   0.07  | static               | slowsway             |
| wan22       | duration_nominal | 0.002 |   0.001 |   0.047 | 6.0                  | 5.0                  |
| hunyuan15   | race             | 0.071 |   0.039 |   0.145 | east_asian           | southeast_asian      |
| hunyuan15   | gender           | 0.028 |   0.003 |   0.058 | m                    | f                    |
| hunyuan15   | age_band         | 0.055 |   0.021 |   0.115 | 60+                  | 18-29                |
| hunyuan15   | cell             | 0.222 |   0.167 |   0.471 | east_asian__m__30-44 | black__f__18-29      |
| hunyuan15   | setting          | 0.321 |   0.079 |   0.321 | lobby                | cafe                 |
| hunyuan15   | lighting         | 0.1   |   0.05  |   0.321 | lowlight             | softwindow           |
| hunyuan15   | behavior         | 0.214 |   0.077 |   0.321 | laugh                | speak                |
| hunyuan15   | camera           | 0.054 |   0.004 |   0.139 | static               | slowsway             |
| hunyuan15   | duration_nominal | 0.017 |   0.001 |   0.112 | 6.0                  | 5.0                  |
| all         | race             | 0.029 |   0.012 |   0.066 | black                | southeast_asian      |
| all         | gender           | 0.01  |   0     |   0.023 | m                    | f                    |
| all         | age_band         | 0.045 |   0.021 |   0.067 | 60+                  | 18-29                |
| all         | cell             | 0.111 |   0.084 |   0.195 | black__m__60+        | east_asian__f__18-29 |
| all         | setting          | 0.09  |   0.057 |   0.202 | lobby                | cafe                 |
| all         | lighting         | 0.05  |   0.034 |   0.128 | backlit              | softwindow           |
| all         | behavior         | 0.132 |   0.068 |   0.195 | laugh                | speak                |
| all         | camera           | 0.029 |   0.003 |   0.063 | static               | slowsway             |
| all         | duration_nominal | 0.001 |   0.001 |   0.04  | 5.0                  | 6.0                  |

### Flip rate at the calibrated threshold

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.472 |   0.306 |   0.639 |        0 |     1 |
| wan22       |         36 |       0.556 |   0.389 |   0.722 |        1 |     1 |
| hunyuan15   |         18 |       0.667 |   0.444 |   0.875 |        1 |     1 |

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

