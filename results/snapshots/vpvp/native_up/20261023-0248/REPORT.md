# vpvp / native_up: snapshot 20261023-0248

> **Detector training data.** V-PVP head trained by the authors on AIGVDBench Real + Open-Sora + CogVideoX1.5 + EasyAnimate with a frozen Kinetics-400 VideoMAE-B/16; none of our generators is in its training set.

> **Provisional threshold.** Every detection rate and flip rate below uses the detector's default threshold (0.5; official: sigmoid(logit) > 0.5 (eval_opensource.py --threshold default)). They will be replaced by the 5%-real-FPR threshold once reals exist (section 6.3).

## Settings

| setting           | value                                                                                  |
|:------------------|:---------------------------------------------------------------------------------------|
| detector          | vpvp 1+c6ec2331                                                                        |
| checkpoint_sha256 | 33581d50452bcf19373a3e5db1204e44b456cb216ac21a3b889ee6970ba6f93b                       |
| view              | native_up (view_hash 4db0c07a46c4b8d9)                                                 |
| ffmpeg            | ffmpeg version 7.1.1 Copyright (c) 2000-2025 the FFmpeg developers                     |
| batches           | fake_b1, fake_b2, fake_b3, real_all                                                    |
| inclusion set     | primary (technical QC pass AND face QC pass)                                           |
| bootstrap         | 1000 resamples of whole counterfactual groups, seed 20261020, 95% percentile intervals |
| git commit        | 2949de581861-dirty                                                                     |
| created           | 2026-10-23T02:48:21Z                                                                   |

Detector preprocessing on top of the view:

| field       | value                                                                                                                                                |
|:------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------|
| source      | manic-cui/Rethinking-the-readout@6ca3b1195c4b842c593638055bbcc9c8eaa6781d src/dataset.py + eval_opensource.py; AIGVDBench section 7 frame extraction |
| extraction  | 32 of the first 128 frames, np.linspace(0, n-1, 32); centre square; 256x256 PIL bilinear                                                             |
| frames_used | np.linspace(0, 31, 16, dtype=int) of the 32                                                                                                          |
| resize      | [224, 224, 'PIL BICUBIC']                                                                                                                            |
| normalize   | {'mean': [0.485, 0.456, 0.406], 'std': [0.229, 0.224, 0.225]}                                                                                        |
| backbone    | MCG-NJU/videomae-base-finetuned-kinetics@488eb9a0565f257b32866000305c8178965eb9f6, frozen, last block, fp16 autocast                                 |
| head        | PVPHead('velocity_gated', D=768), videomae_k400_vpvp.pt (sha 33581d50452b), fp32                                                                     |
| score       | sigmoid(logit) in float64                                                                                                                            |

## Coverage

| batch    | generator   |   clips |   primary |   rendered |   view_excluded |   render_failed |   scored |   score_failed |   included |
|:---------|:------------|--------:|----------:|-----------:|----------------:|----------------:|---------:|---------------:|-----------:|
| fake_b1  | hunyuan15   |     504 |       492 |        504 |               0 |               0 |      504 |              0 |        492 |
| fake_b1  | ltx23       |    2016 |      1878 |       2016 |               0 |               0 |     2016 |              0 |       1878 |
| fake_b1  | wan22       |    2016 |      1566 |       2016 |               0 |               0 |     2016 |              0 |       1566 |
| fake_b2  | hunyuan15   |     504 |       497 |        504 |               0 |               0 |      504 |              0 |        497 |
| fake_b3  | ltx25       |    2016 |      2002 |       2016 |               0 |               0 |     2016 |              0 |       2002 |
| real_all | real        |    2221 |      2221 |        923 |            1275 |              23 |      932 |              0 |        932 |

Reals scored: 1855. Fakes included: 6435 of 8911 scored (0 scoring failures).

## Observations

- LTX 2.3: mean score 0.434 [0.343, 0.530], median 0.266, n = 1878.
- Wan 2.2: mean score 0.796 [0.736, 0.846], median 0.979, n = 1566.
- HunyuanVideo 1.5: mean score 0.160 [0.101, 0.229], median 0.006, n = 989.
- LTX 2.5: mean score 0.262 [0.185, 0.340], median 0.017, n = 2002.
- Provisional detection rate (score >= 0.5), LTX 2.3: 43.1% [33.7, 53.1].
- Provisional detection rate (score >= 0.5), Wan 2.2: 81.4% [75.1, 86.8].
- Provisional detection rate (score >= 0.5), HunyuanVideo 1.5: 14.6% [8.7, 21.9].
- Provisional detection rate (score >= 0.5), LTX 2.5: 25.2% [16.9, 33.4].
- Provisional detection rate (score >= 0.5), all: 42.5% [36.6, 48.8].
- Largest race score gap: LTX 2.3 0.119 [0.094, 0.184] (mena 0.485 vs latino 0.366).
- Largest gender score gap: Wan 2.2 0.153 [0.108, 0.199] (m 0.872 vs f 0.719).
- Largest age band score gap: LTX 2.3 0.075 [0.035, 0.137] (30-44 0.459 vs 45-59 0.385).
- Largest cell score gap: Wan 2.2 0.386 [0.341, 0.557] (latino__m__18-29 0.963 vs white__f__60+ 0.577).
- Largest scene-factor gap (all generators): setting 0.453 [0.341, 0.676] (studio vs office).
- Largest partial eta squared: generator 0.302, behavior 0.037, lighting 0.037; residual holds 58.7% of total SS.
- CF spread, LTX 2.3: 0.307 [0.278, 0.335] over 36 groups (max 0.431).
- CF spread, Wan 2.2: 0.256 [0.215, 0.292] over 36 groups (max 0.415).
- CF spread, HunyuanVideo 1.5: 0.225 [0.162, 0.286] over 18 groups (max 0.410).
- CF spread, LTX 2.5: 0.256 [0.214, 0.300] over 36 groups (max 0.435).
- Provisional flip rate, LTX 2.3: 97.2% of 36 groups [91.7, 100.0].
- Provisional flip rate, Wan 2.2: 80.6% of 36 groups [66.7, 91.7].
- Provisional flip rate, HunyuanVideo 1.5: 77.8% of 18 groups [58.3, 95.0].
- Provisional flip rate, LTX 2.5: 86.1% of 36 groups [75.0, 97.2].

## 6.1 Fakes only, no threshold

### Mean score by generator

| generator   |    n |   n_groups |   estimate |   ci_lo |   ci_hi |    sd |   median |   q05 |   q95 |
|:------------|-----:|-----------:|-----------:|--------:|--------:|------:|---------:|------:|------:|
| ltx23       | 1878 |         36 |      0.434 |   0.343 |   0.53  | 0.43  |    0.266 | 0     | 1     |
| wan22       | 1566 |         36 |      0.796 |   0.736 |   0.846 | 0.322 |    0.979 | 0.041 | 1     |
| hunyuan15   |  989 |         18 |      0.16  |   0.101 |   0.229 | 0.295 |    0.006 | 0     | 0.934 |
| ltx25       | 2002 |         36 |      0.262 |   0.185 |   0.34  | 0.379 |    0.017 | 0     | 0.997 |
| all         | 6435 |         36 |      0.426 |   0.371 |   0.487 | 0.435 |    0.208 | 0     | 1     |

