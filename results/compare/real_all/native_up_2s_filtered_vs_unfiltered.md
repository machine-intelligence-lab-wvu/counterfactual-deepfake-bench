
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
