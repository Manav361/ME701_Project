from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from time import perf_counter

import numpy as np
from scipy.optimize import minimize

from .config import ModelConfig, ObjectiveWeights, OptimizationConfig
from .optimize import (
    PerformanceSummary,
    ScenarioMetrics,
    compute_objective_from_metrics,
    evaluate_design,
    summarize_metrics,
)
from .simulator import DeploymentDesign, simulate_design
from .uncertainty import CrashScenario


@dataclass(frozen=True)
class MethodResult:
    name: str
    method_type: str
    runtime_s: float
    summary: PerformanceSummary
    metrics: ScenarioMetrics
    design: DeploymentDesign | None
    design_mean: DeploymentDesign | None


def evaluate_fixed_design_method(
    name: str,
    method_type: str,
    design: DeploymentDesign,
    scenarios: list[CrashScenario],
    model_config: ModelConfig,
    objective_config: OptimizationConfig,
    weights: ObjectiveWeights,
    runtime_s: float = 0.0,
) -> MethodResult:
    print(f"Evaluation ({name}): 0%")
    _, metrics = evaluate_design(
        design,
        scenarios,
        model_config,
        objective_config,
        weights,
        progress_label=f"Evaluation ({name})",
        show_progress=True,
    )
    summary = summarize_metrics(metrics, objective_config, weights)
    return MethodResult(
        name=name,
        method_type=method_type,
        runtime_s=runtime_s,
        summary=summary,
        metrics=metrics,
        design=design,
        design_mean=design,
    )


def optimize_nominal_design(
    initial_design: DeploymentDesign,
    model_config: ModelConfig,
    objective_config: OptimizationConfig,
    weights: ObjectiveWeights,
) -> tuple[DeploymentDesign, float]:
    print("Training (Deterministic SQP): 0%")
    nominal_scenario = CrashScenario(
        speed_mph=45.0,
        angle_deg=0.0,
        occupant_offset_m=0.0,
        belted=True,
        sensor_delay_s=0.0,
        pulse_duration_s=model_config.nominal_pulse_duration,
        crash_active=True,
        trigger_bias_mps2=0.0,
    )
    bounds = [
        objective_config.delay_bounds_ms,
        objective_config.pressure_bounds_kpa,
        objective_config.pressure_bounds_kpa,
        objective_config.pressure_bounds_kpa,
        objective_config.vent_bounds,
    ]

    def objective_fn(values: np.ndarray) -> float:
        design = DeploymentDesign.from_array(values)
        result = simulate_design(design, nominal_scenario, model_config)
        metrics = ScenarioMetrics(
            hic=np.array([result.hic]),
            chest_deflection_mm=np.array([result.chest_deflection_mm]),
            energy=np.array([result.deployment_energy]),
            false_deployment=np.array([float((not nominal_scenario.crash_active) and result.deployed)]),
        )
        return compute_objective_from_metrics(metrics, objective_config, weights)

    start = perf_counter()
    iteration_counter = {"count": 0}
    result = minimize(
        objective_fn,
        x0=initial_design.to_array(),
        bounds=bounds,
        method="SLSQP",
        callback=lambda _: _print_progress("Training (Deterministic SQP)", iteration_counter, objective_config.maxiter),
        options={"maxiter": objective_config.maxiter, "disp": False, "ftol": 1.0e-4},
    )
    elapsed = perf_counter() - start
    print("Training (Deterministic SQP): 100%")
    return DeploymentDesign.from_array(result.x), elapsed


def coarse_grid_search_design(
    scenarios: list[CrashScenario],
    model_config: ModelConfig,
    objective_config: OptimizationConfig,
    weights: ObjectiveWeights,
) -> tuple[DeploymentDesign, float]:
    delay_grid = np.array([6.0, 16.0, 28.0, 38.0])
    early_grid = np.array([100.0, 170.0, 240.0, 300.0])
    mid_grid = np.array([160.0, 220.0, 270.0, 300.0])
    late_grid = np.array([100.0, 160.0, 210.0, 260.0])
    vent_grid = np.array([4.0, 12.0, 24.0, 45.0])
    grid_scenarios = scenarios[: min(24, len(scenarios))]

    start = perf_counter()
    best_design: DeploymentDesign | None = None
    best_objective = float("inf")
    grid_points = list(product(delay_grid, early_grid, mid_grid, late_grid, vent_grid))
    progress_marks = _progress_marks(len(grid_points))
    print("Training (Grid Search): 0%")
    for idx, values in enumerate(grid_points, start=1):
        design = DeploymentDesign(*values)
        objective, _ = evaluate_design(design, grid_scenarios, model_config, objective_config, weights)
        if objective < best_objective:
            best_objective = objective
            best_design = design
        if idx in progress_marks:
            pct = int(round(100.0 * idx / len(grid_points)))
            print(f"Training (Grid Search): {pct}%")

    if best_design is None:
        raise RuntimeError("Grid search failed to produce a candidate design.")

    refined_points = list(
        product(
            _refine_axis(best_design.trigger_delay_ms, objective_config.delay_bounds_ms, 4.0),
            _refine_axis(best_design.pressure_early_kpa, objective_config.pressure_bounds_kpa, 25.0),
            _refine_axis(best_design.pressure_mid_kpa, objective_config.pressure_bounds_kpa, 20.0),
            _refine_axis(best_design.pressure_late_kpa, objective_config.pressure_bounds_kpa, 20.0),
            _refine_axis(best_design.vent_rate, objective_config.vent_bounds, 4.0),
        )
    )
    refined_points = list(dict.fromkeys(refined_points))
    progress_marks = _progress_marks(len(refined_points))
    print("Training (Grid Search Refinement): 0%")
    for idx, values in enumerate(refined_points, start=1):
        design = DeploymentDesign(*values)
        objective, _ = evaluate_design(design, grid_scenarios, model_config, objective_config, weights)
        if objective < best_objective:
            best_objective = objective
            best_design = design
        if idx in progress_marks:
            pct = int(round(100.0 * idx / len(refined_points)))
            print(f"Training (Grid Search Refinement): {pct}%")
    elapsed = perf_counter() - start
    return best_design, elapsed


