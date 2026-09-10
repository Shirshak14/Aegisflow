"""
Abstract Base Class for Network Attack Forecasting Models.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any
import numpy as np

class BaseForecaster(ABC):
    """
    Abstract interface for multi-head network state and attack stage forecasters.
    """

    @abstractmethod
    def predict_next(self, history: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float, Optional[np.ndarray]]:
        """
        Given a history sequence of shape [sequence_length, feature_dim] or [1, sequence_length, feature_dim],
        returns:
        - next_state: [feature_dim] (Predicted next normalized network state vector)
        - stage_probs: [num_classes] (Probability distribution across attack stages)
        - risk_score: float in [0.0, 1.0]
        - attention_weights: Optional[np.ndarray] of shape [sequence_length] or None
        """
        pass

    @abstractmethod
    def save(self, filepath: str):
        """Persist model weights / parameters."""
        pass

    @abstractmethod
    def load(self, filepath: str):
        """Load model weights / parameters."""
        pass
