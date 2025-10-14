import React from 'react';
import { Link } from 'react-router-dom';

function Home() {
  const isAuthed = localStorage.getItem('token') !== null;
  return (
    <div style={{ width: '100%', background: 'linear-gradient(180deg, #f7fbff 0%, #ffffff 100%)' }}>
      <section style={{ maxWidth: 1100, margin: '0 auto', padding: '64px 20px', textAlign: 'center' }}>
        <h1 style={{ fontSize: 44, margin: 0, color: '#204b72', letterSpacing: -0.5 }}>Feel calmer, one small step at a time</h1>
        <p style={{ fontSize: 18, color: '#5f6b7a', marginTop: 16 }}>A friendly AI mentor that listens, reflects, and helps you grow. Private by design.</p>
        <div style={{ marginTop: 24, display: 'flex', gap: 12, justifyContent: 'center' }}>
          {isAuthed ? (
            <Link to="/chat" style={primaryBtn}>Open Chat</Link>
          ) : (
            <>
              <Link to="/register" style={primaryBtn}>Get started</Link>
              <Link to="/login" style={ghostBtn}>Log in</Link>
            </>
          )}
        </div>
      </section>
      <section style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 20px 64px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
          {features.map((f) => (
            <div key={f.title} style={card}>
              <div style={{ fontSize: 28 }}>{f.emoji}</div>
              <h3 style={{ margin: '8px 0 4px', color: '#204b72' }}>{f.title}</h3>
              <p style={{ margin: 0, color: '#5f6b7a' }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

const features = [
  { emoji: '🤗', title: 'Human-like support', desc: 'Conversational, kind, and relatable tone.' },
  { emoji: '🔒', title: 'Privacy-first', desc: 'Your data is encrypted. Only you can read it.' },
  { emoji: '⚡', title: 'Fast and local', desc: 'Prefers local models for speed and safety.' },
  { emoji: '🧠', title: 'Simple CBT', desc: 'Evidence-based nudges to help reframe and act.' }
];

const primaryBtn = {
  background: '#3a6ea5', color: '#fff', padding: '12px 16px', borderRadius: 12,
  textDecoration: 'none', fontWeight: 700
};

const ghostBtn = {
  background: 'transparent', color: '#3a6ea5', padding: '12px 16px', borderRadius: 12,
  textDecoration: 'none', fontWeight: 700, border: '1px solid #cdd6e1'
};

const card = {
  background: '#ffffff', border: '1px solid #e6e9ef', borderRadius: 16, padding: 16
};

export default Home;


