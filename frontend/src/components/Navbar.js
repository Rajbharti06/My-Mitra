import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';

function Navbar({ darkMode, setDarkMode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthed = localStorage.getItem('token') !== null;

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <nav style={{
      position: 'sticky', top: 0, zIndex: 10,
      background: '#ffffff', borderBottom: '1px solid #e6e9ef',
      padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Link to="/" style={{ textDecoration: 'none' }}>
          <span style={{ color: '#3a6ea5', fontWeight: 800, fontSize: 20 }}>MyMitra</span>
        </Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginLeft: 8 }}>
          <Link to="/chat" style={linkStyle(location.pathname === '/chat')}>Chat</Link>
          {isAuthed && <Link to="/journals" style={linkStyle(location.pathname === '/journals')}>Journals</Link>}
          {isAuthed && <Link to="/habits" style={linkStyle(location.pathname === '/habits')}>Habits</Link>}
          {isAuthed && <Link to="/insights" style={linkStyle(location.pathname === '/insights')}>Insights</Link>}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <button 
          onClick={() => setDarkMode(!darkMode)}
          style={{
            background: 'transparent',
            border: '1px solid #cdd6e1',
            borderRadius: 8,
            padding: '8px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {darkMode ? '☀️' : '🌙'}
        </button>
        {!isAuthed ? (
          <>
            <Link to="/login" style={buttonGhost}>Log in</Link>
            <Link to="/register" style={buttonPrimary}>Get started</Link>
          </>
        ) : (
          <button onClick={handleLogout} style={buttonGhost}>Log out</button>
        )}
      </div>
    </nav>
  );
}

const linkStyle = (active) => ({
  color: active ? '#3a6ea5' : '#5f6b7a',
  textDecoration: 'none',
  fontWeight: active ? 700 : 500,
  padding: '6px 8px',
  borderRadius: 8,
  background: active ? '#e8f0fb' : 'transparent'
});

const buttonPrimary = {
  color: '#fff',
  background: '#3a6ea5',
  borderRadius: 10,
  padding: '8px 12px',
  textDecoration: 'none',
  fontWeight: 700
};

const buttonGhost = {
  color: '#3a6ea5',
  background: 'transparent',
  border: '1px solid #cdd6e1',
  borderRadius: 10,
  padding: '8px 12px',
  textDecoration: 'none',
  fontWeight: 700
};

export default Navbar;


