# Coverage

Updated 2026-10-20T19:07:40Z. Active batches: fake_b1.
`rendered` = view videos that passed ffprobe verification; `excluded` = clips the view rules exclude (e.g. no face for face512); `pending` = rendered but not yet scored by this detector.

| batch   | detector    | view    | clips   | rendered   | excluded   | render_failed   | scored   | score_failed   | pending                  |
|:--------|:------------|:--------|:--------|:-----------|:-----------|:----------------|:---------|:---------------|:-------------------------|
| fake_b1 | decof       | native  | 4536    | 20         | 0          | 0               | 20       | 0              | 0                        |
| fake_b1 | decof       | face512 | 4536    | 20         | 0          | 0               | 20       | 0              | 0                        |
| fake_b1 | demamba     | native  | 4536    | 20         | 0          | 0               | 0        | 0              | detector not implemented |
| fake_b1 | demamba     | face512 | 4536    | 20         | 0          | 0               | 0        | 0              | detector not implemented |
| fake_b1 | aigvdet     | native  | 4536    | 20         | 0          | 0               | 0        | 0              | detector not implemented |
| fake_b1 | aigvdet     | face512 | 4536    | 20         | 0          | 0               | 0        | 0              | detector not implemented |
| fake_b1 | clip_probe  | native  | 4536    | 20         | 0          | 0               | 0        | 0              | detector not implemented |
| fake_b1 | clip_probe  | face512 | 4536    | 20         | 0          | 0               | 0        | 0              | detector not implemented |
| fake_b1 | altfreezing | native  | 4536    | 20         | 0          | 0               | 0        | 0              | detector not implemented |
| fake_b1 | altfreezing | face512 | 4536    | 20         | 0          | 0               | 0        | 0              | detector not implemented |
| fake_b2 | decof       | native  | -       | -          | -          | -               | -        | -              | batch pending            |
| fake_b2 | decof       | face512 | -       | -          | -          | -               | -        | -              | batch pending            |
| fake_b2 | demamba     | native  | -       | -          | -          | -               | -        | -              | batch pending            |
| fake_b2 | demamba     | face512 | -       | -          | -          | -               | -        | -              | batch pending            |
| fake_b2 | aigvdet     | native  | -       | -          | -          | -               | -        | -              | batch pending            |
| fake_b2 | aigvdet     | face512 | -       | -          | -          | -               | -        | -              | batch pending            |
| fake_b2 | clip_probe  | native  | -       | -          | -          | -               | -        | -              | batch pending            |
| fake_b2 | clip_probe  | face512 | -       | -          | -          | -               | -        | -              | batch pending            |
| fake_b2 | altfreezing | native  | -       | -          | -          | -               | -        | -              | batch pending            |
| fake_b2 | altfreezing | face512 | -       | -          | -          | -               | -        | -              | batch pending            |
| real_b1 | decof       | native  | -       | -          | -          | -               | -        | -              | batch pending            |
| real_b1 | decof       | face512 | -       | -          | -          | -               | -        | -              | batch pending            |
| real_b1 | demamba     | native  | -       | -          | -          | -               | -        | -              | batch pending            |
| real_b1 | demamba     | face512 | -       | -          | -          | -               | -        | -              | batch pending            |
| real_b1 | aigvdet     | native  | -       | -          | -          | -               | -        | -              | batch pending            |
| real_b1 | aigvdet     | face512 | -       | -          | -          | -               | -        | -              | batch pending            |
| real_b1 | clip_probe  | native  | -       | -          | -          | -               | -        | -              | batch pending            |
| real_b1 | clip_probe  | face512 | -       | -          | -          | -               | -        | -              | batch pending            |
| real_b1 | altfreezing | native  | -       | -          | -          | -               | -        | -              | batch pending            |
| real_b1 | altfreezing | face512 | -       | -          | -          | -               | -        | -              | batch pending            |
