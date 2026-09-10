"""
Feature Normalization & Scaling Module.
Provides robust scaling and boundary clipping for 24-dimensional Network State vectors.
"""

import json
from pathlib import Path
from typing import List, Dict, Union
import numpy as np
from app.preprocessing.schema import FEATURE_COLUMNS

class NetworkStateScaler:
    def __init__(self, feature_names: List[str] = None):
        self.feature_names = feature_names or FEATURE_COLUMNS
        self.dim = len(self.feature_names)
        self.min_vals = np.zeros(self.dim, dtype=np.float32)
        self.max_vals = np.ones(self.dim, dtype=np.float32)
        self.is_fitted = False
        self._set_default_domain_bounds()

    def _set_default_domain_bounds(self):
        """Set realistic cybersecurity domain bounds as fallback before dataset fitting."""
        domain_bounds = {
            "flow_duration_sec": (0.0, 60.0),
            "fwd_packets_total": (0.0, 5000.0),
            "bwd_packets_total": (0.0, 5000.0),
            "fwd_bytes_total": (0.0, 10_000_000.0),
            "bwd_bytes_total": (0.0, 20_000_000.0),
            "packet_rate_pps": (0.0, 1000.0),
            "byte_rate_bps": (0.0, 5_000_000.0),
            "fwd_bwd_packet_ratio": (0.0, 10.0),
            "flow_iat_mean": (0.0, 5.0),
            "flow_iat_std": (0.0, 5.0),
            "packet_size_mean": (0.0, 1500.0),
            "packet_size_std": (0.0, 1000.0),
            "tcp_syn_ratio": (0.0, 1.0),
            "tcp_rst_ratio": (0.0, 1.0),
            "tcp_fin_ratio": (0.0, 1.0),
            "tcp_psh_ratio": (0.0, 1.0),
            "tcp_window_mean": (0.0, 65535.0),
            "ttl_variance": (0.0, 200.0),
            "unique_dst_ips": (0.0, 255.0),
            "unique_src_ports": (0.0, 1000.0),
            "dst_port_diversity": (0.0, 5.0),
            "failed_connection_ratio": (0.0, 1.0),
            "port_scan_indicator": (0.0, 1.0),
            "internal_lateral_ratio": (0.0, 1.0),
        }
        for i, col in enumerate(self.feature_names):
            if col in domain_bounds:
                self.min_vals[i] = domain_bounds[col][0]
                self.max_vals[i] = domain_bounds[col][1]

    def fit(self, X: np.ndarray):
        """Fit scaler on a 2D numpy array [N_samples, FEATURE_DIM]."""
        X = np.asarray(X, dtype=np.float32)
        mins = np.percentile(X, 1, axis=0)
        maxs = np.percentile(X, 99, axis=0)
        
        # Avoid division by zero
        diff = maxs - mins
        diff[diff < 1e-6] = 1.0
        self.min_vals = mins
        self.max_vals = mins + diff
        self.is_fitted = True

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Scale inputs into [0.0, 1.0] range with clipping."""
        X = np.asarray(X, dtype=np.float32)
        diff = self.max_vals - self.min_vals
        diff[diff < 1e-6] = 1.0
        
        scaled = (X - self.min_vals) / diff
        return np.clip(scaled, 0.0, 1.0)

    def inverse_transform(self, X_scaled: np.ndarray) -> np.ndarray:
        """Convert scaled features back to original physical units."""
        X_scaled = np.asarray(X_scaled, dtype=np.float32)
        diff = self.max_vals - self.min_vals
        return X_scaled * diff + self.min_vals

    def save(self, filepath: Union[str, Path]):
        """Persist scaler bounds to JSON."""
        data = {
            "feature_names": self.feature_names,
            "min_vals": self.min_vals.tolist(),
            "max_vals": self.max_vals.tolist(),
            "is_fitted": self.is_fitted
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: Union[str, Path]):
        """Load scaler bounds from JSON."""
        with open(filepath, "r") as f:
            data = json.load(f)
        self.feature_names = data["feature_names"]
        self.min_vals = np.array(data["min_vals"], dtype=np.float32)
        self.max_vals = np.array(data["max_vals"], dtype=np.float32)
        self.is_fitted = data.get("is_fitted", True)
