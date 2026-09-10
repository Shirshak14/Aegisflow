"""
Core Network State Feature Schema & Attack Taxonomy for SIH26153.
Defines the 24 canonical network state dimensions and 9 MITRE-aligned attack stages.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field

FEATURE_COLUMNS: List[str] = [
    # Flow-level features (1-10)
    "flow_duration_sec",
    "fwd_packets_total",
    "bwd_packets_total",
    "fwd_bytes_total",
    "bwd_bytes_total",
    "packet_rate_pps",
    "byte_rate_bps",
    "fwd_bwd_packet_ratio",
    "flow_iat_mean",
    "flow_iat_std",
    
    # Packet-level features (11-18)
    "packet_size_mean",
    "packet_size_std",
    "tcp_syn_ratio",
    "tcp_rst_ratio",
    "tcp_fin_ratio",
    "tcp_psh_ratio",
    "tcp_window_mean",
    "ttl_variance",
    
    # Host & Behavioral features (19-24)
    "unique_dst_ips",
    "unique_src_ports",
    "dst_port_diversity",
    "failed_connection_ratio",
    "port_scan_indicator",
    "internal_lateral_ratio"
]

FEATURE_DESCRIPTIONS: Dict[str, str] = {
    "flow_duration_sec": "Total active flow duration in time window",
    "fwd_packets_total": "Total forward direction packets",
    "bwd_packets_total": "Total backward direction packets",
    "fwd_bytes_total": "Total payload bytes in forward direction",
    "bwd_bytes_total": "Total payload bytes in backward direction",
    "packet_rate_pps": "Aggregate packets per second rate",
    "byte_rate_bps": "Aggregate bandwidth in bytes per second",
    "fwd_bwd_packet_ratio": "Ratio of forward to backward packet volume",
    "flow_iat_mean": "Mean packet inter-arrival time (jitter indicator)",
    "flow_iat_std": "Standard deviation of inter-arrival time",
    "packet_size_mean": "Average packet payload size (bytes)",
    "packet_size_std": "Variance in packet payload sizes",
    "tcp_syn_ratio": "Ratio of TCP SYN flags (SYN scanning / floods)",
    "tcp_rst_ratio": "Ratio of TCP RST flags (rejected connections)",
    "tcp_fin_ratio": "Ratio of TCP FIN flags (closed sessions)",
    "tcp_psh_ratio": "Ratio of TCP PSH flags (interactive push data)",
    "tcp_window_mean": "Average advertised TCP receive window size",
    "ttl_variance": "IP Time-To-Live variance (spoofing indicator)",
    "unique_dst_ips": "Number of distinct destination endpoints contacted",
    "unique_src_ports": "Count of dynamic source ports utilized",
    "dst_port_diversity": "Entropy of targeted destination service ports",
    "failed_connection_ratio": "Ratio of unacknowledged / reset handshakes",
    "port_scan_indicator": "Synthesized port reconnaissance score [0, 1]",
    "internal_lateral_ratio": "Ratio of internal private IP to private IP traffic"
}

ATTACK_STAGES: Dict[int, str] = {
    0: "Normal",
    1: "Reconnaissance",
    2: "Initial Access",
    3: "Execution",
    4: "Persistence",
    5: "Privilege Escalation",
    6: "Lateral Movement",
    7: "Command and Control",
    8: "Exfiltration"
}

STAGE_TO_ID: Dict[str, int] = {v: k for k, v in ATTACK_STAGES.items()}

# Stage severity & default baseline risk weights
STAGE_SEVERITY: Dict[str, float] = {
    "Normal": 0.05,
    "Reconnaissance": 0.30,
    "Initial Access": 0.55,
    "Execution": 0.70,
    "Persistence": 0.75,
    "Privilege Escalation": 0.82,
    "Lateral Movement": 0.88,
    "Command and Control": 0.92,
    "Exfiltration": 0.98
}

class NetworkStateVector(BaseModel):
    timestamp: float = Field(..., description="Epoch timestamp of temporal window")
    window_id: int = Field(0, description="Sequential window index")
    features: List[float] = Field(..., description="24-dimensional normalized feature vector")
    feature_dict: Dict[str, float] = Field(default_factory=dict, description="Named feature values")
    ground_truth_stage: str = Field("Normal", description="Label if known")
    is_synthetic: bool = Field(False, description="Whether generated via demo generator")