### Mean score by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:----------------|----:|-----------:|--------:|--------:|---------:|
| ltx23       | black           | 273 |      0.466 |   0.371 |   0.568 |    0.367 |
| ltx23       | east_asian      | 270 |      0.404 |   0.307 |   0.51  |    0.126 |
| ltx23       | indian          | 277 |      0.478 |   0.374 |   0.588 |    0.407 |
| ltx23       | latino          | 262 |      0.366 |   0.263 |   0.474 |    0.106 |
| ltx23       | mena            | 267 |      0.485 |   0.385 |   0.592 |    0.428 |
| ltx23       | southeast_asian | 271 |      0.417 |   0.307 |   0.537 |    0.123 |
| ltx23       | white           | 258 |      0.418 |   0.326 |   0.514 |    0.22  |
| wan22       | black           | 217 |      0.822 |   0.758 |   0.883 |    0.987 |
| wan22       | east_asian      | 226 |      0.759 |   0.688 |   0.823 |    0.963 |
| wan22       | indian          | 230 |      0.79  |   0.715 |   0.862 |    0.982 |
| wan22       | latino          | 219 |      0.814 |   0.768 |   0.857 |    0.977 |
| wan22       | mena            | 225 |      0.827 |   0.771 |   0.872 |    0.983 |
| wan22       | southeast_asian | 229 |      0.766 |   0.683 |   0.834 |    0.974 |
| wan22       | white           | 220 |      0.793 |   0.714 |   0.867 |    0.983 |
| hunyuan15   | black           | 141 |      0.201 |   0.117 |   0.307 |    0.015 |
| hunyuan15   | east_asian      | 141 |      0.136 |   0.082 |   0.197 |    0.006 |
| hunyuan15   | indian          | 142 |      0.165 |   0.103 |   0.236 |    0.009 |
| hunyuan15   | latino          | 142 |      0.129 |   0.065 |   0.209 |    0.002 |
| hunyuan15   | mena            | 139 |      0.147 |   0.083 |   0.217 |    0.006 |
| hunyuan15   | southeast_asian | 143 |      0.168 |   0.086 |   0.264 |    0.007 |
| hunyuan15   | white           | 141 |      0.176 |   0.094 |   0.273 |    0.007 |
| ltx25       | black           | 287 |      0.317 |   0.237 |   0.407 |    0.063 |
| ltx25       | east_asian      | 286 |      0.227 |   0.151 |   0.308 |    0.011 |
| ltx25       | indian          | 284 |      0.264 |   0.178 |   0.345 |    0.01  |
| ltx25       | latino          | 286 |      0.253 |   0.169 |   0.345 |    0.014 |
| ltx25       | mena            | 286 |      0.293 |   0.206 |   0.388 |    0.022 |
| ltx25       | southeast_asian | 286 |      0.251 |   0.163 |   0.339 |    0.015 |
| ltx25       | white           | 287 |      0.229 |   0.151 |   0.313 |    0.01  |
| all         | black           | 918 |      0.463 |   0.404 |   0.528 |    0.372 |
| all         | east_asian      | 923 |      0.395 |   0.336 |   0.457 |    0.118 |
| all         | indian          | 933 |      0.442 |   0.383 |   0.505 |    0.272 |
| all         | latino          | 909 |      0.401 |   0.342 |   0.464 |    0.158 |
| all         | mena            | 917 |      0.458 |   0.4   |   0.519 |    0.331 |
| all         | southeast_asian | 929 |      0.414 |   0.35  |   0.483 |    0.153 |
| all         | white           | 906 |      0.412 |   0.352 |   0.475 |    0.175 |

### Mean score by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | f       |  931 |      0.447 |   0.347 |   0.555 |    0.316 |
| ltx23       | m       |  947 |      0.421 |   0.331 |   0.515 |    0.2   |
| wan22       | f       |  785 |      0.719 |   0.646 |   0.787 |    0.942 |
| wan22       | m       |  781 |      0.872 |   0.822 |   0.916 |    0.994 |
| hunyuan15   | f       |  495 |      0.13  |   0.074 |   0.2   |    0.004 |
| hunyuan15   | m       |  494 |      0.191 |   0.117 |   0.272 |    0.011 |
| ltx25       | f       |  999 |      0.237 |   0.163 |   0.32  |    0.01  |
| ltx25       | m       | 1003 |      0.287 |   0.199 |   0.374 |    0.024 |
| all         | f       | 3210 |      0.399 |   0.341 |   0.465 |    0.147 |
| all         | m       | 3225 |      0.453 |   0.396 |   0.518 |    0.285 |

### Mean score by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | 18-29   |  469 |      0.445 |   0.342 |   0.549 |    0.266 |
| ltx23       | 30-44   |  471 |      0.459 |   0.361 |   0.561 |    0.365 |
| ltx23       | 45-59   |  478 |      0.385 |   0.289 |   0.488 |    0.118 |
| ltx23       | 60+     |  460 |      0.448 |   0.351 |   0.553 |    0.318 |
| wan22       | 18-29   |  388 |      0.813 |   0.752 |   0.865 |    0.987 |
| wan22       | 30-44   |  377 |      0.82  |   0.755 |   0.88  |    0.99  |
| wan22       | 45-59   |  398 |      0.755 |   0.683 |   0.819 |    0.959 |
| wan22       | 60+     |  403 |      0.796 |   0.721 |   0.862 |    0.974 |
| hunyuan15   | 18-29   |  242 |      0.193 |   0.123 |   0.268 |    0.011 |
| hunyuan15   | 30-44   |  248 |      0.184 |   0.116 |   0.268 |    0.009 |
| hunyuan15   | 45-59   |  250 |      0.126 |   0.061 |   0.211 |    0.003 |
| hunyuan15   | 60+     |  249 |      0.14  |   0.08  |   0.205 |    0.006 |
| ltx25       | 18-29   |  500 |      0.236 |   0.165 |   0.311 |    0.014 |
| ltx25       | 30-44   |  497 |      0.269 |   0.196 |   0.344 |    0.026 |
| ltx25       | 45-59   |  501 |      0.272 |   0.189 |   0.365 |    0.016 |
| ltx25       | 60+     |  504 |      0.271 |   0.176 |   0.369 |    0.014 |
| all         | 18-29   | 1599 |      0.431 |   0.375 |   0.489 |    0.216 |
| all         | 30-44   | 1593 |      0.443 |   0.382 |   0.508 |    0.254 |
| all         | 45-59   | 1627 |      0.401 |   0.341 |   0.466 |    0.134 |
| all         | 60+     | 1616 |      0.432 |   0.371 |   0.497 |    0.241 |

### Mean score by scene factor (all generators pooled)

