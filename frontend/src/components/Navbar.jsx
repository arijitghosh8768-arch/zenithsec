// File: frontend/src/components/Navbar.jsx
import { useAuth } from '../context/AuthContext'
import { LogOut, Bell, Search, User } from 'lucide-react'
import { useState } from 'react'

export default function Navbar() {
  const { user, logout } = useAuth()
  const [showDropdown, setShowDropdown] = useState(false)

  const headerStyle = {
    position: 'fixed',
    top: 0,
    left: '260px',
    right: 0,
    height: '64px',
    background: 'rgba(17, 24, 39, 0.8)',
    backdropFilter: 'blur(12px)',
    borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 24px',
    zIndex: 40,
    fontFamily: 'Inter, sans-serif'
  };

  return (
    <header style={headerStyle}>
      {/* Search */}
      <div style={{
        display: 'flex', alignItems: 'center',
        background: '#1f2937',
        border: '1px solid rgba(148, 163, 184, 0.1)',
        borderRadius: '8px',
        padding: '6px 12px',
        width: '320px',
      }}>
        <Search size={16} style={{ color: '#94a3b8', marginRight: '8px' }} />
        <input
          type="text"
          placeholder="Search ZenithSec..."
          style={{
            background: 'transparent', border: 'none', outline: 'none',
            color: '#f1f5f9', fontSize: '13px', width: '100%',
          }}
        />
      </div>

      {/* Right section */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', position: 'relative' }}>
          <Bell size={18} />
          <span style={{
            position: 'absolute', top: 0, right: 0,
            width: '8px', height: '8px',
            background: '#22d3ee',
            borderRadius: '50%',
          }} />
        </button>

        {/* User dropdown */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              background: '#1e293b', border: '1px solid rgba(148, 163, 184, 0.1)',
              borderRadius: '8px', padding: '6px 12px',
              cursor: 'pointer', color: '#f1f5f9',
              fontSize: '13px',
            }}
          >
            <div style={{
              width: '28px', height: '28px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'white', fontSize: '12px', fontWeight: 600,
            }}>
              {user?.username?.[0]?.toUpperCase() || 'U'}
            </div>
            <span>{user?.username || 'User'}</span>
          </button>

          {showDropdown && (
            <div style={{
              position: 'absolute', top: '100%', right: 0, marginTop: '8px',
              background: '#111827', border: '1px solid rgba(148, 163, 184, 0.1)',
              borderRadius: '8px', padding: '8px',
              minWidth: '180px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)', zIndex: 100,
            }}>
              <div style={{ padding: '8px 12px', borderBottom: '1px solid rgba(148, 163, 184, 0.1)', marginBottom: '8px' }}>
                <p style={{ fontSize: '13px', fontWeight: 600, color: 'white' }}>{user?.username}</p>
                <p style={{ fontSize: '12px', color: '#94a3b8' }}>{user?.email}</p>
              </div>
              <button
                onClick={() => { logout(); setShowDropdown(false); }}
                style={{
                  display: 'flex', alignItems: 'center', gap: '8px',
                  width: '100%', padding: '8px 12px',
                  background: 'transparent', border: 'none',
                  color: '#f87171', cursor: 'pointer',
                  fontSize: '13px', borderRadius: '4px',
                  textAlign: 'left'
                }}
              >
                <LogOut size={16} /> Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
