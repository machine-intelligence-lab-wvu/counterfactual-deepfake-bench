# vpvp / face512_2s: snapshot 20261021-2230

> **Detector training data.** V-PVP head trained by the authors on AIGVDBench Real + Open-Sora + CogVideoX1.5 + EasyAnimate with a frozen Kinetics-400 VideoMAE-B/16; none of our generators is in its training set.

> **Provisional threshold.** Every detection rate and flip rate below uses the detector's default threshold (0.5; official: sigmoid(logit) > 0.5 (eval_opensource.py --threshold default)). They will be replaced by the 5%-real-FPR threshold once reals exist (section 6.3).

## Settings

| setting           | value                                                                                  |
|:------------------|:---------------------------------------------------------------------------------------|
| detector          | vpvp 1+c6ec2331                                                                        |
| checkpoint_sha256 | 33581d50452bcf19373a3e5db1204e44b456cb216ac21a3b889ee6970ba6f93b                       |
| view              | face512_2s (view_hash 92b6f25d9ce9e5f4)                                                |
| ffmpeg            | ffmpeg version 7.1.1 Copyright (c) 2000-2025 the FFmpeg developers                     |
| batches           | fake_b1, fake_b2, real_all                                                             |
| inclusion set     | primary (technical QC pass AND face QC pass)                                           |
| bootstrap         | 1000 resamples of whole counterfactual groups, seed 20261020, 95% percentile intervals |
| git commit        | 0528ba2cad5a-dirty                                                                     |
| created           | 2026-10-21T22:30:43Z                                                                   |

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
| fake_b1  | ltx23       |    2016 |      1878 |       2005 |              11 |               0 |     2005 |              0 |       1867 |
| fake_b1  | wan22       |    2016 |      1566 |       2016 |               0 |               0 |     2016 |              0 |       1566 |
| fake_b2  | hunyuan15   |     504 |       497 |        504 |               0 |               0 |      504 |              0 |        497 |
| real_all | real        |    2221 |      2221 |       2206 |              15 |               0 |     2206 |              0 |       2206 |

face512 window placement (fixed window at the median YuNet face centre, shifted inward at frame edges). The scaled frame is exactly 512 px on its short side, so every window spans it fully and is "shifted" on that axis by construction; the long-axis count is the informative one.

|   rendered |   shifted_long_axis |   shifted_short_axis |   max_shift_long_px |   excluded_no_face |
|-----------:|--------------------:|---------------------:|--------------------:|-------------------:|
|       9441 |                 439 |                 9405 |                 203 |                 41 |

Reals scored: 4412. Fakes included: 4422 of 9441 scored (0 scoring failures).

## Observations

- LTX 2.3: mean score 0.887 [0.829, 0.935], median 0.999, n = 1867.
- Wan 2.2: mean score 0.985 [0.976, 0.992], median 1.000, n = 1566.
- HunyuanVideo 1.5: mean score 0.707 [0.595, 0.814], median 0.958, n = 989.
- Provisional detection rate (score >= 0.5), LTX 2.3: 89.7% [84.0, 94.6].
- Provisional detection rate (score >= 0.5), Wan 2.2: 99.2% [98.4, 99.8].
- Provisional detection rate (score >= 0.5), HunyuanVideo 1.5: 71.4% [58.9, 82.6].
- Provisional detection rate (score >= 0.5), all: 89.0% [83.8, 93.6].
- Largest race score gap: HunyuanVideo 1.5 0.147 [0.095, 0.230] (east_asian 0.767 vs white 0.620).
- Largest gender score gap: HunyuanVideo 1.5 0.032 [0.001, 0.085] (m 0.723 vs f 0.691).
- Largest age band score gap: HunyuanVideo 1.5 0.245 [0.153, 0.348] (18-29 0.817 vs 60+ 0.571).
- Largest cell score gap: HunyuanVideo 1.5 0.542 [0.433, 0.781] (east_asian__m__18-29 0.925 vs white__f__60+ 0.383).
- Largest scene-factor gap (all generators): behavior 0.269 [0.143, 0.524] (think vs read).
- Largest partial eta squared: generator 0.156, behavior 0.098, setting 0.059; residual holds 63.3% of total SS.
- CF spread, LTX 2.3: 0.167 [0.121, 0.208] over 36 groups (max 0.409).
- CF spread, Wan 2.2: 0.043 [0.023, 0.067] over 36 groups (max 0.207).
- CF spread, HunyuanVideo 1.5: 0.282 [0.238, 0.322] over 18 groups (max 0.425).
- Provisional flip rate, LTX 2.3: 66.7% of 36 groups [52.7, 80.6].
- Provisional flip rate, Wan 2.2: 13.9% of 36 groups [2.8, 25.1].
- Provisional flip rate, HunyuanVideo 1.5: 94.4% of 18 groups [81.8, 100.0].

## 6.1 Fakes only, no threshold

### Mean score by generator

| generator   |    n |   n_groups |   estimate |   ci_lo |   ci_hi |    sd |   median |   q05 |   q95 |
|:------------|-----:|-----------:|-----------:|--------:|--------:|------:|---------:|------:|------:|
| ltx23       | 1867 |         36 |      0.887 |   0.829 |   0.935 | 0.261 |    0.999 | 0.11  |     1 |
| wan22       | 1566 |         36 |      0.985 |   0.976 |   0.992 | 0.078 |    1     | 0.942 |     1 |
| hunyuan15   |  989 |         18 |      0.707 |   0.595 |   0.814 | 0.383 |    0.958 | 0.006 |     1 |
| all         | 4422 |         36 |      0.881 |   0.831 |   0.927 | 0.272 |    1     | 0.072 |     1 |

