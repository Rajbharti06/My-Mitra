import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import * as api from './services/api';

const WARM_ERRORS = {
  'Incorrect username or password': "That doesn't match what I remember. Try again?",
  'Username already registered': "That name is already taken — try another?",
  'Not authenticated': "I don't recognize those details. Want to try again?",
  'Login failed': "Something went wrong connecting. Try again?",
  'Registration failed': "I couldn't save your details. Try again?",
};

function humanizeError(msg = '') {
  return WARM_ERRORS[msg] || msg || "Something feels off. Let's try again.";
}

const GREETINGS = [
  'I remember you.',
  'You came back.',
  "I've been here.",
  'Good to see you.',
  'I was thinking of you.',
];

export default function AuthScreen({ onLogin }) {
  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [greeting] = useState(() => GREETINGS[Math.floor(Math.random() * GREETINGS.length)]);

  useEffect(() => {
    setError('');
  }, [mode]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      if (mode === 'register') {
        await api.register(username, password);
      }
      await api.login(username, password);
      onLogin();
    } catch (err) {
      setError(humanizeError(err.message));
    } finally {
      setLoading(false);
    }
  };

  const isLogin = mode === 'login';

  return (
    <div style={{ position: 'fixed', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      {/* Breathing background */}
      <div className="breathing-bg">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 28, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.7, ease: [0.4, 0, 0.2, 1] }}
        className="glass-elevated"
        style={{
          width: '100%',
          maxWidth: 380,
          padding: '2.5rem 2rem',
          borderRadius: 'var(--mm-radius-2xl)',
          position: 'relative',
          zIndex: 10,
          margin: '0 1rem',
        }}
      >
        {/* Pulsing presence orb */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.75rem' }}>
          <motion.div
            animate={{ scale: [1, 1.15, 1], opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
            style={{
              width: 52,
              height: 52,
              borderRadius: '50%',
              background: 'radial-gradient(circle at 40% 35%, rgba(139,92,246,0.9), rgba(59,130,246,0.7) 60%, rgba(59,130,246,0.2))',
              boxShadow: '0 0 32px rgba(139,92,246,0.35), 0 0 64px rgba(59,130,246,0.15)',
            }}
          />
        </div>

        {/* Heading — animates between login / register */}
        <AnimatePresence mode="wait">
          <motion.div
            key={mode}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.22 }}
            style={{ textAlign: 'center', marginBottom: '2rem' }}
          >
            <h1 style={{
              color: 'var(--mm-text-bright)',
              fontSize: '1.45rem',
              fontWeight: 600,
              letterSpacing: '-0.02em',
              margin: '0 0 0.35rem',
            }}>
              {isLogin ? 'Welcome back.' : 'Nice to meet you.'}
            </h1>
            <p style={{ color: 'var(--mm-text-muted)', fontSize: '0.82rem', margin: 0 }}>
              {isLogin ? greeting : "I'll remember everything you share with me."}
            </p>
          </motion.div>
        </AnimatePresence>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <label style={{ fontSize: '0.72rem', color: 'var(--mm-text-secondary)', fontWeight: 500, letterSpacing: '0.03em', textTransform: 'uppercase' }}>
              Username
            </label>
            <input
              className="input-glass"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="your name here"
              required
              autoFocus
              disabled={loading}
              autoComplete="username"
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <label style={{ fontSize: '0.72rem', color: 'var(--mm-text-secondary)', fontWeight: 500, letterSpacing: '0.03em', textTransform: 'uppercase' }}>
              Password
            </label>
            <input
              className="input-glass"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="keep it between us"
              required
              disabled={loading}
              autoComplete={isLogin ? 'current-password' : 'new-password'}
            />
          </div>

          <AnimatePresence>
            {error && (
              <motion.p
                initial={{ opacity: 0, y: -4, height: 0 }}
                animate={{ opacity: 1, y: 0, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
                style={{
                  color: 'var(--mm-emotion-anxious)',
                  fontSize: '0.8rem',
                  margin: 0,
                  textAlign: 'center',
                  lineHeight: 1.5,
                }}
              >
                {error}
              </motion.p>
            )}
          </AnimatePresence>

          <button
            type="submit"
            className="btn-glow"
            style={{
              marginTop: '0.4rem',
              padding: '0.85rem',
              fontSize: '0.9rem',
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              opacity: loading ? 0.7 : 1,
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
            disabled={loading}
          >
            {loading ? (
              <>
                <motion.span
                  animate={{ opacity: [1, 0.3, 1] }}
                  transition={{ duration: 1.2, repeat: Infinity }}
                  style={{ fontSize: '0.85rem' }}
                >
                  {isLogin ? 'stepping in' : 'beginning'}
                </motion.span>
                <motion.span
                  animate={{ opacity: [0.2, 1, 0.2] }}
                  transition={{ duration: 1.2, repeat: Infinity, delay: 0.4 }}
                >
                  ...
                </motion.span>
              </>
            ) : (
              isLogin ? 'Step in' : 'Begin our journey'
            )}
          </button>
        </form>

        {/* Mode toggle */}
        <p style={{
          textAlign: 'center',
          marginTop: '1.5rem',
          fontSize: '0.8rem',
          color: 'var(--mm-text-muted)',
          lineHeight: 1.6,
        }}>
          {isLogin ? "New here? " : "Already know me? "}
          <button
            type="button"
            onClick={() => setMode(isLogin ? 'register' : 'login')}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--mm-accent)',
              cursor: 'pointer',
              fontSize: '0.8rem',
              fontWeight: 500,
              padding: 0,
              textDecoration: 'underline',
              textDecorationStyle: 'dotted',
              textUnderlineOffset: '3px',
            }}
          >
            {isLogin ? "Let's begin." : 'Come back.'}
          </button>
        </p>
      </motion.div>
    </div>
  );
}
