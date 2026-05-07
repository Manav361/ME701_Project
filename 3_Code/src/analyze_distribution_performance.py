from __future__ import annotations

from pathlib import Path

from airbag_project.config import ModelConfig
from airbag_project.distribution_analysis import (
    add_rarity_columns,
    load_scenario_metrics,
    plot_bucket_winners,
    plot_rarity_performance,
    plot_rarity_score_scatter,
    save_rarity_table,
    summarize_by_rarity,
)


def main() -> None:
    output_dir = Path("outputs")
    metrics_path = output_dir / "scenario_metrics.csv"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing scenario metrics file: {metrics_path}")

    config = ModelConfig()
    data = load_scenario_metrics(metrics_path)
    scored = add_rarity_columns(data, config)
    summaries = summarize_by_rarity(scored)

    scored.to_csv(output_dir / "scenario_metrics_with_rarity.csv", index=False)
    save_rarity_table(summaries, output_dir / "rarity_comparison.csv", output_dir / "rarity_comparison.md")
    plot_rarity_performance(summaries, output_dir / "rarity_performance.png")
    plot_rarity_score_scatter(scored, output_dir / "rarity_hic_scatter.png")
    plot_bucket_winners(summaries, output_dir / "rarity_winners.png")

    print("Distribution-wise analysis saved under:", output_dir.resolve())


if __name__ == "__main__":
    main()