### Mean score by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:----------------|----:|-----------:|--------:|--------:|---------:|
| ltx23       | black           | 270 |      0.893 |   0.825 |   0.947 |    1     |
| ltx23       | east_asian      | 270 |      0.874 |   0.815 |   0.927 |    0.999 |
| ltx23       | indian          | 276 |      0.908 |   0.855 |   0.954 |    0.999 |
| ltx23       | latino          | 261 |      0.873 |   0.808 |   0.933 |    0.999 |
| ltx23       | mena            | 266 |      0.91  |   0.861 |   0.956 |    1     |
| ltx23       | southeast_asian | 271 |      0.87  |   0.803 |   0.928 |    1     |
| ltx23       | white           | 253 |      0.878 |   0.817 |   0.933 |    0.999 |
| wan22       | black           | 217 |      0.988 |   0.981 |   0.995 |    1     |
| wan22       | east_asian      | 226 |      0.974 |   0.953 |   0.992 |    1     |
| wan22       | indian          | 230 |      0.981 |   0.964 |   0.995 |    1     |
| wan22       | latino          | 219 |      0.992 |   0.984 |   0.997 |    1     |
| wan22       | mena            | 225 |      0.993 |   0.983 |   0.998 |    1     |
| wan22       | southeast_asian | 229 |      0.985 |   0.971 |   0.995 |    1     |
| wan22       | white           | 220 |      0.984 |   0.972 |   0.994 |    1     |
| hunyuan15   | black           | 141 |      0.75  |   0.633 |   0.857 |    0.971 |
| hunyuan15   | east_asian      | 141 |      0.767 |   0.667 |   0.867 |    0.968 |
| hunyuan15   | indian          | 142 |      0.717 |   0.592 |   0.84  |    0.971 |
| hunyuan15   | latino          | 142 |      0.681 |   0.557 |   0.796 |    0.922 |
| hunyuan15   | mena            | 139 |      0.735 |   0.616 |   0.841 |    0.965 |
| hunyuan15   | southeast_asian | 143 |      0.679 |   0.54  |   0.811 |    0.958 |
| hunyuan15   | white           | 141 |      0.62  |   0.5   |   0.742 |    0.885 |
| all         | black           | 628 |      0.894 |   0.842 |   0.941 |    1     |
| all         | east_asian      | 637 |      0.886 |   0.839 |   0.928 |    0.999 |
| all         | indian          | 648 |      0.892 |   0.84  |   0.941 |    1     |
| all         | latino          | 622 |      0.871 |   0.816 |   0.921 |    0.999 |
| all         | mena            | 630 |      0.901 |   0.856 |   0.942 |    1     |
| all         | southeast_asian | 643 |      0.869 |   0.813 |   0.922 |    0.999 |
| all         | white           | 614 |      0.857 |   0.803 |   0.909 |    0.999 |

### Mean score by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | f       |  931 |      0.886 |   0.827 |   0.937 |    0.999 |
| ltx23       | m       |  936 |      0.887 |   0.829 |   0.936 |    1     |
| wan22       | f       |  785 |      0.981 |   0.967 |   0.991 |    1     |
| wan22       | m       |  781 |      0.99  |   0.98  |   0.997 |    1     |
| hunyuan15   | f       |  495 |      0.691 |   0.574 |   0.797 |    0.935 |
| hunyuan15   | m       |  494 |      0.723 |   0.603 |   0.838 |    0.965 |
| all         | f       | 2211 |      0.876 |   0.823 |   0.923 |    0.999 |
| all         | m       | 2211 |      0.887 |   0.839 |   0.933 |    1     |

### Mean score by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |   median |
|:------------|:--------|-----:|-----------:|--------:|--------:|---------:|
| ltx23       | 18-29   |  464 |      0.907 |   0.865 |   0.946 |    0.999 |
| ltx23       | 30-44   |  469 |      0.89  |   0.828 |   0.943 |    1     |
| ltx23       | 45-59   |  477 |      0.868 |   0.798 |   0.93  |    0.999 |
| ltx23       | 60+     |  457 |      0.882 |   0.812 |   0.941 |    0.999 |
| wan22       | 18-29   |  388 |      0.986 |   0.971 |   0.997 |    1     |
| wan22       | 30-44   |  377 |      0.99  |   0.982 |   0.996 |    1     |
| wan22       | 45-59   |  398 |      0.984 |   0.973 |   0.994 |    1     |
| wan22       | 60+     |  403 |      0.982 |   0.97  |   0.991 |    1     |
| hunyuan15   | 18-29   |  242 |      0.817 |   0.725 |   0.902 |    0.993 |
| hunyuan15   | 30-44   |  248 |      0.787 |   0.663 |   0.896 |    0.989 |
| hunyuan15   | 45-59   |  250 |      0.656 |   0.526 |   0.785 |    0.855 |
| hunyuan15   | 60+     |  249 |      0.571 |   0.423 |   0.715 |    0.727 |
| all         | 18-29   | 1094 |      0.915 |   0.88  |   0.949 |    1     |
| all         | 30-44   | 1094 |      0.901 |   0.852 |   0.947 |    1     |
| all         | 45-59   | 1125 |      0.862 |   0.802 |   0.918 |    0.999 |
| all         | 60+     | 1109 |      0.848 |   0.784 |   0.908 |    0.999 |

### Mean score by scene factor (all generators pooled)

