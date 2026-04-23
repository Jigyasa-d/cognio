from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
import optuna
import pandas as pd
from sklearn.metrics import classification_report, f1_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from xgboost import XGBClassifier

from src.drift_detector import should_retrain

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"

FEATURES_PATH = DATA_DIR / "features.parquet"
NEW_FEATURES_PATH = DATA_DIR / "new_features.parquet"

MODEL_PATH = MODELS_DIR / "xgb_full.joblib"
CANDIDATE_MODEL_PATH = MODELS_DIR / "xgb_candidate.joblib"
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
    "efficiency_score",
    "error_burden",
    "retry_burden",
    "time_pressure_index",
    "struggle_index",
    "consistency_index",
    "pace_ratio",
    "elapsed_range_proxy",
]


def load_base_data() -> pd.DataFrame:
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"Training features not found at {FEATURES_PATH}. Run feature_engineering.py first."
        )
    return pd.read_parquet(FEATURES_PATH)


def merge_new_data(base_df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    if not NEW_FEATURES_PATH.exists():
        return base_df.copy(), False

    new_df = pd.read_parquet(NEW_FEATURES_PATH).copy()
    combined = pd.concat([base_df, new_df], ignore_index=True)

    if "session_id" in combined.columns:
        combined = combined.drop_duplicates(subset=["session_id"], keep="last")
    else:
        combined = combined.drop_duplicates()

    return combined, True


def validate_training_frame(df: pd.DataFrame) -> pd.DataFrame:
    required_cols = TRAINING_FEATURE_COLUMNS + ["user_id", "strain_level", "target"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required training columns: {missing}")

    clean_df = df.dropna(subset=required_cols).copy()

    if clean_df.empty:
        raise ValueError("Training dataframe is empty after dropping missing values.")

    class_counts = clean_df["target"].value_counts().sort_index()
    if len(class_counts) < 3:
        raise ValueError(f"Expected 3 classes, found {len(class_counts)} classes: {class_counts.to_dict()}")

    if (class_counts < 2).any():
        raise ValueError(f"Each class needs at least 2 rows. Found: {class_counts.to_dict()}")

    if clean_df["user_id"].nunique() < 2:
        raise ValueError("Need at least 2 unique users for user-level train/test split.")

    return clean_df


def group_train_test_split(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
):
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    groups = df["user_id"]

    train_idx, test_idx = next(splitter.split(df, groups=groups))
    train_df = df.iloc[train_idx].copy()
    test_df = df.iloc[test_idx].copy()

    train_classes = set(train_df["target"].unique().tolist())
    test_classes = set(test_df["target"].unique().tolist())

    if train_classes != {0, 1, 2}:
        raise ValueError(
            f"User-level split produced incomplete train classes: {sorted(train_classes)}. "
            "Add more data or adjust split."
        )

    if len(test_classes) < 2:
        raise ValueError(
            f"User-level split produced too few classes in test set: {sorted(test_classes)}. "
            "Add more data or adjust split."
        )

    return train_df, test_df


def build_model(trial: optuna.Trial) -> XGBClassifier:
    return XGBClassifier(
        n_estimators=trial.suggest_int("n_estimators", 80, 300),
        max_depth=trial.suggest_int("max_depth", 3, 8),
        learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        subsample=trial.suggest_float("subsample", 0.7, 1.0),
        colsample_bytree=trial.suggest_float("colsample_bytree", 0.7, 1.0),
        min_child_weight=trial.suggest_int("min_child_weight", 1, 8),
        gamma=trial.suggest_float("gamma", 0.0, 3.0),
        reg_alpha=trial.suggest_float("reg_alpha", 0.0, 3.0),
        reg_lambda=trial.suggest_float("reg_lambda", 0.5, 5.0),
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
        tree_method="hist",
    )


def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series) -> tuple[float, float, str]:
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)

    macro_f1 = f1_score(y_test, preds, average="macro")
    auc_roc = roc_auc_score(y_test, probs, multi_class="ovr")
    report = classification_report(
        y_test,
        preds,
        target_names=["LOW", "MODERATE", "HIGH"],
        digits=4,
        zero_division=0,
    )
    return macro_f1, auc_roc, report


def load_baseline_model():
    if not MODEL_PATH.exists():
        return None

    artifact = joblib.load(MODEL_PATH)
    if not isinstance(artifact, dict) or "model" not in artifact:
        return None
    return artifact["model"]


def write_report(
    rows_used: int,
    unique_users: int,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    macro_f1: float,
    auc_roc: float,
    report: str,
    best_params: dict,
):
    REPORT_PATH.write_text(
        "# XGBoost Evaluation Report\n\n"
        f"Training rows used: {rows_used}\n\n"
        f"Unique users: {unique_users}\n\n"
        f"Train split rows: {len(train_df)}\n\n"
        f"Test split rows: {len(test_df)}\n\n"
        f"Train users: {train_df['user_id'].nunique()}\n\n"
        f"Test users: {test_df['user_id'].nunique()}\n\n"
        f"Macro F1: {macro_f1:.4f}\n\n"
        f"AUC-ROC (OVR): {auc_roc:.4f}\n\n"
        "## Best Optuna Parameters\n\n"
        f"```json\n{json.dumps(best_params, indent=2)}\n```\n\n"
        "## Classification Report\n\n"
        f"```\n{report}\n```\n",
        encoding="utf-8",
    )


