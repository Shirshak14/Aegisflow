"""
Unit Tests for Preprocessing, Feature Schema, Windowing, and Normalization.
"""

import pytest
import numpy as np
import pandas as pd
from app.preprocessing.schema import FEATURE_COLUMNS, ATTACK_STAGES, NetworkStateVector
from app.preprocessing.scaler import NetworkStateScaler
from app.preprocessing.windowing import TemporalWindowAggregator, create_sequences_from_states
from app.preprocessing.adapters import DatasetAdapter

def test_feature_columns_dimension():
    assert len(FEATURE_COLUMNS) == 24
    assert "flow_duration_sec" in FEATURE_COLUMNS
    assert "port_scan_indicator" in FEATURE_COLUMNS
    assert "internal_lateral_ratio" in FEATURE_COLUMNS

def test_attack_stages_count():
    assert len(ATTACK_STAGES) == 9
    assert ATTACK_STAGES[0] == "Normal"
    assert ATTACK_STAGES[1] == "Reconnaissance"
    assert ATTACK_STAGES[8] == "Exfiltration"

def test_scaler_bounds_clipping():
    scaler = NetworkStateScaler()
    raw = np.array([[10.0, 500.0, 500.0, 10000.0, 20000.0, 100.0, 50000.0, 1.0, 0.05, 0.01,
                     400.0, 200.0, 0.1, 0.05, 0.05, 0.3, 16000.0, 1.5, 10.0, 50.0, 1.2, 0.05, 0.1, 0.1]])
    scaled = scaler.transform(raw)
    assert scaled.shape == (1, 24)
    assert np.all(scaled >= 0.0)
    assert np.all(scaled <= 1.0)

def test_window_aggregator_dataframe():
    df = pd.DataFrame([
        {"timestamp": 0.0, "tot_fwd_pkts": 10, "tot_bwd_pkts": 10, "tot_fwd_bytes": 1000, "tot_bwd_bytes": 2000, "stage": "Normal"},
        {"timestamp": 5.0, "tot_fwd_pkts": 20, "tot_bwd_pkts": 15, "tot_fwd_bytes": 2000, "tot_bwd_bytes": 3000, "stage": "Normal"},
        {"timestamp": 12.0, "tot_fwd_pkts": 50, "tot_bwd_pkts": 5, "tot_fwd_bytes": 5000, "tot_bwd_bytes": 500, "stage": "Reconnaissance"}
    ])
    aggregator = TemporalWindowAggregator(window_size_sec=10.0)
    states = aggregator.aggregate_flows_to_states(df)
    assert len(states) == 2
    assert states[0].window_id == 0
    assert states[1].window_id == 1
    assert len(states[0].features) == 24
    assert states[0].ground_truth_stage == "Normal"
    assert states[1].ground_truth_stage == "Reconnaissance"

def test_sequence_creation_no_leakage():
    states = [
        NetworkStateVector(
            timestamp=float(i * 10),
            window_id=i,
            features=[0.1] * 24,
            feature_dict={},
            ground_truth_stage="Normal" if i < 15 else "Reconnaissance",
            is_synthetic=True
        )
        for i in range(25)
    ]
    X, Y_st, Y_sg, Y_rk = create_sequences_from_states(states, sequence_length=10, forecast_horizon_k=5)
    assert len(X) == 11 # 25 - 10 - 5 + 1
    assert X.shape == (11, 10, 24)
    assert Y_st.shape == (11, 5, 24)
    assert Y_sg.shape == (11, 5)
    assert Y_rk.shape == (11, 5)
