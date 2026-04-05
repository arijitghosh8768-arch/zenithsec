import { useState, useEffect } from 'react'
import api from '../services/api'
import { Code2, Plus, FolderGit2, GitBranch, Trash2, File, Clock, X } from 'lucide-react'

export default function CodeVault() {
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [newRepo, setNewRepo] = useState({ name: '', description: '', language: 'python' })
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    loadRepos()
  }, [])

  const loadRepos = async () => {
    try {
      const res = await api.get('/api/code/repos')
      setRepos(res.data.repositories || res.data || [])
    } catch {}
    setLoading(false)
  }

  const createRepo = async (e) => {
    e.preventDefault()
    setCreating(true)
    try {
      await api.post('/api/code/repos', newRepo)
      setShowCreate(false)
      setNewRepo({ name: '', description: '', language: 'python' })
      loadRepos()
    } catch {}
    setCreating(false)
  }

  const deleteRepo = async (id) => {
    if (!confirm('Delete this repository?')) return
    try {
      await api.delete(`/api/code/repos/${id}`)
      setRepos(prev => prev.filter(r => r.id !== id))
    } catch {}
  }

  const langColors = {
    python: '#3572A5',
    javascript: '#f1e05a',
    rust: '#dea584',
    go: '#00ADD8',
    java: '#b07219',
    cpp: '#f34b7d',
  }

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>💻 Code Vault</h1>
          <p>Manage your security projects and code repositories</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={16} /> New Repository
        </button>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0 }}>Create Repository</h2>
              <button className="btn btn-ghost btn-icon" onClick={() => setShowCreate(false)}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={createRepo} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="input-group">
                <label>Repository Name</label>
                <input className="input" placeholder="my-security-tool" required
                  value={newRepo.name} onChange={(e) => setNewRepo({ ...newRepo, name: e.target.value })} />
              </div>
              <div className="input-group">
                <label>Description</label>
                <textarea className="input" placeholder="What does this project do?"
                  value={newRepo.description} onChange={(e) => setNewRepo({ ...newRepo, description: e.target.value })} />
              </div>
              <div className="input-group">
                <label>Language</label>
                <select className="input" value={newRepo.language}
                  onChange={(e) => setNewRepo({ ...newRepo, language: e.target.value })}>
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="rust">Rust</option>
                  <option value="go">Go</option>
                  <option value="java">Java</option>
                  <option value="cpp">C++</option>
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={creating}>
                  {creating ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {loading && (
        <div className="loading-page">
          <div className="loading-spinner" />
          <p>Loading repositories...</p>
        </div>
      )}

      {!loading && repos.length === 0 && (
        <div className="empty-state">
          <FolderGit2 size={48} />
          <h3>No repositories yet</h3>
          <p>Create your first repository to start building security tools.</p>
          <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={() => setShowCreate(true)}>
            <Plus size={16} /> Create Repository
          </button>
        </div>
      )}

      <div className="repo-list">
        {repos.map((repo, i) => (
          <div key={repo.id || i} className="card repo-item animate-fade-in" style={{ animationDelay: `${i * 0.05}s` }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <h3>{repo.name}</h3>
                {repo.language && (
                  <span className="badge" style={{
                    background: `${langColors[repo.language] || '#666'}20`,
                    color: langColors[repo.language] || '#999',
                  }}>
                    <span style={{
                      width: 8, height: 8, borderRadius: '50%',
                      background: langColors[repo.language] || '#999',
                      display: 'inline-block', marginRight: '0.375rem',
                    }} />
                    {repo.language}
                  </span>
                )}
              </div>
              <p>{repo.description || 'No description'}</p>
              <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                <span className="text-xs text-muted" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <File size={12} /> {repo.files_count || 0} files
                </span>
                <span className="text-xs text-muted" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <GitBranch size={12} /> {repo.commits_count || 0} commits
                </span>
                <span className="text-xs text-muted" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <Clock size={12} /> {repo.updated_at ? new Date(repo.updated_at).toLocaleDateString() : 'Recently'}
                </span>
              </div>
            </div>
            <button className="btn btn-danger btn-sm btn-icon" onClick={() => deleteRepo(repo.id)}>
              <Trash2 size={16} />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
