# Design Decisions

This file records the main modeling and implementation decisions behind the project. The goal is to make the workflow traceable from problem formulation to final results.

## 1. Use a Reduced-Order Crash Simulator

**Decision:** Use a simplified one-dimensional occupant-restraint simulator instead of a full finite-element or multibody crash model.

**Reason:** A high-fidelity crash model would require proprietary geometry, material data, calibration, and large compute resources. The course project needed a model that could be run repeatedly inside an optimization loop on a normal laptop.

**Implementation location:**

- `3_Code/src/airbag_project/simulator.py`
- `3_Code/src/airbag_project/config.py`

**Model components included:**

- occupant forward excursion
- seatbelt slack, stiffness, damping, and load limiting
- pretensioner action
- airbag pressure build-up
- airbag venting
- torso and head contact with the airbag
- hard-stop contact for severe cases
- HIC proxy from filtered head acceleration
- chest deflection proxy

**Consequence:** The model is useful for comparing optimization methods, but the results should not be interpreted as certified real-world safety predictions.

## 2. Optimize Deployment Parameters, Not Vehicle Structure

**Decision:** Optimize five airbag deployment parameters:

| Variable | Meaning | Bounds |
| --- | --- | --- |
| `trigger_delay_ms` | delay before deployment | 5 to 40 ms |
| `pressure_early_kpa` | early inflation pressure | 100 to 300 kPa |
| `pressure_mid_kpa` | middle inflation pressure | 100 to 300 kPa |
| `pressure_late_kpa` | late inflation pressure | 100 to 300 kPa |
| `vent_rate` | airbag venting rate | 4 to 45 |

**Reason:** These variables are directly related to deployment timing, restraint aggressiveness, and pressure release. They are also continuous and bounded, making them appropriate for simulation-based optimization.

**Implementation location:**

- `3_Code/src/airbag_project/simulator.py`
- `3_Code/src/airbag_project/config.py`

## 3. Evaluate Many Crash Scenarios Instead of One Nominal Crash

**Decision:** Generate stochastic crash scenarios for training and evaluation.

**Random variables included:**

- crash speed
- impact angle
- occupant seating offset
- seatbelt usage
- sensor delay and trigger bias
- crash pulse duration

**Reason:** A single nominal crash can hide poor tail behavior. Airbag deployment must remain effective across a distribution of possible crashes.

**Implementation location:**

- `3_Code/src/airbag_project/uncertainty.py`

## 4. Include Distribution Shift

**Decision:** Evaluate methods on both a default distribution and a shifted distribution.

**Default profile:** Used for main training and in-distribution evaluation.

**Shifted profile:** Uses more severe or less favorable crash conditions, including higher speeds, larger obliquity, larger occupant offset, lower belt usage, and noisier sensing.

**Reason:** A method can perform well on the distribution it was trained on but fail under slightly different conditions. The shifted distribution tests robustness beyond ordinary in-distribution performance.

**Evidence from final run:**

- Initial design shifted mean HIC: `444.16`
- Shift-refined shifted mean HIC: `372.21`
- Initial shifted HIC failure rate: `32.00%`
- Shift-refined shifted HIC failure rate: `20.33%`

These values are stored in:

- `4_Data_Results/outputs/02_shifted_comparison_table.md`
- `4_Data_Results/outputs/00_summary.json`

## 5. Use a Multi-Term Objective

**Decision:** Optimize a weighted objective that includes average injury, tail injury, chest response, energy, and penalties.

The objective has the form:

```text
J(x) =
  w1 * E[HIC]
+ w2 * E[chest deflection]
+ w3 * E[deployment energy]
+ w4 * CVaR90(HIC)
+ penalties for high HIC failure rate and false deployment rate
```

**Implemented weights:**

| Term | Weight |
| --- | --- |
| Mean HIC | 0.55 |
| Mean chest deflection | 0.25 |
| Deployment energy | 0.08 |
| HIC CVaR90 | 0.12 |
| False deployment penalty | 0.20 |

**Reason:** Minimizing only mean HIC could ignore rare but severe crash outcomes. Including CVaR90 and failure penalties makes the optimization more sensitive to tail-risk behavior.

**Implementation location:**

- `3_Code/src/airbag_project/optimize.py`
- `3_Code/src/airbag_project/config.py`

## 6. Compare Multiple Baselines

**Decision:** Compare several methods instead of presenting only the best optimizer.

**Methods compared:**

| Method | Purpose |
| --- | --- |
| Initial Design | reference design |
| Deterministic SQP | nominal single-scenario baseline |
| Grid Search | transparent coarse-search baseline |
| MPC-Inspired Policy | simple adaptive/control-inspired baseline |
| Robust DE+SLSQP | main stochastic robust optimizer |
| Shift-Robust DRO | shift-aware robust method |
| Shift-Refined Local Search | shifted-scenario local refinement |

**Reason:** Baselines make it possible to tell whether improvements are caused by stochastic optimization rather than by arbitrary parameter changes.

**Implementation location:**

- `3_Code/src/airbag_project/baselines.py`
- `3_Code/src/airbag_project/optimize.py`
- `3_Code/src/run_experiment.py`

## 7. Use Differential Evolution Followed by SLSQP

**Decision:** Use Differential Evolution for global exploration and SLSQP for local refinement.

**Reason:** The simulator produces a nonlinear, noisy, simulation-based objective. Differential Evolution is useful for broad search in a bounded continuous design space. SLSQP can then refine a promising solution locally.

**Evidence from final run:**

On shifted evaluation:

- Initial objective: `0.892`
- Robust DE+SLSQP objective: `0.589`
- Initial failure rate: `32.00%`
- Robust DE+SLSQP failure rate: `21.00%`

## 8. Add Shift-Refined Local Search

**Decision:** Add a shifted-scenario local refinement stage after the robust optimizer.

**Reason:** The robust optimizer improved results, but shifted scenarios still exposed high tail risk. Refining the robust solution on shifted scenarios directly targeted the more severe evaluation profile.

**Evidence from final run:**

On shifted evaluation:

- Robust DE+SLSQP objective: `0.589`
- Shift-refined objective: `0.579`
- Robust DE+SLSQP mean HIC: `377.17`
- Shift-refined mean HIC: `372.21`
- Robust DE+SLSQP failure rate: `21.00%`
- Shift-refined failure rate: `20.33%`

## 9. Select Final Result Bundle

**Decision:** Use `outputs/03_domain_shift_run/` as the selected final run for the report and presentation.

**Reason:** This run contains both default and shifted evaluations, method comparison tables, design tables, scenario metrics, figures, and the shifted crash animation.

**Packaged location:**

- `4_Data_Results/outputs/`
- `4_Data_Results/figures/`

