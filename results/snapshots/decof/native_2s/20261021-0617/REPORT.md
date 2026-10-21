# decof / native_2s: snapshot 20261021-0617

> **Detector training data.** The released DeCoF checkpoint is most likely trained on AIGVDBench's Open-Sora split (per the paper's default training set and the checkpoint name); our generators are therefore likely unseen. Not confirmed by the authors. Our curated GenBuster subset includes LTX-Video and HunyuanVideo, which are separate from DeCoF's training data but not from AIGVDBench as a whole.

> **Provisional threshold.** Every detection rate and flip rate below uses the detector's default threshold (0.5; official: argmax over 2 logits (DeCoF test.py) == softmax[:,1] >= 0.5). They will be replaced by the 5%-real-FPR threshold once reals exist (section 6.3).

## Settings

| setting           | value                                                                                  |
|:------------------|:---------------------------------------------------------------------------------------|
| detector          | decof 1+b75d2cbe                                                                       |
| checkpoint_sha256 | 4edb7b310cc729771e74b93f658c7fdc4f2e31fdfa617a88372a540d4f9e7b4a                       |
| view              | native_2s (view_hash f40f08a345fde671)                                                 |
| ffmpeg            | ffmpeg version 7.1.1 Copyright (c) 2000-2025 the FFmpeg developers                     |
| batches           | fake_b1, fake_b2, real_b1                                                              |
| inclusion set     | primary (technical QC pass AND face QC pass)                                           |
| bootstrap         | 1000 resamples of whole counterfactual groups, seed 20261020, 95% percentile intervals |
| git commit        | ac1140ab3053-dirty                                                                     |
| created           | 2026-10-21T06:17:18Z                                                                   |

Detector preprocessing on top of the view:

| field               | value                                                                           |
|:--------------------|:--------------------------------------------------------------------------------|
| source              | AIGVDBench section 7 + DeCoF src/utils/data.py (test phase)                     |
| frames_window       | 128                                                                             |
| frames_sampled      | 32                                                                              |
| frames_used         | 8                                                                               |
| sampling            | np.linspace(0, n-1, 32).astype(int)[:8], n = min(128, frames)                   |
| crop                | centre square, side = shorter side                                              |
| resize_1            | [256, 256, 'PIL.BILINEAR']                                                      |
| intermediate_format | lossless (PNG-equivalent, kept in memory)                                       |
| resize_2            | [224, 224, 'torchvision Resize default (bilinear, antialias)']                  |
| centre_crop         | 224                                                                             |
| normalize           | {'mean': [0.485, 0.456, 0.406], 'std': [0.229, 0.224, 0.225]}                   |
| backbone            | OpenAI CLIP ViT-L/14 (frozen), fp32                                             |
| head                | DeCoF vit.ViT(num_patches=8, dim=768, depth=2, heads=4, mlp_dim=768, pool=mean) |
| score               | softmax(logits)[:, 1]                                                           |
| precision           | fp32, TF32 off                                                                  |
| code                | LongMa-2025/DeCoF@5f73e8dc4f8cd9faeed07d767c9517e3f2c66044                      |
| clip_sha256         | b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836                |

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

