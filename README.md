# Stochastic Optimization of Airbag Deployment Parameters

**Authors:** Jaladhi Joshi and Manav Agrawal  
**Course:** ME 701

## Project Overview

This project studies how to choose airbag deployment parameters when crash conditions are uncertain. Instead of optimizing for one fixed crash, the workflow generates many stochastic crash scenarios with variation in speed, impact angle, occupant seating offset, belt usage, sensor delay, and crash pulse duration.

A reduced-order occupant-restraint simulator evaluates each airbag design using head injury criterion (HIC), chest deflection, deployment energy, HIC failure rate, and false deployment rate. The project compares nominal and uncertainty-aware design methods, including deterministic SQP, grid search, an MPC-inspired policy, robust Differential Evolution with SLSQP refinement, shift-robust DRO, and shift-refined local search.

The main conclusion is that uncertainty-aware optimization performs better than nominal single-crash tuning. In the selected final run, **Shift-Refined Local Search** gives the best performance on both in-distribution and shifted crash evaluations.

## Folder Structure

```text
Joshi_Agrawal_Stochastic_Airbag_Deployment_Optimization/
│
├── 1_Report/
│   ├── final_report.pdf
│   ├── final_report.tex
│   └── figures/
│
├── 2_Presentation/
│   ├── final_slides.pdf
│   └── presentation_slides.tex
│
├── 3_Code/
│   ├── src/
│   │   ├── airbag_project/
│   │   ├── run_experiment.py
│   │   ├── analyze_distribution_performance.py
│   │   └── make_crash_animation.py
│   ├── notebooks/
│   ├── requirements.txt
│   └── run_instructions.md
│
├── 4_Data_Results/
│   ├── input_data/
│   ├── processed_data/
│   ├── outputs/
│   └── figures/
│
├── 5_Literature/
│   └── literature_summaries.md
│
├── 6_Method_Trace/
│   ├── design_decisions.md
│   ├── failed_attempts.md
│   └── llm_usage_log.md
│
├── 7_Reproducibility/
│   └── REPRODUCE.md
│
└── README.md
```

## How to Run the Code

From the top-level submission folder, run:

```bash
cd 3_Code/src
python -m venv .venv
.venv\Scripts\activate
pip install -r ..\requirements.txt
python run_experiment.py
```

The script will create a new numbered results folder under:

```text
3_Code/src/outputs/
```

For example:

```text
3_Code/src/outputs/08_domain_shift_run/
```

Each run generates comparison tables, design tables, scenario-level metrics, summary JSON files, and plots for both default and shifted evaluation profiles.

For more detailed reproduction instructions, see:

```text
7_Reproducibility/REPRODUCE.md
```

## Main Results

The final selected result bundle used in the report is located at:

```text
4_Data_Results/outputs/
```

Key files:

- `00_summary.json`: overall summary of the selected run
- `01_iid_comparison_table.md`: method comparison on in-distribution evaluation
- `02_shifted_comparison_table.md`: method comparison on shifted evaluation
- `02_shifted_design_table.md`: optimized design parameters for shifted evaluation
- `01_iid_scenario_metrics.csv`: scenario-level metrics for in-distribution evaluation
- `02_shifted_scenario_metrics.csv`: scenario-level metrics for shifted evaluation

Key figures are available in:

```text
4_Data_Results/figures/
```

Important final result:

- Best method on in-distribution evaluation: **Shift-Refined Local Search**
- Best method on shifted evaluation: **Shift-Refined Local Search**
- Shifted mean HIC improved from `444.16` to `372.21`
- Shifted HIC failure rate improved from `32.00%` to `20.33%`

These results come from the reduced-order simulation model and should be interpreted as a comparison of optimization methods, not as real-world airbag certification data.
