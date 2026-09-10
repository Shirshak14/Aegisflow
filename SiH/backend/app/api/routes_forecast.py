"""
API Routes for Network Attack Forecasting & Trajectory Rollouts.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.preprocessing.schema import NetworkStateVector
from app.simulation.replay_engine import replay_engine
from app.forecasting.k_step_forecaster import KStepAttackForecaster
from app.models.registry import model_registry

router = APIRouter(tags=["Forecasting"])

class ForecastRequest(BaseModel):
    history_states: Optional[List[NetworkStateVector]] = None
    horizon_k: Optional[int] = Field(5, ge=1, le=10, description="K-step future forecast horizon")

@router.get("/forecast/latest")
def get_latest_forecast():
    """
    Returns the most recent real-time K-step forecast trajectory,
    threat metrics, current stage, and escalation indicators.
    """
    if not replay_engine.latest_forecast:
        replay_engine._trigger_forecast()
    
    return {
        "status": "success",
        "replay_status": replay_engine.get_status(),
        "traffic_telemetry": replay_engine.latest_traffic_metrics,
        "forecast": replay_engine.latest_forecast,
        "explanation": replay_engine.latest_explanation
    }

@router.post("/forecast")
def post_forecast(req: ForecastRequest):
    """
    Executes a custom K-Step autoregressive forecasting rollout from provided historical windows.
    If no history is provided, utilizes the current live replay buffer.
    """
    history = req.history_states if req.history_states else replay_engine.history_buffer
    if not history:
        raise HTTPException(status_code=400, detail="No historical network states available for forecasting.")
    
    active_model = model_registry.get_active_model()
    forecaster = KStepAttackForecaster(
        model=active_model,
        forecast_horizon_k=req.horizon_k or 5,
        window_size_sec=10.0
    )
    result = forecaster.forecast_trajectory(history, horizon_k=req.horizon_k)
    return {
        "status": "success",
        "model_used": model_registry.active_model_name,
        "forecast": result
    }