| factor           | level      |    n |   estimate |   ci_lo |   ci_hi |
|:-----------------|:-----------|-----:|-----------:|--------:|--------:|
| setting          | cafe       |  373 |      0.748 |   0.443 |   0.951 |
| setting          | classroom  |  373 |      0.795 |   0.745 |   0.923 |
| setting          | corridor   |  493 |      0.85  |   0.734 |   0.981 |
| setting          | kitchen    |  439 |      0.771 |   0.537 |   0.951 |
| setting          | library    |  532 |      0.938 |   0.893 |   0.994 |
| setting          | livingroom |  529 |      0.973 |   0.953 |   1     |
| setting          | lobby      |  345 |      0.948 |   0.918 |   0.985 |
| setting          | office     |  357 |      0.795 |   0.524 |   0.997 |
| setting          | plainwall  |  553 |      0.938 |   0.89  |   0.977 |
| setting          | studio     |  428 |      0.985 |   0.973 |   1     |
| lighting         | backlit    |  782 |      0.956 |   0.922 |   0.983 |
| lighting         | harsh      |  632 |      0.706 |   0.576 |   0.899 |
| lighting         | lowlight   |  781 |      0.968 |   0.943 |   0.988 |
| lighting         | overcast   |  692 |      0.873 |   0.798 |   0.947 |
| lighting         | softwindow |  821 |      0.892 |   0.794 |   0.969 |
| lighting         | warmlamp   |  714 |      0.855 |   0.658 |   0.98  |
| behavior         | laugh      |  498 |      0.899 |   0.768 |   0.988 |
| behavior         | listen     |  676 |      0.968 |   0.952 |   0.983 |
| behavior         | pause      |  520 |      0.915 |   0.83  |   0.963 |
| behavior         | read       |  576 |      0.704 |   0.443 |   0.977 |
| behavior         | smile      |  538 |      0.962 |   0.907 |   1     |
| behavior         | speak      |  530 |      0.836 |   0.754 |   0.925 |
| behavior         | think      |  506 |      0.973 |   0.921 |   0.997 |
| behavior         | turn       |  578 |      0.799 |   0.647 |   0.937 |
| camera           | slowsway   | 2218 |      0.836 |   0.744 |   0.925 |
| camera           | static     | 2204 |      0.927 |   0.898 |   0.953 |
| duration_nominal | 5.0        | 2223 |      0.886 |   0.804 |   0.961 |
| duration_nominal | 6.0        | 2199 |      0.876 |   0.821 |   0.925 |

Per-generator scene-factor and 56-cell rows: `tables/score_by_breakdown.csv`.

### Subgroup gap (max - min of level means)

A gap is max - min, so it is never negative and its interval cannot include 0; it is a size, not a test of a difference. Over many levels with few clips each (56 cells; HunyuanVideo has 9 groups per cell) the gap also grows with noise, so compare it with the per-level intervals in `tables/score_by_breakdown.csv`. Levels seen in a single counterfactual group have no interval.

| generator   | attribute        |   n_levels |   gap |   ci_lo |   ci_hi | max_level            | min_level            |
|:------------|:-----------------|-----------:|------:|--------:|--------:|:---------------------|:---------------------|
| ltx23       | race             |          7 | 0.039 |   0.027 |   0.088 | mena                 | southeast_asian      |
| ltx23       | gender           |          2 | 0.001 |   0.001 |   0.039 | m                    | f                    |
| ltx23       | age_band         |          4 | 0.04  |   0.014 |   0.09  | 18-29                | 45-59                |
| ltx23       | cell             |         56 | 0.175 |   0.157 |   0.337 | east_asian__f__18-29 | east_asian__m__30-44 |
| ltx23       | setting          |         10 | 0.271 |   0.196 |   0.653 | studio               | kitchen              |
| ltx23       | lighting         |          6 | 0.255 |   0.138 |   0.474 | lowlight             | harsh                |
| ltx23       | behavior         |          8 | 0.285 |   0.161 |   0.648 | smile                | read                 |
| ltx23       | camera           |          2 | 0.068 |   0.004 |   0.179 | static               | slowsway             |
| ltx23       | duration_nominal |          2 | 0.012 |   0.002 |   0.124 | 5.0                  | 6.0                  |
| wan22       | race             |          7 | 0.019 |   0.009 |   0.041 | mena                 | east_asian           |
| wan22       | gender           |          2 | 0.009 |   0     |   0.023 | m                    | f                    |
| wan22       | age_band         |          4 | 0.008 |   0.004 |   0.02  | 30-44                | 60+                  |
| wan22       | cell             |         56 | 0.067 |   0.041 |   0.162 | latino__m__18-29     | east_asian__f__60+   |
| wan22       | setting          |         10 | 0.046 |   0.028 |   0.081 | studio               | kitchen              |
| wan22       | lighting         |          6 | 0.031 |   0.016 |   0.065 | backlit              | harsh                |
| wan22       | behavior         |          8 | 0.053 |   0.028 |   0.079 | smile                | read                 |
| wan22       | camera           |          2 | 0.014 |   0.002 |   0.029 | static               | slowsway             |
| wan22       | duration_nominal |          2 | 0.007 |   0     |   0.024 | 5.0                  | 6.0                  |
| hunyuan15   | race             |          7 | 0.147 |   0.095 |   0.23  | east_asian           | white                |
| hunyuan15   | gender           |          2 | 0.032 |   0.001 |   0.085 | m                    | f                    |
| hunyuan15   | age_band         |          4 | 0.245 |   0.153 |   0.348 | 18-29                | 60+                  |
| hunyuan15   | cell             |         56 | 0.542 |   0.433 |   0.781 | east_asian__m__18-29 | white__f__60+        |
| hunyuan15   | setting          |         10 | 0.459 |   0.352 |   0.806 | lobby                | office               |
| hunyuan15   | lighting         |          6 | 0.527 |   0.268 |   0.788 | lowlight             | harsh                |
| hunyuan15   | behavior         |          8 | 0.557 |   0.356 |   0.791 | think                | turn                 |
| hunyuan15   | camera           |          2 | 0.264 |   0.058 |   0.454 | static               | slowsway             |
| hunyuan15   | duration_nominal |          2 | 0.016 |   0.004 |   0.271 | 6.0                  | 5.0                  |
| all         | race             |          7 | 0.044 |   0.031 |   0.065 | mena                 | white                |
| all         | gender           |          2 | 0.011 |   0.001 |   0.028 | m                    | f                    |
| all         | age_band         |          4 | 0.067 |   0.033 |   0.109 | 18-29                | 60+                  |
| all         | cell             |         56 | 0.17  |   0.134 |   0.269 | indian__f__18-29     | white__f__60+        |
| all         | setting          |         10 | 0.236 |   0.174 |   0.542 | studio               | cafe                 |
| all         | lighting         |          6 | 0.263 |   0.124 |   0.409 | lowlight             | harsh                |
| all         | behavior         |          8 | 0.269 |   0.143 |   0.524 | think                | read                 |
| all         | camera           |          2 | 0.09  |   0.006 |   0.183 | static               | slowsway             |
| all         | duration_nominal |          2 | 0.01  |   0.002 |   0.11  | 5.0                  | 6.0                  |

