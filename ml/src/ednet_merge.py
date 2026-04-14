from pathlib import Path
import pandas as pd
import numpy as np

U_PATH = Path("data/raw/KT1/u1.csv")
Q_PATH = Path("data/raw/questions.csv")

OUT_PATH = Path("data/raw/kt1_merged.csv")


def main():
    print("Loading u1.csv...")
    u_df = pd.read_csv(U_PATH, nrows=50000)  # safe limit

    print("Loading questions.csv...")
    q_df = pd.read_csv(Q_PATH)

    # normalize columns
    u_df.columns = [c.lower().strip() for c in u_df.columns]
    q_df.columns = [c.lower().strip() for c in q_df.columns]

    print("\nU columns:", u_df.columns.tolist())
    print("Q columns:", q_df.columns.tolist())

    # --- find correct answer column ---
    possible_answer_cols = ["correct_answer", "answer", "label", "solution"]
    answer_col = None

    for col in possible_answer_cols:
        if col in q_df.columns:
            answer_col = col
            break

    if answer_col is None:
        raise ValueError("No correct answer column found in questions.csv")

    print("Using answer column:", answer_col)

    # --- merge ---
    merged = pd.merge(
        u_df,
        q_df[["question_id", answer_col]],
        on="question_id",
        how="left"
    )

    # --- create correctness ---
    merged["correct"] = (
        merged["user_answer"].astype(str).str.strip() ==
        merged[answer_col].astype(str).str.strip()
    ).astype(int)

    # --- build final clean dataset ---
    clean = pd.DataFrame()

    clean["student_id"] = merged["solving_id"]  # proxy for user
    clean["content_id"] = merged["question_id"]
    clean["correct"] = merged["correct"]

    if "elapsed_time" in merged.columns:
        clean["time_taken_ms"] = pd.to_numeric(merged["elapsed_time"], errors="coerce")
    else:
        clean["time_taken_ms"] = 0

    clean["time_taken_ms"] = clean["time_taken_ms"].fillna(clean["time_taken_ms"].median())

    if "timestamp" in merged.columns:
        clean["timestamp"] = pd.to_numeric(merged["timestamp"], errors="coerce")
    else:
        clean["timestamp"] = np.arange(len(clean))

    # dummy features
    clean["scroll_depth"] = 100
    clean["hint_count"] = 0
    clean["reread_count"] = 0
    clean["exit_flag"] = 0

    clean = clean.dropna(subset=["student_id", "content_id"]).copy()
    clean = clean.sort_values(["student_id", "timestamp"]).reset_index(drop=True)

    # save
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(OUT_PATH, index=False)

    print("\nSaved merged dataset →", OUT_PATH)
    print("Shape:", clean.shape)
    print("\nCorrect distribution:")
    print(clean["correct"].value_counts())


if __name__ == "__main__":
    main()