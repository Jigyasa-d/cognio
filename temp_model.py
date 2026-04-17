from sklearn.ensemble import RandomForestClassifier
from joblib import dump
import numpy as np

X = np.random.rand(200, 5)
y = np.random.choice(["LOW", "MODERATE", "HIGH"], 200)

model = RandomForestClassifier()
model.fit(X, y)

dump(model, "backend/models/strain_model.joblib")

print("Dummy model created")