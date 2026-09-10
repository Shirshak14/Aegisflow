import React, { useState } from 'react';
import { Eye, Clock, BarChart3, Bot, CheckCircle2, AlertTriangle, ShieldCheck, Zap, Shield, Play } from 'lucide-react';

const DEFAULT_EXPLANATION = {
  predicted_stage: 'Reconnaissance',
  stage_confidence: 0.88,
  top_features: [
    { name: 'TCP SYN Flag Ratio', attribution_score: 0.42, is_positive: true },
    { name: 'Port Scan Indicator', attribution_score: 0.38, is_positive: true },
    { name: 'Destination Port Diversity', attribution_score: 0.31, is_positive: true },
    { name: 'Failed Connection Ratio', attribution_score: 0.28, is_positive: true },
    { name: 'Packet Rate (PPS)', attribution_score: 0.22, is_positive: true },
    { name: 'Mean Flow Inter-Arrival Time', attribution_score: -0.15, is_positive: false }
  ],
  attention_timeline: [
    { time_offset: '-90s', weight: 0.06 },
    { time_offset: '-80s', weight: 0.07 },
    { time_offset: '-70s', weight: 0.08 },
    { time_offset: '-60s', weight: 0.09 },
    { time_offset: '-50s', weight: 0.11 },
    { time_offset: '-40s', weight: 0.12 },
    { time_offset: '-30s', weight: 0.13 },
    { time_offset: '-20s', weight: 0.15 },
    { time_offset: '-10s', weight: 0.18 },
    { time_offset: '0s (current)', weight: 0.21 }
  ],
  soc_narrative: {
    incident_summary: 'Forecasting engine identified high SYN flag density (82%) coupled with abnormal destination port entropy. Attack progression modeled toward Initial Access in +20.0s.',
    key_drivers: [
      'Elevated TCP SYN probe ratio (0.82) matching Nmap SYN Stealth Scan (T1046)',
      'High failed TCP connection teardowns indicating aggressive port probing',
      'Low inter-arrival burst latency across external ingress interface'
    ],
    recommended_action: 'Deploy temporary rate-limit ACL on ingress router and block scanning source IP (198.51.100.42).'
  }
};

