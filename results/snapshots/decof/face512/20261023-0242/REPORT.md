# decof / face512: snapshot 20261023-0242

> **Detector training data.** The released DeCoF checkpoint is most likely trained on AIGVDBench's Open-Sora split (per the paper's default training set and the checkpoint name); our generators are therefore likely unseen. Not confirmed by the authors. Our curated GenBuster subset includes LTX-Video and HunyuanVideo, which are separate from DeCoF's training data but not from AIGVDBench as a whole.

> **Provisional threshold.** Every detection rate and flip rate below uses the detector's default threshold (0.5; official: argmax over 2 logits (DeCoF test.py) == softmax[:,1] >= 0.5). They will be replaced by the 5%-real-FPR threshold once reals exist (section 6.3).

## Settings

| setting           | value                                                                                  |
|:------------------|:---------------------------------------------------------------------------------------|
| detector          | decof 1+b75d2cbe                                                                       |
| checkpoint_sha256 | 4edb7b310cc729771e74b93f658c7fdc4f2e31fdfa617a88372a540d4f9e7b4a                       |
| view              | face512 (view_hash 330ecb1e37e36e82)                                                   |
| ffmpeg            | ffmpeg version 7.1.1 Copyright (c) 2000-2025 the FFmpeg developers                     |
| batches           | fake_b1, fake_b2, fake_b3, real_all                                                    |
| inclusion set     | primary (technical QC pass AND face QC pass)                                           |
| bootstrap         | 1000 resamples of whole counterfactual groups, seed 20261020, 95% percentile intervals |
| git commit        | 2949de581861-dirty                                                                     |
| created           | 2026-10-23T02:43:03Z                                                                   |

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

| batch    | generator   |   clips |   primary |   rendered |   view_excluded |   render_failed |   scored |   score_failed |   included |
|:---------|:------------|--------:|----------:|-----------:|----------------:|----------------:|---------:|---------------:|-----------:|
| fake_b1  | hunyuan15   |     504 |       492 |        504 |               0 |               0 |      504 |              0 |        492 |
| fake_b1  | ltx23       |    2016 |      1878 |       2012 |               4 |               0 |     2012 |              0 |       1874 |
| fake_b1  | wan22       |    2016 |      1566 |       2016 |               0 |               0 |     2016 |              0 |       1566 |
| fake_b2  | hunyuan15   |     504 |       497 |        504 |               0 |               0 |      504 |              0 |        497 |
| fake_b3  | ltx25       |    2016 |      2002 |       2016 |               0 |               0 |     2016 |              0 |       2002 |
| real_all | real        |    2221 |      2221 |        919 |            1279 |              23 |      928 |              0 |        928 |

face512 window placement (fixed window at the median YuNet face centre, shifted inward at frame edges). The scaled frame is exactly 512 px on its short side, so every window spans it fully and is "shifted" on that axis by construction; the long-axis count is the informative one.

|   rendered |   shifted_long_axis |   shifted_short_axis |   max_shift_long_px |   excluded_no_face |
|-----------:|--------------------:|---------------------:|--------------------:|-------------------:|
|       8899 |                 159 |                 8839 |                 186 |                 12 |

Reals scored: 1847. Fakes included: 6431 of 8899 scored (0 scoring failures).

## Observations

- LTX 2.3: mean score 0.592 [0.524, 0.661], median 0.665, n = 1874.
- Wan 2.2: mean score 0.180 [0.139, 0.223], median 0.058, n = 1566.
- HunyuanVideo 1.5: mean score 0.381 [0.327, 0.440], median 0.291, n = 989.
- LTX 2.5: mean score 0.400 [0.335, 0.463], median 0.319, n = 2002.
- Provisional detection rate (score >= 0.5), LTX 2.3: 61.2% [52.4, 69.9].
- Provisional detection rate (score >= 0.5), Wan 2.2: 13.3% [9.4, 17.6].
- Provisional detection rate (score >= 0.5), HunyuanVideo 1.5: 35.6% [28.7, 42.7].
- Provisional detection rate (score >= 0.5), LTX 2.5: 37.1% [29.2, 44.8].
- Provisional detection rate (score >= 0.5), all: 38.1% [32.8, 43.3].
- Largest race score gap: Wan 2.2 0.261 [0.221, 0.302] (white 0.353 vs east_asian 0.091).
- Largest gender score gap: Wan 2.2 0.098 [0.062, 0.132] (f 0.229 vs m 0.130).
- Largest age band score gap: HunyuanVideo 1.5 0.295 [0.243, 0.364] (18-29 0.505 vs 60+ 0.210).
- Largest cell score gap: HunyuanVideo 1.5 0.782 [0.717, 0.874] (white__f__18-29 0.838 vs black__f__60+ 0.056).
- Largest scene-factor gap (all generators): behavior 0.337 [0.264, 0.475] (laugh vs think).
- Largest partial eta squared: generator 0.269, age_band 0.102, behavior 0.079; residual holds 55.3% of total SS.
- CF spread, LTX 2.3: 0.252 [0.229, 0.274] over 36 groups (max 0.386).
- CF spread, Wan 2.2: 0.191 [0.166, 0.216] over 36 groups (max 0.324).
- CF spread, HunyuanVideo 1.5: 0.292 [0.274, 0.309] over 18 groups (max 0.349).
- CF spread, LTX 2.5: 0.268 [0.251, 0.286] over 36 groups (max 0.357).
- Provisional flip rate, LTX 2.3: 94.4% of 36 groups [86.1, 100.0].
- Provisional flip rate, Wan 2.2: 77.8% of 36 groups [63.9, 91.7].
- Provisional flip rate, HunyuanVideo 1.5: 100.0% of 18 groups [100.0, 100.0].
- Provisional flip rate, LTX 2.5: 100.0% of 36 groups [100.0, 100.0].

## 6.1 Fakes only, no threshold

### Mean score by generator

| generator   |    n |   n_groups |   estimate |   ci_lo |   ci_hi |    sd |   median |   q05 |   q95 |
|:------------|-----:|-----------:|-----------:|--------:|--------:|------:|---------:|------:|------:|
| ltx23       | 1874 |         36 |      0.592 |   0.524 |   0.661 | 0.331 |    0.665 | 0.036 | 0.992 |
| wan22       | 1566 |         36 |      0.18  |   0.139 |   0.223 | 0.244 |    0.058 | 0.003 | 0.766 |
| hunyuan15   |  989 |         18 |      0.381 |   0.327 |   0.44  | 0.319 |    0.291 | 0.013 | 0.947 |
| ltx25       | 2002 |         36 |      0.4   |   0.335 |   0.463 | 0.337 |    0.319 | 0.011 | 0.963 |
| all         | 6431 |         36 |      0.399 |   0.354 |   0.441 | 0.346 |    0.311 | 0.007 | 0.973 |

