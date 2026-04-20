from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"

FEATURES_PATH = DATA_DIR / "features.parquet"
MODEL_PATH = MODELS_DIR / "xgb_full.joblib"
REPORT_PATH = REPORTS_DIR / "xgb_evaluation.md"
RETRAIN_LOG = REPORTS_DIR / "retrain_log.json"

LABEL_MAP = {"LOW": 0, "MODERATE": 1, "HIGH": 2}
INV_LABEL_MAP = {v: k for k, v in LABEL_MAP.items()}

TRAINING_FEATURE_COLUMNS = [
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
    "strain_score",
    "efficiency_score",
    "error_burden",
    "retry_burden",
    "time_pressure_index",
    "struggle_index",
    "consistency_index",
    "pace_ratio",
    "elapsed_range_proxy",
]


def load_training_data() -> pd.DataFrame:
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"Training features not found at {FEATURES_PATH}. "
            "Run feature_engineering.py first."
        )
    return pd.read_parquet(FEATURES_PATH)


def validate_training_frame(df: pd.DataFrame) -> pd.DataFrame:
    required_cols = TRAINING_FEATURE_COLUMNS + ["strain_level", "target"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required training columns: {missing}")

    clean_df = df.dropna(subset=required_cols).copy()
    if clean_df.empty:
        raise ValueError("Training dataframe is empty after dropping missing values.")

    class_counts = clean_df["target"].value_counts().sort_index()
    if len(class_counts) < 3:
        raise ValueError(
            f"Expected 3 classes, found {len(class_counts)} classes: {class_counts.to_dict()}"
        )

    if (class_counts < 2).any():
        raise ValueError(
            f"Each class needs at least 2 rows for stratified split. Found: {class_counts.to_dict()}"
        )

    return clean_df


def train() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading training data from: {FEATURES_PATH}")
    df = load_training_data()
    df = validate_training_frame(df)

    X = df[TRAINING_FEATURE_COLUMNS].copy()
    y = df["target"].astype(int)

    print("Training rows:", len(df))
    print("Class distribution:")
    print(df["strain_level"].value_counts())

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = XGBClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    macro_f1 = f1_score(y_test, preds, average="macro")
    report = classification_report(
        y_test,
        preds,
        target_names=["LOW", "MODERATE", "HIGH"],
        digits=4,
        zero_division=0,
    )

    artifact = {
        "model": model,
        "feature_columns": TRAINING_FEATURE_COLUMNS,
        "label_map": LABEL_MAP,
        "inverse_label_map": INV_LABEL_MAP,
    }
    joblib.dump(artifact, MODEL_PATH)

    REPORT_PATH.write_text(
        "# XGBoost Evaluation Report\n\n"
        f"Training rows used: {len(df)}\n\n"
        f"Train split rows: {len(X_train)}\n\n"
        f"Test split rows: {len(X_test)}\n\n"
        f"Macro F1: {macro_f1:.4f}\n\n"
        "## Classification Report\n\n"
        f"```\n{report}\n```\n"
    )

    RETRAIN_LOG.write_text(
        json.dumps(
            {
                "status": "success",
                "model_path": str(MODEL_PATH),
                "rows_used": int(len(df)),
                "train_rows": int(len(X_train)),
                "test_rows": int(len(X_test)),
                "macro_f1": round(float(macro_f1), 4),
                "feature_columns": TRAINING_FEATURE_COLUMNS,
                "class_distribution": df["strain_level"].value_counts().to_dict(),
            },
            indent=2,
        )
    )

    print(f"Model saved to: {MODEL_PATH}")
    print(f"Macro F1: {macro_f1:.4f}")
    print("Done.")


if __name__ == "__main__":
    train()