def append_retrain_log(event: dict):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if RETRAIN_LOG.exists():
        try:
            existing = json.loads(RETRAIN_LOG.read_text(encoding="utf-8"))
            if isinstance(existing, list):
                history = existing
            elif isinstance(existing, dict) and "history" in existing:
                history = existing["history"]
            else:
                history = []
        except Exception:
            history = []
    else:
        history = []

    history.append(event)
    RETRAIN_LOG.write_text(json.dumps({"history": history}, indent=2), encoding="utf-8")


def atomic_deploy(candidate_artifact: dict):
    tmp_path = MODEL_PATH.with_suffix(".tmp")
    joblib.dump(candidate_artifact, tmp_path)
    os.replace(tmp_path, MODEL_PATH)


def train_candidate(X_train, y_train):
    def objective(trial: optuna.Trial) -> float:
        model = build_model(trial)
        model.fit(X_train, y_train)
        preds = model.predict(X_test_global)
        return f1_score(y_test_global, preds, average="macro")

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=50, show_progress_bar=False)

    model = build_model(study.best_trial)
    model.fit(X_train, y_train)

    return model, study.best_params


X_test_global = None
y_test_global = None


def main() -> None:
    global X_test_global, y_test_global

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    base_df = load_base_data()
    merged_df, new_data_found = merge_new_data(base_df)
    df = validate_training_frame(merged_df)

    print("Training rows:", len(df))
    print("Unique users:", df["user_id"].nunique())
    print("New data found:", new_data_found)
    print("Class distribution:")
    print(df["strain_level"].value_counts())

    train_df, test_df = group_train_test_split(df, test_size=0.2, random_state=42)

    X_train = train_df[TRAINING_FEATURE_COLUMNS].copy()
    y_train = train_df["target"].astype(int)

    X_test = test_df[TRAINING_FEATURE_COLUMNS].copy()
    y_test = test_df["target"].astype(int)

    X_test_global = X_test
    y_test_global = y_test

    baseline_model = load_baseline_model()
    baseline_f1 = None
    baseline_auc = None

    if baseline_model is not None:
        baseline_f1, baseline_auc, _ = evaluate_model(baseline_model, X_test, y_test)
    else:
        baseline_f1 = 0.0
        baseline_auc = 0.0

    force_retrain = os.getenv("FORCE_RETRAIN", "0") == "1"

    allowed, reasons = should_retrain(
        current_f1=baseline_f1,
        log_path=RETRAIN_LOG,
        interval_days=14,
        drift_threshold=0.05,
    )

    if not force_retrain and not allowed and not new_data_found:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "skipped",
            "reason": "schedule_not_due_and_no_drift_and_no_new_data",
            "baseline_f1": round(float(baseline_f1), 4),
            "baseline_auc": round(float(baseline_auc), 4),
            "details": reasons,
        }
        append_retrain_log(event)
        print("Retrain skipped:", event["reason"])
        return

    candidate_model, best_params = train_candidate(X_train, y_train)
    candidate_f1, candidate_auc, candidate_report = evaluate_model(candidate_model, X_test, y_test)

    artifact = {
        "model": candidate_model,
        "feature_columns": TRAINING_FEATURE_COLUMNS,
        "label_map": LABEL_MAP,
        "inverse_label_map": INV_LABEL_MAP,
        "best_params": best_params,
    }

    deploy = candidate_f1 > baseline_f1

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "deployed" if deploy else "rejected",
        "new_data_found": new_data_found,
        "rows_used": int(len(df)),
        "unique_users": int(df["user_id"].nunique()),
        "baseline_f1": round(float(baseline_f1), 4),
        "baseline_auc": round(float(baseline_auc), 4),
        "candidate_f1": round(float(candidate_f1), 4),
        "candidate_auc": round(float(candidate_auc), 4),
        "best_params": best_params,
        "details": reasons,
    }

    if deploy:
        joblib.dump(artifact, CANDIDATE_MODEL_PATH)
        atomic_deploy(artifact)

        # persist merged data only after successful deploy
        df.to_parquet(FEATURES_PATH, index=False)

        write_report(
            rows_used=len(df),
            unique_users=df["user_id"].nunique(),
            train_df=train_df,
            test_df=test_df,
            macro_f1=candidate_f1,
            auc_roc=candidate_auc,
            report=candidate_report,
            best_params=best_params,
        )

        event["deployed_f1"] = round(float(candidate_f1), 4)
        event["model_path"] = str(MODEL_PATH)
        print(f"Deployed new model. F1 improved from {baseline_f1:.4f} to {candidate_f1:.4f}")
    else:
        print(f"Candidate rejected. Baseline F1={baseline_f1:.4f}, candidate F1={candidate_f1:.4f}")

    append_retrain_log(event)


if __name__ == "__main__":
    main()