from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd
import shap


def get_top_features(model, input_df: pd.DataFrame, feature_columns: List[str], top_k: int = 3) -> List[str]:
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(input_df)

    if isinstance(shap_values, list):
        class_idx = int(np.argmax(model.predict_proba(input_df)[0]))
        values = np.abs(np.asarray(shap_values[class_idx])[0])
    else:
        arr = np.asarray(shap_values)

        if arr.ndim == 3:
            class_idx = int(np.argmax(model.predict_proba(input_df)[0]))
            if arr.shape[0] == len(input_df):
                values = np.abs(arr[0, :, class_idx])
            elif arr.shape[1] == len(input_df):
                values = np.abs(arr[class_idx, 0, :])
            else:
                raise ValueError(f"Unexpected 3D SHAP shape: {arr.shape}")
        elif arr.ndim == 2:
            values = np.abs(arr[0])
        else:
            raise ValueError(f"Unexpected SHAP output shape: {arr.shape}")

    ranked_idx = np.argsort(values)[::-1][:top_k]
    ranked_idx = [int(i) for i in ranked_idx]
    return [feature_columns[i] for i in ranked_idx]