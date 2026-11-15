# B1's cells again, under version 1.1, draft 3 · 15 November 2026 · a check, never a result

All 240 of B1's runs, on B1's own seeds, by B1's own runner and judge (`world/b1/run_b1.py` and `judge.py`, as on main),
with the engines of `wc/b2-points-20-22` at commit fa05337: version 1.1, draft 3, where points 19 and 22 only shorten
a span. The reference's 208 cells on seeds 1 to 100; the second engine's 32 on seeds 100,001 to 100,100. B1's record
stands as run, and nothing here is a result.

- **The 104 cells that could fire, and the second engine's 32:** all 136 give B1's zone, B1's judgement and B1's
  measure, seed by seed. B1's judge gives all 104 "B1 holds in this cell, and the switches hold", and the engines
  agree in all 32.
- **The 104 controls:** 23 give B1's measure seed by seed. The other 81 moved, and every seed that moved, moved upward.
  - Judged: 66 "a defector lasts", 36 "no defector lasts", 2 "settles nothing", as under draft 2. B1's record has 56
    and 48. The 12 that moved from B1's judgement are draft 2's 12.
  - 103 give draft 2's measure seed by seed. The one that does not, `b1-ring-1D-m2-s05-more-control`, moved from
    1.90207 to 1.90216 and still reads "no defector lasts": in seeds 18 and 95, draft 2's point 22 had lengthened the
    span of the seed's largest configuration, and now that seed gives B1's own figure again.
  - Seeds left out, too long to judge: 36 in all, as in B1's record and under draft 2.
- **The points, in the reference's 208 cells:**
  - **The 104 controls:** point 22 applied 27,572 times and was left 8,512 times, the counterparties' span being the
    longer; draft 2 applied it 36,084 times. Point 19 applied 8,071 times and was left 1,326 times; B1's record, at
    version 1.0, applied it 9,397 times, so 1,326 of those had lengthened a span.
  - **The 104 that could fire:** point 22 applied 5,830 times and was left 20,746 times (draft 2: 26,576). Point 19
    never applied. No measure moved.
  - **Point 21** applied nowhere.
- **The judge's heading line** says "Reference engine at world-ref-v1.0": those are the judge's own fixed words. The
  engines here are draft 3's.

## The files

- `compare_b1.json`: every cell, B1's record, draft 2 and draft 3 side by side, by `../compare_b1.py`.
- `judgement-under-draft-3.json` and `.md`: B1's judge on these runs.
- `run.log`; `manifest.sha256`, the fingerprints of all 928 files of the runs. Those, 2.8 GB, are kept on WC's
  computer at `…\b1-rerun-d3\runs`.

## The 104 controls' figures

A judgement in bold is not B1's. "No, upward": the measure moved in some seeds, and every one of them moved upward.

