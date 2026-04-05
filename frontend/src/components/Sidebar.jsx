// File: frontend/src/components/Sidebar.jsx
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, MessageSquare, Globe, FileSearch,
  BookOpen, Code2, Award, BarChart3, User, Shield
} from 'lucide-react'

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/chat', icon: MessageSquare, label: 'AI Mentor' },
  { path: '/url-scanner', icon: Globe, label: 'URL Scanner' },
  { path: '/file-scanner', icon: FileSearch, label: 'File Scanner' },
  { path: '/learning', icon: BookOpen, label: 'Learning Hub' },
  { path: '/code-vault', icon: Code2, label: 'Code Vault' },
  { path: '/certificates', icon: Award, label: 'Certificates' },
  { path: '/analytics', icon: BarChart3, label: 'Analytics' },
  { path: '/portfolio', icon: User, label: 'Portfolio' },
]

export default function Sidebar() {
  const location = useLocation()

  const sidebarStyle = {
    width: '260px',
    height: '100vh',
    position: 'fixed',
    top: 0,
    left: 0,
    background: '#111827',
    borderRight: '1px solid rgba(148, 163, 184, 0.1)',
    display: 'flex',
    flexDirection: 'column',
    zIndex: 50,
    overflowY: 'auto',
    fontFamily: 'Inter, sans-serif'
  };

  return (
    <aside style={sidebarStyle} className="w-64 h-screen bg-gray-900 border-r border-gray-800 flex flex-col">
      {/* Logo */}
      <div style={{ padding: '20px 24px', borderBottom: '1px solid rgba(148, 163, 184, 0.1)', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Shield size={20} color="white" />
        </div>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 800, color: 'white' }}>ZenithSec</h1>
          <p style={{ fontSize: '10px', color: '#64748b', letterSpacing: '0.05em' }}>CYBER PLATFORM</p>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path || (item.path === '/dashboard' && location.pathname === '/')
          return (
            <NavLink
              key={item.path}
              to={item.path}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 400,
                color: isActive ? '#22d3ee' : '#94a3b8',
                background: isActive ? 'rgba(6, 182, 212, 0.1)' : 'transparent',
                textDecoration: 'none',
                transition: 'all 0.2s'
              }}
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          )
        })}
      </nav>

      {/* Footer */}
      <div style={{ padding: '16px 24px', borderTop: '1px solid rgba(148, 163, 184, 0.1)', fontSize: '11px', color: '#64748b', textAlign: 'center' }}>
        ZenithSec v1.0.0
      </div>
    </aside>
  )
}
