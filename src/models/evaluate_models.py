from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    sections = [
        "RETAILPULSE - CONSOLIDATED MODEL EVALUATION",
        "=" * 55,
        "",
        "1. CUSTOMER CHURN PREDICTION",
        "-" * 55,
    ]

    churn_report = REPORT_DIR / "churn_model_report.txt"
    if churn_report.exists():
        sections.append(churn_report.read_text(encoding="utf-8"))
    else:
        sections.append("Churn report not found. Run churn_prediction.py first.")

    sections.extend([
        "",
        "2. DEMAND FORECASTING",
        "-" * 55,
    ])

    forecast_file = DATA_DIR / "forecast_evaluation.csv"
    if forecast_file.exists():
        metrics = pd.read_csv(forecast_file)
        summary = metrics.groupby("baseline")[["mae", "rmse"]].mean().round(3)
        sections.append("Average metrics across evaluated products:")
        sections.append(summary.to_string())
        sections.append("")
        sections.append("Per-product results:")
        sections.append(metrics.to_string(index=False))
    else:
        sections.append(
            "Forecast metrics not found. Run demand_forecasting.py first."
        )

    sections.extend([
        "",
        "3. CUSTOMER SEGMENTATION",
        "-" * 55,
    ])

    segment_file = REPORT_DIR / "customer_cluster_summary.csv"
    if segment_file.exists():
        sections.append(pd.read_csv(segment_file).to_string(index=False))
    else:
        sections.append(
            "Cluster summary not found. Run customer_segmentation.py first."
        )

    sections.extend([
        "",
        "4. INVENTORY PLANNING",
        "-" * 55,
    ])

    inventory_file = DATA_DIR / "inventory_recommendations.csv"
    if inventory_file.exists():
        inventory = pd.read_csv(inventory_file)
        sections.append(f"Products analyzed: {len(inventory)}")
        sections.append(
            "Products flagged for reorder: "
            + str((inventory["planning_status"] == "Reorder suggested").sum())
        )
        sections.append(inventory.to_string(index=False))
        sections.append(
            "Inventory quantities depend on assumed stock levels and lead times."
        )
    else:
        sections.append(
            "Inventory recommendations not found. "
            "Run inventory_optimization.py first."
        )

    sections.extend([
        "",
        "5. EVALUATION NOTES",
        "-" * 55,
        "- Churn metrics use a historical holdout split and a defined churn window.",
        "- Forecast MAE and RMSE are measured in units and depend on each product's scale.",
        "- Forecast baseline selection used the evaluation period; results are not an untouched final test.",
        "- Customer cluster IDs are arbitrary and must be interpreted from their profiles.",
        "- Inventory recommendations use assumptions rather than actual stock records.",
        "- Do not describe these results as production performance without further validation.",
    ])

    output_file = REPORT_DIR / "model_evaluation_summary.txt"
    output_file.write_text("\n".join(sections), encoding="utf-8")

    print("Consolidated evaluation report created:")
    print(output_file)
    print("\nSections included:")
    print("Churn prediction, demand forecasting, customer segmentation, inventory planning")


if __name__ == "__main__":
    main()
