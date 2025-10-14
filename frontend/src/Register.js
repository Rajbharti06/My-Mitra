import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        navigate('/login');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to register');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
      <div style={{ background: '#fff', border: '1px solid #e6e9ef', borderRadius: 16, padding: 24, marginTop: 40, width: '100%', maxWidth: 420 }}>
        <h2 style={{ marginTop: 0, color: '#204b72' }}>Create account</h2>
        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 12 }}>
          <div style={{ display: 'grid', gap: 6 }}>
            <label style={{ color: '#5f6b7a', fontSize: 14 }}>Username</label>
            <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} required style={input} />
          </div>
          <div style={{ display: 'grid', gap: 6 }}>
            <label style={{ color: '#5f6b7a', fontSize: 14 }}>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required style={input} />
          </div>
          {error && <p style={{ color: '#c0392b', margin: 0 }}>{error}</p>}
          <button type="submit" style={button}>Register</button>
        </form>
      </div>
    </div>
  );
}

export default Register;

const input = {
  padding: '10px 12px', borderRadius: 10, border: '1px solid #cdd6e1'
};
const button = {
  padding: '10px 14px', borderRadius: 10, border: '1px solid #3a6ea5', background: '#3a6ea5', color: '#fff', fontWeight: 700, marginTop: 4
};
