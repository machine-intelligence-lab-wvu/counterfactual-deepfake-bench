# Coverage

Updated 2026-10-21T15:54:26Z. Active batches: fake_b1, fake_b2, real_all.
`rendered` = view videos that passed ffprobe verification; `excluded` = clips the view rules exclude (e.g. no face for face512); `pending` = rendered but not yet scored by this detector.

| batch    | detector    | view       | clips               |   rendered |   excluded |   render_failed |   scored |   score_failed | pending                  |
|:---------|:------------|:-----------|:--------------------|-----------:|-----------:|----------------:|---------:|---------------:|:-------------------------|
| fake_b1  | decof       | native     | 4536                |       4536 |          0 |               0 |     4536 |              0 | 0                        |
| fake_b1  | decof       | face512    | 4536                |       4532 |          4 |               0 |     4532 |              0 | 0                        |
| fake_b1  | decof       | native_2s  | 4536                |       4536 |          0 |               0 |     4536 |              0 | 0                        |
| fake_b1  | decof       | face512_2s | 4536                |       4525 |         11 |               0 |     4525 |              0 | 0                        |
| fake_b1  | demamba     | native     | 4536                |       4536 |          0 |               0 |     4536 |              0 | 0                        |
| fake_b1  | demamba     | face512    | 4536                |       4532 |          4 |               0 |     4532 |              0 | 0                        |
| fake_b1  | demamba     | native_2s  | 4536                |       4536 |          0 |               0 |     4536 |              0 | 0                        |
| fake_b1  | demamba     | face512_2s | 4536                |       4525 |         11 |               0 |     4525 |              0 | 0                        |
| fake_b1  | aigvdet     | native     | 4536                |       4536 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b1  | aigvdet     | face512    | 4536                |       4532 |          4 |               0 |        0 |              0 | detector not implemented |
| fake_b1  | aigvdet     | native_2s  | 4536                |       4536 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b1  | aigvdet     | face512_2s | 4536                |       4525 |         11 |               0 |        0 |              0 | detector not implemented |
| fake_b1  | clip_probe  | native     | 4536                |       4536 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b1  | clip_probe  | face512    | 4536                |       4532 |          4 |               0 |        0 |              0 | detector not implemented |
| fake_b1  | clip_probe  | native_2s  | 4536                |       4536 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b1  | clip_probe  | face512_2s | 4536                |       4525 |         11 |               0 |        0 |              0 | detector not implemented |
| fake_b1  | altfreezing | native     | 4536                |       4536 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b1  | altfreezing | face512    | 4536                |       4532 |          4 |               0 |        0 |              0 | detector not implemented |
| fake_b1  | altfreezing | native_2s  | 4536                |       4536 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b1  | altfreezing | face512_2s | 4536                |       4525 |         11 |               0 |        0 |              0 | detector not implemented |
| fake_b2  | decof       | native     | 504                 |        504 |          0 |               0 |      504 |              0 | 0                        |
| fake_b2  | decof       | face512    | 504                 |        504 |          0 |               0 |      504 |              0 | 0                        |
| fake_b2  | decof       | native_2s  | 504                 |        504 |          0 |               0 |      504 |              0 | 0                        |
| fake_b2  | decof       | face512_2s | 504                 |        504 |          0 |               0 |      504 |              0 | 0                        |
| fake_b2  | demamba     | native     | 504                 |        504 |          0 |               0 |      504 |              0 | 0                        |
| fake_b2  | demamba     | face512    | 504                 |        504 |          0 |               0 |      504 |              0 | 0                        |
| fake_b2  | demamba     | native_2s  | 504                 |        504 |          0 |               0 |      504 |              0 | 0                        |
| fake_b2  | demamba     | face512_2s | 504                 |        504 |          0 |               0 |      504 |              0 | 0                        |
| fake_b2  | aigvdet     | native     | 504                 |        504 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b2  | aigvdet     | face512    | 504                 |        504 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b2  | aigvdet     | native_2s  | 504                 |        504 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b2  | aigvdet     | face512_2s | 504                 |        504 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b2  | clip_probe  | native     | 504                 |        504 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b2  | clip_probe  | face512    | 504                 |        504 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b2  | clip_probe  | native_2s  | 504                 |        504 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b2  | clip_probe  | face512_2s | 504                 |        504 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b2  | altfreezing | native     | 504                 |        504 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b2  | altfreezing | face512    | 504                 |        504 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b2  | altfreezing | native_2s  | 504                 |        504 |          0 |               0 |        0 |              0 | detector not implemented |
| fake_b2  | altfreezing | face512_2s | 504                 |        504 |          0 |               0 |        0 |              0 | detector not implemented |
| real_b1  | decof       | native     | 1785 (3570 renders) |          0 |       3570 |               0 |        0 |              0 | 0                        |
| real_b1  | decof       | face512    | 1785 (3570 renders) |       1306 |       2216 |              48 |     1306 |              0 | 0                        |
| real_b1  | decof       | native_2s  | 1785 (3570 renders) |          0 |       3570 |               0 |        0 |              0 | 0                        |
| real_b1  | decof       | face512_2s | 1785 (3570 renders) |       3536 |          0 |              34 |     3536 |              0 | 0                        |
| real_b1  | demamba     | native     | 1785 (3570 renders) |          0 |       3570 |               0 |        0 |              0 | 0                        |
| real_b1  | demamba     | face512    | 1785 (3570 renders) |       1306 |       2216 |              48 |     1306 |              0 | 0                        |
| real_b1  | demamba     | native_2s  | 1785 (3570 renders) |          0 |       3570 |               0 |        0 |              0 | 0                        |
| real_b1  | demamba     | face512_2s | 1785 (3570 renders) |       3536 |          0 |              34 |     3536 |              0 | 0                        |
| real_b1  | aigvdet     | native     | 1785 (3570 renders) |          0 |       3570 |               0 |        0 |              0 | detector not implemented |
| real_b1  | aigvdet     | face512    | 1785 (3570 renders) |       1306 |       2216 |              48 |        0 |              0 | detector not implemented |
| real_b1  | aigvdet     | native_2s  | 1785 (3570 renders) |          0 |       3570 |               0 |        0 |              0 | detector not implemented |
| real_b1  | aigvdet     | face512_2s | 1785 (3570 renders) |       3536 |          0 |              34 |        0 |              0 | detector not implemented |
| real_b1  | clip_probe  | native     | 1785 (3570 renders) |          0 |       3570 |               0 |        0 |              0 | detector not implemented |
| real_b1  | clip_probe  | face512    | 1785 (3570 renders) |       1306 |       2216 |              48 |        0 |              0 | detector not implemented |
| real_b1  | clip_probe  | native_2s  | 1785 (3570 renders) |          0 |       3570 |               0 |        0 |              0 | detector not implemented |
| real_b1  | clip_probe  | face512_2s | 1785 (3570 renders) |       3536 |          0 |              34 |        0 |              0 | detector not implemented |
| real_b1  | altfreezing | native     | 1785 (3570 renders) |          0 |       3570 |               0 |        0 |              0 | detector not implemented |
| real_b1  | altfreezing | face512    | 1785 (3570 renders) |       1306 |       2216 |              48 |        0 |              0 | detector not implemented |
| real_b1  | altfreezing | native_2s  | 1785 (3570 renders) |          0 |       3570 |               0 |        0 |              0 | detector not implemented |
| real_b1  | altfreezing | face512_2s | 1785 (3570 renders) |       3536 |          0 |              34 |        0 |              0 | detector not implemented |
| real_all | decof       | native     | 2221 (4442 renders) |          0 |          0 |               0 |        0 |              0 | 0                        |
| real_all | decof       | face512    | 2221 (4442 renders) |       1847 |       2558 |              37 |     1847 |              0 | 0                        |
| real_all | decof       | native_2s  | 2221 (4442 renders) |          0 |          0 |               0 |        0 |              0 | 0                        |
| real_all | decof       | face512_2s | 2221 (4442 renders) |       4412 |         30 |               0 |     4412 |              0 | 0                        |
| real_all | demamba     | native     | 2221 (4442 renders) |          0 |          0 |               0 |        0 |              0 | 0                        |
| real_all | demamba     | face512    | 2221 (4442 renders) |       1847 |       2558 |              37 |     1847 |              0 | 0                        |
| real_all | demamba     | native_2s  | 2221 (4442 renders) |          0 |          0 |               0 |        0 |              0 | 0                        |
| real_all | demamba     | face512_2s | 2221 (4442 renders) |       4412 |         30 |               0 |     4412 |              0 | 0                        |
| real_all | aigvdet     | native     | 2221 (4442 renders) |          0 |          0 |               0 |        0 |              0 | detector not implemented |
| real_all | aigvdet     | face512    | 2221 (4442 renders) |       1847 |       2558 |              37 |        0 |              0 | detector not implemented |
| real_all | aigvdet     | native_2s  | 2221 (4442 renders) |          0 |          0 |               0 |        0 |              0 | detector not implemented |
| real_all | aigvdet     | face512_2s | 2221 (4442 renders) |       4412 |         30 |               0 |        0 |              0 | detector not implemented |
| real_all | clip_probe  | native     | 2221 (4442 renders) |          0 |          0 |               0 |        0 |              0 | detector not implemented |
| real_all | clip_probe  | face512    | 2221 (4442 renders) |       1847 |       2558 |              37 |        0 |              0 | detector not implemented |
| real_all | clip_probe  | native_2s  | 2221 (4442 renders) |          0 |          0 |               0 |        0 |              0 | detector not implemented |
| real_all | clip_probe  | face512_2s | 2221 (4442 renders) |       4412 |         30 |               0 |        0 |              0 | detector not implemented |
| real_all | altfreezing | native     | 2221 (4442 renders) |          0 |          0 |               0 |        0 |              0 | detector not implemented |
| real_all | altfreezing | face512    | 2221 (4442 renders) |       1847 |       2558 |              37 |        0 |              0 | detector not implemented |
| real_all | altfreezing | native_2s  | 2221 (4442 renders) |          0 |          0 |               0 |        0 |              0 | detector not implemented |
| real_all | altfreezing | face512_2s | 2221 (4442 renders) |       4412 |         30 |               0 |        0 |              0 | detector not implemented |
