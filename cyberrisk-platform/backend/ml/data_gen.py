"""
Generates synthetic ICS telemetry data for training the Random Forest model.
Normal vs attack distributions are grounded in published ICS anomaly datasets
(BATADAL, SWaT) parameter ranges.
"""
import numpy as np
import pandas as pd


NORMAL_PARAMS = {
    "temperature": (65.0, 5.0),    # mean, std — Celsius
    "pressure":    (4.5,  0.3),    # bar
    "flow_rate":   (120.0, 10.0),  # L/min
    "voltage":     (230.0, 5.0),   # V
}

# Each attack type shifts/spikes certain sensors
ATTACK_PROFILES = {
    "DoS": {
        "temperature": (90.0, 8.0),   # overheating
        "pressure":    (7.5,  0.5),   # pressure spike
        "flow_rate":   (50.0, 20.0),  # flow disruption
        "voltage":     (230.0, 5.0),  # unchanged
    },
    "Spoofing": {
        "temperature": (65.0, 0.1),   # suspiciously flat — spoofed
        "pressure":    (4.5,  0.01),
        "flow_rate":   (120.0, 0.1),
        "voltage":     (230.0, 0.1),
    },
    "Replay": {
        "temperature": (65.0, 5.0),   # same as normal — hard to detect
        "pressure":    (4.5,  0.3),
        "flow_rate":   (120.0, 10.0),
        "voltage":     (195.0, 3.0),  # slight voltage drop
    },
    "PhysicalTamper": {
        "temperature": (110.0, 15.0),  # extreme heat
        "pressure":    (9.0,   1.0),   # very high pressure
        "flow_rate":   (10.0,  5.0),   # near-zero flow
        "voltage":     (180.0, 10.0),  # voltage sag
    },
}


def _sample(params: dict, n: int, label: int, attack_type: str = "Normal") -> pd.DataFrame:
    rows = {
        "temperature": np.random.normal(*params["temperature"], n),
        "pressure":    np.random.normal(*params["pressure"],    n),
        "flow_rate":   np.random.normal(*params["flow_rate"],   n),
        "voltage":     np.random.normal(*params["voltage"],     n),
        "label":       np.full(n, label),
        "attack_type": [attack_type] * n,
    }
    return pd.DataFrame(rows)


def generate_dataset(n_normal: int = 5000, n_per_attack: int = 300) -> pd.DataFrame:
    frames = [_sample(NORMAL_PARAMS, n_normal, 0, "Normal")]
    for name, profile in ATTACK_PROFILES.items():
        frames.append(_sample(profile, n_per_attack, 1, name))
    df = pd.concat(frames, ignore_index=True).sample(frac=1, random_state=42)
    return df


if __name__ == "__main__":
    df = generate_dataset()
    df.to_csv("ml/artifacts/training_data.csv", index=False)
    print(f"Generated {len(df)} samples — Normal: {(df.label==0).sum()}, Attack: {(df.label==1).sum()}")
