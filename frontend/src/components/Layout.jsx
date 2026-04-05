// File: frontend/src/components/Layout.jsx
import Sidebar from './Sidebar'
import Navbar from './Navbar'

export default function Layout({ children }) {
  const layoutStyle = {
    display: 'flex',
    minHeight: '100vh',
    background: '#0f172a',
    color: '#f1f5f9',
    fontFamily: 'Inter, sans-serif'
  };

  const mainStyle = {
    flex: 1,
    marginLeft: '260px',
    marginTop: '64px',
    padding: '32px',
    transition: 'margin 0.3s ease'
  };

  return (
    <div style={layoutStyle} className="app-layout min-h-screen bg-gray-900 flex">
      <Sidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Navbar />
        <main style={mainStyle} className="main-content flex-1 p-8">
          {children}
        </main>
      </div>
    </div>
  )
}
