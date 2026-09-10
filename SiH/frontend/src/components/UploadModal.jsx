import React, { useState } from 'react';
import { X, UploadCloud, FileText, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { uploadDataset } from '../api/client';

export default function UploadModal({ isOpen, onClose, onUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setErrorMsg('');
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setIsUploading(true);
      setErrorMsg('');
      const res = await uploadDataset(selectedFile);
      setUploadResult(res);
      setIsUploading(false);
      if (onUploadSuccess) onUploadSuccess(res);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to upload and parse file.');
      setIsUploading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '650px' }}>
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <UploadCloud size={20} color="var(--accent-cyan)" />
            <h2 className="font-display" style={{ fontSize: '1.1rem', color: 'var(--text-primary)', letterSpacing: '0.05em' }}>
              Upload Network Telemetry & PCAP Logs
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px' }}
          >
            <X size={20} />
          </button>
        </div>

        <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Upload raw network flow captures (CIC-IDS2017, UNSW-NB15, PCAP / CSV). The pipeline automatically computes 24 dense behavioral metrics, aggregates them into 10s temporal windows, and loads the stream for live trajectory forecasting.
          </p>

          {/* Drag & Drop Box */}
          <label style={{
            border: '2px dashed var(--border-color)',
            borderRadius: 'var(--radius-lg)',
            padding: '30px 20px',
            textAlign: 'center',
            cursor: 'pointer',
            background: 'rgba(236, 227, 209, 0.5)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '10px',
            transition: 'all 0.2s ease'
          }}>
            <input
              type="file"
              accept=".pcap,.pcapng,.csv,.json"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <FileText size={36} color="var(--accent-cyan)" style={{ opacity: 0.8 }} />
            <div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                {selectedFile ? selectedFile.name : 'Click to select or drag & drop files'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Supports .CSV, .PCAP, .PCAPNG, .JSON (Max 100MB)
              </div>
            </div>
          </label>

          {errorMsg && (
            <div style={{ background: 'rgba(179, 57, 44, 0.1)', border: '1px solid rgba(179, 57, 44, 0.2)', borderRadius: 'var(--radius-md)', padding: '10px 14px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-danger)', fontSize: '0.8rem' }}>
              <AlertCircle size={16} />
              <span>{errorMsg}</span>
            </div>
          )}

          {uploadResult && (
            <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 'var(--radius-md)', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '4px', color: 'var(--accent-emerald)', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
                <CheckCircle size={16} /> Dataset Ingested Successfully!
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                Extracted {uploadResult.window_count || 0} temporal 10s windows. Replay buffer ready.
              </div>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
            <button className="btn btn-outline" onClick={onClose}>
              Close
            </button>
            <button
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={!selectedFile || isUploading}
            >
              {isUploading ? <RefreshCw size={14} className="spinning" /> : <UploadCloud size={14} />}
              {isUploading ? 'Parsing & Windowing...' : 'Upload & Launch Simulation'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
