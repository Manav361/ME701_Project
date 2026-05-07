# Run Instructions

From this folder:

```bash
cd src
python -m venv .venv
.venv\Scripts\activate
pip install -r ..\requirements.txt
python run_experiment.py
```

The script creates a new numbered run directory under `src/outputs/`, such as `outputs/08_domain_shift_run/`.

Optional post-processing:

```bash
python analyze_distribution_performance.py
```

This optional analysis expects `src/outputs/scenario_metrics.csv`. The packaged final result bundle is already available in `../4_Data_Results/outputs/`.
