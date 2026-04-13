from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from src.feature_engineering import FEATURE_COLUMNS
from src.synthetic_generator import generate_dataset


ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
DATA_DIR = ROOT / "data"

MODEL_PATH = MODELS_DIR / "xgb_full.joblib"
REPORT_PATH = REPORTS_DIR / "xgb_evaluation.md"
RETRAIN_LOG = REPORTS_DIR / "retrain_log.json"


LABEL_MAP = {"LOW": 0, "MODERATE": 1, "HIGH": 2}
INV_LABEL_MAP = {v: k for k, v in LABEL_MAP.items()}


def load_training_data() -> pd.DataFrame:
    labeled_file = DATA_DIR / "labeled_sessions.parquet"
    if labeled_file.exists():
        try:
            return pd.read_parquet(labeled_file)
        except Exception:
            pass

    df = generate_dataset(per_class=500)
    return df


def train():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_training_data()
    df = df.dropna(subset=FEATURE_COLUMNS + ["strain_level"]).copy()

    X = df[FEATURE_COLUMNS]
    y = df["strain_level"].map(LABEL_MAP)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    f1 = f1_score(y_test, preds, average="macro")
    report = classification_report(
        y_test,
        preds,
        target_names=["LOW", "MODERATE", "HIGH"],
        digits=4
    )

    joblib.dump(model, MODEL_PATH)

    REPORT_PATH.write_text(
        "# XGBoost Evaluation Report\n\n"
        f"Macro F1: {f1:.4f}\n\n"
        "## Classification Report\n\n"
        f"```\n{report}\n```\n"
    )

    RETRAIN_LOG.write_text(
        json.dumps(
            {
                "status": "success",
                "model_path": str(MODEL_PATH),
                "macro_f1": round(float(f1), 4),
                "rows_used": int(len(df)),
            },
            indent=2,
        )
    )

    print(f"Model saved to: {MODEL_PATH}")
    print(f"Macro F1: {f1:.4f}")


if __name__ == "__main__":
    train()