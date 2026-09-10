import React, { useEffect, useMemo, useState } from 'react';
import Header from './components/Header';
import PlaybackControls from './components/PlaybackControls';
import TrajectoryForecast from './components/TrajectoryForecast';
import TelemetryGauges from './components/TelemetryGauges';
import NetworkMap from './components/NetworkMap';
import ExplainabilityPanel from './components/ExplainabilityPanel';
import MitreMatrixModal from './components/MitreMatrixModal';
import BenchmarkModal from './components/BenchmarkModal';
import UploadModal from './components/UploadModal';
import IncidentReportModal from './components/IncidentReportModal';
import { fetchHealth, fetchLatestForecast, fetchScenarios, setScenario, startReplay, pauseReplay, stepReplay, setPlaybackSpeed, resetReplay, fetchModels, setActiveModel, fetchMitreMatrix } from './api/client';
import { AlertCircle, ArrowRight, Bot, CheckCircle2, ChevronDown, ChevronUp, Clock3, Gauge, Network, Shield, Sparkles, Target, TrendingUp, Zap } from 'lucide-react';

const STAGE_COLORS = {
  Normal: 'stage-normal',
  Reconnaissance: 'stage-recon',
  'Initial Access': 'stage-initial',
  Execution: 'stage-execution',
  'Privilege Escalation': 'stage-privilege',
  'Defense Evasion': 'stage-defense',
  'Credential Access': 'stage-credential',
  'Lateral Movement': 'stage-lateral',
  'Command and Control': 'stage-c2',
  Exfiltration: 'stage-exfiltration'
};

function stageClass(stage) { return STAGE_COLORS[stage] || 'stage-neutral'; }
function pct(value) { return Math.round((Number(value) || 0) * 100); }
function formatBytes(bytes) {
  if (!bytes) return '0 B/s';
  if (bytes < 1024) return `${Math.round(bytes)} B/s`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB/s`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB/s`;
}

