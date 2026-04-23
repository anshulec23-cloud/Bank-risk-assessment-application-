"""
Random Forest anomaly detector.
Features: temperature, pressure, flow_rate, voltage
Output:   anomaly probability score ∈ [0, 1]
"""
import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from ml.data_gen import generate_dataset

FEATURES = ["temperature", "pressure", "flow_rate", "voltage"]
ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(ARTIFACT_DIR, "rf_model.joblib")


def train():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    df = generate_dataset(n_normal=5000, n_per_attack=400)

    X = df[FEATURES].values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=["Normal", "Attack"]))

    joblib.dump(clf, MODEL_PATH)
    print(f"Model saved → {MODEL_PATH}")
    return clf


def load_model() -> RandomForestClassifier:
    if not os.path.exists(MODEL_PATH):
        print("Model not found — training now...")
        return train()
    return joblib.load(MODEL_PATH)


# Module-level singleton — loaded once on import
_model: RandomForestClassifier | None = None


def get_model() -> RandomForestClassifier:
    global _model
    if _model is None:
        _model = load_model()
    return _model


def predict(temperature: float, pressure: float, flow_rate: float, voltage: float) -> dict:
    """
    Returns:
        anomaly_score: float ∈ [0, 1]  — probability of attack class
        is_anomaly:    bool             — True if score > threshold
        feature_importances: dict
    """
    from core.config import settings
    model = get_model()
    X = np.array([[temperature, pressure, flow_rate, voltage]])
    proba = model.predict_proba(X)[0]
    score = float(proba[1])  # probability of class 1 (attack)

    importances = dict(zip(FEATURES, model.feature_importances_.tolist()))

    return {
        "anomaly_score": round(score, 4),
        "is_anomaly": score >= settings.ANOMALY_THRESHOLD,
        "feature_importances": importances,
    }


if __name__ == "__main__":
    train()
