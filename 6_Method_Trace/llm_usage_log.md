# LLM and External Tool Usage Log

This file documents external assistance used in preparing the project package. The purpose is transparency and reproducibility.

## Summary

An LLM assistant, ChatGPT Codex, was used for the coding part of project to help us assist writing some part of code to improve efficiency and productivity. The project idea, modeling work, code development, interpretation of results, and research direction were controlled by the team. The LLM was used as a productivity tool for packaging, writing support text, and checking that the submission followed the required structure.


## Tools and Software Used

| Tool | Purpose |
| --- | --- |
| Python | main simulation and optimization workflow |
| NumPy | numerical arrays and random sampling |
| SciPy | optimization methods including Differential Evolution and SLSQP |
| pandas | tabular metrics and CSV output |
| Matplotlib | plots and figures |
| LaTeX / IEEE style source | report source format |
| PowerShell | file organization and zip creation |
| ChatGPT Codex | documentation, packaging, and trace-writing assistance |

## Verification of Results

The LLM did not generate the numerical results. Reported values were taken from saved output files created by the project code.

Key verification points:

| Claim | Source file |
| --- | --- |
| Best method is Shift-Refined Local Search for both profiles | `4_Data_Results/outputs/00_summary.json` |
| In-distribution comparison values | `4_Data_Results/outputs/01_iid_comparison_table.md` |
| Shifted comparison values | `4_Data_Results/outputs/02_shifted_comparison_table.md` |
| Final optimized design variables | `4_Data_Results/outputs/02_shifted_design_table.md` |
| Plots used in report/presentation | `4_Data_Results/figures/` |

## Numerical Values Checked

Selected final shifted-distribution results:

| Method | Objective | Mean HIC | Failure rate |
| --- | ---: | ---: | ---: |
| Initial Design | 0.892 | 444.16 | 32.00% |
| Robust DE+SLSQP | 0.589 | 377.17 | 21.00% |
| Shift-Refined Local Search | 0.579 | 372.21 | 20.33% |

Selected final in-distribution results:

| Method | Objective | Mean HIC | Failure rate |
| --- | ---: | ---: | ---: |
| Initial Design | 0.431 | 259.89 | 16.00% |
| Robust DE+SLSQP | 0.356 | 230.41 | 11.67% |
| Shift-Refined Local Search | 0.352 | 226.52 | 11.00% |

## Limits of LLM Use

The LLM was not used as a substitute for numerical validation. It did not independently certify the crash model, and it did not replace engineering judgment. The reduced-order model assumptions and limitations remain part of the project and are stated in the report.

