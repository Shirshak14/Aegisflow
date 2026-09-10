"""
Baseline Model 1: Multi-Class Logistic Regression & Linear Forecaster.
Provides a non-temporal standard statistical baseline.
"""

from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge
from app.models.base import BaseForecaster
from app.preprocessing.schema import STAGE_SEVERITY

class BaselineLogisticRegressionForecaster(BaseForecaster):
    def __init__(self, feature_dim: int = 24, num_classes: int = 9):
        self.feature_dim = feature_dim
        self.num_classes = num_classes
        self.clf = LogisticRegression(max_iter=500, solver="lbfgs", class_weight="balanced")
        self.regressor = Ridge(alpha=1.0)
        self.is_fitted = False

    def _extract_features(self, X_seq: np.ndarray) -> np.ndarray:
        """
        Converts 3D sequence [N_samples, seq_len, feat_dim] or 2D [seq_len, feat_dim]
        into tabular features: concatenation of mean, std, and latest state.
        """
        if X_seq.ndim == 2:
            X_seq = X_seq[np.newaxis, :, :]
        
        mean_feats = np.mean(X_seq, axis=1)
        last_feats = X_seq[:, -1, :]
        return np.concatenate([last_feats, mean_feats], axis=1)

    def fit(self, X_seq: np.ndarray, y_next_state: np.ndarray, y_stage: np.ndarray):
        X_tab = self._extract_features(X_seq)
        if y_stage.ndim > 1:
            y_stage = y_stage[:, 0] # First step target
        if y_next_state.ndim > 2:
            y_next_state = y_next_state[:, 0, :]
            
        self.clf.fit(X_tab, y_stage)
        self.regressor.fit(X_tab, y_next_state)
        self.is_fitted = True

    def predict_next(self, history: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float, Optional[np.ndarray]]:
        if not self.is_fitted:
            # Return neutral fallback
            next_state = history[-1] if history.ndim == 2 else history[0, -1]
            probs = np.zeros(self.num_classes, dtype=np.float32)
            probs[0] = 1.0
            return next_state, probs, 0.05, None

        X_tab = self._extract_features(history)
        next_state = self.regressor.predict(X_tab)[0]
        next_state = np.clip(next_state, 0.0, 1.0)

        # Handle class prediction with full probability array
        probs = np.zeros(self.num_classes, dtype=np.float32)
        present_classes = self.clf.classes_
        pred_probs = self.clf.predict_proba(X_tab)[0]
        for idx, cls_id in enumerate(present_classes):
            if int(cls_id) < self.num_classes:
                probs[int(cls_id)] = pred_probs[idx]

        # Compute risk score from stage distribution
        from app.preprocessing.schema import ATTACK_STAGES
        risk_score = 0.0
        for i, p in enumerate(probs):
            stage_name = ATTACK_STAGES.get(i, "Normal")
            risk_score += p * STAGE_SEVERITY.get(stage_name, 0.05)

        return next_state, probs, float(np.clip(risk_score, 0.0, 1.0)), None

    def save(self, filepath: str):
        with open(filepath, "wb") as f:
            pickle.dump({"clf": self.clf, "regressor": self.regressor, "is_fitted": self.is_fitted}, f)

    def load(self, filepath: str):
        with open(filepath, "rb") as f:
            data = pickle.load(f)
            self.clf = data["clf"]
            self.regressor = data["regressor"]
            self.is_fitted = data.get("is_fitted", True)
