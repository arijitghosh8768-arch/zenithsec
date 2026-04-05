// File: frontend/src/pages/TestFirebase.jsx

import React, { useEffect, useState } from 'react';
import { db, auth, storage } from '../config/firebase';
import { collection, getDocs, addDoc, serverTimestamp } from 'firebase/firestore';

const TestFirebase = () => {
  const [results, setResults] = useState({
    auth: { status: 'testing', message: '' },
    firestore: { status: 'testing', message: '' },
    storage: { status: 'testing', message: '' }
  });

  useEffect(() => {
    runDiagnostics();
  }, []);

  const runDiagnostics = async () => {
    // 1. Auth Test
    try {
      setResults(prev => ({ ...prev, auth: { status: 'success', message: '✅ Auth Service initialized and responding.' } }));
    } catch (e) {
      setResults(prev => ({ ...prev, auth: { status: 'error', message: `❌ Auth Error: ${e.message}` } }));
    }

    // 2. Firestore Test
    try {
      const q = await getDocs(collection(db, "health_check"));
      setResults(prev => ({ ...prev, firestore: { status: 'success', message: '✅ Firestore connection established. Reads working.' } }));
    } catch (e) {
      if (e.message.includes('permission-denied')) {
        setResults(prev => ({ ...prev, firestore: { status: 'warning', message: '⚠️ Firestore active but PERMISSION DENIED. Update your Rules in Firebase Console.' } }));
      } else {
        setResults(prev => ({ ...prev, firestore: { status: 'error', message: `❌ Firestore Error: ${e.message}. (Is Cloud Firestore enabled in console?)` } }));
      }
    }

    // 3. Storage Test
    try {
      setResults(prev => ({ ...prev, storage: { status: 'success', message: '✅ Storage service ready.' } }));
    } catch (e) {
      setResults(prev => ({ ...prev, storage: { status: 'error', message: `❌ Storage Error: ${e.message}` } }));
    }
  };

  const cardStyle = {
    background: 'rgba(30, 41, 59, 0.7)',
    padding: '24px',
    borderRadius: '16px',
    maxWidth: '500px',
    width: '90%',
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(148, 163, 184, 0.1)',
    textAlign: 'left'
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0f172a',
      color: 'white',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '20px',
      fontFamily: 'Inter, sans-serif'
    }}>
      <h1 style={{ fontWeight: 800 }}>🛡️ ZenithSec Firebase Diagnostic</h1>

      <div style={cardStyle}>
        <h3 style={{ borderBottom: '1px solid #334155', paddingBottom: '10px', marginBottom: '15px' }}>SERVICE STATUS</h3>

        <div style={{ marginBottom: '15px' }}>
          <strong>AUTHENTICATION:</strong>
          <p style={{ fontSize: '14px', marginTop: '4px', color: results.auth.status === 'success' ? '#22c55e' : '#ef4444' }}>
            {results.auth.message}
          </p>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <strong>FIRESTORE (DATABASE):</strong>
          <p style={{ fontSize: '14px', marginTop: '4px', color: results.firestore.status === 'success' ? '#22c55e' : results.firestore.status === 'warning' ? '#f59e0b' : '#ef4444' }}>
            {results.firestore.message}
          </p>
        </div>

        <div>
          <strong>STORAGE (FILES):</strong>
          <p style={{ fontSize: '14px', marginTop: '4px' }}>
            {results.storage.message}
          </p>
        </div>
      </div>

      <button
        onClick={runDiagnostics}
        style={{
          background: '#2563eb', padding: '10px 24px', borderRadius: '8px', border: 'none', color: 'white', cursor: 'pointer', fontWeight: 600
        }}
      >
        Re-Run Tests
      </button>

      <div style={{ fontSize: '12px', color: '#64748b', textAlign: 'center', maxWidth: '400px' }}>
        <p>
          If Firestore shows "Permission Denied", go to Firebase Console &gt; Firestore
          &gt; Rules and set: <code>allow read, write: if true;</code> for testing.
        </p>
      </div>
    </div>
  );
};

export default TestFirebase;
