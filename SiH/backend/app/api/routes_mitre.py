"""
API Routes for MITRE ATT&CK Matrix Navigation & Technique Playbooks.
"""

from fastapi import APIRouter, HTTPException
from app.mitre.mitre_service import mitre_service

router = APIRouter(tags=["MITRE ATT&CK"])

@router.get("/mitre")
def get_mitre_matrix():
    """Returns the full MITRE ATT&CK framework mapping for all supported attack stages."""
    matrix = mitre_service.get_full_matrix()
    return {
        "status": "success",
        "total_stages": len(matrix),
        "matrix": matrix
    }

@router.get("/mitre/{stage_name}")
def get_mitre_for_stage(stage_name: str):
    """Returns specific MITRE Tactic, Technique IDs, and SOC remediation playbook for a stage."""
    info = mitre_service.get_mapping_for_stage(stage_name)
    return {
        "stage": stage_name,
        **info
    }