### CF spread (mean over groups of the std of score across the group's cells)

| generator   |   n_groups |   cf_spread |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.167 |   0.121 |   0.208 |    0.139 | 0.409 |
| wan22       |         36 |       0.043 |   0.023 |   0.067 |    0.014 | 0.207 |
| hunyuan15   |         18 |       0.282 |   0.238 |   0.322 |    0.301 | 0.425 |

### Factor attribution

OLS with every factor as a fixed effect, type-II ANOVA. `ss_share` is the factor's type-II sum of squares over the total sum of squares (type-II shares need not add to 1). Scene factors are constant within a counterfactual group, so their effects are estimated from between-group differences only. The OLS F tests treat clips as independent although clips are clustered in counterfactual groups, so their p values are optimistic; use the group-bootstrap intervals above for inference.

| factor           |   df |      sum_sq | F        | p          | partial_eta2   |   ss_share |
|:-----------------|-----:|------------:|:---------|:-----------|:---------------|-----------:|
| race             |    6 |   0.8833    | 3.11     | 0.004841   | 0.004236       |  0.002692  |
| gender           |    1 |   0.08199   | 1.732    | 0.1882     | 0.0003947      |  0.0002499 |
| age_band         |    3 |   3.163     | 22.27    | 2.61e-14   | 0.01501        |  0.009642  |
| setting          |    9 |  12.95      | 30.38    | 5.362e-52  | 0.05869        |  0.03946   |
| lighting         |    5 |   8.449     | 35.69    | 6.271e-36  | 0.0391         |  0.02575   |
| behavior         |    7 |  22.48      | 67.82    | 2.646e-93  | 0.09767        |  0.06851   |
| camera           |    1 |   1.558     | 32.9     | 1.034e-08  | 0.007446       |  0.004747  |
| duration_nominal |    1 |   0.0001512 | 0.003194 | 0.9549     | 7.281e-07      |  4.608e-07 |
| generator        |    2 |  38.46      | 406.2    | 1.377e-162 | 0.1563         |  0.1172    |
| Residual         | 4386 | 207.6       |          |            |                |  0.6329    |

Lighting x race interaction (added to the same OLS):

| term            |   df |   sum_sq |      F |      p |   partial_eta2 |
|:----------------|-----:|---------:|-------:|-------:|---------------:|
| lighting x race |   30 |     1.18 | 0.8301 | 0.7293 |       0.005685 |

Mixed model `score ~ factors + (1 | counterfactual_group)` (REML) variance components (fixed effects: `tables/factor_mixed_fixed.csv`):

| component                               |   variance | converged   |
|:----------------------------------------|-----------:|:------------|
| counterfactual_group (random intercept) |    0       | True        |
| residual                                |    0.04626 | True        |
| ICC (group share of random variance)    |    0       | True        |

A group variance at or near 0 is a boundary estimate: setting, lighting, behavior, camera and duration are fixed per group and absorb most between-group variation, leaving little for the random intercept. It does not mean scenes do not matter.

## 6.2 Provisional (threshold 0.5, provisional)

### Detection rate by generator (provisional)

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1867 |      0.897 |   0.84  |   0.946 |
| wan22       | 1566 |      0.992 |   0.984 |   0.998 |
| hunyuan15   |  989 |      0.714 |   0.589 |   0.826 |
| all         | 4422 |      0.89  |   0.838 |   0.936 |

### Detection rate by race (provisional)

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 270 |      0.893 |   0.824 |   0.953 |
| ltx23       | east_asian      | 270 |      0.889 |   0.83  |   0.943 |
| ltx23       | indian          | 276 |      0.913 |   0.854 |   0.961 |
| ltx23       | latino          | 261 |      0.866 |   0.794 |   0.934 |
| ltx23       | mena            | 266 |      0.932 |   0.888 |   0.975 |
| ltx23       | southeast_asian | 271 |      0.889 |   0.821 |   0.952 |
| ltx23       | white           | 253 |      0.897 |   0.842 |   0.951 |
| wan22       | black           | 217 |      1     |   1     |   1     |
| wan22       | east_asian      | 226 |      0.978 |   0.951 |   1     |
| wan22       | indian          | 230 |      0.987 |   0.964 |   1     |
| wan22       | latino          | 219 |      1     |   1     |   1     |
| wan22       | mena            | 225 |      0.996 |   0.985 |   1     |
| wan22       | southeast_asian | 229 |      0.991 |   0.978 |   1     |
| wan22       | white           | 220 |      0.995 |   0.986 |   1     |
| hunyuan15   | black           | 141 |      0.745 |   0.614 |   0.869 |
| hunyuan15   | east_asian      | 141 |      0.809 |   0.698 |   0.908 |
| hunyuan15   | indian          | 142 |      0.732 |   0.586 |   0.867 |
| hunyuan15   | latino          | 142 |      0.704 |   0.57  |   0.829 |
| hunyuan15   | mena            | 139 |      0.748 |   0.615 |   0.863 |
| hunyuan15   | southeast_asian | 143 |      0.664 |   0.514 |   0.807 |
| hunyuan15   | white           | 141 |      0.596 |   0.467 |   0.725 |
| all         | black           | 628 |      0.896 |   0.839 |   0.949 |
| all         | east_asian      | 637 |      0.903 |   0.853 |   0.947 |
| all         | indian          | 648 |      0.9   |   0.842 |   0.954 |
| all         | latino          | 622 |      0.876 |   0.817 |   0.929 |
| all         | mena            | 630 |      0.914 |   0.87  |   0.955 |
| all         | southeast_asian | 643 |      0.876 |   0.82  |   0.929 |
| all         | white           | 614 |      0.863 |   0.809 |   0.913 |

### Detection rate by gender (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.898 |   0.839 |   0.948 |
| ltx23       | m       |  936 |      0.896 |   0.836 |   0.946 |
| wan22       | f       |  785 |      0.989 |   0.975 |   0.999 |
| wan22       | m       |  781 |      0.996 |   0.99  |   1     |
| hunyuan15   | f       |  495 |      0.695 |   0.57  |   0.809 |
| hunyuan15   | m       |  494 |      0.733 |   0.606 |   0.852 |
| all         | f       | 2211 |      0.885 |   0.83  |   0.935 |
| all         | m       | 2211 |      0.895 |   0.846 |   0.943 |