### Mean score by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:----------------|----:|-----------:|--------:|--------:|---------:|
| ltx23       | black           | 272 |      0.578 |   0.495 |   0.662 |    0.661 |
| ltx23       | east_asian      | 270 |      0.498 |   0.415 |   0.581 |    0.482 |
| ltx23       | indian          | 277 |      0.664 |   0.593 |   0.733 |    0.799 |
| ltx23       | latino          | 262 |      0.606 |   0.528 |   0.682 |    0.67  |
| ltx23       | mena            | 266 |      0.585 |   0.508 |   0.663 |    0.655 |
| ltx23       | southeast_asian | 271 |      0.55  |   0.474 |   0.625 |    0.583 |
| ltx23       | white           | 256 |      0.664 |   0.59  |   0.742 |    0.763 |
| wan22       | black           | 217 |      0.165 |   0.11  |   0.224 |    0.055 |
| wan22       | east_asian      | 226 |      0.091 |   0.059 |   0.123 |    0.031 |
| wan22       | indian          | 230 |      0.118 |   0.079 |   0.157 |    0.024 |
| wan22       | latino          | 219 |      0.221 |   0.163 |   0.277 |    0.08  |
| wan22       | mena            | 225 |      0.215 |   0.163 |   0.267 |    0.077 |
| wan22       | southeast_asian | 229 |      0.103 |   0.067 |   0.141 |    0.03  |
| wan22       | white           | 220 |      0.353 |   0.295 |   0.412 |    0.283 |
| hunyuan15   | black           | 141 |      0.311 |   0.234 |   0.391 |    0.191 |
| hunyuan15   | east_asian      | 141 |      0.288 |   0.231 |   0.348 |    0.182 |
| hunyuan15   | indian          | 142 |      0.449 |   0.382 |   0.523 |    0.412 |
| hunyuan15   | latino          | 142 |      0.368 |   0.301 |   0.441 |    0.28  |
| hunyuan15   | mena            | 139 |      0.4   |   0.344 |   0.456 |    0.349 |
| hunyuan15   | southeast_asian | 143 |      0.332 |   0.265 |   0.401 |    0.22  |
| hunyuan15   | white           | 141 |      0.519 |   0.445 |   0.594 |    0.526 |
| ltx25       | black           | 287 |      0.412 |   0.336 |   0.486 |    0.35  |
| ltx25       | east_asian      | 286 |      0.344 |   0.272 |   0.408 |    0.24  |
| ltx25       | indian          | 284 |      0.381 |   0.316 |   0.444 |    0.258 |
| ltx25       | latino          | 286 |      0.345 |   0.281 |   0.409 |    0.231 |
| ltx25       | mena            | 286 |      0.425 |   0.356 |   0.497 |    0.393 |
| ltx25       | southeast_asian | 286 |      0.341 |   0.275 |   0.407 |    0.249 |
| ltx25       | white           | 287 |      0.548 |   0.475 |   0.618 |    0.59  |
| all         | black           | 917 |      0.387 |   0.337 |   0.439 |    0.31  |
| all         | east_asian      | 923 |      0.319 |   0.273 |   0.363 |    0.179 |
| all         | indian          | 933 |      0.41  |   0.37  |   0.448 |    0.3   |
| all         | latino          | 909 |      0.394 |   0.342 |   0.445 |    0.301 |
| all         | mena            | 916 |      0.416 |   0.369 |   0.461 |    0.364 |
| all         | southeast_asian | 929 |      0.342 |   0.298 |   0.385 |    0.216 |
| all         | white           | 904 |      0.529 |   0.477 |   0.579 |    0.559 |

### Mean score by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | f       |  931 |      0.613 |   0.541 |   0.684 |    0.715 |
| ltx23       | m       |  943 |      0.572 |   0.504 |   0.642 |    0.628 |
| wan22       | f       |  785 |      0.229 |   0.18  |   0.276 |    0.092 |
| wan22       | m       |  781 |      0.13  |   0.089 |   0.176 |    0.034 |
| hunyuan15   | f       |  495 |      0.423 |   0.361 |   0.483 |    0.38  |
| hunyuan15   | m       |  494 |      0.339 |   0.273 |   0.412 |    0.238 |
| ltx25       | f       |  999 |      0.396 |   0.333 |   0.459 |    0.316 |
| ltx25       | m       | 1003 |      0.404 |   0.336 |   0.471 |    0.323 |
| all         | f       | 3210 |      0.422 |   0.378 |   0.466 |    0.35  |
| all         | m       | 3221 |      0.377 |   0.331 |   0.423 |    0.276 |

### Mean score by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | 18-29   |  468 |      0.644 |   0.574 |   0.71  |    0.761 |
| ltx23       | 30-44   |  470 |      0.686 |   0.622 |   0.752 |    0.798 |
| ltx23       | 45-59   |  478 |      0.571 |   0.494 |   0.647 |    0.626 |
| ltx23       | 60+     |  458 |      0.465 |   0.381 |   0.556 |    0.431 |
| wan22       | 18-29   |  388 |      0.23  |   0.176 |   0.284 |    0.09  |
| wan22       | 30-44   |  377 |      0.237 |   0.179 |   0.295 |    0.103 |
| wan22       | 45-59   |  398 |      0.185 |   0.146 |   0.226 |    0.079 |
| wan22       | 60+     |  403 |      0.072 |   0.041 |   0.113 |    0.019 |
| hunyuan15   | 18-29   |  242 |      0.505 |   0.437 |   0.585 |    0.493 |
| hunyuan15   | 30-44   |  248 |      0.497 |   0.415 |   0.582 |    0.524 |
| hunyuan15   | 45-59   |  250 |      0.316 |   0.26  |   0.369 |    0.211 |
| hunyuan15   | 60+     |  249 |      0.21  |   0.165 |   0.261 |    0.124 |
| ltx25       | 18-29   |  500 |      0.45  |   0.372 |   0.523 |    0.394 |
| ltx25       | 30-44   |  497 |      0.512 |   0.44  |   0.581 |    0.512 |
| ltx25       | 45-59   |  501 |      0.382 |   0.312 |   0.452 |    0.287 |
| ltx25       | 60+     |  504 |      0.257 |   0.193 |   0.321 |    0.133 |
| all         | 18-29   | 1598 |      0.462 |   0.408 |   0.514 |    0.425 |
| all         | 30-44   | 1592 |      0.496 |   0.445 |   0.543 |    0.504 |
| all         | 45-59   | 1627 |      0.379 |   0.335 |   0.423 |    0.294 |
| all         | 60+     | 1614 |      0.263 |   0.222 |   0.303 |    0.124 |

### Mean score by scene factor (all generators pooled)

