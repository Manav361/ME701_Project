| method | type | runtime_s | objective | hic_mean | hic_std | hic_cvar90 | chest_mean_mm | chest_std_mm | failure_rate_pct | false_deployment_rate_pct | energy_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Initial Design | reference | 0.000 | 0.892 | 444.160 | 371.340 | 1312.550 | 44.130 | 13.760 | 32.000 | 1.000 | 0.500 |
| Deterministic SQP | baseline_fixed | 0.062 | 0.891 | 443.960 | 370.960 | 1311.020 | 44.130 | 13.760 | 32.000 | 1.000 | 0.500 |
| Grid Search | baseline_fixed | 74.180 | 0.738 | 401.870 | 322.900 | 1153.820 | 43.500 | 13.680 | 28.670 | 1.000 | 0.113 |
| MPC-Inspired Policy | adaptive_policy | 0.893 | 0.766 | 412.990 | 331.570 | 1189.620 | 44.700 | 14.030 | 27.330 | 1.000 | 0.649 |
| Robust DE+SLSQP | robust_fixed | 200.507 | 0.589 | 377.170 | 318.340 | 1144.520 | 43.930 | 14.050 | 21.000 | 1.000 | 0.120 |
| Shift-Robust DRO | robust_shift_aware | 342.423 | 0.658 | 386.900 | 314.020 | 1126.580 | 43.720 | 13.840 | 25.000 | 1.000 | 0.169 |
| Shift-Refined Local Search | robust_local_refinement | 85.115 | 0.579 | 372.210 | 317.470 | 1142.550 | 44.200 | 14.110 | 20.330 | 1.000 | 0.119 |
