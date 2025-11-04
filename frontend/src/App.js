import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThemeProvider } from './utils/theme';
import { ToastContainer } from 'react-toastify';
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

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [nameInput, setNameInput] = useState(() => {
    try { return localStorage.getItem('username') || ''; } catch { return ''; }
  });
  const [nameSavedNotice, setNameSavedNotice] = useState('');

  const renderContent = () => {
    const contentVariants = {
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

    switch (activeTab) {
      case 'dashboard':
        return (
          <motion.div
            key="dashboard"
            variants={contentVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            <Dashboard onNavigate={setActiveTab} />
          </motion.div>
        );
      case 'chat':
        return (
          <motion.div
            key="chat"
            variants={contentVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="h-full"
          >
            <Chat />
          </motion.div>
        );
      case 'journal':
         return (
           <motion.div
             key="journal"
             variants={contentVariants}
             initial="hidden"
             animate="visible"
             exit="exit"
           >
             <Journal />
           </motion.div>
         );
      case 'habits':
        return (
          <motion.div
            key="habits"
            variants={contentVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="p-6"
          >
            <HabitTracker />
          </motion.div>
        );
      case 'mood':
        return (
          <motion.div
            key="mood"
            variants={contentVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="p-6"
          >
            <MoodTracking />
          </motion.div>
        );
      case 'progress':
        return (
          <motion.div
            key="progress"
            variants={contentVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            <Insights />
          </motion.div>
        );
      case 'settings':
        return (
          <motion.div
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
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-soft space-y-4">
                <div>
                  <h2 className="text-lg font-semibold text-warm-brown dark:text-dark-accent mb-2">Display Name</h2>
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
              </div>
            </div>
          </motion.div>
        );
      default:
        return (
          <motion.div
            key="dashboard"
            variants={contentVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            <Dashboard onNavigate={setActiveTab} />
          </motion.div>
        );
    }
  };

  return (
     <ThemeProvider>
       <div className="flex h-screen bg-cream dark:bg-dark-bg overflow-hidden relative">
         {/* Floating Leaves Animation */}
         <FloatingLeaves count={3} enabled={true} />
         
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
     </ThemeProvider>
   );
}

export default App;
