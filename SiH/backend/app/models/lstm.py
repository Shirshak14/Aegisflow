"""
Baseline Model 2: Multi-Head LSTM Forecaster.
Demonstrates sequential recurrent modeling of temporal network states.
"""

from typing import Tuple, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from app.models.base import BaseForecaster
from app.preprocessing.schema import STAGE_SEVERITY, ATTACK_STAGES

class LSTMNetwork(nn.Module):
    def __init__(self, feature_dim: int = 24, hidden_dim: int = 128, num_layers: int = 2, num_classes: int = 9, dropout: float = 0.1):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=feature_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.state_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, feature_dim),
            nn.Sigmoid() # Features normalized to [0, 1]
        )
        self.stage_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, num_classes)
        )
        self.risk_head = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        # x: [batch, seq_len, feat_dim]
        out, (hn, cn) = self.lstm(x)
        # Use last step hidden state
        last_hidden = out[:, -1, :] # [batch, hidden_dim]
        
        pred_state = self.state_head(last_hidden)
        stage_logits = self.stage_head(last_hidden)
        risk = self.risk_head(last_hidden)
        return pred_state, stage_logits, risk

class LSTMForecaster(BaseForecaster):
    def __init__(self, feature_dim: int = 24, hidden_dim: int = 128, num_layers: int = 2, num_classes: int = 9, device: Optional[str] = None):
        self.feature_dim = feature_dim
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = LSTMNetwork(feature_dim, hidden_dim, num_layers, num_classes).to(self.device)

    def predict_next(self, history: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float, Optional[np.ndarray]]:
        self.model.eval()
        if history.ndim == 2:
            history = history[np.newaxis, :, :] # [1, seq_len, feat_dim]
            
        tensor_x = torch.tensor(history, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            pred_state, stage_logits, risk = self.model(tensor_x)
            stage_probs = F.softmax(stage_logits, dim=-1).cpu().numpy()[0]
            next_state = pred_state.cpu().numpy()[0]
            risk_score = float(risk.cpu().numpy()[0, 0])
            
        return next_state, stage_probs, risk_score, None

    def save(self, filepath: str):
        torch.save(self.model.state_dict(), filepath)

    def load(self, filepath: str):
        self.model.load_state_dict(torch.load(filepath, map_location=self.device))
        self.model.eval()
