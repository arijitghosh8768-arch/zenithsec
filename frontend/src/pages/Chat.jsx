// File: frontend/src/pages/Chat.jsx

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import '../styles/chat.css';

// ── Constants ──

const SESSION_KEY = 'zs_active_session';

const HINTS = [
  'What is SQL injection?',
  'Explain XSS to me',
  'How does a buffer overflow work?',
  'Cybersecurity roadmap for beginners',
  'What is a reverse shell?',
  'Best CTF platforms to practice',
];

// ── Helpers ──

const stamp = () =>
  new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

const md = (text) => {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`\n]+)`/g, '<code>$1</code>')
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" class="zc-link">$1</a>')
    .replace(/^▸\s(.+)/gm, "<span class='zc-li'>▸ $1</span>")
    .replace(/\n/g, '<br/>');
};

// ── Component ──

const Chat = () => {
  const navigate = useNavigate();

  // State
  const [messages, setMessages]       = useState([]);
  const [input, setInput]             = useState('');
  const [mode, setMode]               = useState('normal');
  const [loading, setLoading]         = useState(false);
  const [status, setStatus]           = useState('connecting');
  const [sessions, setSessions]       = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Refs
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  // ── Load sessions on mount ──

  useEffect(() => {
    loadSessions();
    checkBackendStatus();
  }, []);

  // ── Auto-scroll on new messages ──

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // ── Backend health check ──

  const checkBackendStatus = async () => {
    try {
      await api.get('/api/health');
      setStatus('online');
    } catch (err) {
      if (err.response?.status === 401) {
        setStatus('online');
      } else {
        setStatus('offline');
      }
    }
  };

  // ── Session management ──

  const loadSessions = async () => {
    try {
      const res = await api.get('/api/chatbot/sessions');
      setSessions(res.data || []);
      setStatus('online');
    } catch (err) {
      if (err.response?.status === 401) {
        setStatus('unauthorized');
        console.warn("User is unauthenticated. Please log in.");
      } else {
        setStatus('offline');
      }
    }
  };

  const loadSessionMessages = async (sessionId) => {
    try {
      const res = await api.get(`/api/chatbot/sessions/${sessionId}/history`);
      const history = res.data.messages || [];
      setMessages(
        history.map((m, i) => ({
          role: m.role,
          content: m.content,
          ts: new Date(m.created_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          id: `h${i}`,
        }))
      );
      setActiveSession(sessionId);
      localStorage.setItem(SESSION_KEY, sessionId);
    } catch {
      // silently fail
    }
  };

  const createNewSession = async (title) => {
    try {
      const res = await api.post('/api/chatbot/sessions', { title: title || 'New Chat' });
      const newSession = res.data;
      setSessions((prev) => [newSession, ...prev]);
      setActiveSession(newSession.session_id);
      setMessages([]);
      localStorage.setItem(SESSION_KEY, newSession.session_id);
      return newSession.session_id;
    } catch (err) {
      console.error("Failed to create session:", err);
      throw err; // Rethrow to let the caller handle it (e.g., 401 errors)
    }
  };

  const deleteSession = async (e, sessionId) => {
    e.stopPropagation();
    try {
      await api.delete(`/api/chatbot/sessions/${sessionId}`);
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      if (activeSession === sessionId) {
        setActiveSession(null);
        setMessages([]);
        localStorage.removeItem(SESSION_KEY);
      }
    } catch {
      // silently fail
    }
  };

  // ── Send message ──

  const send = useCallback(async (text) => {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;

    setInput('');
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: msg, ts: stamp(), id: Date.now() },
    ]);
    setLoading(true);

    try {
      // Create session if none active
      let sessionId = activeSession;
      if (!sessionId) {
        sessionId = await createNewSession(msg.slice(0, 40));
        if (!sessionId) throw new Error('Failed to create session');
      }

      const res = await api.post('/api/chatbot/chat', {
        message: msg,
        session_id: sessionId,
        context: { mode },
      });

      const reply = res.data.response || res.data.message || 'No response';

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: reply, ts: stamp(), id: Date.now() + 1 },
      ]);

      // Refresh sessions list (title may have updated)
      loadSessions();
    } catch (err) {
      let errorMsg = '❌ Cannot reach backend. Is the server running?';
      
      if (err.response?.status === 401) {
        errorMsg = '🔐 **Session Expired or Not Logged In.** Please [login](/login) to use the AI Mentor.';
      } else if (err.response?.data?.detail) {
        errorMsg = `⚠️ ${err.response.data.detail}`;
      } else if (err.message) {
        errorMsg = `❌ ${err.message}`;
      }

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: errorMsg, ts: stamp(), id: Date.now() + 1 },
      ]);
    }

    setLoading(false);
    setTimeout(() => inputRef.current?.focus(), 50);
  }, [input, loading, activeSession, mode]);

  // ── Clear current session ──

  const clearChat = async () => {
    if (activeSession) {
      try {
        await api.delete(`/api/chatbot/sessions/${activeSession}`);
        setSessions((prev) => prev.filter((s) => s.session_id !== activeSession));
      } catch {
        // silently fail
      }
    }
    setActiveSession(null);
    setMessages([]);
    localStorage.removeItem(SESSION_KEY);
  };

  // ── Keyboard handler ──

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  // ── Render ──

  return (
    <div className="zc-shell">
      {/* ── Sidebar ── */}
      <aside className={`zc-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="zc-brand">
          <span className="zc-dot-live" />
          <span className="zc-brand-name">ZENITHSEC</span>
        </div>
        <div className="zc-brand-sub">AI MENTOR · CHAT</div>

        {/* Back to Dashboard */}
        <button className="zc-back-btn" onClick={() => navigate('/dashboard')}>
          ← DASHBOARD
        </button>

        {/* AI Mode */}
        <div className="zc-sec-label">AI MODE</div>
        {['normal', 'hacker', 'mentor'].map((m) => (
          <button
            key={m}
            className={`zc-mode-btn ${mode === m ? 'active' : ''}`}
            onClick={() => setMode(m)}
          >
            <span className="zc-mode-icon">
              {m === 'normal' ? '◈' : m === 'hacker' ? '💀' : '◎'}
            </span>
            {m.toUpperCase()}
          </button>
        ))}

        {/* New Chat */}
        <div className="zc-sec-label" style={{ marginTop: 16 }}>SESSIONS</div>
        <button className="zc-new-session-btn" onClick={() => createNewSession()}>
          + NEW CHAT
        </button>

        {/* Session List */}
        <div className="zc-session-list">
          {sessions.map((s) => (
            <button
              key={s.session_id || s.id}
              className={`zc-session-item ${activeSession === s.session_id ? 'active' : ''}`}
              onClick={() => loadSessionMessages(s.session_id)}
            >
              <span className="zc-session-title">{s.title || 'Untitled'}</span>
              <span
                className="zc-session-del"
                onClick={(e) => deleteSession(e, s.session_id)}
              >
                ✕
              </span>
            </button>
          ))}
        </div>

        {/* Quick Asks */}
        <div className="zc-sec-label" style={{ marginTop: 12 }}>QUICK ASKS</div>
        {HINTS.map((h, i) => (
          <button key={i} className="zc-hint-btn" onClick={() => send(h)}>
            ▸ {h}
          </button>
        ))}

        {/* Footer */}
        <div className="zc-sidebar-footer" title={status === 'unauthorized' ? 'Server is online but authentication is required' : ''}>
          <div className={`zc-status-dot ${status}`} />
          <span className="zc-status-txt">
            {status === 'online' ? 'System Online' : 
             status === 'unauthorized' ? 'Auth Required' : 
             status === 'connecting' ? 'Connecting...' : 'Backend Offline'}
          </span>
        </div>
      </aside>

      {/* ── Main Panel ── */}
      <div className="zc-main">
        {/* Topbar */}
        <div className="zc-topbar">
          <button className="zc-mobile-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            ☰
          </button>
          <span className="zc-topbar-title">
            CHAT <span className="zc-topbar-mode">[{mode}]</span>
          </span>
          <button className="zc-clear-btn" onClick={clearChat}>
            ⟳ CLEAR
          </button>
        </div>

        {/* Messages */}
        <div className="zc-messages">
          {messages.length === 0 && !loading && (
            <div className="zc-empty">
              <div className="zc-empty-logo">⬡</div>
              <div className="zc-empty-title">ZENITHSEC ONLINE</div>
              <div className="zc-empty-sub">
                AI Mentor · Chat interface ready<br />
                Ask anything — cybersecurity, code, CTF, or general AI.
              </div>
            </div>
          )}

          {messages.map((m) => (
            <div key={m.id} className={`zc-msg zc-msg-${m.role}`}>
              <div className="zc-msg-head">
                <span className={`zc-msg-av ${m.role}`}>
                  {m.role === 'user' ? '◈' : '⬡'}
                </span>
                <span className={`zc-msg-name ${m.role}`}>
                  {m.role === 'user' ? 'YOU' : 'ZENITHSEC'}
                </span>
                <span className="zc-msg-ts">{m.ts}</span>
              </div>
              <div
                className="zc-msg-body"
                dangerouslySetInnerHTML={{ __html: md(m.content) }}
              />
            </div>
          ))}

          {loading && (
            <div className="zc-msg zc-msg-assistant">
              <div className="zc-msg-head">
                <span className="zc-msg-av assistant">⬡</span>
                <span className="zc-msg-name assistant">ZENITHSEC</span>
                <span className="zc-msg-ts">thinking…</span>
              </div>
              <div className="zc-msg-body">
                <span className="zc-dot" />
                <span className="zc-dot" />
                <span className="zc-dot" />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="zc-input-bar">
          <span className="zc-prompt">›</span>
          <textarea
            ref={inputRef}
            className="zc-input"
            placeholder="Ask ZenithSec anything… (Enter to send)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKey}
            rows={1}
          />
          <button
            className="zc-send-btn"
            onClick={() => send()}
            disabled={loading || !input.trim()}
          >
            ⌤
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chat;