export default function App() {
  const [health, setHealth] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [replayStatus, setReplayStatus] = useState(null);
  const [scenarios, setScenarios] = useState(['Full Multi-Stage Attack', 'Recon -> Initial Access', 'Brute Force -> Initial Access', 'Lateral Movement -> C2', 'Normal Scenario']);
  const [selectedScenario, setSelectedScenario] = useState('Full Multi-Stage Attack');
  const [models, setModels] = useState(['Temporal Transformer', 'LSTM', 'Logistic Regression']);
  const [activeModel, setActiveModelName] = useState('Temporal Transformer');
  const [modelsData, setModelsData] = useState(null);
  const [mitreMatrix, setMitreMatrix] = useState({});
  const [activeTab, setActiveTab] = useState('dashboard');
  const [playbackSpeed, setPlaybackSpeedState] = useState(1.0);
  const [showDetails, setShowDetails] = useState(false);
  const [isMitreOpen, setIsMitreOpen] = useState(false);
  const [isBenchmarkOpen, setIsBenchmarkOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const loadInitialData = async () => {
    try {
      const [h, f, sc, md, mt] = await Promise.all([
        fetchHealth().catch(() => null), fetchLatestForecast().catch(() => null), fetchScenarios().catch(() => null), fetchModels().catch(() => null), fetchMitreMatrix().catch(() => null)
      ]);
      if (h) setHealth(h);
      if (f?.status === 'success') {
        setForecastData(f.forecast); setTelemetry(f.traffic_telemetry); setExplanation(f.explanation); setReplayStatus(f.replay_status);
        if (f.replay_status?.scenario_name) setSelectedScenario(f.replay_status.scenario_name);
        if (f.replay_status?.active_model) setActiveModelName(f.replay_status.active_model);
      }
      if (sc?.scenarios) setScenarios(sc.scenarios.map((s) => typeof s === 'string' ? s : s.name));
      if (md) { setModelsData(md); if (md.available_models) setModels(md.available_models); if (md.active_model) setActiveModelName(md.active_model); }
      if (mt?.matrix) setMitreMatrix(mt.matrix);
    } catch (err) {
      console.error(err); setErrorMessage('Backend connection lost. Start FastAPI on http://127.0.0.1:8000');
    }
  };

  useEffect(() => { loadInitialData(); }, []);

  useEffect(() => {
    let interval;
    const poll = async () => {
      try {
        const f = await fetchLatestForecast();
        if (f?.status === 'success') { setForecastData(f.forecast); setTelemetry(f.traffic_telemetry); setExplanation(f.explanation); setReplayStatus(f.replay_status); }
      } catch (err) { console.error(err); }
    };
    if (replayStatus?.is_running && !replayStatus?.is_paused) interval = setInterval(poll, Math.max(400, Math.round(1500 / playbackSpeed)));
    return () => interval && clearInterval(interval);
  }, [replayStatus?.is_running, replayStatus?.is_paused, playbackSpeed]);

  const refreshForecast = async () => {
    const f = await fetchLatestForecast();
    if (f?.status === 'success') { setForecastData(f.forecast); setTelemetry(f.traffic_telemetry); setExplanation(f.explanation); setReplayStatus(f.replay_status); }
  };
  const handleScenarioChange = async (name) => { setSelectedScenario(name); try { await setScenario(name); await refreshForecast(); } catch (e) { console.error(e); } };
  const handleModelChange = async (name) => { setActiveModelName(name); try { await setActiveModel(name); await refreshForecast(); } catch (e) { console.error(e); } };
  const handlePlay = async () => { try { await startReplay(playbackSpeed); setReplayStatus((p) => ({ ...p, is_running: true, is_paused: false })); } catch (e) { console.error(e); } };
  const handlePause = async () => { try { await pauseReplay(); setReplayStatus((p) => ({ ...p, is_paused: true })); } catch (e) { console.error(e); } };
  const handleStep = async () => { try { await stepReplay(); await refreshForecast(); } catch (e) { console.error(e); } };
  const handleSpeedChange = async (speed) => { setPlaybackSpeedState(speed); try { await setPlaybackSpeed(speed); } catch (e) { console.error(e); } };
  const handleReset = async () => { try { await resetReplay(); await refreshForecast(); } catch (e) { console.error(e); } };
  const handleUploadSuccess = async () => { await refreshForecast(); setIsUploadOpen(false); };

  const trajectory = forecastData?.trajectory?.length ? forecastData.trajectory : [
    { step: 1, predicted_stage: 'Reconnaissance', stage_probability: .88, risk_score: .35 },
    { step: 2, predicted_stage: 'Initial Access', stage_probability: .84, risk_score: .52 },
    { step: 3, predicted_stage: 'Execution', stage_probability: .79, risk_score: .65 },
    { step: 4, predicted_stage: 'Lateral Movement', stage_probability: .75, risk_score: .78 },
    { step: 5, predicted_stage: 'Exfiltration', stage_probability: .71, risk_score: .89 }
  ];
  const currentStage = telemetry?.ground_truth_stage || 'Normal';
  const next = trajectory[0] || {};
  const maxRisk = Math.max(...trajectory.map((s) => Number(s.risk_score) || 0), 0);
  const leadStep = trajectory.find((s) => (s.risk_score || 0) >= .7 || s.predicted_stage === 'Exfiltration');
  const leadTime = (leadStep?.step || trajectory.length) * 10;
  const risk = pct(maxRisk);
  const currentRisk = Math.min(99, Math.max(0, Math.round((Number(next.risk_score) || 0) * 100)));
  const drivers = (explanation?.top_features || []).slice(0, 3);
  const narrative = explanation?.soc_narrative;
  const telemetryItems = useMemo(() => ([
    ['Packets/sec', `${Math.round(telemetry?.packet_rate_pps || 0).toLocaleString()}`, 'Network activity'],
    ['Failed connections', `${pct(telemetry?.failed_conn_ratio)}%`, 'Connection drops'],
    ['TCP SYN ratio', `${pct(telemetry?.syn_ratio)}%`, 'Scan indicator'],
    ['Throughput', formatBytes(telemetry?.byte_rate_bps), 'Traffic volume']
  ]), [telemetry]);

  return (
    <div className="app-shell">
      <div className="scanlines" />
      <Header health={health} replayStatus={replayStatus} scenarios={scenarios} selectedScenario={selectedScenario} onScenarioChange={handleScenarioChange} models={models} activeModel={activeModel} onModelChange={handleModelChange} onOpenMitre={() => setIsMitreOpen(true)} onOpenBenchmark={() => setIsBenchmarkOpen(true)} onOpenUpload={() => setIsUploadOpen(true)} onOpenReport={() => setIsReportOpen(true)} maxRiskScore={maxRisk / 1} />

      <main className="dashboard-main">
        {errorMessage && <div className="error-banner"><AlertCircle size={18} /><span>{errorMessage}</span></div>}

        <div className="dashboard-toolbar">
          <div className="view-tabs">
            <button className={activeTab === 'dashboard' ? 'view-tab active' : 'view-tab'} onClick={() => setActiveTab('dashboard')}><Target size={15} /> Command Center</button>
            <button className={activeTab === 'topology' ? 'view-tab active' : 'view-tab'} onClick={() => setActiveTab('topology')}><Network size={15} /> Network Map</button>
            <button className={activeTab === 'details' ? 'view-tab active' : 'view-tab'} onClick={() => setActiveTab('details')}><Gauge size={15} /> Technical Details</button>
          </div>
          <div className="compact-meta"><span>10s windows</span><span>•</span><span>9 attack stages</span><span>•</span><span>{activeModel}</span></div>
        </div>

        {activeTab === 'dashboard' && (
          <>
            <section className={`hero-grid ${maxRisk >= .75 ? 'critical' : ''}`}>
              <div className="current-threat panel">
                <div className="eyebrow"><span className="live-dot" /> CURRENT NETWORK STATE</div>
                <div className="threat-row">
                  <div>
                    <div className={`stage-pill ${stageClass(currentStage)}`}>{currentStage}</div>
                    <h2>{narrative?.incident_summary ? 'Suspicious activity detected' : 'Network activity under observation'}</h2>
                    <p>{narrative?.incident_summary || 'The forecasting engine is analyzing recent network windows for attack progression.'}</p>
                  </div>
                  <div className="risk-ring" style={{ '--risk': `${Math.max(currentRisk, risk)}%` }}><strong>{Math.max(currentRisk, risk)}%</strong><span>risk</span></div>
                </div>
              </div>

              <div className="prediction-card panel">
                <div className="eyebrow"><Sparkles size={14} /> AI FORECAST</div>
                <div className="prediction-stage"><span className="forecast-label">NEXT LIKELY STAGE</span><div className={`stage-pill large ${stageClass(next.predicted_stage)}`}>{next.predicted_stage || 'Normal'}</div></div>
                <div className="prediction-stats"><div><strong>{pct(next.stage_probability) || 0}%</strong><span>confidence</span></div><div><strong>+{leadStep?.step ? leadStep.step * 10 : 10}s</strong><span>early warning</span></div></div>
                <div className="forecast-arrow"><span>Current: {currentStage}</span><ArrowRight size={16} /><span>Next: {next.predicted_stage || 'Normal'}</span></div>
              </div>
            </section>

            <section className="timeline panel">
              <div className="section-head"><div><div className="eyebrow"><TrendingUp size={14} /> ATTACK PROGRESSION</div><h3>What the model expects next</h3></div><div className="lead-time"><Clock3 size={15} /><strong>+{leadTime}s</strong><span>to critical risk</span></div></div>
              <div className="timeline-track">
                <div className="timeline-line" />
                <div className="timeline-items">
                  <div className="timeline-item now"><div className="timeline-dot" /><span className="timeline-time">NOW</span><strong>{currentStage}</strong></div>
                  {trajectory.map((step, idx) => <div className={`timeline-item ${idx === 0 ? 'next' : ''}`} key={step.step || idx}><div className="timeline-dot" /><span className="timeline-time">+{(step.step || idx + 1) * 10}s</span><strong>{step.predicted_stage}</strong><small>{pct(step.stage_probability)}% confidence</small></div>)}
                </div>
              </div>
            </section>

            <section className="three-column">
              <div className="panel activity-panel"><div className="section-title"><Gauge size={16} /> NETWORK SIGNALS</div><div className="metric-list">{telemetryItems.map(([label, value, sub]) => <div className="metric-row" key={label}><div><span>{label}</span><small>{sub}</small></div><strong>{value}</strong></div>)}</div><button className="text-button" onClick={() => setActiveTab('details')}>View all telemetry <ArrowRight size={14} /></button></div>
              <div className="panel why-panel"><div className="section-title"><Bot size={16} /> WHY THE AI IS WARNING</div><div className="driver-list">{drivers.length ? drivers.map((d, i) => <div className="driver" key={d.name || i}><span>{i + 1}</span><div><strong>{d.name}</strong><small>{d.is_positive === false ? 'reduces predicted risk' : 'increases predicted risk'}</small></div><b>{d.is_positive === false ? '' : '+'}{Number(d.attribution_score || 0).toFixed(2)}</b></div>) : <p className="muted">Feature attribution will appear after the forecast runs.</p>}</div><button className="text-button" onClick={() => setShowDetails(!showDetails)}>{showDetails ? 'Hide explanation' : 'Show explanation'} {showDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</button></div>
              <div className="panel action-panel"><div className="section-title"><Zap size={16} /> RECOMMENDED ACTION</div><div className="action-copy"><CheckCircle2 size={19} /><p>{narrative?.recommended_action || 'Continue monitoring the current ingress traffic and prepare containment controls.'}</p></div><button className="btn btn-primary" onClick={() => setIsReportOpen(true)}>Open incident response <ArrowRight size={15} /></button><div className="action-note">AI recommendation • human approval required</div></div>
            </section>

            {showDetails && <section className="explanation-strip panel"><strong>Model reasoning</strong><span>{narrative?.incident_summary || explanation?.summary_text || 'The model combines temporal network features across recent windows to forecast the next attack stage.'}</span></section>}

            <div className="simulation-row"><PlaybackControls replayStatus={replayStatus} onPlay={handlePlay} onPause={handlePause} onStep={handleStep} onSpeedChange={handleSpeedChange} onReset={handleReset} speed={playbackSpeed} /></div>
          </>
        )}

        {activeTab === 'topology' && <div className="secondary-view"><NetworkMap currentStage={currentStage} predictedStage={next.predicted_stage || 'Normal'} telemetry={telemetry} /><TrajectoryForecast forecastData={forecastData} activeModel={activeModel} /></div>}

        {activeTab === 'details' && <div className="secondary-view"><TelemetryGauges telemetry={telemetry} replayStatus={replayStatus} /><ExplainabilityPanel explanation={explanation} activeModel={activeModel} /><TrajectoryForecast forecastData={forecastData} activeModel={activeModel} /></div>}
      </main>

      <footer className="app-footer"><div><Shield size={14} /> <strong>AegisFlow</strong> • SIH26153</div><span>AI-based network attack forecasting</span><span>Time-aware • Multi-step • Explainable</span></footer>

      <MitreMatrixModal isOpen={isMitreOpen} onClose={() => setIsMitreOpen(false)} mitreMatrix={mitreMatrix} currentStage={currentStage} predictedStage={next.predicted_stage || 'Normal'} />
      <BenchmarkModal isOpen={isBenchmarkOpen} onClose={() => setIsBenchmarkOpen(false)} modelsData={modelsData} onRetrainCompleted={loadInitialData} />
      <UploadModal isOpen={isUploadOpen} onClose={() => setIsUploadOpen(false)} onUploadSuccess={handleUploadSuccess} />
      <IncidentReportModal isOpen={isReportOpen} onClose={() => setIsReportOpen(false)} forecastData={forecastData} telemetry={telemetry} explanation={explanation} replayStatus={replayStatus} activeModel={activeModel} />
    </div>
  );
}
