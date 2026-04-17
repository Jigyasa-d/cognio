from pathlib import Path
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw" / "kt1_merged.csv"
OUT_PATH = ROOT / "data" / "labeled_sessions.parquet"


def pick_column(df: pd.DataFrame, candidates, required=True):
    for col in candidates:
        if col in df.columns:
            return col
    if required:
        raise ValueError(
            f"None of these columns were found: {candidates}\nAvailable columns: {list(df.columns)}"
        )
    return None


def normalize_elapsed_to_seconds(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").fillna(0).clip(lower=0)

    # Convert ms to seconds if values look like milliseconds
    if s.median() > 100:
        s = s / 1000.0

    upper = s.quantile(0.95)
    if pd.notna(upper) and upper > 0:
        s = s.clip(upper=upper)

    return s


def longest_wrong_streak(values) -> int:
    streak = 0
    best = 0
    for v in values:
        if v == 0:
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    return best


def safe_rank_pct(series: pd.Series) -> pd.Series:
    if series.nunique(dropna=True) <= 1:
        return pd.Series(np.zeros(len(series)), index=series.index, dtype=float)
    return series.rank(pct=True, method="average").fillna(0.0)


def main():
    print("Loading merged EdNet dataset...")
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing file: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    user_col = pick_column(df, ["user_id", "uid", "learner_id", "student_id"])
    question_col = pick_column(
        df, ["question_id", "content_id", "qid", "item_id", "problem_id"], required=False
    )
    correct_col = pick_column(
        df, ["correct", "answered_correctly", "is_correct", "label"]
    )
    elapsed_col = pick_column(
        df,
        [
            "elapsed_time",
            "elapsed",
            "response_time",
            "solving_time",
            "duration",
            "user_elapsed",
            "time_taken_ms",
        ],
    )
    timestamp_col = pick_column(
        df,
        ["timestamp", "event_time", "action_time", "ts", "time"],
        required=False,
    )

    scroll_col = pick_column(df, ["scroll_depth"], required=False)
    hint_col = pick_column(df, ["hint_count"], required=False)
    reread_col = pick_column(df, ["reread_count"], required=False)
    exit_col = pick_column(df, ["exit_flag"], required=False)

    use_cols = [user_col, correct_col, elapsed_col]
    if question_col:
        use_cols.append(question_col)
    if timestamp_col:
        use_cols.append(timestamp_col)
    if scroll_col:
        use_cols.append(scroll_col)
    if hint_col:
        use_cols.append(hint_col)
    if reread_col:
        use_cols.append(reread_col)
    if exit_col:
        use_cols.append(exit_col)

    work = df[use_cols].copy()

    rename_map = {
        user_col: "user_id",
        correct_col: "correct",
        elapsed_col: "elapsed_time",
    }
    if question_col:
        rename_map[question_col] = "question_id"
    if timestamp_col:
        rename_map[timestamp_col] = "timestamp"
    if scroll_col:
        rename_map[scroll_col] = "scroll_depth"
    if hint_col:
        rename_map[hint_col] = "hint_count"
    if reread_col:
        rename_map[reread_col] = "reread_count"
    if exit_col:
        rename_map[exit_col] = "exit_flag"

    work = work.rename(columns=rename_map)

    work["correct"] = pd.to_numeric(work["correct"], errors="coerce").fillna(0).clip(0, 1).astype(int)
    work["elapsed_time"] = normalize_elapsed_to_seconds(work["elapsed_time"])

    for col in ["scroll_depth", "hint_count", "reread_count", "exit_flag"]:
        if col not in work.columns:
            work[col] = 0
        work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)

    if "timestamp" in work.columns:
        work["timestamp"] = pd.to_numeric(work["timestamp"], errors="coerce")
        work = work.sort_values(["user_id", "timestamp"], kind="stable")
    else:
        work = work.sort_values(["user_id"], kind="stable")

    if "question_id" not in work.columns:
        work["question_id"] = np.arange(len(work))

    work = work.dropna(subset=["user_id"]).reset_index(drop=True)

    work["interaction_idx"] = work.groupby("user_id").cumcount()

    SESSION_SIZE = 25
    work["session_num"] = (work["interaction_idx"] // SESSION_SIZE).astype(int)
    work["session_id"] = work["user_id"].astype(str) + "_s" + work["session_num"].astype(str)

    work["is_incorrect"] = 1 - work["correct"]

    user_p75 = work.groupby("user_id")["elapsed_time"].transform(lambda s: s.quantile(0.75))
    work["long_response"] = (work["elapsed_time"] > user_p75).astype(int)

    work["attempt_order"] = (
        work.groupby(["user_id", "session_num", "question_id"]).cumcount() + 1
    )
    work["is_retry"] = (work["attempt_order"] > 1).astype(int)

    print("Building labeled dataset...")

    session_rows = []
    for (user_id, session_num, session_id), g in work.groupby(
        ["user_id", "session_num", "session_id"], sort=False
    ):
        n = len(g)
        if n < 5:
            continue

        correct_vals = g["correct"].tolist()
        elapsed_vals = g["elapsed_time"]

        session_rows.append(
            {
                "user_id": user_id,
                "session_num": int(session_num),
                "session_id": session_id,
                "n_interactions": int(n),
                "accuracy": float(g["correct"].mean()),
                "incorrect_rate": float(g["is_incorrect"].mean()),
                "avg_elapsed_time": float(elapsed_vals.mean()),
                "median_elapsed_time": float(elapsed_vals.median()),
                "std_elapsed_time": float(elapsed_vals.std(ddof=0) if n > 1 else 0.0),
                "p90_elapsed_time": float(elapsed_vals.quantile(0.90)),
                "long_response_rate": float(g["long_response"].mean()),
                "retry_rate": float(g["is_retry"].mean()),
                "wrong_streak_max": int(longest_wrong_streak(correct_vals)),
                "avg_scroll_depth": float(g["scroll_depth"].mean()),
                "hint_usage_rate": float(g["hint_count"].sum() / n),
                "reread_rate": float(g["reread_count"].sum() / n),
                "exit_flag_rate": float(g["exit_flag"].sum() / n),
            }
        )

    features = pd.DataFrame(session_rows)

    if features.empty:
        raise ValueError("No session-level rows were created. Check dataset and session logic.")

    features["time_score"] = safe_rank_pct(features["avg_elapsed_time"])
    features["variability_score"] = safe_rank_pct(features["std_elapsed_time"])
    features["incorrect_score"] = safe_rank_pct(features["incorrect_rate"])
    features["retry_score"] = safe_rank_pct(features["retry_rate"])
    features["streak_score"] = safe_rank_pct(features["wrong_streak_max"])
    features["long_response_score"] = safe_rank_pct(features["long_response_rate"])
    features["hint_score"] = safe_rank_pct(features["hint_usage_rate"])
    features["reread_score"] = safe_rank_pct(features["reread_rate"])
    features["exit_score"] = safe_rank_pct(features["exit_flag_rate"])

    features["strain_score"] = (
        0.22 * features["incorrect_score"]
        + 0.18 * features["time_score"]
        + 0.12 * features["retry_score"]
        + 0.12 * features["streak_score"]
        + 0.12 * features["long_response_score"]
        + 0.08 * features["variability_score"]
        + 0.07 * features["hint_score"]
        + 0.05 * features["reread_score"]
        + 0.04 * features["exit_score"]
    )

    ranks = features["strain_score"].rank(method="first")
    features["strain_level"] = pd.qcut(
        ranks,
        q=3,
        labels=["LOW", "MODERATE", "HIGH"],
    ).astype(str)

    final_cols = [
        "user_id",
        "session_num",
        "session_id",
        "n_interactions",
        "accuracy",
        "incorrect_rate",
        "avg_elapsed_time",
        "median_elapsed_time",
        "std_elapsed_time",
        "p90_elapsed_time",
        "long_response_rate",
        "retry_rate",
        "wrong_streak_max",
        "avg_scroll_depth",
        "hint_usage_rate",
        "reread_rate",
        "exit_flag_rate",
        "strain_score",
        "strain_level",
    ]
    features = features[final_cols]

    print("Saving labeled dataset...")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(OUT_PATH, index=False)

    print(f"\nSaved: {OUT_PATH}")
    print(f"Shape: {features.shape}")
    print("\nClass distribution:")
    print(features["strain_level"].value_counts())


if __name__ == "__main__":
    main()