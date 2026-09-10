"""
Natural Language SOC Incident Reasoner.
Transforms model feature deviations and attack stages into clear, actionable SOC incident summaries.
"""

from typing import Dict, Any, List
from app.preprocessing.schema import FEATURE_DESCRIPTIONS

class SocIncidentReasoner:
    """
    Synthesizes model forecasts and feature attributions into natural language analyst briefings.
    """

    @staticmethod
    def generate_narrative(
        current_stage: str,
        forecast_step: Dict[str, Any]
    ) -> Dict[str, Any]:
        target_stage = forecast_step["predicted_stage"]
        confidence = int(forecast_step["stage_probability"] * 100)
        time_h = forecast_step["time_horizon"]
        top_feats = forecast_step.get("top_features", [])
        mitre = forecast_step.get("mitre", {})

        reasons = []
        for feat in top_feats[:4]:
            name = feat.get("description", feat.get("feature", ""))
            val = feat.get("value", 0.0)
            delta = feat.get("delta", 0.0)
            direction = "surged by" if delta > 0.05 else ("dropped by" if delta < -0.05 else "elevated at")
            reasons.append(f"{name} {direction} {abs(delta):.2f} (current index: {val:.2f})")

        if target_stage == "Normal":
            headline = "Nominal Network State Expected"
            summary = "Telemetry patterns indicate steady enterprise operations with no anomalous protocol or port sweeps."
        else:
            headline = f"Potential Escalation to {target_stage} ({time_h}, {confidence}% probability)"
            summary = (
                f"Transitioning from {current_stage} to {target_stage} based on temporal behavioral evolution. "
                f"Primary indicators: " + "; ".join(reasons) + "."
            )

        return {
            "headline": headline,
            "summary": summary,
            "indicators": reasons,
            "mitre_technique": f"{mitre.get('technique_id', 'T0000')} - {mitre.get('technique_name', '')}",
            "recommended_action": mitre.get("soc_playbook", "Verify host telemetry and monitor egress traffic.")
        }