| factor           | level      |    n |   estimate |   ci_lo |   ci_hi |
|:-----------------|:-----------|-----:|-----------:|--------:|--------:|
| setting          | cafe       |  592 |      0.256 |   0.169 |   0.431 |
| setting          | classroom  |  541 |      0.5   |   0.412 |   0.625 |
| setting          | corridor   |  716 |      0.478 |   0.386 |   0.561 |
| setting          | kitchen    |  605 |      0.335 |   0.169 |   0.58  |
| setting          | library    |  755 |      0.573 |   0.534 |   0.686 |
| setting          | livingroom |  754 |      0.286 |   0.165 |   0.374 |
| setting          | lobby      |  513 |      0.341 |   0.303 |   0.398 |
| setting          | office     |  580 |      0.396 |   0.313 |   0.48  |
| setting          | plainwall  |  777 |      0.374 |   0.341 |   0.416 |
| setting          | studio     |  598 |      0.431 |   0.286 |   0.588 |
| lighting         | backlit    | 1122 |      0.418 |   0.255 |   0.55  |
| lighting         | harsh      |  967 |      0.32  |   0.202 |   0.479 |
| lighting         | lowlight   | 1116 |      0.513 |   0.409 |   0.618 |
| lighting         | overcast   | 1022 |      0.369 |   0.296 |   0.434 |
| lighting         | softwindow | 1157 |      0.401 |   0.379 |   0.43  |
| lighting         | warmlamp   | 1047 |      0.358 |   0.255 |   0.461 |
| behavior         | laugh      |  721 |      0.603 |   0.555 |   0.672 |
| behavior         | listen     |  959 |      0.492 |   0.406 |   0.566 |
| behavior         | pause      |  744 |      0.324 |   0.175 |   0.378 |
| behavior         | read       |  796 |      0.272 |   0.169 |   0.416 |
| behavior         | smile      |  817 |      0.382 |   0.297 |   0.471 |
| behavior         | speak      |  806 |      0.411 |   0.277 |   0.498 |
| behavior         | think      |  732 |      0.265 |   0.135 |   0.329 |
| behavior         | turn       |  856 |      0.428 |   0.353 |   0.533 |
| camera           | slowsway   | 3223 |      0.41  |   0.335 |   0.479 |
| camera           | static     | 3208 |      0.388 |   0.341 |   0.437 |
| duration_nominal | 5.0        | 3225 |      0.381 |   0.307 |   0.456 |
| duration_nominal | 6.0        | 3206 |      0.418 |   0.377 |   0.466 |

Per-generator scene-factor and 56-cell rows: `tables/score_by_breakdown.csv`.

### Subgroup gap (max - min of level means)

A gap is max - min, so it is never negative and its interval cannot include 0; it is a size, not a test of a difference. Over many levels with few clips each (56 cells; HunyuanVideo has 9 groups per cell) the gap also grows with noise, so compare it with the per-level intervals in `tables/score_by_breakdown.csv`. Levels seen in a single counterfactual group have no interval.

| generator   | attribute        |   n_levels |   gap |   ci_lo |   ci_hi | max_level       | min_level          |
|:------------|:-----------------|-----------:|------:|--------:|--------:|:----------------|:-------------------|
| ltx23       | race             |          7 | 0.166 |   0.131 |   0.225 | white           | east_asian         |
| ltx23       | gender           |          2 | 0.041 |   0.011 |   0.073 | f               | m                  |
| ltx23       | age_band         |          4 | 0.221 |   0.167 |   0.275 | 30-44           | 60+                |
| ltx23       | cell             |         56 | 0.545 |   0.483 |   0.652 | white__f__30-44 | east_asian__f__60+ |
| ltx23       | setting          |         10 | 0.417 |   0.326 |   0.733 | library         | cafe               |
| ltx23       | lighting         |          6 | 0.388 |   0.215 |   0.604 | lowlight        | harsh              |
| ltx23       | behavior         |          8 | 0.419 |   0.304 |   0.659 | laugh           | think              |
| ltx23       | camera           |          2 | 0.062 |   0.004 |   0.205 | slowsway        | static             |
| ltx23       | duration_nominal |          2 | 0.045 |   0.003 |   0.194 | 6.0             | 5.0                |
| wan22       | race             |          7 | 0.261 |   0.221 |   0.302 | white           | east_asian         |
| wan22       | gender           |          2 | 0.098 |   0.062 |   0.132 | f               | m                  |
| wan22       | age_band         |          4 | 0.165 |   0.121 |   0.214 | 30-44           | 60+                |
| wan22       | cell             |         56 | 0.617 |   0.521 |   0.726 | white__f__18-29 | east_asian__f__60+ |
| wan22       | setting          |         10 | 0.291 |   0.229 |   0.444 | library         | cafe               |
| wan22       | lighting         |          6 | 0.091 |   0.067 |   0.315 | lowlight        | overcast           |
| wan22       | behavior         |          8 | 0.292 |   0.192 |   0.435 | laugh           | read               |
| wan22       | camera           |          2 | 0.004 |   0.001 |   0.103 | static          | slowsway           |
| wan22       | duration_nominal |          2 | 0.083 |   0.011 |   0.158 | 5.0             | 6.0                |
| hunyuan15   | race             |          7 | 0.232 |   0.175 |   0.306 | white           | east_asian         |
| hunyuan15   | gender           |          2 | 0.084 |   0.023 |   0.146 | f               | m                  |
| hunyuan15   | age_band         |          4 | 0.295 |   0.243 |   0.364 | 18-29           | 60+                |
| hunyuan15   | cell             |         56 | 0.782 |   0.717 |   0.874 | white__f__18-29 | black__f__60+      |
| hunyuan15   | setting          |         10 | 0.373 |   0.224 |   0.411 | library         | kitchen            |
| hunyuan15   | lighting         |          6 | 0.134 |   0.11  |   0.362 | lowlight        | softwindow         |
| hunyuan15   | behavior         |          8 | 0.328 |   0.186 |   0.401 | laugh           | pause              |
| hunyuan15   | camera           |          2 | 0.087 |   0.007 |   0.193 | static          | slowsway           |
| hunyuan15   | duration_nominal |          2 | 0.031 |   0.003 |   0.148 | 6.0             | 5.0                |
| ltx25       | race             |          7 | 0.207 |   0.18  |   0.251 | white           | southeast_asian    |
| ltx25       | gender           |          2 | 0.008 |   0.001 |   0.044 | m               | f                  |
| ltx25       | age_band         |          4 | 0.254 |   0.189 |   0.321 | 30-44           | 60+                |
| ltx25       | cell             |         56 | 0.664 |   0.594 |   0.751 | white__f__30-44 | indian__f__60+     |
| ltx25       | setting          |         10 | 0.344 |   0.292 |   0.661 | library         | livingroom         |
| ltx25       | lighting         |          6 | 0.237 |   0.161 |   0.477 | lowlight        | overcast           |
| ltx25       | behavior         |          8 | 0.454 |   0.361 |   0.616 | laugh           | pause              |
| ltx25       | camera           |          2 | 0.054 |   0.003 |   0.18  | slowsway        | static             |
| ltx25       | duration_nominal |          2 | 0.073 |   0.005 |   0.201 | 6.0             | 5.0                |
| all         | race             |          7 | 0.21  |   0.181 |   0.241 | white           | east_asian         |
| all         | gender           |          2 | 0.045 |   0.021 |   0.068 | f               | m                  |
| all         | age_band         |          4 | 0.233 |   0.2   |   0.264 | 30-44           | 60+                |
| all         | cell             |         56 | 0.596 |   0.551 |   0.657 | white__f__30-44 | east_asian__f__60+ |
| all         | setting          |         10 | 0.317 |   0.248 |   0.462 | library         | cafe               |
| all         | lighting         |          6 | 0.194 |   0.106 |   0.366 | lowlight        | harsh              |
| all         | behavior         |          8 | 0.337 |   0.264 |   0.475 | laugh           | think              |
| all         | camera           |          2 | 0.022 |   0.002 |   0.108 | slowsway        | static             |
| all         | duration_nominal |          2 | 0.037 |   0.001 |   0.124 | 6.0             | 5.0                |

