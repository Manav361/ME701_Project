from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import differential_evolution, minimize

from .config import ModelConfig, ObjectiveWeights, OptimizationConfig
from .simulator import DeploymentDesign, SimulationResult, simulate_design
from .uncertainty import CrashScenario, sample_scenarios


@dataclass(frozen=True)
class ScenarioMetrics:
    hic: np.ndarray
    chest_deflection_mm: np.ndarray
    energy: np.ndarray
    false_deployment: np.ndarray


@dataclass(frozen=True)
class PerformanceSummary:
    objective: float
    hic_mean: float
    hic_std: float
    hic_cvar90: float
    chest_mean: float
    chest_std: float
    failure_rate: float
    energy_mean: float
    false_deployment_rate: float


@dataclass(frozen=True)
class EvaluationSummary:
    design: DeploymentDesign
    objective: float
    hic_mean: float
    hic_std: float
    hic_cvar90: float
    chest_mean: float
    chest_std: float
    failure_rate: float
    energy_mean: float
    false_deployment_rate: float


def evaluate_design(
    design: DeploymentDesign,
    scenarios: list[CrashScenario],
    model_config: ModelConfig,
    objective_config: OptimizationConfig,
    weights: ObjectiveWeights,
    progress_label: str | None = None,
    show_progress: bool = False,
) -> tuple[float, ScenarioMetrics]:
    hic = np.zeros(len(scenarios))
    chest = np.zeros(len(scenarios))
    energy = np.zeros(len(scenarios))
    false_deployment = np.zeros(len(scenarios))
    progress_marks = _progress_marks(len(scenarios)) if show_progress else set()
    for i, scenario in enumerate(scenarios):
        result = simulate_design(design, scenario, model_config)
        hic[i] = result.hic
        chest[i] = result.chest_deflection_mm
        energy[i] = result.deployment_energy
        false_deployment[i] = float((not scenario.crash_active) and result.deployed)
        if show_progress and (i + 1) in progress_marks:
            pct = int(round(100.0 * (i + 1) / len(scenarios)))
            label = progress_label or "Evaluation"
            print(f"{label}: {pct}%")

    objective = compute_objective_from_metrics(
        ScenarioMetrics(
            hic=hic,
            chest_deflection_mm=chest,
            energy=energy,
            false_deployment=false_deployment,
        ),
        objective_config,
        weights,
    )
    return objective, ScenarioMetrics(
        hic=hic,
        chest_deflection_mm=chest,
        energy=energy,
        false_deployment=false_deployment,
    )


def optimize_design(
    initial_design: DeploymentDesign,
    scenarios: list[CrashScenario],
    model_config: ModelConfig,
    objective_config: OptimizationConfig,
    weights: ObjectiveWeights,
) -> tuple[DeploymentDesign, EvaluationSummary]:
    bounds = [
        objective_config.delay_bounds_ms,
        objective_config.pressure_bounds_kpa,
        objective_config.pressure_bounds_kpa,
        objective_config.pressure_bounds_kpa,
        objective_config.vent_bounds,
    ]

    def objective_fn(values: np.ndarray) -> float:
        design = DeploymentDesign.from_array(values)
        objective, _ = evaluate_design(design, scenarios, model_config, objective_config, weights)
        return objective

    de_generations = {"count": 0}
    slsqp_iterations = {"count": 0}

    def de_callback(intermediate_result=None, convergence=None):
        de_generations["count"] += 1
        pct = min(100, int(round(100.0 * de_generations["count"] / max(1, objective_config.de_maxiter))))
        print(f"Training (Robust DE stage): {pct}%")
        return False

    result = minimize(
        objective_fn,
        x0=_global_seed(initial_design, bounds, objective_fn, objective_config, de_callback, de_generations),
        bounds=bounds,
        method="SLSQP",
        callback=lambda _: _print_slsqp_progress(slsqp_iterations, objective_config.maxiter),
        options={"maxiter": objective_config.maxiter, "disp": False, "ftol": 1.0e-4},
    )
    print("Training (Robust SLSQP stage): 100%")
    final_design = DeploymentDesign.from_array(result.x)
    return final_design, summarize_design(final_design, scenarios, model_config, objective_config, weights)


