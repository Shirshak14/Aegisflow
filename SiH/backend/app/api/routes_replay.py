"""
API Routes for Live Scenario Replay & Traffic Stream Controls.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.simulation.replay_engine import replay_engine

router = APIRouter(tags=["Replay & Simulation"])

AVAILABLE_SCENARIOS = [
    {
        "id": "full_attack",
        "name": "Full Multi-Stage Attack",
        "description": "Complete kill-chain progression: Normal -> Recon -> Initial Access -> Execution -> PrivEsc -> Lateral -> C2 -> Exfiltration."
    },
    {
        "id": "recon_access",
        "name": "Recon -> Initial Access",
        "description": "Port scanning and service enumeration escalating into credential exploitation."
    },
    {
        "id": "brute_force",
        "name": "Brute Force -> Initial Access",
        "description": "High-frequency authentication attempts transitioning into remote code execution."
    },
    {
        "id": "lateral_c2",
        "name": "Lateral Movement -> C2",
        "description": "Internal subnet pivoting and remote service exploitation establishing beaconing channels."
    },
    {
        "id": "normal_baseline",
        "name": "Normal Scenario",
        "description": "Clean enterprise traffic baseline with standard web and internal traffic."
    }
]

class ScenarioSelectRequest(BaseModel):
    scenario_name: str = Field(..., description="Name of the scenario to load")

class StartReplayRequest(BaseModel):
    speed: float = Field(1.0, ge=0.2, le=5.0, description="Playback multiplier (1x = ~1.5s per window)")

@router.get("/scenarios")
def get_scenarios():
    """Returns list of all available attack simulation scenarios."""
    return {"scenarios": AVAILABLE_SCENARIOS}

@router.get("/replay/status")
def get_replay_status():
    """Returns current playback state, window index, and active scenario info."""
    return replay_engine.get_status()

@router.post("/replay/start")
def start_replay(req: StartReplayRequest = StartReplayRequest()):
    """Starts continuous background scenario streaming."""
    replay_engine.start(speed=req.speed)
    return {"status": "started", "playback_speed": req.speed}

@router.post("/replay/pause")
def pause_replay():
    """Pauses traffic replay."""
    replay_engine.pause()
    return {"status": "paused"}

@router.post("/replay/resume")
def resume_replay():
    """Resumes traffic replay."""
    replay_engine.resume()
    return {"status": "resumed"}

@router.post("/replay/stop")
def stop_replay():
    """Stops streaming and cancels background task."""
    replay_engine.stop()
    return {"status": "stopped"}

@router.post("/replay/step")
def step_replay():
    """Manually steps forward by 1 temporal window (10 seconds of traffic)."""
    replay_engine.step()
    return {
        "status": "stepped",
        "current_window": replay_engine.current_window_idx,
        "latest_stage": replay_engine.history_buffer[-1].ground_truth_stage if replay_engine.history_buffer else "Normal"
    }

@router.post("/replay/scenario")
def select_scenario(req: ScenarioSelectRequest):
    """Loads and resets the simulation to a specific attack scenario."""
    matched = next((s["name"] for s in AVAILABLE_SCENARIOS if s["name"].lower() == req.scenario_name.lower() or s["id"] == req.scenario_name.lower()), None)
    if not matched:
        raise HTTPException(status_code=400, detail=f"Scenario '{req.scenario_name}' not recognized.")
    
    replay_engine.load_scenario(matched)
    return {
        "status": "loaded",
        "scenario_name": matched,
        "total_windows": len(replay_engine.scenario_states)
    }
