
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
