"""
API Routes for Dataset Management, Uploads, and Preprocessing.
"""

from pathlib import Path
import io
import time
from typing import Dict, Any, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import pandas as pd
import numpy as np

from app.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, settings
from app.preprocessing.adapters import DatasetAdapter
from app.preprocessing.windowing import TemporalWindowAggregator
from app.storage.db import save_dataset_meta, list_datasets
from app.simulation.replay_engine import replay_engine

router = APIRouter(tags=["Datasets & Preprocessing"])

SUPPORTED_DATASETS_INFO = [
    {
        "name": "CIC-IDS2018 (Primary)",
        "description": "Comprehensive Canadian Institute for Cybersecurity intrusion dataset featuring DoS, Brute Force, Web Attacks, Infiltration, and Botnets.",
        "recommended_file": "Friday-02-03-2018_TrafficForML_CICFlowMeter.csv",
        "status": "Adapter Ready"
    },
    {
        "name": "CTU-13 (Validation)",
        "description": "Capture of genuine Botnet traffic mixed with normal enterprise background and scan activities.",
        "recommended_file": "capture20110810.binetflow",
        "status": "Adapter Ready"
    },
    {
        "name": "UNSW-NB15 (Independent Testing)",
        "description": "Network traffic dataset created by the Australian Centre for Cyber Security containing modern synthesized normal and attack activities.",
        "recommended_file": "UNSW-NB15_1.csv",
        "status": "Adapter Ready"
    },
    {
        "name": "PCAP Network Capture",
        "description": "Raw Wireshark/tcpdump .pcap / .pcapng captures parsed via Scapy.",
        "recommended_file": "*.pcap",
        "status": "Scapy Parser Ready"
    }
]

@router.get("/datasets/supported")
def get_supported_datasets():
    """Returns documentation and format guidelines for benchmark datasets."""
    return {"supported_datasets": SUPPORTED_DATASETS_INFO}

@router.get("/datasets")
def get_all_datasets():
    """Lists all uploaded datasets and their preprocessing status."""
    db_list = list_datasets()
    return {"datasets": db_list}

@router.post("/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_type: str = Form("AUTO")
):
    """
    Uploads and validates a CSV, Parquet, or PCAP file.
    Runs adapter normalization and temporal windowing.
    """
    # Validate extension
    filename = file.filename or "uploaded_dataset"
    ext = Path(filename).suffix.lower()
    if ext not in [".csv", ".parquet", ".pcap", ".pcapng", ".binetflow"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload CSV, Parquet, or PCAP.")

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.")

    saved_path = RAW_DATA_DIR / f"{int(time.time())}_{filename}"
    with open(saved_path, "wb") as f:
        f.write(contents)

    # Process file
    try:
        if ext in [".pcap", ".pcapng"]:
            df = DatasetAdapter.parse_pcap(saved_path)
            detected_type = "PCAP"
        elif ext == ".parquet":
            df = pd.read_parquet(saved_path)
            detected_type = DatasetAdapter.identify_format(df)
            df = DatasetAdapter.adapt(df, dataset_type if dataset_type != "AUTO" else detected_type)
        else:
            # CSV / Binetflow
            df = pd.read_csv(io.BytesIO(contents), nrows=10000) # Process first 10,000 rows for responsive preview
            detected_type = DatasetAdapter.identify_format(df)
            df = DatasetAdapter.adapt(df, dataset_type if dataset_type != "AUTO" else detected_type)

        if df.empty:
            raise HTTPException(status_code=400, detail="Unable to extract valid flow records from file.")

        # Aggregate into temporal windows
        aggregator = TemporalWindowAggregator(window_size_sec=10.0)
        states = aggregator.aggregate_flows_to_states(df)

        normal_count = sum(1 for s in states if s.ground_truth_stage == "Normal")
        attack_count = len(states) - normal_count
        normal_ratio = float(normal_count / max(len(states), 1))
        attack_ratio = float(attack_count / max(len(states), 1))

        # Save to database
        row_id = save_dataset_meta(
            name=filename,
            file_path=str(saved_path),
            file_type=detected_type,
            num_records=len(df),
            num_windows=len(states),
            normal_ratio=round(normal_ratio, 3),
            attack_ratio=round(attack_ratio, 3)
        )

        return {
            "status": "success",
            "dataset_id": row_id,
            "filename": filename,
            "detected_format": detected_type,
            "flow_records_parsed": len(df),
            "temporal_windows_created": len(states),
            "distribution": {
                "normal_windows": normal_count,
                "attack_windows": attack_count,
                "attack_ratio": round(attack_ratio, 3)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process dataset: {str(e)}")

@router.post("/datasets/{dataset_id}/load-replay")
def load_dataset_for_replay(dataset_id: int):
    """Loads a previously uploaded dataset into the live replay engine."""
    datasets = list_datasets()
    match = next((d for d in datasets if d["id"] == dataset_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Dataset ID not found.")

    file_path = Path(match["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Underlying dataset file no longer exists.")

    df = pd.read_csv(file_path, nrows=5000)
    adapted_df = DatasetAdapter.adapt(df, match["file_type"])
    aggregator = TemporalWindowAggregator(window_size_sec=10.0)
    states = aggregator.aggregate_flows_to_states(adapted_df)

    replay_engine.load_custom_states(states, dataset_name=match["name"])
    return {
        "status": "loaded",
        "dataset_name": match["name"],
        "windows_loaded": len(states)
    }
