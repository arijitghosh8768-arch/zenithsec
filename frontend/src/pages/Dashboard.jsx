// File: frontend/src/pages/Dashboard.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { MessageSquare, Shield, BookOpen, Award } from 'lucide-react';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const features = [
    { icon: MessageSquare, title: 'AI Mentor', description: 'Get personalized cybersecurity guidance', path: '/chat', color: '#3b82f6' },
    { icon: Shield, title: 'Security Scanner', description: 'Scan URLs and files for threats', path: '/url-scanner', color: '#22c55e' },
    { icon: BookOpen, title: 'Learning Hub', description: 'Access courses and resources', path: '/learning', color: '#8b5cf6' },
    { icon: Award, title: 'Certificates', description: 'Earn verified certificates', path: '/certificates', color: '#f59e0b' },
  ];

  const headerBoxStyle = {
    marginBottom: '32px'
  };

  const statsGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '24px',
    marginBottom: '32px'
  };

  const statCardStyle = {
    background: '#1e293b',
    padding: '24px',
    borderRadius: '16px',
    border: '1px solid rgba(148, 163, 184, 0.1)',
    textAlign: 'left'
  };

  const featureGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '24px'
  };

  const featureButtonStyle = (color) => ({
    background: '#1e293b',
    padding: '24px',
    borderRadius: '16px',
    border: '1px solid rgba(148, 163, 184, 0.1)',
    textAlign: 'left',
    cursor: 'pointer',
    transition: 'transform 0.2s, border-color 0.2s',
    outline: 'none',
    color: 'inherit'
  });

  return (
    <div style={{ color: '#f1f5f9' }}>
      <div style={headerBoxStyle}>
        <h1 style={{ fontSize: '30px', fontWeight: 800, color: 'white', marginBottom: '8px' }}>
          Welcome back, {user?.username || 'Cyber Sentinel'}!
        </h1>
        <p style={{ color: '#94a3b8' }}>Your AI-powered cybersecurity learning journey continues...</p>
      </div>

      {/* Stats Cards */}
      <div style={statsGridStyle} className="dashboard-stats">
        <div style={statCardStyle}>
          <div style={{ fontSize: '24px', marginBottom: '8px' }}>📚</div>
          <div style={{ fontWeight: 700, fontSize: '20px' }}>5</div>
          <div style={{ color: '#94a3b8', fontSize: '12px' }}>Courses Completed</div>
        </div>
        <div style={statCardStyle}>
          <div style={{ fontSize: '24px', marginBottom: '8px' }}>🎯</div>
          <div style={{ fontWeight: 700, fontSize: '20px' }}>12</div>
          <div style={{ color: '#94a3b8', fontSize: '12px' }}>Challenges Solved</div>
        </div>
        <div style={statCardStyle}>
          <div style={{ fontSize: '24px', marginBottom: '8px' }}>🏆</div>
          <div style={{ fontWeight: 700, fontSize: '20px' }}>3</div>
          <div style={{ color: '#94a3b8', fontSize: '12px' }}>Certificates Earned</div>
        </div>
        <div style={statCardStyle}>
          <div style={{ fontSize: '24px', marginBottom: '8px' }}>🔥</div>
          <div style={{ fontWeight: 700, fontSize: '20px' }}>7</div>
          <div style={{ color: '#94a3b8', fontSize: '12px' }}>Day Streak</div>
        </div>
      </div>

      {/* Features Grid */}
      <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px', color: 'white' }}>Quick Access</h2>
      <div style={featureGridStyle} className="dashboard-features">
        {features.map((feature, index) => (
          <button
            key={index}
            onClick={() => navigate(feature.path)}
            style={featureButtonStyle(feature.color)}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = feature.color;
              e.currentTarget.style.transform = 'translateY(-4px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'rgba(148, 163, 184, 0.1)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <div style={{ 
              background: feature.color, 
              width: '48px', height: '48px', 
              borderRadius: '12px', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              marginBottom: '16px'
            }}>
              <feature.icon size={24} color="white" />
            </div>
            <h3 style={{ fontWeight: 700, marginBottom: '8px', color: 'white' }}>{feature.title}</h3>
            <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.5 }}>{feature.description}</p>
          </button>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
