// File: frontend/src/App.jsx

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import URLScanner from './pages/URLScanner';
import FileScanner from './pages/FileScanner';
import LearningHub from './pages/LearningHub';
import CodeVault from './pages/CodeVault';
import Portfolio from './pages/Portfolio';
import Analytics from './pages/Analytics';
import Certificates from './pages/Certificates';
import TestFirebase from './pages/TestFirebase';

// Layout
import Layout from './components/Layout';

// Protected Route wrapper
const ProtectedRoute = ({ children }) => {
  const { user, loading, isAuthenticated } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="loading-spinner mb-4 border-4 border-blue-500 border-t-transparent rounded-full w-12 h-12 animate-spin mx-auto" />
          <p className="mt-4 font-mono">AUTHENTICATING ZENITHSEC...</p>
        </div>
      </div>
    );
  }
  
  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/test-firebase" element={<TestFirebase />} />
        
        {/* Protected Routes */}
        <Route path="/" element={
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        } />
        
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        } />
        
        <Route path="/chat" element={
          <ProtectedRoute>
            <Chat />
          </ProtectedRoute>
        } />

        <Route path="/url-scanner" element={
          <ProtectedRoute>
            <Layout>
              <URLScanner />
            </Layout>
          </ProtectedRoute>
        } />

        <Route path="/file-scanner" element={
          <ProtectedRoute>
            <Layout>
              <FileScanner />
            </Layout>
          </ProtectedRoute>
        } />

        <Route path="/learning" element={
          <ProtectedRoute>
            <Layout>
              <LearningHub />
            </Layout>
          </ProtectedRoute>
        } />

        <Route path="/code-vault" element={
          <ProtectedRoute>
            <Layout>
              <CodeVault />
            </Layout>
          </ProtectedRoute>
        } />

        <Route path="/portfolio" element={
          <ProtectedRoute>
            <Layout>
              <Portfolio />
            </Layout>
          </ProtectedRoute>
        } />

        <Route path="/analytics" element={
          <ProtectedRoute>
            <Layout>
              <Analytics />
            </Layout>
          </ProtectedRoute>
        } />

        <Route path="/certificates" element={
          <ProtectedRoute>
            <Layout>
              <Certificates />
            </Layout>
          </ProtectedRoute>
        } />

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
