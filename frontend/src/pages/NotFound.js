import React from 'react';
import { Link } from 'react-router-dom';

function NotFound() {
  return (
    <div style={{ maxWidth: 700, margin: '0 auto', padding: 24, textAlign: 'center' }}>
      <h2 style={{ color: '#204b72' }}>Page not found</h2>
      <p style={{ color: '#5f6b7a' }}>The page you were looking for doesn’t exist.</p>
      <Link to="/" style={{ color: '#3a6ea5', fontWeight: 700 }}>Go home</Link>
    </div>
  );
}

export default NotFound;


