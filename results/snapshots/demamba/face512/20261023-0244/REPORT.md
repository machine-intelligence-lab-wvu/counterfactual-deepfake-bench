# demamba / face512: snapshot 20261023-0244

> **Detector training data.** DeMamba weights are our own (GenVideo-100K, single-GPU adaptation of the authors' code), not an official release; the authors have published none. GenVideo-100K contains none of our generators. On GenVideo validation it flags 16.8% of real videos at 0.5.

> **Provisional threshold.** Every detection rate and flip rate below uses the detector's default threshold (0.5; sigmoid(logit) > 0.5 (training metrics and our standalone evaluator)). They will be replaced by the 5%-real-FPR threshold once reals exist (section 6.3).

## Settings

| setting           | value                                                                                  |
|:------------------|:---------------------------------------------------------------------------------------|
| detector          | demamba 1+504611ba                                                                     |
| checkpoint_sha256 | f89897c72b595aa85a524e59083919cebb0b92161d2a694a2cbffbdd8456ce17                       |
| view              | face512 (view_hash 330ecb1e37e36e82)                                                   |
| ffmpeg            | ffmpeg version 7.1.1 Copyright (c) 2000-2025 the FFmpeg developers                     |
| batches           | fake_b1, fake_b2, fake_b3, real_all                                                    |
| inclusion set     | primary (technical QC pass AND face QC pass)                                           |
| bootstrap         | 1000 resamples of whole counterfactual groups, seed 20261020, 95% percentile intervals |
| git commit        | 2949de581861-dirty                                                                     |
| created           | 2026-10-23T02:44:29Z                                                                   |

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

- LTX 2.3: mean score 0.978 [0.960, 0.992], median 1.000, n = 1874.
- Wan 2.2: mean score 1.000 [1.000, 1.000], median 1.000, n = 1566.
- HunyuanVideo 1.5: mean score 0.999 [0.999, 1.000], median 1.000, n = 989.
- LTX 2.5: mean score 0.983 [0.973, 0.992], median 1.000, n = 2002.
- Provisional detection rate (score >= 0.5), LTX 2.3: 98.7% [97.5, 99.7].
- Provisional detection rate (score >= 0.5), Wan 2.2: 100.0% [100.0, 100.0].
- Provisional detection rate (score >= 0.5), HunyuanVideo 1.5: 100.0% [100.0, 100.0].
- Provisional detection rate (score >= 0.5), LTX 2.5: 99.2% [98.4, 99.8].
- Provisional detection rate (score >= 0.5), all: 99.3% [98.8, 99.8].
- Largest race score gap: LTX 2.3 0.058 [0.024, 0.098] (mena 0.993 vs east_asian 0.935).
- Largest gender score gap: LTX 2.3 0.008 [0.000, 0.026] (m 0.982 vs f 0.974).
- Largest age band score gap: LTX 2.3 0.026 [0.008, 0.049] (60+ 0.994 vs 18-29 0.968).
- Largest cell score gap: LTX 2.3 0.113 [0.050, 0.206] (white__m__60+ 1.000 vs east_asian__f__18-29 0.887).
- Largest scene-factor gap (all generators): lighting 0.040 [0.017, 0.068] (softwindow vs lowlight).
- Largest partial eta squared: race 0.033, lighting 0.028, behavior 0.024; residual holds 86.7% of total SS.
- CF spread, LTX 2.3: 0.042 [0.018, 0.068] over 36 groups (max 0.272).
- CF spread, Wan 2.2: 0.000 [0.000, 0.000] over 36 groups (max 0.003).
- CF spread, HunyuanVideo 1.5: 0.003 [0.001, 0.005] over 18 groups (max 0.020).
- CF spread, LTX 2.5: 0.040 [0.020, 0.061] over 36 groups (max 0.218).
- Provisional flip rate, LTX 2.3: 16.7% of 36 groups [5.6, 30.6].
- Provisional flip rate, Wan 2.2: 0.0% of 36 groups [0.0, 0.0].
- Provisional flip rate, HunyuanVideo 1.5: 0.0% of 18 groups [0.0, 0.0].
- Provisional flip rate, LTX 2.5: 25.0% of 36 groups [11.1, 38.9].

## 6.1 Fakes only, no threshold

### Mean score by generator

| generator   |    n |   n_groups |   estimate |   ci_lo |   ci_hi |    sd |   median |   q05 |   q95 |
|:------------|-----:|-----------:|-----------:|--------:|--------:|------:|---------:|------:|------:|
| ltx23       | 1874 |         36 |      0.978 |   0.96  |   0.992 | 0.1   |        1 | 0.909 |     1 |
| wan22       | 1566 |         36 |      1     |   1     |   1     | 0.001 |        1 | 1     |     1 |
| hunyuan15   |  989 |         18 |      0.999 |   0.999 |   1     | 0.006 |        1 | 0.999 |     1 |
| ltx25       | 2002 |         36 |      0.983 |   0.973 |   0.992 | 0.078 |        1 | 0.932 |     1 |
| all         | 6431 |         36 |      0.988 |   0.98  |   0.995 | 0.07  |        1 | 0.972 |     1 |

### Mean score by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:----------------|----:|-----------:|--------:|--------:|---------:|
| ltx23       | black           | 272 |      0.988 |   0.973 |   0.999 |    1     |
| ltx23       | east_asian      | 270 |      0.935 |   0.889 |   0.973 |    0.999 |
| ltx23       | indian          | 277 |      0.99  |   0.978 |   0.999 |    1     |
| ltx23       | latino          | 262 |      0.992 |   0.984 |   0.999 |    1     |
| ltx23       | mena            | 266 |      0.993 |   0.985 |   0.999 |    1     |
| ltx23       | southeast_asian | 271 |      0.957 |   0.924 |   0.983 |    1     |
| ltx23       | white           | 256 |      0.991 |   0.979 |   0.999 |    1     |
| wan22       | black           | 217 |      1     |   1     |   1     |    1     |
| wan22       | east_asian      | 226 |      1     |   0.999 |   1     |    1     |
| wan22       | indian          | 230 |      1     |   1     |   1     |    1     |
| wan22       | latino          | 219 |      1     |   1     |   1     |    1     |
| wan22       | mena            | 225 |      1     |   1     |   1     |    1     |
| wan22       | southeast_asian | 229 |      1     |   1     |   1     |    1     |
| wan22       | white           | 220 |      1     |   1     |   1     |    1     |
| hunyuan15   | black           | 141 |      1     |   0.999 |   1     |    1     |
| hunyuan15   | east_asian      | 141 |      0.997 |   0.994 |   0.999 |    1     |
| hunyuan15   | indian          | 142 |      1     |   0.999 |   1     |    1     |
| hunyuan15   | latino          | 142 |      1     |   1     |   1     |    1     |
| hunyuan15   | mena            | 139 |      1     |   1     |   1     |    1     |
| hunyuan15   | southeast_asian | 143 |      0.999 |   0.998 |   1     |    1     |
| hunyuan15   | white           | 141 |      1     |   1     |   1     |    1     |
| ltx25       | black           | 287 |      0.998 |   0.997 |   0.999 |    1     |
| ltx25       | east_asian      | 286 |      0.949 |   0.915 |   0.978 |    0.999 |
| ltx25       | indian          | 284 |      0.989 |   0.98  |   0.996 |    1     |
| ltx25       | latino          | 286 |      0.995 |   0.991 |   0.998 |    1     |
| ltx25       | mena            | 286 |      0.992 |   0.984 |   0.997 |    1     |
| ltx25       | southeast_asian | 286 |      0.961 |   0.935 |   0.983 |    0.999 |
| ltx25       | white           | 287 |      0.998 |   0.996 |   1     |    1     |
| all         | black           | 917 |      0.996 |   0.991 |   0.999 |    1     |
| all         | east_asian      | 923 |      0.964 |   0.943 |   0.983 |    1     |
| all         | indian          | 933 |      0.993 |   0.989 |   0.997 |    1     |
| all         | latino          | 909 |      0.996 |   0.993 |   0.999 |    1     |
| all         | mena            | 916 |      0.995 |   0.992 |   0.998 |    1     |
| all         | southeast_asian | 929 |      0.975 |   0.959 |   0.989 |    1     |
| all         | white           | 904 |      0.997 |   0.993 |   0.999 |    1     |

### Mean score by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | f       |  931 |      0.974 |   0.95  |   0.993 |        1 |
| ltx23       | m       |  943 |      0.982 |   0.969 |   0.993 |        1 |
| wan22       | f       |  785 |      1     |   1     |   1     |        1 |
| wan22       | m       |  781 |      1     |   1     |   1     |        1 |
| hunyuan15   | f       |  495 |      0.999 |   0.998 |   1     |        1 |
| hunyuan15   | m       |  494 |      0.999 |   0.999 |   1     |        1 |
| ltx25       | f       |  999 |      0.984 |   0.973 |   0.993 |        1 |
| ltx25       | m       | 1003 |      0.982 |   0.97  |   0.993 |        1 |
| all         | f       | 3210 |      0.987 |   0.978 |   0.995 |        1 |
| all         | m       | 3221 |      0.989 |   0.982 |   0.995 |        1 |

### Mean score by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | 18-29   |  468 |      0.968 |   0.941 |   0.989 |    1     |
| ltx23       | 30-44   |  470 |      0.976 |   0.954 |   0.992 |    1     |
| ltx23       | 45-59   |  478 |      0.974 |   0.954 |   0.991 |    1     |
| ltx23       | 60+     |  458 |      0.994 |   0.99  |   0.997 |    1     |
| wan22       | 18-29   |  388 |      1     |   1     |   1     |    1     |
| wan22       | 30-44   |  377 |      1     |   1     |   1     |    1     |
| wan22       | 45-59   |  398 |      1     |   1     |   1     |    1     |
| wan22       | 60+     |  403 |      1     |   1     |   1     |    1     |
| hunyuan15   | 18-29   |  242 |      0.999 |   0.997 |   1     |    1     |
| hunyuan15   | 30-44   |  248 |      0.999 |   0.997 |   1     |    1     |
| hunyuan15   | 45-59   |  250 |      1     |   1     |   1     |    1     |
| hunyuan15   | 60+     |  249 |      1     |   1     |   1     |    1     |
| ltx25       | 18-29   |  500 |      0.978 |   0.965 |   0.99  |    0.999 |
| ltx25       | 30-44   |  497 |      0.978 |   0.961 |   0.991 |    1     |
| ltx25       | 45-59   |  501 |      0.985 |   0.97  |   0.995 |    1     |
| ltx25       | 60+     |  504 |      0.991 |   0.981 |   0.998 |    1     |
| all         | 18-29   | 1598 |      0.984 |   0.972 |   0.993 |    1     |
| all         | 30-44   | 1592 |      0.986 |   0.976 |   0.994 |    1     |
| all         | 45-59   | 1627 |      0.988 |   0.979 |   0.995 |    1     |
| all         | 60+     | 1614 |      0.995 |   0.992 |   0.998 |    1     |

### Mean score by scene factor (all generators pooled)

| factor           | level      |    n |   estimate |   ci_lo |   ci_hi |
|:-----------------|:-----------|-----:|-----------:|--------:|--------:|
| setting          | cafe       |  592 |      0.992 |   0.978 |   0.999 |
| setting          | classroom  |  541 |      0.999 |   0.997 |   1     |
| setting          | corridor   |  716 |      0.994 |   0.982 |   1     |
| setting          | kitchen    |  605 |      0.97  |   0.901 |   0.999 |
| setting          | library    |  755 |      0.975 |   0.96  |   0.998 |
| setting          | livingroom |  754 |      0.999 |   0.998 |   1     |
| setting          | lobby      |  513 |      0.971 |   0.932 |   1     |
| setting          | office     |  580 |      0.982 |   0.939 |   1     |
| setting          | plainwall  |  777 |      0.995 |   0.984 |   1     |
| setting          | studio     |  598 |      1     |   0.999 |   1     |
| lighting         | backlit    | 1122 |      0.992 |   0.981 |   0.999 |
| lighting         | harsh      |  967 |      0.987 |   0.963 |   0.999 |
| lighting         | lowlight   | 1116 |      0.958 |   0.931 |   0.983 |
| lighting         | overcast   | 1022 |      0.995 |   0.988 |   0.999 |
| lighting         | softwindow | 1157 |      0.999 |   0.997 |   1     |
| lighting         | warmlamp   | 1047 |      0.998 |   0.996 |   1     |
| behavior         | laugh      |  721 |      0.99  |   0.97  |   1     |
| behavior         | listen     |  959 |      0.991 |   0.978 |   1     |
| behavior         | pause      |  744 |      0.998 |   0.996 |   1     |
| behavior         | read       |  796 |      0.994 |   0.984 |   1     |
| behavior         | smile      |  817 |      1     |   0.999 |   1     |
| behavior         | speak      |  806 |      0.989 |   0.973 |   0.999 |
| behavior         | think      |  732 |      0.98  |   0.932 |   1     |
| behavior         | turn       |  856 |      0.963 |   0.921 |   0.994 |
| camera           | slowsway   | 3223 |      0.984 |   0.972 |   0.994 |
| camera           | static     | 3208 |      0.992 |   0.983 |   0.999 |
| duration_nominal | 5.0        | 3225 |      0.993 |   0.986 |   0.998 |
| duration_nominal | 6.0        | 3206 |      0.983 |   0.968 |   0.995 |

Per-generator scene-factor and 56-cell rows: `tables/score_by_breakdown.csv`.

### Subgroup gap (max - min of level means)

A gap is max - min, so it is never negative and its interval cannot include 0; it is a size, not a test of a difference. Over many levels with few clips each (56 cells; HunyuanVideo has 9 groups per cell) the gap also grows with noise, so compare it with the per-level intervals in `tables/score_by_breakdown.csv`. Levels seen in a single counterfactual group have no interval.

| generator   | attribute        |   n_levels |   gap |   ci_lo |   ci_hi | max_level       | min_level            |
|:------------|:-----------------|-----------:|------:|--------:|--------:|:----------------|:---------------------|
| ltx23       | race             |          7 | 0.058 |   0.024 |   0.098 | mena            | east_asian           |
| ltx23       | gender           |          2 | 0.008 |   0     |   0.026 | m               | f                    |
| ltx23       | age_band         |          4 | 0.026 |   0.008 |   0.049 | 60+             | 18-29                |
| ltx23       | cell             |         56 | 0.113 |   0.05  |   0.206 | white__m__60+   | east_asian__f__18-29 |
| ltx23       | setting          |         10 | 0.063 |   0.034 |   0.176 | classroom       | lobby                |
| ltx23       | lighting         |          6 | 0.085 |   0.033 |   0.146 | softwindow      | lowlight             |
| ltx23       | behavior         |          8 | 0.072 |   0.033 |   0.176 | smile           | turn                 |
| ltx23       | camera           |          2 | 0.015 |   0.001 |   0.045 | static          | slowsway             |
| ltx23       | duration_nominal |          2 | 0.019 |   0.001 |   0.049 | 5.0             | 6.0                  |
| wan22       | race             |          7 | 0     |   0     |   0.001 | white           | east_asian           |
| wan22       | gender           |          2 | 0     |   0     |   0     | m               | f                    |
| wan22       | age_band         |          4 | 0     |   0     |   0     | 60+             | 18-29                |
| wan22       | cell             |         56 | 0.001 |   0     |   0.002 | white__f__60+   | east_asian__f__30-44 |
| wan22       | setting          |         10 | 0     |   0     |   0.001 | studio          | classroom            |
| wan22       | lighting         |          6 | 0     |   0     |   0.001 | warmlamp        | overcast             |
| wan22       | behavior         |          8 | 0     |   0     |   0.001 | smile           | turn                 |
| wan22       | camera           |          2 | 0     |   0     |   0     | slowsway        | static               |
| wan22       | duration_nominal |          2 | 0     |   0     |   0     | 5.0             | 6.0                  |
| hunyuan15   | race             |          7 | 0.003 |   0.001 |   0.006 | white           | east_asian           |
| hunyuan15   | gender           |          2 | 0     |   0     |   0.001 | m               | f                    |
| hunyuan15   | age_band         |          4 | 0.001 |   0     |   0.003 | 45-59           | 18-29                |
| hunyuan15   | cell             |         56 | 0.011 |   0.002 |   0.025 | white__m__30-44 | east_asian__f__18-29 |
| hunyuan15   | setting          |         10 | 0.003 |   0.001 |   0.006 | lobby           | office               |
| hunyuan15   | lighting         |          6 | 0.002 |   0     |   0.006 | backlit         | harsh                |
| hunyuan15   | behavior         |          8 | 0.003 |   0.001 |   0.006 | smile           | turn                 |
| hunyuan15   | camera           |          2 | 0.001 |   0     |   0.002 | static          | slowsway             |
| hunyuan15   | duration_nominal |          2 | 0     |   0     |   0.001 | 5.0             | 6.0                  |
| ltx25       | race             |          7 | 0.05  |   0.021 |   0.082 | black           | east_asian           |
| ltx25       | gender           |          2 | 0.002 |   0     |   0.011 | f               | m                    |
| ltx25       | age_band         |          4 | 0.013 |   0.004 |   0.031 | 60+             | 30-44                |
| ltx25       | cell             |         56 | 0.095 |   0.053 |   0.163 | black__m__60+   | east_asian__m__18-29 |
| ltx25       | setting          |         10 | 0.045 |   0.024 |   0.124 | livingroom      | kitchen              |
| ltx25       | lighting         |          6 | 0.056 |   0.023 |   0.095 | warmlamp        | lowlight             |
| ltx25       | behavior         |          8 | 0.039 |   0.021 |   0.091 | smile           | turn                 |
| ltx25       | camera           |          2 | 0.012 |   0.001 |   0.031 | static          | slowsway             |
| ltx25       | duration_nominal |          2 | 0.01  |   0     |   0.031 | 5.0             | 6.0                  |
| all         | race             |          7 | 0.032 |   0.015 |   0.051 | white           | east_asian           |
| all         | gender           |          2 | 0.002 |   0     |   0.007 | m               | f                    |
| all         | age_band         |          4 | 0.012 |   0.004 |   0.023 | 60+             | 18-29                |
| all         | cell             |         56 | 0.052 |   0.029 |   0.085 | white__f__60+   | east_asian__m__18-29 |
| all         | setting          |         10 | 0.029 |   0.019 |   0.099 | studio          | kitchen              |
| all         | lighting         |          6 | 0.04  |   0.017 |   0.068 | softwindow      | lowlight             |
| all         | behavior         |          8 | 0.036 |   0.016 |   0.079 | smile           | turn                 |
| all         | camera           |          2 | 0.008 |   0     |   0.022 | static          | slowsway             |
| all         | duration_nominal |          2 | 0.009 |   0     |   0.024 | 5.0             | 6.0                  |

### CF spread (mean over groups of the std of score across the group's cells)

| generator   |   n_groups |   cf_spread |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.042 |   0.018 |   0.068 |    0.002 | 0.272 |
| wan22       |         36 |       0     |   0     |   0     |    0     | 0.003 |
| hunyuan15   |         18 |       0.003 |   0.001 |   0.005 |    0     | 0.02  |
| ltx25       |         36 |       0.04  |   0.02  |   0.061 |    0.009 | 0.218 |

### Factor attribution

OLS with every factor as a fixed effect, type-II ANOVA. `ss_share` is the factor's type-II sum of squares over the total sum of squares (type-II shares need not add to 1). Scene factors are constant within a counterfactual group, so their effects are estimated from between-group differences only. The OLS F tests treat clips as independent although clips are clustered in counterfactual groups, so their p values are optimistic; use the group-bootstrap intervals above for inference.

| factor           |   df |    sum_sq | F      | p         | partial_eta2   |   ss_share |
|:-----------------|-----:|----------:|:-------|:----------|:---------------|-----------:|
| race             |    6 |  0.9371   | 36.19  | 2.393e-43 | 0.03285        |  0.02944   |
| gender           |    1 |  0.00406  | 0.9408 | 0.3321    | 0.0001471      |  0.0001276 |
| age_band         |    3 |  0.1254   | 9.685  | 2.247e-06 | 0.004524       |  0.00394   |
| setting          |    9 |  0.5778   | 14.88  | 3.464e-24 | 0.02051        |  0.01816   |
| lighting         |    5 |  0.7878   | 36.51  | 5.209e-37 | 0.02776        |  0.02475   |
| behavior         |    7 |  0.6831   | 22.61  | 1.809e-30 | 0.02416        |  0.02146   |
| camera           |    1 |  0.01396  | 3.236  | 0.07209   | 0.0005058      |  0.0004387 |
| duration_nominal |    1 |  0.001488 | 0.3449 | 0.557     | 5.394e-05      |  4.676e-05 |
| generator        |    3 |  0.509    | 39.32  | 3.625e-25 | 0.01811        |  0.01599   |
| Residual         | 6394 | 27.59     |        |           |                |  0.8669    |

Lighting x race interaction (added to the same OLS):

| term            |   df |   sum_sq |     F |         p |   partial_eta2 |
|:----------------|-----:|---------:|------:|----------:|---------------:|
| lighting x race |   30 |    1.373 | 11.11 | 2.422e-51 |        0.04975 |

Mixed model `score ~ factors + (1 | counterfactual_group)` (REML) variance components (fixed effects: `tables/factor_mixed_fixed.csv`):

| component                               |   variance | converged   |
|:----------------------------------------|-----------:|:------------|
| counterfactual_group (random intercept) |   0        | True        |
| residual                                |   0.004233 | True        |
| ICC (group share of random variance)    |   0        | True        |

A group variance at or near 0 is a boundary estimate: setting, lighting, behavior, camera and duration are fixed per group and absorb most between-group variation, leaving little for the random intercept. It does not mean scenes do not matter.

## 6.2 Provisional (threshold 0.5, provisional)

### Detection rate by generator (provisional)

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1874 |      0.987 |   0.975 |   0.997 |
| wan22       | 1566 |      1     |   1     |   1     |
| hunyuan15   |  989 |      1     |   1     |   1     |
| ltx25       | 2002 |      0.992 |   0.984 |   0.998 |
| all         | 6431 |      0.993 |   0.988 |   0.998 |

### Detection rate by race (provisional)

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 272 |      0.993 |   0.982 |   1     |
| ltx23       | east_asian      | 270 |      0.952 |   0.906 |   0.989 |
| ltx23       | indian          | 277 |      1     |   1     |   1     |
| ltx23       | latino          | 262 |      1     |   1     |   1     |
| ltx23       | mena            | 266 |      1     |   1     |   1     |
| ltx23       | southeast_asian | 271 |      0.97  |   0.944 |   0.993 |
| ltx23       | white           | 256 |      0.992 |   0.981 |   1     |
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
| ltx25       | east_asian      | 286 |      0.965 |   0.93  |   0.993 |
| ltx25       | indian          | 284 |      1     |   1     |   1     |
| ltx25       | latino          | 286 |      1     |   1     |   1     |
| ltx25       | mena            | 286 |      1     |   1     |   1     |
| ltx25       | southeast_asian | 286 |      0.976 |   0.951 |   0.993 |
| ltx25       | white           | 287 |      1     |   1     |   1     |
| all         | black           | 917 |      0.998 |   0.994 |   1     |
| all         | east_asian      | 923 |      0.975 |   0.954 |   0.992 |
| all         | indian          | 933 |      1     |   1     |   1     |
| all         | latino          | 909 |      1     |   1     |   1     |
| all         | mena            | 916 |      1     |   1     |   1     |
| all         | southeast_asian | 929 |      0.984 |   0.969 |   0.996 |
| all         | white           | 904 |      0.998 |   0.994 |   1     |

### Detection rate by gender (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.984 |   0.966 |   0.998 |
| ltx23       | m       |  943 |      0.989 |   0.979 |   0.998 |
| wan22       | f       |  785 |      1     |   1     |   1     |
| wan22       | m       |  781 |      1     |   1     |   1     |
| hunyuan15   | f       |  495 |      1     |   1     |   1     |
| hunyuan15   | m       |  494 |      1     |   1     |   1     |
| ltx25       | f       |  999 |      0.992 |   0.984 |   0.998 |
| ltx25       | m       | 1003 |      0.991 |   0.981 |   0.999 |
| all         | f       | 3210 |      0.993 |   0.987 |   0.998 |
| all         | m       | 3221 |      0.994 |   0.989 |   0.998 |

### Detection rate by age band (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  468 |      0.976 |   0.953 |   0.996 |
| ltx23       | 30-44   |  470 |      0.989 |   0.975 |   1     |
| ltx23       | 45-59   |  478 |      0.983 |   0.968 |   0.996 |
| ltx23       | 60+     |  458 |      0.998 |   0.993 |   1     |
| wan22       | 18-29   |  388 |      1     |   1     |   1     |
| wan22       | 30-44   |  377 |      1     |   1     |   1     |
| wan22       | 45-59   |  398 |      1     |   1     |   1     |
| wan22       | 60+     |  403 |      1     |   1     |   1     |
| hunyuan15   | 18-29   |  242 |      1     |   1     |   1     |
| hunyuan15   | 30-44   |  248 |      1     |   1     |   1     |
| hunyuan15   | 45-59   |  250 |      1     |   1     |   1     |
| hunyuan15   | 60+     |  249 |      1     |   1     |   1     |
| ltx25       | 18-29   |  500 |      0.992 |   0.982 |   1     |
| ltx25       | 30-44   |  497 |      0.986 |   0.972 |   0.996 |
| ltx25       | 45-59   |  501 |      0.992 |   0.978 |   1     |
| ltx25       | 60+     |  504 |      0.996 |   0.99  |   1     |
| all         | 18-29   | 1598 |      0.991 |   0.981 |   0.998 |
| all         | 30-44   | 1592 |      0.992 |   0.985 |   0.998 |
| all         | 45-59   | 1627 |      0.993 |   0.985 |   0.999 |
| all         | 60+     | 1614 |      0.998 |   0.996 |   1     |

### Detection-rate gap (provisional)

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level       | min_level            |
|:------------|:-----------------|------:|--------:|--------:|:----------------|:---------------------|
| ltx23       | race             | 0.048 |   0.012 |   0.094 | indian          | east_asian           |
| ltx23       | gender           | 0.006 |   0     |   0.021 | m               | f                    |
| ltx23       | age_band         | 0.021 |   0.006 |   0.045 | 60+             | 18-29                |
| ltx23       | cell             | 0.094 |   0.033 |   0.219 | black__f__30-44 | east_asian__f__18-29 |
| ltx23       | setting          | 0.042 |   0.022 |   0.109 | cafe            | kitchen              |
| ltx23       | lighting         | 0.059 |   0.022 |   0.1   | backlit         | lowlight             |
| ltx23       | behavior         | 0.04  |   0.018 |   0.109 | listen          | turn                 |
| ltx23       | camera           | 0.009 |   0     |   0.03  | static          | slowsway             |
| ltx23       | duration_nominal | 0.008 |   0     |   0.029 | 5.0             | 6.0                  |
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
| ltx25       | race             | 0.035 |   0.011 |   0.07  | black           | east_asian           |
| ltx25       | gender           | 0.001 |   0     |   0.011 | f               | m                    |
| ltx25       | age_band         | 0.01  |   0.002 |   0.025 | 60+             | 30-44                |
| ltx25       | cell             | 0.083 |   0.056 |   0.194 | black__f__18-29 | east_asian__m__30-44 |
| ltx25       | setting          | 0.037 |   0.011 |   0.113 | classroom       | kitchen              |
| ltx25       | lighting         | 0.039 |   0.011 |   0.074 | softwindow      | lowlight             |
| ltx25       | behavior         | 0.029 |   0.009 |   0.08  | pause           | turn                 |
| ltx25       | camera           | 0.007 |   0     |   0.022 | static          | slowsway             |
| ltx25       | duration_nominal | 0.011 |   0.001 |   0.027 | 5.0             | 6.0                  |
| all         | race             | 0.025 |   0.008 |   0.046 | indian          | east_asian           |
| all         | gender           | 0.001 |   0     |   0.006 | m               | f                    |
| all         | age_band         | 0.008 |   0.002 |   0.017 | 60+             | 18-29                |
| all         | cell             | 0.035 |   0.018 |   0.091 | black__f__30-44 | east_asian__f__30-44 |
| all         | setting          | 0.021 |   0.01  |   0.075 | classroom       | kitchen              |
| all         | lighting         | 0.029 |   0.01  |   0.053 | softwindow      | lowlight             |
| all         | behavior         | 0.022 |   0.008 |   0.055 | pause           | turn                 |
| all         | camera           | 0.005 |   0     |   0.015 | static          | slowsway             |
| all         | duration_nominal | 0.006 |   0     |   0.017 | 5.0             | 6.0                  |

### Flip rate (provisional): share of groups whose clips get different decisions

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.167 |   0.056 |   0.306 |        0 |     1 |
| wan22       |         36 |       0     |   0     |   0     |        0 |     0 |
| hunyuan15   |         18 |       0     |   0     |   0     |        0 |     0 |
| ltx25       |         36 |       0.25  |   0.111 |   0.389 |        0 |     1 |

### Sensitivity: inclusion set

| set     | generator   |    n |   mean_score |   provisional_detection_rate |
|:--------|:------------|-----:|-------------:|-----------------------------:|
| all     | hunyuan15   | 1008 |        0.999 |                        1     |
| all     | ltx23       | 2012 |        0.979 |                        0.988 |
| all     | ltx25       | 2016 |        0.983 |                        0.992 |
| all     | wan22       | 2016 |        1     |                        1     |
| primary | hunyuan15   |  989 |        0.999 |                        1     |
| primary | ltx23       | 1874 |        0.978 |                        0.987 |
| primary | ltx25       | 2002 |        0.983 |                        0.992 |
| primary | wan22       | 1566 |        1     |                        1     |

## 6.3 Real vs generated (calibrated threshold 0.9998)

The threshold is the score at which 5% of primary real renders (24 and 16 fps pooled) are flagged; one per detector and view, never per subgroup. Each generator is compared with reals rendered at its own fps. Intervals: fakes resample counterfactual groups, reals resample identity clusters (source video). Real labels are perceived (FairFace), not self-reported.

### Calibration

| scope            |   n_renders |   n_sources |   n_identities |   threshold |    fpr |
|:-----------------|------------:|------------:|---------------:|------------:|-------:|
| all real renders |        1847 |         928 |            807 |      0.9998 | 0.0504 |
| 16 fps renders   |         928 |         928 |            807 |      0.9998 | 0.0528 |
| 24 fps renders   |         919 |         919 |            798 |      0.9998 | 0.0479 |

### AUC, AP, EER, TPR at 5% FPR

| generator   | real_fps   |   n_fake |   n_real |   auc |   auc_ci_lo |   auc_ci_hi |    ap |   eer |   tpr_at_5fpr |   detection_rate_global_thr |   det_ci_lo |   det_ci_hi |
|:------------|:-----------|---------:|---------:|------:|------------:|------------:|------:|------:|--------------:|----------------------------:|------------:|------------:|
| ltx23       | 24         |     1874 |      919 | 0.884 |       0.839 |       0.924 | 0.938 | 0.202 |         0.553 |                       0.543 |       0.434 |       0.653 |
| wan22       | 16         |     1566 |      928 | 0.984 |       0.978 |       0.99  | 0.989 | 0.061 |         0.914 |                       0.922 |       0.891 |       0.95  |
| hunyuan15   | 24         |      989 |      919 | 0.968 |       0.954 |       0.981 | 0.97  | 0.101 |         0.825 |                       0.821 |       0.746 |       0.886 |
| ltx25       | 24         |     2002 |      919 | 0.867 |       0.829 |       0.906 | 0.927 | 0.224 |         0.451 |                       0.44  |       0.342 |       0.541 |
| all         | 24+16      |     6431 |     1847 | 0.913 |       0.888 |       0.938 | 0.972 | 0.176 |         0.646 |                       0.646 |       0.581 |       0.713 |

### Real FPR by perceived subgroup

| attribute   | level              |   n_renders |   n_identities |   fpr |   ci_lo |   ci_hi |
|:------------|:-------------------|------------:|---------------:|------:|--------:|--------:|
| race        | black              |         123 |             59 | 0.049 |   0     |   0.103 |
| race        | east_asian         |         163 |             75 | 0.018 |   0     |   0.048 |
| race        | indian             |          46 |             23 | 0.043 |   0     |   0.154 |
| race        | latino             |         115 |             55 | 0.061 |   0.009 |   0.133 |
| race        | mena               |         120 |             59 | 0.025 |   0     |   0.068 |
| race        | southeast_asian    |          70 |             34 | 0.043 |   0     |   0.117 |
| race        | white              |        1204 |            523 | 0.057 |   0.039 |   0.077 |
| gender      | f                  |         587 |            266 | 0.063 |   0.037 |   0.092 |
| gender      | m                  |        1254 |            553 | 0.045 |   0.029 |   0.061 |
| age_band    | 18-29              |         594 |            275 | 0.052 |   0.028 |   0.077 |
| age_band    | 30-44              |         626 |            290 | 0.056 |   0.031 |   0.08  |
| age_band    | 45-59              |         300 |            134 | 0.047 |   0.018 |   0.083 |
| age_band    | 60+                |         241 |            112 | 0.046 |   0.016 |   0.086 |
| race_gender | black__f           |          20 |             10 | 0     |   0     |   0     |
| race_gender | black__m           |         103 |             50 | 0.058 |   0     |   0.124 |
| race_gender | east_asian__f      |          76 |             35 | 0.039 |   0     |   0.106 |
| race_gender | east_asian__m      |          87 |             41 | 0     |   0     |   0     |
| race_gender | indian__f          |          12 |              6 | 0     |   0     |   0     |
| race_gender | indian__m          |          34 |             17 | 0.059 |   0     |   0.214 |
| race_gender | latino__f          |          20 |             10 | 0     |   0     |   0     |
| race_gender | latino__m          |          95 |             45 | 0.074 |   0.012 |   0.158 |
| race_gender | mena__f            |          34 |             17 | 0.029 |   0     |   0.1   |
| race_gender | mena__m            |          86 |             42 | 0.023 |   0     |   0.078 |
| race_gender | southeast_asian__f |          20 |              9 | 0.15  |   0     |   0.423 |
| race_gender | southeast_asian__m |          50 |             25 | 0     |   0     |   0     |
| race_gender | white__f           |         405 |            183 | 0.074 |   0.039 |   0.111 |
| race_gender | white__m           |         799 |            350 | 0.049 |   0.029 |   0.07  |

### Real FPR gap (max - min across levels; non-negative by construction)

| attribute   |   n_levels |   fpr_gap |   ci_lo |   ci_hi | max_level          |   max_fpr | min_level   |   min_fpr |
|:------------|-----------:|----------:|--------:|--------:|:-------------------|----------:|:------------|----------:|
| race        |          7 |     0.042 |   0.041 |   0.155 | latino             |     0.061 | east_asian  |     0.018 |
| gender      |          2 |     0.018 |   0.001 |   0.05  | f                  |     0.063 | m           |     0.045 |
| age_band    |          4 |     0.01  |   0.011 |   0.063 | 30-44              |     0.056 | 60+         |     0.046 |
| race_gender |         14 |     0.15  |   0.076 |   0.429 | southeast_asian__f |     0.15  | black__f    |     0     |

### Worst-subgroup AUC and AUC gap

| generator   | attribute   |   n_levels | worst_level     |   worst_auc |   worst_ci_lo |   worst_ci_hi | best_level   |   best_auc |   auc_gap |   gap_ci_lo |   gap_ci_hi |
|:------------|:------------|-----------:|:----------------|------------:|--------------:|--------------:|:-------------|-----------:|----------:|------------:|------------:|
| ltx23       | race        |          6 | southeast_asian |       0.846 |         0.758 |         0.91  | mena         |      0.946 |     0.1   |       0.05  |       0.19  |
| ltx23       | gender      |          2 | f               |       0.859 |         0.801 |         0.912 | m            |      0.898 |     0.039 |       0.005 |       0.078 |
| ltx23       | age_band    |          4 | 18-29           |       0.853 |         0.798 |         0.904 | 60+          |      0.897 |     0.044 |       0.021 |       0.093 |
| ltx23       | race_gender |          7 | east_asian__f   |       0.845 |         0.744 |         0.913 | mena__m      |      0.957 |     0.112 |       0.056 |       0.216 |
| wan22       | race        |          6 | black           |       0.981 |         0.948 |         0.988 | latino       |      0.998 |     0.017 |       0.011 |       0.049 |
| wan22       | gender      |          2 | f               |       0.979 |         0.967 |         0.988 | m            |      0.987 |     0.008 |       0     |       0.019 |
| wan22       | age_band    |          4 | 18-29           |       0.97  |         0.953 |         0.983 | 45-59        |      0.992 |     0.022 |       0.01  |       0.041 |
| wan22       | race_gender |          7 | east_asian__f   |       0.975 |         0.933 |         0.989 | latino__m    |      0.999 |     0.025 |       0.011 |       0.067 |
| hunyuan15   | race        |          6 | east_asian      |       0.959 |         0.917 |         0.978 | white        |      0.989 |     0.03  |       0.017 |       0.076 |
| hunyuan15   | gender      |          2 | f               |       0.955 |         0.929 |         0.977 | m            |      0.976 |     0.021 |       0.004 |       0.042 |
| hunyuan15   | age_band    |          4 | 18-29           |       0.939 |         0.908 |         0.965 | 45-59        |      0.988 |     0.049 |       0.025 |       0.081 |
| hunyuan15   | race_gender |          7 | east_asian__f   |       0.942 |         0.881 |         0.977 | white__m     |      0.997 |     0.055 |       0.022 |       0.118 |
| ltx25       | race        |          6 | southeast_asian |       0.831 |         0.735 |         0.895 | black        |      0.931 |     0.1   |       0.059 |       0.206 |
| ltx25       | gender      |          2 | f               |       0.844 |         0.794 |         0.89  | m            |      0.878 |     0.033 |       0.003 |       0.07  |
| ltx25       | age_band    |          4 | 18-29           |       0.816 |         0.763 |         0.865 | 60+          |      0.896 |     0.08  |       0.042 |       0.135 |
| ltx25       | race_gender |          7 | east_asian__f   |       0.822 |         0.708 |         0.901 | black__m     |      0.944 |     0.121 |       0.059 |       0.247 |
| all         | race        |          7 | southeast_asian |       0.89  |         0.82  |         0.927 | mena         |      0.955 |     0.065 |       0.044 |       0.141 |
| all         | gender      |          2 | f               |       0.895 |         0.859 |         0.928 | m            |      0.923 |     0.027 |       0.004 |       0.053 |
| all         | age_band    |          4 | 18-29           |       0.88  |         0.843 |         0.913 | 60+          |      0.931 |     0.051 |       0.028 |       0.087 |
| all         | race_gender |         10 | east_asian__f   |       0.884 |         0.793 |         0.925 | white__m     |      0.964 |     0.08  |       0.05  |       0.173 |

### Detection rate at the calibrated threshold

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1874 |      0.543 |   0.434 |   0.653 |
| wan22       | 1566 |      0.922 |   0.891 |   0.95  |
| hunyuan15   |  989 |      0.821 |   0.746 |   0.886 |
| ltx25       | 2002 |      0.44  |   0.342 |   0.541 |
| all         | 6431 |      0.646 |   0.581 |   0.713 |

#### by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 272 |      0.614 |   0.494 |   0.732 |
| ltx23       | east_asian      | 270 |      0.322 |   0.208 |   0.456 |
| ltx23       | indian          | 277 |      0.545 |   0.417 |   0.679 |
| ltx23       | latino          | 262 |      0.649 |   0.525 |   0.768 |
| ltx23       | mena            | 266 |      0.624 |   0.507 |   0.74  |
| ltx23       | southeast_asian | 271 |      0.384 |   0.264 |   0.507 |
| ltx23       | white           | 256 |      0.676 |   0.556 |   0.782 |
| wan22       | black           | 217 |      0.908 |   0.857 |   0.955 |
| wan22       | east_asian      | 226 |      0.801 |   0.72  |   0.874 |
| wan22       | indian          | 230 |      0.957 |   0.923 |   0.987 |
| wan22       | latino          | 219 |      0.991 |   0.971 |   1     |
| wan22       | mena            | 225 |      0.991 |   0.972 |   1     |
| wan22       | southeast_asian | 229 |      0.825 |   0.753 |   0.895 |
| wan22       | white           | 220 |      0.986 |   0.965 |   1     |
| hunyuan15   | black           | 141 |      0.844 |   0.752 |   0.921 |
| hunyuan15   | east_asian      | 141 |      0.603 |   0.5   |   0.704 |
| hunyuan15   | indian          | 142 |      0.817 |   0.681 |   0.925 |
| hunyuan15   | latino          | 142 |      0.88  |   0.807 |   0.944 |
| hunyuan15   | mena            | 139 |      0.935 |   0.881 |   0.98  |
| hunyuan15   | southeast_asian | 143 |      0.741 |   0.617 |   0.845 |
| hunyuan15   | white           | 141 |      0.929 |   0.875 |   0.973 |
| ltx25       | black           | 287 |      0.512 |   0.406 |   0.617 |
| ltx25       | east_asian      | 286 |      0.192 |   0.129 |   0.269 |
| ltx25       | indian          | 284 |      0.461 |   0.332 |   0.597 |
| ltx25       | latino          | 286 |      0.483 |   0.359 |   0.604 |
| ltx25       | mena            | 286 |      0.493 |   0.377 |   0.604 |
| ltx25       | southeast_asian | 286 |      0.287 |   0.189 |   0.387 |
| ltx25       | white           | 287 |      0.648 |   0.535 |   0.757 |
| all         | black           | 917 |      0.687 |   0.617 |   0.756 |
| all         | east_asian      | 923 |      0.442 |   0.379 |   0.509 |
| all         | indian          | 933 |      0.662 |   0.585 |   0.747 |
| all         | latino          | 909 |      0.715 |   0.645 |   0.782 |
| all         | mena            | 916 |      0.721 |   0.652 |   0.787 |
| all         | southeast_asian | 929 |      0.518 |   0.445 |   0.594 |
| all         | white           | 904 |      0.782 |   0.719 |   0.843 |

#### by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.537 |   0.424 |   0.655 |
| ltx23       | m       |  943 |      0.549 |   0.44  |   0.659 |
| wan22       | f       |  785 |      0.91  |   0.863 |   0.947 |
| wan22       | m       |  781 |      0.935 |   0.908 |   0.96  |
| hunyuan15   | f       |  495 |      0.776 |   0.678 |   0.86  |
| hunyuan15   | m       |  494 |      0.866 |   0.806 |   0.917 |
| ltx25       | f       |  999 |      0.433 |   0.334 |   0.537 |
| ltx25       | m       | 1003 |      0.446 |   0.343 |   0.552 |
| all         | f       | 3210 |      0.633 |   0.564 |   0.702 |
| all         | m       | 3221 |      0.659 |   0.595 |   0.724 |

#### by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  468 |      0.474 |   0.356 |   0.598 |
| ltx23       | 30-44   |  470 |      0.528 |   0.416 |   0.641 |
| ltx23       | 45-59   |  478 |      0.561 |   0.444 |   0.675 |
| ltx23       | 60+     |  458 |      0.611 |   0.496 |   0.731 |
| wan22       | 18-29   |  388 |      0.851 |   0.787 |   0.902 |
| wan22       | 30-44   |  377 |      0.881 |   0.828 |   0.927 |
| wan22       | 45-59   |  398 |      0.96  |   0.937 |   0.981 |
| wan22       | 60+     |  403 |      0.993 |   0.984 |   1     |
| hunyuan15   | 18-29   |  242 |      0.69  |   0.575 |   0.796 |
| hunyuan15   | 30-44   |  248 |      0.758 |   0.643 |   0.859 |
| hunyuan15   | 45-59   |  250 |      0.924 |   0.851 |   0.979 |
| hunyuan15   | 60+     |  249 |      0.908 |   0.833 |   0.967 |
| ltx25       | 18-29   |  500 |      0.326 |   0.227 |   0.427 |
| ltx25       | 30-44   |  497 |      0.4   |   0.293 |   0.509 |
| ltx25       | 45-59   |  501 |      0.481 |   0.377 |   0.589 |
| ltx25       | 60+     |  504 |      0.55  |   0.427 |   0.669 |
| all         | 18-29   | 1598 |      0.552 |   0.477 |   0.629 |
| all         | 30-44   | 1592 |      0.607 |   0.537 |   0.68  |
| all         | 45-59   | 1627 |      0.69  |   0.621 |   0.755 |
| all         | 60+     | 1614 |      0.733 |   0.664 |   0.801 |

### Detection-rate gap at the calibrated threshold

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level       | min_level            |
|:------------|:-----------------|------:|--------:|--------:|:----------------|:---------------------|
| ltx23       | race             | 0.354 |   0.277 |   0.449 | white           | east_asian           |
| ltx23       | gender           | 0.012 |   0.001 |   0.066 | m               | f                    |
| ltx23       | age_band         | 0.137 |   0.065 |   0.213 | 60+             | 18-29                |
| ltx23       | cell             | 0.578 |   0.517 |   0.785 | mena__m__60+    | east_asian__m__45-59 |
| ltx23       | setting          | 0.535 |   0.494 |   1     | livingroom      | library              |
| ltx23       | lighting         | 0.756 |   0.595 |   0.937 | softwindow      | lowlight             |
| ltx23       | behavior         | 0.759 |   0.579 |   0.961 | smile           | turn                 |
| ltx23       | camera           | 0.199 |   0.02  |   0.398 | static          | slowsway             |
| ltx23       | duration_nominal | 0.077 |   0.004 |   0.301 | 5.0             | 6.0                  |
| wan22       | race             | 0.19  |   0.125 |   0.269 | mena            | east_asian           |
| wan22       | gender           | 0.025 |   0.001 |   0.062 | m               | f                    |
| wan22       | age_band         | 0.142 |   0.092 |   0.204 | 60+             | 18-29                |
| wan22       | cell             | 0.483 |   0.344 |   0.667 | black__f__60+   | east_asian__m__18-29 |
| wan22       | setting          | 0.164 |   0.114 |   0.442 | studio          | classroom            |
| wan22       | lighting         | 0.15  |   0.064 |   0.299 | warmlamp        | overcast             |
| wan22       | behavior         | 0.212 |   0.113 |   0.36  | laugh           | turn                 |
| wan22       | camera           | 0.012 |   0.001 |   0.075 | static          | slowsway             |
| wan22       | duration_nominal | 0.053 |   0.005 |   0.106 | 5.0             | 6.0                  |
| hunyuan15   | race             | 0.332 |   0.257 |   0.415 | mena            | east_asian           |
| hunyuan15   | gender           | 0.091 |   0.041 |   0.143 | m               | f                    |
| hunyuan15   | age_band         | 0.234 |   0.167 |   0.33  | 45-59           | 18-29                |
| hunyuan15   | cell             | 0.765 |   0.619 |   0.945 | black__m__60+   | east_asian__m__18-29 |
| hunyuan15   | setting          | 0.232 |   0.189 |   0.54  | lobby           | library              |
| hunyuan15   | lighting         | 0.227 |   0.136 |   0.526 | backlit         | harsh                |
| hunyuan15   | behavior         | 0.295 |   0.196 |   0.558 | smile           | speak                |
| hunyuan15   | camera           | 0.045 |   0.004 |   0.187 | static          | slowsway             |
| hunyuan15   | duration_nominal | 0.07  |   0.004 |   0.224 | 6.0             | 5.0                  |
| ltx25       | race             | 0.456 |   0.367 |   0.537 | white           | east_asian           |
| ltx25       | gender           | 0.012 |   0.001 |   0.065 | m               | f                    |
| ltx25       | age_band         | 0.224 |   0.129 |   0.332 | 60+             | 18-29                |
| ltx25       | cell             | 0.667 |   0.611 |   0.861 | white__f__45-59 | east_asian__m__18-29 |
| ltx25       | setting          | 0.782 |   0.625 |   0.875 | studio          | library              |
| ltx25       | lighting         | 0.402 |   0.244 |   0.736 | warmlamp        | lowlight             |
| ltx25       | behavior         | 0.499 |   0.357 |   0.812 | smile           | turn                 |
| ltx25       | camera           | 0.172 |   0.022 |   0.359 | static          | slowsway             |
| ltx25       | duration_nominal | 0.054 |   0.004 |   0.248 | 5.0             | 6.0                  |
| all         | race             | 0.34  |   0.297 |   0.384 | white           | east_asian           |
| all         | gender           | 0.026 |   0.002 |   0.054 | m               | f                    |
| all         | age_band         | 0.181 |   0.124 |   0.248 | 60+             | 18-29                |
| all         | cell             | 0.585 |   0.503 |   0.699 | white__m__60+   | east_asian__m__18-29 |
| all         | setting          | 0.393 |   0.331 |   0.681 | studio          | library              |
| all         | lighting         | 0.346 |   0.224 |   0.546 | softwindow      | lowlight             |
| all         | behavior         | 0.486 |   0.358 |   0.643 | smile           | turn                 |
| all         | camera           | 0.122 |   0.014 |   0.249 | static          | slowsway             |
| all         | duration_nominal | 0.058 |   0.003 |   0.188 | 5.0             | 6.0                  |

### Flip rate at the calibrated threshold

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.861 |   0.75  |   0.972 |        1 |     1 |
| wan22       |         36 |       0.611 |   0.444 |   0.778 |        1 |     1 |
| hunyuan15   |         18 |       0.944 |   0.824 |   1     |        1 |     1 |
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