### Detection rate by age band (provisional)

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  464 |      0.916 |   0.874 |   0.956 |
| ltx23       | 30-44   |  469 |      0.906 |   0.84  |   0.959 |
| ltx23       | 45-59   |  477 |      0.874 |   0.805 |   0.936 |
| ltx23       | 60+     |  457 |      0.893 |   0.827 |   0.95  |
| wan22       | 18-29   |  388 |      0.99  |   0.974 |   1     |
| wan22       | 30-44   |  377 |      0.995 |   0.985 |   1     |
| wan22       | 45-59   |  398 |      0.992 |   0.983 |   1     |
| wan22       | 60+     |  403 |      0.993 |   0.982 |   1     |
| hunyuan15   | 18-29   |  242 |      0.822 |   0.732 |   0.91  |
| hunyuan15   | 30-44   |  248 |      0.798 |   0.655 |   0.922 |
| hunyuan15   | 45-59   |  250 |      0.664 |   0.522 |   0.801 |
| hunyuan15   | 60+     |  249 |      0.574 |   0.413 |   0.732 |
| all         | 18-29   | 1094 |      0.921 |   0.886 |   0.955 |
| all         | 30-44   | 1094 |      0.912 |   0.859 |   0.96  |
| all         | 45-59   | 1125 |      0.869 |   0.808 |   0.926 |
| all         | 60+     | 1109 |      0.858 |   0.789 |   0.918 |

### Detection-rate gap (provisional)

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level            | min_level          |
|:------------|:-----------------|------:|--------:|--------:|:---------------------|:-------------------|
| ltx23       | race             | 0.066 |   0.037 |   0.112 | mena                 | latino             |
| ltx23       | gender           | 0.002 |   0.001 |   0.044 | f                    | m                  |
| ltx23       | age_band         | 0.042 |   0.015 |   0.093 | 18-29                | 45-59              |
| ltx23       | cell             | 0.206 |   0.182 |   0.394 | east_asian__f__18-29 | black__f__60+      |
| ltx23       | setting          | 0.261 |   0.187 |   0.661 | studio               | kitchen            |
| ltx23       | lighting         | 0.253 |   0.13  |   0.489 | lowlight             | harsh              |
| ltx23       | behavior         | 0.289 |   0.154 |   0.661 | smile                | read               |
| ltx23       | camera           | 0.068 |   0.004 |   0.181 | static               | slowsway           |
| ltx23       | duration_nominal | 0.002 |   0.001 |   0.124 | 5.0                  | 6.0                |
| wan22       | race             | 0.022 |   0.008 |   0.05  | black                | east_asian         |
| wan22       | gender           | 0.008 |   0     |   0.022 | m                    | f                  |
| wan22       | age_band         | 0.005 |   0.002 |   0.022 | 30-44                | 18-29              |
| wan22       | cell             | 0.074 |   0.034 |   0.191 | black__f__18-29      | east_asian__f__60+ |
| wan22       | setting          | 0.043 |   0.018 |   0.083 | classroom            | kitchen            |
| wan22       | lighting         | 0.028 |   0.007 |   0.068 | backlit              | harsh              |
| wan22       | behavior         | 0.042 |   0.013 |   0.083 | laugh                | read               |
| wan22       | camera           | 0.01  |   0.001 |   0.025 | static               | slowsway           |
| wan22       | duration_nominal | 0.001 |   0     |   0.016 | 6.0                  | 5.0                |
| hunyuan15   | race             | 0.213 |   0.139 |   0.306 | east_asian           | white              |
| hunyuan15   | gender           | 0.038 |   0.003 |   0.088 | m                    | f                  |
| hunyuan15   | age_band         | 0.248 |   0.158 |   0.368 | 18-29                | 60+                |
| hunyuan15   | cell             | 0.608 |   0.526 |   0.889 | east_asian__m__18-29 | white__f__60+      |
| hunyuan15   | setting          | 0.468 |   0.368 |   0.891 | lobby                | cafe               |
| hunyuan15   | lighting         | 0.553 |   0.289 |   0.85  | lowlight             | harsh              |
| hunyuan15   | behavior         | 0.57  |   0.373 |   0.867 | think                | turn               |
| hunyuan15   | camera           | 0.288 |   0.071 |   0.496 | static               | slowsway           |
| hunyuan15   | duration_nominal | 0.037 |   0.006 |   0.294 | 6.0                  | 5.0                |
| all         | race             | 0.051 |   0.036 |   0.076 | mena                 | white              |
| all         | gender           | 0.01  |   0.001 |   0.029 | m                    | f                  |
| all         | age_band         | 0.064 |   0.034 |   0.109 | 18-29                | 60+                |
| all         | cell             | 0.175 |   0.152 |   0.304 | mena__m__45-59       | black__f__60+      |
| all         | setting          | 0.238 |   0.168 |   0.577 | studio               | cafe               |
| all         | lighting         | 0.268 |   0.124 |   0.425 | lowlight             | harsh              |
| all         | behavior         | 0.277 |   0.138 |   0.563 | think                | read               |
| all         | camera           | 0.095 |   0.007 |   0.193 | static               | slowsway           |
| all         | duration_nominal | 0.002 |   0.002 |   0.109 | 6.0                  | 5.0                |

### Flip rate (provisional): share of groups whose clips get different decisions

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.667 |   0.527 |   0.806 |        1 |     1 |
| wan22       |         36 |       0.139 |   0.028 |   0.251 |        0 |     1 |
| hunyuan15   |         18 |       0.944 |   0.818 |   1     |        1 |     1 |

### Sensitivity: inclusion set

| set     | generator   |    n |   mean_score |   provisional_detection_rate |
|:--------|:------------|-----:|-------------:|-----------------------------:|
| all     | hunyuan15   | 1008 |        0.707 |                        0.713 |
| all     | ltx23       | 2005 |        0.883 |                        0.893 |
| all     | wan22       | 2016 |        0.987 |                        0.994 |
| primary | hunyuan15   |  989 |        0.707 |                        0.714 |
| primary | ltx23       | 1867 |        0.887 |                        0.897 |
| primary | wan22       | 1566 |        0.985 |                        0.992 |

