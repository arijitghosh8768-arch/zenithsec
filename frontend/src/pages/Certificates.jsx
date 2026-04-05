import { useState, useEffect } from 'react'
import api from '../services/api'
import { Award, Search, ShieldCheck, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'

export default function Certificates() {
  const [certs, setCerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [verifyHash, setVerifyHash] = useState('')
  const [verifyResult, setVerifyResult] = useState(null)
  const [verifying, setVerifying] = useState(false)

  useEffect(() => {
    api.get('/api/certificates/mine')
      .then(res => setCerts(res.data.certificates || res.data || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const verifyCert = async () => {
    if (!verifyHash.trim()) return
    setVerifying(true)
    setVerifyResult(null)
    try {
      const res = await api.post('/api/certificates/verify', { certificate_hash: verifyHash.trim() })
      setVerifyResult(res.data)
    } catch (err) {
      setVerifyResult({ valid: false, message: err.response?.data?.detail || 'Verification failed' })
    }
    setVerifying(false)
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>🏆 Certificates</h1>
        <p>Your earned certificates secured by blockchain verification</p>
      </div>

      {/* Verify Section */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3 className="card-title" style={{ marginBottom: '1rem' }}>🔍 Verify Certificate</h3>
        <div className="scanner-input-group">
          <input
            className="input"
            placeholder="Enter certificate hash to verify..."
            value={verifyHash}
            onChange={(e) => setVerifyHash(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && verifyCert()}
            style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.8125rem' }}
          />
          <button className="btn btn-primary" onClick={verifyCert} disabled={verifying || !verifyHash.trim()}>
            {verifying ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            Verify
          </button>
        </div>

        {verifyResult && (
          <div className="animate-fade-in" style={{
            marginTop: '1rem', padding: '1rem',
            background: verifyResult.valid ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            border: `1px solid ${verifyResult.valid ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            borderRadius: 'var(--radius-sm)',
            display: 'flex', alignItems: 'center', gap: '0.75rem',
          }}>
            {verifyResult.valid
              ? <CheckCircle2 size={20} style={{ color: 'var(--green-400)' }} />
              : <AlertCircle size={20} style={{ color: 'var(--red-400)' }} />}
            <div>
              <p style={{
                fontWeight: 600, fontSize: '0.875rem',
                color: verifyResult.valid ? 'var(--green-400)' : 'var(--red-400)',
              }}>
                {verifyResult.valid ? 'Certificate Verified ✓' : 'Verification Failed'}
              </p>
              <p className="text-sm text-secondary">{verifyResult.message || ''}</p>
            </div>
          </div>
        )}
      </div>

      {/* Certificates */}
      {loading && (
        <div className="loading-page"><div className="loading-spinner" /><p>Loading certificates...</p></div>
      )}

      {!loading && certs.length === 0 && (
        <div className="empty-state">
          <Award size={48} />
          <h3>No certificates yet</h3>
          <p>Complete courses and challenges to earn blockchain-verified certificates.</p>
        </div>
      )}

      <div className="grid-3">
        {certs.map((cert, i) => (
          <div key={cert.id || i} className="cert-card animate-fade-in" style={{ animationDelay: `${i * 0.1}s` }}>
            <div style={{
              width: 56, height: 56, borderRadius: '50%',
              background: 'rgba(6, 182, 212, 0.15)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 1rem',
            }}>
              <Award size={28} style={{ color: 'var(--cyan-400)' }} />
            </div>
            <h3>{cert.title || cert.course_name || 'Certificate'}</h3>
            <p className="cert-id">ID: {cert.id || 'N/A'}</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', textAlign: 'left' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-xs text-muted">Issued</span>
                <span className="text-xs">{cert.issued_at ? new Date(cert.issued_at).toLocaleDateString() : 'N/A'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-xs text-muted">Status</span>
                <span className="badge badge-green" style={{ fontSize: '0.625rem' }}>
                  <ShieldCheck size={10} style={{ marginRight: '0.25rem' }} /> Verified
                </span>
              </div>
            </div>
            {cert.blockchain_hash && (
              <div className="cert-hash">
                {cert.blockchain_hash}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
