| method | type | runtime_s | objective | hic_mean | hic_std | hic_cvar90 | chest_mean_mm | chest_std_mm | failure_rate_pct | false_deployment_rate_pct | energy_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Initial Design | reference | 0.000 | 0.431 | 259.890 | 248.290 | 811.400 | 35.230 | 14.910 | 16.000 | 1.670 | 0.442 |
| Deterministic SQP | baseline_fixed | 0.062 | 0.431 | 259.850 | 248.250 | 811.400 | 35.230 | 14.910 | 16.000 | 1.670 | 0.442 |
| Grid Search | baseline_fixed | 74.180 | 0.379 | 249.090 | 229.380 | 752.150 | 34.600 | 14.670 | 14.330 | 1.670 | 0.101 |
| MPC-Inspired Policy | adaptive_policy | 0.874 | 0.415 | 247.590 | 225.720 | 751.790 | 35.690 | 15.180 | 12.670 | 1.670 | 0.596 |
| Robust DE+SLSQP | robust_fixed | 200.507 | 0.356 | 230.410 | 216.600 | 706.290 | 34.860 | 14.880 | 11.670 | 1.670 | 0.106 |
| Shift-Robust DRO | robust_shift_aware | 342.423 | 0.367 | 238.520 | 218.310 | 714.410 | 34.740 | 14.760 | 12.670 | 1.670 | 0.150 |
| Shift-Refined Local Search | robust_local_refinement | 85.115 | 0.352 | 226.520 | 210.640 | 691.210 | 35.140 | 14.980 | 11.000 | 1.670 | 0.106 |
