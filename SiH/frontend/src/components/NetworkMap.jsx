import React from 'react';
import { Server, Shield, Radio, Database, Laptop, Lock, ArrowRight, AlertTriangle } from 'lucide-react';

export default function NetworkMap({ currentStage, predictedStage, telemetry }) {
  // Determine state of each node based on MITRE kill-chain progression
  const stageOrder = [
    'Normal',
    'Reconnaissance',
    'Initial Access',
    'Execution',
    'Privilege Escalation',
    'Defense Evasion',
    'Credential Access',
    'Lateral Movement',
    'Command and Control',
    'Exfiltration'
  ];

  const currentIdx = stageOrder.indexOf(currentStage || 'Normal');
  const predictedIdx = stageOrder.indexOf(predictedStage || 'Normal');
  const maxStageIdx = Math.max(currentIdx, predictedIdx);

  const isEdgeAttacked = maxStageIdx >= 1; // Recon
  const isDMZCompromised = maxStageIdx >= 2; // Initial Access / Execution
  const isLateralSpread = maxStageIdx >= 7; // Lateral Movement / Credential Access
  const isCoreThreatened = maxStageIdx >= 8; // C2 / Exfiltration

  const nodes = [
    {
      id: 'attacker',
      title: 'External Vector',
      sub: telemetry?.is_synthetic ? 'Simulated IP: 198.51.100.42' : 'Ingress Flow Stream',
      icon: Radio,
      status: maxStageIdx > 0 ? 'hostile' : 'quiet',
      color: maxStageIdx > 0 ? 'var(--accent-danger)' : 'var(--text-muted)'
    },
    {
      id: 'perimeter',
      title: 'Edge IDS / Firewall',
      sub: `Port diversity: ${(telemetry?.port_diversity || 1.2).toFixed(1)}`,
      icon: Shield,
      status: isEdgeAttacked ? 'alert' : 'secure',
      color: isEdgeAttacked ? 'var(--accent-amber)' : 'var(--accent-emerald)'
    },
    {
      id: 'dmz',
      title: 'DMZ Gateway / Web Server',
      sub: isDMZCompromised ? 'Compromised Target' : 'Active (10.0.1.15)',
      icon: Server,
      status: isDMZCompromised ? 'breached' : 'nominal',
      color: isDMZCompromised ? 'var(--accent-rose)' : 'var(--accent-cyan)'
    },
    {
      id: 'internal',
      title: 'Internal Subnet Pivot',
      sub: `${Math.round((telemetry?.internal_lateral_ratio || 0) * 100)}% Lateral Ratio`,
      icon: Laptop,
      status: isLateralSpread ? 'compromised' : 'nominal',
      color: isLateralSpread ? 'var(--accent-purple)' : 'var(--text-muted)'
    },
    {
      id: 'core',
      title: 'Core Domain Vault',
      sub: isCoreThreatened ? 'CRITICAL EXFILTRATION RISK' : 'Secured (10.0.3.5)',
      icon: Database,
      status: isCoreThreatened ? 'critical' : 'nominal',
      color: isCoreThreatened ? 'var(--accent-danger)' : 'var(--accent-emerald)'
    }
  ];

  return (
    <div className="cyber-card" style={{ marginBottom: '20px' }}>
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Shield size={16} color="var(--accent-cyan)" />
          <h3 className="card-title">Live Attack Path & Topology Vector</h3>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="badge" style={{ background: 'rgba(236, 227, 209, 0.7)', color: 'var(--text-secondary)', border: '1px solid var(--border-subtle)', fontSize: '0.68rem' }}>
            Current Focus: <strong style={{ color: 'var(--accent-cyan)', marginLeft: '4px' }}>{currentStage}</strong>
          </span>
          {predictedStage !== currentStage && (
            <span className="badge" style={{ background: 'rgba(179, 57, 44, 0.13)', color: 'var(--accent-danger)', border: '1px solid var(--accent-danger)', fontSize: '0.68rem' }}>
              Forecasted: <strong style={{ marginLeft: '4px' }}>{predictedStage}</strong>
            </span>
          )}
        </div>
      </div>

      <div className="card-body" style={{ padding: '20px' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
          gap: '12px',
          position: 'relative'
        }}>
          {nodes.map((node, i) => {
            const Icon = node.icon;
            const isAlert = node.status === 'hostile' || node.status === 'breached' || node.status === 'critical';

            return (
              <div
                key={node.id}
                className="topo-node"
                style={{
                  background: isAlert ? 'linear-gradient(180deg, rgba(179, 57, 44, 0.12) 0%, rgba(247, 242, 231, 0.9) 100%)' : 'rgba(236, 227, 209, 0.5)',
                  border: `1px solid ${isAlert ? node.color : 'var(--border-subtle)'}`,
                  borderRadius: 'var(--radius-md)',
                  padding: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  boxShadow: isAlert ? `0 0 15px ${node.color}33` : 'none',
                  position: 'relative'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    background: 'rgba(247, 242, 231, 0.9)',
                    border: `1px solid ${node.color}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Icon size={16} color={node.color} />
                  </div>
                  <span className="font-mono" style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                    NODE 0{i + 1}
                  </span>
                </div>

                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                    {node.title}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: node.color, marginTop: '2px', fontWeight: 500 }}>
                    {node.sub}
                  </div>
                </div>

                <div style={{
                  height: '3px',
                  width: '100%',
                  background: 'rgba(112, 92, 58, 0.16)',
                  borderRadius: '999px',
                  overflow: 'hidden',
                  marginTop: 'auto'
                }}>
                  <div
                    style={{
                      height: '100%',
                      width: isAlert ? '100%' : '30%',
                      background: node.color,
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
  );
}
