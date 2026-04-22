import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from joblib import dump

# load your features dataset
df = pd.read_parquet("ml/data/features.parquet")

# features used in training
FEATURES = [
    "n_interactions",
    "accuracy",
    "avg_elapsed_time",
    "strain_score",
    "struggle_index"
]

X = df[FEATURES]
y = df["strain_label"]

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    class_weight="balanced"
)

model.fit(X, y)

# save model
dump(model, "backend/models/strain_model.joblib")

print("Model trained and saved")