"""
API Routes for Explainable AI (XAI) and Temporal Attention Extraction.
"""

from fastapi import APIRouter
from app.simulation.replay_engine import replay_engine

router = APIRouter(tags=["Explainability & XAI"])

@router.get("/explanations")
def get_current_explanations():
    """
    Returns SHAP feature attribution scores, temporal attention weights,
    and natural language root-cause reasoning for the current forecasting state.
    """
    if not replay_engine.latest_explanation:
        replay_engine._trigger_forecast()

    return {
        "status": "success",
        "explanation": replay_engine.latest_explanation
    }
