import React from 'react';
import { Activity, AlertTriangle, ArrowRight, ShieldAlert, Sparkles, TrendingUp, Zap, Clock, ShieldCheck, Flame } from 'lucide-react';

const STAGE_COLORS = {
  'Normal': { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981', border: 'rgba(16, 185, 129, 0.4)' },
  'Reconnaissance': { bg: 'rgba(56, 189, 248, 0.15)', text: '#38bdf8', border: 'rgba(56, 189, 248, 0.4)' },
  'Initial Access': { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b', border: 'rgba(245, 158, 11, 0.4)' },
  'Execution': { bg: 'rgba(249, 115, 22, 0.15)', text: '#f97316', border: 'rgba(249, 115, 22, 0.4)' },
  'Privilege Escalation': { bg: 'rgba(234, 88, 12, 0.15)', text: '#ea580c', border: 'rgba(234, 88, 12, 0.4)' },
  'Defense Evasion': { bg: 'rgba(236, 72, 153, 0.15)', text: '#ec4899', border: 'rgba(236, 72, 153, 0.4)' },
  'Credential Access': { bg: 'rgba(217, 70, 239, 0.15)', text: '#d946ef', border: 'rgba(217, 70, 239, 0.4)' },
  'Lateral Movement': { bg: 'rgba(168, 85, 247, 0.15)', text: '#a855f7', border: 'rgba(168, 85, 247, 0.4)' },
  'Command and Control': { bg: 'rgba(139, 92, 246, 0.15)', text: '#8b5cf6', border: 'rgba(139, 92, 246, 0.4)' },
  'Exfiltration': { bg: 'rgba(179, 57, 44, 0.16)', text: '#b3392c', border: 'rgba(179, 57, 44, 0.35)' },
};

const DEFAULT_TRAJECTORY = [
  { step: 1, time_horizon: '+10s', predicted_stage: 'Reconnaissance', stage_probability: 0.88, risk_score: 0.35, mitre: { tactic_id: 'TA0043', primary_technique_id: 'T1046', primary_technique_name: 'Network Service Scanning' } },
  { step: 2, time_horizon: '+20s', predicted_stage: 'Initial Access', stage_probability: 0.84, risk_score: 0.52, mitre: { tactic_id: 'TA0001', primary_technique_id: 'T1110', primary_technique_name: 'Brute Force Authentication' } },
  { step: 3, time_horizon: '+30s', predicted_stage: 'Execution', stage_probability: 0.79, risk_score: 0.65, mitre: { tactic_id: 'TA0002', primary_technique_id: 'T1059', primary_technique_name: 'Command and Scripting Interpreter' } },
  { step: 4, time_horizon: '+40s', predicted_stage: 'Lateral Movement', stage_probability: 0.75, risk_score: 0.78, mitre: { tactic_id: 'TA0008', primary_technique_id: 'T1021', primary_technique_name: 'Remote Services' } },
  { step: 5, time_horizon: '+50s', predicted_stage: 'Exfiltration', stage_probability: 0.71, risk_score: 0.89, mitre: { tactic_id: 'TA0010', primary_technique_id: 'T1048', primary_technique_name: 'Exfiltration Over Alternative Protocol' } }
];

function getRiskGradient(score) {
  if (score < 0.25) return 'linear-gradient(90deg, #10b981, #38bdf8)';
  if (score < 0.55) return 'linear-gradient(90deg, #38bdf8, #f59e0b)';
  if (score < 0.8) return 'linear-gradient(90deg, #f59e0b, #f97316)';
  return 'linear-gradient(90deg, #f97316, #b3392c)';
}

export default function TrajectoryForecast({ forecastData, activeModel }) {
  const trajectory = (forecastData?.trajectory && forecastData.trajectory.length > 0) ? forecastData.trajectory : DEFAULT_TRAJECTORY;
  const horizonK = forecastData?.forecast_horizon_k || 5;

  // Compute highest risk step
  const maxRisk = trajectory.reduce((max, step) => Math.max(max, step.risk_score || 0), 0);
  const isCritical = maxRisk >= 0.75;
  const isEscalating = trajectory.length > 1 && (trajectory[trajectory.length - 1].risk_score > trajectory[0].risk_score + 0.15);
  
  // Calculate lead time before critical exfiltration/breach step
  let leadTimeSec = 50.0;
  const firstCriticalStep = trajectory.find(s => (s.risk_score >= 0.7 || s.predicted_stage === 'Exfiltration'));
  if (firstCriticalStep) {
    leadTimeSec = firstCriticalStep.step * 10.0;
  }

  return (
    <div style={{ marginBottom: '24px' }}>
      {/* Early Warning Lead Time Banner */}
      <div className="lead-time-banner" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: isCritical ? 'rgba(179, 57, 44, 0.15)' : 'rgba(154, 106, 31, 0.15)',
            border: `1px solid ${isCritical ? 'var(--accent-danger)' : 'var(--accent-cyan)'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: isCritical ? '0 0 15px rgba(179, 57, 44, 0.25)' : '0 0 15px rgba(154, 106, 31, 0.2)'
          }}>
            {isCritical ? <Flame size={24} color="var(--accent-danger)" /> : <Clock size={24} color="var(--accent-cyan)" />}
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Autoregressive Early Warning Lead Time (SIH26153 Core USP)
            </div>
            <div className="font-display" style={{ fontSize: '1.2rem', fontWeight: 800, color: isCritical ? 'var(--accent-danger)' : 'var(--text-primary)' }}>
              +{leadTimeSec.toFixed(1)}s Early Warning Window{' '}
              <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)' }}>
                ({trajectory[0]?.predicted_stage || 'Normal'} $\to$ {trajectory[trajectory.length - 1]?.predicted_stage || 'Exfiltration'})
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Trajectory Traversal</div>
            <div className="font-mono" style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
              Horizon: +50.0s (5 $\times$ 10s Windows)
            </div>
          </div>
          <div style={{ height: '30px', width: '1px', background: 'var(--border-subtle)' }} />
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Engine</div>
            <div className="font-mono" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-purple)' }}>
              {activeModel || 'Temporal Transformer'}
            </div>
          </div>
        </div>
      </div>

      {/* Trajectory Timeline Horizon Cards */}
      <div className="cyber-card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <TrendingUp size={18} color="var(--accent-cyan)" />
            <h2 className="card-title">
              Autoregressive Multi-Step Attack Trajectory Forecast Horizon
            </h2>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {isCritical && (
              <span className="badge badge-exfiltration">
                <AlertTriangle size={13} /> CRITICAL ESCALATION
              </span>
            )}
            {isEscalating && !isCritical && (
              <span className="badge badge-initial">
                <TrendingUp size={13} /> ESCALATING THREAT
              </span>
            )}
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Confidence Rollout: <strong>Autoregressive Next-State Sampling</strong>
            </span>
          </div>
        </div>

        <div className="card-body" style={{ padding: '20px' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '16px',
            position: 'relative'
          }}>
            {trajectory.map((step, idx) => {
              const stageStyle = STAGE_COLORS[step.predicted_stage] || { bg: 'rgba(112, 92, 58, 0.16)', text: 'var(--text-primary)', border: 'var(--border-subtle)' };
              const riskPercent = Math.round((step.risk_score || 0) * 100);
              const probPercent = Math.round((step.stage_probability || 0) * 100);
              const isHigh = (step.risk_score || 0) >= 0.7;

              return (
                <div
                  key={step.step || idx}
                  className={`trajectory-step-card ${isHigh ? 'high-risk' : ''}`}
                >
                  {/* Step Horizon Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span className="font-mono" style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', fontWeight: 800 }}>
                        +{step.step * 10}s
                      </span>
                      <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                        (Step 0{step.step})
                      </span>
                    </div>
                    <span
                      className="badge"
                      style={{
                        background: stageStyle.bg,
                        color: stageStyle.text,
                        border: `1px solid ${stageStyle.border}`,
                        fontSize: '0.7rem'
                      }}
                    >
                      {step.predicted_stage}
                    </span>
                  </div>

                  {/* Probability & Risk */}
                  <div style={{ background: 'rgba(236, 227, 209, 0.5)', padding: '8px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(112, 92, 58, 0.2)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Stage Probability:</span>
                      <strong className="font-mono" style={{ color: stageStyle.text }}>{probPercent}%</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', marginBottom: '6px' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Projected Risk:</span>
                      <strong className="font-mono" style={{ color: step.risk_score >= 0.7 ? 'var(--accent-danger)' : step.risk_score >= 0.4 ? 'var(--accent-amber)' : 'var(--accent-emerald)' }}>
                        {riskPercent}%
                      </strong>
                    </div>
                    <div className="risk-bar-container">
                      <div
                        className="risk-bar-fill"
                        style={{
                          width: `${riskPercent}%`,
                          background: getRiskGradient(step.risk_score || 0)
                        }}
                      />
                    </div>
                  </div>

                  {/* MITRE Technique Info */}
                  {step.mitre && (
                    <div style={{
                      background: 'rgba(247, 242, 231, 0.85)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '8px 10px',
                      fontSize: '0.72rem',
                      border: '1px solid rgba(112, 92, 58, 0.16)'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '2px' }}>
                        <span>Tactic: {step.mitre.tactic_id}</span>
                        <span className="font-mono" style={{ color: 'var(--accent-purple)' }}>{step.mitre.primary_technique_id}</span>
                      </div>
                      <div style={{ fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.3 }}>
                        {step.mitre.primary_technique_name}
                      </div>
                    </div>
                  )}

                  {/* Key Behavioral Indicators */}
                  {step.top_features && step.top_features.length > 0 && (
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>Drivers: </span>
                      {step.top_features.slice(0, 2).map((f, i) => {
                        const label = f.description || f.name || f.feature || 'Feature';
                        const delta = typeof f.delta === 'number' ? f.delta : (typeof f.attribution_score === 'number' ? f.attribution_score : 0);
                        return (
                          <span key={i} style={{ color: 'var(--text-primary)' }}>
                            {label} ({delta > 0 ? '+' : ''}{delta.toFixed(2)}){i < 1 ? ', ' : ''}
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