### CF spread (mean over groups of the std of score across the group's cells)

| generator   |   n_groups |   cf_spread |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.252 |   0.229 |   0.274 |    0.265 | 0.386 |
| wan22       |         36 |       0.191 |   0.166 |   0.216 |    0.205 | 0.324 |
| hunyuan15   |         18 |       0.292 |   0.274 |   0.309 |    0.302 | 0.349 |
| ltx25       |         36 |       0.268 |   0.251 |   0.286 |    0.285 | 0.357 |

### Factor attribution

OLS with every factor as a fixed effect, type-II ANOVA. `ss_share` is the factor's type-II sum of squares over the total sum of squares (type-II shares need not add to 1). Scene factors are constant within a counterfactual group, so their effects are estimated from between-group differences only. The OLS F tests treat clips as independent although clips are clustered in counterfactual groups, so their p values are optimistic; use the group-bootstrap intervals above for inference.

| factor           |   df |    sum_sq | F      | p          | partial_eta2   |   ss_share |
|:-----------------|-----:|----------:|:-------|:-----------|:---------------|-----------:|
| race             |    6 |  25.26    | 63.03  | 2.689e-76  | 0.05584        |  0.03273   |
| gender           |    1 |   3.237   | 48.47  | 3.69e-12   | 0.007523       |  0.004195  |
| age_band         |    3 |  48.71    | 243.1  | 2.275e-149 | 0.1024         |  0.06312   |
| setting          |    9 |  21.5     | 35.77  | 2.459e-62  | 0.04794        |  0.02787   |
| lighting         |    5 |   7.892   | 23.63  | 1.285e-23  | 0.01814        |  0.01023   |
| behavior         |    7 |  36.65    | 78.38  | 1.534e-109 | 0.07903        |  0.04749   |
| camera           |    1 |   0.05087 | 0.7617 | 0.3828     | 0.0001191      |  6.593e-05 |
| duration_nominal |    1 |   0.02264 | 0.339  | 0.5604     | 5.302e-05      |  2.935e-05 |
| generator        |    3 | 157.2     | 784.6  | 0          | 0.2691         |  0.2038    |
| Residual         | 6394 | 427.1     |        |            |                |  0.5535    |

Lighting x race interaction (added to the same OLS):

| term            |   df |   sum_sq |    F |      p |   partial_eta2 |
|:----------------|-----:|---------:|-----:|-------:|---------------:|
| lighting x race |   30 |    2.423 | 1.21 | 0.1988 |       0.005673 |

Mixed model `score ~ factors + (1 | counterfactual_group)` (REML) variance components (fixed effects: `tables/factor_mixed_fixed.csv`):

| component                               |   variance | converged   |
|:----------------------------------------|-----------:|:------------|
| counterfactual_group (random intercept) |    0       | True        |
| residual                                |    0.06582 | True        |
| ICC (group share of random variance)    |    0       | True        |

A group variance at or near 0 is a boundary estimate: setting, lighting, behavior, camera and duration are fixed per group and absorb most between-group variation, leaving little for the random intercept. It does not mean scenes do not matter.

## 6.2 Provisional (threshold 0.5, provisional)

### Detection rate by generator (provisional)

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1874 |      0.612 |   0.524 |   0.699 |
| wan22       | 1566 |      0.133 |   0.094 |   0.176 |
| hunyuan15   |  989 |      0.356 |   0.287 |   0.427 |
| ltx25       | 2002 |      0.371 |   0.292 |   0.448 |
| all         | 6431 |      0.381 |   0.328 |   0.433 |

### Detection rate by race (provisional)

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 272 |      0.592 |   0.48  |   0.703 |
| ltx23       | east_asian      | 270 |      0.496 |   0.383 |   0.603 |
| ltx23       | indian          | 277 |      0.682 |   0.59  |   0.777 |
| ltx23       | latino          | 262 |      0.634 |   0.534 |   0.732 |
| ltx23       | mena            | 266 |      0.617 |   0.508 |   0.72  |
| ltx23       | southeast_asian | 271 |      0.565 |   0.46  |   0.669 |
| ltx23       | white           | 256 |      0.699 |   0.606 |   0.789 |
| wan22       | black           | 217 |      0.111 |   0.045 |   0.182 |
| wan22       | east_asian      | 226 |      0.031 |   0.008 |   0.061 |
| wan22       | indian          | 230 |      0.065 |   0.026 |   0.104 |
| wan22       | latino          | 219 |      0.183 |   0.114 |   0.255 |
| wan22       | mena            | 225 |      0.182 |   0.119 |   0.247 |
| wan22       | southeast_asian | 229 |      0.052 |   0.019 |   0.088 |
| wan22       | white           | 220 |      0.314 |   0.239 |   0.39  |
| hunyuan15   | black           | 141 |      0.27  |   0.161 |   0.391 |
| hunyuan15   | east_asian      | 141 |      0.234 |   0.161 |   0.316 |
| hunyuan15   | indian          | 142 |      0.43  |   0.333 |   0.523 |
| hunyuan15   | latino          | 142 |      0.352 |   0.247 |   0.47  |
| hunyuan15   | mena            | 139 |      0.353 |   0.277 |   0.425 |
| hunyuan15   | southeast_asian | 143 |      0.315 |   0.231 |   0.401 |
| hunyuan15   | white           | 141 |      0.539 |   0.436 |   0.636 |
| ltx25       | black           | 287 |      0.38  |   0.278 |   0.479 |
| ltx25       | east_asian      | 286 |      0.318 |   0.226 |   0.409 |
| ltx25       | indian          | 284 |      0.327 |   0.243 |   0.408 |
| ltx25       | latino          | 286 |      0.294 |   0.211 |   0.381 |
| ltx25       | mena            | 286 |      0.413 |   0.325 |   0.498 |
| ltx25       | southeast_asian | 286 |      0.308 |   0.217 |   0.397 |
| ltx25       | white           | 287 |      0.554 |   0.456 |   0.647 |
| all         | black           | 917 |      0.362 |   0.305 |   0.42  |
| all         | east_asian      | 923 |      0.287 |   0.23  |   0.342 |
| all         | indian          | 933 |      0.384 |   0.334 |   0.435 |
| all         | latino          | 909 |      0.374 |   0.304 |   0.442 |
| all         | mena            | 916 |      0.406 |   0.348 |   0.465 |
| all         | southeast_asian | 929 |      0.321 |   0.271 |   0.371 |
| all         | white           | 904 |      0.534 |   0.471 |   0.6   |

