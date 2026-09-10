import React, { useState, useEffect } from 'react';
import { Shield, ShieldAlert, Cpu, Crosshair, Award, UploadCloud, FileText, Volume2, VolumeX, Clock } from 'lucide-react';

export default function Header({
  health,
  replayStatus,
  scenarios,
  selectedScenario,
  onScenarioChange,
  models,
  activeModel,
  onModelChange,
  onOpenMitre,
  onOpenBenchmark,
  onOpenUpload,
  onOpenReport,
  maxRiskScore
}) {
  const [timeStr, setTimeStr] = useState('');
  const [soundEnabled, setSoundEnabled] = useState(true);

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setTimeStr(now.toTimeString().split(' ')[0] + ' UTC');
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Compute DEFCON level based on maximum forecasted risk score
  const getDefcon = (risk) => {
    if (risk >= 0.8) return { level: 1, text: 'DEFCON 1: CRITICAL', cls: 'defcon-1' };
    if (risk >= 0.6) return { level: 2, text: 'DEFCON 2: SEVERE', cls: 'defcon-2' };
    if (risk >= 0.4) return { level: 3, text: 'DEFCON 3: ELEVATED', cls: 'defcon-3' };
    if (risk >= 0.2) return { level: 4, text: 'DEFCON 4: GUARDED', cls: 'defcon-4' };
    return { level: 5, text: 'DEFCON 5: NOMINAL', cls: 'defcon-5' };
  };

  const defcon = getDefcon(maxRiskScore || 0);

  return (
    <header style={{
      background: 'rgba(250, 246, 235, 0.95)',
      borderBottom: '1px solid var(--border-card)',
      padding: '12px 24px',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      backdropFilter: 'blur(20px)'
    }}>
      <div style={{
        maxWidth: '1680px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        {/* Left: Branding & DEFCON Threat Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '44px',
            height: '44px',
            borderRadius: 'var(--radius-sm)',
            background: 'linear-gradient(135deg, rgba(154, 106, 31, 0.18), rgba(168, 85, 247, 0.25))',
            border: '1px solid var(--accent-cyan)',
            boxShadow: '0 0 20px rgba(154, 106, 31, 0.22)'
          }}>
            <Shield size={24} color="var(--accent-cyan)" />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 className="font-display" style={{ fontSize: '1.25rem', fontWeight: 900, letterSpacing: '0.08em', color: 'var(--text-primary)', margin: 0 }}>
                AEGIS<span style={{ color: 'var(--accent-cyan)' }}>FLOW</span>
              </h1>
              <span className="badge" style={{ background: 'rgba(154, 106, 31, 0.1)', color: 'var(--accent-cyan)', border: '1px solid rgba(154, 106, 31, 0.22)', fontSize: '0.68rem' }}>
                SIH26153
              </span>
            </div>
            <p style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', letterSpacing: '0.02em', margin: 0 }}>
              AI-Powered Cyber Attack Forecasting & Trajectory Modeling Platform
            </p>
          </div>

          <div style={{ height: '32px', width: '1px', background: 'var(--border-subtle)', margin: '0 4px' }} />

          {/* DEFCON Status */}
          <div className={`defcon-badge ${defcon.cls}`}>
            <span className={`pulse-dot ${defcon.level <= 2 ? 'alert' : 'online'}`} />
            {defcon.text}
          </div>

          {/* Live Clock */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <Clock size={13} color="var(--accent-cyan)" />
            <span className="font-mono">{timeStr || '12:00:00 UTC'}</span>
          </div>
        </div>

        {/* Right: Selectors, Controls & Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Scenario Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(236, 227, 209, 0.7)', padding: '4px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-card)' }}>
            <Crosshair size={14} color="var(--accent-cyan)" />
            <select
              value={selectedScenario}
              onChange={(e) => onScenarioChange(e.target.value)}
              style={{
                background: 'transparent',
                color: 'var(--text-primary)',
                border: 'none',
                fontSize: '0.8rem',
                fontFamily: 'var(--font-body)',
                fontWeight: 600,
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              {scenarios.map((sc) => (
                <option key={sc} value={sc} style={{ background: '#ffffff', color: 'var(--text-primary)' }}>
                  Kill-Chain: {sc}
                </option>
              ))}
            </select>
          </div>

          {/* Model Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(236, 227, 209, 0.7)', padding: '4px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-card)' }}>
            <Cpu size={14} color="var(--accent-purple)" />
            <select
              value={activeModel}
              onChange={(e) => onModelChange(e.target.value)}
              style={{
                background: 'transparent',
                color: 'var(--text-primary)',
                border: 'none',
                fontSize: '0.8rem',
                fontFamily: 'var(--font-body)',
                fontWeight: 600,
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              {models.map((m) => (
                <option key={m} value={m} style={{ background: '#ffffff', color: 'var(--text-primary)' }}>
                  Model: {m}
                </option>
              ))}
            </select>
          </div>

          {/* Modals Triggers */}
          <button className="btn btn-outline" onClick={onOpenMitre} style={{ fontSize: '0.78rem', padding: '6px 12px' }}>
            <ShieldAlert size={14} color="var(--accent-cyan)" />
            MITRE Matrix
          </button>

          <button className="btn btn-outline" onClick={onOpenBenchmark} style={{ fontSize: '0.78rem', padding: '6px 12px' }}>
            <Award size={14} color="var(--accent-amber)" />
            Benchmarks
          </button>

          <button className="btn btn-outline" onClick={onOpenReport} style={{ fontSize: '0.78rem', padding: '6px 12px' }}>
            <FileText size={14} color="var(--accent-emerald)" />
            Incident Report
          </button>

          <button className="btn btn-primary" onClick={onOpenUpload} style={{ fontSize: '0.78rem', padding: '6px 14px' }}>
            <UploadCloud size={14} />
            Ingest PCAP
          </button>
        </div>
      </div>
    </header>
  );
}
