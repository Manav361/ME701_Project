from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import shorten

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import beta as beta_dist
from scipy.stats import norm

from .config import ModelConfig


@dataclass(frozen=True)
class DistributionMethodSummary:
    method: str
    bucket: str
    scenario_count: int
    hic_mean: float
    chest_mean: float
    failure_rate_pct: float
    energy_mean: float


def load_scenario_metrics(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def add_rarity_columns(data: pd.DataFrame, config: ModelConfig) -> pd.DataFrame:
    scored = data.copy()
    scored["rarity_score"] = _rarity_score(scored, config)
    q1, q2 = scored["rarity_score"].quantile([1 / 3, 2 / 3]).to_list()
    scored["rarity_bucket"] = np.where(
        scored["rarity_score"] <= q1,
        "Common",
        np.where(scored["rarity_score"] <= q2, "Moderate", "Rare"),
    )
    return scored


def summarize_by_rarity(data: pd.DataFrame) -> list[DistributionMethodSummary]:
    method_names = _method_names(data.columns)
    summaries: list[DistributionMethodSummary] = []
    for bucket in ["Common", "Moderate", "Rare"]:
        bucket_df = data[data["rarity_bucket"] == bucket]
        for method in method_names:
            hic_col = f"hic_{method}"
            chest_col = f"chest_{method}"
            energy_col = f"energy_{method}"
            summaries.append(
                DistributionMethodSummary(
                    method=method,
                    bucket=bucket,
                    scenario_count=int(len(bucket_df)),
                    hic_mean=float(bucket_df[hic_col].mean()),
                    chest_mean=float(bucket_df[chest_col].mean()),
                    failure_rate_pct=float(100.0 * (bucket_df[hic_col] > 1000.0).mean()),
                    energy_mean=float(bucket_df[energy_col].mean()),
                )
            )
    return summaries


def save_rarity_table(summaries: list[DistributionMethodSummary], output_csv: Path, output_md: Path) -> None:
    rows = [
        {
            "bucket": summary.bucket,
            "method": _pretty_method(summary.method),
            "scenario_count": summary.scenario_count,
            "hic_mean": round(summary.hic_mean, 2),
            "chest_mean_mm": round(summary.chest_mean, 2),
            "failure_rate_pct": round(summary.failure_rate_pct, 2),
            "energy_mean": round(summary.energy_mean, 4),
        }
        for summary in summaries
    ]
    frame = pd.DataFrame(rows)
    frame.to_csv(output_csv, index=False)
    output_md.write_text(frame.to_markdown(index=False), encoding="utf-8")


def plot_rarity_performance(summaries: list[DistributionMethodSummary], output_path: Path) -> None:
    buckets = ["Common", "Moderate", "Rare"]
    methods = list(dict.fromkeys(summary.method for summary in summaries))
    pretty = [_pretty_method(method) for method in methods]
    x = np.arange(len(methods))
    width = 0.22
    colors = ["#1b9e77", "#d95f02", "#7570b3"]

    fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.8))
    metric_getters = [
        ("Mean HIC", lambda s: s.hic_mean),
        ("Failure Rate (%)", lambda s: s.failure_rate_pct),
        ("Mean Chest Deflection (mm)", lambda s: s.chest_mean),
    ]

    for ax, (title, getter) in zip(axes, metric_getters):
        for idx, bucket in enumerate(buckets):
            subset = [summary for summary in summaries if summary.bucket == bucket]
            values = [getter(next(item for item in subset if item.method == method)) for method in methods]
            ax.bar(x + (idx - 1) * width, values, width=width, label=bucket, color=colors[idx])
        ax.set_title(title)
        ax.set_xticks(x, [shorten(name, width=16, placeholder="...") for name in pretty], rotation=20, ha="right")
        ax.grid(axis="y", alpha=0.25)
        if title == "Mean HIC":
            ax.axhline(1000.0, linestyle="--", linewidth=1.0, color="black")

    axes[0].legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_rarity_score_scatter(data: pd.DataFrame, output_path: Path) -> None:
    methods = _method_names(data.columns)
    fig, axes = plt.subplots(len(methods), 1, figsize=(10.5, 2.5 * len(methods)), sharex=True)
    axes = np.atleast_1d(axes)
    rarity = data["rarity_score"].to_numpy()

    for ax, method in zip(axes, methods):
        hic = data[f"hic_{method}"].to_numpy()
        ax.scatter(rarity, hic, s=14, alpha=0.45, color="#386cb0")
        ax.axhline(1000.0, linestyle="--", linewidth=1.0, color="black")
        ax.set_ylabel(shorten(_pretty_method(method), width=16, placeholder="..."))
        ax.grid(alpha=0.22)

    axes[-1].set_xlabel("Scenario rarity score (higher = rarer)")
    fig.suptitle("HIC vs Scenario Rarity", y=0.995)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_bucket_winners(summaries: list[DistributionMethodSummary], output_path: Path) -> None:
    buckets = ["Common", "Moderate", "Rare"]
    records = {bucket: [summary for summary in summaries if summary.bucket == bucket] for bucket in buckets}
    best_hic = [min(records[bucket], key=lambda s: s.hic_mean).method for bucket in buckets]
    best_failure = [min(records[bucket], key=lambda s: s.failure_rate_pct).method for bucket in buckets]
    best_energy = [min(records[bucket], key=lambda s: s.energy_mean).method for bucket in buckets]

    labels = ["Best Mean HIC", "Best Failure Rate", "Best Energy"]
    values = [best_hic, best_failure, best_energy]

    fig, ax = plt.subplots(figsize=(9.2, 3.6))
    ax.axis("off")

    table_data = [[label] + [_pretty_method(method) for method in row] for label, row in zip(labels, values)]
    table = ax.table(
        cellText=table_data,
        colLabels=["Metric"] + buckets,
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.7)
    ax.set_title("Best Method by Scenario Rarity Bucket")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def _method_names(columns: list[str] | pd.Index) -> list[str]:
    names = []
    for col in columns:
        if col.startswith("hic_"):
            names.append(col.removeprefix("hic_"))
    return names


