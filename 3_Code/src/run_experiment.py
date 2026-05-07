from __future__ import annotations

from pathlib import Path
from time import perf_counter

import numpy as np

from airbag_project.baselines import (
    coarse_grid_search_design,
    evaluate_adaptive_policy_method,
    evaluate_fixed_design_method,
    optimize_nominal_design,
)
from airbag_project.config import ModelConfig, ObjectiveWeights, OptimizationConfig
from airbag_project.optimize import (
    optimize_design,
    optimize_shift_refined_design,
    representative_trace,
)
from airbag_project.reporting import (
    plot_method_boxplots,
    plot_method_comparison,
    plot_metric_histograms,
    plot_speed_hic_panels,
    plot_tradeoff,
    plot_trace,
    save_comparison_table,
    save_design_table,
    save_metrics_csv,
    save_method_summary_json,
    save_summary,
)
from airbag_project.simulator import DeploymentDesign
from airbag_project.uncertainty import sample_scenarios


def main() -> None:
    model_config = ModelConfig()
    weights = ObjectiveWeights()
    opt_config = OptimizationConfig()
    rng = np.random.default_rng(opt_config.seed)

    train_scenarios = sample_scenarios(opt_config.training_scenarios, rng, model_config, profile="default")
    shifted_train_scenarios = sample_scenarios(opt_config.shifted_training_scenarios, rng, model_config, profile="shifted_eval")
    eval_iid_scenarios = sample_scenarios(opt_config.evaluation_scenarios, rng, model_config, profile="default")
    eval_shifted_scenarios = sample_scenarios(opt_config.evaluation_scenarios, rng, model_config, profile="shifted_eval")

    initial_design = DeploymentDesign(
        trigger_delay_ms=18.0,
        pressure_early_kpa=220.0,
        pressure_mid_kpa=190.0,
        pressure_late_kpa=140.0,
        vent_rate=18.0,
    )

    nominal_design, nominal_runtime = optimize_nominal_design(
        initial_design=initial_design,
        model_config=model_config,
        objective_config=opt_config,
        weights=weights,
    )
    grid_design, grid_runtime = coarse_grid_search_design(train_scenarios, model_config, opt_config, weights)

    robust_start = perf_counter()
    optimized_design, train_summary = optimize_design(initial_design, train_scenarios, model_config, opt_config, weights)
    robust_runtime = perf_counter() - robust_start

    shift_refined_start = perf_counter()
    shift_refined_design, shift_refined_train_summary = optimize_shift_refined_design(
        optimized_design,
        train_scenarios,
        shifted_train_scenarios,
        model_config,
        opt_config,
        weights,
    )
    shift_refined_runtime = perf_counter() - shift_refined_start

    output_dir = _next_output_dir(Path("outputs"))
    output_dir.mkdir(parents=True, exist_ok=False)

    iid_results = _evaluate_suite(
        scenarios=eval_iid_scenarios,
        model_config=model_config,
        opt_config=opt_config,
        weights=weights,
        initial_design=initial_design,
        nominal_design=nominal_design,
        nominal_runtime=nominal_runtime,
        grid_design=grid_design,
        grid_runtime=grid_runtime,
        optimized_design=optimized_design,
        robust_runtime=robust_runtime,
        shift_refined_design=shift_refined_design,
        shift_refined_runtime=shift_refined_runtime,
    )
    shifted_results = _evaluate_suite(
        scenarios=eval_shifted_scenarios,
        model_config=model_config,
        opt_config=opt_config,
        weights=weights,
        initial_design=initial_design,
        nominal_design=nominal_design,
        nominal_runtime=nominal_runtime,
        grid_design=grid_design,
        grid_runtime=grid_runtime,
        optimized_design=optimized_design,
        robust_runtime=robust_runtime,
        shift_refined_design=shift_refined_design,
        shift_refined_runtime=shift_refined_runtime,
    )

    _write_evaluation_bundle(
        output_dir=output_dir,
        prefix="01_iid",
        label="In-Distribution Evaluation",
        scenarios=eval_iid_scenarios,
        results=iid_results,
        initial_design=initial_design,
        optimized_design=optimized_design,
        model_config=model_config,
    )
    _write_evaluation_bundle(
        output_dir=output_dir,
        prefix="02_shifted",
        label="Distribution-Shift Evaluation",
        scenarios=eval_shifted_scenarios,
        results=shifted_results,
        initial_design=initial_design,
        optimized_design=optimized_design,
        model_config=model_config,
    )

    iid_best = min(iid_results, key=lambda result: result.summary.objective)
    shifted_best = min(shifted_results, key=lambda result: result.summary.objective)

    save_summary(
        output_dir / "00_summary.json",
        {
            "training_distribution": "default",
            "evaluation_profiles": ["default", "shifted_eval"],
            "output_dir": str(output_dir.resolve()),
            "robust_training_summary": {
                "design": {
                    "trigger_delay_ms": train_summary.design.trigger_delay_ms,
                    "pressure_early_kpa": train_summary.design.pressure_early_kpa,
                    "pressure_mid_kpa": train_summary.design.pressure_mid_kpa,
                    "pressure_late_kpa": train_summary.design.pressure_late_kpa,
                    "vent_rate": train_summary.design.vent_rate,
                },
                "objective": train_summary.objective,
                "hic_mean": train_summary.hic_mean,
                "hic_std": train_summary.hic_std,
                "hic_cvar90": train_summary.hic_cvar90,
                "chest_mean": train_summary.chest_mean,
                "chest_std": train_summary.chest_std,
                "failure_rate_hic_gt_1000": train_summary.failure_rate,
                "false_deployment_rate": train_summary.false_deployment_rate,
                "energy_mean": train_summary.energy_mean,
            },
            "shift_refined_training_summary": {
                "design": {
                    "trigger_delay_ms": shift_refined_train_summary.design.trigger_delay_ms,
                    "pressure_early_kpa": shift_refined_train_summary.design.pressure_early_kpa,
                    "pressure_mid_kpa": shift_refined_train_summary.design.pressure_mid_kpa,
                    "pressure_late_kpa": shift_refined_train_summary.design.pressure_late_kpa,
                    "vent_rate": shift_refined_train_summary.design.vent_rate,
                },
                "objective": shift_refined_train_summary.objective,
                "hic_mean": shift_refined_train_summary.hic_mean,
                "hic_std": shift_refined_train_summary.hic_std,
                "hic_cvar90": shift_refined_train_summary.hic_cvar90,
                "chest_mean": shift_refined_train_summary.chest_mean,
                "chest_std": shift_refined_train_summary.chest_std,
                "failure_rate_hic_gt_1000": shift_refined_train_summary.failure_rate,
                "false_deployment_rate": shift_refined_train_summary.false_deployment_rate,
                "energy_mean": shift_refined_train_summary.energy_mean,
            },
            "best_method_iid": iid_best.name,
            "best_method_shifted": shifted_best.name,
            "robust_vs_initial_iid": _improvement_payload_for_method(iid_results, "Robust DE+SLSQP"),
            "robust_vs_initial_shifted": _improvement_payload_for_method(shifted_results, "Robust DE+SLSQP"),
            "shift_refined_vs_initial_iid": _improvement_payload_for_method(iid_results, "Shift-Refined Local Search"),
            "shift_refined_vs_initial_shifted": _improvement_payload_for_method(shifted_results, "Shift-Refined Local Search"),
        },
    )

    print("In-distribution results:")
    _print_results(iid_results)
    print("Shifted-distribution results:")
    _print_results(shifted_results)
    print("Artifacts written to:", output_dir.resolve())


