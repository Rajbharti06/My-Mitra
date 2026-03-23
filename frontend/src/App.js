import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThemeProvider, useTheme } from './utils/theme';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Import new components
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import Chat from './Chat';
import HabitTracker from './components/HabitTracker';
import EmotionRing from './components/EmotionRing';
import Journal from './components/Journal';
import FloatingLeaves from './components/FloatingLeaves';

// Import existing pages
import Journals from './pages/Journals';
import Insights from './pages/Insights';
import MoodTracking from './pages/MoodTracking';
import * as api from './services/api';

function AppContent() {
  const { performanceMode, togglePerformanceMode, isDark, toggleTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [nameInput, setNameInput] = useState(() => {
    try { return localStorage.getItem('username') || ''; } catch { return ''; }
  });
  const [nameSavedNotice, setNameSavedNotice] = useState('');

  // Adaptive memory opt-in categories (opt-in only; mental-health inference off by default).
  const [memoryPrefs, setMemoryPrefs] = useState(null);
  const [memorySaving, setMemorySaving] = useState(false);

  // System actions request flow (preview -> confirmation modal -> commit).
  const [systemCapabilities, setSystemCapabilities] = useState([]);
  const [actionType, setActionType] = useState('file_list');
  const [actionParams, setActionParams] = useState({
    relative_dir: '',
    relative_path: '',
    content: '',
    max_bytes: 50000,
    days: 30
  });
  const [pendingApproval, setPendingApproval] = useState(null); // { approval_id, summary }
  const [actionModalOpen, setActionModalOpen] = useState(false);

  useEffect(() => {
    // Lightweight defaults to avoid a heavy dependency on initial API fetch.
    setMemoryPrefs({
      allow_routine_tracking: true,
      allow_preference_learning: true,
      allow_mental_health_inference: false,
      enable_long_term_memory: true,
    });
    setSystemCapabilities([
      { action_type: 'file_list' },
      { action_type: 'file_read_text' },
      { action_type: 'file_write_text' },
      { action_type: 'file_delete' },
      { action_type: 'reveal_in_explorer' },
      { action_type: 'set_chat_history_retention_days' },
    ]);

    if (!api.isAuthenticated()) return;

    (async () => {
      try {
        const mp = await api.getMemoryPreferences();
        if (mp) setMemoryPrefs(mp);
      } catch (e) {
        // Keep defaults; avoid blocking the settings UI.
      }
      try {
        const caps = await api.getSystemCapabilities();
        if (caps?.actions) setSystemCapabilities(caps.actions);
      } catch (e) {
        // Keep defaults.
      }
    })();
  }, []);

  const renderContent = () => {
    const contentVariants = performanceMode ? {} : {
      hidden: { opacity: 0, x: 20 },
      visible: { 
        opacity: 1, 
        x: 0,
        transition: { duration: 0.3 }
      },
      exit: { 
        opacity: 0, 
        x: -20,
        transition: { duration: 0.2 }
      }
    };

    const MotionWrapper = performanceMode ? 'div' : motion.div;

    switch (activeTab) {
      case 'dashboard':
        return (
          <MotionWrapper
            key="dashboard"
            variants={contentVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            <Dashboard onNavigate={setActiveTab} />
          </MotionWrapper>
        );
      case 'chat':
        return (
          <MotionWrapper
            key="chat"
            variants={contentVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="h-full"
          >
            <Chat />
          </MotionWrapper>
        );
      case 'journal':
         return (
           <MotionWrapper
             key="journal"
             variants={contentVariants}
             initial="hidden"
             animate="visible"
             exit="exit"
           >
             <Journal />
           </MotionWrapper>
         );
      case 'habits':
        return (
          <MotionWrapper
            key="habits"
            variants={contentVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="p-6"
          >
            <HabitTracker />
          </MotionWrapper>
        );
      case 'mood':
        return (
          <MotionWrapper
            key="mood"
            variants={contentVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="p-6"
          >
            <MoodTracking />
          </MotionWrapper>
        );
      case 'progress':
        return (
          <MotionWrapper
            key="progress"
            variants={contentVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            <Insights />
          </MotionWrapper>
        );
      case 'settings':
        return (
          <MotionWrapper
            key="settings"
            variants={contentVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="p-6"
          >
            <div className="max-w-2xl mx-auto">
              <h1 className="text-3xl font-bold text-warm-brown dark:text-dark-accent mb-6">
                Settings
              </h1>
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-soft space-y-6">
                {/* Personalization */}
                <div>
                  <h2 className="text-lg font-semibold text-warm-brown dark:text-dark-accent mb-2">Personalization</h2>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">Set the name Mitra should use when greeting you.</p>
                  <div className="flex gap-2 items-center">
                    <input
                      type="text"
                      value={nameInput}
                      onChange={(e) => setNameInput(e.target.value)}
                      placeholder="Enter your name"
                      className="flex-1 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-xl px-3 py-2 text-sm text-gray-800 dark:text-gray-200"
                    />
                    <button
                      onClick={() => {
                        const cleaned = (nameInput || '').trim();
                        try { localStorage.setItem('username', cleaned); } catch {}
                        setNameSavedNotice('Name saved');
                        setTimeout(() => setNameSavedNotice(''), 2000);
                      }}
                      className="bg-warm-brown text-white rounded-xl px-4 py-2 text-sm font-semibold hover:opacity-90"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => {
                        try { localStorage.removeItem('username'); } catch {}
                        setNameInput('');
                        setNameSavedNotice('Name cleared');
                        setTimeout(() => setNameSavedNotice(''), 2000);
                      }}
                      className="bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-xl px-4 py-2 text-sm hover:opacity-90"
                    >
                      Clear
                    </button>
                  </div>
                  {nameSavedNotice && (
                    <p className="text-xs text-green-600 dark:text-green-400 mt-2">{nameSavedNotice}</p>
                  )}
                </div>

                {/* Performance & Accessibility */}
                <div className="pt-4 border-t border-gray-100 dark:border-gray-700">
                  <h2 className="text-lg font-semibold text-warm-brown dark:text-dark-accent mb-2">Performance & Accessibility</h2>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-800 dark:text-gray-200">Low-end Device Mode</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Disables animations and visual effects for better performance.</p>
                      </div>
                      <button 
                        onClick={togglePerformanceMode}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${performanceMode ? 'bg-warm-brown' : 'bg-gray-300 dark:bg-gray-600'}`}
                      >
                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${performanceMode ? 'translate-x-6' : 'translate-x-1'}`} />
                      </button>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-800 dark:text-gray-200">Dark Mode</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Toggle between light and dark visual themes.</p>
                      </div>
                      <button 
                        onClick={toggleTheme}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${isDark ? 'bg-warm-brown' : 'bg-gray-300 dark:bg-gray-600'}`}
                      >
                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${isDark ? 'translate-x-6' : 'translate-x-1'}`} />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Adaptive Memory */}
                <div className="pt-4 border-t border-gray-100 dark:border-gray-700">
                  <h2 className="text-lg font-semibold text-warm-brown dark:text-dark-accent mb-2">Adaptive Memory (Opt-In)</h2>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
                    Control what the assistant can remember over time. “Mental health inference” is off by default.
                  </p>

                  {memoryPrefs === null ? (
                    <div className="text-xs text-gray-500 dark:text-gray-400">Loading...</div>
                  ) : (
                    <div className="space-y-3">
                      <label className="flex items-center justify-between gap-3">
                        <span className="text-sm text-gray-800 dark:text-gray-200">Allow routine tracking</span>
                        <input
                          type="checkbox"
                          checked={memoryPrefs.allow_routine_tracking}
                          onChange={(e) => setMemoryPrefs((p) => ({ ...p, allow_routine_tracking: e.target.checked }))}
                        />
                      </label>
                      <label className="flex items-center justify-between gap-3">
                        <span className="text-sm text-gray-800 dark:text-gray-200">Allow preference learning</span>
                        <input
                          type="checkbox"
                          checked={memoryPrefs.allow_preference_learning}
                          onChange={(e) => setMemoryPrefs((p) => ({ ...p, allow_preference_learning: e.target.checked }))}
                        />
                      </label>
                      <label className="flex items-center justify-between gap-3">
                        <span className="text-sm text-gray-800 dark:text-gray-200">Allow mental health inference</span>
                        <input
                          type="checkbox"
                          checked={memoryPrefs.allow_mental_health_inference}
                          onChange={(e) => setMemoryPrefs((p) => ({ ...p, allow_mental_health_inference: e.target.checked }))}
                        />
                      </label>

                      <div className="flex gap-2 items-center pt-2">
                        <button
                          className="bg-warm-brown text-white rounded-xl px-4 py-2 text-sm font-semibold hover:opacity-90"
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
                        {!api.isAuthenticated() && (
                          <span className="text-xs text-red-600 dark:text-red-400">
                            Sign in to change preferences
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* System Actions */}
                <div className="pt-4 border-t border-gray-100 dark:border-gray-700">
                  <h2 className="text-lg font-semibold text-warm-brown dark:text-dark-accent mb-2">System Actions (Allowlisted)</h2>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
                    All actions require a preview + explicit confirmation. Files are restricted to the app sandbox.
                  </p>

                  <div className="space-y-3">
                    <label className="text-sm text-gray-800 dark:text-gray-200">Action type</label>
                    <select
                      value={actionType}
                      onChange={(e) => setActionType(e.target.value)}
                      className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-xl px-3 py-2 text-sm text-gray-800 dark:text-gray-200"
                    >
                      {(systemCapabilities?.length ? systemCapabilities : [{ action_type: 'file_list' }]).map((a) => (
                        <option key={a.action_type} value={a.action_type}>
                          {a.action_type}
                        </option>
                      ))}
                    </select>

                    {actionType === 'file_list' && (
                      <div className="space-y-1">
                        <label className="text-xs text-gray-500 dark:text-gray-400">relative_dir</label>
                        <input
                          className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-xl px-3 py-2 text-sm text-gray-800 dark:text-gray-200"
                          value={actionParams.relative_dir}
                          onChange={(e) => setActionParams((p) => ({ ...p, relative_dir: e.target.value }))}
                        />
                      </div>
                    )}

                    {(actionType === 'file_read_text' || actionType === 'file_delete' || actionType === 'reveal_in_explorer') && (
                      <div className="space-y-1">
                        <label className="text-xs text-gray-500 dark:text-gray-400">relative_path</label>
                        <input
                          className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-xl px-3 py-2 text-sm text-gray-800 dark:text-gray-200"
                          value={actionParams.relative_path}
                          onChange={(e) => setActionParams((p) => ({ ...p, relative_path: e.target.value }))}
                        />
                      </div>
                    )}

                    {actionType === 'file_read_text' && (
                      <div className="space-y-1">
                        <label className="text-xs text-gray-500 dark:text-gray-400">max_bytes</label>
                        <input
                          type="number"
                          className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-xl px-3 py-2 text-sm text-gray-800 dark:text-gray-200"
                          value={actionParams.max_bytes}
                          onChange={(e) => setActionParams((p) => ({ ...p, max_bytes: Number(e.target.value) }))}
                        />
                      </div>
                    )}

                    {actionType === 'file_write_text' && (
                      <>
                        <div className="space-y-1">
                          <label className="text-xs text-gray-500 dark:text-gray-400">relative_path</label>
                          <input
                            className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-xl px-3 py-2 text-sm text-gray-800 dark:text-gray-200"
                            value={actionParams.relative_path}
                            onChange={(e) => setActionParams((p) => ({ ...p, relative_path: e.target.value }))}
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-xs text-gray-500 dark:text-gray-400">content (text)</label>
                          <textarea
                            className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-xl px-3 py-2 text-sm text-gray-800 dark:text-gray-200 h-28"
                            value={actionParams.content}
                            onChange={(e) => setActionParams((p) => ({ ...p, content: e.target.value }))}
                          />
                        </div>
                      </>
                    )}

                    {actionType === 'set_chat_history_retention_days' && (
                      <div className="space-y-1">
                        <label className="text-xs text-gray-500 dark:text-gray-400">days</label>
                        <input
                          type="number"
                          className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-xl px-3 py-2 text-sm text-gray-800 dark:text-gray-200"
                          value={actionParams.days}
                          onChange={(e) => setActionParams((p) => ({ ...p, days: Number(e.target.value) }))}
                        />
                      </div>
                    )}

                    <button
                      className="w-full bg-blue-600 text-white rounded-xl px-4 py-2 text-sm font-semibold hover:opacity-90 disabled:opacity-50"
                      disabled={!api.isAuthenticated()}
                      onClick={async () => {
                        try {
                          let params = {};
                          if (actionType === 'file_list') params = { relative_dir: actionParams.relative_dir };
                          if (actionType === 'file_read_text') params = { relative_path: actionParams.relative_path, max_bytes: actionParams.max_bytes };
                          if (actionType === 'file_write_text') params = { relative_path: actionParams.relative_path, content: actionParams.content };
                          if (actionType === 'file_delete') params = { relative_path: actionParams.relative_path };
                          if (actionType === 'reveal_in_explorer') params = { relative_path: actionParams.relative_path };
                          if (actionType === 'set_chat_history_retention_days') params = { days: actionParams.days };

                          const resp = await api.previewSystemAction(actionType, params);
                          setPendingApproval({ approval_id: resp.approval_id, summary: resp.summary });
                          setActionModalOpen(true);
                        } catch (e) {
                          toast.error('Failed to request action preview');
                        }
                      }}
                    >
                      Request Preview
                    </button>
                  </div>

                  {actionModalOpen && pendingApproval && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
                      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg w-[520px] p-4">
                        <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2">
                          Confirm system action
                        </h3>
                        <p className="text-xs text-gray-600 dark:text-gray-300 mb-4">
                          {pendingApproval.summary}
                        </p>
                        <div className="flex gap-2">
                          <button
                            className="flex-1 bg-blue-600 text-white rounded-xl px-3 py-2 text-sm font-semibold hover:opacity-90"
                            onClick={async () => {
                              try {
                                const resp = await api.commitSystemAction(pendingApproval.approval_id, true);
                                toast.success(resp.ok ? 'Action executed' : 'Action failed');
                                if (resp.result?.error) toast.error(resp.result.error);
                              } catch (e) {
                                toast.error('Execution failed');
                              } finally {
                                setActionModalOpen(false);
                                setPendingApproval(null);
                              }
                            }}
                          >
                            Allow
                          </button>
                          <button
                            className="flex-1 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-xl px-3 py-2 text-sm font-semibold hover:opacity-90"
                            onClick={async () => {
                              try {
                                await api.commitSystemAction(pendingApproval.approval_id, false);
                                toast.info('Action denied');
                              } catch (e) {
                                toast.error('Failed to deny');
                              } finally {
                                setActionModalOpen(false);
                                setPendingApproval(null);
                              }
                            }}
                          >
                            Deny
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </MotionWrapper>
        );
      default:
        return (
          <MotionWrapper
            key="dashboard"
            variants={contentVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            <Dashboard onNavigate={setActiveTab} />
          </MotionWrapper>
        );
    }
  };

  return (
    <div className="flex h-screen bg-cream dark:bg-dark-bg overflow-hidden relative">
      {/* Floating Leaves Animation - Disabled in performance mode */}
      {!performanceMode && <FloatingLeaves count={3} enabled={true} />}
      
      {/* Sidebar */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab}
        isCollapsed={sidebarCollapsed}
      />
      
      {/* Main Content */}
      <div className="flex-1 overflow-auto relative z-10">
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
        theme="colored"
        toastClassName="rounded-xl"
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