| Control | B1: mean (SE) | B1's judgement | Draft 3: mean (SE) | Draft 3's judgement | Seeds measured, left out | Seed by seed as B1 |
|---|---|---|---|---|---|---|
| entry-ring-1D-m3-s0-more | 89.440 (9.458) | a defector lasts | 139.070 (8.808) | a defector lasts | 95, 5 | no, upward |
| entry-ring-1D-m3-s0-quiet | 92.567 (8.902) | a defector lasts | 135.378 (9.233) | a defector lasts | 97, 3 | no, upward |
| entry-ring-1D-m3-s0-reading | 82.074 (6.016) | a defector lasts | 122.431 (4.004) | a defector lasts | 95, 5 | no, upward |
| entry-ring-1D-m3-s0-some | 84.146 (9.071) | a defector lasts | 135.244 (8.412) | a defector lasts | 97, 3 | no, upward |
| entry-ring-1D-m3-s05-more | 75.457 (7.044) | a defector lasts | 133.339 (14.768) | a defector lasts | 95, 5 | no, upward |
| entry-ring-1D-m3-s05-quiet | 66.906 (4.524) | a defector lasts | 113.433 (7.443) | a defector lasts | 96, 4 | no, upward |
| entry-ring-1D-m3-s05-reading | 83.507 (5.701) | a defector lasts | 111.883 (4.779) | a defector lasts | 96, 4 | no, upward |
| entry-ring-1D-m3-s05-some | 77.629 (7.301) | a defector lasts | 137.610 (14.411) | a defector lasts | 96, 4 | no, upward |
| random-1D-m2-s0-more | 132.116 (8.507) | a defector lasts | 132.690 (8.423) | a defector lasts | 98, 0 | no, upward |
| random-1D-m2-s0-quiet | 158.309 (21.679) | a defector lasts | 158.355 (21.676) | a defector lasts | 98, 0 | no, upward |
| random-1D-m2-s0-reading | 158.309 (21.679) | a defector lasts | 158.355 (21.676) | a defector lasts | 98, 0 | no, upward |
| random-1D-m2-s0-some | 143.534 (9.511) | a defector lasts | 143.631 (9.496) | a defector lasts | 98, 0 | no, upward |
| random-1D-m2-s05-more | 117.368 (6.182) | a defector lasts | 118.507 (6.007) | a defector lasts | 98, 0 | no, upward |
| random-1D-m2-s05-quiet | 116.971 (5.428) | a defector lasts | 116.971 (5.428) | a defector lasts | 98, 0 | yes |
| random-1D-m2-s05-reading | 116.971 (5.428) | a defector lasts | 116.971 (5.428) | a defector lasts | 98, 0 | yes |
| random-1D-m2-s05-some | 116.823 (5.254) | a defector lasts | 116.823 (5.254) | a defector lasts | 98, 0 | yes |
| random-1D-m3-s0-more | 117.511 (10.668) | a defector lasts | 117.606 (10.657) | a defector lasts | 98, 0 | no, upward |
| random-1D-m3-s0-quiet | 136.617 (8.895) | a defector lasts | 136.632 (8.893) | a defector lasts | 98, 0 | no, upward |
| random-1D-m3-s0-reading | 136.617 (8.895) | a defector lasts | 136.632 (8.893) | a defector lasts | 98, 0 | no, upward |
| random-1D-m3-s0-some | 116.882 (9.785) | a defector lasts | 117.418 (9.733) | a defector lasts | 98, 0 | no, upward |
| random-1D-m3-s05-more | 120.779 (9.776) | a defector lasts | 121.113 (9.742) | a defector lasts | 97, 1 | no, upward |
| random-1D-m3-s05-quiet | 139.454 (8.522) | a defector lasts | 139.463 (8.520) | a defector lasts | 98, 0 | no, upward |
| random-1D-m3-s05-reading | 139.454 (8.522) | a defector lasts | 139.463 (8.520) | a defector lasts | 98, 0 | no, upward |
| random-1D-m3-s05-some | 132.516 (8.703) | a defector lasts | 132.691 (8.677) | a defector lasts | 98, 0 | no, upward |
| random-1D-m4-s0-more | 109.963 (8.455) | a defector lasts | 109.987 (8.452) | a defector lasts | 98, 0 | no, upward |
| random-1D-m4-s0-quiet | 113.061 (9.165) | a defector lasts | 113.085 (9.162) | a defector lasts | 98, 0 | no, upward |
| random-1D-m4-s0-reading | 113.061 (9.165) | a defector lasts | 113.085 (9.162) | a defector lasts | 98, 0 | no, upward |
| random-1D-m4-s0-some | 112.235 (8.560) | a defector lasts | 112.259 (8.557) | a defector lasts | 98, 0 | no, upward |
| random-1D-m4-s05-more | 109.484 (8.395) | a defector lasts | 109.548 (8.387) | a defector lasts | 98, 0 | no, upward |
| random-1D-m4-s05-quiet | 116.132 (7.118) | a defector lasts | 116.145 (7.116) | a defector lasts | 98, 0 | no, upward |
| random-1D-m4-s05-reading | 116.132 (7.118) | a defector lasts | 116.145 (7.116) | a defector lasts | 98, 0 | no, upward |
| random-1D-m4-s05-some | 108.838 (7.842) | a defector lasts | 108.906 (7.833) | a defector lasts | 98, 0 | no, upward |
| random-3D-m2-s0-more | 193.984 (13.659) | a defector lasts | 197.698 (13.266) | a defector lasts | 100, 0 | no, upward |
| random-3D-m2-s0-quiet | 194.925 (11.479) | a defector lasts | 195.802 (11.332) | a defector lasts | 100, 0 | no, upward |
| random-3D-m2-s0-reading | 194.925 (11.479) | a defector lasts | 195.802 (11.332) | a defector lasts | 100, 0 | no, upward |
| random-3D-m2-s0-some | 193.343 (12.078) | a defector lasts | 193.975 (11.977) | a defector lasts | 100, 0 | no, upward |
| random-3D-m2-s05-more | 159.107 (8.992) | a defector lasts | 162.229 (8.473) | a defector lasts | 100, 0 | no, upward |
| random-3D-m2-s05-quiet | 217.076 (16.329) | a defector lasts | 217.076 (16.329) | a defector lasts | 100, 0 | yes |
| random-3D-m2-s05-reading | 217.076 (16.329) | a defector lasts | 217.076 (16.329) | a defector lasts | 100, 0 | yes |
| random-3D-m2-s05-some | 233.331 (32.739) | a defector lasts | 237.459 (32.760) | a defector lasts | 100, 0 | no, upward |
| random-3D-m3-s0-more | 194.330 (14.027) | a defector lasts | 194.330 (14.027) | a defector lasts | 100, 0 | yes |
| random-3D-m3-s0-quiet | 207.752 (16.818) | a defector lasts | 207.752 (16.818) | a defector lasts | 100, 0 | yes |
| random-3D-m3-s0-reading | 207.752 (16.818) | a defector lasts | 207.752 (16.818) | a defector lasts | 100, 0 | yes |
| random-3D-m3-s0-some | 191.606 (17.763) | a defector lasts | 193.433 (17.682) | a defector lasts | 100, 0 | no, upward |
| random-3D-m3-s05-more | 188.650 (12.255) | a defector lasts | 189.015 (12.229) | a defector lasts | 98, 2 | no, upward |
| random-3D-m3-s05-quiet | 195.756 (14.564) | a defector lasts | 195.756 (14.564) | a defector lasts | 100, 0 | yes |
| random-3D-m3-s05-reading | 195.756 (14.564) | a defector lasts | 195.756 (14.564) | a defector lasts | 100, 0 | yes |
| random-3D-m3-s05-some | 194.706 (14.506) | a defector lasts | 194.706 (14.506) | a defector lasts | 100, 0 | yes |
| random-3D-m4-s0-more | 167.471 (14.653) | a defector lasts | 167.748 (14.630) | a defector lasts | 100, 0 | no, upward |
| random-3D-m4-s0-quiet | 174.061 (14.528) | a defector lasts | 174.061 (14.528) | a defector lasts | 100, 0 | yes |
| random-3D-m4-s0-reading | 174.061 (14.528) | a defector lasts | 174.061 (14.528) | a defector lasts | 100, 0 | yes |
| random-3D-m4-s0-some | 171.486 (14.304) | a defector lasts | 171.991 (14.279) | a defector lasts | 100, 0 | no, upward |
| random-3D-m4-s05-more | 164.973 (12.537) | a defector lasts | 164.973 (12.537) | a defector lasts | 100, 0 | yes |
| random-3D-m4-s05-quiet | 180.994 (13.580) | a defector lasts | 180.994 (13.580) | a defector lasts | 100, 0 | yes |
| random-3D-m4-s05-reading | 180.994 (13.580) | a defector lasts | 180.994 (13.580) | a defector lasts | 100, 0 | yes |
| random-3D-m4-s05-some | 230.744 (67.795) | a defector lasts | 230.744 (67.795) | a defector lasts | 100, 0 | yes |
| ring-1D-m2-s0-more | 0.486 (0.009) | no defector lasts | 0.826 (0.047) | no defector lasts | 100, 0 | no, upward |
| ring-1D-m2-s0-quiet | 0.449 (0.000) | no defector lasts | 0.449 (0.000) | no defector lasts | 100, 0 | yes |
| ring-1D-m2-s0-reading | 0.449 (0.000) | no defector lasts | 0.449 (0.000) | no defector lasts | 100, 0 | yes |
| ring-1D-m2-s0-some | 0.466 (0.004) | no defector lasts | 0.803 (0.043) | no defector lasts | 100, 0 | no, upward |
| ring-1D-m2-s05-more | 0.316 (0.006) | no defector lasts | 1.902 (0.196) | no defector lasts | 100, 0 | no, upward |
| ring-1D-m2-s05-quiet | 0.295 (0.000) | no defector lasts | 0.546 (0.000) | no defector lasts | 100, 0 | no, upward |
| ring-1D-m2-s05-reading | 0.295 (0.000) | no defector lasts | 0.546 (0.000) | no defector lasts | 100, 0 | no, upward |
| ring-1D-m2-s05-some | 0.308 (0.004) | no defector lasts | 1.811 (0.151) | no defector lasts | 100, 0 | no, upward |
| ring-1D-m3-s0-more | 0.312 (0.004) | no defector lasts | 1.705 (0.118) | no defector lasts | 100, 0 | no, upward |
| ring-1D-m3-s0-quiet | 0.293 (0.000) | no defector lasts | 0.900 (0.000) | no defector lasts | 100, 0 | no, upward |
| ring-1D-m3-s0-reading | 0.293 (0.000) | no defector lasts | 0.900 (0.000) | no defector lasts | 100, 0 | no, upward |
| ring-1D-m3-s0-some | 0.302 (0.002) | no defector lasts | 1.618 (0.113) | no defector lasts | 100, 0 | no, upward |
| ring-1D-m3-s05-more | 0.201 (0.004) | no defector lasts | 4.248 (0.438) | **a defector lasts** | 100, 0 | no, upward |
| ring-1D-m3-s05-quiet | 0.178 (0.000) | no defector lasts | 1.221 (0.000) | no defector lasts | 100, 0 | no, upward |
| ring-1D-m3-s05-reading | 0.178 (0.000) | no defector lasts | 1.221 (0.000) | no defector lasts | 100, 0 | no, upward |
| ring-1D-m3-s05-some | 0.188 (0.002) | no defector lasts | 4.043 (0.339) | **a defector lasts** | 100, 0 | no, upward |
| ring-1D-m4-s0-more | 0.475 (0.026) | no defector lasts | 3.025 (0.209) | **settles nothing** | 100, 0 | no, upward |
| ring-1D-m4-s0-quiet | 1.597 (0.000) | no defector lasts | 1.597 (0.000) | no defector lasts | 100, 0 | yes |
| ring-1D-m4-s0-reading | 1.597 (0.000) | no defector lasts | 1.597 (0.000) | no defector lasts | 100, 0 | yes |
| ring-1D-m4-s0-some | 0.627 (0.024) | no defector lasts | 2.871 (0.200) | **settles nothing** | 100, 0 | no, upward |
| ring-1D-m4-s05-more | 0.678 (0.037) | no defector lasts | 7.538 (0.778) | **a defector lasts** | 100, 0 | no, upward |
| ring-1D-m4-s05-quiet | 2.167 (0.000) | no defector lasts | 2.167 (0.000) | no defector lasts | 100, 0 | yes |
| ring-1D-m4-s05-reading | 2.167 (0.000) | no defector lasts | 2.167 (0.000) | no defector lasts | 100, 0 | yes |
| ring-1D-m4-s05-some | 0.923 (0.029) | no defector lasts | 7.174 (0.602) | **a defector lasts** | 100, 0 | no, upward |
| ring-3D-m2-s0-more | 0.604 (0.011) | no defector lasts | 1.037 (0.050) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m2-s0-quiet | 0.516 (0.006) | no defector lasts | 0.558 (0.010) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m2-s0-reading | 0.516 (0.006) | no defector lasts | 0.558 (0.010) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m2-s0-some | 0.562 (0.007) | no defector lasts | 1.048 (0.070) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m2-s05-more | 0.434 (0.010) | no defector lasts | 1.864 (0.118) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m2-s05-quiet | 0.360 (0.006) | no defector lasts | 0.699 (0.021) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m2-s05-reading | 0.360 (0.006) | no defector lasts | 0.699 (0.021) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m2-s05-some | 0.396 (0.006) | no defector lasts | 2.278 (0.272) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m3-s0-more | 0.401 (0.007) | no defector lasts | 2.169 (0.119) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m3-s0-quiet | 0.359 (0.006) | no defector lasts | 1.020 (0.017) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m3-s0-reading | 0.359 (0.006) | no defector lasts | 1.020 (0.017) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m3-s0-some | 0.379 (0.006) | no defector lasts | 2.235 (0.162) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m3-s05-more | 0.267 (0.005) | no defector lasts | 4.022 (0.267) | **a defector lasts** | 100, 0 | no, upward |
| ring-3D-m3-s05-quiet | 0.234 (0.005) | no defector lasts | 1.413 (0.027) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m3-s05-reading | 0.234 (0.005) | no defector lasts | 1.413 (0.027) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m3-s05-some | 0.251 (0.005) | no defector lasts | 5.044 (0.612) | **a defector lasts** | 100, 0 | no, upward |
| ring-3D-m4-s0-more | 0.561 (0.019) | no defector lasts | 3.800 (0.216) | **a defector lasts** | 100, 0 | no, upward |
| ring-3D-m4-s0-quiet | 1.496 (0.034) | no defector lasts | 1.734 (0.019) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m4-s0-reading | 1.496 (0.034) | no defector lasts | 1.734 (0.019) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m4-s0-some | 0.642 (0.020) | no defector lasts | 4.097 (0.334) | **a defector lasts** | 100, 0 | no, upward |
| ring-3D-m4-s05-more | 0.725 (0.032) | no defector lasts | 7.076 (0.487) | **a defector lasts** | 100, 0 | no, upward |
| ring-3D-m4-s05-quiet | 2.014 (0.052) | no defector lasts | 2.378 (0.030) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m4-s05-reading | 2.014 (0.052) | no defector lasts | 2.378 (0.030) | no defector lasts | 100, 0 | no, upward |
| ring-3D-m4-s05-some | 0.905 (0.029) | no defector lasts | 8.990 (1.088) | **a defector lasts** | 100, 0 | no, upward |