def optimize_shift_refined_design(
    seed_design: DeploymentDesign,
    default_scenarios: list[CrashScenario],
    shifted_scenarios: list[CrashScenario],
    model_config: ModelConfig,
    objective_config: OptimizationConfig,
    weights: ObjectiveWeights,
) -> tuple[DeploymentDesign, EvaluationSummary]:
    bounds = [
        objective_config.delay_bounds_ms,
        objective_config.pressure_bounds_kpa,
        objective_config.pressure_bounds_kpa,
        objective_config.pressure_bounds_kpa,
        objective_config.vent_bounds,
    ]
    refinement_scenarios = sample_scenarios(
        objective_config.shift_refine_scenarios,
        np.random.default_rng(objective_config.seed + 101),
        model_config,
        profile="shifted_eval",
    )
    combined_scenarios = default_scenarios + shifted_scenarios + refinement_scenarios

    def objective_fn(values: np.ndarray) -> float:
        design = DeploymentDesign.from_array(values)
        objective, _ = evaluate_design(design, refinement_scenarios, model_config, objective_config, weights)
        return objective

    seed_candidates = _shift_refinement_seed_candidates(seed_design, objective_config)
    best_values = None
    best_objective = float("inf")

    for seed_index, seed in enumerate(seed_candidates[: objective_config.shift_refine_multistarts], start=1):
        print(
            "Training (Shift-Refined local search): "
            f"seed {seed_index}/{min(len(seed_candidates), objective_config.shift_refine_multistarts)}"
        )
        refined_values, refined_score = _coordinate_pattern_refine(
            seed,
            bounds,
            objective_fn,
            label=f"Training (Shift-Refined coordinate refine seed {seed_index})",
        )
        if refined_score < best_objective:
            best_objective = refined_score
            best_values = refined_values.copy()

    if best_values is None:
        best_values = seed_design.to_array()

    final_design = DeploymentDesign.from_array(best_values)
    return final_design, summarize_design(final_design, combined_scenarios, model_config, objective_config, weights)


def _global_seed(
    initial_design: DeploymentDesign,
    bounds: list[tuple[float, float]],
    objective_fn,
    objective_config: OptimizationConfig,
    callback=None,
    progress_counter: dict[str, int] | None = None,
    stage_label: str = "Training (Robust DE stage)",
) -> np.ndarray:
    result = differential_evolution(
        objective_fn,
        bounds=bounds,
        seed=objective_config.seed,
        popsize=objective_config.de_popsize,
        maxiter=objective_config.de_maxiter,
        polish=False,
        x0=initial_design.to_array(),
        disp=False,
        callback=callback,
    )
    if progress_counter is None or progress_counter.get("count", 0) < objective_config.de_maxiter:
        print(f"{stage_label}: 100%")
    return result.x


def summarize_design(
    design: DeploymentDesign,
    scenarios: list[CrashScenario],
    model_config: ModelConfig,
    objective_config: OptimizationConfig,
    weights: ObjectiveWeights,
) -> EvaluationSummary:
    objective, metrics = evaluate_design(design, scenarios, model_config, objective_config, weights)
    summary = summarize_metrics(metrics, objective_config, weights, objective_override=objective)
    return EvaluationSummary(
        design=design,
        objective=summary.objective,
        hic_mean=summary.hic_mean,
        hic_std=summary.hic_std,
        hic_cvar90=summary.hic_cvar90,
        chest_mean=summary.chest_mean,
        chest_std=summary.chest_std,
        failure_rate=summary.failure_rate,
        energy_mean=summary.energy_mean,
        false_deployment_rate=summary.false_deployment_rate,
    )


def _print_slsqp_progress(counter: dict[str, int], maxiter: int) -> None:
    counter["count"] += 1
    pct = min(100, int(round(100.0 * counter["count"] / max(1, maxiter))))
    print(f"Training (Robust SLSQP stage): {pct}%")


def _print_progress_generic(label: str, counter: dict[str, int], total: int) -> None:
    counter["count"] += 1
    pct = min(100, int(round(100.0 * counter["count"] / max(1, total))))
    print(f"{label}: {pct}%")