| factor           | level      |    n |   estimate |   ci_lo |   ci_hi |
|:-----------------|:-----------|-----:|-----------:|--------:|--------:|
| setting          | cafe       |  593 |      0.341 |   0.105 |   0.567 |
| setting          | classroom  |  541 |      0.284 |   0.211 |   0.404 |
| setting          | corridor   |  716 |      0.394 |   0.192 |   0.706 |
| setting          | kitchen    |  605 |      0.281 |   0.159 |   0.418 |
| setting          | library    |  757 |      0.551 |   0.465 |   0.618 |
| setting          | livingroom |  754 |      0.511 |   0.357 |   0.64  |
| setting          | lobby      |  513 |      0.406 |   0.29  |   0.553 |
| setting          | office     |  580 |      0.228 |   0.101 |   0.574 |
| setting          | plainwall  |  777 |      0.496 |   0.387 |   0.612 |
| setting          | studio     |  599 |      0.681 |   0.626 |   0.827 |
| lighting         | backlit    | 1126 |      0.584 |   0.518 |   0.648 |
| lighting         | harsh      |  967 |      0.216 |   0.143 |   0.305 |
| lighting         | lowlight   | 1116 |      0.539 |   0.472 |   0.591 |
| lighting         | overcast   | 1022 |      0.357 |   0.257 |   0.466 |
| lighting         | softwindow | 1157 |      0.487 |   0.298 |   0.658 |
| lighting         | warmlamp   | 1047 |      0.331 |   0.19  |   0.489 |
| behavior         | laugh      |  723 |      0.49  |   0.29  |   0.706 |
| behavior         | listen     |  960 |      0.569 |   0.483 |   0.626 |
| behavior         | pause      |  744 |      0.425 |   0.306 |   0.574 |
| behavior         | read       |  796 |      0.303 |   0.105 |   0.531 |
| behavior         | smile      |  817 |      0.501 |   0.273 |   0.734 |
| behavior         | speak      |  806 |      0.332 |   0.191 |   0.506 |
| behavior         | think      |  733 |      0.504 |   0.29  |   0.607 |
| behavior         | turn       |  856 |      0.279 |   0.166 |   0.409 |
| camera           | slowsway   | 3224 |      0.384 |   0.293 |   0.483 |
| camera           | static     | 3211 |      0.469 |   0.397 |   0.54  |
| duration_nominal | 5.0        | 3226 |      0.446 |   0.356 |   0.542 |
| duration_nominal | 6.0        | 3209 |      0.407 |   0.33  |   0.479 |

Per-generator scene-factor and 56-cell rows: `tables/score_by_breakdown.csv`.

### Subgroup gap (max - min of level means)

A gap is max - min, so it is never negative and its interval cannot include 0; it is a size, not a test of a difference. Over many levels with few clips each (56 cells; HunyuanVideo has 9 groups per cell) the gap also grows with noise, so compare it with the per-level intervals in `tables/score_by_breakdown.csv`. Levels seen in a single counterfactual group have no interval.

| generator   | attribute        |   n_levels |   gap |   ci_lo |   ci_hi | max_level        | min_level        |
|:------------|:-----------------|-----------:|------:|--------:|--------:|:-----------------|:-----------------|
| ltx23       | race             |          7 | 0.119 |   0.094 |   0.184 | mena             | latino           |
| ltx23       | gender           |          2 | 0.025 |   0.001 |   0.088 | f                | m                |
| ltx23       | age_band         |          4 | 0.075 |   0.035 |   0.137 | 30-44            | 45-59            |
| ltx23       | cell             |         56 | 0.316 |   0.321 |   0.51  | indian__m__60+   | latino__f__45-59 |
| ltx23       | setting          |         10 | 0.614 |   0.558 |   0.84  | studio           | classroom        |
| ltx23       | lighting         |          6 | 0.539 |   0.445 |   0.728 | lowlight         | harsh            |
| ltx23       | behavior         |          8 | 0.441 |   0.407 |   0.803 | smile            | read             |
| ltx23       | camera           |          2 | 0.091 |   0.005 |   0.285 | static           | slowsway         |
| ltx23       | duration_nominal |          2 | 0.121 |   0.005 |   0.316 | 5.0              | 6.0              |
| wan22       | race             |          7 | 0.068 |   0.043 |   0.137 | mena             | east_asian       |
| wan22       | gender           |          2 | 0.153 |   0.108 |   0.199 | m                | f                |
| wan22       | age_band         |          4 | 0.065 |   0.032 |   0.12  | 30-44            | 45-59            |
| wan22       | cell             |         56 | 0.386 |   0.341 |   0.557 | latino__m__18-29 | white__f__60+    |
| wan22       | setting          |         10 | 0.381 |   0.217 |   0.63  | studio           | kitchen          |
| wan22       | lighting         |          6 | 0.185 |   0.156 |   0.4   | softwindow       | overcast         |
| wan22       | behavior         |          8 | 0.275 |   0.201 |   0.548 | think            | turn             |
| wan22       | camera           |          2 | 0.095 |   0.008 |   0.206 | static           | slowsway         |
| wan22       | duration_nominal |          2 | 0.013 |   0.002 |   0.131 | 5.0              | 6.0              |
| hunyuan15   | race             |          7 | 0.073 |   0.049 |   0.165 | black            | latino           |
| hunyuan15   | gender           |          2 | 0.062 |   0.011 |   0.117 | m                | f                |
| hunyuan15   | age_band         |          4 | 0.067 |   0.036 |   0.129 | 18-29            | 45-59            |
| hunyuan15   | cell             |         56 | 0.306 |   0.276 |   0.552 | white__m__18-29  | mena__f__45-59   |
| hunyuan15   | setting          |         10 | 0.295 |   0.201 |   0.475 | studio           | classroom        |
| hunyuan15   | lighting         |          6 | 0.249 |   0.137 |   0.469 | backlit          | harsh            |
| hunyuan15   | behavior         |          8 | 0.324 |   0.219 |   0.473 | think            | speak            |
| hunyuan15   | camera           |          2 | 0.138 |   0.024 |   0.254 | static           | slowsway         |
| hunyuan15   | duration_nominal |          2 | 0.051 |   0.004 |   0.192 | 5.0              | 6.0              |
| ltx25       | race             |          7 | 0.089 |   0.068 |   0.155 | black            | east_asian       |
| ltx25       | gender           |          2 | 0.049 |   0.004 |   0.099 | m                | f                |
| ltx25       | age_band         |          4 | 0.036 |   0.019 |   0.1   | 45-59            | 18-29            |
| ltx25       | cell             |         56 | 0.324 |   0.296 |   0.512 | black__m__30-44  | white__m__18-29  |
| ltx25       | setting          |         10 | 0.411 |   0.36  |   0.654 | studio           | kitchen          |
| ltx25       | lighting         |          6 | 0.385 |   0.309 |   0.596 | lowlight         | warmlamp         |
| ltx25       | behavior         |          8 | 0.352 |   0.283 |   0.612 | listen           | turn             |
| ltx25       | camera           |          2 | 0.053 |   0.004 |   0.223 | static           | slowsway         |
| ltx25       | duration_nominal |          2 | 0.073 |   0.005 |   0.22  | 6.0              | 5.0              |
| all         | race             |          7 | 0.068 |   0.053 |   0.11  | black            | east_asian       |
| all         | gender           |          2 | 0.054 |   0.027 |   0.08  | m                | f                |
| all         | age_band         |          4 | 0.042 |   0.024 |   0.07  | 30-44            | 45-59            |
| all         | cell             |         56 | 0.274 |   0.225 |   0.369 | black__m__30-44  | latino__f__45-59 |
| all         | setting          |         10 | 0.453 |   0.341 |   0.676 | studio           | office           |
| all         | lighting         |          6 | 0.368 |   0.276 |   0.49  | backlit          | harsh            |
| all         | behavior         |          8 | 0.29  |   0.239 |   0.531 | listen           | turn             |
| all         | camera           |          2 | 0.085 |   0.005 |   0.203 | static           | slowsway         |
| all         | duration_nominal |          2 | 0.039 |   0.003 |   0.156 | 5.0              | 6.0              |