### Detection rate by gender (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.629 |   0.542 |   0.716 |
| ltx23       | m       |  943 |      0.594 |   0.502 |   0.69  |
| wan22       | f       |  785 |      0.192 |   0.137 |   0.244 |
| wan22       | m       |  781 |      0.073 |   0.033 |   0.119 |
| hunyuan15   | f       |  495 |      0.43  |   0.349 |   0.508 |
| hunyuan15   | m       |  494 |      0.281 |   0.191 |   0.375 |
| ltx25       | f       |  999 |      0.374 |   0.301 |   0.451 |
| ltx25       | m       | 1003 |      0.367 |   0.28  |   0.456 |
| all         | f       | 3210 |      0.412 |   0.361 |   0.461 |
| all         | m       | 3221 |      0.349 |   0.296 |   0.405 |

### Detection rate by age band (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  468 |      0.669 |   0.58  |   0.753 |
| ltx23       | 30-44   |  470 |      0.726 |   0.642 |   0.807 |
| ltx23       | 45-59   |  478 |      0.594 |   0.485 |   0.698 |
| ltx23       | 60+     |  458 |      0.454 |   0.344 |   0.57  |
| wan22       | 18-29   |  388 |      0.204 |   0.138 |   0.27  |
| wan22       | 30-44   |  377 |      0.204 |   0.14  |   0.27  |
| wan22       | 45-59   |  398 |      0.108 |   0.065 |   0.151 |
| wan22       | 60+     |  403 |      0.022 |   0     |   0.049 |
| hunyuan15   | 18-29   |  242 |      0.496 |   0.398 |   0.602 |
| hunyuan15   | 30-44   |  248 |      0.52  |   0.404 |   0.636 |
| hunyuan15   | 45-59   |  250 |      0.288 |   0.22  |   0.355 |
| hunyuan15   | 60+     |  249 |      0.124 |   0.065 |   0.186 |
| ltx25       | 18-29   |  500 |      0.436 |   0.34  |   0.528 |
| ltx25       | 30-44   |  497 |      0.505 |   0.413 |   0.597 |
| ltx25       | 45-59   |  501 |      0.347 |   0.262 |   0.435 |
| ltx25       | 60+     |  504 |      0.196 |   0.121 |   0.274 |
| all         | 18-29   | 1598 |      0.457 |   0.391 |   0.52  |
| all         | 30-44   | 1592 |      0.501 |   0.439 |   0.558 |
| all         | 45-59   | 1627 |      0.352 |   0.3   |   0.407 |
| all         | 60+     | 1614 |      0.215 |   0.167 |   0.262 |

### Detection-rate gap (provisional)

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level       | min_level          |
|:------------|:-----------------|------:|--------:|--------:|:----------------|:-------------------|
| ltx23       | race             | 0.203 |   0.147 |   0.284 | white           | east_asian         |
| ltx23       | gender           | 0.036 |   0.002 |   0.085 | f               | m                  |
| ltx23       | age_band         | 0.271 |   0.191 |   0.35  | 30-44           | 60+                |
| ltx23       | cell             | 0.643 |   0.575 |   0.829 | white__f__30-44 | east_asian__f__60+ |
| ltx23       | setting          | 0.57  |   0.435 |   0.868 | library         | cafe               |
| ltx23       | lighting         | 0.465 |   0.248 |   0.742 | lowlight        | harsh              |
| ltx23       | behavior         | 0.543 |   0.383 |   0.838 | laugh           | think              |
| ltx23       | camera           | 0.07  |   0.004 |   0.246 | slowsway        | static             |
| ltx23       | duration_nominal | 0.059 |   0.003 |   0.244 | 6.0             | 5.0                |
| wan22       | race             | 0.283 |   0.208 |   0.356 | white           | east_asian         |
| wan22       | gender           | 0.119 |   0.071 |   0.166 | f               | m                  |
| wan22       | age_band         | 0.182 |   0.139 |   0.247 | 30-44           | 60+                |
| wan22       | cell             | 0.741 |   0.591 |   0.897 | white__f__18-29 | black__f__45-59    |
| wan22       | setting          | 0.272 |   0.203 |   0.449 | classroom       | cafe               |
| wan22       | lighting         | 0.08  |   0.063 |   0.321 | harsh           | overcast           |
| wan22       | behavior         | 0.267 |   0.169 |   0.437 | laugh           | think              |
| wan22       | camera           | 0.004 |   0.001 |   0.099 | slowsway        | static             |
| wan22       | duration_nominal | 0.079 |   0.009 |   0.152 | 5.0             | 6.0                |
| hunyuan15   | race             | 0.305 |   0.227 |   0.418 | white           | east_asian         |
| hunyuan15   | gender           | 0.149 |   0.057 |   0.241 | f               | m                  |
| hunyuan15   | age_band         | 0.396 |   0.328 |   0.495 | 30-44           | 60+                |
| hunyuan15   | cell             | 0.941 |   0.869 |   1     | white__f__18-29 | black__f__60+      |
| hunyuan15   | setting          | 0.491 |   0.286 |   0.554 | library         | kitchen            |
| hunyuan15   | lighting         | 0.175 |   0.137 |   0.464 | lowlight        | softwindow         |
| hunyuan15   | behavior         | 0.423 |   0.236 |   0.536 | laugh           | pause              |
| hunyuan15   | camera           | 0.112 |   0.009 |   0.246 | static          | slowsway           |
| hunyuan15   | duration_nominal | 0.043 |   0.004 |   0.199 | 6.0             | 5.0                |
| ltx25       | race             | 0.26  |   0.208 |   0.327 | white           | latino             |
| ltx25       | gender           | 0.007 |   0.001 |   0.059 | f               | m                  |
| ltx25       | age_band         | 0.309 |   0.229 |   0.398 | 30-44           | 60+                |
| ltx25       | cell             | 0.806 |   0.722 |   0.944 | white__f__30-44 | black__f__60+      |
| ltx25       | setting          | 0.44  |   0.368 |   0.816 | library         | livingroom         |
| ltx25       | lighting         | 0.292 |   0.199 |   0.589 | lowlight        | harsh              |
| ltx25       | behavior         | 0.561 |   0.431 |   0.774 | laugh           | think              |
| ltx25       | camera           | 0.063 |   0.003 |   0.222 | slowsway        | static             |
| ltx25       | duration_nominal | 0.082 |   0.005 |   0.239 | 6.0             | 5.0                |
| all         | race             | 0.247 |   0.205 |   0.291 | white           | east_asian         |
| all         | gender           | 0.064 |   0.031 |   0.092 | f               | m                  |
| all         | age_band         | 0.286 |   0.242 |   0.329 | 30-44           | 60+                |
| all         | cell             | 0.714 |   0.655 |   0.805 | white__f__30-44 | black__f__60+      |
| all         | setting          | 0.386 |   0.296 |   0.572 | library         | cafe               |
| all         | lighting         | 0.23  |   0.128 |   0.433 | lowlight        | harsh              |
| all         | behavior         | 0.408 |   0.305 |   0.582 | laugh           | think              |
| all         | camera           | 0.026 |   0.002 |   0.127 | slowsway        | static             |
| all         | duration_nominal | 0.05  |   0.002 |   0.148 | 6.0             | 5.0                |

