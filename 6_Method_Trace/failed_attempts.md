# Failed Attempts and Revisions

This file records approaches that were tried, found insufficient, or revised during the project. Some of these methods were kept as baselines because their limitations are informative.

## 1. Nominal Deterministic Optimization Was Not Enough

**Attempt:** Optimize deployment parameters using deterministic SQP on a nominal crash scenario.

**Why it seemed reasonable:** Many engineering design workflows begin with a nominal operating condition. SQP is efficient and gives a local optimum for smooth constrained problems.

**What happened:** The deterministic SQP result was almost identical to the initial design and produced almost no improvement.

**Evidence from final run:**

In-distribution evaluation:

| Method | Objective | Mean HIC | Failure rate |
| --- | ---: | ---: | ---: |
| Initial Design | 0.431 | 259.89 | 16.00% |
| Deterministic SQP | 0.431 | 259.85 | 16.00% |

Shifted evaluation:

| Method | Objective | Mean HIC | Failure rate |
| --- | ---: | ---: | ---: |
| Initial Design | 0.892 | 444.16 | 32.00% |
| Deterministic SQP | 0.891 | 443.96 | 32.00% |

**Conclusion:** Single-scenario tuning does not address the uncertainty in crash speed, impact angle, occupant position, belt usage, and sensor delay.

**Action taken:** Kept deterministic SQP as a baseline and added stochastic training/evaluation.

## 2. Evaluating Only the Default Distribution Was Too Optimistic

**Attempt:** Evaluate all methods only on the same default scenario distribution used for training.

**Why it seemed reasonable:** In-distribution evaluation is a standard first check and gives a clean comparison between algorithms.

**Problem:** It did not test whether a design remained strong when crash severity or sensing assumptions changed. A method could look good on the training-like distribution while still being fragile.

**Action taken:** Added a shifted evaluation profile with:

- higher crash speeds
- larger oblique/offset effects
- larger occupant seating offset
- lower seatbelt usage
- noisier sensing

**Result:** The shifted evaluation exposed much higher baseline injury risk. Initial mean HIC increased from `259.89` in distribution to `444.16` under shift, and failure rate increased from `16.00%` to `32.00%`.

## 3. Robust Optimization Improved Results But Did Not Fully Address Shift

**Attempt:** Use robust DE+SLSQP trained on stochastic default scenarios.

**What worked:** It substantially improved both default and shifted evaluation.

**Evidence from final shifted evaluation:**

| Method | Objective | Mean HIC | Failure rate |
| --- | ---: | ---: | ---: |
| Initial Design | 0.892 | 444.16 | 32.00% |
| Robust DE+SLSQP | 0.589 | 377.17 | 21.00% |

**Remaining issue:** Shifted performance was still meaningfully worse than in-distribution performance, and the shifted distribution still had high tail risk.

**Action taken:** Added shift-aware methods, including Shift-Robust DRO and Shift-Refined Local Search.

## 4. Shift-Robust DRO Did Not Beat Shift-Refined Local Search

**Attempt:** Add a shift-robust DRO-style method that emphasizes shifted scenarios during optimization.

**What worked:** It improved over the initial design on shifted evaluation.

**What did not work as well:** It did not outperform the simpler shift-refined local-search method in the final selected run.

**Evidence from final shifted evaluation:**

| Method | Objective | Mean HIC | Failure rate |
| --- | ---: | ---: | ---: |
| Shift-Robust DRO | 0.658 | 386.90 | 25.00% |
| Shift-Refined Local Search | 0.579 | 372.21 | 20.33% |

**Conclusion:** For this reduced-order model and chosen run settings, local refinement from a strong robust solution was more effective than the DRO-style variant.

## 5. Full Industrial Crash Modeling Was Out of Scope

**Attempt considered:** Use a high-fidelity crash or occupant model.

**Why it was not used:** A full crash model would require geometry, meshing, material properties, calibration, and much larger computation time. That would make repeated optimization runs impractical for this course project.

**Action taken:** Use a reduced-order model and explicitly state the limitation in:

- `1_Report/final_report.pdf`
- `1_Report/final_report.tex`
- top-level `README.md`

## 6. Excessive Intermediate Outputs Were Removed From Submission

**Issue:** The working folder contained many repeated output runs and Python cache files.

**Problem:** Including every repeated run would make the submission harder to inspect and less focused.

**Action taken:** The final package keeps the selected result bundle and excludes unnecessary cache files such as `__pycache__` and `.pyc` files.

**Selected final run:** `outputs/03_domain_shift_run/`

**Packaged location:** `4_Data_Results/outputs/`

