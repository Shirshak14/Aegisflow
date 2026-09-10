/**
 * AegisFlow API Client
 * Handles communication with the FastAPI backend.
 */

const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch('/health');
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchLatestForecast() {
  const res = await fetch(`${API_BASE}/forecast/latest`);
  if (!res.ok) throw new Error('Failed to fetch forecast');
  return res.json();
}

export async function fetchScenarios() {
  const res = await fetch(`${API_BASE}/scenarios`);
  if (!res.ok) throw new Error('Failed to fetch scenarios');
  return res.json();
}

export async function setScenario(scenarioName) {
  const res = await fetch(`${API_BASE}/replay/scenario?name=${encodeURIComponent(scenarioName)}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to switch scenario');
  return res.json();
}

export async function startReplay(speed = 1.0) {
  const res = await fetch(`${API_BASE}/replay/start?speed=${speed}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to start replay');
  return res.json();
}

export async function pauseReplay() {
  const res = await fetch(`${API_BASE}/replay/pause`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to pause replay');
  return res.json();
}

export async function stepReplay() {
  const res = await fetch(`${API_BASE}/replay/step`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to step replay');
  return res.json();
}

export async function setPlaybackSpeed(speed) {
  const res = await fetch(`${API_BASE}/replay/speed?speed=${speed}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to set replay speed');
  return res.json();
}

export async function resetReplay() {
  const res = await fetch(`${API_BASE}/replay/reset`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to reset replay');
  return res.json();
}

export async function fetchModels() {
  const res = await fetch(`${API_BASE}/models`);
  if (!res.ok) throw new Error('Failed to fetch models');
  return res.json();
}

export async function setActiveModel(modelName) {
  const res = await fetch(`${API_BASE}/models/active`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_name: modelName })
  });
  if (!res.ok) throw new Error('Failed to set active model');
  return res.json();
}

export async function trainModels(epochs = 15, batchSize = 32) {
  const res = await fetch(`${API_BASE}/models/train`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ epochs, batch_size: batchSize })
  });
  if (!res.ok) throw new Error('Failed to trigger training');
  return res.json();
}

export async function fetchTrainingStatus() {
  const res = await fetch(`${API_BASE}/models/training-status`);
  if (!res.ok) throw new Error('Failed to fetch training status');
  return res.json();
}

export async function fetchMitreMatrix() {
  const res = await fetch(`${API_BASE}/mitre`);
  if (!res.ok) throw new Error('Failed to fetch MITRE matrix');
  return res.json();
}

export async function uploadDataset(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/datasets/upload`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) throw new Error('Failed to upload dataset');
  return res.json();
}
