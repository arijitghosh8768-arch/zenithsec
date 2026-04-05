import { useState, useEffect, useRef } from 'react'
import api from '../services/api'
import { BarChart3, TrendingUp, Activity, Calendar } from 'lucide-react'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, RadialLinearScale, ArcElement, Title, Tooltip, Legend, Filler } from 'chart.js'
import { Bar, Radar, Line } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, RadialLinearScale, ArcElement, Title, Tooltip, Legend, Filler)

export default function Analytics() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/api/analytics/dashboard').catch(() => ({ data: null })),
      api.get('/api/analytics/skills').catch(() => ({ data: null })),
      api.get('/api/analytics/activity').catch(() => ({ data: null })),
    ]).then(([dash, skills, activity]) => {
      setData({
        dashboard: dash.data,
        skills: skills.data,
        activity: activity.data,
      })
    }).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-page"><div className="loading-spinner" /><p>Loading analytics...</p></div>
      </div>
    )
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1a2235',
        borderColor: 'rgba(148, 163, 184, 0.2)',
        borderWidth: 1,
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
        padding: 12,
        cornerRadius: 8,
      },
    },
    scales: {
      x: {
        ticks: { color: '#64748b', font: { size: 11 } },
        grid: { color: 'rgba(148, 163, 184, 0.05)' },
      },
      y: {
        ticks: { color: '#64748b', font: { size: 11 } },
        grid: { color: 'rgba(148, 163, 184, 0.05)' },
      },
    },
  }

  const activityData = {
    labels: data?.activity?.labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [{
      label: 'Activity',
      data: data?.activity?.data || [3, 5, 2, 8, 4, 6, 7],
      backgroundColor: 'rgba(6, 182, 212, 0.3)',
      borderColor: '#06b6d4',
      borderWidth: 2,
      borderRadius: 6,
    }],
  }

  const skillsData = {
    labels: data?.skills?.labels || ['Networking', 'Web Security', 'Cryptography', 'Forensics', 'Malware', 'OSINT'],
    datasets: [{
      label: 'Skill Level',
      data: data?.skills?.data || [70, 85, 60, 45, 55, 75],
      backgroundColor: 'rgba(168, 85, 247, 0.2)',
      borderColor: '#a855f7',
      borderWidth: 2,
      pointBackgroundColor: '#a855f7',
    }],
  }

  const progressData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [{
      label: 'Score',
      data: data?.dashboard?.progress || [20, 35, 45, 55, 70, 82],
      borderColor: '#06b6d4',
      backgroundColor: 'rgba(6, 182, 212, 0.1)',
      fill: true,
      tension: 0.4,
      borderWidth: 2,
      pointRadius: 4,
      pointBackgroundColor: '#06b6d4',
    }],
  }

  const stats = data?.dashboard?.stats || {}

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>📊 Analytics</h1>
        <p>Track your cybersecurity learning progress and activity</p>
      </div>

      {/* Quick Stats */}
      <div className="grid-4" style={{ marginBottom: '2rem' }}>
        {[
          { label: 'Security Score', value: stats.security_score || 82, icon: TrendingUp, color: 'cyan' },
          { label: 'Streak Days', value: stats.streak_days || 7, icon: Activity, color: 'amber' },
          { label: 'Completed', value: stats.completed_lessons || 24, icon: BarChart3, color: 'green' },
          { label: 'Certificates', value: stats.certificates || 3, icon: Calendar, color: 'purple' },
        ].map((s, i) => (
          <div key={i} className="card stat-card">
            <div className={`stat-icon ${s.color}`}><s.icon size={22} /></div>
            <div className="stat-info">
              <h3>{s.value}</h3>
              <p>{s.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid-2" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '1rem' }}>📈 Security Score Progress</h3>
          <div style={{ height: 280 }}>
            <Line data={progressData} options={{
              ...chartOptions,
              scales: {
                ...chartOptions.scales,
                y: { ...chartOptions.scales.y, min: 0, max: 100 },
              },
            }} />
          </div>
        </div>

        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '1rem' }}>🎯 Skill Radar</h3>
          <div style={{ height: 280 }}>
            <Radar data={skillsData} options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: { legend: { display: false } },
              scales: {
                r: {
                  beginAtZero: true,
                  max: 100,
                  ticks: { display: false },
                  pointLabels: { color: '#94a3b8', font: { size: 11 } },
                  grid: { color: 'rgba(148, 163, 184, 0.1)' },
                  angleLines: { color: 'rgba(148, 163, 184, 0.1)' },
                },
              },
            }} />
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="card-title" style={{ marginBottom: '1rem' }}>📅 Weekly Activity</h3>
        <div style={{ height: 280 }}>
          <Bar data={activityData} options={chartOptions} />
        </div>
      </div>
    </div>
  )
}
