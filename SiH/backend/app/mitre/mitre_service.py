"""
MITRE ATT&CK Mapping Service.
Provides lookup for MITRE tactics, techniques, severity, and SOC playbooks.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from app.preprocessing.schema import ATTACK_STAGES

MAPPING_FILE = Path(__file__).resolve().parent / "mitre_mapping.json"

class MitreService:
    def __init__(self, mapping_path: Path = MAPPING_FILE):
        self.mapping_path = mapping_path
        self.mappings: Dict[str, Any] = {}
        self.load_mappings()

    def load_mappings(self):
        if self.mapping_path.exists():
            with open(self.mapping_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.mappings = data.get("mappings", {})
        else:
            self.mappings = {}

    def get_mapping_for_stage(self, stage: str) -> Dict[str, Any]:
        """Returns MITRE mapping dictionary for a given attack stage."""
        if stage in self.mappings:
            return self.mappings[stage]
        # Fallback for unknown
        return {
            "tactic_id": "TA0000",
            "tactic_name": stage,
            "primary_technique_id": "T0000",
            "primary_technique_name": f"{stage} Activity",
            "description": "Unclassified or custom attack pattern.",
            "soc_playbook": "Analyze packet headers and isolate source endpoints.",
            "severity": "Medium",
            "techniques": []
        }

    def get_full_matrix(self) -> List[Dict[str, Any]]:
        """Returns all MITRE stages and tactics in an ordered list for the SOC Matrix UI."""
        matrix = []
        for stage_id, stage_name in sorted(ATTACK_STAGES.items()):
            info = self.get_mapping_for_stage(stage_name)
            matrix.append({
                "stage_id": stage_id,
                "stage_name": stage_name,
                **info
            })
        return matrix

mitre_service = MitreService()