def representative_trace(
    design: DeploymentDesign,
    scenarios: list[CrashScenario],
    model_config: ModelConfig,
) -> SimulationResult:
    representative = scenarios[len(scenarios) // 2]
    return simulate_design(design, representative, model_config)


def _cvar(values: np.ndarray, alpha: float) -> float:
    threshold = np.quantile(values, alpha)
    tail = values[values >= threshold]
    return float(np.mean(tail))


def compute_objective_from_metrics(
    metrics: ScenarioMetrics,
    objective_config: OptimizationConfig,
    weights: ObjectiveWeights,
) -> float:
    cvar90 = _cvar(metrics.hic, 0.90)
    failure_rate = float(np.mean(metrics.hic > objective_config.hic_limit))
    false_deployment_rate = float(np.mean(metrics.false_deployment))
    objective = (
        weights.hic_mean * np.mean(metrics.hic) / 1000.0
        + weights.chest_mean * np.mean(metrics.chest_deflection_mm) / 60.0
        + weights.energy * np.mean(metrics.energy)
        + weights.hic_cvar * cvar90 / 1200.0
        + weights.false_deployment * false_deployment_rate
    )
    objective += 6.0 * max(0.0, failure_rate - objective_config.chance_hic_limit) ** 2
    objective += 10.0 * max(0.0, false_deployment_rate - objective_config.false_deployment_limit) ** 2
    objective += 2.0 * max(0.0, np.mean(metrics.chest_deflection_mm) - 55.0) ** 2 / (55.0**2)
    return float(objective)


def summarize_metrics(
    metrics: ScenarioMetrics,
    objective_config: OptimizationConfig,
    weights: ObjectiveWeights,
    objective_override: float | None = None,
) -> PerformanceSummary:
    objective = (
        float(objective_override)
        if objective_override is not None
        else compute_objective_from_metrics(metrics, objective_config, weights)
    )
    return PerformanceSummary(
        objective=objective,
        hic_mean=float(np.mean(metrics.hic)),
        hic_std=float(np.std(metrics.hic)),
        hic_cvar90=float(_cvar(metrics.hic, 0.90)),
        chest_mean=float(np.mean(metrics.chest_deflection_mm)),
        chest_std=float(np.std(metrics.chest_deflection_mm)),
        failure_rate=float(np.mean(metrics.hic > objective_config.hic_limit)),
        energy_mean=float(np.mean(metrics.energy)),
        false_deployment_rate=float(np.mean(metrics.false_deployment)),
    )


def _shift_refinement_seed_candidates(
    seed_design: DeploymentDesign,
    objective_config: OptimizationConfig,
) -> list[np.ndarray]:
    bounds = np.array(
        [
            objective_config.delay_bounds_ms,
            objective_config.pressure_bounds_kpa,
            objective_config.pressure_bounds_kpa,
            objective_config.pressure_bounds_kpa,
            objective_config.vent_bounds,
        ],
        dtype=float,
    )
    seed = seed_design.to_array()
    raw = [
        seed,
        seed + np.array([-2.0, 0.0, 12.0, 10.0, -0.5]),
        seed + np.array([1.0, 8.0, 16.0, 6.0, -1.0]),
        seed + np.array([-1.0, -10.0, 8.0, 12.0, -0.5]),
    ]
    clipped = [np.clip(seed, bounds[:, 0], bounds[:, 1]) for seed in raw]
    unique: list[np.ndarray] = []
    seen = set()
    for seed in clipped:
        key = tuple(np.round(seed, 6))
        if key not in seen:
            seen.add(key)
            unique.append(seed)
    return unique


def _coordinate_pattern_refine(
    start_values: np.ndarray,
    bounds: list[tuple[float, float]],
    objective_fn,
    label: str,
) -> tuple[np.ndarray, float]:
    lower = np.array([bound[0] for bound in bounds], dtype=float)
    upper = np.array([bound[1] for bound in bounds], dtype=float)
    best_values = np.clip(np.asarray(start_values, dtype=float), lower, upper)
    best_objective = float(objective_fn(best_values))
    step_schedule = [
        np.array([2.0, 14.0, 14.0, 12.0, 2.5], dtype=float),
        np.array([1.0, 8.0, 8.0, 6.0, 1.25], dtype=float),
        np.array([0.5, 4.0, 4.0, 3.0, 0.6], dtype=float),
    ]

    for pass_index, steps in enumerate(step_schedule, start=1):
        improved = True
        accepted_moves = 0
        while improved and accepted_moves < 24:
            improved = False
            for dim in range(best_values.size):
                for direction in (-1.0, 1.0):
                    candidate = best_values.copy()
                    candidate[dim] = np.clip(candidate[dim] + direction * steps[dim], lower[dim], upper[dim])
                    if np.isclose(candidate[dim], best_values[dim]):
                        continue
                    candidate_objective = float(objective_fn(candidate))
                    if candidate_objective + 1.0e-6 < best_objective:
                        best_values = candidate
                        best_objective = candidate_objective
                        improved = True
                        accepted_moves += 1
        print(f"{label}: pass {pass_index}/{len(step_schedule)} best={best_objective:.4f}")
    return best_values, best_objective


def _progress_marks(total: int) -> set[int]:
    if total <= 0:
        return set()
    marks = set()
    for pct in range(10, 101, 10):
        marks.add(max(1, int(np.ceil(total * pct / 100.0))))
    return marks
