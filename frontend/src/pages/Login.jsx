// File: frontend/src/pages/Login.jsx

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    skillLevel: 'beginner'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login, register } = useAuth();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
        navigate('/dashboard');
      } else {
        await register(
          formData.username,
          formData.email,
          formData.password,
          formData.skillLevel
        );
        navigate('/dashboard');
      }
    } catch (err) {
      const detail = err.response?.data?.detail || err.message;
      setError(Array.isArray(detail) ? detail[0].msg : detail);
    } finally {
      setLoading(false);
    }
  };

  // Premium Fallback Styles
  const containerStyle = {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '20px',
    fontFamily: 'Inter, sans-serif'
  };

  const cardStyle = {
    background: 'rgba(30, 41, 59, 0.7)',
    backdropFilter: 'blur(12px)',
    padding: '40px',
    borderRadius: '24px',
    width: '100%',
    maxWidth: '400px',
    border: '1px solid rgba(148, 163, 184, 0.1)',
    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
  };

  const inputStyle = {
    width: '100%',
    padding: '12px 16px',
    background: '#334155',
    border: '1px solid #475569',
    borderRadius: '12px',
    color: 'white',
    marginTop: '8px',
    marginBottom: '20px',
    outline: 'none',
    transition: 'all 0.2s'
  };

  return (
    <div style={containerStyle} className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center p-4">
      <div style={cardStyle} className="bg-gray-800/50 backdrop-blur-sm p-8 rounded-2xl shadow-2xl w-full max-w-md border border-gray-700">
        <div className="text-center mb-8">
          <div style={{ fontSize: '64px', marginBottom: '12px' }} className="text-5xl mb-3">🛡️</div>
          <h1 style={{ color: 'white', fontSize: '32px', fontWeight: 800 }} className="text-3xl font-bold text-white">ZenithSec</h1>
          <p style={{ color: '#94a3b8', fontSize: '14px' }} className="text-gray-400 mt-2">AI-Powered Cybersecurity Mentor</p>
        </div>

        {error && (
          <div style={{ 
            background: 'rgba(239, 68, 68, 0.1)', 
            border: '1px solid #ef4444', 
            padding: '12px', 
            borderRadius: '12px', 
            marginBottom: '20px' 
          }} className="bg-red-900/30 border border-red-500 rounded-lg p-3 mb-4">
            <p style={{ color: '#fca5a5', fontSize: '13px' }} className="text-red-200 text-sm">
              {error}
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <div className="mb-4">
              <label style={{ color: '#cbd5e1', fontSize: '13px' }}>Username</label>
              <input
                style={inputStyle}
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                required={!isLogin}
                placeholder="johndoe"
              />
            </div>
          )}

          <div className="mb-4">
            <label style={{ color: '#cbd5e1', fontSize: '13px' }}>Email</label>
            <input
              style={inputStyle}
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="you@example.com"
            />
          </div>

          <div className="mb-4">
            <label style={{ color: '#cbd5e1', fontSize: '13px' }}>Password</label>
            <input
              style={inputStyle}
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="••••••••"
            />
          </div>

          {!isLogin && (
            <div className="mb-6">
              <label style={{ color: '#cbd5e1', fontSize: '13px' }}>Experience Level</label>
              <select
                style={inputStyle}
                name="skillLevel"
                value={formData.skillLevel}
                onChange={handleChange}
              >
                <option value="beginner">🌱 Beginner</option>
                <option value="intermediate">📚 Intermediate</option>
                <option value="advanced">🚀 Advanced</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '14px',
              background: '#2563eb',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: '0 10px 15px -3px rgba(37, 99, 235, 0.3)'
            }}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
            }}
            style={{ background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer', fontSize: '13px' }}
            className="text-blue-400 hover:text-blue-300 text-sm transition"
          >
            {isLogin ? "Don't have an account? Create one" : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
