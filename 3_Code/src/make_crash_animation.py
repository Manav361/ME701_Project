from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from airbag_project.config import ModelConfig, ObjectiveWeights, OptimizationConfig
from airbag_project.reporting import animate_crash_comparison
from airbag_project.simulator import DeploymentDesign, simulate_design
from airbag_project.uncertainty import sample_scenarios


def main() -> None:
    output_dir = _latest_output_dir(Path("outputs"))
    methods_path = output_dir / "02_shifted_methods.json"
    metrics_path = output_dir / "02_shifted_scenario_metrics.csv"
    output_path = output_dir / "02_shifted_initial_vs_shift_refined_animation.gif"

    methods = json.loads(methods_path.read_text(encoding="utf-8"))["methods"]
    initial_design = _load_design(methods, "Initial Design")
    candidate_name = "Shift-Refined Local Search"
    candidate_design = _load_design(methods, candidate_name)

    scenario_index = _select_animation_scenario_index(metrics_path, "hic_shift_refined_local_search")
    scenarios = _recreate_shifted_eval_scenarios()
    scenario = scenarios[scenario_index]

    initial_trace = simulate_design(initial_design, scenario, ModelConfig())
    candidate_trace = simulate_design(candidate_design, scenario, ModelConfig())

    animate_crash_comparison(
        initial_trace,
        candidate_trace,
        scenario,
        output_path=output_path,
        reference_label="Initial Design",
        candidate_label=candidate_name,
        fps=20,
        frame_step=2,
    )
    print(f"Animation written to: {output_path.resolve()}")
    print(
        "Scenario used:",
        {
            "scenario_index": scenario_index,
            "speed_mph": round(scenario.speed_mph, 3),
            "angle_deg": round(scenario.angle_deg, 3),
            "occupant_offset_m": round(scenario.occupant_offset_m, 4),
            "belted": scenario.belted,
            "sensor_delay_s": round(scenario.sensor_delay_s, 5),
            "pulse_duration_s": round(scenario.pulse_duration_s, 5),
        },
    )


def _latest_output_dir(base_dir: Path) -> Path:
    candidates = []
    for child in base_dir.iterdir():
        if child.is_dir():
            prefix = child.name.split("_", 1)[0]
            if prefix.isdigit():
                candidates.append((int(prefix), child))
    if not candidates:
        raise FileNotFoundError("No output directories found in outputs/.")
    return max(candidates, key=lambda item: item[0])[1]


def _load_design(methods: list[dict], name: str) -> DeploymentDesign:
    method = next(item for item in methods if item["name"] == name)
    design = method["design_mean"] if method["design"] is None else method["design"]
    return DeploymentDesign(
        trigger_delay_ms=float(design["trigger_delay_ms"]),
        pressure_early_kpa=float(design["pressure_early_kpa"]),
        pressure_mid_kpa=float(design["pressure_mid_kpa"]),
        pressure_late_kpa=float(design["pressure_late_kpa"]),
        vent_rate=float(design["vent_rate"]),
    )


def _select_animation_scenario_index(metrics_path: Path, metric_key: str) -> int:
    with metrics_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        best_index = 0
        best_value = float("-inf")
        for row in reader:
            value = float(row[metric_key])
            if value > best_value:
                best_value = value
                best_index = int(row["scenario_id"])
    return best_index


def _recreate_shifted_eval_scenarios() -> list:
    model_config = ModelConfig()
    opt_config = OptimizationConfig()
    rng = np.random.default_rng(opt_config.seed)
    sample_scenarios(opt_config.training_scenarios, rng, model_config, profile="default")
    sample_scenarios(opt_config.shifted_training_scenarios, rng, model_config, profile="shifted_eval")
    sample_scenarios(opt_config.evaluation_scenarios, rng, model_config, profile="default")
    return sample_scenarios(opt_config.evaluation_scenarios, rng, model_config, profile="shifted_eval")


if __name__ == "__main__":
    main()
