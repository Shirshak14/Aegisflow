"""
Unit Tests for Synthetic Traffic Generator and Kill-Chain Scenarios.
"""

import pytest
from app.simulation.synthetic_traffic import SyntheticTrafficGenerator
from app.preprocessing.schema import ATTACK_STAGES

def test_synthetic_scenario_generation():
    generator = SyntheticTrafficGenerator()
    scenarios = [
        "Normal Scenario",
        "Recon -> Initial Access",
        "Brute Force -> Initial Access",
        "Lateral Movement -> C2",
        "Full Multi-Stage Attack"
    ]
    for sc in scenarios:
        states = generator.generate_scenario(sc, total_windows=40)
        assert len(states) == 40
        assert all(len(s.features) == 24 for s in states)
        assert all(s.is_synthetic is True for s in states)
        assert states[0].ground_truth_stage in ATTACK_STAGES.values()

def test_full_attack_kill_chain_progression():
    generator = SyntheticTrafficGenerator()
    states = generator.generate_scenario("Full Multi-Stage Attack", total_windows=45)
    stages = [s.ground_truth_stage for s in states]
    
    # Verify stages sequence includes scanning, access, and exfiltration
    assert "Normal" in stages
    assert "Reconnaissance" in stages
    assert "Initial Access" in stages
    assert "Lateral Movement" in stages
    assert "Exfiltration" in stages