## 6.3 Real vs generated (calibrated threshold 1.0000)

The threshold is the score at which 5% of primary real renders (24 and 16 fps pooled) are flagged; one per detector and view, never per subgroup. Each generator is compared with reals rendered at its own fps. Intervals: fakes resample counterfactual groups, reals resample identity clusters (source video). Real labels are perceived (FairFace), not self-reported.

### Calibration

| scope            |   n_renders |   n_sources |   n_identities |   threshold |    fpr |
|:-----------------|------------:|------------:|---------------:|------------:|-------:|
| all real renders |        4412 |        2206 |           1809 |           1 | 0.0501 |
| 16 fps renders   |        2206 |        2206 |           1809 |           1 | 0.0512 |
| 24 fps renders   |        2206 |        2206 |           1809 |           1 | 0.049  |

### AUC, AP, EER, TPR at 5% FPR

| generator   | real_fps   |   n_fake |   n_real |   auc |   auc_ci_lo |   auc_ci_hi |    ap |   eer |   tpr_at_5fpr |   detection_rate_global_thr |   det_ci_lo |   det_ci_hi |
|:------------|:-----------|---------:|---------:|------:|------------:|------------:|------:|------:|--------------:|----------------------------:|------------:|------------:|
| ltx23       | 24         |     1867 |     2206 | 0.518 |       0.449 |       0.585 | 0.456 | 0.48  |         0.023 |                       0.022 |       0.009 |       0.041 |
| wan22       | 16         |     1566 |     2206 | 0.655 |       0.603 |       0.703 | 0.495 | 0.391 |         0.029 |                       0.031 |       0.012 |       0.054 |
| hunyuan15   | 24         |      989 |     2206 | 0.305 |       0.241 |       0.373 | 0.218 | 0.636 |         0.001 |                       0.001 |       0     |       0.003 |
| all         | 24+16      |     4422 |     4412 | 0.519 |       0.463 |       0.575 | 0.497 | 0.476 |         0.021 |                       0.021 |       0.009 |       0.036 |

### Real FPR by perceived subgroup

| attribute   | level              |   n_renders |   n_identities |   fpr |   ci_lo |   ci_hi |
|:------------|:-------------------|------------:|---------------:|------:|--------:|--------:|
| race        | black              |         378 |            173 | 0.066 |   0.037 |   0.103 |
| race        | east_asian         |         380 |            169 | 0.021 |   0.005 |   0.042 |
| race        | indian             |         112 |             54 | 0.036 |   0     |   0.085 |
| race        | latino             |         254 |            119 | 0.028 |   0.004 |   0.057 |
| race        | mena               |         258 |            124 | 0.12  |   0.07  |   0.176 |
| race        | southeast_asian    |         184 |             85 | 0.049 |   0.011 |   0.094 |
| race        | white              |        2836 |           1179 | 0.048 |   0.037 |   0.06  |
| gender      | f                  |        1378 |            604 | 0.027 |   0.016 |   0.038 |
| gender      | m                  |        3024 |           1263 | 0.061 |   0.048 |   0.074 |
| age_band    | 18-29              |        1380 |            624 | 0.04  |   0.027 |   0.054 |
| age_band    | 30-44              |        1518 |            679 | 0.059 |   0.044 |   0.074 |
| age_band    | 45-59              |         644 |            274 | 0.07  |   0.037 |   0.105 |
| age_band    | 60+                |         624 |            268 | 0.045 |   0.022 |   0.072 |
| race_gender | black__f           |          64 |             30 | 0.016 |   0     |   0.054 |
| race_gender | black__m           |         314 |            144 | 0.076 |   0.041 |   0.119 |
| race_gender | east_asian__f      |         136 |             62 | 0     |   0     |   0     |
| race_gender | east_asian__m      |         244 |            110 | 0.033 |   0.008 |   0.067 |
| race_gender | indian__f          |          32 |             16 | 0     |   0     |   0     |
| race_gender | indian__m          |          80 |             38 | 0.05  |   0     |   0.118 |
| race_gender | latino__f          |          62 |             30 | 0.032 |   0     |   0.105 |
| race_gender | latino__m          |         192 |             89 | 0.026 |   0     |   0.062 |
| race_gender | mena__f            |          60 |             30 | 0.05  |   0     |   0.133 |
| race_gender | mena__m            |         198 |             94 | 0.141 |   0.081 |   0.21  |
| race_gender | southeast_asian__f |          64 |             30 | 0.047 |   0     |   0.128 |
| race_gender | southeast_asian__m |         120 |             56 | 0.05  |   0     |   0.113 |
| race_gender | white__f           |         960 |            425 | 0.029 |   0.015 |   0.045 |
| race_gender | white__m           |        1876 |            789 | 0.058 |   0.043 |   0.073 |

### Real FPR gap (max - min across levels; non-negative by construction)

| attribute   |   n_levels |   fpr_gap |   ci_lo |   ci_hi | max_level   |   max_fpr | min_level     |   min_fpr |
|:------------|-----------:|----------:|--------:|--------:|:------------|----------:|:--------------|----------:|
| race        |          7 |     0.099 |   0.058 |   0.165 | mena        |     0.12  | east_asian    |     0.021 |
| gender      |          2 |     0.034 |   0.017 |   0.051 | m           |     0.061 | f             |     0.027 |
| age_band    |          4 |     0.03  |   0.014 |   0.069 | 45-59       |     0.07  | 18-29         |     0.04  |
| race_gender |         14 |     0.141 |   0.09  |   0.21  | mena__m     |     0.141 | east_asian__f |     0     |

### Worst-subgroup AUC and AUC gap