- LTX 2.3: mean score 0.438 [0.366, 0.513], median 0.380, n = 1878.
- Wan 2.2: mean score 0.082 [0.057, 0.108], median 0.012, n = 1566.
- HunyuanVideo 1.5: mean score 0.192 [0.145, 0.242], median 0.064, n = 989.
- Provisional detection rate (score >= 0.5), LTX 2.3: 41.9% [33.2, 50.9].
- Provisional detection rate (score >= 0.5), Wan 2.2: 5.2% [2.5, 8.1].
- Provisional detection rate (score >= 0.5), HunyuanVideo 1.5: 14.1% [8.7, 20.2].
- Provisional detection rate (score >= 0.5), all: 22.7% [17.8, 27.2].
- Largest race score gap: LTX 2.3 0.180 [0.129, 0.233] (white 0.532 vs east_asian 0.352).
- Largest gender score gap: Wan 2.2 0.056 [0.029, 0.083] (f 0.110 vs m 0.054).
- Largest age band score gap: LTX 2.3 0.264 [0.208, 0.318] (30-44 0.552 vs 60+ 0.289).
- Largest cell score gap: HunyuanVideo 1.5 0.639 [0.552, 0.762] (white__f__18-29 0.651 vs black__f__60+ 0.012).
- Largest scene-factor gap (all generators): setting 0.276 [0.209, 0.430] (library vs cafe).
- Largest partial eta squared: generator 0.343, age_band 0.095, setting 0.069; residual holds 51.9% of total SS.
- CF spread, LTX 2.3: 0.265 [0.243, 0.284] over 36 groups (max 0.361).
- CF spread, Wan 2.2: 0.118 [0.091, 0.145] over 36 groups (max 0.341).
- CF spread, HunyuanVideo 1.5: 0.224 [0.189, 0.260] over 18 groups (max 0.340).
- Provisional flip rate, LTX 2.3: 97.2% of 36 groups [91.7, 100.0].
- Provisional flip rate, Wan 2.2: 44.4% of 36 groups [27.8, 61.1].
- Provisional flip rate, HunyuanVideo 1.5: 94.4% of 18 groups [82.4, 100.0].

## 6.1 Fakes only, no threshold

### Mean score by generator

| generator   |    n |   n_groups |   estimate |   ci_lo |   ci_hi |    sd |   median |   q05 |   q95 |
|:------------|-----:|-----------:|-----------:|--------:|--------:|------:|---------:|------:|------:|
| ltx23       | 1878 |         36 |      0.438 |   0.366 |   0.513 | 0.35  |    0.38  | 0.008 | 0.984 |
| wan22       | 1566 |         36 |      0.082 |   0.057 |   0.108 | 0.164 |    0.012 | 0     | 0.505 |
| hunyuan15   |  989 |         18 |      0.192 |   0.145 |   0.242 | 0.257 |    0.064 | 0.002 | 0.807 |
| all         | 4433 |         36 |      0.257 |   0.218 |   0.296 | 0.319 |    0.088 | 0.001 | 0.946 |

### Mean score by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:----------------|----:|-----------:|--------:|--------:|---------:|
| ltx23       | black           | 273 |      0.414 |   0.335 |   0.501 |    0.341 |
| ltx23       | east_asian      | 270 |      0.352 |   0.27  |   0.435 |    0.236 |
| ltx23       | indian          | 277 |      0.499 |   0.42  |   0.582 |    0.497 |
| ltx23       | latino          | 262 |      0.455 |   0.378 |   0.536 |    0.431 |
| ltx23       | mena            | 267 |      0.428 |   0.35  |   0.508 |    0.347 |
| ltx23       | southeast_asian | 271 |      0.388 |   0.308 |   0.468 |    0.275 |
| ltx23       | white           | 258 |      0.532 |   0.457 |   0.616 |    0.571 |
| wan22       | black           | 217 |      0.059 |   0.035 |   0.085 |    0.014 |
| wan22       | east_asian      | 226 |      0.025 |   0.015 |   0.036 |    0.006 |
| wan22       | indian          | 230 |      0.047 |   0.026 |   0.069 |    0.006 |
| wan22       | latino          | 219 |      0.103 |   0.067 |   0.144 |    0.021 |
| wan22       | mena            | 225 |      0.113 |   0.073 |   0.156 |    0.015 |
| wan22       | southeast_asian | 229 |      0.034 |   0.02  |   0.049 |    0.007 |
| wan22       | white           | 220 |      0.198 |   0.146 |   0.25  |    0.062 |
| hunyuan15   | black           | 141 |      0.129 |   0.076 |   0.193 |    0.043 |
| hunyuan15   | east_asian      | 141 |      0.13  |   0.087 |   0.181 |    0.036 |
| hunyuan15   | indian          | 142 |      0.247 |   0.188 |   0.308 |    0.101 |
| hunyuan15   | latino          | 142 |      0.187 |   0.13  |   0.246 |    0.054 |
| hunyuan15   | mena            | 139 |      0.188 |   0.134 |   0.248 |    0.073 |
| hunyuan15   | southeast_asian | 143 |      0.167 |   0.117 |   0.225 |    0.051 |
| hunyuan15   | white           | 141 |      0.293 |   0.231 |   0.358 |    0.173 |
| all         | black           | 631 |      0.228 |   0.187 |   0.27  |    0.08  |
| all         | east_asian      | 637 |      0.187 |   0.146 |   0.229 |    0.041 |
| all         | indian          | 649 |      0.284 |   0.245 |   0.322 |    0.095 |
| all         | latino          | 623 |      0.27  |   0.225 |   0.318 |    0.096 |
| all         | mena            | 631 |      0.263 |   0.219 |   0.305 |    0.107 |
| all         | southeast_asian | 643 |      0.213 |   0.174 |   0.25  |    0.054 |
| all         | white           | 619 |      0.359 |   0.311 |   0.412 |    0.234 |

