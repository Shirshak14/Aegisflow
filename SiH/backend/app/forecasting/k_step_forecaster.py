"""
K-Step Autoregressive Network Attack Forecaster.
Core USP: Models the temporal evolution of network states and predicts K steps into the future.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from app.models.base import BaseForecaster
from app.preprocessing.schema import (
    FEATURE_COLUMNS,
    FEATURE_DESCRIPTIONS,
    ATTACK_STAGES,
    STAGE_SEVERITY,
    NetworkStateVector
)
from app.mitre.mitre_service import mitre_service

class KStepAttackForecaster:
    """
    Executes K-Step autoregressive future state rollouts and attack stage forecasting.
    """

    def __init__(self, model: BaseForecaster, forecast_horizon_k: int = 5, window_size_sec: float = 10.0):
        self.model = model
        self.forecast_horizon_k = forecast_horizon_k
        self.window_size_sec = window_size_sec

    def _determine_risk_level(self, risk_score: float) -> str:
        if risk_score >= 0.75:
            return "CRITICAL"
        elif risk_score >= 0.50:
            return "HIGH"
        elif risk_score >= 0.25:
            return "MEDIUM"
        return "LOW"

    def _extract_top_contributing_features(
        self,
        current_state: np.ndarray,
        next_state: np.ndarray,
        predicted_stage: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Computes feature deviations and domain sensitivity weights to identify the top driving signals.
        """
        # Baseline normal weights for typical deviations
        stage_relevance = {
            "Reconnaissance": {"dst_port_diversity": 3.0, "port_scan_indicator": 3.5, "tcp_syn_ratio": 2.5, "failed_connection_ratio": 2.0, "unique_dst_ips": 2.0},
            "Initial Access": {"failed_connection_ratio": 3.0, "tcp_rst_ratio": 2.5, "tcp_psh_ratio": 2.0, "packet_rate_pps": 1.5, "unique_src_ports": 2.0},
            "Execution": {"tcp_psh_ratio": 3.0, "fwd_bytes_total": 2.5, "packet_size_mean": 2.0, "byte_rate_bps": 2.0},
            "Persistence": {"tcp_psh_ratio": 2.0, "flow_iat_mean": 2.0, "internal_lateral_ratio": 2.0},
            "Privilege Escalation": {"internal_lateral_ratio": 3.0, "tcp_syn_ratio": 2.0, "failed_connection_ratio": 2.0},
            "Lateral Movement": {"internal_lateral_ratio": 4.0, "unique_dst_ips": 3.0, "dst_port_diversity": 2.5, "fwd_packets_total": 2.0},
            "Command and Control": {"flow_iat_std": -3.0, "tcp_psh_ratio": 3.0, "unique_dst_ips": -2.0, "flow_duration_sec": 2.0},
            "Exfiltration": {"fwd_bytes_total": 4.0, "fwd_bwd_packet_ratio": 3.5, "byte_rate_bps": 3.5, "packet_size_mean": 2.5},
            "Normal": {}
        }
        rel = stage_relevance.get(predicted_stage, {})
        
        feature_scores = []
        for i, col in enumerate(FEATURE_COLUMNS):
            val = float(next_state[i])
            delta = float(next_state[i] - current_state[i])
            mult = rel.get(col, 1.0)
            
            # Score based on value intensity + delta + domain relevance
            impact = (abs(val) * 0.5 + abs(delta) * 0.5) * abs(mult)
            direction = "INCREASING" if delta > 0.01 else ("DECREASING" if delta < -0.01 else "STABLE")
            
            feature_scores.append({
                "feature": col,
                "description": FEATURE_DESCRIPTIONS.get(col, col),
                "value": round(val, 4),
                "delta": round(delta, 4),
                "impact_score": round(float(impact), 4),
                "direction": direction
            })

        feature_scores.sort(key=lambda x: x["impact_score"], reverse=True)
        return feature_scores[:top_k]

    def forecast_trajectory(
        self,
        history_states: List[NetworkStateVector],
        horizon_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes K-Step Autoregressive forecasting rollout from a list of historical states.
        """
        k_steps = horizon_k or self.forecast_horizon_k
        if not history_states:
            return {"error": "Empty history provided", "trajectory": []}

        # Extract features array [N, feat_dim]
        feat_history = np.array([s.features for s in history_states], dtype=np.float32)
        rolling_seq = feat_history.copy() # Rolling buffer
        
        last_state = history_states[-1]
        current_stage = last_state.ground_truth_stage
        current_time = last_state.timestamp

        forecast_steps: List[Dict[str, Any]] = []
        all_attentions: List[List[float]] = []

        curr_input_state = rolling_seq[-1]

        for step in range(1, k_steps + 1):
            # 1. Model inference on rolling history
            pred_state, stage_probs, risk_score, attn_weights = self.model.predict_next(rolling_seq)
            
            # 2. Extract predicted stage
            stage_idx = int(np.argmax(stage_probs))
            predicted_stage_name = ATTACK_STAGES.get(stage_idx, "Normal")
            stage_prob = float(stage_probs[stage_idx])
            
            # 3. Top contributing features for this step
            top_feats = self._extract_top_contributing_features(
                curr_input_state, pred_state, predicted_stage_name, top_k=5
            )
            
            # 4. MITRE ATT&CK Mapping
            mitre_info = mitre_service.get_mapping_for_stage(predicted_stage_name)
            
            step_horizon_sec = int(step * self.window_size_sec)
            step_record = {
                "step": step,
                "time_horizon": f"+{step_horizon_sec}s",
                "time_horizon_sec": step_horizon_sec,
                "predicted_timestamp": current_time + step_horizon_sec,
                "predicted_stage": predicted_stage_name,
                "stage_id": stage_idx,
                "stage_probability": round(stage_prob, 4),
                "stage_probabilities": {
                    ATTACK_STAGES[i]: round(float(p), 4) for i, p in enumerate(stage_probs)
                },
                "risk_score": round(risk_score, 4),
                "risk_level": self._determine_risk_level(risk_score),
                "predicted_state_vector": [round(float(v), 4) for v in pred_state],
                "top_features": top_feats,
                "mitre": {
                    "tactic_id": mitre_info["tactic_id"],
                    "tactic_name": mitre_info["tactic_name"],
                    "technique_id": mitre_info["primary_technique_id"],
                    "technique_name": mitre_info["primary_technique_name"],
                    "severity": mitre_info["severity"],
                    "soc_playbook": mitre_info["soc_playbook"]
                }
            }
            forecast_steps.append(step_record)
            
            if attn_weights is not None:
                all_attentions.append([round(float(w), 4) for w in attn_weights])

            # 5. Autoregressively roll the predicted state back into history buffer
            curr_input_state = pred_state
            rolling_seq = np.vstack([rolling_seq[1:], pred_state[np.newaxis, :]])

        # Global trajectory insights
        max_risk_step = max(forecast_steps, key=lambda x: x["risk_score"])
        escalation = (forecast_steps[-1]["risk_score"] > forecast_steps[0]["risk_score"] + 0.15)

        return {
            "current_window_id": last_state.window_id,
            "current_timestamp": current_time,
            "current_stage": current_stage,
            "forecast_horizon_k": k_steps,
            "is_synthetic": last_state.is_synthetic,
            "escalation_detected": escalation,
            "peak_risk_step": max_risk_step["step"],
            "peak_risk_stage": max_risk_step["predicted_stage"],
            "peak_risk_score": max_risk_step["risk_score"],
            "trajectory": forecast_steps,
            "attention_maps": all_attentions
        }
