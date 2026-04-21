import shap
import joblib
import numpy as np

class CognioExplainer:
    def __init__(self, model_path="ml/models/xgb_full.joblib"):
        self.model = joblib.load(model_path)
        self.explainer = shap.TreeExplainer(self.model)

        self.feature_names = [
            "n_interactions",
            "accuracy",
            "avg_elapsed_time",
            "incorrect_rate",
            "retry_rate",
            "strain_score",
            "struggle_index"
        ]

    def explain(self, input_array):
        shap_values = self.explainer.shap_values(input_array)

        values = shap_values[0]
        feature_impact = dict(zip(self.feature_names, values))

        # sort by importance
        sorted_features = sorted(
            feature_impact.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )

        top_features = [f[0] for f in sorted_features[:3]]

        return {
            "top_features": top_features,
            "feature_contributions": feature_impact
        }