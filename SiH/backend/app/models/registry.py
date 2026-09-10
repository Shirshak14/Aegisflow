"""
Model Registry, Training Pipeline, and Empirical Evaluation Benchmarking for SIH26153.
Ensures strict time-aware splitting to prevent temporal data leakage.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import time
import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

from app.config import settings, MODELS_DIR
from app.preprocessing.schema import FEATURE_COLUMNS, ATTACK_STAGES, STAGE_TO_ID
from app.preprocessing.scaler import NetworkStateScaler
from app.models.base import BaseForecaster
from app.models.logreg import BaselineLogisticRegressionForecaster
from app.models.lstm import LSTMForecaster
from app.models.transformer import TemporalTransformerForecaster

class ModelRegistry:
    def __init__(self, models_dir: Path = MODELS_DIR):
        self.models_dir = models_dir
        self.scaler = NetworkStateScaler()
        self.models: Dict[str, BaseForecaster] = {}
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.active_model_name: str = "Temporal Transformer"
        self.training_status: Dict[str, Any] = {"status": "idle", "progress": 0, "message": "Ready"}
        
        self.init_models()

    def init_models(self):
        """Initializes instances of all three models."""
        self.models["Logistic Regression"] = BaselineLogisticRegressionForecaster(
            feature_dim=settings.FEATURE_DIM,
            num_classes=settings.NUM_CLASSES
        )
        self.models["LSTM"] = LSTMForecaster(
            feature_dim=settings.FEATURE_DIM,
            hidden_dim=settings.HIDDEN_DIM,
            num_layers=settings.NUM_LAYERS,
            num_classes=settings.NUM_CLASSES
        )
        self.models["Temporal Transformer"] = TemporalTransformerForecaster(
            feature_dim=settings.FEATURE_DIM,
            hidden_dim=settings.HIDDEN_DIM,
            num_heads=settings.NUM_HEADS,
            num_layers=settings.NUM_LAYERS,
            num_classes=settings.NUM_CLASSES,
            dropout=settings.DROPOUT
        )

    def get_active_model(self) -> BaseForecaster:
        return self.models.get(self.active_model_name, self.models["Temporal Transformer"])

    def set_active_model(self, name: str) -> bool:
        if name in self.models:
            self.active_model_name = name
            return True
        return False

    def train_all(
        self,
        X_seq: np.ndarray,
        Y_states: np.ndarray,
        Y_stages: np.ndarray,
        Y_risks: np.ndarray,
        epochs: int = 15,
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """
        Executes strict time-aware split training and benchmarking across all 3 models.
        """
        self.training_status = {"status": "running", "progress": 5, "message": "Preparing time-aware train/test splits..."}
        
        n_samples = len(X_seq)
        if n_samples < 20:
            self.training_status = {"status": "failed", "progress": 0, "message": "Insufficient samples for training"}
            return {"error": "Need at least 20 samples"}

        # STRICT TIME-AWARE SPLIT (Avoids random shuffling leakage)
        train_idx = int(0.70 * n_samples)
        val_idx = int(0.85 * n_samples)

        X_train, X_val, X_test = X_seq[:train_idx], X_seq[train_idx:val_idx], X_seq[val_idx:]
        Y_states_tr, Y_states_val, Y_states_te = Y_states[:train_idx], Y_states[train_idx:val_idx], Y_states[val_idx:]
        Y_stages_tr, Y_stages_val, Y_stages_te = Y_stages[:train_idx], Y_stages[train_idx:val_idx], Y_stages[val_idx:]
        Y_risks_tr, Y_risks_val, Y_risks_te = Y_risks[:train_idx], Y_risks[train_idx:val_idx], Y_risks[val_idx:]

        results = {}

        # 1. Train Logistic Regression
        self.training_status = {"status": "running", "progress": 20, "message": "Training Logistic Regression baseline..."}
        logreg = self.models["Logistic Regression"]
        logreg.fit(X_train, Y_states_tr, Y_stages_tr)
        results["Logistic Regression"] = self._evaluate_model(logreg, X_test, Y_states_te, Y_stages_te, Y_risks_te)
        logreg.save(str(self.models_dir / "logreg.pkl"))

        # 2. Train LSTM
        self.training_status = {"status": "running", "progress": 45, "message": "Training Multi-Head LSTM baseline..."}
        lstm_forecaster = self.models["LSTM"]
        self._train_torch_model(lstm_forecaster.model, X_train, Y_states_tr, Y_stages_tr, Y_risks_tr, epochs=epochs, batch_size=batch_size)
        results["LSTM"] = self._evaluate_model(lstm_forecaster, X_test, Y_states_te, Y_stages_te, Y_risks_te)
        lstm_forecaster.save(str(self.models_dir / "lstm.pt"))

        # 3. Train Temporal Transformer
        self.training_status = {"status": "running", "progress": 75, "message": "Training Multi-Head Temporal Transformer..."}
        transformer_forecaster = self.models["Temporal Transformer"]
        self._train_torch_model(transformer_forecaster.model, X_train, Y_states_tr, Y_stages_tr, Y_risks_tr, epochs=epochs, batch_size=batch_size, is_transformer=True)
        results["Temporal Transformer"] = self._evaluate_model(transformer_forecaster, X_test, Y_states_te, Y_stages_te, Y_risks_te)
        transformer_forecaster.save(str(self.models_dir / "transformer.pt"))

        self.metrics = results
        self.training_status = {"status": "completed", "progress": 100, "message": "Training and benchmarking finished successfully."}
        
        # Save metrics to json
        with open(self.models_dir / "metrics.json", "w") as f:
            json.dump(self.metrics, f, indent=2)

        return results

    def _train_torch_model(self, model: nn.Module, X_train: np.ndarray, Y_states: np.ndarray, Y_stages: np.ndarray, Y_risks: np.ndarray, epochs: int, batch_size: int, is_transformer: bool = False):
        device = next(model.parameters()).device
        model.train()
        
        optimizer = optim.AdamW(model.parameters(), lr=settings.LEARNING_RATE, weight_decay=1e-4)
        criterion_state = nn.MSELoss()
        
        # Class weights to handle imbalance
        unique_classes, counts = np.unique(Y_stages[:, 0], return_counts=True)
        weights = np.ones(settings.NUM_CLASSES, dtype=np.float32)
        total_counts = len(Y_stages)
        for cls, count in zip(unique_classes, counts):
            if int(cls) < settings.NUM_CLASSES:
                weights[int(cls)] = total_counts / (len(unique_classes) * count + 1e-6)
        class_weights_tensor = torch.tensor(weights, dtype=torch.float32).to(device)
        criterion_stage = nn.CrossEntropyLoss(weight=class_weights_tensor)
        criterion_risk = nn.MSELoss()

        n_samples = len(X_train)
        indices = np.arange(n_samples)

        tensor_x = torch.tensor(X_train, dtype=torch.float32)
        tensor_y_state = torch.tensor(Y_states[:, 0, :], dtype=torch.float32)
        tensor_y_stage = torch.tensor(Y_stages[:, 0], dtype=torch.long)
        tensor_y_risk = torch.tensor(Y_risks[:, 0:1], dtype=torch.float32)

        for epoch in range(epochs):
            np.random.shuffle(indices)
            for start_idx in range(0, n_samples, batch_size):
                batch_idx = indices[start_idx : start_idx + batch_size]
                bx = tensor_x[batch_idx].to(device)
                by_state = tensor_y_state[batch_idx].to(device)
                by_stage = tensor_y_stage[batch_idx].to(device)
                by_risk = tensor_y_risk[batch_idx].to(device)

                optimizer.zero_grad()
                if is_transformer:
                    p_state, p_stage, p_risk, _ = model(bx)
                else:
                    p_state, p_stage, p_risk = model(bx)

                loss_s = criterion_state(p_state, by_state)
                loss_c = criterion_stage(p_stage, by_stage)
                loss_r = criterion_risk(p_risk, by_risk)
                
                loss = loss_s * 1.0 + loss_c * 2.0 + loss_r * 1.0
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()

        model.eval()

    def _evaluate_model(
        self,
        forecaster: BaseForecaster,
        X_test: np.ndarray,
        Y_states_te: np.ndarray,
        Y_stages_te: np.ndarray,
        Y_risks_te: np.ndarray
    ) -> Dict[str, Any]:
        """
        Calculates standard classification and forecasting metrics.
        """
        y_true_first = Y_stages_te[:, 0]
        y_pred_first = []
        y_pred_probs = []

        # K-step accuracy tracker
        k_horizons = min(settings.FORECAST_HORIZON_K, Y_stages_te.shape[1])
        k_step_correct = [0] * k_horizons

        for i in range(len(X_test)):
            curr_seq = X_test[i].copy()
            for step in range(k_horizons):
                next_state, probs, risk, _ = forecaster.predict_next(curr_seq)
                pred_cls = int(np.argmax(probs))
                
                if step == 0:
                    y_pred_first.append(pred_cls)
                    y_pred_probs.append(probs)

                if pred_cls == Y_stages_te[i, step]:
                    k_step_correct[step] += 1

                # Roll forward for K-step test
                curr_seq = np.vstack([curr_seq[1:], next_state[np.newaxis, :]])

        y_pred_first = np.array(y_pred_first)
        acc = accuracy_score(y_true_first, y_pred_first)
        prec, rec, f1, _ = precision_recall_fscore_support(y_true_first, y_pred_first, average="weighted", zero_division=0)
        
        # Binary FPR calculation (Normal vs Any Attack)
        y_true_bin = (y_true_first > 0).astype(int)
        y_pred_bin = (y_pred_first > 0).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true_bin, y_pred_bin, labels=[0, 1]).ravel() if len(np.unique(np.concatenate([y_true_bin, y_pred_bin]))) > 1 else (0, 0, 0, len(y_true_bin))
        fpr = float(fp / max(fp + tn, 1))

        # K-step accuracies
        k_step_accuracies = [round(float(c / len(X_test)), 4) for c in k_step_correct]
        
        # Lead time estimate (early warning window in seconds)
        lead_time_sec = float(np.mean([k * 10.0 for k, acc_k in enumerate(k_step_accuracies, start=1) if acc_k > 0.60] or [10.0]))

        return {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "false_positive_rate": round(float(fpr), 4),
            "next_stage_accuracy": round(float(k_step_accuracies[0] if k_step_accuracies else acc), 4),
            "k_step_accuracies": k_step_accuracies,
            "mean_k_step_accuracy": round(float(np.mean(k_step_accuracies)), 4),
            "estimated_lead_time_sec": round(lead_time_sec, 1),
            "test_samples": len(X_test)
        }

model_registry = ModelRegistry()