### CF spread (mean over groups of the std of score across the group's cells)

| generator   |   n_groups |   cf_spread |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.307 |   0.278 |   0.335 |    0.329 | 0.431 |
| wan22       |         36 |       0.256 |   0.215 |   0.292 |    0.281 | 0.415 |
| hunyuan15   |         18 |       0.225 |   0.162 |   0.286 |    0.27  | 0.41  |
| ltx25       |         36 |       0.256 |   0.214 |   0.3   |    0.254 | 0.435 |

### Factor attribution

OLS with every factor as a fixed effect, type-II ANOVA. `ss_share` is the factor's type-II sum of squares over the total sum of squares (type-II shares need not add to 1). Scene factors are constant within a counterfactual group, so their effects are estimated from between-group differences only. The OLS F tests treat clips as independent although clips are clustered in counterfactual groups, so their p values are optimistic; use the group-bootstrap intervals above for inference.

| factor           |   df |    sum_sq | F     | p         | partial_eta2   |   ss_share |
|:-----------------|-----:|----------:|:------|:----------|:---------------|-----------:|
| race             |    6 |   4.195   | 6.245 | 1.491e-06 | 0.005822       |  0.003439  |
| gender           |    1 |   4.454   | 39.78 | 3.025e-10 | 0.00618        |  0.003652  |
| age_band         |    3 |   1.638   | 4.877 | 0.002176  | 0.002282       |  0.001343  |
| setting          |    9 |  12.83    | 12.73 | 2.709e-20 | 0.01759        |  0.01051   |
| lighting         |    5 |  27.44    | 49.02 | 5.794e-50 | 0.03689        |  0.0225    |
| behavior         |    7 |  27.74    | 35.4  | 7.703e-49 | 0.03729        |  0.02274   |
| camera           |    1 |   8.488   | 75.81 | 3.918e-18 | 0.01171        |  0.006959  |
| duration_nominal |    1 |   0.02642 | 0.236 | 0.6271    | 3.689e-05      |  2.166e-05 |
| generator        |    3 | 309.3     | 920.8 | 0         | 0.3016         |  0.2536    |
| Residual         | 6398 | 716.3     |       |           |                |  0.5873    |

Lighting x race interaction (added to the same OLS):

| term            |   df |   sum_sq |    F |      p |   partial_eta2 |
|:----------------|-----:|---------:|-----:|-------:|---------------:|
| lighting x race |   30 |    3.893 | 1.16 | 0.2509 |       0.005434 |

Mixed model `score ~ factors + (1 | counterfactual_group)` (REML) variance components (fixed effects: `tables/factor_mixed_fixed.csv`):

| component                               |   variance | converged   |
|:----------------------------------------|-----------:|:------------|
| counterfactual_group (random intercept) |     0      | True        |
| residual                                |     0.1073 | True        |
| ICC (group share of random variance)    |     0      | True        |

A group variance at or near 0 is a boundary estimate: setting, lighting, behavior, camera and duration are fixed per group and absorb most between-group variation, leaving little for the random intercept. It does not mean scenes do not matter.

## 6.2 Provisional (threshold 0.5, provisional)

### Detection rate by generator (provisional)

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1878 |      0.431 |   0.337 |   0.531 |
| wan22       | 1566 |      0.814 |   0.751 |   0.868 |
| hunyuan15   |  989 |      0.146 |   0.087 |   0.219 |
| ltx25       | 2002 |      0.252 |   0.169 |   0.334 |
| all         | 6435 |      0.425 |   0.366 |   0.488 |

### Detection rate by race (provisional)

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 273 |      0.473 |   0.363 |   0.588 |
| ltx23       | east_asian      | 270 |      0.4   |   0.297 |   0.506 |
| ltx23       | indian          | 277 |      0.48  |   0.371 |   0.599 |
| ltx23       | latino          | 262 |      0.359 |   0.245 |   0.479 |
| ltx23       | mena            | 267 |      0.491 |   0.381 |   0.602 |
| ltx23       | southeast_asian | 271 |      0.399 |   0.287 |   0.522 |
| ltx23       | white           | 258 |      0.415 |   0.316 |   0.52  |
| wan22       | black           | 217 |      0.848 |   0.774 |   0.912 |
| wan22       | east_asian      | 226 |      0.77  |   0.691 |   0.841 |
| wan22       | indian          | 230 |      0.817 |   0.739 |   0.892 |
| wan22       | latino          | 219 |      0.831 |   0.777 |   0.881 |
| wan22       | mena            | 225 |      0.844 |   0.776 |   0.901 |
| wan22       | southeast_asian | 229 |      0.769 |   0.675 |   0.856 |
| wan22       | white           | 220 |      0.818 |   0.731 |   0.897 |
| hunyuan15   | black           | 141 |      0.191 |   0.092 |   0.317 |
| hunyuan15   | east_asian      | 141 |      0.113 |   0.061 |   0.173 |
| hunyuan15   | indian          | 142 |      0.148 |   0.077 |   0.232 |
| hunyuan15   | latino          | 142 |      0.12  |   0.053 |   0.207 |
| hunyuan15   | mena            | 139 |      0.122 |   0.066 |   0.188 |
| hunyuan15   | southeast_asian | 143 |      0.147 |   0.062 |   0.244 |
| hunyuan15   | white           | 141 |      0.177 |   0.083 |   0.298 |
| ltx25       | black           | 287 |      0.303 |   0.213 |   0.403 |
| ltx25       | east_asian      | 286 |      0.22  |   0.14  |   0.304 |
| ltx25       | indian          | 284 |      0.254 |   0.167 |   0.339 |
| ltx25       | latino          | 286 |      0.241 |   0.155 |   0.34  |
| ltx25       | mena            | 286 |      0.301 |   0.203 |   0.406 |
| ltx25       | southeast_asian | 286 |      0.234 |   0.146 |   0.324 |
| ltx25       | white           | 287 |      0.209 |   0.128 |   0.296 |
| all         | black           | 918 |      0.465 |   0.404 |   0.534 |
| all         | east_asian      | 923 |      0.391 |   0.328 |   0.456 |
| all         | indian          | 933 |      0.444 |   0.38  |   0.511 |
| all         | latino          | 909 |      0.398 |   0.334 |   0.467 |
| all         | mena            | 917 |      0.462 |   0.401 |   0.528 |
| all         | southeast_asian | 929 |      0.4   |   0.334 |   0.47  |
| all         | white           | 906 |      0.411 |   0.347 |   0.479 |

