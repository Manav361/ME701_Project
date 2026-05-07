from __future__ import annotations

import json
from csv import DictWriter
from pathlib import Path
from textwrap import shorten

import matplotlib
matplotlib.use("Agg")
from matplotlib import animation
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch

from .baselines import MethodResult
from .optimize import EvaluationSummary, ScenarioMetrics
from .simulator import SimulationResult
from .uncertainty import CrashScenario


def save_summary(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def plot_metric_histograms(
    metrics_before: ScenarioMetrics,
    metrics_after: ScenarioMetrics,
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    axes[0].hist(metrics_before.hic, bins=20, alpha=0.7, label="Initial", color="#d95f02")
    axes[0].hist(metrics_after.hic, bins=20, alpha=0.6, label="Optimized", color="#1b9e77")
    axes[0].axvline(1000.0, color="black", linestyle="--", linewidth=1.0)
    axes[0].set_title("HIC Distribution")
    axes[0].set_xlabel("HIC")
    axes[0].set_ylabel("Count")
    axes[0].legend()

    axes[1].hist(metrics_before.chest_deflection_mm, bins=20, alpha=0.7, label="Initial", color="#d95f02")
    axes[1].hist(metrics_after.chest_deflection_mm, bins=20, alpha=0.6, label="Optimized", color="#1b9e77")
    axes[1].set_title("Chest Deflection Distribution")
    axes[1].set_xlabel("Chest Deflection (mm)")
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_method_comparison(results: list[MethodResult], output_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 7.5))
    names = [shorten(result.name, width=18, placeholder="...") for result in results]
    x = np.arange(len(results))
    colors = _method_colors(len(results))

    metrics = [
        ("Mean HIC", [result.summary.hic_mean for result in results]),
        ("HIC CVaR90", [result.summary.hic_cvar90 for result in results]),
        ("Chest Mean (mm)", [result.summary.chest_mean for result in results]),
        ("Failure Rate (%)", [100.0 * result.summary.failure_rate for result in results]),
    ]

    for ax, (title, values) in zip(axes.flat, metrics):
        ax.bar(x, values, color=colors)
        ax.set_title(title)
        ax.set_xticks(x, names, rotation=25, ha="right")
        ax.grid(axis="y", alpha=0.25)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_method_boxplots(results: list[MethodResult], output_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    labels = [shorten(result.name, width=16, placeholder="...") for result in results]
    hic_data = [result.metrics.hic for result in results]
    chest_data = [result.metrics.chest_deflection_mm for result in results]

    axes[0].boxplot(hic_data, tick_labels=labels, showfliers=False)
    axes[0].axhline(1000.0, color="black", linestyle="--", linewidth=1.0)
    axes[0].set_title("Scenario HIC Spread")
    axes[0].set_ylabel("HIC")
    axes[0].tick_params(axis="x", rotation=20)

    axes[1].boxplot(chest_data, tick_labels=labels, showfliers=False)
    axes[1].set_title("Scenario Chest Deflection Spread")
    axes[1].set_ylabel("Chest Deflection (mm)")
    axes[1].tick_params(axis="x", rotation=20)

    for ax in axes:
        ax.grid(axis="y", alpha=0.25)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_tradeoff(results: list[MethodResult], output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 6.0))
    colors = _method_colors(len(results))
    runtimes = np.array([result.runtime_s for result in results], dtype=float)
    sizes = 180.0 + 35.0 * np.sqrt(np.maximum(runtimes, 0.05))

    for color, size, result in zip(colors, sizes, results):
        ax.scatter(
            result.summary.hic_mean,
            result.summary.chest_mean,
            s=size,
            color=color,
            alpha=0.78,
            edgecolor="black",
            linewidth=0.7,
        )
        ax.annotate(result.name, (result.summary.hic_mean, result.summary.chest_mean), xytext=(6, 6), textcoords="offset points")

    ax.set_title("Method Trade-Off Map")
    ax.set_xlabel("Mean HIC")
    ax.set_ylabel("Mean Chest Deflection (mm)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_speed_hic_panels(
    scenarios: list[CrashScenario],
    results: list[MethodResult],
    output_path: Path,
) -> None:
    cols = 2
    rows = int(np.ceil(len(results) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(12.5, 4.0 * rows), squeeze=False)
    speeds = np.array([scenario.speed_mph for scenario in scenarios], dtype=float)

    for ax, result in zip(axes.flat, results):
        ax.scatter(speeds, result.metrics.hic, alpha=0.45, s=18, color="#386cb0")
        ax.axhline(1000.0, color="black", linestyle="--", linewidth=1.0)
        ax.set_title(result.name)
        ax.set_xlabel("Crash Speed (mph)")
        ax.set_ylabel("HIC")
        ax.grid(alpha=0.22)

    for ax in axes.flat[len(results) :]:
        ax.axis("off")

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_trace(trace: SimulationResult, output_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.8))
    t_ms = 1000.0 * trace.time_s

    axes[0, 0].plot(t_ms, 1000.0 * trace.displacement_m, color="#386cb0")
    axes[0, 0].set_title("Occupant Excursion")
    axes[0, 0].set_ylabel("Displacement (mm)")

    axes[0, 1].plot(t_ms, trace.pressure_kpa, color="#7fc97f")
    axes[0, 1].set_title("Airbag Pressure")
    axes[0, 1].set_ylabel("Pressure (kPa)")

    axes[1, 0].plot(t_ms, trace.head_acceleration_mps2 / 9.81, color="#ef3b2c")
    axes[1, 0].set_title("Head Proxy Acceleration")
    axes[1, 0].set_ylabel("Acceleration (g)")
    axes[1, 0].set_xlabel("Time (ms)")

    axes[1, 1].plot(t_ms, trace.belt_force_n, label="Belt", color="#4daf4a")
    axes[1, 1].plot(t_ms, trace.bag_force_n, label="Airbag", color="#984ea3")
    axes[1, 1].plot(t_ms, trace.hard_stop_force_n, label="Hard stop", color="#ff7f00")
    axes[1, 1].set_title("Restraint Loads")
    axes[1, 1].set_ylabel("Force (N)")
    axes[1, 1].set_xlabel("Time (ms)")
    axes[1, 1].legend()

    for ax in axes.flat:
        ax.grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def animate_crash_comparison(
    trace_reference: SimulationResult,
    trace_candidate: SimulationResult,
    scenario: CrashScenario,
    output_path: Path,
    reference_label: str = "Initial Design",
    candidate_label: str = "Optimized Design",
    fps: int = 20,
    frame_step: int = 2,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    indices = np.arange(0, min(len(trace_reference.time_s), len(trace_candidate.time_s)), max(1, frame_step))
    max_pressure = max(float(np.max(trace_reference.pressure_kpa)), float(np.max(trace_candidate.pressure_kpa)), 1.0)
    max_accel_g = max(
        float(np.max(np.abs(trace_reference.head_acceleration_mps2 / 9.81))),
        float(np.max(np.abs(trace_candidate.head_acceleration_mps2 / 9.81))),
        1.0,
    )
    max_chest = max(
        float(np.max(trace_reference.chest_deflection_trace_mm)),
        float(np.max(trace_candidate.chest_deflection_trace_mm)),
        1.0,
    )

    fig = plt.figure(figsize=(12.8, 7.2))
    grid = fig.add_gridspec(2, 2, height_ratios=[2.3, 1.2], hspace=0.28, wspace=0.16)
    ax_ref = fig.add_subplot(grid[0, 0])
    ax_cand = fig.add_subplot(grid[0, 1])
    ax_pressure = fig.add_subplot(grid[1, 0])
    ax_accel = fig.add_subplot(grid[1, 1])

    scene_ref = _build_crash_scene(ax_ref, reference_label)
    scene_cand = _build_crash_scene(ax_cand, candidate_label)

    time_ms_ref = 1000.0 * trace_reference.time_s
    time_ms_cand = 1000.0 * trace_candidate.time_s
    accel_ref_g = trace_reference.head_acceleration_mps2 / 9.81
    accel_cand_g = trace_candidate.head_acceleration_mps2 / 9.81

    ax_pressure.plot(time_ms_ref, trace_reference.pressure_kpa, color="#d95f02", linewidth=2.0, label=reference_label)
    ax_pressure.plot(time_ms_cand, trace_candidate.pressure_kpa, color="#1b9e77", linewidth=2.0, label=candidate_label)
    pressure_marker_ref, = ax_pressure.plot([], [], "o", color="#d95f02", markersize=6)
    pressure_marker_cand, = ax_pressure.plot([], [], "o", color="#1b9e77", markersize=6)
    pressure_cursor = ax_pressure.axvline(0.0, color="black", linestyle="--", linewidth=1.0, alpha=0.8)
    ax_pressure.set_title("Airbag Pressure")
    ax_pressure.set_xlabel("Time (ms)")
    ax_pressure.set_ylabel("Pressure (kPa)")
    ax_pressure.set_xlim(0.0, max(time_ms_ref[-1], time_ms_cand[-1]))
    ax_pressure.set_ylim(0.0, 1.08 * max_pressure)
    ax_pressure.grid(alpha=0.25)
    ax_pressure.legend(loc="upper right", fontsize=9)

    ax_accel.plot(time_ms_ref, accel_ref_g, color="#d95f02", linewidth=2.0, label=reference_label)
    ax_accel.plot(time_ms_cand, accel_cand_g, color="#1b9e77", linewidth=2.0, label=candidate_label)
    accel_marker_ref, = ax_accel.plot([], [], "o", color="#d95f02", markersize=6)
    accel_marker_cand, = ax_accel.plot([], [], "o", color="#1b9e77", markersize=6)
    accel_cursor = ax_accel.axvline(0.0, color="black", linestyle="--", linewidth=1.0, alpha=0.8)
    ax_accel.set_title("Head Proxy Acceleration")
    ax_accel.set_xlabel("Time (ms)")
    ax_accel.set_ylabel("Acceleration (g)")
    ax_accel.set_xlim(0.0, max(time_ms_ref[-1], time_ms_cand[-1]))
    ax_accel.set_ylim(-1.08 * max_accel_g, 1.08 * max_accel_g)
    ax_accel.grid(alpha=0.25)

    scenario_text = (
        f"Scenario: {scenario.speed_mph:.1f} mph, angle {scenario.angle_deg:.1f} deg, "
        f"offset {1000.0 * scenario.occupant_offset_m:.0f} mm, "
        f"{'belted' if scenario.belted else 'unbelted'}"
    )
    title = fig.suptitle(scenario_text, fontsize=13, y=0.98)

    def update(frame_number: int):
        idx = int(indices[frame_number])
        _update_crash_scene(scene_ref, trace_reference, idx, max_pressure, max_chest)
        _update_crash_scene(scene_cand, trace_candidate, idx, max_pressure, max_chest)

        t_ref = time_ms_ref[idx]
        t_cand = time_ms_cand[idx]
        pressure_marker_ref.set_data([t_ref], [trace_reference.pressure_kpa[idx]])
        pressure_marker_cand.set_data([t_cand], [trace_candidate.pressure_kpa[idx]])
        accel_marker_ref.set_data([t_ref], [accel_ref_g[idx]])
        accel_marker_cand.set_data([t_cand], [accel_cand_g[idx]])
        pressure_cursor.set_xdata([t_ref, t_ref])
        accel_cursor.set_xdata([t_ref, t_ref])
        title.set_text(f"{scenario_text} | time = {t_ref:.0f} ms")
        return (
            pressure_marker_ref,
            pressure_marker_cand,
            accel_marker_ref,
            accel_marker_cand,
            pressure_cursor,
            accel_cursor,
            title,
        )

    anim = animation.FuncAnimation(
        fig,
        update,
        frames=len(indices),
        interval=1000.0 / max(1, fps),
        blit=False,
    )
    anim.save(output_path, writer=animation.PillowWriter(fps=fps), dpi=120)
    plt.close(fig)


def summary_to_dict(summary: EvaluationSummary) -> dict:
    return {
        "design": {
            "trigger_delay_ms": summary.design.trigger_delay_ms,
            "pressure_early_kpa": summary.design.pressure_early_kpa,
            "pressure_mid_kpa": summary.design.pressure_mid_kpa,
            "pressure_late_kpa": summary.design.pressure_late_kpa,
            "vent_rate": summary.design.vent_rate,
        },
        "objective": summary.objective,
        "hic_mean": summary.hic_mean,
        "hic_std": summary.hic_std,
        "hic_cvar90": summary.hic_cvar90,
        "chest_mean": summary.chest_mean,
        "chest_std": summary.chest_std,
        "failure_rate_hic_gt_1000": summary.failure_rate,
        "energy_mean": summary.energy_mean,
        "false_deployment_rate": summary.false_deployment_rate,
    }


def save_metrics_csv(output_path: Path, scenarios: list[CrashScenario], results: list[MethodResult]) -> None:
    method_keys = [_method_key(result.name) for result in results]
    fieldnames = [
        "scenario_id",
        "speed_mph",
        "angle_deg",
        "occupant_offset_m",
        "belted",
        "sensor_delay_s",
        "pulse_duration_s",
        "crash_active",
    ]
    for key in method_keys:
        fieldnames.extend([f"hic_{key}", f"chest_{key}", f"energy_{key}", f"false_deploy_{key}"])

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for i, scenario in enumerate(scenarios):
            row = {
                "scenario_id": i,
                "speed_mph": scenario.speed_mph,
                "angle_deg": scenario.angle_deg,
                "occupant_offset_m": scenario.occupant_offset_m,
                "belted": int(scenario.belted),
                "sensor_delay_s": scenario.sensor_delay_s,
                "pulse_duration_s": scenario.pulse_duration_s,
                "crash_active": int(scenario.crash_active),
            }
            for key, result in zip(method_keys, results):
                row[f"hic_{key}"] = result.metrics.hic[i]
                row[f"chest_{key}"] = result.metrics.chest_deflection_mm[i]
                row[f"energy_{key}"] = result.metrics.energy[i]
                row[f"false_deploy_{key}"] = result.metrics.false_deployment[i]
            writer.writerow(row)


def save_comparison_table(results: list[MethodResult], output_csv: Path, output_md: Path) -> None:
    rows = [_result_row(result) for result in results]
    fieldnames = list(rows[0].keys())
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    header = "| " + " | ".join(fieldnames) + " |\n"
    separator = "| " + " | ".join(["---"] * len(fieldnames)) + " |\n"
    body = "".join("| " + " | ".join(_stringify(row[key]) for key in fieldnames) + " |\n" for row in rows)
    output_md.write_text(header + separator + body, encoding="utf-8")


def save_design_table(results: list[MethodResult], output_csv: Path, output_md: Path) -> None:
    rows = []
    for result in results:
        design = result.design if result.design is not None else result.design_mean
        row = {
            "method": result.name,
            "design_type": "fixed" if result.design is not None else "adaptive_mean",
            "trigger_delay_ms": _maybe_value(design, "trigger_delay_ms"),
            "pressure_early_kpa": _maybe_value(design, "pressure_early_kpa"),
            "pressure_mid_kpa": _maybe_value(design, "pressure_mid_kpa"),
            "pressure_late_kpa": _maybe_value(design, "pressure_late_kpa"),
            "vent_rate": _maybe_value(design, "vent_rate"),
        }
        rows.append(row)

    fieldnames = list(rows[0].keys())
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    header = "| " + " | ".join(fieldnames) + " |\n"
    separator = "| " + " | ".join(["---"] * len(fieldnames)) + " |\n"
    body = "".join("| " + " | ".join(_stringify(row[key]) for key in fieldnames) + " |\n" for row in rows)
    output_md.write_text(header + separator + body, encoding="utf-8")


def save_method_summary_json(results: list[MethodResult], path: Path) -> None:
    payload = {"methods": [_method_result_to_dict(result) for result in results]}
    save_summary(path, payload)


def _method_key(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


def _result_row(result: MethodResult) -> dict:
    return {
        "method": result.name,
        "type": result.method_type,
        "runtime_s": round(result.runtime_s, 3),
        "objective": round(result.summary.objective, 4),
        "hic_mean": round(result.summary.hic_mean, 2),
        "hic_std": round(result.summary.hic_std, 2),
        "hic_cvar90": round(result.summary.hic_cvar90, 2),
        "chest_mean_mm": round(result.summary.chest_mean, 2),
        "chest_std_mm": round(result.summary.chest_std, 2),
        "failure_rate_pct": round(100.0 * result.summary.failure_rate, 2),
        "false_deployment_rate_pct": round(100.0 * result.summary.false_deployment_rate, 2),
        "energy_mean": round(result.summary.energy_mean, 4),
    }


def _method_result_to_dict(result: MethodResult) -> dict:
    return {
        "name": result.name,
        "method_type": result.method_type,
        "runtime_s": result.runtime_s,
        "summary": {
            "objective": result.summary.objective,
            "hic_mean": result.summary.hic_mean,
            "hic_std": result.summary.hic_std,
            "hic_cvar90": result.summary.hic_cvar90,
            "chest_mean": result.summary.chest_mean,
            "chest_std": result.summary.chest_std,
            "failure_rate_hic_gt_1000": result.summary.failure_rate,
            "false_deployment_rate": result.summary.false_deployment_rate,
            "energy_mean": result.summary.energy_mean,
        },
        "design": _design_dict(result.design),
        "design_mean": _design_dict(result.design_mean),
    }


def _design_dict(design) -> dict | None:
    if design is None:
        return None
    return {
        "trigger_delay_ms": float(design.trigger_delay_ms),
        "pressure_early_kpa": float(design.pressure_early_kpa),
        "pressure_mid_kpa": float(design.pressure_mid_kpa),
        "pressure_late_kpa": float(design.pressure_late_kpa),
        "vent_rate": float(design.vent_rate),
    }


def _maybe_value(design, field: str) -> float | str:
    if design is None:
        return "n/a"
    return round(float(getattr(design, field)), 3)


def _stringify(value) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _method_colors(count: int) -> list[str]:
    palette = [
        "#7570b3",
        "#e7298a",
        "#66a61e",
        "#1b9e77",
        "#d95f02",
        "#386cb0",
        "#e6ab02",
        "#a6761d",
    ]
    if count <= len(palette):
        return palette[:count]
    return [palette[i % len(palette)] for i in range(count)]


def _build_crash_scene(ax, title: str) -> dict:
    ax.set_title(title)
    ax.set_xlim(0.0, 0.40)
    ax.set_ylim(0.0, 0.24)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#f7f4ea")

    seat = FancyBboxPatch((0.015, 0.04), 0.05, 0.12, boxstyle="round,pad=0.01", facecolor="#7f8c8d", edgecolor="#2d3436")
    seat_base = FancyBboxPatch((0.00, 0.01), 0.10, 0.03, boxstyle="round,pad=0.01", facecolor="#95a5a6", edgecolor="#2d3436")
    dashboard = FancyBboxPatch((0.345, 0.0), 0.045, 0.22, boxstyle="round,pad=0.01", facecolor="#2c3e50", edgecolor="#17202a")
    windshield = FancyBboxPatch((0.318, 0.17), 0.06, 0.05, boxstyle="round,pad=0.01", facecolor="#d6eaf8", edgecolor="#7fb3d5")
    ax.add_patch(seat)
    ax.add_patch(seat_base)
    ax.add_patch(dashboard)
    ax.add_patch(windshield)
    ax.plot([0.335, 0.335], [0.0, 0.22], color="#34495e", linestyle="--", linewidth=1.4, alpha=0.8)
    ax.text(0.337, 0.215, "hard stop", fontsize=8, color="#34495e", va="top")

    bag = Ellipse((0.287, 0.105), 0.04, 0.09, facecolor="#85c1e9", edgecolor="#2e86c1", alpha=0.15, linewidth=2.0)
    torso = Circle((0.075, 0.085), 0.028, facecolor="#f5cba7", edgecolor="#935116", linewidth=2.0)
    head = Circle((0.118, 0.145), 0.021, facecolor="#fad7a0", edgecolor="#935116", linewidth=2.0)
    belt, = ax.plot([0.045, 0.075], [0.135, 0.085], color="#27ae60", linewidth=3.0)
    neck, = ax.plot([0.097, 0.118], [0.106, 0.125], color="#7d6608", linewidth=2.4)
    chest_text = ax.text(0.012, 0.216, "", fontsize=9, ha="left", va="top", color="#6e2c00")
    hic_text = ax.text(0.012, 0.195, "", fontsize=9, ha="left", va="top", color="#6e2c00")
    pressure_text = ax.text(0.012, 0.174, "", fontsize=9, ha="left", va="top", color="#1f618d")

    ax.add_patch(bag)
    ax.add_patch(torso)
    ax.add_patch(head)

    return {
        "ax": ax,
        "bag": bag,
        "torso": torso,
        "head": head,
        "belt": belt,
        "neck": neck,
        "chest_text": chest_text,
        "hic_text": hic_text,
        "pressure_text": pressure_text,
    }


def _update_crash_scene(scene: dict, trace: SimulationResult, idx: int, max_pressure: float, max_chest: float) -> None:
    base_torso_x = 0.075
    base_head_x = 0.118
    torso_y = 0.085
    head_y = 0.145

    torso_x = base_torso_x + float(trace.displacement_m[idx])
    head_x = base_head_x + float(trace.head_displacement_m[idx])
    pressure_ratio = float(trace.pressure_kpa[idx] / max_pressure)
    chest_ratio = float(trace.chest_deflection_trace_mm[idx] / max(max_chest, 1.0))

    scene["torso"].center = (torso_x, torso_y)
    scene["head"].center = (head_x, head_y)
    scene["neck"].set_data([torso_x + 0.020, head_x], [torso_y + 0.022, head_y - 0.020])
    scene["belt"].set_data([0.045, torso_x], [0.135, torso_y])

    scene["bag"].center = (0.287 - 0.012 * pressure_ratio, 0.105)
    scene["bag"].width = 0.035 + 0.085 * pressure_ratio
    scene["bag"].height = 0.070 + 0.085 * pressure_ratio
    scene["bag"].set_alpha(0.12 + 0.48 * pressure_ratio)

    scene["torso"].set_facecolor("#f5cba7" if trace.hard_stop_force_n[idx] <= 1.0 else "#f1948a")
    scene["chest_text"].set_text(f"Chest: {trace.chest_deflection_trace_mm[idx]:.1f} mm")
    scene["hic_text"].set_text(f"Head accel: {trace.head_acceleration_mps2[idx] / 9.81:.1f} g")
    scene["pressure_text"].set_text(f"Pressure: {trace.pressure_kpa[idx]:.0f} kPa")
    scene["belt"].set_linewidth(2.5 + 2.5 * chest_ratio)