def evaluate_adaptive_policy_method(
    name: str,
    scenarios: list[CrashScenario],
    model_config: ModelConfig,
    objective_config: OptimizationConfig,
    weights: ObjectiveWeights,
) -> MethodResult:
    start = perf_counter()
    hic = np.zeros(len(scenarios))
    chest = np.zeros(len(scenarios))
    energy = np.zeros(len(scenarios))
    false_deployment = np.zeros(len(scenarios))
    chosen_designs = np.zeros((len(scenarios), 5))
    progress_marks = _progress_marks(len(scenarios))
    print(f"Evaluation ({name}): 0%")

    for i, scenario in enumerate(scenarios):
        design = mpc_inspired_policy(scenario, objective_config)
        chosen_designs[i, :] = design.to_array()
        result = simulate_design(design, scenario, model_config)
        hic[i] = result.hic
        chest[i] = result.chest_deflection_mm
        energy[i] = result.deployment_energy
        false_deployment[i] = float((not scenario.crash_active) and result.deployed)
        if (i + 1) in progress_marks:
            pct = int(round(100.0 * (i + 1) / len(scenarios)))
            print(f"Evaluation ({name}): {pct}%")

    elapsed = perf_counter() - start
    metrics = ScenarioMetrics(
        hic=hic,
        chest_deflection_mm=chest,
        energy=energy,
        false_deployment=false_deployment,
    )
    summary = summarize_metrics(metrics, objective_config, weights)
    mean_design = DeploymentDesign.from_array(np.mean(chosen_designs, axis=0))
    return MethodResult(
        name=name,
        method_type="adaptive_policy",
        runtime_s=elapsed,
        summary=summary,
        metrics=metrics,
        design=None,
        design_mean=mean_design,
    )


def _print_progress(label: str, counter: dict[str, int], total: int) -> None:
    counter["count"] += 1
    pct = min(100, int(round(100.0 * counter["count"] / max(1, total))))
    print(f"{label}: {pct}%")


def _progress_marks(total: int) -> set[int]:
    if total <= 0:
        return set()
    marks = set()
    for pct in range(10, 101, 10):
        marks.add(max(1, int(np.ceil(total * pct / 100.0))))
    return marks


def _refine_axis(center: float, bounds: tuple[float, float], step: float) -> np.ndarray:
    values = np.array([center - step, center, center + step], dtype=float)
    return np.clip(values, bounds[0], bounds[1])


def mpc_inspired_policy(
    scenario: CrashScenario,
    objective_config: OptimizationConfig,
) -> DeploymentDesign:
    speed_score = np.clip((scenario.speed_mph - 30.0) / 30.0, 0.0, 1.0)
    angle_score = np.clip(abs(scenario.angle_deg) / 35.0, 0.0, 1.0)
    offset_score = np.clip((scenario.occupant_offset_m + 0.06) / 0.13, 0.0, 1.0)
    belt_penalty = 0.18 if not scenario.belted else 0.0
    severity = np.clip(0.62 * speed_score + 0.18 * angle_score + 0.10 * offset_score + belt_penalty, 0.0, 1.0)

    delay = 24.0 - 16.0 * severity - 500.0 * scenario.sensor_delay_s
    early = 115.0 + 55.0 * severity + 15.0 * angle_score
    mid = 205.0 + 95.0 * severity + 10.0 * offset_score
    late = 135.0 + 60.0 * severity + 10.0 * angle_score
    vent = 28.0 - 18.0 * severity + 4.0 * angle_score

    delay = float(np.clip(delay, *objective_config.delay_bounds_ms))
    early = float(np.clip(early, *objective_config.pressure_bounds_kpa))
    mid = float(np.clip(mid, *objective_config.pressure_bounds_kpa))
    late = float(np.clip(late, *objective_config.pressure_bounds_kpa))
    vent = float(np.clip(vent, *objective_config.vent_bounds))
    return DeploymentDesign(
        trigger_delay_ms=delay,
        pressure_early_kpa=early,
        pressure_mid_kpa=mid,
        pressure_late_kpa=late,
        vent_rate=vent,
    )
