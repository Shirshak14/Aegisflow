"""
Primary Model: Multi-Head Temporal Transformer Forecaster.
Uses temporal self-attention across historical network state windows
to predict future state representations, attack stage probabilities, and risk score.
Exposes attention weights for explainability.
"""

from typing import Tuple, Optional, Dict, Any, List
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from app.models.base import BaseForecaster
from app.preprocessing.schema import ATTACK_STAGES, STAGE_SEVERITY

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 100):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0)) # [1, max_len, d_model]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [batch, seq_len, d_model]
        return x + self.pe[:, :x.size(1), :]

class TemporalTransformerBlock(nn.Module):
    def __init__(self, d_model: int = 128, nhead: int = 4, dim_feedforward: int = 256, dropout: float = 0.1):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=True)
        self.linear1 = nn.Linear(d_model, dim_feedforward)
        self.dropout = nn.Dropout(dropout)
        self.linear2 = nn.Linear(dim_feedforward, d_model)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # returns (out, attn_weights)
        attn_out, attn_weights = self.self_attn(x, x, x, need_weights=True, average_attn_weights=True)
        x = self.norm1(x + self.dropout1(attn_out))
        ff_out = self.linear2(self.dropout(F.relu(self.linear1(x))))
        x = self.norm2(x + self.dropout2(ff_out))
        return x, attn_weights

class TemporalTransformerNetwork(nn.Module):
    def __init__(
        self,
        feature_dim: int = 24,
        hidden_dim: int = 128,
        num_heads: int = 4,
        num_layers: int = 2,
        num_classes: int = 9,
        dropout: float = 0.1,
        max_seq_len: int = 50
    ):
        super().__init__()
        self.input_proj = nn.Linear(feature_dim, hidden_dim)
        self.pos_encoder = PositionalEncoding(hidden_dim, max_len=max_seq_len)
        
        self.layers = nn.ModuleList([
            TemporalTransformerBlock(hidden_dim, num_heads, hidden_dim * 2, dropout)
            for _ in range(num_layers)
        ])
        
        # State Head: Predicts next-state vector S_t+1 in [0, 1]
        self.state_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, feature_dim),
            nn.Sigmoid()
        )
        
        # Stage Head: Predicts MITRE attack stage distribution
        self.stage_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_classes)
        )
        
        # Risk Head: Predicts continuous threat risk score [0, 1]
        self.risk_head = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.GELU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        # x: [batch, seq_len, feat_dim]
        h = self.input_proj(x)
        h = self.pos_encoder(h)
        
        last_attn_weights = None
        for layer in self.layers:
            h, last_attn_weights = layer(h)
            
        # Aggregate temporal representations: focus on latest state context
        context_vector = h[:, -1, :] # [batch, hidden_dim]
        
        pred_state = self.state_head(context_vector)
        stage_logits = self.stage_head(context_vector)
        risk = self.risk_head(context_vector)
        
        # last_attn_weights: [batch, seq_len, seq_len]
        # Attention from the last query token to all historical keys:
        query_attention = last_attn_weights[:, -1, :] if last_attn_weights is not None else torch.zeros((x.size(0), x.size(1)), device=x.device)
        
        return pred_state, stage_logits, risk, query_attention

class TemporalTransformerForecaster(BaseForecaster):
    def __init__(
        self,
        feature_dim: int = 24,
        hidden_dim: int = 128,
        num_heads: int = 4,
        num_layers: int = 2,
        num_classes: int = 9,
        dropout: float = 0.1,
        device: Optional[str] = None
    ):
        self.feature_dim = feature_dim
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.num_classes = num_classes
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = TemporalTransformerNetwork(
            feature_dim=feature_dim,
            hidden_dim=hidden_dim,
            num_heads=num_heads,
            num_layers=num_layers,
            num_classes=num_classes,
            dropout=dropout
        ).to(self.device)

    def predict_next(self, history: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float, Optional[np.ndarray]]:
        self.model.eval()
        if history.ndim == 2:
            history = history[np.newaxis, :, :] # [1, seq_len, feat_dim]
            
        tensor_x = torch.tensor(history, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            pred_state, stage_logits, risk, query_attn = self.model(tensor_x)
            stage_probs = F.softmax(stage_logits, dim=-1).cpu().numpy()[0]
            next_state = pred_state.cpu().numpy()[0]
            risk_score = float(risk.cpu().numpy()[0, 0])
            attn_weights = query_attn.cpu().numpy()[0]
            
        return next_state, stage_probs, risk_score, attn_weights

    def save(self, filepath: str):
        torch.save(self.model.state_dict(), filepath)

    def load(self, filepath: str):
        self.model.load_state_dict(torch.load(filepath, map_location=self.device))
        self.model.eval()
