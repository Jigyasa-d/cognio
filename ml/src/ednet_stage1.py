from pathlib import Path
import pandas as pd
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.feature_engineering import build_feature_vector, heuristic_label


INPUT_PATH = Path("data/raw/kt1_merged.csv")
OUTPUT_PATH = Path("data/labeled_sessions.parquet")


def load_merged_ednet():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"{INPUT_PATH} not found. Run python src/ednet_merge.py first.")

    df = pd.read_csv(INPUT_PATH)
    df = df.sort_values(["student_id", "timestamp"]).reset_index(drop=True)
    return df


def build_labeled_dataset(df):
    rows = []

    grouped = df.groupby(["student_id", "content_id"], dropna=False)

    for (sid, cid), group in grouped:
        events = group.to_dict(orient="records")

        features = build_feature_vector(events)
        label = heuristic_label(features)

        features["student_id"] = sid
        features["content_id"] = cid
        features["strain_level"] = label

        rows.append(features)

    return pd.DataFrame(rows)


def main():
    print("Loading merged EdNet dataset...")
    df = load_merged_ednet()

    print("Building labeled dataset...")
    labeled_df = build_labeled_dataset(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    labeled_df.to_csv("data/labeled_sessions.csv", index=False)
    print("\nSaved:", OUTPUT_PATH)
    print("Shape:", labeled_df.shape)
    print("\nClass distribution:")
    print(labeled_df["strain_level"].value_counts(dropna=False))


if __name__ == "__main__":
    main()