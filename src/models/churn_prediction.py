from pathlib import Path
import json

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "data" / "processed" / "retail_transactions_cleaned.csv.gz"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"
OUTPUT_DIR = ROOT / "data" / "processed"

FEATURE_START = pd.Timestamp("2010-12-01")
FEATURE_END = pd.Timestamp("2011-06-30 23:59:59")
OBSERVATION_START = pd.Timestamp("2011-07-01")
OBSERVATION_END = pd.Timestamp("2011-09-30 23:59:59")

FEATURE_COLUMNS = [
    "recency_days",
    "invoice_count",
    "total_items",
    "total_spend",
    "average_line_value",
    "distinct_products",
    "active_days",
]


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}. Run the cleaning pipeline first."
        )

    print("Loading transactions...")
    df = pd.read_csv(DATA_FILE, compression="gzip", low_memory=False)
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")

    # Define qualifying purchases consistently for features and labels.
    sales = df[
        df["customer_id"].notna()
        & (~df["is_cancellation_invoice"].astype(bool))
        & (df["quantity"] > 0)
        & (df["unit_price"] > 0)
        & (df["line_revenue"] > 0)
        & df["invoice_date"].notna()
    ].copy()

    sales["customer_id"] = sales["customer_id"].astype("int64")

    historical = sales[
        sales["invoice_date"].between(FEATURE_START, FEATURE_END)
    ].copy()

    observation = sales[
        sales["invoice_date"].between(OBSERVATION_START, OBSERVATION_END)
    ].copy()

    if historical.empty or observation.empty:
        raise ValueError("Historical or observation window has no qualifying sales.")

    # Features use only purchases in the historical window.
    reference_date = FEATURE_END.normalize() + pd.Timedelta(days=1)

    features = historical.groupby("customer_id").agg(
        last_purchase=("invoice_date", "max"),
        invoice_count=("invoice", "nunique"),
        total_items=("quantity", "sum"),
        total_spend=("line_revenue", "sum"),
        average_line_value=("line_revenue", "mean"),
        distinct_products=("stock_code", "nunique"),
        active_days=("invoice_date", lambda values: values.dt.normalize().nunique()),
    )

    features["recency_days"] = (
        reference_date - features["last_purchase"].dt.normalize()
    ).dt.days

    features = features[FEATURE_COLUMNS].copy()

    # Label 1 means no qualifying purchase during July-September 2011.
    later_customers = set(observation["customer_id"].unique())
    features["churn"] = [
        0 if customer_id in later_customers else 1
        for customer_id in features.index
    ]

    X = features[FEATURE_COLUMNS].replace([float("inf"), float("-inf")], pd.NA)
    y = features["churn"].astype(int)

    class_counts = y.value_counts()
    if len(class_counts) < 2 or class_counts.min() < 2:
        raise ValueError(
            "Not enough examples in both churn classes for a stratified train/test split."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    candidates = {
        "Logistic Regression": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=42,
            )),
        ]),
        "Random Forest": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("model", RandomForestClassifier(
                n_estimators=200,
                min_samples_leaf=3,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            )),
        ]),
    }

    results = {}
    predictions = {}
    for name, model in candidates.items():
        print(f"Training {name}...")
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        probabilities = model.predict_proba(X_test)[:, 1]

        results[name] = {
            "accuracy": float(accuracy_score(y_test, pred)),
            "precision_churn": float(precision_score(
                y_test, pred, pos_label=1, zero_division=0
            )),
            "recall_churn": float(recall_score(
                y_test, pred, pos_label=1, zero_division=0
            )),
            "f1_churn": float(f1_score(
                y_test, pred, pos_label=1, zero_division=0
            )),
            "roc_auc": (
                float(roc_auc_score(y_test, probabilities))
                if y_test.nunique() == 2 else None
            ),
        }
        predictions[name] = (model, pred, probabilities)

    # Select by held-out churn-class F1; ties retain the first candidate.
    best_name = max(results, key=lambda name: results[name]["f1_churn"])
    best_model, best_pred, best_prob = predictions[best_name]

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model_path = MODEL_DIR / "churn_model.pkl"
    joblib.dump({
        "model": best_model,
        "feature_columns": FEATURE_COLUMNS,
        "selected_model": best_name,
        "feature_start": str(FEATURE_START.date()),
        "feature_end": str(FEATURE_END.date()),
        "observation_start": str(OBSERVATION_START.date()),
        "observation_end": str(OBSERVATION_END.date()),
        "target_definition": "1 = no qualifying purchase during observation window",
    }, model_path)

    test_output = pd.DataFrame({
        "customer_id": X_test.index,
        "actual_churn": y_test.values,
        "predicted_churn": best_pred,
        "churn_probability": best_prob,
    })
    test_output.to_csv(
        OUTPUT_DIR / "churn_test_predictions.csv", index=False
    )

    matrix = confusion_matrix(y_test, best_pred, labels=[0, 1])
    plt.figure(figsize=(6, 5))
    plt.imshow(matrix)
    plt.title(f"Churn Confusion Matrix - {best_name}")
    plt.xlabel("Predicted label")
    plt.ylabel("Actual label")
    plt.xticks([0, 1], ["Active", "Churn"])
    plt.yticks([0, 1], ["Active", "Churn"])
    for (i, j), value in __import__("numpy").ndenumerate(matrix):
        plt.text(j, i, str(value), ha="center", va="center")
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "figures" / "churn_confusion_matrix.png", dpi=150)
    plt.close()

    report_lines = [
        "RETAILPULSE - CUSTOMER CHURN PREDICTION",
        "=" * 50,
        f"Feature window: {FEATURE_START.date()} to {FEATURE_END.date()}",
        f"Observation window: {OBSERVATION_START.date()} to {OBSERVATION_END.date()}",
        "Target: 1 = no qualifying purchase in observation window; 0 = at least one",
        f"Customers labeled: {len(features):,}",
        f"Training customers: {len(X_train):,}",
        f"Test customers: {len(X_test):,}",
        "",
        "CLASS DISTRIBUTION",
        "-" * 50,
        y.value_counts().sort_index().rename(index={0: "Active", 1: "Churn"}).to_string(),
        "",
        "MODEL COMPARISON (HELD-OUT TEST SET)",
        "-" * 50,
        json.dumps(results, indent=2),
        "",
        f"Selected model by churn F1-score: {best_name}",
        "",
        "CLASSIFICATION REPORT",
        "-" * 50,
        classification_report(
            y_test, best_pred, labels=[0, 1],
            target_names=["Active", "Churn"], zero_division=0
        ),
        "CONFUSION MATRIX (rows=actual, columns=predicted; Active then Churn)",
        str(matrix),
        "",
        f"Saved model: {model_path}",
        f"Saved test predictions: {OUTPUT_DIR / 'churn_test_predictions.csv'}",
        f"Saved confusion matrix: {REPORT_DIR / 'figures' / 'churn_confusion_matrix.png'}",
        "",
        "LIMITATIONS",
        "-" * 50,
        "Churn is an operational definition based on a three-month no-purchase window.",
        "The model applies to customers with qualifying purchases in the feature window.",
        "This is a historical holdout evaluation, not proof of future performance.",
        "Customers first appearing after the feature window are not included.",
    ]

    report_path = REPORT_DIR / "churn_model_report.txt"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print("\n".join(report_lines))


if __name__ == "__main__":
    main()