### Mean score by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | f       |  931 |      0.458 |   0.386 |   0.536 |    0.418 |
| ltx23       | m       |  947 |      0.418 |   0.341 |   0.498 |    0.344 |
| wan22       | f       |  785 |      0.11  |   0.074 |   0.146 |    0.016 |
| wan22       | m       |  781 |      0.054 |   0.034 |   0.08  |    0.009 |
| hunyuan15   | f       |  495 |      0.217 |   0.168 |   0.269 |    0.088 |
| hunyuan15   | m       |  494 |      0.166 |   0.108 |   0.231 |    0.05  |
| all         | f       | 2211 |      0.281 |   0.239 |   0.324 |    0.108 |
| all         | m       | 2222 |      0.234 |   0.195 |   0.276 |    0.07  |

### Mean score by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | 18-29   |  469 |      0.503 |   0.426 |   0.583 |    0.497 |
| ltx23       | 30-44   |  471 |      0.552 |   0.475 |   0.631 |    0.608 |
| ltx23       | 45-59   |  478 |      0.404 |   0.328 |   0.483 |    0.347 |
| ltx23       | 60+     |  460 |      0.289 |   0.215 |   0.373 |    0.159 |
| wan22       | 18-29   |  388 |      0.11  |   0.073 |   0.15  |    0.017 |
| wan22       | 30-44   |  377 |      0.116 |   0.078 |   0.154 |    0.021 |
| wan22       | 45-59   |  398 |      0.08  |   0.058 |   0.102 |    0.018 |
| wan22       | 60+     |  403 |      0.026 |   0.01  |   0.047 |    0.004 |
| hunyuan15   | 18-29   |  242 |      0.303 |   0.223 |   0.392 |    0.163 |
| hunyuan15   | 30-44   |  248 |      0.271 |   0.203 |   0.342 |    0.149 |
| hunyuan15   | 45-59   |  250 |      0.134 |   0.098 |   0.171 |    0.049 |
| hunyuan15   | 60+     |  249 |      0.061 |   0.037 |   0.09  |    0.021 |
| all         | 18-29   | 1099 |      0.32  |   0.274 |   0.368 |    0.151 |
| all         | 30-44   | 1096 |      0.339 |   0.292 |   0.383 |    0.177 |
| all         | 45-59   | 1126 |      0.229 |   0.191 |   0.271 |    0.083 |
| all         | 60+     | 1112 |      0.143 |   0.109 |   0.18  |    0.025 |

### Mean score by scene factor (all generators pooled)