### Flip rate (provisional): share of groups whose clips get different decisions

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.944 |   0.861 |   1     |        1 |     1 |
| wan22       |         36 |       0.778 |   0.639 |   0.917 |        1 |     1 |
| hunyuan15   |         18 |       1     |   1     |   1     |        1 |     1 |
| ltx25       |         36 |       1     |   1     |   1     |        1 |     1 |

### Sensitivity: inclusion set

| set     | generator   |    n |   mean_score |   provisional_detection_rate |
|:--------|:------------|-----:|-------------:|-----------------------------:|
| all     | hunyuan15   | 1008 |        0.384 |                        0.36  |
| all     | ltx23       | 2012 |        0.593 |                        0.611 |
| all     | ltx25       | 2016 |        0.399 |                        0.371 |
| all     | wan22       | 2016 |        0.188 |                        0.145 |
| primary | hunyuan15   |  989 |        0.381 |                        0.356 |
| primary | ltx23       | 1874 |        0.592 |                        0.612 |
| primary | ltx25       | 2002 |        0.4   |                        0.371 |
| primary | wan22       | 1566 |        0.18  |                        0.133 |

## 6.3 Real vs generated (calibrated threshold 0.8563)

The threshold is the score at which 5% of primary real renders (24 and 16 fps pooled) are flagged; one per detector and view, never per subgroup. Each generator is compared with reals rendered at its own fps. Intervals: fakes resample counterfactual groups, reals resample identity clusters (source video). Real labels are perceived (FairFace), not self-reported.

### Calibration

| scope            |   n_renders |   n_sources |   n_identities |   threshold |    fpr |
|:-----------------|------------:|------------:|---------------:|------------:|-------:|
| all real renders |        1847 |         928 |            807 |      0.8563 | 0.0504 |
| 16 fps renders   |         928 |         928 |            807 |      0.8563 | 0.0496 |
| 24 fps renders   |         919 |         919 |            798 |      0.8563 | 0.0511 |

### AUC, AP, EER, TPR at 5% FPR

| generator   | real_fps   |   n_fake |   n_real |   auc |   auc_ci_lo |   auc_ci_hi |    ap |   eer |   tpr_at_5fpr |   detection_rate_global_thr |   det_ci_lo |   det_ci_hi |
|:------------|:-----------|---------:|---------:|------:|------------:|------------:|------:|------:|--------------:|----------------------------:|------------:|------------:|
| ltx23       | 24         |     1874 |      919 | 0.83  |       0.79  |       0.87  | 0.892 | 0.245 |         0.316 |                       0.317 |       0.242 |       0.411 |
| wan22       | 16         |     1566 |      928 | 0.532 |       0.478 |       0.587 | 0.625 | 0.487 |         0.029 |                       0.026 |       0.014 |       0.038 |
| hunyuan15   | 24         |      989 |      919 | 0.712 |       0.667 |       0.755 | 0.676 | 0.344 |         0.121 |                       0.122 |       0.084 |       0.164 |
| ltx25       | 24         |     2002 |      919 | 0.714 |       0.667 |       0.76  | 0.819 | 0.344 |         0.153 |                       0.153 |       0.105 |       0.203 |
| all         | 24+16      |     6431 |     1847 | 0.705 |       0.669 |       0.739 | 0.879 | 0.348 |         0.165 |                       0.165 |       0.127 |       0.206 |

### Real FPR by perceived subgroup

| attribute   | level              |   n_renders |   n_identities |   fpr |   ci_lo |   ci_hi |
|:------------|:-------------------|------------:|---------------:|------:|--------:|--------:|
| race        | black              |         123 |             59 | 0.016 |   0     |   0.057 |
| race        | east_asian         |         163 |             75 | 0.043 |   0.006 |   0.09  |
| race        | indian             |          46 |             23 | 0.043 |   0     |   0.148 |
| race        | latino             |         115 |             55 | 0.043 |   0     |   0.107 |
| race        | mena               |         120 |             59 | 0.125 |   0.044 |   0.213 |
| race        | southeast_asian    |          70 |             34 | 0     |   0     |   0     |
| race        | white              |        1204 |            523 | 0.05  |   0.034 |   0.069 |
| gender      | f                  |         587 |            266 | 0.043 |   0.022 |   0.066 |
| gender      | m                  |        1254 |            553 | 0.053 |   0.036 |   0.071 |
| age_band    | 18-29              |         594 |            275 | 0.051 |   0.027 |   0.078 |
| age_band    | 30-44              |         626 |            290 | 0.051 |   0.028 |   0.074 |
| age_band    | 45-59              |         300 |            134 | 0.037 |   0.011 |   0.069 |
| age_band    | 60+                |         241 |            112 | 0.05  |   0.013 |   0.095 |
| race_gender | black__f           |          20 |             10 | 0     |   0     |   0     |
| race_gender | black__m           |         103 |             50 | 0.019 |   0     |   0.068 |
| race_gender | east_asian__f      |          76 |             35 | 0.026 |   0     |   0.08  |
| race_gender | east_asian__m      |          87 |             41 | 0.057 |   0     |   0.138 |
| race_gender | indian__f          |          12 |              6 | 0     |   0     |   0     |
| race_gender | indian__m          |          34 |             17 | 0.059 |   0     |   0.19  |
| race_gender | latino__f          |          20 |             10 | 0.15  |   0     |   0.417 |
| race_gender | latino__m          |          95 |             45 | 0.021 |   0     |   0.074 |
| race_gender | mena__f            |          34 |             17 | 0.088 |   0     |   0.233 |
| race_gender | mena__m            |          86 |             42 | 0.14  |   0.043 |   0.25  |
| race_gender | southeast_asian__f |          20 |              9 | 0     |   0     |   0     |
| race_gender | southeast_asian__m |          50 |             25 | 0     |   0     |   0     |
| race_gender | white__f           |         405 |            183 | 0.042 |   0.018 |   0.072 |
| race_gender | white__m           |         799 |            350 | 0.054 |   0.033 |   0.077 |

### Real FPR gap (max - min across levels; non-negative by construction)

| attribute   |   n_levels |   fpr_gap |   ci_lo |   ci_hi | max_level   |   max_fpr | min_level       |   min_fpr |
|:------------|-----------:|----------:|--------:|--------:|:------------|----------:|:----------------|----------:|
| race        |          7 |     0.125 |   0.06  |   0.213 | mena        |     0.125 | southeast_asian |     0     |
| gender      |          2 |     0.01  |   0.001 |   0.038 | m           |     0.053 | f               |     0.043 |
| age_band    |          4 |     0.014 |   0.009 |   0.069 | 30-44       |     0.051 | 45-59           |     0.037 |
| race_gender |         14 |     0.15  |   0.095 |   0.417 | latino__f   |     0.15  | black__f        |     0     |

### Worst-subgroup AUC and AUC gap

