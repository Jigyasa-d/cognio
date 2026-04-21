from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "features.parquet"
MODEL_PATH = ROOT / "models" / "rf_prototype.joblib"
SCALER_PATH = ROOT / "models" / "scaler.joblib"
REPORT_PATH = ROOT / "reports" / "rf_evaluation.md"

FEATURE_COLUMNS = [
    "n_interactions",
    "accuracy",
    "accuracy_pct",
    "incorrect_rate",
    "avg_elapsed_time",
    "median_elapsed_time",
    "std_elapsed_time",
    "p90_elapsed_time",
    "long_response_rate",
    "retry_rate",
    "wrong_streak_max",
    "efficiency_score",
    "error_burden",
    "retry_burden",
    "time_pressure_index",
    "struggle_index",
    "consistency_index",
    "pace_ratio",
    "elapsed_range_proxy",
]

TARGET_COL = "target"
LABEL_COL = "strain_level"


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing file: {DATA_PATH}")

    df = pd.read_parquet(DATA_PATH).copy()

    required = FEATURE_COLUMNS + [TARGET_COL, LABEL_COL]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.dropna(subset=required).reset_index(drop=True)

    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COL].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train_scaled, y_train)

    preds = model.predict(X_test_scaled)
    probs = model.predict_proba(X_test_scaled)

    macro_f1 = f1_score(y_test, preds, average="macro")
    auc_roc = roc_auc_score(y_test, probs, multi_class="ovr")
    cm = confusion_matrix(y_test, preds)
    report = classification_report(
        y_test,
        preds,
        target_names=["LOW", "MODERATE", "HIGH"],
        digits=4,
        zero_division=0,
    )

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    cm_df = pd.DataFrame(
        cm,
        index=["Actual LOW", "Actual MODERATE", "Actual HIGH"],
        columns=["Pred LOW", "Pred MODERATE", "Pred HIGH"],
    )

    feature_importance = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    report_text = [
        "# Random Forest Evaluation Report",
        "",
        f"Dataset rows used: {len(df)}",
        f"Train rows: {len(X_train)}",
        f"Test rows: {len(X_test)}",
        "",
        f"Macro F1: {macro_f1:.4f}",
        f"AUC-ROC (OVR): {auc_roc:.4f}",
        "",
        "## Classification Report",
        "",
        "```",
        report,
        "```",
        "",
        "## Confusion Matrix",
        "",
        cm_df.to_markdown(),
        "",
        "## Feature Importances",
        "",
        feature_importance.to_markdown(index=False),
        "",
    ]

    REPORT_PATH.write_text("\n".join(report_text), encoding="utf-8")

    print(f"Saved model to: {MODEL_PATH}")
    print(f"Saved scaler to: {SCALER_PATH}")
    print(f"Saved report to: {REPORT_PATH}")
    print(f"Macro F1: {macro_f1:.4f}")
    print(f"AUC-ROC: {auc_roc:.4f}")


if __name__ == "__main__":
    main()