# LLM and External Tool Usage Log

This file documents external assistance used in preparing the project package. The purpose is transparency and reproducibility.

## Summary

An LLM assistant, ChatGPT Codex, was used to help organize the final submission package and improve documentation. The project idea, modeling work, code development, interpretation of results, and research direction were controlled by the project team. The LLM was used as a productivity tool for packaging, writing support text, and checking that the submission followed the required structure.

## LLM Assistance Used

### 1. Submission Folder Organization

**Task:** Create the required submission structure:

```text
1_Report/
2_Presentation/
3_Code/
4_Data_Results/
5_Literature/
6_Method_Trace/
7_Reproducibility/
README.md
```

**LLM role:** Helped arrange existing files into the required structure and remove unnecessary cache files.

**Human verification:** The final folder structure was checked manually against the course instructions.

### 2. README and Reproducibility Documentation

**Task:** Draft and improve:

- top-level `README.md`
- `3_Code/run_instructions.md`
- `7_Reproducibility/REPRODUCE.md`

**LLM role:** Helped write clear instructions for running the code and locating main results.

**Human verification:** Commands and paths were matched against the actual packaged folder layout.

### 3. Report Drafting and Formatting

**Task:** Prepare an IEEE-style report source and PDF with required sections:

- problem formulation
- mathematical model
- methodology and justification
- results and discussion
- limitations

**LLM role:** Helped convert existing project results and code structure into a report draft.

**Human verification:** Numerical claims were checked against the generated output files:

- `4_Data_Results/outputs/00_summary.json`
- `4_Data_Results/outputs/01_iid_comparison_table.md`
- `4_Data_Results/outputs/02_shifted_comparison_table.md`
- `4_Data_Results/outputs/02_shifted_design_table.md`

### 4. Method Trace Documentation

**Task:** Expand design-decision, failed-attempt, and tool-usage logs.

**LLM role:** Helped structure the trace into auditable sections with rationale, evidence, and file references.

**Human verification:** The trace was based on the actual code modules and final output bundle.

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