| factor           | level      |    n |   estimate |   ci_lo |   ci_hi |
|:-----------------|:-----------|-----:|-----------:|--------:|--------:|
| setting          | cafe       |  376 |      0.123 |   0.059 |   0.188 |
| setting          | classroom  |  373 |      0.314 |   0.197 |   0.478 |
| setting          | corridor   |  493 |      0.329 |   0.248 |   0.419 |
| setting          | kitchen    |  441 |      0.204 |   0.042 |   0.425 |
| setting          | library    |  534 |      0.399 |   0.334 |   0.533 |
| setting          | livingroom |  530 |      0.145 |   0.064 |   0.241 |
| setting          | lobby      |  345 |      0.188 |   0.159 |   0.226 |
| setting          | office     |  357 |      0.261 |   0.181 |   0.328 |
| setting          | plainwall  |  553 |      0.277 |   0.242 |   0.362 |
| setting          | studio     |  431 |      0.285 |   0.183 |   0.421 |
| lighting         | backlit    |  790 |      0.267 |   0.145 |   0.389 |
| lighting         | harsh      |  632 |      0.181 |   0.077 |   0.289 |
| lighting         | lowlight   |  784 |      0.363 |   0.264 |   0.461 |
| lighting         | overcast   |  692 |      0.278 |   0.228 |   0.366 |
| lighting         | softwindow |  821 |      0.228 |   0.188 |   0.27  |
| lighting         | warmlamp   |  714 |      0.211 |   0.132 |   0.311 |
| behavior         | laugh      |  500 |      0.399 |   0.339 |   0.498 |
| behavior         | listen     |  680 |      0.313 |   0.171 |   0.427 |
| behavior         | pause      |  520 |      0.221 |   0.059 |   0.288 |
| behavior         | read       |  576 |      0.171 |   0.042 |   0.362 |
| behavior         | smile      |  538 |      0.225 |   0.171 |   0.284 |
| behavior         | speak      |  530 |      0.25  |   0.185 |   0.311 |
| behavior         | think      |  509 |      0.153 |   0.039 |   0.226 |
| behavior         | turn       |  580 |      0.316 |   0.218 |   0.425 |
| camera           | slowsway   | 2225 |      0.27  |   0.205 |   0.335 |
| camera           | static     | 2208 |      0.245 |   0.207 |   0.29  |
| duration_nominal | 5.0        | 2227 |      0.247 |   0.18  |   0.317 |
| duration_nominal | 6.0        | 2206 |      0.267 |   0.23  |   0.308 |

Per-generator scene-factor and 56-cell rows: `tables/score_by_breakdown.csv`.

### Subgroup gap (max - min of level means)

A gap is max - min, so it is never negative and its interval cannot include 0; it is a size, not a test of a difference. Over many levels with few clips each (56 cells; HunyuanVideo has 9 groups per cell) the gap also grows with noise, so compare it with the per-level intervals in `tables/score_by_breakdown.csv`. Levels seen in a single counterfactual group have no interval.

