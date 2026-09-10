"""
Unit Tests for K-Step Autoregressive Forecaster.
"""

import pytest
import numpy as np
from app.simulation.synthetic_traffic import SyntheticTrafficGenerator
from app.models.transformer import TemporalTransformerForecaster
from app.forecasting.k_step_forecaster import KStepAttackForecaster

def test_k_step_forecasting_trajectory():
    generator = SyntheticTrafficGenerator()
    states = generator.generate_scenario("Full Multi-Stage Attack", total_windows=15)
    
    model = TemporalTransformerForecaster(feature_dim=24, hidden_dim=64, num_heads=4, num_layers=2, num_classes=9, device="cpu")
    forecaster = KStepAttackForecaster(model=model, forecast_horizon_k=5, window_size_sec=10.0)
    
    result = forecaster.forecast_trajectory(states, horizon_k=5)
    
    assert "trajectory" in result
    assert len(result["trajectory"]) == 5
    assert result["forecast_horizon_k"] == 5
    
    # Check step structure
    step_1 = result["trajectory"][0]
    assert step_1["step"] == 1
    assert step_1["time_horizon"] == "+10s"
    assert "predicted_stage" in step_1
    assert "stage_probability" in step_1
    assert "risk_score" in step_1
    assert "top_features" in step_1
    assert len(step_1["top_features"]) == 5
    assert "mitre" in step_1
    assert "tactic_id" in step_1["mitre"]
