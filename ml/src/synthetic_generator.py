from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd


def generate_session(strain_level: str = "HIGH", n_rows: int = 200) -> pd.DataFrame:
    rows = []

    for _ in range(n_rows):
        if strain_level.upper() == "HIGH":
            row = {
                "latency_delta": max(0, np.random.normal(8000, 2000)),
                "error_rate": np.random.uniform(0.65, 1.0),
                "attempt_burst": 1,
                "attention_drop": np.random.choice([0, 1], p=[0.2, 0.8]),
                "hint_reliance": np.random.uniform(0.5, 1.0),
                "cold_start_latency": max(0, np.random.normal(6000, 1500)),
                "exit_flag_ratio": np.random.uniform(0.2, 0.8),
                "reread_normalized": np.random.uniform(1.0, 3.0),
                "strain_level": "HIGH",
            }
        elif strain_level.upper() == "MODERATE":
            row = {
                "latency_delta": max(0, np.random.normal(4500, 1200)),
                "error_rate": np.random.uniform(0.35, 0.6),
                "attempt_burst": np.random.choice([0, 1], p=[0.6, 0.4]),
                "attention_drop": np.random.choice([0, 1], p=[0.5, 0.5]),
                "hint_reliance": np.random.uniform(0.2, 0.6),
                "cold_start_latency": max(0, np.random.normal(3500, 1000)),
                "exit_flag_ratio": np.random.uniform(0.05, 0.3),
                "reread_normalized": np.random.uniform(0.4, 1.2),
                "strain_level": "MODERATE",
            }
        else:
            row = {
                "latency_delta": max(0, np.random.normal(1200, 500)),
                "error_rate": np.random.uniform(0.0, 0.3),
                "attempt_burst": 0,
                "attention_drop": np.random.choice([0, 1], p=[0.85, 0.15]),
                "hint_reliance": np.random.uniform(0.0, 0.2),
                "cold_start_latency": max(0, np.random.normal(1500, 500)),
                "exit_flag_ratio": np.random.uniform(0.0, 0.1),
                "reread_normalized": np.random.uniform(0.0, 0.5),
                "strain_level": "LOW",
            }
        rows.append(row)

    return pd.DataFrame(rows)


def generate_dataset(per_class: int = 300) -> pd.DataFrame:
    df = pd.concat(
        [
            generate_session("LOW", per_class),
            generate_session("MODERATE", per_class),
            generate_session("HIGH", per_class),
        ],
        ignore_index=True,
    )
    return df.sample(frac=1, random_state=42).reset_index(drop=True)


if __name__ == "__main__":
    df = generate_dataset()
    print(df.head())
    print(df["strain_level"].value_counts())