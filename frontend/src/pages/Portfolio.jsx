import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext'
import api from '../services/api'
import { User, Edit3, Save, Plus, Trash2, ExternalLink, X } from 'lucide-react'

export default function Portfolio() {
  const { user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [editData, setEditData] = useState({ bio: '', skills: '', github_url: '', linkedin_url: '' })
  const [showAddProject, setShowAddProject] = useState(false)
  const [newProject, setNewProject] = useState({ title: '', description: '', technologies: '', url: '' })

  useEffect(() => {
    loadPortfolio()
  }, [])

  const loadPortfolio = async () => {
    try {
      const res = await api.get('/api/portfolio/me')
      setProfile(res.data.profile || res.data)
      setProjects(res.data.projects || [])
    } catch {}
    setLoading(false)
  }

  const saveProfile = async () => {
    try {
      await api.put('/api/portfolio/me', {
        ...editData,
        skills: editData.skills.split(',').map(s => s.trim()).filter(Boolean),
      })
      setEditing(false)
      loadPortfolio()
    } catch {}
  }

  const addProject = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/portfolio/projects', {
        ...newProject,
        technologies: newProject.technologies.split(',').map(s => s.trim()).filter(Boolean),
      })
      setShowAddProject(false)
      setNewProject({ title: '', description: '', technologies: '', url: '' })
      loadPortfolio()
    } catch {}
  }

  const deleteProject = async (id) => {
    if (!confirm('Delete this project?')) return
    try {
      await api.delete(`/api/portfolio/projects/${id}`)
      loadPortfolio()
    } catch {}
  }

  const startEditing = () => {
    setEditData({
      bio: profile?.bio || '',
      skills: (profile?.skills || []).join(', '),
      github_url: profile?.github_url || '',
      linkedin_url: profile?.linkedin_url || '',
    })
    setEditing(true)
  }

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-page"><div className="loading-spinner" /><p>Loading portfolio...</p></div>
      </div>
    )
  }

  return (
    <div className="page-container">
      {/* Profile Header */}
      <div className="portfolio-header">
        <div style={{
          width: 80, height: 80, borderRadius: '50%',
          background: 'var(--gradient-primary)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 1rem', fontSize: '2rem', fontWeight: 700, color: 'white',
        }}>
          {user?.username?.[0]?.toUpperCase() || 'U'}
        </div>
        <h1>{user?.full_name || user?.username}</h1>
        <p>{profile?.bio || 'Cybersecurity enthusiast and learner'}</p>
        <div className="skill-badges">
          {(profile?.skills || ['Security', 'Python', 'Networking']).map((skill, i) => (
            <span key={i} className="badge badge-cyan">{skill}</span>
          ))}
        </div>
        <div style={{ marginTop: '1rem', display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
          <button className="btn btn-secondary btn-sm" onClick={startEditing}>
            <Edit3 size={14} /> Edit Profile
          </button>
        </div>
      </div>

      {/* Edit Modal */}
      {editing && (
        <div className="modal-overlay" onClick={() => setEditing(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0 }}>Edit Profile</h2>
              <button className="btn btn-ghost btn-icon" onClick={() => setEditing(false)}><X size={18} /></button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="input-group">
                <label>Bio</label>
                <textarea className="input" placeholder="Tell us about yourself"
                  value={editData.bio} onChange={(e) => setEditData({ ...editData, bio: e.target.value })} />
              </div>
              <div className="input-group">
                <label>Skills (comma separated)</label>
                <input className="input" placeholder="Python, Network Security, Pen Testing"
                  value={editData.skills} onChange={(e) => setEditData({ ...editData, skills: e.target.value })} />
              </div>
              <div className="input-group">
                <label>GitHub URL</label>
                <input className="input" placeholder="https://github.com/username"
                  value={editData.github_url} onChange={(e) => setEditData({ ...editData, github_url: e.target.value })} />
              </div>
              <div className="input-group">
                <label>LinkedIn URL</label>
                <input className="input" placeholder="https://linkedin.com/in/username"
                  value={editData.linkedin_url} onChange={(e) => setEditData({ ...editData, linkedin_url: e.target.value })} />
              </div>
              <div className="modal-actions">
                <button className="btn btn-secondary" onClick={() => setEditing(false)}>Cancel</button>
                <button className="btn btn-primary" onClick={saveProfile}><Save size={14} /> Save</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Projects */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Projects</h2>
        <button className="btn btn-primary btn-sm" onClick={() => setShowAddProject(true)}>
          <Plus size={14} /> Add Project
        </button>
      </div>

      {/* Add Project Modal */}
      {showAddProject && (
        <div className="modal-overlay" onClick={() => setShowAddProject(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0 }}>Add Project</h2>
              <button className="btn btn-ghost btn-icon" onClick={() => setShowAddProject(false)}><X size={18} /></button>
            </div>
            <form onSubmit={addProject} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="input-group">
                <label>Project Title</label>
                <input className="input" placeholder="My Security Tool" required
                  value={newProject.title} onChange={(e) => setNewProject({ ...newProject, title: e.target.value })} />
              </div>
              <div className="input-group">
                <label>Description</label>
                <textarea className="input" placeholder="What does this project do?"
                  value={newProject.description} onChange={(e) => setNewProject({ ...newProject, description: e.target.value })} />
              </div>
              <div className="input-group">
                <label>Technologies (comma separated)</label>
                <input className="input" placeholder="Python, FastAPI, React"
                  value={newProject.technologies} onChange={(e) => setNewProject({ ...newProject, technologies: e.target.value })} />
              </div>
              <div className="input-group">
                <label>Project URL (optional)</label>
                <input className="input" placeholder="https://github.com/..."
                  value={newProject.url} onChange={(e) => setNewProject({ ...newProject, url: e.target.value })} />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddProject(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Add Project</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {projects.length === 0 && (
        <div className="empty-state">
          <User size={48} />
          <h3>No projects yet</h3>
          <p>Showcase your cybersecurity projects and achievements.</p>
        </div>
      )}

      <div className="grid-2">
        {projects.map((project, i) => (
          <div key={project.id || i} className="card animate-fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--cyan-400)' }}>{project.title}</h3>
              <div style={{ display: 'flex', gap: '0.25rem' }}>
                {project.url && (
                  <a href={project.url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-icon btn-sm">
                    <ExternalLink size={14} />
                  </a>
                )}
                <button className="btn btn-ghost btn-icon btn-sm" onClick={() => deleteProject(project.id)}
                  style={{ color: 'var(--red-400)' }}>
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', margin: '0.5rem 0' }}>
              {project.description}
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
              {(project.technologies || []).map((tech, j) => (
                <span key={j} className="badge badge-purple" style={{ fontSize: '0.6875rem' }}>{tech}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