| generator   | attribute   |   n_levels | worst_level   |   worst_auc |   worst_ci_lo |   worst_ci_hi | best_level    |   best_auc |   auc_gap |   gap_ci_lo |   gap_ci_hi |
|:------------|:------------|-----------:|:--------------|------------:|--------------:|--------------:|:--------------|-----------:|----------:|------------:|------------:|
| ltx23       | race        |          6 | mena          |       0.746 |         0.652 |         0.831 | east_asian    |      0.896 |     0.15  |       0.075 |       0.256 |
| ltx23       | gender      |          2 | m             |       0.825 |         0.782 |         0.866 | f             |      0.841 |     0.016 |       0.001 |       0.048 |
| ltx23       | age_band    |          4 | 60+           |       0.77  |         0.695 |         0.84  | 30-44         |      0.878 |     0.108 |       0.053 |       0.176 |
| ltx23       | race_gender |          7 | mena__m       |       0.694 |         0.579 |         0.806 | east_asian__m |      0.903 |     0.209 |       0.108 |       0.348 |
| wan22       | race        |          6 | mena          |       0.483 |         0.379 |         0.555 | white         |      0.685 |     0.202 |       0.146 |       0.302 |
| wan22       | gender      |          2 | m             |       0.48  |         0.414 |         0.545 | f             |      0.592 |     0.112 |       0.057 |       0.171 |
| wan22       | age_band    |          4 | 60+           |       0.388 |         0.304 |         0.473 | 30-44         |      0.604 |     0.216 |       0.134 |       0.301 |
| wan22       | race_gender |          7 | mena__m       |       0.361 |         0.235 |         0.488 | white__f      |      0.745 |     0.384 |       0.262 |       0.515 |
| hunyuan15   | race        |          6 | mena          |       0.642 |         0.529 |         0.697 | east_asian    |      0.816 |     0.174 |       0.128 |       0.304 |
| hunyuan15   | gender      |          2 | m             |       0.693 |         0.638 |         0.744 | f             |      0.737 |     0.044 |       0.003 |       0.105 |
| hunyuan15   | age_band    |          4 | 60+           |       0.619 |         0.53  |         0.687 | 18-29         |      0.786 |     0.166 |       0.106 |       0.264 |
| hunyuan15   | race_gender |          7 | mena__m       |       0.549 |         0.416 |         0.668 | white__f      |      0.827 |     0.278 |       0.186 |       0.44  |
| ltx25       | race        |          6 | mena          |       0.637 |         0.539 |         0.699 | east_asian    |      0.818 |     0.18  |       0.123 |       0.294 |
| ltx25       | gender      |          2 | f             |       0.714 |         0.654 |         0.754 | m             |      0.721 |     0.007 |       0.001 |       0.064 |
| ltx25       | age_band    |          4 | 60+           |       0.62  |         0.539 |         0.696 | 30-44         |      0.795 |     0.174 |       0.1   |       0.26  |
| ltx25       | race_gender |          7 | mena__m       |       0.601 |         0.484 |         0.682 | east_asian__m |      0.848 |     0.247 |       0.179 |       0.384 |
| all         | race        |          7 | mena          |       0.632 |         0.511 |         0.681 | east_asian    |      0.796 |     0.164 |       0.124 |       0.303 |
| all         | gender      |          2 | m             |       0.69  |         0.648 |         0.729 | f             |      0.727 |     0.036 |       0.003 |       0.079 |
| all         | age_band    |          4 | 60+           |       0.608 |         0.54  |         0.672 | 30-44         |      0.774 |     0.166 |       0.108 |       0.232 |
| all         | race_gender |         10 | indian__m     |       0.53  |         0.387 |         0.62  | east_asian__m |      0.807 |     0.277 |       0.211 |       0.457 |

### Detection rate at the calibrated threshold

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1874 |      0.317 |   0.242 |   0.411 |
| wan22       | 1566 |      0.026 |   0.014 |   0.038 |
| hunyuan15   |  989 |      0.122 |   0.084 |   0.164 |
| ltx25       | 2002 |      0.153 |   0.105 |   0.203 |
| all         | 6431 |      0.165 |   0.127 |   0.206 |

#### by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 272 |      0.265 |   0.168 |   0.374 |
| ltx23       | east_asian      | 270 |      0.222 |   0.133 |   0.328 |
| ltx23       | indian          | 277 |      0.412 |   0.322 |   0.511 |
| ltx23       | latino          | 262 |      0.344 |   0.258 |   0.447 |
| ltx23       | mena            | 266 |      0.297 |   0.213 |   0.392 |
| ltx23       | southeast_asian | 271 |      0.251 |   0.165 |   0.345 |
| ltx23       | white           | 256 |      0.434 |   0.328 |   0.544 |
| wan22       | black           | 217 |      0     |   0     |   0     |
| wan22       | east_asian      | 226 |      0     |   0     |   0     |
| wan22       | indian          | 230 |      0.017 |   0     |   0.038 |
| wan22       | latino          | 219 |      0.027 |   0.009 |   0.046 |
| wan22       | mena            | 225 |      0.031 |   0.005 |   0.06  |
| wan22       | southeast_asian | 229 |      0     |   0     |   0     |
| wan22       | white           | 220 |      0.105 |   0.048 |   0.17  |
| hunyuan15   | black           | 141 |      0.064 |   0.025 |   0.114 |
| hunyuan15   | east_asian      | 141 |      0.057 |   0.007 |   0.126 |
| hunyuan15   | indian          | 142 |      0.211 |   0.139 |   0.282 |
| hunyuan15   | latino          | 142 |      0.113 |   0.054 |   0.175 |
| hunyuan15   | mena            | 139 |      0.086 |   0.036 |   0.143 |
| hunyuan15   | southeast_asian | 143 |      0.105 |   0.049 |   0.176 |
| hunyuan15   | white           | 141 |      0.22  |   0.153 |   0.295 |
| ltx25       | black           | 287 |      0.136 |   0.073 |   0.202 |
| ltx25       | east_asian      | 286 |      0.087 |   0.038 |   0.139 |
| ltx25       | indian          | 284 |      0.155 |   0.094 |   0.213 |
| ltx25       | latino          | 286 |      0.108 |   0.07  |   0.153 |
| ltx25       | mena            | 286 |      0.196 |   0.129 |   0.269 |
| ltx25       | southeast_asian | 286 |      0.098 |   0.046 |   0.153 |
| ltx25       | white           | 287 |      0.289 |   0.212 |   0.373 |
| all         | black           | 917 |      0.131 |   0.089 |   0.18  |
| all         | east_asian      | 923 |      0.101 |   0.063 |   0.141 |
| all         | indian          | 933 |      0.206 |   0.166 |   0.247 |
| all         | latino          | 909 |      0.157 |   0.122 |   0.196 |
| all         | mena            | 916 |      0.168 |   0.123 |   0.216 |
| all         | southeast_asian | 929 |      0.119 |   0.083 |   0.159 |
| all         | white           | 904 |      0.274 |   0.215 |   0.34  |

#### by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.368 |   0.285 |   0.463 |
| ltx23       | m       |  943 |      0.266 |   0.19  |   0.357 |
| wan22       | f       |  785 |      0.038 |   0.019 |   0.056 |
| wan22       | m       |  781 |      0.013 |   0.005 |   0.024 |
| hunyuan15   | f       |  495 |      0.156 |   0.111 |   0.204 |
| hunyuan15   | m       |  494 |      0.089 |   0.045 |   0.14  |
| ltx25       | f       |  999 |      0.15  |   0.105 |   0.195 |
| ltx25       | m       | 1003 |      0.156 |   0.096 |   0.221 |
| all         | f       | 3210 |      0.187 |   0.147 |   0.231 |
| all         | m       | 3221 |      0.143 |   0.106 |   0.185 |

