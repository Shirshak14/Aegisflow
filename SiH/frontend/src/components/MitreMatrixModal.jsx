import React, { useState } from 'react';
import { X, ShieldAlert, BookOpen, ExternalLink, CheckCircle2, ChevronRight, Search, Shield, AlertTriangle } from 'lucide-react';

export default function MitreMatrixModal({ isOpen, onClose, mitreMatrix, currentStage, predictedStage }) {
  const [searchTerm, setSearchTerm] = useState('');

  if (!isOpen) return null;

  const entries = Object.entries(mitreMatrix || {});
  const filtered = entries.filter(([stageName, info]) => {
    const q = searchTerm.toLowerCase();
    return (
      stageName.toLowerCase().includes(q) ||
      info.tactic_id?.toLowerCase().includes(q) ||
      info.primary_technique_name?.toLowerCase().includes(q) ||
      info.primary_technique_id?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '1200px' }}>
        <div className="card-header" style={{ position: 'sticky', top: 0, zIndex: 10, background: 'var(--bg-secondary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ShieldAlert size={22} color="var(--accent-cyan)" />
            <div>
              <h2 className="font-display" style={{ fontSize: '1.1rem', color: 'var(--text-primary)', letterSpacing: '0.05em', margin: 0 }}>
                MITRE ATT&CK Matrix & SOC Playbook Registry
              </h2>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', margin: 0 }}>
                Standardized mapping of 24-dimensional temporal network state vectors to enterprise tactics
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(236, 227, 209, 0.7)', padding: '4px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-card)' }}>
              <Search size={14} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="Filter tactics, techniques..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-primary)',
                  fontSize: '0.78rem',
                  outline: 'none',
                  width: '180px'
                }}
              />
            </div>

            <button
              onClick={onClose}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px' }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Matrix Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: '16px'
          }}>
            {filtered.map(([stageName, info]) => {
              const isCurrent = currentStage === stageName;
              const isPredicted = predictedStage === stageName;

              return (
                <div
                  key={stageName}
                  style={{
                    background: isCurrent
                      ? 'linear-gradient(180deg, rgba(56, 189, 248, 0.15) 0%, rgba(247, 242, 231, 0.95) 100%)'
                      : isPredicted
                      ? 'linear-gradient(180deg, rgba(179, 57, 44, 0.13) 0%, rgba(247, 242, 231, 0.95) 100%)'
                      : 'rgba(236, 227, 209, 0.55)',
                    border: isCurrent
                      ? '1px solid var(--accent-cyan)'
                      : isPredicted
                      ? '1px solid var(--accent-danger)'
                      : '1px solid var(--border-card)',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                    position: 'relative',
                    boxShadow: isCurrent ? '0 0 20px rgba(154, 106, 31, 0.15)' : isPredicted ? '0 0 20px rgba(179, 57, 44, 0.18)' : 'none'
                  }}
                >
                  {/* Status Badges */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--accent-cyan)', fontWeight: 700 }}>
                      {info.tactic_id} • {info.tactic_name}
                    </span>
                    {isCurrent && (
                      <span className="badge" style={{ background: 'rgba(154, 106, 31, 0.15)', color: 'var(--accent-cyan)', border: '1px solid var(--accent-cyan)', fontSize: '0.65rem' }}>
                        Observed Now
                      </span>
                    )}
                    {isPredicted && !isCurrent && (
                      <span className="badge badge-exfiltration" style={{ fontSize: '0.65rem' }}>
                        Forecasted (+10s)
                      </span>
                    )}
                  </div>

                  <h4 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                    {stageName}
                  </h4>

                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Primary Technique: <strong style={{ color: 'var(--text-primary)' }}>{info.primary_technique_name}</strong> (<span className="font-mono" style={{ color: 'var(--accent-purple)', fontWeight: 600 }}>{info.primary_technique_id}</span>)
                  </div>

                  {/* Telemetry Trigger */}
                  <div style={{
                    background: 'rgba(236, 227, 209, 0.7)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '10px',
                    fontSize: '0.76rem',
                    color: 'var(--text-secondary)',
                    border: '1px solid rgba(112, 92, 58, 0.2)'
                  }}>
                    <strong style={{ color: 'var(--accent-amber)' }}>Telemetry Trigger Signature: </strong>
                    {info.detection_logic}
                  </div>

                  {/* Playbook Steps */}
                  {info.soc_playbook && (
                    <div style={{ marginTop: 'auto', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--accent-cyan)', textTransform: 'uppercase', marginBottom: '6px' }}>
                        Containment Checklist:
                      </div>
                      <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '5px', margin: 0, padding: 0 }}>
                        {info.soc_playbook.map((step, idx) => (
                          <li key={idx} style={{ fontSize: '0.76rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
                            <ChevronRight size={12} color="var(--accent-cyan)" style={{ marginTop: '3px', flexShrink: 0 }} />
                            <span>{step}</span>
                          </li>
                        ))}
                      </ul>
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
