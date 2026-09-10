import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DEMO_DATA_DIR = DATA_DIR / "demo"
MODELS_DIR = BASE_DIR / "models"
STORAGE_DIR = BASE_DIR / "backend" / "app" / "storage"

for d in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, DEMO_DATA_DIR, MODELS_DIR, STORAGE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    PROJECT_NAME: str = "AegisFlow SIH26153 - Network Attack Forecasting"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Temporal State & Forecasting Settings
    WINDOW_SIZE_SEC: float = 10.0
    SEQUENCE_LENGTH: int = 10       # History N=10 windows (100 seconds history)
    FORECAST_HORIZON_K: int = 5     # K-step forecast (50 seconds into future)
    FEATURE_DIM: int = 24           # 24 core network state features
    NUM_CLASSES: int = 9            # 9 MITRE-aligned attack stages
    
    # Model Hyperparameters
    HIDDEN_DIM: int = 128
    NUM_HEADS: int = 4
    NUM_LAYERS: int = 2
    DROPOUT: float = 0.1
    LEARNING_RATE: float = 0.001
    BATCH_SIZE: int = 32
    EPOCHS: int = 25
    
    # Security & Storage
    MAX_UPLOAD_SIZE_MB: int = 100
    DATABASE_URL: str = f"sqlite:///{STORAGE_DIR / 'sih_storage.db'}"
    DB_PATH: Path = STORAGE_DIR / "sih_storage.db"

settings = Settings()
