| method | design_type | trigger_delay_ms | pressure_early_kpa | pressure_mid_kpa | pressure_late_kpa | vent_rate |
| --- | --- | --- | --- | --- | --- | --- |
| Initial Design | fixed | 18.000 | 220.000 | 190.000 | 140.000 | 18.000 |
| Deterministic SQP | fixed | 18.021 | 220.000 | 190.000 | 140.000 | 18.000 |
| Grid Search | fixed | 16.000 | 300.000 | 300.000 | 100.000 | 4.000 |
| MPC-Inspired Policy | adaptive_mean | 14.451 | 157.179 | 268.390 | 177.301 | 19.393 |
| Robust DE+SLSQP | fixed | 25.893 | 299.164 | 286.950 | 102.732 | 4.412 |
| Shift-Robust DRO | fixed | 20.061 | 298.501 | 299.376 | 104.210 | 6.002 |
| Shift-Refined Local Search | fixed | 25.393 | 300.000 | 300.000 | 120.732 | 4.000 |
