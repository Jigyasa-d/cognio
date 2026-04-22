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
        values = np.abs(shap_values[class_idx][0])
    else:
        values = np.abs(shap_values[0])

    ranked_idx = np.argsort(values)[::-1][:top_k]
    return [feature_columns[i] for i in ranked_idx]