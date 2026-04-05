import { useState, useEffect } from 'react'
import api from '../services/api'
import { BookOpen, Clock, Award, ChevronRight, Loader2, Star } from 'lucide-react'

export default function LearningHub() {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    api.get('/api/learning/courses')
      .then(res => setCourses(res.data.courses || res.data || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const difficultyColor = {
    beginner: 'badge-green',
    intermediate: 'badge-amber',
    advanced: 'badge-red',
  }

  const categoryColor = {
    'network-security': 'badge-cyan',
    'web-security': 'badge-purple',
    'cryptography': 'badge-blue',
    'malware-analysis': 'badge-red',
    'ethical-hacking': 'badge-amber',
  }

  const filteredCourses = filter === 'all'
    ? courses
    : courses.filter(c => c.difficulty === filter || c.category === filter)

  const filters = ['all', 'beginner', 'intermediate', 'advanced']

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>📚 Learning Hub</h1>
        <p>Master cybersecurity through structured courses and hands-on labs</p>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        {filters.map(f => (
          <button
            key={f}
            className={`btn ${filter === f ? 'btn-primary' : 'btn-secondary'} btn-sm`}
            onClick={() => setFilter(f)}
            style={{ textTransform: 'capitalize' }}
          >
            {f}
          </button>
        ))}
      </div>

      {loading && (
        <div className="loading-page">
          <div className="loading-spinner" />
          <p>Loading courses...</p>
        </div>
      )}

      {!loading && filteredCourses.length === 0 && (
        <div className="empty-state">
          <BookOpen size={48} />
          <h3>No courses found</h3>
          <p>Try a different filter or check back later for new content.</p>
        </div>
      )}

      <div className="course-grid">
        {filteredCourses.map((course, i) => (
          <div key={course.id || i} className="card course-card" style={{ animationDelay: `${i * 0.05}s` }}>
            <div className="course-meta">
              <span className={`badge ${difficultyColor[course.difficulty] || 'badge-cyan'}`}>
                {course.difficulty || 'Beginner'}
              </span>
              <span className={`badge ${categoryColor[course.category] || 'badge-blue'}`}>
                {(course.category || 'general').replace('-', ' ')}
              </span>
            </div>
            <h3>{course.title}</h3>
            <p>{course.description}</p>
            <div className="course-footer">
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span className="text-sm text-muted" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <Clock size={14} /> {course.duration || '2h'}
                </span>
                <span className="text-sm text-muted" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <BookOpen size={14} /> {course.lessons || 8} lessons
                </span>
              </div>
              <button className="btn btn-ghost btn-sm" style={{ color: 'var(--cyan-400)' }}>
                Start <ChevronRight size={14} />
              </button>
            </div>

            {/* Progress bar */}
            {course.progress > 0 && (
              <div style={{ marginTop: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <span className="text-xs text-muted">Progress</span>
                  <span className="text-xs text-cyan">{course.progress}%</span>
                </div>
                <div style={{
                  height: 4, borderRadius: 2,
                  background: 'var(--bg-input)',
                }}>
                  <div style={{
                    height: '100%', borderRadius: 2,
                    background: 'var(--gradient-primary)',
                    width: `${course.progress}%`,
                    transition: 'width 0.5s ease',
                  }} />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
