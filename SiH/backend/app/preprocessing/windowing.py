"""
Temporal Windowing and Sequence Creation Module.
Aggregates network flow events into discrete time slices and constructs sliding temporal sequences.
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
import pandas as pd
from app.preprocessing.schema import FEATURE_COLUMNS, ATTACK_STAGES, STAGE_TO_ID, NetworkStateVector
from app.preprocessing.scaler import NetworkStateScaler

class TemporalWindowAggregator:
    def __init__(self, window_size_sec: float = 10.0, scaler: Optional[NetworkStateScaler] = None):
        self.window_size_sec = window_size_sec
        self.scaler = scaler or NetworkStateScaler()

    def aggregate_flows_to_states(self, df: pd.DataFrame, timestamp_col: str = "timestamp", label_col: Optional[str] = "stage") -> List[NetworkStateVector]:
        """
        Groups flow-level records into temporal windows of duration `window_size_sec`.
        Computes the 24 aggregate network state features for each window.
        """
        if df.empty:
            return []

        df = df.sort_values(by=timestamp_col).reset_index(drop=True)
        min_ts = df[timestamp_col].min()
        df["window_id"] = ((df[timestamp_col] - min_ts) // self.window_size_sec).astype(int)

        states: List[NetworkStateVector] = []
        for win_id, group in df.groupby("window_id"):
            feat_dict = {}
            # Compute flow-level aggregates
            feat_dict["flow_duration_sec"] = float(group.get("flow_duration_sec", pd.Series([self.window_size_sec])).sum())
            feat_dict["fwd_packets_total"] = float(group.get("fwd_packets_total", group.get("tot_fwd_pkts", pd.Series([0]))).sum())
            feat_dict["bwd_packets_total"] = float(group.get("bwd_packets_total", group.get("tot_bwd_pkts", pd.Series([0]))).sum())
            feat_dict["fwd_bytes_total"] = float(group.get("fwd_bytes_total", group.get("tot_fwd_bytes", pd.Series([0]))).sum())
            feat_dict["bwd_bytes_total"] = float(group.get("bwd_bytes_total", group.get("tot_bwd_bytes", pd.Series([0]))).sum())
            
            tot_pkts = feat_dict["fwd_packets_total"] + feat_dict["bwd_packets_total"]
            tot_bytes = feat_dict["fwd_bytes_total"] + feat_dict["bwd_bytes_total"]
            
            feat_dict["packet_rate_pps"] = float(tot_pkts / max(self.window_size_sec, 0.1))
            feat_dict["byte_rate_bps"] = float(tot_bytes / max(self.window_size_sec, 0.1))
            feat_dict["fwd_bwd_packet_ratio"] = float(feat_dict["fwd_packets_total"] / max(feat_dict["bwd_packets_total"], 1.0))
            
            feat_dict["flow_iat_mean"] = float(group.get("flow_iat_mean", pd.Series([0.05])).mean())
            feat_dict["flow_iat_std"] = float(group.get("flow_iat_std", pd.Series([0.01])).std(ddof=0)) if len(group) > 1 else 0.0
            
            # Packet-level aggregates
            feat_dict["packet_size_mean"] = float(group.get("packet_size_mean", group.get("pkt_len_mean", pd.Series([tot_bytes / max(tot_pkts, 1.0)]))).mean())
            feat_dict["packet_size_std"] = float(group.get("packet_size_std", group.get("pkt_len_std", pd.Series([0.0]))).mean())
            feat_dict["tcp_syn_ratio"] = float(group.get("tcp_syn_ratio", group.get("syn_flag_count", pd.Series([0.0]))).mean())
            feat_dict["tcp_rst_ratio"] = float(group.get("tcp_rst_ratio", group.get("rst_flag_count", pd.Series([0.0]))).mean())
            feat_dict["tcp_fin_ratio"] = float(group.get("tcp_fin_ratio", group.get("fin_flag_count", pd.Series([0.0]))).mean())
            feat_dict["tcp_psh_ratio"] = float(group.get("tcp_psh_ratio", group.get("psh_flag_count", pd.Series([0.0]))).mean())
            feat_dict["tcp_window_mean"] = float(group.get("tcp_window_mean", group.get("init_win_bytes_fwd", pd.Series([8192.0]))).mean())
            feat_dict["ttl_variance"] = float(group.get("ttl_variance", pd.Series([1.0])).var(ddof=0)) if len(group) > 1 else 0.0
            
            # Host / Behavioral aggregates
            feat_dict["unique_dst_ips"] = float(group.get("unique_dst_ips", group.get("dst_ip", pd.Series(["192.168.1.1"]))).nunique())
            feat_dict["unique_src_ports"] = float(group.get("unique_src_ports", group.get("src_port", pd.Series([80]))).nunique())
            
            # Port entropy / diversity
            if "dst_port" in group:
                port_counts = group["dst_port"].value_counts(normalize=True)
                entropy = -float(np.sum(port_counts * np.log2(port_counts + 1e-9)))
            else:
                entropy = float(group.get("dst_port_diversity", pd.Series([0.5])).mean())
            feat_dict["dst_port_diversity"] = entropy
            
            feat_dict["failed_connection_ratio"] = float(group.get("failed_connection_ratio", pd.Series([0.02])).mean())
            feat_dict["port_scan_indicator"] = float(group.get("port_scan_indicator", pd.Series([min(1.0, entropy / 3.0)])).mean())
            feat_dict["internal_lateral_ratio"] = float(group.get("internal_lateral_ratio", pd.Series([0.1])).mean())
            
            # Form raw vector aligned with FEATURE_COLUMNS
            raw_vector = np.array([feat_dict[col] for col in FEATURE_COLUMNS], dtype=np.float32)
            
            # Determine majority ground truth stage if provided
            stage_str = "Normal"
            if label_col and label_col in group:
                mode_stage = group[label_col].mode()
                if not mode_stage.empty:
                    stage_str = str(mode_stage.iloc[0])
            
            scaled_vec = self.scaler.transform(raw_vector[np.newaxis, :])[0]
            
            state = NetworkStateVector(
                timestamp=float(min_ts + win_id * self.window_size_sec),
                window_id=int(win_id),
                features=scaled_vec.tolist(),
                feature_dict={col: float(feat_dict[col]) for col in FEATURE_COLUMNS},
                ground_truth_stage=stage_str,
                is_synthetic=bool(group.get("is_synthetic", pd.Series([False])).any())
            )
            states.append(state)
            
        return states

def create_sequences_from_states(
    states: List[NetworkStateVector],
    sequence_length: int = 10,
    forecast_horizon_k: int = 5
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Constructs time-series samples avoiding data leakage.
    Returns:
    - X_seq: [N_samples, sequence_length, FEATURE_DIM] (historical states S_t-N+1 ... S_t)
    - Y_states: [N_samples, forecast_horizon_k, FEATURE_DIM] (future states S_t+1 ... S_t+K)
    - Y_stages: [N_samples, forecast_horizon_k] (future stage integer IDs)
    - Y_risks: [N_samples, forecast_horizon_k] (future risk values 0.0-1.0)
    """
    if len(states) < sequence_length + forecast_horizon_k:
        return np.empty((0, sequence_length, len(FEATURE_COLUMNS))), np.empty((0, forecast_horizon_k, len(FEATURE_COLUMNS))), np.empty((0, forecast_horizon_k)), np.empty((0, forecast_horizon_k))

    feature_matrix = np.array([s.features for s in states], dtype=np.float32)
    stage_ids = np.array([STAGE_TO_ID.get(s.ground_truth_stage, 0) for s in states], dtype=np.int64)
    
    # Precompute severity risk score per stage
    from app.preprocessing.schema import STAGE_SEVERITY
    risk_values = np.array([STAGE_SEVERITY.get(s.ground_truth_stage, 0.05) for s in states], dtype=np.float32)

    X_seq_list = []
    Y_states_list = []
    Y_stages_list = []
    Y_risks_list = []

    num_samples = len(states) - sequence_length - forecast_horizon_k + 1
    for i in range(num_samples):
        # Input history: windows [i : i + sequence_length]
        x = feature_matrix[i : i + sequence_length]
        # Future targets: windows [i + sequence_length : i + sequence_length + forecast_horizon_k]
        y_state = feature_matrix[i + sequence_length : i + sequence_length + forecast_horizon_k]
        y_stage = stage_ids[i + sequence_length : i + sequence_length + forecast_horizon_k]
        y_risk = risk_values[i + sequence_length : i + sequence_length + forecast_horizon_k]

        X_seq_list.append(x)
        Y_states_list.append(y_state)
        Y_stages_list.append(y_stage)
        Y_risks_list.append(y_risk)

    return (
        np.array(X_seq_list, dtype=np.float32),
        np.array(Y_states_list, dtype=np.float32),
        np.array(Y_stages_list, dtype=np.int64),
        np.array(Y_risks_list, dtype=np.float32)
    )
