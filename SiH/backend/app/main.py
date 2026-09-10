"""
Main FastAPI Application Entrypoint for SIH26153.
AegisFlow: AI-Based Network Attack Forecasting & Trajectory Modeling.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.routes_forecast import router as forecast_router
from app.api.routes_replay import router as replay_router
from app.api.routes_models import router as models_router
from app.api.routes_datasets import router as datasets_router
from app.api.routes_explain import router as explain_router
from app.api.routes_mitre import router as mitre_router
from app.simulation.replay_engine import replay_engine

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## SIH26153: AI based Network Attack Forecasting from Network Traffic Data
    
    **Core USP**: *Not just detecting the attack — modelling its trajectory.*
    
    ### Key Features:
    - **Temporal Network States**: Dense 24-dimensional behavioral network representations.
    - **Multi-Head Temporal Transformer**: Autoregressively forecasts future state transitions, MITRE attack stages, and risk scores.
    - **Empirical Baseline Comparison**: Multi-class Logistic Regression vs LSTM vs Temporal Transformer.
    - **Explainable AI (XAI)**: Transformer Attention Heatmaps + SHAP Feature Attribution + Natural Language SOC Incident summaries.
    - **MITRE ATT&CK Matrix**: Direct mapping to Tactics, Techniques, and SOC containment playbooks.
    - **High-Fidelity Demo Simulation**: Pre-configured multi-stage cyber kill-chain scenarios.
    """
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(forecast_router, prefix=settings.API_V1_STR)
app.include_router(replay_router, prefix=settings.API_V1_STR)
app.include_router(models_router, prefix=settings.API_V1_STR)
app.include_router(datasets_router, prefix=settings.API_V1_STR)
app.include_router(explain_router, prefix=settings.API_V1_STR)
app.include_router(mitre_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "mode": "Demonstration / Offline Capable",
        "simulation_status": replay_engine.get_status()
    }

@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs_url": "/docs",
        "health_url": "/health",
        "api_v1": settings.API_V1_STR
    }

@app.on_event("startup")
async def on_startup():
    # Pre-seed initial forecast on server launch
    try:
        replay_engine._trigger_forecast()
    except Exception as e:
        print(f"Initial forecast setup warning: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    replay_engine.stop()
