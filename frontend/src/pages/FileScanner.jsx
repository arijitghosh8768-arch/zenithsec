import { useState, useRef } from 'react'
import api from '../services/api'
import { FileSearch, Upload, ShieldCheck, ShieldAlert, AlertTriangle, Loader2 } from 'lucide-react'

export default function FileScanner() {
  const [file, setFile] = useState(null)
  const [results, setResults] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [error, setError] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef(null)

  const scanFile = async (fileToScan) => {
    if (!fileToScan) return
    setScanning(true)
    setError('')
    setResults(null)
    const formData = new FormData()
    formData.append('file', fileToScan)
    try {
      const res = await api.post('/api/file-scanner/scan', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResults(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to scan file')
    } finally {
      setScanning(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) {
      setFile(dropped)
      scanFile(dropped)
    }
  }

  const handleSelect = (e) => {
    const selected = e.target.files[0]
    if (selected) {
      setFile(selected)
      scanFile(selected)
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / 1048576).toFixed(1) + ' MB'
  }

  const getRiskLevel = (score) => {
    if (score >= 80) return { level: 'critical', label: 'Critical' }
    if (score >= 60) return { level: 'high', label: 'High Risk' }
    if (score >= 30) return { level: 'medium', label: 'Medium' }
    return { level: 'low', label: 'Clean' }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>📄 File Scanner</h1>
        <p>Upload files for malware detection and security analysis</p>
      </div>

      <div className="scanner-container">
        {/* Drop Zone */}
        <div
          className={`drop-zone ${dragOver ? 'dragover' : ''}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          style={{ marginBottom: '2rem' }}
        >
          <Upload size={40} style={{ color: 'var(--cyan-400)', marginBottom: '0.5rem' }} />
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.375rem' }}>
            Drop a file here or click to browse
          </h3>
          <p>Supports all file types up to 50MB</p>
          <input ref={inputRef} type="file" onChange={handleSelect} style={{ display: 'none' }} />
        </div>

        {error && <div className="auth-error" style={{ marginBottom: '1.5rem' }}>{error}</div>}

        {scanning && (
          <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
            <div className="loading-spinner" />
            <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>
              Scanning <strong>{file?.name}</strong>...
            </p>
          </div>
        )}

        {results && !scanning && (
          <div className="scan-results animate-fade-in">
            {/* File Info + Risk */}
            <div className="card">
              <div className="risk-indicator">
                <div className={`risk-circle ${getRiskLevel(results.risk_score || 0).level}`}>
                  {results.risk_score || 0}
                  <span>{getRiskLevel(results.risk_score || 0).label}</span>
                </div>
                <div>
                  <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '0.375rem' }}>
                    {file?.name || 'Uploaded File'}
                  </h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>
                    Size: {file ? formatSize(file.size) : 'N/A'} • Type: {file?.type || 'Unknown'}
                  </p>
                </div>
              </div>
            </div>

            {/* Hashes */}
            {results.hashes && (
              <div className="card">
                <h3 className="card-title" style={{ marginBottom: '0.75rem' }}>🔑 File Hashes</h3>
                {Object.entries(results.hashes).map(([algo, hash]) => (
                  <div key={algo} style={{ marginBottom: '0.5rem' }}>
                    <p className="text-xs text-muted" style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}>{algo}</p>
                    <p className="font-mono text-sm" style={{ wordBreak: 'break-all', color: 'var(--text-secondary)' }}>{hash}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Threats */}
            {results.threats && results.threats.length > 0 && (
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">⚠️ Detected Issues</h3>
                  <span className="badge badge-red">{results.threats.length}</span>
                </div>
                <div className="threat-list">
                  {results.threats.map((t, i) => (
                    <div key={i} className="threat-item">
                      <span className={`threat-severity ${t.severity || 'medium'}`}>
                        {(t.severity || 'MEDIUM').toUpperCase()}
                      </span>
                      <span>{t.description || t}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(!results.threats || results.threats.length === 0) && (results.risk_score || 0) < 30 && (
              <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
                <ShieldCheck size={48} style={{ color: 'var(--green-400)', marginBottom: '0.75rem' }} />
                <h3 style={{ color: 'var(--green-400)', marginBottom: '0.5rem' }}>File Appears Clean</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                  No malware signatures or suspicious patterns were detected.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
