# Filtered vs unfiltered reals — every view

Concatenated from `results/compare/real_all/`. The real-half filter's verdict is kept
per clip, so the same scores are read both ways.


<!-- face512_2s_filtered_vs_unfiltered.md -->

## View `face512_2s`

| detector   | generator        |   n_fake |   n_real_all |   AUC all reals |   n_real_filtered |   AUC filtered reals |
|:-----------|:-----------------|---------:|-------------:|----------------:|------------------:|---------------------:|
| decof      | LTX 2.3          |     1867 |         2206 |           0.813 |              1785 |                0.804 |
| decof      | Wan 2.2          |     1566 |         2206 |           0.509 |              1785 |                0.487 |
| decof      | HunyuanVideo 1.5 |      989 |         2206 |           0.693 |              1785 |                0.677 |
| decof      | all              |     4422 |         2206 |           0.679 |              1785 |                0.664 |
| demamba    | LTX 2.3          |     1867 |         2206 |           0.89  |              1785 |                0.881 |
| demamba    | Wan 2.2          |     1566 |         2206 |           0.983 |              1785 |                0.981 |
| demamba    | HunyuanVideo 1.5 |      989 |         2206 |           0.964 |              1785 |                0.96  |
| demamba    | all              |     4422 |         2206 |           0.937 |              1785 |                0.931 |

Real false-positive rate by perceived subgroup (threshold = 5% FPR over all reals):

| attribute   | level           |   n_clips |   decof |   demamba |
|:------------|:----------------|----------:|--------:|----------:|
| age_band    | 18-29           |       690 |   0.058 |     0.059 |
| age_band    | 30-44           |       759 |   0.052 |     0.049 |
| age_band    | 45-59           |       322 |   0.045 |     0.051 |
| age_band    | 60+             |       312 |   0.019 |     0.05  |
| gender      | f               |       689 |   0.054 |     0.059 |
| gender      | m               |      1512 |   0.048 |     0.046 |
| race        | black           |       189 |   0.032 |     0.082 |
| race        | east_asian      |       190 |   0.037 |     0.016 |
| race        | indian          |        56 |   0.098 |     0.062 |
| race        | latino          |       127 |   0.063 |     0.055 |
| race        | mena            |       129 |   0.074 |     0.008 |
| race        | southeast_asian |        92 |   0.022 |     0.011 |
| race        | white           |      1418 |   0.05  |     0.056 |


<!-- face512_filtered_vs_unfiltered.md -->

## View `face512`

| detector   | generator        |   n_fake |   n_real_all |   AUC all reals |   n_real_filtered |   AUC filtered reals |
|:-----------|:-----------------|---------:|-------------:|----------------:|------------------:|---------------------:|
| decof      | LTX 2.3          |     1874 |          919 |           0.83  |               763 |                0.821 |
| decof      | Wan 2.2          |     1566 |          928 |           0.532 |               772 |                0.511 |
| decof      | HunyuanVideo 1.5 |      989 |          919 |           0.712 |               763 |                0.697 |
| decof      | all              |     4429 |          928 |           0.699 |               772 |                0.684 |
| demamba    | LTX 2.3          |     1874 |          919 |           0.884 |               763 |                0.875 |
| demamba    | Wan 2.2          |     1566 |          928 |           0.984 |               772 |                0.983 |
| demamba    | HunyuanVideo 1.5 |      989 |          919 |           0.968 |               763 |                0.966 |
| demamba    | all              |     4429 |          928 |           0.936 |               772 |                0.931 |

Real false-positive rate by perceived subgroup (threshold = 5% FPR over all reals):

| attribute   | level           |   n_clips |   decof |   demamba |
|:------------|:----------------|----------:|--------:|----------:|
| age_band    | 18-29           |       298 |   0.051 |     0.052 |
| age_band    | 30-44           |       314 |   0.051 |     0.056 |
| age_band    | 45-59           |       151 |   0.037 |     0.047 |
| age_band    | 60+             |       122 |   0.05  |     0.046 |
| gender      | f               |       294 |   0.043 |     0.063 |
| gender      | m               |       631 |   0.053 |     0.045 |
| race        | black           |        62 |   0.016 |     0.049 |
| race        | east_asian      |        82 |   0.043 |     0.018 |
| race        | indian          |        23 |   0.043 |     0.043 |
| race        | latino          |        58 |   0.043 |     0.061 |
| race        | mena            |        60 |   0.125 |     0.025 |
| race        | southeast_asian |        35 |   0     |     0.043 |
| race        | white           |       605 |   0.05  |     0.057 |