| generator   | attribute   |   n_levels | worst_level   |   worst_auc |   worst_ci_lo |   worst_ci_hi | best_level    |   best_auc |   auc_gap |   gap_ci_lo |   gap_ci_hi |
|:------------|:------------|-----------:|:--------------|------------:|--------------:|--------------:|:--------------|-----------:|----------:|------------:|------------:|
| ltx23       | race        |          7 | mena          |       0.453 |         0.366 |         0.523 | east_asian    |      0.562 |     0.109 |       0.07  |       0.211 |
| ltx23       | gender      |          2 | m             |       0.504 |         0.438 |         0.574 | f             |      0.551 |     0.047 |       0.006 |       0.089 |
| ltx23       | age_band    |          4 | 45-59         |       0.494 |         0.416 |         0.564 | 60+           |      0.549 |     0.056 |       0.029 |       0.127 |
| ltx23       | race_gender |         13 | mena__m       |       0.465 |         0.333 |         0.508 | black__f      |      0.603 |     0.137 |       0.132 |       0.311 |
| wan22       | race        |          7 | mena          |       0.589 |         0.507 |         0.639 | east_asian    |      0.701 |     0.111 |       0.081 |       0.219 |
| wan22       | gender      |          2 | f             |       0.651 |         0.596 |         0.7   | m             |      0.687 |     0.036 |       0.003 |       0.084 |
| wan22       | age_band    |          4 | 45-59         |       0.622 |         0.546 |         0.683 | 18-29         |      0.704 |     0.082 |       0.039 |       0.146 |
| wan22       | race_gender |         13 | mena__f       |       0.599 |         0.469 |         0.639 | east_asian__m |      0.752 |     0.153 |       0.134 |       0.322 |
| hunyuan15   | race        |          7 | mena          |       0.229 |         0.151 |         0.289 | east_asian    |      0.379 |     0.15  |       0.103 |       0.241 |
| hunyuan15   | gender      |          2 | m             |       0.304 |         0.226 |         0.37  | f             |      0.32  |     0.016 |       0.001 |       0.067 |
| hunyuan15   | age_band    |          4 | 60+           |       0.237 |         0.168 |         0.301 | 18-29         |      0.404 |     0.167 |       0.115 |       0.236 |
| hunyuan15   | race_gender |         13 | mena__f       |       0.218 |         0.112 |         0.272 | east_asian__f |      0.388 |     0.17  |       0.154 |       0.339 |
| all         | race        |          7 | mena          |       0.453 |         0.38  |         0.514 | east_asian    |      0.571 |     0.118 |       0.075 |       0.207 |
| all         | gender      |          2 | m             |       0.524 |         0.462 |         0.578 | f             |      0.536 |     0.012 |       0.001 |       0.046 |
| all         | age_band    |          4 | 45-59         |       0.489 |         0.42  |         0.553 | 18-29         |      0.571 |     0.082 |       0.041 |       0.137 |
| all         | race_gender |         14 | mena__f       |       0.461 |         0.356 |         0.513 | indian__f     |      0.685 |     0.224 |       0.141 |       0.39  |

### Detection rate at the calibrated threshold

| generator   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|-----:|-----------:|--------:|--------:|
| ltx23       | 1867 |      0.022 |   0.009 |   0.041 |
| wan22       | 1566 |      0.031 |   0.012 |   0.054 |
| hunyuan15   |  989 |      0.001 |   0     |   0.003 |
| all         | 4422 |      0.021 |   0.009 |   0.036 |

#### by race

| generator   | level           |   n |   estimate |   ci_lo |   ci_hi |
|:------------|:----------------|----:|-----------:|--------:|--------:|
| ltx23       | black           | 270 |      0.022 |   0     |   0.052 |
| ltx23       | east_asian      | 270 |      0.015 |   0     |   0.033 |
| ltx23       | indian          | 276 |      0.025 |   0.007 |   0.053 |
| ltx23       | latino          | 261 |      0.011 |   0     |   0.025 |
| ltx23       | mena            | 266 |      0.053 |   0.018 |   0.097 |
| ltx23       | southeast_asian | 271 |      0.007 |   0     |   0.019 |
| ltx23       | white           | 253 |      0.024 |   0.007 |   0.047 |
| wan22       | black           | 217 |      0.023 |   0     |   0.067 |
| wan22       | east_asian      | 226 |      0.027 |   0     |   0.061 |
| wan22       | indian          | 230 |      0.035 |   0.009 |   0.065 |
| wan22       | latino          | 219 |      0.023 |   0.005 |   0.042 |
| wan22       | mena            | 225 |      0.049 |   0.018 |   0.087 |
| wan22       | southeast_asian | 229 |      0.022 |   0     |   0.048 |
| wan22       | white           | 220 |      0.036 |   0.005 |   0.078 |
| hunyuan15   | black           | 141 |      0     |   0     |   0     |
| hunyuan15   | east_asian      | 141 |      0.007 |   0     |   0.023 |
| hunyuan15   | indian          | 142 |      0     |   0     |   0     |
| hunyuan15   | latino          | 142 |      0     |   0     |   0     |
| hunyuan15   | mena            | 139 |      0     |   0     |   0     |
| hunyuan15   | southeast_asian | 143 |      0     |   0     |   0     |
| hunyuan15   | white           | 141 |      0     |   0     |   0     |
| all         | black           | 628 |      0.018 |   0.002 |   0.037 |
| all         | east_asian      | 637 |      0.017 |   0.003 |   0.038 |
| all         | indian          | 648 |      0.023 |   0.008 |   0.042 |
| all         | latino          | 622 |      0.013 |   0.003 |   0.024 |
| all         | mena            | 630 |      0.04  |   0.017 |   0.066 |
| all         | southeast_asian | 643 |      0.011 |   0.003 |   0.021 |
| all         | white           | 614 |      0.023 |   0.008 |   0.043 |

#### by gender

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | f       |  931 |      0.012 |   0.003 |   0.022 |
| ltx23       | m       |  936 |      0.033 |   0.011 |   0.064 |
| wan22       | f       |  785 |      0.005 |   0     |   0.012 |
| wan22       | m       |  781 |      0.056 |   0.023 |   0.097 |
| hunyuan15   | f       |  495 |      0     |   0     |   0     |
| hunyuan15   | m       |  494 |      0.002 |   0     |   0.007 |
| all         | f       | 2211 |      0.007 |   0.002 |   0.013 |
| all         | m       | 2211 |      0.034 |   0.015 |   0.06  |

