from __future__ import annotations

from typing import List

import numpy as np
import shap

from src.feature_engineering import FEATURE_COLUMNS


def get_top_features(model, feature_array: np.ndarray, top_k: int = 3) -> List[str]:
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(feature_array)

    if isinstance(shap_values, list):
        values = np.mean(np.abs(np.array(shap_values)), axis=0)[0]
    else:
        values = np.abs(shap_values)[0]

    ranked_idx = np.argsort(values)[::-1][:top_k]
    return [FEATURE_COLUMNS[i] for i in ranked_idx]