| generator   | attribute        |   n_levels |   gap |   ci_lo |   ci_hi | max_level       | min_level          |
|:------------|:-----------------|-----------:|------:|--------:|--------:|:----------------|:-------------------|
| ltx23       | race             |          7 | 0.18  |   0.129 |   0.233 | white           | east_asian         |
| ltx23       | gender           |          2 | 0.04  |   0.004 |   0.079 | f               | m                  |
| ltx23       | age_band         |          4 | 0.264 |   0.208 |   0.318 | 30-44           | 60+                |
| ltx23       | cell             |         56 | 0.607 |   0.54  |   0.706 | white__f__30-44 | east_asian__f__60+ |
| ltx23       | setting          |         10 | 0.452 |   0.356 |   0.764 | library         | cafe               |
| ltx23       | lighting         |          6 | 0.412 |   0.219 |   0.651 | lowlight        | harsh              |
| ltx23       | behavior         |          8 | 0.424 |   0.297 |   0.697 | laugh           | think              |
| ltx23       | camera           |          2 | 0.068 |   0.003 |   0.218 | slowsway        | static             |
| ltx23       | duration_nominal |          2 | 0.009 |   0.003 |   0.178 | 6.0             | 5.0                |
| wan22       | race             |          7 | 0.173 |   0.129 |   0.218 | white           | east_asian         |
| wan22       | gender           |          2 | 0.056 |   0.029 |   0.083 | f               | m                  |
| wan22       | age_band         |          4 | 0.09  |   0.063 |   0.124 | 30-44           | 60+                |
| wan22       | cell             |         56 | 0.358 |   0.282 |   0.465 | white__f__18-29 | east_asian__f__60+ |
| wan22       | setting          |         10 | 0.167 |   0.114 |   0.269 | library         | cafe               |
| wan22       | lighting         |          6 | 0.063 |   0.043 |   0.198 | lowlight        | warmlamp           |
| wan22       | behavior         |          8 | 0.176 |   0.1   |   0.27  | laugh           | read               |
| wan22       | camera           |          2 | 0.016 |   0.001 |   0.07  | slowsway        | static             |
| wan22       | duration_nominal |          2 | 0.043 |   0.004 |   0.092 | 5.0             | 6.0                |
| hunyuan15   | race             |          7 | 0.165 |   0.119 |   0.232 | white           | black              |
| hunyuan15   | gender           |          2 | 0.052 |   0.005 |   0.107 | f               | m                  |
| hunyuan15   | age_band         |          4 | 0.241 |   0.176 |   0.315 | 18-29           | 60+                |
| hunyuan15   | cell             |         56 | 0.639 |   0.552 |   0.762 | white__f__18-29 | black__f__60+      |
| hunyuan15   | setting          |         10 | 0.3   |   0.188 |   0.359 | library         | kitchen            |
| hunyuan15   | lighting         |          6 | 0.127 |   0.097 |   0.312 | lowlight        | softwindow         |
| hunyuan15   | behavior         |          8 | 0.309 |   0.142 |   0.351 | laugh           | pause              |
| hunyuan15   | camera           |          2 | 0.053 |   0.002 |   0.146 | static          | slowsway           |
| hunyuan15   | duration_nominal |          2 | 0.045 |   0.002 |   0.144 | 6.0             | 5.0                |
| all         | race             |          7 | 0.172 |   0.137 |   0.207 | white           | east_asian         |
| all         | gender           |          2 | 0.047 |   0.023 |   0.07  | f               | m                  |
| all         | age_band         |          4 | 0.196 |   0.165 |   0.225 | 30-44           | 60+                |
| all         | cell             |         56 | 0.496 |   0.448 |   0.572 | white__f__30-44 | east_asian__f__60+ |
| all         | setting          |         10 | 0.276 |   0.209 |   0.43  | library         | cafe               |
| all         | lighting         |          6 | 0.181 |   0.096 |   0.332 | lowlight        | harsh              |
| all         | behavior         |          8 | 0.246 |   0.175 |   0.404 | laugh           | think              |
| all         | camera           |          2 | 0.025 |   0.002 |   0.101 | slowsway        | static             |
| all         | duration_nominal |          2 | 0.02  |   0.002 |   0.1   | 6.0             | 5.0                |

### CF spread (mean over groups of the std of score across the group's cells)

| generator   |   n_groups |   cf_spread |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.265 |   0.243 |   0.284 |    0.282 | 0.361 |
| wan22       |         36 |       0.118 |   0.091 |   0.145 |    0.093 | 0.341 |
| hunyuan15   |         18 |       0.224 |   0.189 |   0.26  |    0.229 | 0.34  |

### Factor attribution

OLS with every factor as a fixed effect, type-II ANOVA. `ss_share` is the factor's type-II sum of squares over the total sum of squares (type-II shares need not add to 1). Scene factors are constant within a counterfactual group, so their effects are estimated from between-group differences only. The OLS F tests treat clips as independent although clips are clustered in counterfactual groups, so their p values are optimistic; use the group-bootstrap intervals above for inference.