<!-- native_up_2s_filtered_vs_unfiltered.md -->

## View `native_up_2s`

| detector   | generator        |   n_fake |   n_real_all |   AUC all reals |   n_real_filtered |   AUC filtered reals |
|:-----------|:-----------------|---------:|-------------:|----------------:|------------------:|---------------------:|
| decof      | LTX 2.3          |     1878 |         2221 |           0.738 |              1785 |                0.727 |
| decof      | Wan 2.2          |     1566 |         2221 |           0.372 |              1785 |                0.353 |
| decof      | HunyuanVideo 1.5 |      989 |         2221 |           0.536 |              1785 |                0.519 |
| decof      | all              |     4433 |         2221 |           0.565 |              1785 |                0.55  |
| demamba    | LTX 2.3          |     1878 |         2221 |           0.897 |              1785 |                0.891 |
| demamba    | Wan 2.2          |     1566 |         2221 |           0.952 |              1785 |                0.949 |
| demamba    | HunyuanVideo 1.5 |      989 |         2221 |           0.96  |              1785 |                0.958 |
| demamba    | all              |     4433 |         2221 |           0.93  |              1785 |                0.926 |

Real false-positive rate by perceived subgroup (threshold = 5% FPR over all reals):

| attribute   | level           |   n_clips |   decof |   demamba |
|:------------|:----------------|----------:|--------:|----------:|
| age_band    | 18-29           |       691 |   0.06  |     0.076 |
| age_band    | 30-44           |       759 |   0.051 |     0.035 |
| age_band    | 45-59           |       322 |   0.042 |     0.045 |
| age_band    | 60+             |       312 |   0.024 |     0.042 |
| gender      | f               |       690 |   0.052 |     0.084 |
| gender      | m               |      1512 |   0.049 |     0.036 |
| race        | black           |       189 |   0.037 |     0.053 |
| race        | east_asian      |       191 |   0.045 |     0.034 |
| race        | indian          |        56 |   0.062 |     0.036 |
| race        | latino          |       127 |   0.055 |     0.051 |
| race        | mena            |       129 |   0.097 |     0.023 |
| race        | southeast_asian |        92 |   0.022 |     0.022 |
| race        | white           |      1418 |   0.049 |     0.058 |


<!-- native_up_filtered_vs_unfiltered.md -->

## View `native_up`

| detector   | generator        |   n_fake |   n_real_all |   AUC all reals |   n_real_filtered |   AUC filtered reals |
|:-----------|:-----------------|---------:|-------------:|----------------:|------------------:|---------------------:|
| decof      | LTX 2.3          |     1878 |          923 |           0.755 |               763 |                0.746 |
| decof      | Wan 2.2          |     1566 |          932 |           0.393 |               772 |                0.375 |
| decof      | HunyuanVideo 1.5 |      989 |          923 |           0.562 |               763 |                0.546 |
| decof      | all              |     4433 |          932 |           0.585 |               772 |                0.571 |
| demamba    | LTX 2.3          |     1878 |          923 |           0.904 |               763 |                0.9   |
| demamba    | Wan 2.2          |     1566 |          932 |           0.961 |               772 |                0.96  |
| demamba    | HunyuanVideo 1.5 |      989 |          923 |           0.967 |               763 |                0.966 |
| demamba    | all              |     4433 |          932 |           0.938 |               772 |                0.935 |

Real false-positive rate by perceived subgroup (threshold = 5% FPR over all reals):

| attribute   | level           |   n_clips |   decof |   demamba |
|:------------|:----------------|----------:|--------:|----------:|
| age_band    | 18-29           |       298 |   0.047 |     0.084 |
| age_band    | 30-44           |       314 |   0.056 |     0.043 |
| age_band    | 45-59           |       151 |   0.04  |     0.03  |
| age_band    | 60+             |       122 |   0.05  |     0.017 |
| gender      | f               |       294 |   0.041 |     0.092 |
| gender      | m               |       631 |   0.055 |     0.03  |
| race        | black           |        62 |   0.016 |     0.049 |
| race        | east_asian      |        82 |   0.049 |     0.043 |
| race        | indian          |        23 |   0     |     0.043 |
| race        | latino          |        58 |   0.061 |     0.009 |
| race        | mena            |        60 |   0.125 |     0.017 |
| race        | southeast_asian |        35 |   0.029 |     0     |
| race        | white           |       605 |   0.049 |     0.061 |
