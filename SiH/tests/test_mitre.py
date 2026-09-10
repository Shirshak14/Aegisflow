"""
Unit Tests for MITRE ATT&CK Mapping Service.
"""

import pytest
from app.mitre.mitre_service import mitre_service

def test_mitre_service_mappings():
    matrix = mitre_service.get_full_matrix()
    assert len(matrix) == 9
    
    recon = mitre_service.get_mapping_for_stage("Reconnaissance")
    assert recon["tactic_id"] == "TA0043"
    assert recon["primary_technique_id"] == "T1046"
    assert "soc_playbook" in recon

    lateral = mitre_service.get_mapping_for_stage("Lateral Movement")
    assert lateral["tactic_id"] == "TA0008"
    assert lateral["primary_technique_id"] == "T1021"

    c2 = mitre_service.get_mapping_for_stage("Command and Control")
    assert c2["tactic_id"] == "TA0011"
    assert c2["primary_technique_id"] == "T1071"