def _pretty_method(method: str) -> str:
    mapping = {
        "initial_design": "Initial Design",
        "deterministic_sqp": "Deterministic SQP",
        "grid_search": "Grid Search",
        "mpc_inspired_policy": "MPC-Inspired Policy",
        "robust_de+slsqp": "Robust DE+SLSQP",
        "shift_refined_local_search": "Shift-Refined Local Search",
    }
    return mapping.get(method, method.replace("_", " "))


def _rarity_score(data: pd.DataFrame, config: ModelConfig) -> np.ndarray:
    speed_u = np.clip(
        (data["speed_mph"].to_numpy(dtype=float) - config.speed_min_mph)
        / (config.speed_max_mph - config.speed_min_mph),
        1.0e-6,
        1.0 - 1.0e-6,
    )
    angle_u = np.clip(np.abs(data["angle_deg"].to_numpy(dtype=float)) / 35.0, 1.0e-6, 1.0 - 1.0e-6)
    offset = data["occupant_offset_m"].to_numpy(dtype=float)
    sensor = data["sensor_delay_s"].to_numpy(dtype=float)
    pulse = data["pulse_duration_s"].to_numpy(dtype=float)
    belted = data["belted"].to_numpy(dtype=int)

    logp_speed = beta_dist.logpdf(speed_u, 2.1, 1.7)
    logp_angle = beta_dist.logpdf(angle_u, 2.5, 3.0) - np.log(35.0)
    logp_offset = norm.logpdf(offset, loc=config.seat_position_bias, scale=config.seat_position_spread)
    logp_sensor = norm.logpdf(sensor, loc=0.0, scale=max(config.sensor_sigma, 1.0e-6))
    logp_pulse = norm.logpdf(pulse, loc=config.nominal_pulse_duration, scale=max(config.pulse_duration_spread, 1.0e-6))
    logp_belt = np.where(belted == 1, np.log(0.9), np.log(0.1))

    total_logp = logp_speed + logp_angle + logp_offset + logp_sensor + logp_pulse + logp_belt
    rarity = -total_logp
    return rarity - np.min(rarity)
