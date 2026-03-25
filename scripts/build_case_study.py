#!/usr/bin/env python3
"""Build sample datasets and visuals for the subsidy-response case study."""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def build_kpi_dataset() -> pd.DataFrame:
    quarters = [
        "2021-Q4",
        "2022-Q1",
        "2022-Q2",
        "2022-Q3",
        "2022-Q4",
        "2023-Q1",
        "2023-Q2",
        "2023-Q3",
        "2023-Q4",
    ]
    revenue_m = [118, 116, 110, 108, 112, 120, 126, 131, 138]
    operating_cost_m = [104, 106, 104, 100, 100, 103, 106, 108, 110]
    profit_m = [14, 10, 6, 8, 12, 17, 20, 23, 28]
    cashflow_m = [11, 8, 5, 7, 10, 14, 16, 19, 24]
    forecast_profit_m = [13, 9.5, 5.5, 7.2, 11, 15, 18, 22, 26]

    kpi = pd.DataFrame(
        {
            "quarter": quarters,
            "revenue_m": revenue_m,
            "operating_cost_m": operating_cost_m,
            "profit_m": profit_m,
            "cashflow_m": cashflow_m,
            "forecast_profit_m": forecast_profit_m,
        }
    )
    kpi["profit_margin_pct"] = (kpi["profit_m"] / kpi["revenue_m"] * 100).round(2)
    kpi["forecast_error_pct"] = (
        (kpi["forecast_profit_m"] - kpi["profit_m"]).abs() / kpi["profit_m"] * 100
    ).round(2)
    return kpi


def build_assumptions_dataset(kpi: pd.DataFrame) -> pd.DataFrame:
    mitigation_map = {
        "2021-Q4": 0.00,
        "2022-Q1": 0.00,
        "2022-Q2": 0.00,
        "2022-Q3": 0.20,
        "2022-Q4": 0.40,
        "2023-Q1": 0.60,
        "2023-Q2": 0.75,
        "2023-Q3": 0.85,
        "2023-Q4": 0.95,
    }

    rows = []
    for _, row in kpi.iterrows():
        quarter = row["quarter"]
        revenue = float(row["revenue_m"])
        actual_profit = float(row["profit_m"])
        gross_headwind = 0.05 * revenue if quarter >= "2022-Q2" else 0.0
        mitigation_effect = mitigation_map[quarter] * gross_headwind
        net_shock = gross_headwind - mitigation_effect
        no_intervention_profit = actual_profit - mitigation_effect

        rows.append(
            {
                "quarter": quarter,
                "assumed_gross_headwind_m": round(gross_headwind, 2),
                "assumed_mitigation_rate_pct": round(mitigation_map[quarter] * 100, 1),
                "assumed_mitigation_effect_m": round(mitigation_effect, 2),
                "assumed_net_shock_m": round(net_shock, 2),
                "counterfactual_profit_without_intervention_m": round(
                    no_intervention_profit, 2
                ),
                "actual_profit_m": round(actual_profit, 2),
                "implied_intervention_lift_m": round(mitigation_effect, 2),
            }
        )

    return pd.DataFrame(rows)


