from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
KT1_DIR = RAW_DIR / "KT1"
QUESTIONS_PATH = RAW_DIR / "questions.csv"
OUTPUT_PATH = RAW_DIR / "kt1_merged.csv"

USER_FILES = [
    "u1.csv",
    "u10.csv",
    "u100.csv",
]


def pick_column(df: pd.DataFrame, candidates, required=True):
    for col in candidates:
        if col in df.columns:
            return col
    if required:
        raise ValueError(
            f"None of these columns were found: {candidates}\nAvailable columns: {list(df.columns)}"
        )
    return None


def main():
    if not QUESTIONS_PATH.exists():
        raise FileNotFoundError(f"questions.csv not found at: {QUESTIONS_PATH}")

    user_dfs = []

    for filename in USER_FILES:
        file_path = KT1_DIR / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Missing user file: {file_path}")

        print(f"Loading {filename}...")
        df = pd.read_csv(file_path)
        print(f"{filename} shape: {df.shape}")
        print(f"{filename} columns: {df.columns.tolist()}")
        user_dfs.append(df)

    print("\nCombining user files...")
    users_df = pd.concat(user_dfs, ignore_index=True)
    print(f"Combined user shape: {users_df.shape}")

    print("\nLoading questions.csv...")
    questions_df = pd.read_csv(QUESTIONS_PATH)
    print(f"questions.csv shape: {questions_df.shape}")
    print(f"questions.csv columns: {questions_df.columns.tolist()}")

    user_join_col = pick_column(
        users_df,
        ["content_id", "question_id", "qid", "item_id", "problem_id"],
    )
    question_join_col = pick_column(
        questions_df,
        ["question_id", "content_id", "qid", "item_id", "problem_id"],
    )

    print(f"\nMerging users[{user_join_col}] with questions[{question_join_col}] ...")
    merged_df = users_df.merge(
        questions_df,
        left_on=user_join_col,
        right_on=question_join_col,
        how="left",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(OUTPUT_PATH, index=False)

    print(f"\nSaved merged file to: {OUTPUT_PATH}")
    print(f"Shape: {merged_df.shape}")
    print("\nColumns:")
    print(merged_df.columns.tolist())


if __name__ == "__main__":
    main()