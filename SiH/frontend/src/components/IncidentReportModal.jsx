import React from 'react';
import { X, FileDown, ShieldAlert, CheckCircle, Printer, Terminal } from 'lucide-react';

export default function IncidentReportModal({
  isOpen,
  onClose,
  forecastData,
  telemetry,
  explanation,
  replayStatus,
  activeModel
}) {
  if (!isOpen) return null;

  const trajectory = forecastData?.trajectory || [];
  const currentStage = telemetry?.ground_truth_stage || 'Normal';
  const predictedStage = trajectory[0]?.predicted_stage || 'Normal';
  const maxRisk = trajectory.reduce((max, s) => Math.max(max, s.risk_score || 0), 0);
  const timestamp = new Date().toISOString();

  const handleDownloadJSON = () => {
    const reportData = {
      incident_id: `INC-SIH26153-${Date.now()}`,
      generated_at: timestamp,
      system: 'AegisFlow AI Network Attack Forecasting',
      status: 'ACTIVE_FORECAST_INCIDENT',
      active_model: activeModel,
      scenario: replayStatus?.scenario_name,
      current_window_id: telemetry?.window_id,
      threat_assessment: {
        observed_stage: currentStage,
        forecasted_stage_plus_10s: predictedStage,
        max_horizon_risk_index: maxRisk,
        is_critical_escalation: maxRisk >= 0.75
      },
      telemetry_snapshot: telemetry,
      trajectory_forecast: trajectory,
      explainability: explanation
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `AegisFlow_SOC_Report_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '850px' }}>
        <div className="card-header" style={{ position: 'sticky', top: 0, zIndex: 10, background: 'var(--bg-secondary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ShieldAlert size={20} color="var(--accent-cyan)" />
            <h2 className="font-display" style={{ fontSize: '1.1rem', color: 'var(--text-primary)', letterSpacing: '0.05em' }}>
              SOC Executive Threat Trajectory Briefing
            </h2>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button className="btn btn-outline" onClick={handlePrint} style={{ padding: '6px 12px', fontSize: '0.75rem' }}>
              <Printer size={14} /> Print
            </button>
            <button className="btn btn-primary" onClick={handleDownloadJSON} style={{ padding: '6px 12px', fontSize: '0.75rem' }}>
              <FileDown size={14} /> Export JSON
            </button>
            <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px' }}>
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', color: 'var(--text-primary)' }}>
          {/* Header Metadata */}
          <div style={{ background: 'rgba(236, 227, 209, 0.6)', border: '1px solid var(--border-card)', borderRadius: 'var(--radius-md)', padding: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px', fontSize: '0.8rem' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Report ID: </span>
                <span className="font-mono" style={{ color: 'var(--accent-cyan)' }}>INC-AETHER-{Date.now().toString().slice(-6)}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Timestamp (UTC): </span>
                <span className="font-mono">{timestamp}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Threat Classification: </span>
                <strong style={{ color: maxRisk >= 0.7 ? 'var(--accent-danger)' : 'var(--accent-amber)' }}>
                  {maxRisk >= 0.7 ? 'HIGH PRIORITY ESCALATION' : 'ELEVATED MONITORING'}
                </strong>
              </div>
            </div>
          </div>

          {/* Key Findings */}
          <div>
            <h4 className="font-display" style={{ fontSize: '0.9rem', color: 'var(--accent-cyan)', marginBottom: '8px' }}>
              1. Executive Threat Trajectory Summary
            </h4>
            <p style={{ fontSize: '0.85rem', lineHeight: '1.6', background: 'rgba(236, 227, 209, 0.5)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
              {explanation?.soc_narrative?.incident_summary || explanation?.summary_text || 'Active telemetry monitored within acceptable baseline thresholds.'}
            </p>
          </div>

          {/* Trajectory Table */}
          <div>
            <h4 className="font-display" style={{ fontSize: '0.9rem', color: 'var(--accent-purple)', marginBottom: '8px' }}>
              2. Autoregressive K-Step Projection Table (+10s to +50s)
            </h4>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                <thead>
                  <tr style={{ background: 'rgba(236, 227, 209, 0.6)', borderBottom: '1px solid var(--border-card)' }}>
                    <th style={{ padding: '8px 12px', textAlign: 'left' }}>Step / Horizon</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left' }}>Predicted Stage</th>
                    <th style={{ padding: '8px 12px', textAlign: 'center' }}>Confidence</th>
                    <th style={{ padding: '8px 12px', textAlign: 'center' }}>Risk Score</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left' }}>MITRE Technique</th>
                  </tr>
                </thead>
                <tbody>
                  {trajectory.map((step, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(112, 92, 58, 0.2)' }}>
                      <td className="font-mono" style={{ padding: '8px 12px', color: 'var(--accent-cyan)' }}>+{step.step * 10}s</td>
                      <td style={{ padding: '8px 12px', fontWeight: 600 }}>{step.predicted_stage}</td>
                      <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'center' }}>{Math.round((step.stage_probability || 0) * 100)}%</td>
                      <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'center', color: step.risk_score >= 0.7 ? 'var(--accent-danger)' : 'var(--accent-amber)' }}>
                        {Math.round((step.risk_score || 0) * 100)}%
                      </td>
                      <td style={{ padding: '8px 12px', color: 'var(--text-secondary)' }}>
                        {step.mitre?.primary_technique_name || 'N/A'} ({step.mitre?.primary_technique_id || 'N/A'})
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Containment Playbook Actions */}
          <div>
            <h4 className="font-display" style={{ fontSize: '0.9rem', color: 'var(--accent-emerald)', marginBottom: '8px' }}>
              3. Recommended SOC Containment Steps
            </h4>
            <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 'var(--radius-sm)', padding: '12px' }}>
              <p style={{ fontSize: '0.85rem', margin: 0, color: 'var(--text-primary)' }}>
                {explanation?.soc_narrative?.recommended_action || 'Maintain active logging and verify port traffic anomalies.'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
