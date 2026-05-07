# Design Decisions

- Used a reduced-order 1D occupant-airbag model so the full optimization workflow can run on a normal laptop.
- Optimized five deployment variables: trigger delay, early pressure, mid pressure, late pressure, and vent rate.
- Included stochastic crash speed, angle, occupant offset, belt usage, sensor delay, and crash pulse duration to avoid tuning to a single nominal crash.
- Used mean HIC, chest deflection, deployment energy, HIC CVaR90, failure rate, and false deployment rate to balance average performance and tail risk.
- Compared deterministic SQP, grid search, MPC-inspired heuristic control, robust DE+SLSQP, shift-robust DRO, and shift-refined local search.