def _evaluate_suite(
    scenarios,
    model_config,
    opt_config,
    weights,
    initial_design,
    nominal_design,
    nominal_runtime,
    grid_design,
    grid_runtime,
    optimized_design,
    robust_runtime,
    shift_refined_design,
    shift_refined_runtime,
):
    initial_result = evaluate_fixed_design_method(
        "Initial Design",
        "reference",
        initial_design,
        scenarios,
        model_config,
        opt_config,
        weights,
    )
    nominal_result = evaluate_fixed_design_method(
        "Deterministic SQP",
        "baseline_fixed",
        nominal_design,
        scenarios,
        model_config,
        opt_config,
        weights,
        runtime_s=nominal_runtime,
    )
    grid_result = evaluate_fixed_design_method(
        "Grid Search",
        "baseline_fixed",
        grid_design,
        scenarios,
        model_config,
        opt_config,
        weights,
        runtime_s=grid_runtime,
    )
    adaptive_result = evaluate_adaptive_policy_method(
        "MPC-Inspired Policy",
        scenarios,
        model_config,
        opt_config,
        weights,
    )
    robust_result = evaluate_fixed_design_method(
        "Robust DE+SLSQP",
        "robust_fixed",
        optimized_design,
        scenarios,
        model_config,
        opt_config,
        weights,
        runtime_s=robust_runtime,
    )
    shift_refined_result = evaluate_fixed_design_method(
        "Shift-Refined Local Search",
        "robust_local_refinement",
        shift_refined_design,
        scenarios,
        model_config,
        opt_config,
        weights,
        runtime_s=shift_refined_runtime,
    )
    return [initial_result, nominal_result, grid_result, adaptive_result, robust_result, shift_refined_result]


