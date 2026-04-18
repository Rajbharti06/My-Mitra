import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThemeProvider } from './utils/theme';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Import components
import Sidebar from './components/Sidebar';
import Chat from './Chat';
import HabitTracker from './components/HabitTracker';
import Journal from './components/Journal';

// Import existing pages
import Insights from './pages/Insights';
import MoodTracking from './pages/MoodTracking';
import AuthScreen from './Login';
import * as api from './services/api';

function BreathingBackground({ emotion = 'calm' }) {
  return (
    <div className={`breathing-bg emotion-tint-${emotion}`}>
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="orb orb-3" />
    </div>
  );
}

function AppContent() {
  // Auth gate — check localStorage for a real token
  const [isLoggedIn, setIsLoggedIn] = useState(() => !!localStorage.getItem('access_token'));

  // When any API call returns 401, slide back to the auth screen
  useEffect(() => {
    api.setAuthFailureCallback(() => setIsLoggedIn(false));
    return () => api.setAuthFailureCallback(null);
  }, []);

  // Chat is default — presence-first design
  const [activeTab, setActiveTab] = useState('chat');
  const [currentEmotion, setCurrentEmotion] = useState('calm');

  // Settings state
  const [nameInput, setNameInput] = useState(() => {
    try { return localStorage.getItem('username') || ''; } catch { return ''; }
  });
  const [nameSavedNotice, setNameSavedNotice] = useState('');
  const [memoryPrefs, setMemoryPrefs] = useState(null);
  const [memorySaving, setMemorySaving] = useState(false);

  useEffect(() => {
    if (!isLoggedIn) return;
    setMemoryPrefs({
      allow_routine_tracking: true,
      allow_preference_learning: true,
      allow_mental_health_inference: false,
      enable_long_term_memory: true,
    });

    if (!api.isAuthenticated()) return;
    (async () => {
      try {
        const mp = await api.getMemoryPreferences();
        if (mp) setMemoryPrefs(mp);
      } catch (e) { /* Keep defaults */ }
    })();
  }, [isLoggedIn]);

  // Show auth screen if not logged in
  if (!isLoggedIn) {
    return <AuthScreen onLogin={() => setIsLoggedIn(true)} />;
  }

  const contentVariants = {
    hidden: { opacity: 0, y: 8 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] } },
    exit: { opacity: 0, y: -8, transition: { duration: 0.2 } }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return (
          <motion.div key="chat" variants={contentVariants} initial="hidden" animate="visible" exit="exit" className="h-full">
            <Chat onEmotionChange={setCurrentEmotion} />
          </motion.div>
        );
      case 'journal':
        return (
          <motion.div key="journal" variants={contentVariants} initial="hidden" animate="visible" exit="exit" className="h-full overflow-auto p-6">
            <Journal />
          </motion.div>
        );
      case 'habits':
        return (
          <motion.div key="habits" variants={contentVariants} initial="hidden" animate="visible" exit="exit" className="h-full overflow-auto p-6">
            <HabitTracker />
          </motion.div>
        );
      case 'mood':
        return (
          <motion.div key="mood" variants={contentVariants} initial="hidden" animate="visible" exit="exit" className="h-full overflow-auto p-6">
            <MoodTracking />
          </motion.div>
        );
      case 'progress':
        return (
          <motion.div key="progress" variants={contentVariants} initial="hidden" animate="visible" exit="exit" className="h-full overflow-auto">
            <Insights />
          </motion.div>
        );
      case 'settings':
        return (
          <motion.div key="settings" variants={contentVariants} initial="hidden" animate="visible" exit="exit" className="h-full overflow-auto p-6">
            <div className="max-w-2xl mx-auto space-y-6">
              <h1 className="text-xl font-semibold" style={{ color: 'var(--mm-text-primary)' }}>
                Settings
              </h1>

              {/* Personalization */}
              <div className="glass-elevated rounded-2xl p-5 space-y-4">
                <h2 className="text-sm font-semibold" style={{ color: 'var(--mm-accent)' }}>Personalization</h2>
                <p className="text-xs" style={{ color: 'var(--mm-text-muted)' }}>
                  Set the name Mitra should use when greeting you.
                </p>
                <div className="flex gap-2 items-center">
                  <input
                    type="text"
                    value={nameInput}
                    onChange={(e) => setNameInput(e.target.value)}
                    placeholder="Enter your name"
                    className="input-glass flex-1 text-sm"
                  />
                  <button
                    onClick={() => {
                      const cleaned = (nameInput || '').trim();
                      try { localStorage.setItem('username', cleaned); } catch {}
                      setNameSavedNotice('Name saved ✓');
                      setTimeout(() => setNameSavedNotice(''), 2000);
                    }}
                    className="btn-glow px-4 py-2.5 text-xs"
                  >
                    Save
                  </button>
                </div>
                {nameSavedNotice && (
                  <p className="text-xs text-green-400">{nameSavedNotice}</p>
                )}
              </div>

              {/* Adaptive Memory */}
              <div className="glass-elevated rounded-2xl p-5 space-y-4">
                <h2 className="text-sm font-semibold" style={{ color: 'var(--mm-accent)' }}>Adaptive Memory (Opt-In)</h2>
                <p className="text-xs" style={{ color: 'var(--mm-text-muted)' }}>
                  Control what the assistant can remember over time. Mental health inference is off by default.
                </p>

                {memoryPrefs && (
                  <div className="space-y-3">
                    {[
                      { key: 'allow_routine_tracking', label: 'Allow routine tracking' },
                      { key: 'allow_preference_learning', label: 'Allow preference learning' },
                      { key: 'allow_mental_health_inference', label: 'Allow mental health inference' },
                    ].map(({ key, label }) => (
                      <label key={key} className="flex items-center justify-between gap-3">
                        <span className="text-xs" style={{ color: 'var(--mm-text-secondary)' }}>{label}</span>
                        <div
                          className={`toggle-switch ${memoryPrefs[key] ? 'active' : ''}`}
                          onClick={() => setMemoryPrefs((p) => ({ ...p, [key]: !p[key] }))}
                        />
                      </label>
                    ))}
                    <button
                      className="btn-glow w-full py-2.5 text-xs mt-2"
                      disabled={memorySaving || !api.isAuthenticated()}
                      onClick={async () => {
                        try {
                          setMemorySaving(true);
                          await api.updateMemoryPreferences({
                            allow_routine_tracking: memoryPrefs.allow_routine_tracking,
                            allow_preference_learning: memoryPrefs.allow_preference_learning,
                            allow_mental_health_inference: memoryPrefs.allow_mental_health_inference
                          });
                          toast.success('Memory preferences saved');
                        } catch (e) {
                          toast.error('Failed to save memory preferences');
                        } finally {
                          setMemorySaving(false);
                        }
                      }}
                    >
                      {memorySaving ? 'Saving...' : 'Save Memory Preferences'}
                    </button>
                  </div>
                )}
              </div>

              {/* Privacy Notice */}
              <div className="glass rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm">🔒</span>
                  <h2 className="text-sm font-semibold" style={{ color: 'var(--mm-text-primary)' }}>Privacy First</h2>
                </div>
                <p className="text-xs leading-relaxed" style={{ color: 'var(--mm-text-muted)' }}>
                  All your conversations, journals, and habits are encrypted and stored locally.
                  No one — not even the admin — can read your data. MyMitra is designed to protect your privacy above everything.
                </p>
              </div>

              {/* Sign out */}
              <div className="glass-elevated rounded-2xl p-5">
                <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--mm-text-primary)' }}>Account</h2>
                <button
                  className="btn-glow w-full py-2.5 text-xs"
                  style={{ background: 'rgba(248,113,113,0.1)', borderColor: 'rgba(248,113,113,0.25)', color: '#f87171' }}
                  onClick={async () => {
                    await api.logout();
                    setIsLoggedIn(false);
                  }}
                >
                  Sign out of Mitra
                </button>
              </div>
            </div>
          </motion.div>
        );
      default:
        return (
          <motion.div key="chat" variants={contentVariants} initial="hidden" animate="visible" exit="exit" className="h-full">
            <Chat onEmotionChange={setCurrentEmotion} />
          </motion.div>
        );
    }
  };

  return (
    <div className="flex h-screen overflow-hidden relative">
      {/* Breathing Background */}
      <BreathingBackground emotion={currentEmotion} />
      
      {/* Sidebar */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab}
        isCollapsed={false}
      />
      
      {/* Main Content */}
      <div className="flex-1 overflow-hidden relative z-10">
        <AnimatePresence mode="wait">
          {renderContent()}
        </AnimatePresence>
      </div>
      
      {/* Toast Notifications */}
      <ToastContainer
        position="bottom-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
        toastClassName="rounded-xl"
        style={{ zIndex: 9999 }}
      />
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