### Detection rate by gender (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.446 |   0.338 |   0.559 |
| ltx23       | m       |  947 |      0.417 |   0.324 |   0.517 |
| wan22       | f       |  785 |      0.732 |   0.649 |   0.807 |
| wan22       | m       |  781 |      0.895 |   0.847 |   0.937 |
| hunyuan15   | f       |  495 |      0.107 |   0.056 |   0.176 |
| hunyuan15   | m       |  494 |      0.184 |   0.109 |   0.269 |
| ltx25       | f       |  999 |      0.221 |   0.145 |   0.307 |
| ltx25       | m       | 1003 |      0.282 |   0.19  |   0.38  |
| all         | f       | 3210 |      0.394 |   0.332 |   0.461 |
| all         | m       | 3225 |      0.455 |   0.395 |   0.523 |

### Detection rate by age band (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  469 |      0.448 |   0.341 |   0.555 |
| ltx23       | 30-44   |  471 |      0.461 |   0.36  |   0.568 |
| ltx23       | 45-59   |  478 |      0.383 |   0.28  |   0.491 |
| ltx23       | 60+     |  460 |      0.435 |   0.335 |   0.548 |
| wan22       | 18-29   |  388 |      0.827 |   0.761 |   0.888 |
| wan22       | 30-44   |  377 |      0.828 |   0.757 |   0.891 |
| wan22       | 45-59   |  398 |      0.779 |   0.701 |   0.852 |
| wan22       | 60+     |  403 |      0.821 |   0.742 |   0.892 |
| hunyuan15   | 18-29   |  242 |      0.169 |   0.099 |   0.244 |
| hunyuan15   | 30-44   |  248 |      0.173 |   0.097 |   0.274 |
| hunyuan15   | 45-59   |  250 |      0.112 |   0.044 |   0.207 |
| hunyuan15   | 60+     |  249 |      0.129 |   0.067 |   0.195 |
| ltx25       | 18-29   |  500 |      0.222 |   0.148 |   0.303 |
| ltx25       | 30-44   |  497 |      0.268 |   0.185 |   0.351 |
| ltx25       | 45-59   |  501 |      0.259 |   0.175 |   0.355 |
| ltx25       | 60+     |  504 |      0.258 |   0.159 |   0.361 |
| all         | 18-29   | 1599 |      0.427 |   0.368 |   0.488 |
| all         | 30-44   | 1593 |      0.443 |   0.377 |   0.513 |
| all         | 45-59   | 1627 |      0.4   |   0.336 |   0.47  |
| all         | 60+     | 1616 |      0.429 |   0.362 |   0.498 |

### Detection-rate gap (provisional)

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level        | min_level            |
|:------------|:-----------------|------:|--------:|--------:|:-----------------|:---------------------|
| ltx23       | race             | 0.132 |   0.1   |   0.214 | mena             | latino               |
| ltx23       | gender           | 0.029 |   0.002 |   0.1   | f                | m                    |
| ltx23       | age_band         | 0.078 |   0.035 |   0.154 | 30-44            | 45-59                |
| ltx23       | cell             | 0.405 |   0.386 |   0.626 | indian__m__60+   | east_asian__m__60+   |
| ltx23       | setting          | 0.635 |   0.576 |   0.895 | studio           | classroom            |
| ltx23       | lighting         | 0.55  |   0.452 |   0.762 | lowlight         | harsh                |
| ltx23       | behavior         | 0.464 |   0.424 |   0.845 | smile            | read                 |
| ltx23       | camera           | 0.1   |   0.006 |   0.296 | static           | slowsway             |
| ltx23       | duration_nominal | 0.138 |   0.009 |   0.34  | 5.0              | 6.0                  |
| wan22       | race             | 0.079 |   0.056 |   0.177 | black            | southeast_asian      |
| wan22       | gender           | 0.163 |   0.108 |   0.22  | m                | f                    |
| wan22       | age_band         | 0.049 |   0.025 |   0.121 | 30-44            | 45-59                |
| wan22       | cell             | 0.448 |   0.367 |   0.655 | latino__m__18-29 | east_asian__f__18-29 |
| wan22       | setting          | 0.406 |   0.228 |   0.662 | studio           | kitchen              |
| wan22       | lighting         | 0.194 |   0.171 |   0.424 | backlit          | lowlight             |
| wan22       | behavior         | 0.293 |   0.205 |   0.57  | think            | turn                 |
| wan22       | camera           | 0.11  |   0.011 |   0.225 | static           | slowsway             |
| wan22       | duration_nominal | 0.007 |   0.003 |   0.137 | 6.0              | 5.0                  |
| hunyuan15   | race             | 0.078 |   0.048 |   0.211 | black            | east_asian           |
| hunyuan15   | gender           | 0.077 |   0.023 |   0.131 | m                | f                    |
| hunyuan15   | age_band         | 0.061 |   0.035 |   0.136 | 30-44            | 45-59                |
| hunyuan15   | cell             | 0.389 |   0.304 |   0.647 | indian__m__30-44 | mena__f__30-44       |
| hunyuan15   | setting          | 0.326 |   0.196 |   0.482 | studio           | classroom            |
| hunyuan15   | lighting         | 0.256 |   0.14  |   0.482 | backlit          | harsh                |
| hunyuan15   | behavior         | 0.33  |   0.219 |   0.482 | think            | speak                |
| hunyuan15   | camera           | 0.132 |   0.014 |   0.259 | static           | slowsway             |
| hunyuan15   | duration_nominal | 0.052 |   0.002 |   0.203 | 5.0              | 6.0                  |
| ltx25       | race             | 0.094 |   0.076 |   0.174 | black            | white                |
| ltx25       | gender           | 0.061 |   0.006 |   0.119 | m                | f                    |
| ltx25       | age_band         | 0.046 |   0.023 |   0.104 | 30-44            | 18-29                |
| ltx25       | cell             | 0.402 |   0.345 |   0.611 | black__m__30-44  | white__m__18-29      |
| ltx25       | setting          | 0.427 |   0.369 |   0.682 | studio           | kitchen              |
| ltx25       | lighting         | 0.395 |   0.314 |   0.622 | lowlight         | warmlamp             |
| ltx25       | behavior         | 0.374 |   0.291 |   0.625 | listen           | turn                 |
| ltx25       | camera           | 0.049 |   0.005 |   0.225 | static           | slowsway             |
| ltx25       | duration_nominal | 0.079 |   0.006 |   0.235 | 6.0              | 5.0                  |
| all         | race             | 0.074 |   0.06  |   0.126 | black            | east_asian           |
| all         | gender           | 0.061 |   0.03  |   0.091 | m                | f                    |
| all         | age_band         | 0.042 |   0.021 |   0.076 | 30-44            | 45-59                |
| all         | cell             | 0.289 |   0.255 |   0.413 | black__m__30-44  | latino__f__45-59     |
| all         | setting          | 0.477 |   0.351 |   0.72  | studio           | office               |
| all         | lighting         | 0.384 |   0.292 |   0.509 | backlit          | harsh                |
| all         | behavior         | 0.309 |   0.247 |   0.547 | listen           | turn                 |
| all         | camera           | 0.089 |   0.004 |   0.214 | static           | slowsway             |
| all         | duration_nominal | 0.039 |   0.002 |   0.162 | 5.0              | 6.0                  |

