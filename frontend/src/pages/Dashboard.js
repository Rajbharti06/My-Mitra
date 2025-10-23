import React, { useMemo } from 'react';
import './Dashboard.css';
import MoodRing from '../components/MoodRing';
import { Link } from 'react-router-dom';

function Dashboard() {
  const userName = useMemo(() => localStorage.getItem('username') || 'Friend', []);
  const hours = new Date().getHours();
  const greetingPrefix = hours < 12 ? 'Good Morning' : hours < 18 ? 'Good Afternoon' : 'Good Evening';

  return (
    <div className="dashboard">
      <h2 className="greeting">{greetingPrefix}, {userName} 🌞</h2>
      <p className="subtext">Let’s make today meaningful.</p>

      <div className="cards">
        <div className="card mood-ring-card">
          <MoodRing emotion="calm" size={80} animate={true} showLabel={true} />
          <div>
            <h3>Mood ring</h3>
            <p style={{ color: 'var(--text-secondary)', margin: 0 }}>Gentle snapshot of how you’re feeling.</p>
          </div>
        </div>

        <div className="card">
          <h3>Today’s Journal</h3>
          <p style={{ color: 'var(--text-secondary)' }}>Write a short reflection to start your day.</p>
          <div className="cta"><Link to="/journals">Open Journal</Link></div>
        </div>

        <div className="card">
          <h3>Habit Progress</h3>
          <div style={{ display: 'grid', gap: 10 }}>
            <Progress label="Study 2 hrs" value={0.6} />
            <Progress label="Meditation" value={0.4} />
            <Progress label="Evening Walk" value={0.2} />
          </div>
        </div>

        <div className="card quote-card">
          <h3>Quote of the day</h3>
          <p style={{ fontStyle: 'italic', marginBottom: 8 }}>
            “Build through the fall.”
          </p>
          <p style={{ color: 'var(--text-secondary)', margin: 0 }}>— Hacktober theme</p>
        </div>
      </div>

      <div className="cta" style={{ marginTop: 20 }}>
        <Link to="/chat">Talk to Mitra</Link>
      </div>
    </div>
  );
}

function Progress({ label, value }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ color: 'var(--text-primary)' }}>{label}</span>
        <span style={{ color: 'var(--text-secondary)' }}>{Math.round(value * 100)}%</span>
      </div>
      <div style={{ height: 10, background: 'var(--bg-secondary)', borderRadius: 24, border: '1px solid var(--mm-border)' }}>
        <div style={{ height: '100%', width: `${value * 100}%`, background: 'var(--mm-primary)', borderRadius: 24, transition: 'width 0.3s ease' }} />
      </div>
    </div>
  );
}

export default Dashboard;