export default function ExplainabilityPanel({ explanation, activeModel }) {
  const [containmentExecuted, setContainmentExecuted] = useState(false);

  const exp = explanation || DEFAULT_EXPLANATION;
  const topFeatures = exp.top_features || [];
  const attentionTimeline = exp.attention_timeline || [];
  const socNarrative = exp.soc_narrative || {};

  const handleExecuteContainment = () => {
    setContainmentExecuted(true);
  };

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
      gap: '20px',
      marginBottom: '24px'
    }}>
      {/* Panel 1: SOC AI Copilot & Automated Reasoner */}
      <div className="cyber-card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Bot size={18} color="var(--accent-cyan)" />
            <h3 className="card-title">SOC Incident Copilot & Natural Language Reasoner</h3>
          </div>
          <span className="badge" style={{ background: 'rgba(154, 106, 31, 0.1)', color: 'var(--accent-cyan)', border: '1px solid rgba(154, 106, 31, 0.2)' }}>
            AI Reasoner
          </span>
        </div>

        <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Natural Language Narrative */}
          <div style={{
            background: 'rgba(236, 227, 209, 0.7)',
            borderLeft: '4px solid var(--accent-cyan)',
            padding: '14px 16px',
            borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
            fontSize: '0.85rem',
            lineHeight: '1.6',
            color: 'var(--text-primary)'
          }}>
            {socNarrative.incident_summary || exp.summary_text || 'Telemetry normal.'}
          </div>

          {/* Key Threat Indicators List */}
          {socNarrative.key_drivers && socNarrative.key_drivers.length > 0 && (
            <div>
              <div style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '6px', letterSpacing: '0.04em' }}>
                Observed Physical Attack Signatures:
              </div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px', margin: 0, padding: 0 }}>
                {socNarrative.key_drivers.map((driver, i) => (
                  <li key={i} style={{ fontSize: '0.8rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                    <span style={{ color: 'var(--accent-amber)', marginTop: '1px' }}>▸</span>
                    <span>{driver}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Containment Playbook Action Box */}
          <div style={{
            background: containmentExecuted ? 'rgba(16, 185, 129, 0.12)' : 'rgba(168, 85, 247, 0.12)',
            border: `1px solid ${containmentExecuted ? 'var(--accent-emerald)' : 'rgba(168, 85, 247, 0.4)'}`,
            borderRadius: 'var(--radius-sm)',
            padding: '12px 16px',
            marginTop: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 800, color: containmentExecuted ? 'var(--accent-emerald)' : 'var(--accent-purple)', textTransform: 'uppercase' }}>
                <ShieldCheck size={14} /> Recommended Containment Action:
              </div>
              {containmentExecuted && (
                <span className="badge badge-normal" style={{ fontSize: '0.65rem' }}>
                  Rule Applied
                </span>
              )}
            </div>

            <p style={{ fontSize: '0.8rem', color: 'var(--text-primary)', margin: '0 0 10px 0', lineHeight: 1.4 }}>
              {socNarrative.recommended_action || 'Enforce egress firewall filters and log DNS query spikes.'}
            </p>

            <button
              className={`btn ${containmentExecuted ? 'btn-outline' : 'btn-primary'}`}
              onClick={handleExecuteContainment}
              disabled={containmentExecuted}
              style={{ width: '100%', fontSize: '0.78rem', padding: '6px' }}
            >
              {containmentExecuted ? <CheckCircle2 size={14} color="var(--accent-emerald)" /> : <Zap size={14} />}
              {containmentExecuted ? 'Containment Playbook Active' : 'Execute Immediate Containment Rule'}
            </button>
          </div>
        </div>
      </div>

      {/* Panel 2: SHAP Feature Attribution (Why this stage was predicted) */}
      <div className="cyber-card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart3 size={18} color="var(--accent-purple)" />
            <h3 className="card-title">XAI Feature Attributions (Risk Drivers)</h3>
          </div>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            SHAP Divergence
          </span>
        </div>

        <div className="card-body">
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
            Impact of dense network state features relative to nominal historical baselines:
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {topFeatures.slice(0, 6).map((feat, idx) => {
              const score = feat.attribution_score;
              const absScore = Math.abs(score);
              const isPos = feat.is_positive;
              const barWidth = Math.min(100, Math.round(absScore * 130));

              return (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.76rem' }}>
                    <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                      {feat.name}
                    </span>
                    <span className="font-mono" style={{ color: isPos ? 'var(--accent-danger)' : 'var(--accent-emerald)', fontWeight: 700 }}>
                      {isPos ? '+' : ''}{score.toFixed(3)}
                    </span>
                  </div>

                  <div style={{ width: '100%', height: '6px', background: 'rgba(112, 92, 58, 0.2)', borderRadius: '999px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${barWidth}%`,
                        height: '100%',
                        background: isPos ? 'linear-gradient(90deg, #f59e0b, #b3392c)' : 'linear-gradient(90deg, #38bdf8, #10b981)',
                        borderRadius: '999px',
                        transition: 'width 0.4s ease'
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Panel 3: Multi-Head Temporal Attention Timeline */}
      <div className="cyber-card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Eye size={18} color="var(--accent-cyan)" />
            <h3 className="card-title">Temporal Self-Attention Horizon</h3>
          </div>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            Transformer Heads
          </span>
        </div>

        <div className="card-body">
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Transformer self-attention distribution across the 100-second sequence buffer:
          </p>

          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', height: '120px', padding: '0 4px', gap: '6px' }}>
            {attentionTimeline.length > 0 ? (
              attentionTimeline.map((item, idx) => {
                const heightPercent = Math.min(100, Math.max(12, Math.round(item.weight * 320)));
                const isCurrent = idx === attentionTimeline.length - 1;

                return (
                  <div key={idx} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end', gap: '4px' }}>
                    <span className="font-mono" style={{ fontSize: '0.62rem', color: isCurrent ? 'var(--accent-cyan)' : 'var(--text-muted)' }}>
                      {(item.weight * 100).toFixed(0)}%
                    </span>
                    <div
                      style={{
                        width: '100%',
                        height: `${heightPercent}%`,
                        background: isCurrent ? 'linear-gradient(180deg, var(--accent-cyan), var(--accent-purple))' : 'linear-gradient(180deg, rgba(154, 106, 31, 0.28), rgba(112, 92, 58, 0.22))',
                        borderRadius: '4px 4px 0 0',
                        boxShadow: isCurrent ? '0 0 12px rgba(154, 106, 31, 0.3)' : 'none',
                        transition: 'height 0.3s ease'
                      }}
                      title={`${item.time_offset}: ${(item.weight * 100).toFixed(1)}%`}
                    />
                    <span style={{ fontSize: '0.6rem', color: isCurrent ? 'var(--accent-cyan)' : 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {item.time_offset.replace(' (current)', '')}
                    </span>
                  </div>
                );
              })
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                Self-Attention maps generated exclusively via Temporal Transformer.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
