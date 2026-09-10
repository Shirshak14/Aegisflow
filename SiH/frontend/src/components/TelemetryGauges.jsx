import React from 'react';
import { Activity, Server, Network, Wifi, AlertOctagon, Share2, Layers, ShieldCheck } from 'lucide-react';

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 Bps';
  const k = 1024;
  const sizes = ['Bps', 'KBps', 'MBps', 'GBps'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

const DEFAULT_TELEMETRY = {
  timestamp: Date.now() / 1000,
  window_id: 1,
  ground_truth_stage: 'Reconnaissance',
  packet_rate_pps: 1450.0,
  byte_rate_bps: 285000.0,
  fwd_packets: 1200,
  bwd_packets: 250,
  syn_ratio: 0.82,
  rst_ratio: 0.45,
  port_diversity: 4.2,
  failed_conn_ratio: 0.72,
  internal_lateral_ratio: 0.15,
  is_synthetic: true
};

export default function TelemetryGauges({ telemetry, replayStatus }) {
  const tel = telemetry || DEFAULT_TELEMETRY;

  const synPercent = Math.round((tel.syn_ratio || 0) * 100);
  const rstPercent = Math.round((tel.rst_ratio || 0) * 100);
  const failedConnPercent = Math.round((tel.failed_conn_ratio || 0) * 100);
  const lateralPercent = Math.round((tel.internal_lateral_ratio || 0) * 100);

  const isSynHigh = synPercent >= 50;
  const isFailedHigh = failedConnPercent >= 40;
  const isLateralHigh = lateralPercent >= 40;

  const metrics = [
    {
      title: 'Packet Rate (PPS)',
      value: `${tel.packet_rate_pps || 0}`,
      unit: 'pkts/sec',
      sub: `${tel.fwd_packets || 0} fwd / ${tel.bwd_packets || 0} bwd`,
      icon: Activity,
      color: 'var(--accent-cyan)',
      alert: (tel.packet_rate_pps || 0) > 1200,
      trend: '+24%'
    },
    {
      title: 'Network Throughput',
      value: formatBytes(tel.byte_rate_bps || 0),
      unit: 'bandwidth',
      sub: `Window duration: 10.0s`,
      icon: Network,
      color: 'var(--accent-blue)',
      alert: false,
      trend: 'nominal'
    },
    {
      title: 'TCP SYN Flag Ratio',
      value: `${synPercent}%`,
      unit: 'handshake flags',
      sub: isSynHigh ? 'Port sweep signature detected' : 'Nominal handshake stream',
      icon: Wifi,
      color: isSynHigh ? 'var(--accent-danger)' : 'var(--accent-cyan)',
      alert: isSynHigh,
      trend: isSynHigh ? 'HIGH' : 'NORMAL'
    },
    {
      title: 'Failed Connection Rate',
      value: `${failedConnPercent}%`,
      unit: 'drop ratio',
      sub: isFailedHigh ? 'High connection drop/reset rate' : 'Standard connection response',
      icon: AlertOctagon,
      color: isFailedHigh ? 'var(--accent-amber)' : 'var(--accent-emerald)',
      alert: isFailedHigh,
      trend: isFailedHigh ? 'ALERT' : 'OK'
    },
    {
      title: 'Port Diversity & Entropy',
      value: (tel.port_diversity || 0).toFixed(2),
      unit: 'entropy index',
      sub: (tel.port_diversity || 0) > 2.5 ? 'Broad multi-port sweep' : 'Targeted service ports',
      icon: Layers,
      color: (tel.port_diversity || 0) > 2.5 ? 'var(--accent-rose)' : 'var(--accent-purple)',
      alert: (tel.port_diversity || 0) > 2.5,
      trend: (tel.port_diversity || 0) > 2.5 ? 'ELEVATED' : 'STABLE'
    },
    {
      title: 'Internal Lateral Movement',
      value: `${lateralPercent}%`,
      unit: 'subnet traffic',
      sub: isLateralHigh ? 'Host-to-host pivot activity' : 'External boundary flow',
      icon: Share2,
      color: isLateralHigh ? 'var(--accent-danger)' : 'var(--accent-cyan)',
      alert: isLateralHigh,
      trend: isLateralHigh ? 'PIVOT' : 'CLEAN'
    }
  ];

  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '16px'
      }}>
        {metrics.map((m, idx) => {
          const Icon = m.icon;
          return (
            <div
              key={idx}
              className={`cyber-card ${m.alert ? 'alert-active' : ''}`}
              style={{
                padding: '16px 18px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    {m.title}
                  </span>
                  <div style={{
                    padding: '6px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(236, 227, 209, 0.7)',
                    border: `1px solid ${m.alert ? 'var(--accent-danger)' : 'var(--border-subtle)'}`
                  }}>
                    <Icon size={16} color={m.color} />
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '4px' }}>
                  <span className="font-mono" style={{ fontSize: '1.5rem', fontWeight: 800, color: m.color, letterSpacing: '-0.02em' }}>
                    {m.value}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    {m.unit}
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.72rem', color: m.alert ? 'var(--accent-rose)' : 'var(--text-muted)' }}>
                  {m.sub}
                </span>
                <span className="font-mono" style={{ fontSize: '0.68rem', fontWeight: 700, color: m.alert ? 'var(--accent-danger)' : 'var(--accent-emerald)', background: 'rgba(236, 227, 209, 0.5)', padding: '2px 6px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
                  {m.trend}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