### Flip rate (provisional): share of groups whose clips get different decisions

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.972 |   0.917 |   1     |        1 |     1 |
| wan22       |         36 |       0.806 |   0.667 |   0.917 |        1 |     1 |
| hunyuan15   |         18 |       0.778 |   0.583 |   0.95  |        1 |     1 |
| ltx25       |         36 |       0.861 |   0.75  |   0.972 |        1 |     1 |

### Sensitivity: inclusion set

| set     | generator   |    n |   mean_score |   provisional_detection_rate |
|:--------|:------------|-----:|-------------:|-----------------------------:|
| all     | hunyuan15   | 1008 |        0.16  |                        0.145 |
| all     | ltx23       | 2016 |        0.445 |                        0.443 |
| all     | ltx25       | 2016 |        0.261 |                        0.25  |
| all     | wan22       | 2016 |        0.803 |                        0.82  |
| primary | hunyuan15   |  989 |        0.16  |                        0.146 |
| primary | ltx23       | 1878 |        0.434 |                        0.431 |
| primary | ltx25       | 2002 |        0.262 |                        0.252 |
| primary | wan22       | 1566 |        0.796 |                        0.814 |

## 6.3 Real vs generated (calibrated threshold 1.0000)

The threshold is the score at which 5% of primary real renders (24 and 16 fps pooled) are flagged; one per detector and view, never per subgroup. Each generator is compared with reals rendered at its own fps. Intervals: fakes resample counterfactual groups, reals resample identity clusters (source video). Real labels are perceived (FairFace), not self-reported.

### Calibration

| scope            |   n_renders |   n_sources |   n_identities |   threshold |    fpr |
|:-----------------|------------:|------------:|---------------:|------------:|-------:|
| all real renders |        1855 |         932 |            811 |           1 | 0.0501 |
| 16 fps renders   |         932 |         932 |            811 |           1 | 0.0526 |
| 24 fps renders   |         923 |         923 |            802 |           1 | 0.0477 |

### AUC, AP, EER, TPR at 5% FPR

| generator   | real_fps   |   n_fake |   n_real |   auc |   auc_ci_lo |   auc_ci_hi |    ap |   eer |   tpr_at_5fpr |   detection_rate_global_thr |   det_ci_lo |   det_ci_hi |
|:------------|:-----------|---------:|---------:|------:|------------:|------------:|------:|------:|--------------:|----------------------------:|------------:|------------:|
| ltx23       | 24         |     1878 |      923 | 0.412 |       0.349 |       0.478 | 0.598 | 0.562 |         0.011 |                       0.01  |       0.002 |       0.019 |
| wan22       | 16         |     1566 |      932 | 0.634 |       0.588 |       0.679 | 0.671 | 0.402 |         0.02  |                       0.022 |       0.008 |       0.039 |
| hunyuan15   | 24         |      989 |      923 | 0.228 |       0.172 |       0.283 | 0.365 | 0.692 |         0     |                       0     |       0     |       0     |
| ltx25       | 24         |     2002 |      923 | 0.288 |       0.233 |       0.345 | 0.55  | 0.65  |         0     |                       0     |       0     |       0.002 |
| all         | 24+16      |     6435 |     1855 | 0.4   |       0.353 |       0.447 | 0.711 | 0.567 |         0.008 |                       0.008 |       0.003 |       0.014 |

### Real FPR by perceived subgroup

| attribute   | level              |   n_renders |   n_identities |   fpr |   ci_lo |   ci_hi |
|:------------|:-------------------|------------:|---------------:|------:|--------:|--------:|
| race        | black              |         123 |             59 | 0.057 |   0.008 |   0.116 |
| race        | east_asian         |         163 |             75 | 0.025 |   0     |   0.058 |
| race        | indian             |          46 |             23 | 0.022 |   0     |   0.071 |
| race        | latino             |         115 |             55 | 0.052 |   0.008 |   0.109 |
| race        | mena               |         120 |             59 | 0.15  |   0.069 |   0.241 |
| race        | southeast_asian    |          70 |             34 | 0     |   0     |   0     |
| race        | white              |        1204 |            523 | 0.047 |   0.03  |   0.064 |
| gender      | f                  |         587 |            266 | 0.027 |   0.011 |   0.047 |
| gender      | m                  |        1254 |            553 | 0.061 |   0.043 |   0.079 |
| age_band    | 18-29              |         594 |            275 | 0.034 |   0.015 |   0.056 |
| age_band    | 30-44              |         626 |            290 | 0.062 |   0.038 |   0.089 |
| age_band    | 45-59              |         300 |            134 | 0.077 |   0.039 |   0.118 |
| age_band    | 60+                |         241 |            112 | 0.025 |   0     |   0.056 |
| race_gender | black__f           |          20 |             10 | 0     |   0     |   0     |
| race_gender | black__m           |         103 |             50 | 0.068 |   0.01  |   0.142 |
| race_gender | east_asian__f      |          76 |             35 | 0.013 |   0     |   0.044 |
| race_gender | east_asian__m      |          87 |             41 | 0.034 |   0     |   0.093 |
| race_gender | indian__f          |          12 |              6 | 0     |   0     |   0     |
| race_gender | indian__m          |          34 |             17 | 0.029 |   0     |   0.1   |
| race_gender | latino__f          |          20 |             10 | 0     |   0     |   0     |
| race_gender | latino__m          |          95 |             45 | 0.063 |   0.01  |   0.132 |
| race_gender | mena__f            |          34 |             17 | 0.147 |   0     |   0.334 |
| race_gender | mena__m            |          86 |             42 | 0.151 |   0.057 |   0.268 |
| race_gender | southeast_asian__f |          20 |              9 | 0     |   0     |   0     |
| race_gender | southeast_asian__m |          50 |             25 | 0     |   0     |   0     |
| race_gender | white__f           |         405 |            183 | 0.025 |   0.007 |   0.047 |
| race_gender | white__m           |         799 |            350 | 0.058 |   0.034 |   0.082 |

### Real FPR gap (max - min across levels; non-negative by construction)

| attribute   |   n_levels |   fpr_gap |   ci_lo |   ci_hi | max_level   |   max_fpr | min_level       |   min_fpr |
|:------------|-----------:|----------:|--------:|--------:|:------------|----------:|:----------------|----------:|
| race        |          7 |     0.15  |   0.075 |   0.241 | mena        |     0.15  | southeast_asian |     0     |
| gender      |          2 |     0.033 |   0.009 |   0.058 | m           |     0.061 | f               |     0.027 |
| age_band    |          4 |     0.052 |   0.024 |   0.104 | 45-59       |     0.077 | 60+             |     0.025 |
| race_gender |         14 |     0.151 |   0.094 |   0.342 | mena__m     |     0.151 | black__f        |     0     |

