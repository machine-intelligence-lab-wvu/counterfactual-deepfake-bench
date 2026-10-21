
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