def plot_financial_trends(kpi: pd.DataFrame, output_file: Path) -> None:
    quarters = kpi["quarter"].tolist()
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7.2), sharex=True)

    subsidy_idx = quarters.index("2022-Q2")

    ax1.plot(quarters, kpi["revenue_m"], marker="o", label="Revenue ($M)", linewidth=2.4)
    ax1.plot(
        quarters,
        kpi["operating_cost_m"],
        marker="o",
        label="Operating Cost ($M)",
        linewidth=2.4,
    )
    ax1.axvspan(subsidy_idx - 0.5, len(quarters) - 0.5, color="#ffe8cc", alpha=0.35)
    ax1.set_ylabel("USD Millions")
    ax1.set_title(
        "Financial Trend Overview: Pre- and Post-Subsidy Reduction",
        fontsize=14,
        fontweight="bold",
    )
    ax1.legend(loc="upper left", ncol=2, fontsize=9)
    ax1.grid(alpha=0.25)

    ax2.plot(quarters, kpi["profit_m"], marker="o", label="Profit ($M)", linewidth=2.4)
    ax2.plot(
        quarters, kpi["cashflow_m"], marker="o", label="Cash Flow ($M)", linewidth=2.2
    )
    ax2.axvline(
        x="2022-Q2", color="#d9480f", linestyle="--", linewidth=1.8, label="Policy Shock"
    )
    ax2.axvspan(subsidy_idx - 0.5, len(quarters) - 0.5, color="#ffe8cc", alpha=0.35)
    ax2.set_ylabel("USD Millions")
    ax2.set_xlabel("Quarter")
    ax2.tick_params(axis="x", rotation=30)
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(alpha=0.25)

    low_profit_idx = int(np.argmin(kpi["profit_m"].values))
    ax2.annotate(
        "Low point",
        xy=(low_profit_idx, kpi["profit_m"].iloc[low_profit_idx]),
        xytext=(low_profit_idx + 0.6, kpi["profit_m"].iloc[low_profit_idx] + 4),
        arrowprops={"arrowstyle": "->", "color": "#343a40"},
        fontsize=9,
    )
    ax2.annotate(
        "Recovery trend",
        xy=(len(quarters) - 1, kpi["profit_m"].iloc[-1]),
        xytext=(len(quarters) - 3.2, kpi["profit_m"].iloc[-1] + 3.5),
        arrowprops={"arrowstyle": "->", "color": "#2b8a3e"},
        fontsize=9,
    )

    fig.tight_layout()
    fig.savefig(output_file, dpi=200)
    plt.close(fig)


