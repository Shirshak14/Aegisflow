"""
Live Traffic & Scenario Replay Streaming Engine for SIH26153.
Simulates real-time network state window ingestion and continuously triggers K-step forecasting.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
import numpy as np

from app.preprocessing.schema import NetworkStateVector, ATTACK_STAGES
from app.simulation.synthetic_traffic import SyntheticTrafficGenerator
from app.forecasting.k_step_forecaster import KStepAttackForecaster
from app.models.registry import model_registry
from app.explainability.explainer import SecurityExplainer
from app.explainability.reasoner import SocIncidentReasoner

class ReplayEngine:
    def __init__(self):
        self.generator = SyntheticTrafficGenerator()
        self.explainer = SecurityExplainer()
        self.is_running: bool = False
        self.is_paused: bool = False
        self.playback_speed: float = 1.0 # 1x = 1.5s per 10s window
        self.current_scenario_name: str = "Full Multi-Stage Attack"
        self.current_window_idx: int = 0
        self.scenario_states: List[NetworkStateVector] = []
        self.history_buffer: List[NetworkStateVector] = []
        self.latest_forecast: Dict[str, Any] = {}
        self.latest_traffic_metrics: Dict[str, Any] = {}
        self.latest_explanation: Dict[str, Any] = {}
        self._task: Optional[asyncio.Task] = None
        
        # Initialize default scenario
        self.load_scenario(self.current_scenario_name)

    def load_scenario(self, scenario_name: str, total_windows: int = 40):
        self.current_scenario_name = scenario_name
        self.scenario_states = self.generator.generate_scenario(scenario_name, total_windows=total_windows)
        self.current_window_idx = 0
        self.history_buffer = []
        
        # Pre-seed history with initial 10 windows so forecasting works immediately
        initial_seed = self.scenario_states[:10]
        self.history_buffer = list(initial_seed)
        self.current_window_idx = 10
        self._trigger_forecast()

    def load_custom_states(self, states: List[NetworkStateVector], dataset_name: str = "Custom Dataset"):
        self.current_scenario_name = dataset_name
        self.scenario_states = states
        self.current_window_idx = 0
        self.history_buffer = []
        if len(states) >= 10:
            self.history_buffer = list(states[:10])
            self.current_window_idx = 10
        else:
            self.history_buffer = list(states)
            self.current_window_idx = len(states)
        self._trigger_forecast()

    def _trigger_forecast(self):
        if not self.history_buffer:
            return

        active_model = model_registry.get_active_model()
        forecaster = KStepAttackForecaster(model=active_model, forecast_horizon_k=5, window_size_sec=10.0)
        
        # Run K-step forecasting rollout
        forecast_res = forecaster.forecast_trajectory(self.history_buffer)
        self.latest_forecast = forecast_res
        
        # Extract latest live traffic telemetry
        latest_st = self.history_buffer[-1]
        fd = latest_st.feature_dict
        self.latest_traffic_metrics = {
            "timestamp": latest_st.timestamp,
            "window_id": latest_st.window_id,
            "ground_truth_stage": latest_st.ground_truth_stage,
            "packet_rate_pps": round(fd.get("packet_rate_pps", 0.0), 1),
            "byte_rate_bps": round(fd.get("byte_rate_bps", 0.0), 1),
            "fwd_packets": int(fd.get("fwd_packets_total", 0)),
            "bwd_packets": int(fd.get("bwd_packets_total", 0)),
            "syn_ratio": round(fd.get("tcp_syn_ratio", 0.0), 3),
            "rst_ratio": round(fd.get("tcp_rst_ratio", 0.0), 3),
            "port_diversity": round(fd.get("dst_port_diversity", 0.0), 2),
            "failed_conn_ratio": round(fd.get("failed_connection_ratio", 0.0), 3),
            "internal_lateral_ratio": round(fd.get("internal_lateral_ratio", 0.0), 3),
            "is_synthetic": latest_st.is_synthetic
        }

        # Generate Explainability & SOC Reasoner output
        if forecast_res.get("trajectory"):
            first_step = forecast_res["trajectory"][0]
            narrative = SocIncidentReasoner.generate_narrative(latest_st.ground_truth_stage, first_step)
            
            history_arr = np.array([s.features for s in self.history_buffer], dtype=np.float32)
            attn_arr = np.array(forecast_res["attention_maps"][0]) if forecast_res.get("attention_maps") else None
            
            xai = self.explainer.explain_sample(
                history_arr,
                first_step["predicted_stage"],
                first_step["stage_probabilities"],
                attn_arr
            )
            self.latest_explanation = {
                **xai,
                "soc_narrative": narrative
            }

    def step(self):
        """Advances simulation by one temporal window."""
        if self.current_window_idx >= len(self.scenario_states):
            # Loop back or restart scenario
            self.current_window_idx = 0
            self.history_buffer = list(self.scenario_states[:10])
            self.current_window_idx = 10
        else:
            new_state = self.scenario_states[self.current_window_idx]
            self.history_buffer.append(new_state)
            if len(self.history_buffer) > 15:
                self.history_buffer.pop(0)
            self.current_window_idx += 1

        self._trigger_forecast()

    async def _run_loop(self):
        while self.is_running:
            if not self.is_paused:
                self.step()
            sleep_time = max(0.5, 1.5 / max(self.playback_speed, 0.1))
            await asyncio.sleep(sleep_time)

    def start(self, speed: float = 1.0):
        self.playback_speed = speed
        self.is_running = True
        self.is_paused = False
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run_loop())

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def stop(self):
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "playback_speed": self.playback_speed,
            "scenario_name": self.current_scenario_name,
            "current_window_idx": self.current_window_idx,
            "total_windows": len(self.scenario_states),
            "is_synthetic": True if "Scenario" in self.current_scenario_name or "Attack" in self.current_scenario_name or (self.history_buffer and self.history_buffer[-1].is_synthetic) else False,
            "active_model": model_registry.active_model_name
        }

replay_engine = ReplayEngine()