def _write_evaluation_bundle(
    output_dir: Path,
    prefix: str,
    label: str,
    scenarios,
    results,
    initial_design,
    optimized_design,
    model_config,
) -> None:
    save_method_summary_json(results, output_dir / f"{prefix}_methods.json")
    save_comparison_table(results, output_dir / f"{prefix}_comparison_table.csv", output_dir / f"{prefix}_comparison_table.md")
    save_design_table(results, output_dir / f"{prefix}_design_table.csv", output_dir / f"{prefix}_design_table.md")
    save_metrics_csv(output_dir / f"{prefix}_scenario_metrics.csv", scenarios, results)

    initial_result = next(result for result in results if result.name == "Initial Design")
    robust_result = next(result for result in results if result.name == "Robust DE+SLSQP")

    plot_metric_histograms(initial_result.metrics, robust_result.metrics, output_dir / f"{prefix}_initial_vs_robust_histograms.png")
    plot_method_comparison(results, output_dir / f"{prefix}_method_comparison.png")
    plot_method_boxplots(results, output_dir / f"{prefix}_method_boxplots.png")
    plot_tradeoff(results, output_dir / f"{prefix}_tradeoff_map.png")
    plot_speed_hic_panels(scenarios, results, output_dir / f"{prefix}_speed_hic_panels.png")

    initial_trace = representative_trace(initial_design, scenarios, model_config)
    robust_trace = representative_trace(optimized_design, scenarios, model_config)
    plot_trace(initial_trace, output_dir / f"{prefix}_initial_trace.png")
    plot_trace(robust_trace, output_dir / f"{prefix}_robust_trace.png")

    best_result = min(results, key=lambda result: result.summary.objective)
    save_summary(
        output_dir / f"{prefix}_summary.json",
        {
            "label": label,
            "best_method": best_result.name,
            "robust_vs_initial": _improvement_payload_for_method(results, "Robust DE+SLSQP"),
            "shift_refined_vs_initial": _improvement_payload_for_method(results, "Shift-Refined Local Search"),
        },
    )


def _improvement_payload_for_method(results, target_name: str) -> dict:
    initial_result = next(result for result in results if result.name == "Initial Design")
    target_result = next(result for result in results if result.name == target_name)
    return {
        "method": target_name,
        "hic_mean_percent": _percent_drop(initial_result.summary.hic_mean, target_result.summary.hic_mean),
        "hic_cvar90_percent": _percent_drop(initial_result.summary.hic_cvar90, target_result.summary.hic_cvar90),
        "chest_mean_percent": _percent_drop(initial_result.summary.chest_mean, target_result.summary.chest_mean),
        "failure_rate_percent": _percent_drop(initial_result.summary.failure_rate, target_result.summary.failure_rate),
        "false_deployment_rate_percent": _percent_drop(
            initial_result.summary.false_deployment_rate,
            target_result.summary.false_deployment_rate,
        ),
    }


def _print_results(results) -> None:
    for result in results:
        print(
            f"  {result.name}: objective={result.summary.objective:.4f}, "
            f"mean HIC={result.summary.hic_mean:.2f}, "
            f"failure rate={100.0 * result.summary.failure_rate:.2f}%, "
            f"false deploy={100.0 * result.summary.false_deployment_rate:.2f}%"
        )
    best_result = min(results, key=lambda result: result.summary.objective)
    print("  Best method:", best_result.name)


def _next_output_dir(base_dir: Path) -> Path:
    base_dir.mkdir(exist_ok=True)
    numeric_prefixes = []
    for child in base_dir.iterdir():
        if child.is_dir():
            prefix = child.name.split("_", 1)[0]
            if prefix.isdigit():
                numeric_prefixes.append(int(prefix))
    next_index = max(numeric_prefixes, default=0) + 1
    return base_dir / f"{next_index:02d}_domain_shift_run"


def _percent_drop(before: float, after: float) -> float:
    if before == 0.0:
        return 0.0
    return 100.0 * (before - after) / before


if __name__ == "__main__":
    main()