| factor           |   df |   sum_sq | F      | p         | partial_eta2   |   ss_share |
|:-----------------|-----:|---------:|:-------|:----------|:---------------|-----------:|
| race             |    6 |  12.21   | 38.22  | 1.759e-45 | 0.04956        |  0.02708   |
| gender           |    1 |   2.449  | 46     | 1.336e-11 | 0.01035        |  0.005434  |
| age_band         |    3 |  24.66   | 154.4  | 3.88e-95  | 0.0953         |  0.05471   |
| setting          |    9 |  17.38   | 36.27  | 1.575e-62 | 0.06912        |  0.03856   |
| lighting         |    5 |   6.561  | 24.65  | 1.44e-24  | 0.02727        |  0.01456   |
| behavior         |    7 |  15.15   | 40.67  | 8.029e-56 | 0.06081        |  0.03362   |
| camera           |    1 |   0.0333 | 0.6256 | 0.429     | 0.0001423      |  7.389e-05 |
| duration_nominal |    1 |   1.036  | 19.46  | 1.052e-05 | 0.004406       |  0.002298  |
| generator        |    2 | 122.1    | 1147   | 0         | 0.3429         |  0.271     |
| Residual         | 4397 | 234.1    |        |           |                |  0.5193    |

Lighting x race interaction (added to the same OLS):

| term            |   df |   sum_sq |     F |       p |   partial_eta2 |
|:----------------|-----:|---------:|------:|--------:|---------------:|
| lighting x race |   30 |    2.311 | 1.452 | 0.05318 |       0.009874 |

Mixed model `score ~ factors + (1 | counterfactual_group)` (REML) variance components (fixed effects: `tables/factor_mixed_fixed.csv`):

| component                               |   variance | converged   |
|:----------------------------------------|-----------:|:------------|
| counterfactual_group (random intercept) |    0       | True        |
| residual                                |    0.05179 | True        |
| ICC (group share of random variance)    |    0       | True        |

A group variance at or near 0 is a boundary estimate: setting, lighting, behavior, camera and duration are fixed per group and absorb most between-group variation, leaving little for the random intercept. It does not mean scenes do not matter.

## 6.2 Provisional (threshold 0.5, provisional)

### Detection rate by generator (provisional)

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1878 |      0.419 |   0.332 |   0.509 |
| wan22       | 1566 |      0.052 |   0.025 |   0.081 |
| hunyuan15   |  989 |      0.141 |   0.087 |   0.202 |
| all         | 4433 |      0.227 |   0.178 |   0.272 |

### Detection rate by race (provisional)

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 273 |      0.366 |   0.264 |   0.476 |
| ltx23       | east_asian      | 270 |      0.304 |   0.207 |   0.405 |
| ltx23       | indian          | 277 |      0.498 |   0.397 |   0.601 |
| ltx23       | latino          | 262 |      0.427 |   0.339 |   0.522 |
| ltx23       | mena            | 267 |      0.423 |   0.327 |   0.532 |
| ltx23       | southeast_asian | 271 |      0.373 |   0.273 |   0.478 |
| ltx23       | white           | 258 |      0.543 |   0.444 |   0.644 |
| wan22       | black           | 217 |      0.014 |   0     |   0.035 |
| wan22       | east_asian      | 226 |      0     |   0     |   0     |
| wan22       | indian          | 230 |      0.022 |   0     |   0.046 |
| wan22       | latino          | 219 |      0.073 |   0.026 |   0.128 |
| wan22       | mena            | 225 |      0.084 |   0.029 |   0.154 |
| wan22       | southeast_asian | 229 |      0.009 |   0     |   0.026 |
| wan22       | white           | 220 |      0.164 |   0.095 |   0.238 |
| hunyuan15   | black           | 141 |      0.078 |   0.019 |   0.154 |
| hunyuan15   | east_asian      | 141 |      0.085 |   0.031 |   0.152 |
| hunyuan15   | indian          | 142 |      0.211 |   0.119 |   0.303 |
| hunyuan15   | latino          | 142 |      0.155 |   0.078 |   0.234 |
| hunyuan15   | mena            | 139 |      0.115 |   0.046 |   0.189 |
| hunyuan15   | southeast_asian | 143 |      0.098 |   0.04  |   0.167 |
| hunyuan15   | white           | 141 |      0.241 |   0.169 |   0.315 |
| all         | black           | 631 |      0.181 |   0.13  |   0.233 |
| all         | east_asian      | 637 |      0.148 |   0.099 |   0.197 |
| all         | indian          | 649 |      0.267 |   0.218 |   0.314 |
| all         | latino          | 623 |      0.241 |   0.19  |   0.297 |
| all         | mena            | 631 |      0.235 |   0.176 |   0.293 |
| all         | southeast_asian | 643 |      0.182 |   0.136 |   0.231 |
| all         | white           | 619 |      0.339 |   0.274 |   0.408 |

