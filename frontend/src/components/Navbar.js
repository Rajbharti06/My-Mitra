import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';

function Navbar({ darkMode, setDarkMode }) {
  const location = useLocation();

  return (
    <nav className="nav">
      <div className="nav-inner">
        <div className="nav-group">
          <Link to="/" className="brand">MyMitra</Link>
          <div className="nav-links">
            <Link to="/chat" className={`nav-link ${location.pathname === '/chat' ? 'active' : ''}`}>Chat</Link>
            <Link to="/journals" className={`nav-link ${location.pathname === '/journals' ? 'active' : ''}`}>Journals</Link>
            <Link to="/habits" className={`nav-link ${location.pathname === '/habits' ? 'active' : ''}`}>Habits</Link>
            <Link to="/insights" className={`nav-link ${location.pathname === '/insights' ? 'active' : ''}`}>Insights</Link>
            <li>
              <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>Home</Link>
            </li>
          </div>
        </div>
        <div className="nav-actions">
          <button 
            onClick={() => setDarkMode(!darkMode)}
            className="theme-toggle"
            aria-label="Toggle dark mode"
          >
            {darkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;