def plot_forecast_vs_actual(kpi: pd.DataFrame, output_file: Path) -> None:
    quarters = kpi["quarter"].tolist()
    profit = kpi["profit_m"].tolist()
    forecast = kpi["forecast_profit_m"].tolist()
    errors = kpi["forecast_error_pct"].tolist()

    fig, ax = plt.subplots(figsize=(11, 5.2))
    idx = np.arange(len(quarters))
    width = 0.38
    ax.bar(idx - width / 2, profit, width, label="Actual Profit ($M)", color="#1f77b4")
    ax.bar(
        idx + width / 2,
        forecast,
        width,
        label="Forecast Profit ($M)",
        color="#ff7f0e",
    )
    avg_error = float(np.mean(errors))
    for i, err in enumerate(errors):
        ax.text(
            i,
            max(profit[i], forecast[i]) + 0.6,
            f"{err:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    ax.set_xticks(idx)
    ax.set_xticklabels(quarters, rotation=30)
    ax.set_title(
        "Forecast vs Actual Profit with Quarter-Level Error",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_ylabel("USD Millions")
    ax.set_xlabel("Quarter")
    ax.grid(axis="y", alpha=0.2)

    ax2 = ax.twinx()
    ax2.plot(idx, errors, color="#2b8a3e", marker="o", linewidth=2, label="Error %")
    ax2.axhline(avg_error, color="#2b8a3e", linestyle="--", linewidth=1.2)
    ax2.set_ylabel("Forecast Error (%)", color="#2b8a3e")
    ax2.tick_params(axis="y", colors="#2b8a3e")
    ax2.text(
        len(quarters) - 1.7,
        avg_error + 0.25,
        f"Avg error: {avg_error:.1f}%",
        color="#2b8a3e",
        fontsize=9,
    )

    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(handles1 + handles2, labels1 + labels2, fontsize=9, loc="upper left")

    fig.tight_layout()
    fig.savefig(output_file, dpi=200)
    plt.close(fig)


def plot_swot_matrix(output_file: Path) -> None:
    swot = {
        "Strengths": [8.5, 8.2, 8.8],
        "Weaknesses": [4.2, 3.9, 3.5],
        "Opportunities": [8.7, 8.9, 9.1],
        "Threats": [6.8, 6.1, 5.6],
    }
    labels = ["Cost Optimization", "Demand Forecasting", "Working Capital"]
    values = np.array([swot[k] for k in swot.keys()])

    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    image = ax.imshow(values, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=15)
    ax.set_yticks(np.arange(len(swot)))
    ax.set_yticklabels(list(swot.keys()))
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            text_color = "white" if values[i, j] >= 7.5 else "black"
            ax.text(
                j,
                i,
                f"{values[i, j]:.1f}",
                ha="center",
                va="center",
                color=text_color,
                fontsize=10,
                fontweight="bold",
            )
    ax.set_title(
        "SWOT Priority Heatmap (Higher Score = Higher Strategic Priority)",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Intervention Theme")
    ax.set_ylabel("SWOT Dimension")
    fig.colorbar(image, ax=ax, fraction=0.03, pad=0.03, label="Priority Score")
    fig.tight_layout()
    fig.savefig(output_file, dpi=200)
    plt.close(fig)


def plot_intervention_impact(assumptions: pd.DataFrame, output_file: Path) -> None:
    quarters = assumptions["quarter"].tolist()
    actual_profit = assumptions["actual_profit_m"].tolist()
    no_intervention = assumptions["counterfactual_profit_without_intervention_m"].tolist()
    lift = assumptions["implied_intervention_lift_m"].tolist()

    fig, ax = plt.subplots(figsize=(11, 5.4))
    idx = np.arange(len(quarters))

    ax.plot(idx, actual_profit, marker="o", linewidth=2.6, color="#1f77b4", label="Actual Profit")
    ax.plot(
        idx,
        no_intervention,
        marker="o",
        linewidth=2.2,
        linestyle="--",
        color="#868e96",
        label="Counterfactual (No Intervention)",
    )

    ax.fill_between(
        idx,
        no_intervention,
        actual_profit,
        where=np.array(actual_profit) >= np.array(no_intervention),
        color="#40c057",
        alpha=0.25,
        label="Intervention Lift",
    )

    for i, value in enumerate(lift):
        if value > 0:
            ax.text(i, actual_profit[i] + 0.45, f"+{value:.2f}", ha="center", fontsize=8.5)

    ax.set_xticks(idx)
    ax.set_xticklabels(quarters, rotation=30)
    ax.set_ylabel("USD Millions")
    ax.set_xlabel("Quarter")
    ax.set_title(
        "Profit Uplift from Cross-Functional Interventions (Assumption-Based)",
        fontsize=14,
        fontweight="bold",
    )
    ax.grid(alpha=0.22)
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    fig.savefig(output_file, dpi=200)
    plt.close(fig)


def main() -> None:
    matplotlib.use("Agg")
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    visuals_dir = root / "visuals"
    data_dir.mkdir(parents=True, exist_ok=True)
    visuals_dir.mkdir(parents=True, exist_ok=True)

    kpi = build_kpi_dataset()
    assumptions = build_assumptions_dataset(kpi)

    kpi.to_csv(data_dir / "kpi_summary.csv", index=False)
    assumptions.to_csv(data_dir / "assumptions_and_calculations.csv", index=False)

    plot_financial_trends(kpi, visuals_dir / "financial_trends.png")
    plot_forecast_vs_actual(kpi, visuals_dir / "forecast_vs_actual.png")
    plot_swot_matrix(visuals_dir / "swot_priority_scores.png")
    plot_intervention_impact(assumptions, visuals_dir / "intervention_impact.png")

    print("Build complete:")
    print(f"- {data_dir / 'kpi_summary.csv'}")
    print(f"- {data_dir / 'assumptions_and_calculations.csv'}")
    print(f"- {visuals_dir / 'financial_trends.png'}")
    print(f"- {visuals_dir / 'forecast_vs_actual.png'}")
    print(f"- {visuals_dir / 'swot_priority_scores.png'}")
    print(f"- {visuals_dir / 'intervention_impact.png'}")


if __name__ == "__main__":
    main()
