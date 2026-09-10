"""
API Routes for Model Management, Training, and Empirical Benchmarking.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.models.registry import model_registry
from app.simulation.synthetic_traffic import SyntheticTrafficGenerator
from app.preprocessing.windowing import create_sequences_from_states
from app.config import settings

router = APIRouter(tags=["Models & Training"])

class ModelSelectRequest(BaseModel):
    model_name: str = Field(..., description="Name of model to activate ('Logistic Regression', 'LSTM', or 'Temporal Transformer')")

class TrainRequest(BaseModel):
    epochs: int = Field(15, ge=2, le=50, description="Training epochs for PyTorch models")
    batch_size: int = Field(32, ge=8, le=128)
    dataset_source: str = Field("synthetic_all", description="'synthetic_all' or uploaded dataset name")

@router.get("/models")
def get_models():
    """Returns all available models, active selection, and architecture configurations."""
    return {
        "active_model": model_registry.active_model_name,
        "available_models": list(model_registry.models.keys()),
        "hyperparameters": {
            "sequence_length": settings.SEQUENCE_LENGTH,
            "forecast_horizon_k": settings.FORECAST_HORIZON_K,
            "hidden_dimension": settings.HIDDEN_DIM,
            "num_heads": settings.NUM_HEADS,
            "num_layers": settings.NUM_LAYERS,
            "dropout": settings.DROPOUT
        }
    }

@router.post("/models/select")
def select_active_model(req: ModelSelectRequest):
    """Sets the active forecasting model."""
    success = model_registry.set_active_model(req.model_name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Model '{req.model_name}' is not registered.")
    return {"status": "success", "active_model": model_registry.active_model_name}

def _run_training_job(epochs: int, batch_size: int):
    generator = SyntheticTrafficGenerator()
    # Generate balanced scenarios for comprehensive multi-stage training
    scenarios = ["Normal Scenario", "Recon -> Initial Access", "Brute Force -> Initial Access", "Lateral Movement -> C2", "Full Multi-Stage Attack"]
    all_states = []
    for sc in scenarios:
        states = generator.generate_scenario(sc, total_windows=50)
        all_states.extend(states)

    X_seq, Y_states, Y_stages, Y_risks = create_sequences_from_states(
        all_states,
        sequence_length=settings.SEQUENCE_LENGTH,
        forecast_horizon_k=settings.FORECAST_HORIZON_K
    )
    
    model_registry.train_all(X_seq, Y_states, Y_stages, Y_risks, epochs=epochs, batch_size=batch_size)

@router.post("/train")
def train_models(req: TrainRequest, background_tasks: BackgroundTasks):
    """
    Triggers time-aware multi-model training and empirical benchmarking in the background.
    """
    if model_registry.training_status.get("status") == "running":
        return {"status": "already_running", "message": "A training process is already active."}

    background_tasks.add_task(_run_training_job, req.epochs, req.batch_size)
    return {
        "status": "started",
        "message": "Model training and benchmarking initiated in background.",
        "parameters": req.dict()
    }

@router.get("/training-status")
def get_training_status():
    """Returns the current training progress and status message."""
    return model_registry.training_status

@router.get("/metrics")
def get_model_metrics():
    """
    Returns empirical evaluation metrics comparing Logistic Regression, LSTM, and Temporal Transformer.
    """
    if not model_registry.metrics:
        # Precompute initial default benchmarks if not yet trained
        _run_training_job(epochs=8, batch_size=32)

    return {
        "status": "success",
        "active_model": model_registry.active_model_name,
        "metrics": model_registry.metrics
    }
