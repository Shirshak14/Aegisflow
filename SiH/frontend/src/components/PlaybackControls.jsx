import React from 'react';
import { Play, Pause, StepForward, RotateCcw, Gauge, Clock, Radio } from 'lucide-react';

export default function PlaybackControls({
  replayStatus,
  onPlay,
  onPause,
  onStep,
  onSpeedChange,
  onReset,
  speed
}) {
  const currentIdx = replayStatus?.current_window_idx || 0;
  const totalWindows = replayStatus?.total_windows || 40;
  const progressPercent = Math.min(100, Math.round((currentIdx / Math.max(totalWindows, 1)) * 100));
  const isRunning = replayStatus?.is_running && !replayStatus?.is_paused;

  return (
    <div className="card" style={{ padding: '12px 20px', marginBottom: '20px', background: 'rgba(250, 246, 235, 0.95)' }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        {/* Playback Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {isRunning ? (
            <button className="btn btn-primary" onClick={onPause} title="Pause Simulation">
              <Pause size={16} />
              Pause
            </button>
          ) : (
            <button className="btn btn-primary" onClick={onPlay} title="Start Live Stream Simulation">
              <Play size={16} />
              Live Stream
            </button>
          )}

          <button className="btn btn-outline" onClick={onStep} title="Step Forward 1 Window (10s)">
            <StepForward size={16} />
            Step (+10s)
          </button>

          <button className="btn btn-outline" onClick={onReset} title="Reset Simulation to Initial State">
            <RotateCcw size={16} />
            Reset
          </button>
        </div>

        {/* Speed Multipliers */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(236, 227, 209, 0.6)', padding: '4px 8px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
          <Gauge size={14} color="var(--accent-cyan)" />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginRight: '4px' }}>Speed:</span>
          {[0.5, 1.0, 2.0, 5.0].map((s) => (
            <button
              key={s}
              onClick={() => onSpeedChange(s)}
              style={{
                background: speed === s ? 'var(--accent-cyan)' : 'transparent',
                color: speed === s ? '#000' : 'var(--text-secondary)',
                border: 'none',
                borderRadius: '4px',
                padding: '3px 8px',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {s}x
            </button>
          ))}
        </div>

        {/* Timeline Progress Bar & Window Stats */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', minWidth: '280px', flex: '1', maxWidth: '450px' }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
              <span style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={12} /> Window: {currentIdx} / {totalWindows} ({currentIdx * 10}s elapsed)
              </span>
              <span className="font-mono" style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>
                {progressPercent}%
              </span>
            </div>
            <div style={{ width: '100%', height: '6px', background: 'rgba(112, 92, 58, 0.2)', borderRadius: '999px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${progressPercent}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-purple))',
                  boxShadow: '0 0 8px rgba(154, 106, 31, 0.25)',
                  transition: 'width 0.3s ease'
                }}
              />
            </div>
          </div>

          <span className="badge" style={{ background: replayStatus?.is_synthetic ? 'rgba(168, 85, 247, 0.15)' : 'rgba(16, 185, 129, 0.15)', color: replayStatus?.is_synthetic ? 'var(--accent-purple)' : 'var(--accent-emerald)', border: `1px solid ${replayStatus?.is_synthetic ? 'rgba(168, 85, 247, 0.3)' : 'rgba(16, 185, 129, 0.3)'}` }}>
            <Radio size={12} />
            {replayStatus?.is_synthetic ? 'Synthetic Feed' : 'Real PCAP Feed'}
          </span>
        </div>
      </div>
    </div>
  );
}
