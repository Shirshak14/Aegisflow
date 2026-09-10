"""
Synthetic Temporal Network Traffic Generator for SIH26153 Demo Mode.
Generates realistic temporal network state sequences with genuine behavioral correlations.
Clearly flagged with is_synthetic=True.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from app.preprocessing.schema import (
    FEATURE_COLUMNS,
    ATTACK_STAGES,
    STAGE_TO_ID,
    STAGE_SEVERITY,
    NetworkStateVector
)
from app.preprocessing.scaler import NetworkStateScaler

class SyntheticTrafficGenerator:
    """
    Simulates high-fidelity temporal network state sequences modeling the cyber kill-chain.
    """

    def __init__(self, scaler: Optional[NetworkStateScaler] = None):
        self.scaler = scaler or NetworkStateScaler()

    def generate_state_for_stage(self, stage: str, window_id: int, timestamp: float, noise_level: float = 0.05) -> NetworkStateVector:
        """
        Generates a 24-dimensional NetworkStateVector matching the physical and behavioral
        characteristics of a specific MITRE attack stage.
        """
        feats: Dict[str, float] = {}
        rng = np.random.default_rng(seed=int(timestamp * 1000) % 1000000 + window_id)

        # Baseline jitter/noise helper
        def n(base: float, scale: float = 0.1) -> float:
            return float(max(0.0, base + rng.normal(0, base * scale * (1.0 + noise_level))))

        if stage == "Normal":
            feats["flow_duration_sec"] = n(10.0, 0.05)
            feats["fwd_packets_total"] = n(250.0, 0.15)
            feats["bwd_packets_total"] = n(300.0, 0.15)
            feats["fwd_bytes_total"] = n(45_000.0, 0.20)
            feats["bwd_bytes_total"] = n(180_000.0, 0.20)
            feats["packet_rate_pps"] = (feats["fwd_packets_total"] + feats["bwd_packets_total"]) / 10.0
            feats["byte_rate_bps"] = (feats["fwd_bytes_total"] + feats["bwd_bytes_total"]) / 10.0
            feats["fwd_bwd_packet_ratio"] = feats["fwd_packets_total"] / max(feats["bwd_packets_total"], 1.0)
            feats["flow_iat_mean"] = n(0.04, 0.10)
            feats["flow_iat_std"] = n(0.02, 0.10)
            feats["packet_size_mean"] = n(410.0, 0.10)
            feats["packet_size_std"] = n(320.0, 0.10)
            feats["tcp_syn_ratio"] = float(np.clip(rng.uniform(0.02, 0.05), 0.0, 1.0))
            feats["tcp_rst_ratio"] = float(np.clip(rng.uniform(0.01, 0.03), 0.0, 1.0))
            feats["tcp_fin_ratio"] = float(np.clip(rng.uniform(0.04, 0.07), 0.0, 1.0))
            feats["tcp_psh_ratio"] = float(np.clip(rng.uniform(0.20, 0.35), 0.0, 1.0))
            feats["tcp_window_mean"] = n(28_000.0, 0.10)
            feats["ttl_variance"] = n(1.5, 0.20)
            feats["unique_dst_ips"] = n(12.0, 0.20)
            feats["unique_src_ports"] = n(45.0, 0.20)
            feats["dst_port_diversity"] = n(1.2, 0.15)
            feats["failed_connection_ratio"] = float(np.clip(rng.uniform(0.01, 0.04), 0.0, 1.0))
            feats["port_scan_indicator"] = float(np.clip(rng.uniform(0.02, 0.08), 0.0, 1.0))
            feats["internal_lateral_ratio"] = float(np.clip(rng.uniform(0.05, 0.15), 0.0, 1.0))

        elif stage == "Reconnaissance":
            # High port diversity, high SYN, high failed connections, scanning indicator
            feats["flow_duration_sec"] = n(10.0, 0.05)
            feats["fwd_packets_total"] = n(1800.0, 0.15)
            feats["bwd_packets_total"] = n(250.0, 0.20)
            feats["fwd_bytes_total"] = n(80_000.0, 0.15)
            feats["bwd_bytes_total"] = n(15_000.0, 0.20)
            feats["packet_rate_pps"] = (feats["fwd_packets_total"] + feats["bwd_packets_total"]) / 10.0
            feats["byte_rate_bps"] = (feats["fwd_bytes_total"] + feats["bwd_bytes_total"]) / 10.0
            feats["fwd_bwd_packet_ratio"] = feats["fwd_packets_total"] / max(feats["bwd_packets_total"], 1.0)
            feats["flow_iat_mean"] = n(0.005, 0.10) # Rapid bursts
            feats["flow_iat_std"] = n(0.002, 0.10)
            feats["packet_size_mean"] = n(48.0, 0.08) # Small probe packets
            feats["packet_size_std"] = n(12.0, 0.10)
            feats["tcp_syn_ratio"] = float(np.clip(rng.uniform(0.72, 0.95), 0.0, 1.0))
            feats["tcp_rst_ratio"] = float(np.clip(rng.uniform(0.40, 0.65), 0.0, 1.0))
            feats["tcp_fin_ratio"] = float(np.clip(rng.uniform(0.01, 0.03), 0.0, 1.0))
            feats["tcp_psh_ratio"] = float(np.clip(rng.uniform(0.02, 0.06), 0.0, 1.0))
            feats["tcp_window_mean"] = n(1024.0, 0.20)
            feats["ttl_variance"] = n(8.5, 0.25)
            feats["unique_dst_ips"] = n(85.0, 0.15) # IP sweep
            feats["unique_src_ports"] = n(450.0, 0.15)
            feats["dst_port_diversity"] = n(4.2, 0.10) # High port entropy
            feats["failed_connection_ratio"] = float(np.clip(rng.uniform(0.65, 0.90), 0.0, 1.0))
            feats["port_scan_indicator"] = float(np.clip(rng.uniform(0.85, 0.98), 0.0, 1.0))
            feats["internal_lateral_ratio"] = float(np.clip(rng.uniform(0.10, 0.25), 0.0, 1.0))

        elif stage == "Initial Access":
            # Targeted authentication brute force / exploit delivery
            feats["flow_duration_sec"] = n(10.0, 0.05)
            feats["fwd_packets_total"] = n(1200.0, 0.15)
            feats["bwd_packets_total"] = n(1100.0, 0.15)
            feats["fwd_bytes_total"] = n(180_000.0, 0.15)
            feats["bwd_bytes_total"] = n(90_000.0, 0.15)
            feats["packet_rate_pps"] = (feats["fwd_packets_total"] + feats["bwd_packets_total"]) / 10.0
            feats["byte_rate_bps"] = (feats["fwd_bytes_total"] + feats["bwd_bytes_total"]) / 10.0
            feats["fwd_bwd_packet_ratio"] = 1.1
            feats["flow_iat_mean"] = n(0.009, 0.15)
            feats["flow_iat_std"] = n(0.008, 0.15)
            feats["packet_size_mean"] = n(150.0, 0.12)
            feats["packet_size_std"] = n(95.0, 0.15)
            feats["tcp_syn_ratio"] = float(np.clip(rng.uniform(0.35, 0.55), 0.0, 1.0))
            feats["tcp_rst_ratio"] = float(np.clip(rng.uniform(0.30, 0.50), 0.0, 1.0))
            feats["tcp_fin_ratio"] = float(np.clip(rng.uniform(0.05, 0.10), 0.0, 1.0))
            feats["tcp_psh_ratio"] = float(np.clip(rng.uniform(0.40, 0.60), 0.0, 1.0))
            feats["tcp_window_mean"] = n(8192.0, 0.15)
            feats["ttl_variance"] = n(3.2, 0.20)
            feats["unique_dst_ips"] = n(3.0, 0.30) # Focused on 1-3 victim servers
            feats["unique_src_ports"] = n(280.0, 0.15)
            feats["dst_port_diversity"] = n(0.8, 0.20) # Focused on specific ports (e.g., 22/3389/443)
            feats["failed_connection_ratio"] = float(np.clip(rng.uniform(0.50, 0.75), 0.0, 1.0))
            feats["port_scan_indicator"] = float(np.clip(rng.uniform(0.20, 0.40), 0.0, 1.0))
            feats["internal_lateral_ratio"] = float(np.clip(rng.uniform(0.15, 0.30), 0.0, 1.0))

        elif stage == "Execution":
            # Exploit execution, reverse shell initialization, payload download
            feats["flow_duration_sec"] = n(10.0, 0.05)
            feats["fwd_packets_total"] = n(850.0, 0.15)
            feats["bwd_packets_total"] = n(920.0, 0.15)
            feats["fwd_bytes_total"] = n(650_000.0, 0.25) # Payload download
            feats["bwd_bytes_total"] = n(450_000.0, 0.20)
            feats["packet_rate_pps"] = (feats["fwd_packets_total"] + feats["bwd_packets_total"]) / 10.0
            feats["byte_rate_bps"] = (feats["fwd_bytes_total"] + feats["bwd_bytes_total"]) / 10.0
            feats["fwd_bwd_packet_ratio"] = 0.92
            feats["flow_iat_mean"] = n(0.015, 0.15)
            feats["flow_iat_std"] = n(0.025, 0.20)
            feats["packet_size_mean"] = n(620.0, 0.15)
            feats["packet_size_std"] = n(480.0, 0.15)
            feats["tcp_syn_ratio"] = float(np.clip(rng.uniform(0.08, 0.18), 0.0, 1.0))
            feats["tcp_rst_ratio"] = float(np.clip(rng.uniform(0.05, 0.12), 0.0, 1.0))
            feats["tcp_fin_ratio"] = float(np.clip(rng.uniform(0.04, 0.08), 0.0, 1.0))
            feats["tcp_psh_ratio"] = float(np.clip(rng.uniform(0.55, 0.75), 0.0, 1.0)) # Interactive shell
            feats["tcp_window_mean"] = n(16_384.0, 0.15)
            feats["ttl_variance"] = n(2.0, 0.20)
            feats["unique_dst_ips"] = n(4.0, 0.25)
            feats["unique_src_ports"] = n(60.0, 0.20)
            feats["dst_port_diversity"] = n(1.1, 0.20)
            feats["failed_connection_ratio"] = float(np.clip(rng.uniform(0.10, 0.25), 0.0, 1.0))
            feats["port_scan_indicator"] = float(np.clip(rng.uniform(0.05, 0.15), 0.0, 1.0))
            feats["internal_lateral_ratio"] = float(np.clip(rng.uniform(0.20, 0.40), 0.0, 1.0))

        elif stage == "Persistence":
            # Scheduled tasks, backdoor registration
            feats["flow_duration_sec"] = n(10.0, 0.05)
            feats["fwd_packets_total"] = n(350.0, 0.15)
            feats["bwd_packets_total"] = n(380.0, 0.15)
            feats["fwd_bytes_total"] = n(120_000.0, 0.20)
            feats["bwd_bytes_total"] = n(140_000.0, 0.20)
            feats["packet_rate_pps"] = (feats["fwd_packets_total"] + feats["bwd_packets_total"]) / 10.0
            feats["byte_rate_bps"] = (feats["fwd_bytes_total"] + feats["bwd_bytes_total"]) / 10.0
            feats["fwd_bwd_packet_ratio"] = 0.92
            feats["flow_iat_mean"] = n(0.03, 0.15)
            feats["flow_iat_std"] = n(0.018, 0.15)
            feats["packet_size_mean"] = n(360.0, 0.15)
            feats["packet_size_std"] = n(240.0, 0.15)
            feats["tcp_syn_ratio"] = float(np.clip(rng.uniform(0.06, 0.14), 0.0, 1.0))
            feats["tcp_rst_ratio"] = float(np.clip(rng.uniform(0.02, 0.06), 0.0, 1.0))
            feats["tcp_fin_ratio"] = float(np.clip(rng.uniform(0.05, 0.09), 0.0, 1.0))
            feats["tcp_psh_ratio"] = float(np.clip(rng.uniform(0.35, 0.50), 0.0, 1.0))
            feats["tcp_window_mean"] = n(24_000.0, 0.15)
            feats["ttl_variance"] = n(1.8, 0.20)
            feats["unique_dst_ips"] = n(6.0, 0.25)
            feats["unique_src_ports"] = n(40.0, 0.20)
            feats["dst_port_diversity"] = n(1.0, 0.20)
            feats["failed_connection_ratio"] = float(np.clip(rng.uniform(0.04, 0.10), 0.0, 1.0))
            feats["port_scan_indicator"] = float(np.clip(rng.uniform(0.04, 0.10), 0.0, 1.0))
            feats["internal_lateral_ratio"] = float(np.clip(rng.uniform(0.30, 0.50), 0.0, 1.0))

        elif stage == "Privilege Escalation":
            # Internal service exploitation, named pipe / RPC queries
            feats["flow_duration_sec"] = n(10.0, 0.05)
            feats["fwd_packets_total"] = n(600.0, 0.15)
            feats["bwd_packets_total"] = n(640.0, 0.15)
            feats["fwd_bytes_total"] = n(240_000.0, 0.20)
            feats["bwd_bytes_total"] = n(310_000.0, 0.20)
            feats["packet_rate_pps"] = (feats["fwd_packets_total"] + feats["bwd_packets_total"]) / 10.0
            feats["byte_rate_bps"] = (feats["fwd_bytes_total"] + feats["bwd_bytes_total"]) / 10.0
            feats["fwd_bwd_packet_ratio"] = 0.94
            feats["flow_iat_mean"] = n(0.018, 0.15)
            feats["flow_iat_std"] = n(0.012, 0.15)
            feats["packet_size_mean"] = n(440.0, 0.15)
            feats["packet_size_std"] = n(280.0, 0.15)
            feats["tcp_syn_ratio"] = float(np.clip(rng.uniform(0.12, 0.22), 0.0, 1.0))
            feats["tcp_rst_ratio"] = float(np.clip(rng.uniform(0.08, 0.16), 0.0, 1.0))
            feats["tcp_fin_ratio"] = float(np.clip(rng.uniform(0.04, 0.08), 0.0, 1.0))
            feats["tcp_psh_ratio"] = float(np.clip(rng.uniform(0.45, 0.65), 0.0, 1.0))
            feats["tcp_window_mean"] = n(20_000.0, 0.15)
            feats["ttl_variance"] = n(2.2, 0.20)
            feats["unique_dst_ips"] = n(8.0, 0.25)
            feats["unique_src_ports"] = n(90.0, 0.20)
            feats["dst_port_diversity"] = n(1.4, 0.20)
            feats["failed_connection_ratio"] = float(np.clip(rng.uniform(0.15, 0.30), 0.0, 1.0))
            feats["port_scan_indicator"] = float(np.clip(rng.uniform(0.10, 0.25), 0.0, 1.0))
            feats["internal_lateral_ratio"] = float(np.clip(rng.uniform(0.55, 0.75), 0.0, 1.0))

        elif stage == "Lateral Movement":
            # High internal-to-internal ratio, SMB/RDP/SSH pivoting, new internal targets
            feats["flow_duration_sec"] = n(10.0, 0.05)
            feats["fwd_packets_total"] = n(1400.0, 0.15)
            feats["bwd_packets_total"] = n(1350.0, 0.15)
            feats["fwd_bytes_total"] = n(580_000.0, 0.20)
            feats["bwd_bytes_total"] = n(520_000.0, 0.20)
            feats["packet_rate_pps"] = (feats["fwd_packets_total"] + feats["bwd_packets_total"]) / 10.0
            feats["byte_rate_bps"] = (feats["fwd_bytes_total"] + feats["bwd_bytes_total"]) / 10.0
            feats["fwd_bwd_packet_ratio"] = 1.04
            feats["flow_iat_mean"] = n(0.008, 0.15)
            feats["flow_iat_std"] = n(0.007, 0.15)
            feats["packet_size_mean"] = n(400.0, 0.12)
            feats["packet_size_std"] = n(310.0, 0.15)
            feats["tcp_syn_ratio"] = float(np.clip(rng.uniform(0.25, 0.45), 0.0, 1.0))
            feats["tcp_rst_ratio"] = float(np.clip(rng.uniform(0.15, 0.35), 0.0, 1.0))
            feats["tcp_fin_ratio"] = float(np.clip(rng.uniform(0.03, 0.07), 0.0, 1.0))
            feats["tcp_psh_ratio"] = float(np.clip(rng.uniform(0.50, 0.70), 0.0, 1.0))
            feats["tcp_window_mean"] = n(16_000.0, 0.15)
            feats["ttl_variance"] = n(1.2, 0.20)
            feats["unique_dst_ips"] = n(22.0, 0.20) # Multiple internal subnets
            feats["unique_src_ports"] = n(180.0, 0.15)
            feats["dst_port_diversity"] = n(2.2, 0.15) # Port 445, 135, 3389, 5985
            feats["failed_connection_ratio"] = float(np.clip(rng.uniform(0.25, 0.45), 0.0, 1.0))
            feats["port_scan_indicator"] = float(np.clip(rng.uniform(0.35, 0.60), 0.0, 1.0))
            feats["internal_lateral_ratio"] = float(np.clip(rng.uniform(0.85, 0.98), 0.0, 1.0)) # Key differentiator

        elif stage == "Command and Control":
            # Periodic heartbeats/beaconing, low jitter IAT std, single external C2 endpoint
            feats["flow_duration_sec"] = n(10.0, 0.05)
            feats["fwd_packets_total"] = n(450.0, 0.10)
            feats["bwd_packets_total"] = n(420.0, 0.10)
            feats["fwd_bytes_total"] = n(85_000.0, 0.15)
            feats["bwd_bytes_total"] = n(120_000.0, 0.15)
            feats["packet_rate_pps"] = (feats["fwd_packets_total"] + feats["bwd_packets_total"]) / 10.0
            feats["byte_rate_bps"] = (feats["fwd_bytes_total"] + feats["bwd_bytes_total"]) / 10.0
            feats["fwd_bwd_packet_ratio"] = 1.07
            feats["flow_iat_mean"] = n(0.022, 0.05) # Precise timing
            feats["flow_iat_std"] = n(0.001, 0.05) # Almost zero jitter (beacon heartbeat)
            feats["packet_size_mean"] = n(235.0, 0.08) # Encrypted command payloads
            feats["packet_size_std"] = n(45.0, 0.08)
            feats["tcp_syn_ratio"] = float(np.clip(rng.uniform(0.03, 0.06), 0.0, 1.0))
            feats["tcp_rst_ratio"] = float(np.clip(rng.uniform(0.01, 0.03), 0.0, 1.0))
            feats["tcp_fin_ratio"] = float(np.clip(rng.uniform(0.02, 0.05), 0.0, 1.0))
            feats["tcp_psh_ratio"] = float(np.clip(rng.uniform(0.65, 0.85), 0.0, 1.0)) # Continuous push
            feats["tcp_window_mean"] = n(32_768.0, 0.10)
            feats["ttl_variance"] = n(0.5, 0.15)
            feats["unique_dst_ips"] = n(1.0, 0.05) # Fixed external C2 server
            feats["unique_src_ports"] = n(8.0, 0.15)
            feats["dst_port_diversity"] = n(0.2, 0.10) # Single port (e.g. 443 / 8443)
            feats["failed_connection_ratio"] = float(np.clip(rng.uniform(0.01, 0.03), 0.0, 1.0))
            feats["port_scan_indicator"] = float(np.clip(rng.uniform(0.01, 0.05), 0.0, 1.0))
            feats["internal_lateral_ratio"] = float(np.clip(rng.uniform(0.02, 0.08), 0.0, 1.0))

        elif stage == "Exfiltration":
            # Massive outbound bytes spike, highly skewed fwd/bwd ratio, sustained high bandwidth
            feats["flow_duration_sec"] = n(10.0, 0.05)
            feats["fwd_packets_total"] = n(4200.0, 0.10)
            feats["bwd_packets_total"] = n(350.0, 0.15)
            feats["fwd_bytes_total"] = n(5_800_000.0, 0.15) # Huge outbound data transfer
            feats["bwd_bytes_total"] = n(25_000.0, 0.15)
            feats["packet_rate_pps"] = (feats["fwd_packets_total"] + feats["bwd_packets_total"]) / 10.0
            feats["byte_rate_bps"] = (feats["fwd_bytes_total"] + feats["bwd_bytes_total"]) / 10.0
            feats["fwd_bwd_packet_ratio"] = feats["fwd_packets_total"] / max(feats["bwd_packets_total"], 1.0) # > 12.0
            feats["flow_iat_mean"] = n(0.002, 0.08)
            feats["flow_iat_std"] = n(0.001, 0.08)
            feats["packet_size_mean"] = n(1420.0, 0.05) # MTU size packet packing
            feats["packet_size_std"] = n(120.0, 0.08)
            feats["tcp_syn_ratio"] = float(np.clip(rng.uniform(0.01, 0.03), 0.0, 1.0))
            feats["tcp_rst_ratio"] = float(np.clip(rng.uniform(0.01, 0.02), 0.0, 1.0))
            feats["tcp_fin_ratio"] = float(np.clip(rng.uniform(0.01, 0.03), 0.0, 1.0))
            feats["tcp_psh_ratio"] = float(np.clip(rng.uniform(0.70, 0.90), 0.0, 1.0))
            feats["tcp_window_mean"] = n(64_000.0, 0.05)
            feats["ttl_variance"] = n(0.8, 0.15)
            feats["unique_dst_ips"] = n(2.0, 0.15)
            feats["unique_src_ports"] = n(15.0, 0.15)
            feats["dst_port_diversity"] = n(0.3, 0.15)
            feats["failed_connection_ratio"] = float(np.clip(rng.uniform(0.01, 0.03), 0.0, 1.0))
            feats["port_scan_indicator"] = float(np.clip(rng.uniform(0.01, 0.05), 0.0, 1.0))
            feats["internal_lateral_ratio"] = float(np.clip(rng.uniform(0.05, 0.15), 0.0, 1.0))

        raw_vec = np.array([feats[col] for col in FEATURE_COLUMNS], dtype=np.float32)
        scaled_vec = self.scaler.transform(raw_vec[np.newaxis, :])[0]

        return NetworkStateVector(
            timestamp=float(timestamp),
            window_id=int(window_id),
            features=scaled_vec.tolist(),
            feature_dict=feats,
            ground_truth_stage=stage,
            is_synthetic=True
        )

    def generate_scenario(self, scenario_name: str, total_windows: int = 40, start_time: float = 1700000000.0) -> List[NetworkStateVector]:
        """
        Generates a sequence of temporal network state windows according to a predefined kill-chain scenario.
        """
        states: List[NetworkStateVector] = []

        if scenario_name == "Normal Scenario":
            stages = ["Normal"] * total_windows

        elif scenario_name == "Recon -> Initial Access":
            # 12 Normal -> 14 Recon -> 14 Initial Access
            stages = (
                ["Normal"] * 12 +
                ["Reconnaissance"] * 14 +
                ["Initial Access"] * (total_windows - 26)
            )

        elif scenario_name == "Brute Force -> Initial Access":
            # 10 Normal -> 15 Initial Access (Brute Force) -> 15 Execution
            stages = (
                ["Normal"] * 10 +
                ["Initial Access"] * 15 +
                ["Execution"] * (total_windows - 25)
            )

        elif scenario_name == "Lateral Movement -> C2":
            # 8 Initial Access -> 16 Lateral Movement -> 16 C2
            stages = (
                ["Initial Access"] * 8 +
                ["Lateral Movement"] * 16 +
                ["Command and Control"] * (total_windows - 24)
            )

        elif scenario_name == "Full Multi-Stage Attack":
            # Complete multi-stage kill chain
            # Normal (6) -> Recon (6) -> Initial Access (6) -> Execution (5) -> PrivEsc (5) -> Lateral (6) -> C2 (6) -> Exfil (6)
            stages = (
                ["Normal"] * 6 +
                ["Reconnaissance"] * 6 +
                ["Initial Access"] * 6 +
                ["Execution"] * 5 +
                ["Privilege Escalation"] * 5 +
                ["Lateral Movement"] * 6 +
                ["Command and Control"] * 6 +
                ["Exfiltration"] * max(4, total_windows - 40)
            )
        else:
            stages = ["Normal"] * total_windows

        for i, stg in enumerate(stages[:total_windows]):
            ts = start_time + i * 10.0
            states.append(self.generate_state_for_stage(stg, i, ts))

        return states
