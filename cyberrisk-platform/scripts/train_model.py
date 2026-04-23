"""
Train the Random Forest model.
Run from /backend: python scripts/train_model.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml.model import train
os.makedirs("ml/artifacts", exist_ok=True)
train()
