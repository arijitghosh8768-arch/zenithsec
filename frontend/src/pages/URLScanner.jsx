import { useState } from 'react'
import api from '../services/api'
import { Globe, Search, ShieldCheck, ShieldAlert, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react'

export default function URLScanner() {
  const [url, setUrl] = useState('')
  const [results, setResults] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [error, setError] = useState('')

  const scanURL = async () => {
    if (!url.trim()) return
    setScanning(true)
    setError('')
    setResults(null)
    try {
      const res = await api.post('/api/url-scanner/scan', { url: url.trim() })
      setResults(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to scan URL')
    } finally {
      setScanning(false)
    }
  }

  const getRiskLevel = (score) => {
    if (score >= 80) return { level: 'critical', label: 'Critical', icon: ShieldAlert }
    if (score >= 60) return { level: 'high', label: 'High Risk', icon: ShieldAlert }
    if (score >= 30) return { level: 'medium', label: 'Medium', icon: AlertTriangle }
    return { level: 'low', label: 'Safe', icon: ShieldCheck }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>🌐 URL Scanner</h1>
        <p>Analyze URLs for potential security threats, phishing, and malware</p>
      </div>

      <div className="scanner-container">
        {/* Search */}
        <div className="scanner-input-group">
          <input
            className="input"
            placeholder="Enter URL to scan (e.g., https://example.com)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && scanURL()}
          />
          <button className="btn btn-primary" onClick={scanURL} disabled={scanning || !url.trim()}>
            {scanning ? <Loader2 size={18} className="animate-spin" /> : <Search size={18} />}
            {scanning ? 'Scanning...' : 'Scan'}
          </button>
        </div>

        {error && <div className="auth-error" style={{ marginBottom: '1.5rem' }}>{error}</div>}

        {scanning && (
          <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
            <div className="loading-spinner" />
            <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>Analyzing URL security...</p>
          </div>
        )}

        {results && !scanning && (
          <div className="scan-results animate-fade-in">
            {/* Risk Score */}
            <div className="card">
              <div className="risk-indicator">
                <div className={`risk-circle ${getRiskLevel(results.risk_score || 0).level}`}>
                  {results.risk_score || 0}
                  <span>{getRiskLevel(results.risk_score || 0).label}</span>
                </div>
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                    {results.url || url}
                  </h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    Scanned at {new Date().toLocaleString()}
                  </p>
                </div>
              </div>
            </div>

            {/* SSL Info */}
            {results.ssl_info && (
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">🔒 SSL Certificate</h3>
                  <span className={`badge ${results.ssl_info.valid ? 'badge-green' : 'badge-red'}`}>
                    {results.ssl_info.valid ? 'Valid' : 'Invalid'}
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  {results.ssl_info.issuer && (
                    <div>
                      <p className="text-sm text-muted">Issuer</p>
                      <p className="text-sm">{results.ssl_info.issuer}</p>
                    </div>
                  )}
                  {results.ssl_info.expires && (
                    <div>
                      <p className="text-sm text-muted">Expires</p>
                      <p className="text-sm">{results.ssl_info.expires}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Threats */}
            {results.threats && results.threats.length > 0 && (
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">⚠️ Detected Threats</h3>
                  <span className="badge badge-red">{results.threats.length} found</span>
                </div>
                <div className="threat-list">
                  {results.threats.map((threat, i) => (
                    <div key={i} className="threat-item">
                      <span className={`threat-severity ${threat.severity || 'medium'}`}>
                        {threat.severity || 'MEDIUM'}
                      </span>
                      <span>{threat.description || threat}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Safe message */}
            {(!results.threats || results.threats.length === 0) && (results.risk_score || 0) < 30 && (
              <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
                <CheckCircle2 size={48} style={{ color: 'var(--green-400)', marginBottom: '0.75rem' }} />
                <h3 style={{ color: 'var(--green-400)', marginBottom: '0.5rem' }}>URL Appears Safe</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                  No significant threats detected. Always exercise caution when visiting unfamiliar sites.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Empty state */}
        {!results && !scanning && !error && (
          <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <Globe size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
            <h3 style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Enter a URL to scan</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', maxWidth: 400, margin: '0 auto' }}>
              Our scanner checks SSL certificates, domain reputation, known phishing databases, and suspicious patterns.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
