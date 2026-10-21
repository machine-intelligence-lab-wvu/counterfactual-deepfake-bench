
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
