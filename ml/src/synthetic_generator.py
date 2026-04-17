from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np
import pandas as pd


def _generate_one_group(
    student_id: str,
    content_id: str,
    strain_level: str,
    n_events: int = 10,
    seed: int | None = None,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: List[dict] = []

    timestamp = 0

    for i in range(n_events):
        if strain_level.upper() == "HIGH":
            time_taken_ms = max(500, int(rng.normal(8500, 1800)))
            correct = int(rng.choice([0, 1], p=[0.75, 0.25]))
            scroll_depth = max(0, min(100, int(rng.normal(40, 20))))
            hint_count = int(rng.integers(1, 4))
            reread_count = int(rng.integers(1, 5))
            exit_flag = int(rng.choice([0, 1], p=[0.65, 0.35]))
            gap_ms = int(rng.integers(5000, 30000))
            content_length_words = int(rng.integers(250, 500))

        elif strain_level.upper() == "MODERATE":
            time_taken_ms = max(500, int(rng.normal(4500, 1200)))
            correct = int(rng.choice([0, 1], p=[0.45, 0.55]))
            scroll_depth = max(0, min(100, int(rng.normal(65, 18))))
            hint_count = int(rng.integers(0, 3))
            reread_count = int(rng.integers(0, 3))
            exit_flag = int(rng.choice([0, 1], p=[0.85, 0.15]))
            gap_ms = int(rng.integers(10000, 40000))
            content_length_words = int(rng.integers(250, 500))

        else:
            time_taken_ms = max(500, int(rng.normal(1800, 500)))
            correct = int(rng.choice([0, 1], p=[0.15, 0.85]))
            scroll_depth = max(0, min(100, int(rng.normal(85, 10))))
            hint_count = int(rng.integers(0, 2))
            reread_count = int(rng.integers(0, 2))
            exit_flag = int(rng.choice([0, 1], p=[0.95, 0.05]))
            gap_ms = int(rng.integers(15000, 50000))
            content_length_words = int(rng.integers(250, 500))

        timestamp += gap_ms

        rows.append(
            {
                "student_id": student_id,
                "content_id": content_id,
                "timestamp": timestamp,
                "time_taken_ms": time_taken_ms,
                "correct": correct,
                "scroll_depth": scroll_depth,
                "hint_count": hint_count,
                "reread_count": reread_count,
                "exit_flag": exit_flag,
                "content_length_words": content_length_words,
                "synthetic_strain": strain_level.upper(),
                "event_index": i,
            }
        )

    return pd.DataFrame(rows)


def generate_synthetic_events(
    per_class_groups: int = 50,
    events_per_group: int = 10,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    all_groups = []
    group_counter = 0

    for label in ["LOW", "MODERATE", "HIGH"]:
        for _ in range(per_class_groups):
            group_counter += 1
            student_id = f"syn_student_{group_counter:04d}"
            content_id = f"syn_content_{int(rng.integers(1, 15)):03d}"

            group_df = _generate_one_group(
                student_id=student_id,
                content_id=content_id,
                strain_level=label,
                n_events=events_per_group,
                seed=int(rng.integers(0, 1_000_000)),
            )
            all_groups.append(group_df)

    return pd.concat(all_groups, ignore_index=True)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    output_path = project_root / "data" / "raw" / "synthetic_events.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = generate_synthetic_events(per_class_groups=50, events_per_group=10, seed=42)
    df.to_csv(output_path, index=False)

    print(f"Saved synthetic events to: {output_path}")
    print(df.head())
    print("\nShape:", df.shape)
    print("\nSynthetic label counts:")
    print(df["synthetic_strain"].value_counts())


if __name__ == "__main__":
    main()