#### by age band

| generator   | level   |    n |   estimate |   ci_lo |   ci_hi |
|:------------|:--------|-----:|-----------:|--------:|--------:|
| ltx23       | 18-29   |  464 |      0.019 |   0.006 |   0.037 |
| ltx23       | 30-44   |  469 |      0.028 |   0.008 |   0.053 |
| ltx23       | 45-59   |  477 |      0.025 |   0.01  |   0.044 |
| ltx23       | 60+     |  457 |      0.018 |   0.002 |   0.043 |
| wan22       | 18-29   |  388 |      0.036 |   0.01  |   0.07  |
| wan22       | 30-44   |  377 |      0.045 |   0.017 |   0.079 |
| wan22       | 45-59   |  398 |      0.018 |   0.003 |   0.036 |
| wan22       | 60+     |  403 |      0.025 |   0.003 |   0.056 |
| hunyuan15   | 18-29   |  242 |      0     |   0     |   0     |
| hunyuan15   | 30-44   |  248 |      0.004 |   0     |   0.013 |
| hunyuan15   | 45-59   |  250 |      0     |   0     |   0     |
| hunyuan15   | 60+     |  249 |      0     |   0     |   0     |
| all         | 18-29   | 1094 |      0.021 |   0.007 |   0.038 |
| all         | 30-44   | 1094 |      0.028 |   0.012 |   0.048 |
| all         | 45-59   | 1125 |      0.017 |   0.006 |   0.031 |
| all         | 60+     | 1109 |      0.016 |   0.004 |   0.032 |

### Detection-rate gap at the calibrated threshold

| generator   | attribute        |   gap |   ci_lo |   ci_hi | max_level            | min_level       |
|:------------|:-----------------|------:|--------:|--------:|:---------------------|:----------------|
| ltx23       | race             | 0.045 |   0.018 |   0.089 | mena                 | southeast_asian |
| ltx23       | gender           | 0.021 |   0.002 |   0.048 | m                    | f               |
| ltx23       | age_band         | 0.01  |   0.004 |   0.033 | 30-44                | 60+             |
| ltx23       | cell             | 0.171 |   0.086 |   0.306 | mena__m__45-59       | black__f__18-29 |
| ltx23       | setting          | 0.116 |   0.036 |   0.255 | studio               | classroom       |
| ltx23       | lighting         | 0.042 |   0.022 |   0.151 | softwindow           | harsh           |
| ltx23       | behavior         | 0.106 |   0.028 |   0.204 | smile                | laugh           |
| ltx23       | camera           | 0.024 |   0.001 |   0.061 | static               | slowsway        |
| ltx23       | duration_nominal | 0.022 |   0.001 |   0.061 | 5.0                  | 6.0             |
| wan22       | race             | 0.027 |   0.019 |   0.078 | mena                 | southeast_asian |
| wan22       | gender           | 0.051 |   0.022 |   0.087 | m                    | f               |
| wan22       | age_band         | 0.028 |   0.01  |   0.063 | 30-44                | 45-59           |
| wan22       | cell             | 0.143 |   0.091 |   0.3   | mena__m__18-29       | black__f__18-29 |
| wan22       | setting          | 0.189 |   0.06  |   0.232 | studio               | cafe            |
| wan22       | lighting         | 0.056 |   0.031 |   0.146 | softwindow           | overcast        |
| wan22       | behavior         | 0.105 |   0.049 |   0.195 | smile                | laugh           |
| wan22       | camera           | 0.013 |   0.001 |   0.053 | static               | slowsway        |
| wan22       | duration_nominal | 0.046 |   0.015 |   0.086 | 5.0                  | 6.0             |
| hunyuan15   | race             | 0.007 |   0     |   0.023 | east_asian           | black           |
| hunyuan15   | gender           | 0.002 |   0     |   0.007 | m                    | f               |
| hunyuan15   | age_band         | 0.004 |   0     |   0.013 | 30-44                | 18-29           |
| hunyuan15   | cell             | 0.056 |   0     |   0.188 | east_asian__m__30-44 | black__f__18-29 |
| hunyuan15   | setting          | 0.01  |   0     |   0.018 | studio               | cafe            |
| hunyuan15   | lighting         | 0.006 |   0     |   0.018 | backlit              | harsh           |
| hunyuan15   | behavior         | 0.009 |   0     |   0.018 | think                | laugh           |
| hunyuan15   | camera           | 0.002 |   0     |   0.006 | static               | slowsway        |
| hunyuan15   | duration_nominal | 0.002 |   0     |   0.007 | 5.0                  | 6.0             |
| all         | race             | 0.029 |   0.014 |   0.054 | mena                 | southeast_asian |
| all         | gender           | 0.028 |   0.012 |   0.048 | m                    | f               |
| all         | age_band         | 0.012 |   0.003 |   0.031 | 30-44                | 60+             |
| all         | cell             | 0.099 |   0.058 |   0.177 | mena__m__45-59       | black__f__18-29 |
| all         | setting          | 0.117 |   0.047 |   0.231 | studio               | classroom       |
| all         | lighting         | 0.037 |   0.019 |   0.119 | softwindow           | harsh           |
| all         | behavior         | 0.084 |   0.028 |   0.177 | smile                | laugh           |
| all         | camera           | 0.015 |   0.001 |   0.044 | static               | slowsway        |
| all         | duration_nominal | 0.026 |   0.005 |   0.055 | 5.0                  | 6.0             |

### Flip rate at the calibrated threshold

| generator   |   n_groups |   flip_rate |   ci_lo |   ci_hi |   median |   max |
|:------------|-----------:|------------:|--------:|--------:|---------:|------:|
| ltx23       |         36 |       0.361 |   0.222 |   0.528 |        0 |     1 |
| wan22       |         36 |       0.333 |   0.194 |   0.5   |        0 |     1 |
| hunyuan15   |         18 |       0.056 |   0     |   0.188 |        0 |     1 |

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