### Detection rate by gender (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.446 |   0.362 |   0.532 |
| ltx23       | m       |  947 |      0.392 |   0.299 |   0.494 |
| wan22       | f       |  785 |      0.076 |   0.035 |   0.121 |
| wan22       | m       |  781 |      0.027 |   0.008 |   0.052 |
| hunyuan15   | f       |  495 |      0.166 |   0.112 |   0.227 |
| hunyuan15   | m       |  494 |      0.115 |   0.047 |   0.196 |
| all         | f       | 2211 |      0.252 |   0.203 |   0.304 |
| all         | m       | 2222 |      0.202 |   0.156 |   0.253 |

### Detection rate by age band (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  469 |      0.499 |   0.405 |   0.594 |
| ltx23       | 30-44   |  471 |      0.558 |   0.462 |   0.657 |
| ltx23       | 45-59   |  478 |      0.372 |   0.276 |   0.479 |
| ltx23       | 60+     |  460 |      0.241 |   0.145 |   0.356 |
| wan22       | 18-29   |  388 |      0.085 |   0.037 |   0.137 |
| wan22       | 30-44   |  377 |      0.08  |   0.037 |   0.126 |
| wan22       | 45-59   |  398 |      0.033 |   0.013 |   0.053 |
| wan22       | 60+     |  403 |      0.012 |   0     |   0.031 |
| hunyuan15   | 18-29   |  242 |      0.273 |   0.162 |   0.401 |
| hunyuan15   | 30-44   |  248 |      0.21  |   0.131 |   0.302 |
| hunyuan15   | 45-59   |  250 |      0.068 |   0.031 |   0.105 |
| hunyuan15   | 60+     |  249 |      0.016 |   0     |   0.038 |
| all         | 18-29   | 1099 |      0.303 |   0.244 |   0.362 |
| all         | 30-44   | 1096 |      0.315 |   0.258 |   0.371 |
| all         | 45-59   | 1126 |      0.185 |   0.14  |   0.232 |
| all         | 60+     | 1112 |      0.108 |   0.065 |   0.158 |