#### by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  468 |      0.376 |   0.282 |   0.478 |
| ltx23       | 30-44   |  470 |      0.438 |   0.345 |   0.535 |
| ltx23       | 45-59   |  478 |      0.276 |   0.194 |   0.377 |
| ltx23       | 60+     |  458 |      0.175 |   0.101 |   0.265 |
| wan22       | 18-29   |  388 |      0.041 |   0.021 |   0.067 |
| wan22       | 30-44   |  377 |      0.042 |   0.017 |   0.07  |
| wan22       | 45-59   |  398 |      0.013 |   0.003 |   0.023 |
| wan22       | 60+     |  403 |      0.007 |   0     |   0.022 |
| hunyuan15   | 18-29   |  242 |      0.223 |   0.141 |   0.322 |
| hunyuan15   | 30-44   |  248 |      0.214 |   0.15  |   0.286 |
| hunyuan15   | 45-59   |  250 |      0.048 |   0.026 |   0.072 |
| hunyuan15   | 60+     |  249 |      0.008 |   0     |   0.025 |
| ltx25       | 18-29   |  500 |      0.2   |   0.131 |   0.268 |
| ltx25       | 30-44   |  497 |      0.233 |   0.172 |   0.295 |
| ltx25       | 45-59   |  501 |      0.12  |   0.068 |   0.171 |
| ltx25       | 60+     |  504 |      0.06  |   0.024 |   0.097 |
| all         | 18-29   | 1598 |      0.217 |   0.165 |   0.268 |
| all         | 30-44   | 1592 |      0.246 |   0.2   |   0.295 |
| all         | 45-59   | 1627 |      0.128 |   0.091 |   0.171 |
| all         | 60+     | 1614 |      0.071 |   0.042 |   0.106 |

### Detection-rate gap at the calibrated threshold

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level        | min_level       |
|:------------|:-----------------|------:|--------:|--------:|:-----------------|:----------------|
| ltx23       | race             | 0.211 |   0.153 |   0.295 | white            | east_asian      |
| ltx23       | gender           | 0.102 |   0.055 |   0.151 | f                | m               |
| ltx23       | age_band         | 0.264 |   0.19  |   0.337 | 30-44            | 60+             |
| ltx23       | cell             | 0.719 |   0.611 |   0.875 | white__f__30-44  | mena__f__60+    |
| ltx23       | setting          | 0.394 |   0.363 |   0.948 | corridor         | cafe            |
| ltx23       | lighting         | 0.46  |   0.245 |   0.763 | lowlight         | harsh           |
| ltx23       | behavior         | 0.494 |   0.353 |   0.828 | listen           | think           |
| ltx23       | camera           | 0.131 |   0.008 |   0.302 | slowsway         | static          |
| ltx23       | duration_nominal | 0.019 |   0.003 |   0.19  | 6.0              | 5.0             |
| wan22       | race             | 0.105 |   0.048 |   0.17  | white            | black           |
| wan22       | gender           | 0.025 |   0.008 |   0.041 | f                | m               |
| wan22       | age_band         | 0.035 |   0.016 |   0.07  | 30-44            | 60+             |
| wan22       | cell             | 0.296 |   0.16  |   0.482 | white__f__18-29  | black__f__18-29 |
| wan22       | setting          | 0.066 |   0.047 |   0.154 | library          | cafe            |
| wan22       | lighting         | 0.033 |   0.019 |   0.088 | lowlight         | overcast        |
| wan22       | behavior         | 0.057 |   0.042 |   0.111 | laugh            | read            |
| wan22       | camera           | 0.002 |   0     |   0.027 | slowsway         | static          |
| wan22       | duration_nominal | 0.019 |   0.001 |   0.041 | 5.0              | 6.0             |
| hunyuan15   | race             | 0.163 |   0.127 |   0.264 | white            | east_asian      |
| hunyuan15   | gender           | 0.066 |   0.017 |   0.118 | f                | m               |
| hunyuan15   | age_band         | 0.215 |   0.153 |   0.313 | 18-29            | 60+             |
| hunyuan15   | cell             | 0.611 |   0.522 |   0.867 | indian__f__30-44 | black__f__30-44 |
| hunyuan15   | setting          | 0.241 |   0.132 |   0.339 | library          | kitchen         |
| hunyuan15   | lighting         | 0.089 |   0.072 |   0.32  | lowlight         | softwindow      |
| hunyuan15   | behavior         | 0.249 |   0.118 |   0.322 | laugh            | pause           |
| hunyuan15   | camera           | 0.046 |   0.002 |   0.128 | static           | slowsway        |
| hunyuan15   | duration_nominal | 0.047 |   0.003 |   0.126 | 6.0              | 5.0             |
| ltx25       | race             | 0.202 |   0.146 |   0.273 | white            | east_asian      |
| ltx25       | gender           | 0.005 |   0.001 |   0.052 | m                | f               |
| ltx25       | age_band         | 0.174 |   0.123 |   0.229 | 30-44            | 60+             |
| ltx25       | cell             | 0.611 |   0.472 |   0.75  | white__f__30-44  | black__f__45-59 |
| ltx25       | setting          | 0.274 |   0.229 |   0.565 | library          | plainwall       |
| ltx25       | lighting         | 0.219 |   0.128 |   0.409 | lowlight         | overcast        |
| ltx25       | behavior         | 0.395 |   0.265 |   0.539 | laugh            | pause           |
| ltx25       | camera           | 0.059 |   0.002 |   0.159 | slowsway         | static          |
| ltx25       | duration_nominal | 0.015 |   0.002 |   0.118 | 6.0              | 5.0             |
| all         | race             | 0.174 |   0.13  |   0.22  | white            | east_asian      |
| all         | gender           | 0.044 |   0.019 |   0.068 | f                | m               |
| all         | age_band         | 0.174 |   0.141 |   0.209 | 30-44            | 60+             |
| all         | cell             | 0.514 |   0.441 |   0.627 | white__f__30-44  | mena__f__60+    |
| all         | setting          | 0.214 |   0.181 |   0.435 | library          | cafe            |
| all         | lighting         | 0.194 |   0.088 |   0.356 | lowlight         | harsh           |
| all         | behavior         | 0.26  |   0.217 |   0.368 | laugh            | think           |
| all         | camera           | 0.051 |   0.002 |   0.131 | slowsway         | static          |
| all         | duration_nominal | 0.025 |   0.001 |   0.1   | 6.0              | 5.0             |

### Flip rate at the calibrated threshold

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.917 |   0.833 |   1     |        1 |     1 |
| wan22       |         36 |       0.417 |   0.25  |   0.583 |        0 |     1 |
| hunyuan15   |         18 |       0.944 |   0.824 |   1     |        1 |     1 |
| ltx25       |         36 |       0.833 |   0.694 |   0.944 |        1 |     1 |

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

