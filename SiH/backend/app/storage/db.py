"""
SQLite Database Storage Layer for SIH26153 Prototype.
Stores metadata, dataset uploads, training runs, and audit logs.
"""

import sqlite3
import json
import time
from typing import Dict, Any, List, Optional
from app.config import settings

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Datasets metadata table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datasets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        num_records INTEGER DEFAULT 0,
        num_windows INTEGER DEFAULT 0,
        normal_ratio REAL DEFAULT 1.0,
        attack_ratio REAL DEFAULT 0.0,
        created_at REAL NOT NULL
    );
    """)

    # Model training runs & evaluation metrics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS training_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_name TEXT NOT NULL,
        dataset_name TEXT NOT NULL,
        samples_count INTEGER NOT NULL,
        metrics_json TEXT NOT NULL,
        created_at REAL NOT NULL
    );
    """)

    # Forecast audit logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS forecast_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp REAL NOT NULL,
        window_id INTEGER NOT NULL,
        model_name TEXT NOT NULL,
        current_stage TEXT NOT NULL,
        forecast_1_stage TEXT NOT NULL,
        forecast_1_prob REAL NOT NULL,
        forecast_k_stage TEXT NOT NULL,
        forecast_k_prob REAL NOT NULL,
        peak_risk REAL NOT NULL,
        payload_json TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()

def save_dataset_meta(name: str, file_path: str, file_type: str, num_records: int, num_windows: int, normal_ratio: float, attack_ratio: float) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO datasets (name, file_path, file_type, num_records, num_windows, normal_ratio, attack_ratio, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, file_path, file_type, num_records, num_windows, normal_ratio, attack_ratio, time.time()))
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id

def list_datasets() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasets ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_training_run(run_name: str, dataset_name: str, samples_count: int, metrics: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO training_runs (run_name, dataset_name, samples_count, metrics_json, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (run_name, dataset_name, samples_count, json.dumps(metrics), time.time()))
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id

# Initialize DB tables on import
init_db()