### Detection-rate gap (provisional)

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level       | min_level          |
|:------------|:-----------------|------:|--------:|--------:|:----------------|:-------------------|
| ltx23       | race             | 0.239 |   0.167 |   0.319 | white           | east_asian         |
| ltx23       | gender           | 0.054 |   0.006 |   0.11  | f               | m                  |
| ltx23       | age_band         | 0.317 |   0.237 |   0.4   | 30-44           | 60+                |
| ltx23       | cell             | 0.726 |   0.666 |   0.9   | white__f__30-44 | east_asian__f__60+ |
| ltx23       | setting          | 0.514 |   0.417 |   0.891 | library         | cafe               |
| ltx23       | lighting         | 0.485 |   0.26  |   0.757 | lowlight        | harsh              |
| ltx23       | behavior         | 0.539 |   0.37  |   0.834 | laugh           | think              |
| ltx23       | camera           | 0.1   |   0.008 |   0.271 | slowsway        | static             |
| ltx23       | duration_nominal | 0.002 |   0.003 |   0.21  | 6.0             | 5.0                |
| wan22       | race             | 0.164 |   0.095 |   0.238 | white           | east_asian         |
| wan22       | gender           | 0.05  |   0.009 |   0.089 | f               | m                  |
| wan22       | age_band         | 0.073 |   0.04  |   0.116 | 18-29           | 60+                |
| wan22       | cell             | 0.37  |   0.231 |   0.556 | white__f__18-29 | black__f__30-44    |
| wan22       | setting          | 0.16  |   0.098 |   0.315 | library         | cafe               |
| wan22       | lighting         | 0.073 |   0.043 |   0.197 | lowlight        | warmlamp           |
| wan22       | behavior         | 0.16  |   0.08  |   0.289 | laugh           | read               |
| wan22       | camera           | 0.034 |   0.002 |   0.093 | slowsway        | static             |
| wan22       | duration_nominal | 0.038 |   0.002 |   0.092 | 5.0             | 6.0                |
| hunyuan15   | race             | 0.163 |   0.114 |   0.255 | white           | black              |
| hunyuan15   | gender           | 0.05  |   0.003 |   0.12  | f               | m                  |
| hunyuan15   | age_band         | 0.257 |   0.159 |   0.37  | 18-29           | 60+                |
| hunyuan15   | cell             | 0.824 |   0.65  |   1     | white__f__18-29 | black__f__30-44    |
| hunyuan15   | setting          | 0.321 |   0.192 |   0.429 | library         | kitchen            |
| hunyuan15   | lighting         | 0.137 |   0.122 |   0.401 | backlit         | warmlamp           |
| hunyuan15   | behavior         | 0.356 |   0.141 |   0.415 | laugh           | pause              |
| hunyuan15   | camera           | 0.045 |   0.003 |   0.158 | static          | slowsway           |
| hunyuan15   | duration_nominal | 0.051 |   0.003 |   0.168 | 6.0             | 5.0                |
| all         | race             | 0.192 |   0.144 |   0.24  | white           | east_asian         |
| all         | gender           | 0.05  |   0.02  |   0.079 | f               | m                  |
| all         | age_band         | 0.207 |   0.168 |   0.25  | 30-44           | 60+                |
| all         | cell             | 0.586 |   0.488 |   0.725 | white__f__18-29 | east_asian__f__60+ |
| all         | setting          | 0.307 |   0.231 |   0.526 | library         | cafe               |
| all         | lighting         | 0.213 |   0.115 |   0.394 | lowlight        | harsh              |
| all         | behavior         | 0.3   |   0.198 |   0.492 | laugh           | think              |
| all         | camera           | 0.047 |   0.003 |   0.136 | slowsway        | static             |
| all         | duration_nominal | 0.021 |   0.002 |   0.116 | 6.0             | 5.0                |

### Flip rate (provisional): share of groups whose clips get different decisions

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.972 |   0.917 |   1     |        1 |     1 |
| wan22       |         36 |       0.444 |   0.278 |   0.611 |        0 |     1 |
| hunyuan15   |         18 |       0.944 |   0.824 |   1     |        1 |     1 |

### Sensitivity: inclusion set

| set     | generator   |    n |   mean_score |   provisional_detection_rate |
|:--------|:------------|-----:|-------------:|-----------------------------:|
| all     | hunyuan15   | 1008 |        0.194 |                        0.144 |
| all     | ltx23       | 2016 |        0.442 |                        0.424 |
| all     | wan22       | 2016 |        0.091 |                        0.059 |
| primary | hunyuan15   |  989 |        0.192 |                        0.141 |
| primary | ltx23       | 1878 |        0.438 |                        0.419 |
| primary | wan22       | 1566 |        0.082 |                        0.052 |

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

