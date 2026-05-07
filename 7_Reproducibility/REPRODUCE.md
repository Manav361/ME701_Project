# Reproduce Main Results

Repository/archive link: to be added before submission if a GitHub or Zenodo archive is created.

## Environment

Python 3.10 or newer is recommended.

```bash
cd 3_Code/src
python -m venv .venv
.venv\Scripts\activate
pip install -r ..\requirements.txt
```

## Main Run

```bash
python run_experiment.py
```

Expected result: a new directory under `outputs/`, for example `outputs/08_domain_shift_run/`, containing:

- `00_summary.json`
- `01_iid_comparison_table.csv` and `.md`
- `01_iid_design_table.csv` and `.md`
- `01_iid_scenario_metrics.csv`
- `01_iid_*` figures
- `02_shifted_comparison_table.csv` and `.md`
- `02_shifted_design_table.csv` and `.md`
- `02_shifted_scenario_metrics.csv`
- `02_shifted_*` figures

Because the optimizer is stochastic but seeded in `airbag_project/config.py`, results should be close to the packaged final run. Small numerical differences can occur across Python, NumPy, and SciPy versions.

## Packaged Expected Outputs

The final selected outputs are in:

```text
4_Data_Results/outputs/
```

Main result files:

- `00_summary.json`
- `01_iid_comparison_table.md`
- `02_shifted_comparison_table.md`
- `02_shifted_design_table.md`

The best method in the packaged final run is `Shift-Refined Local Search` for both in-distribution and shifted evaluation.