### Worst-subgroup AUC and AUC gap

| generator   | attribute   |   n_levels | worst_level   |   worst_auc |   worst_ci_lo |   worst_ci_hi | best_level    |   best_auc |   auc_gap |   gap_ci_lo |   gap_ci_hi |
|:------------|:------------|-----------:|:--------------|------------:|--------------:|--------------:|:--------------|-----------:|----------:|------------:|------------:|
| ltx23       | race        |          6 | black         |       0.323 |         0.224 |         0.381 | white         |      0.422 |     0.099 |       0.074 |       0.251 |
| ltx23       | gender      |          2 | m             |       0.395 |         0.33  |         0.46  | f             |      0.446 |     0.05  |       0.005 |       0.109 |
| ltx23       | age_band    |          4 | 45-59         |       0.394 |         0.31  |         0.457 | 60+           |      0.446 |     0.051 |       0.022 |       0.14  |
| ltx23       | race_gender |          7 | mena__m       |       0.332 |         0.212 |         0.384 | white__f      |      0.474 |     0.142 |       0.104 |       0.274 |
| wan22       | race        |          6 | black         |       0.526 |         0.41  |         0.581 | white         |      0.663 |     0.137 |       0.114 |       0.308 |
| wan22       | gender      |          2 | f             |       0.612 |         0.553 |         0.666 | m             |      0.682 |     0.07  |       0.013 |       0.13  |
| wan22       | age_band    |          4 | 45-59         |       0.607 |         0.519 |         0.668 | 18-29         |      0.666 |     0.059 |       0.022 |       0.158 |
| wan22       | race_gender |          7 | east_asian__f |       0.565 |         0.436 |         0.621 | east_asian__m |      0.741 |     0.176 |       0.116 |       0.358 |
| hunyuan15   | race        |          6 | mena          |       0.136 |         0.074 |         0.183 | east_asian    |      0.245 |     0.109 |       0.078 |       0.247 |
| hunyuan15   | gender      |          2 | f             |       0.232 |         0.166 |         0.278 | m             |      0.236 |     0.004 |       0.001 |       0.067 |
| hunyuan15   | age_band    |          4 | 45-59         |       0.213 |         0.138 |         0.264 | 18-29         |      0.257 |     0.044 |       0.021 |       0.119 |
| hunyuan15   | race_gender |          7 | black__m      |       0.154 |         0.068 |         0.189 | east_asian__m |      0.273 |     0.118 |       0.097 |       0.268 |
| ltx25       | race        |          6 | mena          |       0.211 |         0.136 |         0.258 | latino        |      0.303 |     0.092 |       0.061 |       0.216 |
| ltx25       | gender      |          2 | f             |       0.294 |         0.229 |         0.343 | m             |      0.295 |     0.001 |       0.001 |       0.061 |
| ltx25       | age_band    |          4 | 18-29         |       0.282 |         0.211 |         0.327 | 45-59         |      0.3   |     0.018 |       0.015 |       0.104 |
| ltx25       | race_gender |          7 | mena__m       |       0.221 |         0.132 |         0.273 | east_asian__m |      0.327 |     0.106 |       0.065 |       0.24  |
| all         | race        |          7 | mena          |       0.31  |         0.223 |         0.349 | indian        |      0.467 |     0.157 |       0.102 |       0.322 |
| all         | gender      |          2 | f             |       0.407 |         0.353 |         0.448 | m             |      0.41  |     0.003 |       0     |       0.056 |
| all         | age_band    |          4 | 45-59         |       0.39  |         0.32  |         0.434 | 60+           |      0.424 |     0.034 |       0.016 |       0.113 |
| all         | race_gender |         10 | mena__f       |       0.295 |         0.155 |         0.351 | indian__m     |      0.468 |     0.173 |       0.12  |       0.407 |

### Detection rate at the calibrated threshold

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1878 |      0.01  |   0.002 |   0.019 |
| wan22       | 1566 |      0.022 |   0.008 |   0.039 |
| hunyuan15   |  989 |      0     |   0     |   0     |
| ltx25       | 2002 |      0     |   0     |   0.002 |
| all         | 6435 |      0.008 |   0.003 |   0.014 |

#### by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 273 |      0.004 |   0     |   0.011 |
| ltx23       | east_asian      | 270 |      0.015 |   0     |   0.034 |
| ltx23       | indian          | 277 |      0.004 |   0     |   0.011 |
| ltx23       | latino          | 262 |      0.015 |   0     |   0.034 |
| ltx23       | mena            | 267 |      0.007 |   0     |   0.019 |
| ltx23       | southeast_asian | 271 |      0.007 |   0     |   0.019 |
| ltx23       | white           | 258 |      0.016 |   0     |   0.036 |
| wan22       | black           | 217 |      0.018 |   0     |   0.045 |
| wan22       | east_asian      | 226 |      0.009 |   0     |   0.022 |
| wan22       | indian          | 230 |      0.039 |   0.009 |   0.076 |
| wan22       | latino          | 219 |      0.023 |   0.004 |   0.05  |
| wan22       | mena            | 225 |      0.027 |   0.004 |   0.061 |
| wan22       | southeast_asian | 229 |      0.017 |   0     |   0.04  |
| wan22       | white           | 220 |      0.018 |   0     |   0.042 |
| hunyuan15   | black           | 141 |      0     |   0     |   0     |
| hunyuan15   | east_asian      | 141 |      0     |   0     |   0     |
| hunyuan15   | indian          | 142 |      0     |   0     |   0     |
| hunyuan15   | latino          | 142 |      0     |   0     |   0     |
| hunyuan15   | mena            | 139 |      0     |   0     |   0     |
| hunyuan15   | southeast_asian | 143 |      0     |   0     |   0     |
| hunyuan15   | white           | 141 |      0     |   0     |   0     |
| ltx25       | black           | 287 |      0.003 |   0     |   0.01  |
| ltx25       | east_asian      | 286 |      0     |   0     |   0     |
| ltx25       | indian          | 284 |      0     |   0     |   0     |
| ltx25       | latino          | 286 |      0     |   0     |   0     |
| ltx25       | mena            | 286 |      0     |   0     |   0     |
| ltx25       | southeast_asian | 286 |      0     |   0     |   0     |
| ltx25       | white           | 287 |      0     |   0     |   0     |
| all         | black           | 918 |      0.007 |   0     |   0.015 |
| all         | east_asian      | 923 |      0.007 |   0.001 |   0.013 |
| all         | indian          | 933 |      0.011 |   0.003 |   0.02  |
| all         | latino          | 909 |      0.01  |   0.003 |   0.019 |
| all         | mena            | 917 |      0.009 |   0.002 |   0.017 |
| all         | southeast_asian | 929 |      0.006 |   0.001 |   0.012 |
| all         | white           | 906 |      0.009 |   0.002 |   0.018 |

