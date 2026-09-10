"""
Unit Tests for ML Model Architectures: LogReg, LSTM, and Temporal Transformer.
"""

import pytest
import numpy as np
import torch
from app.models.logreg import BaselineLogisticRegressionForecaster
from app.models.lstm import LSTMForecaster
from app.models.transformer import TemporalTransformerForecaster

def test_logistic_regression_fit_predict():
    model = BaselineLogisticRegressionForecaster(feature_dim=24, num_classes=9)
    X = np.random.uniform(0, 1, size=(20, 10, 24)).astype(np.float32)
    y_st = np.random.uniform(0, 1, size=(20, 5, 24)).astype(np.float32)
    y_sg = np.random.randint(0, 9, size=(20, 5)).astype(np.int64)
    
    model.fit(X, y_st, y_sg)
    assert model.is_fitted is True

    test_seq = np.random.uniform(0, 1, size=(10, 24)).astype(np.float32)
    next_st, probs, risk, attn = model.predict_next(test_seq)
    
    assert next_st.shape == (24,)
    assert probs.shape == (9,)
    assert np.isclose(np.sum(probs), 1.0, atol=1e-3)
    assert 0.0 <= risk <= 1.0
    assert attn is None

def test_lstm_forward():
    model = LSTMForecaster(feature_dim=24, hidden_dim=64, num_layers=2, num_classes=9, device="cpu")
    test_seq = np.random.uniform(0, 1, size=(10, 24)).astype(np.float32)
    next_st, probs, risk, attn = model.predict_next(test_seq)
    
    assert next_st.shape == (24,)
    assert probs.shape == (9,)
    assert np.isclose(np.sum(probs), 1.0, atol=1e-3)
    assert 0.0 <= risk <= 1.0

def test_transformer_forward_and_attention():
    model = TemporalTransformerForecaster(feature_dim=24, hidden_dim=64, num_heads=4, num_layers=2, num_classes=9, device="cpu")
    test_seq = np.random.uniform(0, 1, size=(10, 24)).astype(np.float32)
    next_st, probs, risk, attn = model.predict_next(test_seq)
    
    assert next_st.shape == (24,)
    assert probs.shape == (9,)
    assert np.isclose(np.sum(probs), 1.0, atol=1e-3)
    assert 0.0 <= risk <= 1.0
    assert attn is not None
    assert len(attn) == 10 # Attention for each history step
