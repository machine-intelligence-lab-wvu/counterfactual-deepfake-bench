# demamba / native_up_2s: snapshot 20261023-0245

> **Detector training data.** DeMamba weights are our own (GenVideo-100K, single-GPU adaptation of the authors' code), not an official release; the authors have published none. GenVideo-100K contains none of our generators. On GenVideo validation it flags 16.8% of real videos at 0.5.

> **Provisional threshold.** Every detection rate and flip rate below uses the detector's default threshold (0.5; sigmoid(logit) > 0.5 (training metrics and our standalone evaluator)). They will be replaced by the 5%-real-FPR threshold once reals exist (section 6.3).

## Settings

| setting           | value                                                                                  |
|:------------------|:---------------------------------------------------------------------------------------|
| detector          | demamba 1+504611ba                                                                     |
| checkpoint_sha256 | f89897c72b595aa85a524e59083919cebb0b92161d2a694a2cbffbdd8456ce17                       |
| view              | native_up_2s (view_hash f48f13e3eb9c049d)                                              |
| ffmpeg            | ffmpeg version 7.1.1 Copyright (c) 2000-2025 the FFmpeg developers                     |
| batches           | fake_b1, fake_b2, fake_b3, real_all                                                    |
| inclusion set     | primary (technical QC pass AND face QC pass)                                           |
| bootstrap         | 1000 resamples of whole counterfactual groups, seed 20261020, 95% percentile intervals |
| git commit        | 2949de581861-dirty                                                                     |
| created           | 2026-10-23T02:45:39Z                                                                   |

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
| fake_b3  | ltx25       |    2016 |      2002 |       2016 |               0 |               0 |     2016 |              0 |       2002 |
| real_all | real        |    2221 |      2221 |       2221 |               0 |               0 |     2221 |              0 |       2221 |

Reals scored: 4442. Fakes included: 6435 of 11498 scored (0 scoring failures).

## Observations

- LTX 2.3: mean score 0.989 [0.978, 0.996], median 1.000, n = 1878.
- Wan 2.2: mean score 1.000 [1.000, 1.000], median 1.000, n = 1566.
- HunyuanVideo 1.5: mean score 0.999 [0.999, 1.000], median 1.000, n = 989.
- LTX 2.5: mean score 0.984 [0.970, 0.996], median 1.000, n = 2002.
- Provisional detection rate (score >= 0.5), LTX 2.3: 99.4% [98.8, 99.8].
- Provisional detection rate (score >= 0.5), Wan 2.2: 100.0% [100.0, 100.0].
- Provisional detection rate (score >= 0.5), HunyuanVideo 1.5: 100.0% [100.0, 100.0].
- Provisional detection rate (score >= 0.5), LTX 2.5: 99.1% [97.9, 99.9].
- Provisional detection rate (score >= 0.5), all: 99.5% [99.1, 99.9].
- Largest race score gap: LTX 2.5 0.043 [0.013, 0.077] (black 0.999 vs east_asian 0.956).
- Largest gender score gap: LTX 2.5 0.005 [0.000, 0.015] (f 0.986 vs m 0.981).
- Largest age band score gap: LTX 2.5 0.020 [0.005, 0.042] (60+ 0.997 vs 30-44 0.977).
- Largest cell score gap: LTX 2.5 0.090 [0.036, 0.181] (black__m__60+ 1.000 vs east_asian__m__30-44 0.910).
- Largest scene-factor gap (all generators): lighting 0.038 [0.011, 0.066] (softwindow vs lowlight).
- Largest partial eta squared: lighting 0.036, setting 0.027, race 0.023; residual holds 87.2% of total SS.
- CF spread, LTX 2.3: 0.030 [0.013, 0.049] over 36 groups (max 0.214).
- CF spread, Wan 2.2: 0.000 [0.000, 0.000] over 36 groups (max 0.001).
- CF spread, HunyuanVideo 1.5: 0.003 [0.000, 0.007] over 18 groups (max 0.031).
- CF spread, LTX 2.5: 0.032 [0.011, 0.057] over 36 groups (max 0.274).
- Provisional flip rate, LTX 2.3: 16.7% of 36 groups [5.6, 30.6].
- Provisional flip rate, Wan 2.2: 0.0% of 36 groups [0.0, 0.0].
- Provisional flip rate, HunyuanVideo 1.5: 0.0% of 18 groups [0.0, 0.0].
- Provisional flip rate, LTX 2.5: 13.9% of 36 groups [2.8, 25.0].

## 6.1 Fakes only, no threshold

### Mean score by generator

| generator   |    n |   n_groups |   estimate |   ci_lo |   ci_hi |    sd |   median |   q05 |   q95 |
|:------------|-----:|-----------:|-----------:|--------:|--------:|------:|---------:|------:|------:|
| ltx23       | 1878 |         36 |      0.989 |   0.978 |   0.996 | 0.066 |        1 | 0.978 |     1 |
| wan22       | 1566 |         36 |      1     |   1     |   1     | 0.001 |        1 | 0.999 |     1 |
| hunyuan15   |  989 |         18 |      0.999 |   0.999 |   1     | 0.008 |        1 | 0.999 |     1 |
| ltx25       | 2002 |         36 |      0.984 |   0.97  |   0.996 | 0.084 |        1 | 0.955 |     1 |
| all         | 6435 |         36 |      0.991 |   0.984 |   0.997 | 0.059 |        1 | 0.988 |     1 |

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
| ltx25       | black           | 287 |      0.999 |   0.997 |   1     |    1     |
| ltx25       | east_asian      | 286 |      0.956 |   0.921 |   0.988 |    0.999 |
| ltx25       | indian          | 284 |      0.985 |   0.971 |   0.996 |    1     |
| ltx25       | latino          | 286 |      0.988 |   0.973 |   0.999 |    1     |
| ltx25       | mena            | 286 |      0.995 |   0.989 |   0.999 |    1     |
| ltx25       | southeast_asian | 286 |      0.964 |   0.937 |   0.989 |    0.999 |
| ltx25       | white           | 287 |      0.998 |   0.996 |   1     |    1     |
| all         | black           | 918 |      0.999 |   0.999 |   1     |    1     |
| all         | east_asian      | 923 |      0.975 |   0.956 |   0.99  |    1     |
| all         | indian          | 933 |      0.993 |   0.987 |   0.998 |    1     |
| all         | latino          | 909 |      0.995 |   0.99  |   1     |    1     |
| all         | mena            | 917 |      0.996 |   0.993 |   0.999 |    1     |
| all         | southeast_asian | 929 |      0.984 |   0.97  |   0.995 |    1     |
| all         | white           | 906 |      0.998 |   0.996 |   1     |    1     |

### Mean score by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | f       |  931 |      0.987 |   0.976 |   0.996 |        1 |
| ltx23       | m       |  947 |      0.99  |   0.98  |   0.997 |        1 |
| wan22       | f       |  785 |      1     |   1     |   1     |        1 |
| wan22       | m       |  781 |      1     |   1     |   1     |        1 |
| hunyuan15   | f       |  495 |      1     |   1     |   1     |        1 |
| hunyuan15   | m       |  494 |      0.999 |   0.998 |   1     |        1 |
| ltx25       | f       |  999 |      0.986 |   0.97  |   0.998 |        1 |
| ltx25       | m       | 1003 |      0.981 |   0.966 |   0.994 |        1 |
| all         | f       | 3210 |      0.992 |   0.985 |   0.997 |        1 |
| all         | m       | 3225 |      0.991 |   0.984 |   0.997 |        1 |

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
| ltx25       | 18-29   |  500 |      0.978 |   0.959 |   0.995 |        1 |
| ltx25       | 30-44   |  497 |      0.977 |   0.954 |   0.995 |        1 |
| ltx25       | 45-59   |  501 |      0.982 |   0.967 |   0.995 |        1 |
| ltx25       | 60+     |  504 |      0.997 |   0.994 |   0.999 |        1 |
| all         | 18-29   | 1599 |      0.988 |   0.979 |   0.996 |        1 |
| all         | 30-44   | 1593 |      0.988 |   0.977 |   0.997 |        1 |
| all         | 45-59   | 1627 |      0.991 |   0.984 |   0.997 |        1 |
| all         | 60+     | 1616 |      0.998 |   0.997 |   0.999 |        1 |

### Mean score by scene factor (all generators pooled)

| factor           | level      |    n |   estimate |   ci_lo |   ci_hi |
|:-----------------|:-----------|-----:|-----------:|--------:|--------:|
| setting          | cafe       |  593 |      0.99  |   0.981 |   0.996 |
| setting          | classroom  |  541 |      0.999 |   0.999 |   1     |
| setting          | corridor   |  716 |      0.999 |   0.997 |   1     |
| setting          | kitchen    |  605 |      0.975 |   0.906 |   0.999 |
| setting          | library    |  757 |      0.979 |   0.95  |   1     |
| setting          | livingroom |  754 |      1     |   1     |   1     |
| setting          | lobby      |  513 |      0.977 |   0.943 |   1     |
| setting          | office     |  580 |      0.998 |   0.994 |   1     |
| setting          | plainwall  |  777 |      0.996 |   0.984 |   0.999 |
| setting          | studio     |  599 |      0.999 |   0.999 |   1     |
| lighting         | backlit    | 1126 |      0.996 |   0.989 |   1     |
| lighting         | harsh      |  967 |      0.997 |   0.994 |   0.999 |
| lighting         | lowlight   | 1116 |      0.962 |   0.934 |   0.989 |
| lighting         | overcast   | 1022 |      0.997 |   0.992 |   0.999 |
| lighting         | softwindow | 1157 |      0.999 |   0.999 |   1     |
| lighting         | warmlamp   | 1047 |      0.999 |   0.998 |   1     |
| behavior         | laugh      |  723 |      0.996 |   0.986 |   1     |
| behavior         | listen     |  960 |      0.995 |   0.987 |   1     |
| behavior         | pause      |  744 |      0.998 |   0.992 |   0.999 |
| behavior         | read       |  796 |      0.995 |   0.984 |   0.999 |
| behavior         | smile      |  817 |      1     |   1     |   1     |
| behavior         | speak      |  806 |      0.985 |   0.963 |   1     |
| behavior         | think      |  733 |      0.984 |   0.943 |   1     |
| behavior         | turn       |  856 |      0.98  |   0.938 |   0.999 |
| camera           | slowsway   | 3224 |      0.991 |   0.98  |   0.998 |
| camera           | static     | 3211 |      0.992 |   0.983 |   0.999 |
| duration_nominal | 5.0        | 3226 |      0.994 |   0.986 |   0.999 |
| duration_nominal | 6.0        | 3209 |      0.989 |   0.977 |   0.998 |

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
| ltx25       | race             |          7 | 0.043 |   0.013 |   0.077 | black         | east_asian           |
| ltx25       | gender           |          2 | 0.005 |   0     |   0.015 | f             | m                    |
| ltx25       | age_band         |          4 | 0.02  |   0.005 |   0.042 | 60+           | 30-44                |
| ltx25       | cell             |         56 | 0.09  |   0.036 |   0.181 | black__m__60+ | east_asian__m__30-44 |
| ltx25       | setting          |         10 | 0.058 |   0.02  |   0.175 | livingroom    | kitchen              |
| ltx25       | lighting         |          6 | 0.08  |   0.024 |   0.139 | warmlamp      | lowlight             |
| ltx25       | behavior         |          8 | 0.036 |   0.016 |   0.121 | smile         | turn                 |
| ltx25       | camera           |          2 | 0.004 |   0     |   0.03  | static        | slowsway             |
| ltx25       | duration_nominal |          2 | 0.006 |   0.001 |   0.034 | 5.0           | 6.0                  |
| all         | race             |          7 | 0.025 |   0.01  |   0.043 | black         | east_asian           |
| all         | gender           |          2 | 0.001 |   0     |   0.004 | f             | m                    |
| all         | age_band         |          4 | 0.01  |   0.003 |   0.021 | 60+           | 18-29                |
| all         | cell             |         56 | 0.045 |   0.022 |   0.084 | white__m__60+ | east_asian__m__30-44 |
| all         | setting          |         10 | 0.025 |   0.011 |   0.093 | livingroom    | kitchen              |
| all         | lighting         |          6 | 0.038 |   0.011 |   0.066 | softwindow    | lowlight             |
| all         | behavior         |          8 | 0.019 |   0.007 |   0.062 | smile         | turn                 |
| all         | camera           |          2 | 0.001 |   0     |   0.014 | static        | slowsway             |
| all         | duration_nominal |          2 | 0.005 |   0     |   0.018 | 5.0           | 6.0                  |

### CF spread (mean over groups of the std of score across the group's cells)

| generator   |   n_groups |   cf_spread |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.03  |   0.013 |   0.049 |    0.001 | 0.214 |
| wan22       |         36 |       0     |   0     |   0     |    0     | 0.001 |
| hunyuan15   |         18 |       0.003 |   0     |   0.007 |    0     | 0.031 |
| ltx25       |         36 |       0.032 |   0.011 |   0.057 |    0.002 | 0.274 |

### Factor attribution

OLS with every factor as a fixed effect, type-II ANOVA. `ss_share` is the factor's type-II sum of squares over the total sum of squares (type-II shares need not add to 1). Scene factors are constant within a counterfactual group, so their effects are estimated from between-group differences only. The OLS F tests treat clips as independent although clips are clustered in counterfactual groups, so their p values are optimistic; use the group-bootstrap intervals above for inference.

| factor           |   df |    sum_sq | F      | p         | partial_eta2   |   ss_share |
|:-----------------|-----:|----------:|:-------|:----------|:---------------|-----------:|
| race             |    6 |  0.4625   | 25.05  | 1.505e-29 | 0.02296        |  0.02048   |
| gender           |    1 |  0.001568 | 0.5096 | 0.4753    | 7.965e-05      |  6.942e-05 |
| age_band         |    3 |  0.1113   | 12.05  | 7.262e-08 | 0.00562        |  0.004926  |
| setting          |    9 |  0.5404   | 19.52  | 1.228e-32 | 0.02672        |  0.02392   |
| lighting         |    5 |  0.7252   | 47.14  | 5.027e-48 | 0.03553        |  0.03211   |
| behavior         |    7 |  0.351    | 16.3   | 2.057e-21 | 0.01752        |  0.01554   |
| camera           |    1 |  0.06041  | 19.64  | 9.53e-06  | 0.00306        |  0.002675  |
| duration_nominal |    1 |  0.006361 | 2.067  | 0.1505    | 0.000323       |  0.0002816 |
| generator        |    3 |  0.2945   | 31.91  | 1.818e-20 | 0.01474        |  0.01304   |
| Residual         | 6398 | 19.68     |        |           |                |  0.8715    |

Lighting x race interaction (added to the same OLS):

| term            |   df |   sum_sq |   F |         p |   partial_eta2 |
|:----------------|-----:|---------:|----:|----------:|---------------:|
| lighting x race |   30 |    1.054 |  12 | 1.914e-56 |        0.05352 |

Mixed model `score ~ factors + (1 | counterfactual_group)` (REML) variance components (fixed effects: `tables/factor_mixed_fixed.csv`):

| component                               |   variance | converged   |
|:----------------------------------------|-----------:|:------------|
| counterfactual_group (random intercept) |   0        | True        |
| residual                                |   0.003028 | True        |
| ICC (group share of random variance)    |   0        | True        |

A group variance at or near 0 is a boundary estimate: setting, lighting, behavior, camera and duration are fixed per group and absorb most between-group variation, leaving little for the random intercept. It does not mean scenes do not matter.

## 6.2 Provisional (threshold 0.5, provisional)

### Detection rate by generator (provisional)

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1878 |      0.994 |   0.988 |   0.998 |
| wan22       | 1566 |      1     |   1     |   1     |
| hunyuan15   |  989 |      1     |   1     |   1     |
| ltx25       | 2002 |      0.991 |   0.979 |   0.999 |
| all         | 6435 |      0.995 |   0.991 |   0.999 |

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
| ltx25       | black           | 287 |      1     |   1     |   1     |
| ltx25       | east_asian      | 286 |      0.969 |   0.934 |   0.997 |
| ltx25       | indian          | 284 |      0.996 |   0.989 |   1     |
| ltx25       | latino          | 286 |      0.99  |   0.972 |   1     |
| ltx25       | mena            | 286 |      1     |   1     |   1     |
| ltx25       | southeast_asian | 286 |      0.979 |   0.951 |   1     |
| ltx25       | white           | 287 |      1     |   1     |   1     |
| all         | black           | 918 |      1     |   1     |   1     |
| all         | east_asian      | 923 |      0.982 |   0.964 |   0.995 |
| all         | indian          | 933 |      0.998 |   0.995 |   1     |
| all         | latino          | 909 |      0.997 |   0.991 |   1     |
| all         | mena            | 917 |      1     |   1     |   1     |
| all         | southeast_asian | 929 |      0.991 |   0.98  |   1     |
| all         | white           | 906 |      1     |   1     |   1     |

### Detection rate by gender (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.992 |   0.985 |   0.999 |
| ltx23       | m       |  947 |      0.996 |   0.99  |   1     |
| wan22       | f       |  785 |      1     |   1     |   1     |
| wan22       | m       |  781 |      1     |   1     |   1     |
| hunyuan15   | f       |  495 |      1     |   1     |   1     |
| hunyuan15   | m       |  494 |      1     |   1     |   1     |
| ltx25       | f       |  999 |      0.993 |   0.98  |   1     |
| ltx25       | m       | 1003 |      0.988 |   0.975 |   0.998 |
| all         | f       | 3210 |      0.996 |   0.99  |   0.999 |
| all         | m       | 3225 |      0.995 |   0.99  |   0.999 |

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
| ltx25       | 18-29   |  500 |      0.988 |   0.972 |   1     |
| ltx25       | 30-44   |  497 |      0.984 |   0.967 |   0.998 |
| ltx25       | 45-59   |  501 |      0.99  |   0.976 |   1     |
| ltx25       | 60+     |  504 |      1     |   1     |   1     |
| all         | 18-29   | 1599 |      0.994 |   0.987 |   0.999 |
| all         | 30-44   | 1593 |      0.992 |   0.984 |   0.999 |
| all         | 45-59   | 1627 |      0.995 |   0.99  |   0.999 |
| all         | 60+     | 1616 |      1     |   1     |   1     |

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
| ltx25       | race             | 0.031 |   0.007 |   0.066 | black           | east_asian           |
| ltx25       | gender           | 0.005 |   0     |   0.016 | f               | m                    |
| ltx25       | age_band         | 0.016 |   0.004 |   0.033 | 60+             | 30-44                |
| ltx25       | cell             | 0.111 |   0.029 |   0.222 | black__f__18-29 | east_asian__m__30-44 |
| ltx25       | setting          | 0.055 |   0.006 |   0.17  | classroom       | kitchen              |
| ltx25       | lighting         | 0.054 |   0.007 |   0.109 | harsh           | lowlight             |
| ltx25       | behavior         | 0.033 |   0.006 |   0.111 | laugh           | turn                 |
| ltx25       | camera           | 0.003 |   0     |   0.026 | static          | slowsway             |
| ltx25       | duration_nominal | 0.011 |   0     |   0.034 | 5.0             | 6.0                  |
| all         | race             | 0.018 |   0.005 |   0.036 | black           | east_asian           |
| all         | gender           | 0.001 |   0     |   0.003 | f               | m                    |
| all         | age_band         | 0.008 |   0.002 |   0.016 | 60+             | 30-44                |
| all         | cell             | 0.043 |   0.018 |   0.091 | black__f__18-29 | east_asian__m__30-44 |
| all         | setting          | 0.02  |   0.005 |   0.075 | classroom       | kitchen              |
| all         | lighting         | 0.023 |   0.004 |   0.047 | harsh           | lowlight             |
| all         | behavior         | 0.014 |   0.004 |   0.05  | pause           | turn                 |
| all         | camera           | 0.001 |   0     |   0.011 | static          | slowsway             |
| all         | duration_nominal | 0.004 |   0     |   0.015 | 5.0             | 6.0                  |

### Flip rate (provisional): share of groups whose clips get different decisions

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.167 |   0.056 |   0.306 |        0 |     1 |
| wan22       |         36 |       0     |   0     |   0     |        0 |     0 |
| hunyuan15   |         18 |       0     |   0     |   0     |        0 |     0 |
| ltx25       |         36 |       0.139 |   0.028 |   0.25  |        0 |     1 |

### Sensitivity: inclusion set

| set     | generator   |    n |   mean_score |   provisional_detection_rate |
|:--------|:------------|-----:|-------------:|-----------------------------:|
| all     | hunyuan15   | 1008 |        0.999 |                        1     |
| all     | ltx23       | 2016 |        0.98  |                        0.988 |
| all     | ltx25       | 2016 |        0.984 |                        0.991 |
| all     | wan22       | 2016 |        1     |                        1     |
| primary | hunyuan15   |  989 |        0.999 |                        1     |
| primary | ltx23       | 1878 |        0.989 |                        0.994 |
| primary | ltx25       | 2002 |        0.984 |                        0.991 |
| primary | wan22       | 1566 |        1     |                        1     |

## 6.3 Real vs generated (calibrated threshold 0.9998)

The threshold is the score at which 5% of primary real renders (24 and 16 fps pooled) are flagged; one per detector and view, never per subgroup. Each generator is compared with reals rendered at its own fps. Intervals: fakes resample counterfactual groups, reals resample identity clusters (source video). Real labels are perceived (FairFace), not self-reported.

### Calibration

| scope            |   n_renders |   n_sources |   n_identities |   threshold |    fpr |
|:-----------------|------------:|------------:|---------------:|------------:|-------:|
| all real renders |        4442 |        2221 |           1822 |      0.9998 | 0.0502 |
| 16 fps renders   |        2221 |        2221 |           1822 |      0.9998 | 0.05   |
| 24 fps renders   |        2221 |        2221 |           1822 |      0.9998 | 0.0504 |

### AUC, AP, EER, TPR at 5% FPR

| generator   | real_fps   |   n_fake |   n_real |   auc |   auc_ci_lo |   auc_ci_hi |    ap |   eer |   tpr_at_5fpr |   detection_rate_global_thr |   det_ci_lo |   det_ci_hi |
|:------------|:-----------|---------:|---------:|------:|------------:|------------:|------:|------:|--------------:|----------------------------:|------------:|------------:|
| ltx23       | 24         |     1878 |     2221 | 0.897 |       0.864 |       0.928 | 0.862 | 0.185 |         0.531 |                       0.531 |       0.439 |       0.623 |
| wan22       | 16         |     1566 |     2221 | 0.952 |       0.94  |       0.962 | 0.908 | 0.121 |         0.704 |                       0.704 |       0.639 |       0.772 |
| hunyuan15   | 24         |      989 |     2221 | 0.96  |       0.947 |       0.971 | 0.9   | 0.105 |         0.776 |                       0.776 |       0.71  |       0.835 |
| ltx25       | 24         |     2002 |     2221 | 0.872 |       0.835 |       0.906 | 0.83  | 0.211 |         0.431 |                       0.431 |       0.35  |       0.517 |
| all         | 24+16      |     6435 |     4442 | 0.911 |       0.89  |       0.932 | 0.924 | 0.165 |         0.58  |                       0.58  |       0.522 |       0.639 |

### Real FPR by perceived subgroup

| attribute   | level              |   n_renders |   n_identities |   fpr |   ci_lo |   ci_hi |
|:------------|:-------------------|------------:|---------------:|------:|--------:|--------:|
| race        | black              |         378 |            173 | 0.053 |   0.027 |   0.089 |
| race        | east_asian         |         382 |            170 | 0.034 |   0.011 |   0.061 |
| race        | indian             |         112 |             54 | 0.036 |   0     |   0.083 |
| race        | latino             |         254 |            119 | 0.047 |   0.015 |   0.088 |
| race        | mena               |         258 |            124 | 0.023 |   0     |   0.059 |
| race        | southeast_asian    |         184 |             85 | 0.022 |   0     |   0.059 |
| race        | white              |        2836 |           1179 | 0.057 |   0.045 |   0.071 |
| gender      | f                  |        1380 |            605 | 0.083 |   0.062 |   0.106 |
| gender      | m                  |        3024 |           1263 | 0.035 |   0.026 |   0.045 |
| age_band    | 18-29              |        1382 |            625 | 0.075 |   0.053 |   0.098 |
| age_band    | 30-44              |        1518 |            679 | 0.034 |   0.021 |   0.048 |
| age_band    | 45-59              |         644 |            274 | 0.045 |   0.022 |   0.072 |
| age_band    | 60+                |         624 |            268 | 0.042 |   0.021 |   0.063 |
| race_gender | black__f           |          64 |             30 | 0.094 |   0     |   0.216 |
| race_gender | black__m           |         314 |            144 | 0.045 |   0.016 |   0.081 |
| race_gender | east_asian__f      |         138 |             63 | 0.08  |   0.019 |   0.152 |
| race_gender | east_asian__m      |         244 |            110 | 0.008 |   0     |   0.028 |
| race_gender | indian__f          |          32 |             16 | 0.031 |   0     |   0.107 |
| race_gender | indian__m          |          80 |             38 | 0.037 |   0     |   0.098 |
| race_gender | latino__f          |          62 |             30 | 0.065 |   0     |   0.156 |
| race_gender | latino__m          |         192 |             89 | 0.042 |   0.01  |   0.089 |
| race_gender | mena__f            |          60 |             30 | 0.033 |   0     |   0.111 |
| race_gender | mena__m            |         198 |             94 | 0.02  |   0     |   0.063 |
| race_gender | southeast_asian__f |          64 |             30 | 0     |   0     |   0     |
| race_gender | southeast_asian__m |         120 |             56 | 0.033 |   0     |   0.089 |
| race_gender | white__f           |         960 |            425 | 0.094 |   0.068 |   0.123 |
| race_gender | white__m           |        1876 |            789 | 0.038 |   0.026 |   0.051 |

### Real FPR gap (max - min across levels; non-negative by construction)

| attribute   |   n_levels |   fpr_gap |   ci_lo |   ci_hi | max_level   |   max_fpr | min_level          |   min_fpr |
|:------------|-----------:|----------:|--------:|--------:|:------------|----------:|:-------------------|----------:|
| race        |          7 |     0.035 |   0.034 |   0.091 | white       |     0.057 | southeast_asian    |     0.022 |
| gender      |          2 |     0.047 |   0.025 |   0.072 | f           |     0.083 | m                  |     0.035 |
| age_band    |          4 |     0.04  |   0.022 |   0.069 | 18-29       |     0.075 | 30-44              |     0.034 |
| race_gender |         14 |     0.094 |   0.085 |   0.226 | black__f    |     0.094 | southeast_asian__f |     0     |

### Worst-subgroup AUC and AUC gap

| generator   | attribute   |   n_levels | worst_level     |   worst_auc |   worst_ci_lo |   worst_ci_hi | best_level   |   best_auc |   auc_gap |   gap_ci_lo |   gap_ci_hi |
|:------------|:------------|-----------:|:----------------|------------:|--------------:|--------------:|:-------------|-----------:|----------:|------------:|------------:|
| ltx23       | race        |          7 | east_asian      |       0.881 |         0.827 |         0.917 | mena         |      0.957 |     0.076 |       0.045 |       0.125 |
| ltx23       | gender      |          2 | f               |       0.867 |         0.823 |         0.908 | m            |      0.91  |     0.043 |       0.016 |       0.072 |
| ltx23       | age_band    |          4 | 18-29           |       0.852 |         0.81  |         0.896 | 60+          |      0.926 |     0.073 |       0.045 |       0.108 |
| ltx23       | race_gender |         13 | east_asian__f   |       0.848 |         0.77  |         0.901 | white__m     |      0.96  |     0.113 |       0.08  |       0.197 |
| wan22       | race        |          7 | east_asian      |       0.943 |         0.905 |         0.958 | mena         |      0.984 |     0.04  |       0.03  |       0.086 |
| wan22       | gender      |          2 | f               |       0.934 |         0.914 |         0.954 | m            |      0.959 |     0.024 |       0.006 |       0.044 |
| wan22       | age_band    |          4 | 18-29           |       0.917 |         0.893 |         0.939 | 60+          |      0.97  |     0.053 |       0.033 |       0.081 |
| wan22       | race_gender |         13 | east_asian__f   |       0.921 |         0.855 |         0.946 | mena__f      |      0.992 |     0.071 |       0.049 |       0.143 |
| hunyuan15   | race        |          7 | east_asian      |       0.942 |         0.914 |         0.961 | mena         |      0.989 |     0.047 |       0.029 |       0.08  |
| hunyuan15   | gender      |          2 | f               |       0.948 |         0.926 |         0.966 | m            |      0.964 |     0.016 |       0.001 |       0.035 |
| hunyuan15   | age_band    |          4 | 18-29           |       0.917 |         0.891 |         0.943 | 60+          |      0.986 |     0.069 |       0.046 |       0.096 |
| hunyuan15   | race_gender |         13 | east_asian__f   |       0.932 |         0.874 |         0.954 | white__m     |      0.994 |     0.061 |       0.043 |       0.122 |
| ltx25       | race        |          7 | southeast_asian |       0.857 |         0.792 |         0.893 | mena         |      0.948 |     0.092 |       0.06  |       0.155 |
| ltx25       | gender      |          2 | f               |       0.846 |         0.804 |         0.889 | m            |      0.879 |     0.033 |       0.006 |       0.061 |
| ltx25       | age_band    |          4 | 18-29           |       0.812 |         0.764 |         0.856 | 60+          |      0.92  |     0.108 |       0.072 |       0.148 |
| ltx25       | race_gender |         13 | east_asian__f   |       0.841 |         0.747 |         0.874 | mena__f      |      0.955 |     0.115 |       0.096 |       0.219 |
| all         | race        |          7 | east_asian      |       0.899 |         0.855 |         0.924 | mena         |      0.965 |     0.065 |       0.042 |       0.113 |
| all         | gender      |          2 | f               |       0.888 |         0.859 |         0.918 | m            |      0.92  |     0.031 |       0.011 |       0.053 |
| all         | age_band    |          4 | 18-29           |       0.864 |         0.834 |         0.894 | 60+          |      0.944 |     0.08  |       0.054 |       0.109 |
| all         | race_gender |         14 | east_asian__f   |       0.876 |         0.809 |         0.907 | mena__f      |      0.971 |     0.094 |       0.072 |       0.17  |

### Detection rate at the calibrated threshold

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1878 |      0.531 |   0.439 |   0.623 |
| wan22       | 1566 |      0.704 |   0.639 |   0.772 |
| hunyuan15   |  989 |      0.776 |   0.71  |   0.835 |
| ltx25       | 2002 |      0.431 |   0.35  |   0.517 |
| all         | 6435 |      0.58  |   0.522 |   0.639 |

#### by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 273 |      0.612 |   0.511 |   0.712 |
| ltx23       | east_asian      | 270 |      0.248 |   0.165 |   0.348 |
| ltx23       | indian          | 277 |      0.52  |   0.406 |   0.635 |
| ltx23       | latino          | 262 |      0.656 |   0.543 |   0.772 |
| ltx23       | mena            | 267 |      0.618 |   0.51  |   0.721 |
| ltx23       | southeast_asian | 271 |      0.336 |   0.238 |   0.442 |
| ltx23       | white           | 258 |      0.744 |   0.64  |   0.835 |
| wan22       | black           | 217 |      0.714 |   0.624 |   0.817 |
| wan22       | east_asian      | 226 |      0.425 |   0.312 |   0.545 |
| wan22       | indian          | 230 |      0.713 |   0.608 |   0.819 |
| wan22       | latino          | 219 |      0.881 |   0.816 |   0.939 |
| wan22       | mena            | 225 |      0.853 |   0.785 |   0.917 |
| wan22       | southeast_asian | 229 |      0.406 |   0.299 |   0.516 |
| wan22       | white           | 220 |      0.95  |   0.911 |   0.984 |
| hunyuan15   | black           | 141 |      0.787 |   0.682 |   0.889 |
| hunyuan15   | east_asian      | 141 |      0.546 |   0.462 |   0.641 |
| hunyuan15   | indian          | 142 |      0.782 |   0.669 |   0.886 |
| hunyuan15   | latino          | 142 |      0.887 |   0.822 |   0.947 |
| hunyuan15   | mena            | 139 |      0.863 |   0.799 |   0.925 |
| hunyuan15   | southeast_asian | 143 |      0.622 |   0.5   |   0.747 |
| hunyuan15   | white           | 141 |      0.943 |   0.9   |   0.98  |
| ltx25       | black           | 287 |      0.544 |   0.453 |   0.641 |
| ltx25       | east_asian      | 286 |      0.147 |   0.087 |   0.217 |
| ltx25       | indian          | 284 |      0.423 |   0.316 |   0.539 |
| ltx25       | latino          | 286 |      0.5   |   0.393 |   0.608 |
| ltx25       | mena            | 286 |      0.507 |   0.408 |   0.613 |
| ltx25       | southeast_asian | 286 |      0.21  |   0.136 |   0.291 |
| ltx25       | white           | 287 |      0.686 |   0.582 |   0.785 |
| all         | black           | 918 |      0.642 |   0.576 |   0.71  |
| all         | east_asian      | 923 |      0.306 |   0.245 |   0.37  |
| all         | indian          | 933 |      0.578 |   0.508 |   0.654 |
| all         | latino          | 909 |      0.697 |   0.63  |   0.766 |
| all         | mena            | 917 |      0.678 |   0.614 |   0.742 |
| all         | southeast_asian | 929 |      0.358 |   0.295 |   0.431 |
| all         | white           | 906 |      0.807 |   0.754 |   0.858 |

#### by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.553 |   0.45  |   0.659 |
| ltx23       | m       |  947 |      0.51  |   0.419 |   0.602 |
| wan22       | f       |  785 |      0.734 |   0.661 |   0.804 |
| wan22       | m       |  781 |      0.673 |   0.606 |   0.746 |
| hunyuan15   | f       |  495 |      0.792 |   0.705 |   0.87  |
| hunyuan15   | m       |  494 |      0.759 |   0.702 |   0.813 |
| ltx25       | f       |  999 |      0.448 |   0.365 |   0.536 |
| ltx25       | m       | 1003 |      0.414 |   0.328 |   0.499 |
| all         | f       | 3210 |      0.602 |   0.54  |   0.668 |
| all         | m       | 3225 |      0.558 |   0.501 |   0.617 |

#### by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  469 |      0.416 |   0.315 |   0.524 |
| ltx23       | 30-44   |  471 |      0.493 |   0.397 |   0.589 |
| ltx23       | 45-59   |  478 |      0.586 |   0.483 |   0.685 |
| ltx23       | 60+     |  460 |      0.633 |   0.531 |   0.738 |
| wan22       | 18-29   |  388 |      0.595 |   0.5   |   0.687 |
| wan22       | 30-44   |  377 |      0.631 |   0.534 |   0.729 |
| wan22       | 45-59   |  398 |      0.764 |   0.71  |   0.82  |
| wan22       | 60+     |  403 |      0.816 |   0.762 |   0.87  |
| hunyuan15   | 18-29   |  242 |      0.628 |   0.522 |   0.728 |
| hunyuan15   | 30-44   |  248 |      0.657 |   0.564 |   0.749 |
| hunyuan15   | 45-59   |  250 |      0.872 |   0.817 |   0.925 |
| hunyuan15   | 60+     |  249 |      0.94  |   0.874 |   0.991 |
| ltx25       | 18-29   |  500 |      0.284 |   0.2   |   0.369 |
| ltx25       | 30-44   |  497 |      0.36  |   0.278 |   0.45  |
| ltx25       | 45-59   |  501 |      0.465 |   0.375 |   0.553 |
| ltx25       | 60+     |  504 |      0.613 |   0.506 |   0.72  |
| all         | 18-29   | 1599 |      0.45  |   0.385 |   0.522 |
| all         | 30-44   | 1593 |      0.51  |   0.447 |   0.577 |
| all         | 45-59   | 1627 |      0.636 |   0.579 |   0.694 |
| all         | 60+     | 1616 |      0.72  |   0.657 |   0.786 |

### Detection-rate gap at the calibrated threshold

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level     | min_level            |
|:------------|:-----------------|------:|--------:|--------:|:--------------|:---------------------|
| ltx23       | race             | 0.496 |   0.406 |   0.588 | white         | east_asian           |
| ltx23       | gender           | 0.043 |   0.003 |   0.101 | f             | m                    |
| ltx23       | age_band         | 0.217 |   0.143 |   0.303 | 60+           | 18-29                |
| ltx23       | cell             | 0.728 |   0.672 |   0.907 | white__f__60+ | east_asian__m__18-29 |
| ltx23       | setting          | 0.542 |   0.449 |   0.964 | livingroom    | library              |
| ltx23       | lighting         | 0.634 |   0.503 |   0.841 | softwindow    | lowlight             |
| ltx23       | behavior         | 0.481 |   0.342 |   0.848 | smile         | turn                 |
| ltx23       | camera           | 0.12  |   0.006 |   0.297 | static        | slowsway             |
| ltx23       | duration_nominal | 0.081 |   0.005 |   0.274 | 5.0           | 6.0                  |
| wan22       | race             | 0.544 |   0.449 |   0.646 | white         | southeast_asian      |
| wan22       | gender           | 0.06  |   0.01  |   0.108 | f             | m                    |
| wan22       | age_band         | 0.221 |   0.138 |   0.313 | 60+           | 18-29                |
| wan22       | cell             | 0.862 |   0.759 |   0.969 | black__f__60+ | east_asian__m__18-29 |
| wan22       | setting          | 0.382 |   0.32  |   0.606 | studio        | plainwall            |
| wan22       | lighting         | 0.272 |   0.206 |   0.473 | warmlamp      | overcast             |
| wan22       | behavior         | 0.406 |   0.342 |   0.567 | smile         | read                 |
| wan22       | camera           | 0.086 |   0.005 |   0.227 | static        | slowsway             |
| wan22       | duration_nominal | 0.101 |   0.008 |   0.228 | 5.0           | 6.0                  |
| hunyuan15   | race             | 0.397 |   0.316 |   0.479 | white         | east_asian           |
| hunyuan15   | gender           | 0.033 |   0.002 |   0.098 | f             | m                    |
| hunyuan15   | age_band         | 0.312 |   0.232 |   0.409 | 60+           | 18-29                |
| hunyuan15   | cell             | 0.944 |   0.846 |   1     | black__f__60+ | east_asian__m__30-44 |
| hunyuan15   | setting          | 0.252 |   0.164 |   0.445 | studio        | kitchen              |
| hunyuan15   | lighting         | 0.185 |   0.131 |   0.393 | backlit       | lowlight             |
| hunyuan15   | behavior         | 0.26  |   0.2   |   0.445 | laugh         | pause                |
| hunyuan15   | camera           | 0.016 |   0.002 |   0.146 | slowsway      | static               |
| hunyuan15   | duration_nominal | 0.031 |   0.002 |   0.162 | 6.0           | 5.0                  |
| ltx25       | race             | 0.54  |   0.455 |   0.628 | white         | east_asian           |
| ltx25       | gender           | 0.035 |   0.002 |   0.078 | f             | m                    |
| ltx25       | age_band         | 0.329 |   0.25  |   0.409 | 60+           | 18-29                |
| ltx25       | cell             | 0.861 |   0.75  |   0.972 | black__m__60+ | east_asian__m__18-29 |
| ltx25       | setting          | 0.584 |   0.421 |   0.857 | studio        | library              |
| ltx25       | lighting         | 0.435 |   0.239 |   0.684 | warmlamp      | lowlight             |
| ltx25       | behavior         | 0.312 |   0.259 |   0.71  | smile         | turn                 |
| ltx25       | camera           | 0.165 |   0.023 |   0.32  | static        | slowsway             |
| ltx25       | duration_nominal | 0.023 |   0.002 |   0.197 | 5.0           | 6.0                  |
| all         | race             | 0.501 |   0.446 |   0.558 | white         | east_asian           |
| all         | gender           | 0.044 |   0.009 |   0.08  | f             | m                    |
| all         | age_band         | 0.269 |   0.215 |   0.329 | 60+           | 18-29                |
| all         | cell             | 0.795 |   0.742 |   0.878 | black__m__60+ | east_asian__m__18-29 |
| all         | setting          | 0.348 |   0.275 |   0.605 | studio        | library              |
| all         | lighting         | 0.339 |   0.209 |   0.497 | warmlamp      | lowlight             |
| all         | behavior         | 0.336 |   0.265 |   0.544 | smile         | turn                 |
| all         | camera           | 0.106 |   0.011 |   0.223 | static        | slowsway             |
| all         | duration_nominal | 0.058 |   0.003 |   0.175 | 5.0           | 6.0                  |

### Flip rate at the calibrated threshold

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.861 |   0.75  |   0.972 |        1 |     1 |
| wan22       |         36 |       0.889 |   0.778 |   0.972 |        1 |     1 |
| hunyuan15   |         18 |       1     |   1     |   1     |        1 |     1 |
| ltx25       |         36 |       0.972 |   0.917 |   1     |        1 |     1 |

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