#### by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.008 |   0     |   0.018 |
| ltx23       | m       |  947 |      0.012 |   0.001 |   0.026 |
| wan22       | f       |  785 |      0.005 |   0     |   0.012 |
| wan22       | m       |  781 |      0.038 |   0.013 |   0.072 |
| hunyuan15   | f       |  495 |      0     |   0     |   0     |
| hunyuan15   | m       |  494 |      0     |   0     |   0     |
| ltx25       | f       |  999 |      0     |   0     |   0     |
| ltx25       | m       | 1003 |      0.001 |   0     |   0.003 |
| all         | f       | 3210 |      0.003 |   0.001 |   0.007 |
| all         | m       | 3225 |      0.013 |   0.005 |   0.022 |

#### by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  469 |      0.006 |   0     |   0.014 |
| ltx23       | 30-44   |  471 |      0.015 |   0.002 |   0.032 |
| ltx23       | 45-59   |  478 |      0.008 |   0     |   0.021 |
| ltx23       | 60+     |  460 |      0.009 |   0     |   0.02  |
| wan22       | 18-29   |  388 |      0.026 |   0.005 |   0.049 |
| wan22       | 30-44   |  377 |      0.034 |   0.011 |   0.063 |
| wan22       | 45-59   |  398 |      0.008 |   0     |   0.016 |
| wan22       | 60+     |  403 |      0.02  |   0     |   0.052 |
| hunyuan15   | 18-29   |  242 |      0     |   0     |   0     |
| hunyuan15   | 30-44   |  248 |      0     |   0     |   0     |
| hunyuan15   | 45-59   |  250 |      0     |   0     |   0     |
| hunyuan15   | 60+     |  249 |      0     |   0     |   0     |
| ltx25       | 18-29   |  500 |      0     |   0     |   0     |
| ltx25       | 30-44   |  497 |      0.002 |   0     |   0.006 |
| ltx25       | 45-59   |  501 |      0     |   0     |   0     |
| ltx25       | 60+     |  504 |      0     |   0     |   0     |
| all         | 18-29   | 1599 |      0.008 |   0.002 |   0.015 |
| all         | 30-44   | 1593 |      0.013 |   0.005 |   0.023 |
| all         | 45-59   | 1627 |      0.004 |   0.001 |   0.008 |
| all         | 60+     | 1616 |      0.007 |   0.001 |   0.016 |

### Detection-rate gap at the calibrated threshold

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level        | min_level       |
|:------------|:-----------------|------:|--------:|--------:|:-----------------|:----------------|
| ltx23       | race             | 0.012 |   0.005 |   0.036 | white            | indian          |
| ltx23       | gender           | 0.004 |   0     |   0.021 | m                | f               |
| ltx23       | age_band         | 0.008 |   0.002 |   0.024 | 30-44            | 18-29           |
| ltx23       | cell             | 0.059 |   0.031 |   0.152 | latino__m__30-44 | black__f__18-29 |
| ltx23       | setting          | 0.034 |   0.011 |   0.107 | cafe             | classroom       |
| ltx23       | lighting         | 0.021 |   0.007 |   0.069 | backlit          | harsh           |
| ltx23       | behavior         | 0.036 |   0.009 |   0.094 | listen           | laugh           |
| ltx23       | camera           | 0.004 |   0     |   0.023 | slowsway         | static          |
| ltx23       | duration_nominal | 0.003 |   0     |   0.023 | 5.0              | 6.0             |
| wan22       | race             | 0.03  |   0.017 |   0.067 | indian           | east_asian      |
| wan22       | gender           | 0.033 |   0.007 |   0.066 | m                | f               |
| wan22       | age_band         | 0.027 |   0.011 |   0.058 | 30-44            | 45-59           |
| wan22       | cell             | 0.148 |   0.083 |   0.308 | indian__m__30-44 | black__f__18-29 |
| wan22       | setting          | 0.126 |   0.032 |   0.18  | studio           | cafe            |
| wan22       | lighting         | 0.045 |   0.018 |   0.117 | backlit          | overcast        |
| wan22       | behavior         | 0.063 |   0.025 |   0.153 | think            | read            |
| wan22       | camera           | 0.01  |   0.001 |   0.042 | static           | slowsway        |
| wan22       | duration_nominal | 0.022 |   0.001 |   0.052 | 5.0              | 6.0             |
| hunyuan15   | race             | 0     |   0     |   0     | black            | black           |
| hunyuan15   | gender           | 0     |   0     |   0     | f                | f               |
| hunyuan15   | age_band         | 0     |   0     |   0     | 18-29            | 18-29           |
| hunyuan15   | cell             | 0     |   0     |   0     | black__f__18-29  | black__f__18-29 |
| hunyuan15   | setting          | 0     |   0     |   0     | cafe             | cafe            |
| hunyuan15   | lighting         | 0     |   0     |   0     | backlit          | backlit         |
| hunyuan15   | behavior         | 0     |   0     |   0     | laugh            | laugh           |
| hunyuan15   | camera           | 0     |   0     |   0     | slowsway         | slowsway        |
| hunyuan15   | duration_nominal | 0     |   0     |   0     | 5.0              | 5.0             |
| ltx25       | race             | 0.003 |   0     |   0.01  | black            | east_asian      |
| ltx25       | gender           | 0.001 |   0     |   0.003 | m                | f               |
| ltx25       | age_band         | 0.002 |   0     |   0.006 | 30-44            | 18-29           |
| ltx25       | cell             | 0.029 |   0     |   0.088 | black__m__30-44  | black__f__18-29 |
| ltx25       | setting          | 0.005 |   0     |   0.018 | cafe             | classroom       |
| ltx25       | lighting         | 0.003 |   0     |   0.009 | backlit          | harsh           |
| ltx25       | behavior         | 0.004 |   0     |   0.012 | listen           | laugh           |
| ltx25       | camera           | 0.001 |   0     |   0.003 | slowsway         | static          |
| ltx25       | duration_nominal | 0.001 |   0     |   0.003 | 6.0              | 5.0             |
| all         | race             | 0.004 |   0.004 |   0.015 | indian           | southeast_asian |
| all         | gender           | 0.01  |   0.003 |   0.017 | m                | f               |
| all         | age_band         | 0.009 |   0.003 |   0.018 | 30-44            | 45-59           |
| all         | cell             | 0.044 |   0.026 |   0.084 | indian__m__30-44 | black__f__18-29 |
| all         | setting          | 0.042 |   0.023 |   0.051 | studio           | corridor        |
| all         | lighting         | 0.019 |   0.009 |   0.037 | backlit          | harsh           |
| all         | behavior         | 0.019 |   0.01  |   0.046 | listen           | speak           |
| all         | camera           | 0.001 |   0     |   0.012 | static           | slowsway        |
| all         | duration_nominal | 0.006 |   0     |   0.018 | 5.0              | 6.0             |

### Flip rate at the calibrated threshold

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.167 |   0.056 |   0.306 |        0 |     1 |
| wan22       |         36 |       0.306 |   0.167 |   0.444 |        0 |     1 |
| hunyuan15   |         18 |       0     |   0     |   0     |        0 |     0 |
| ltx25       |         36 |       0.028 |   0     |   0.083 |        0 |     1 |

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

