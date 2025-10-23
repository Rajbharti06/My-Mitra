import React from 'react';
import { motion } from 'framer-motion';
import { 
  Home, 
  MessageCircle, 
  BookOpen, 
  Target, 
  Settings, 
  Sun, 
  Moon,
  Heart,
  TrendingUp
} from 'lucide-react';
import { useTheme } from '../utils/theme';

const Sidebar = ({ activeTab, setActiveTab, isCollapsed = false }) => {
  const { isDark, toggleTheme } = useTheme();

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home, emoji: '🏠' },
    { id: 'chat', label: 'Chat with Mitra', icon: MessageCircle, emoji: '💬' },
    { id: 'journal', label: 'Journal', icon: BookOpen, emoji: '📔' },
    { id: 'habits', label: 'Habits', icon: Target, emoji: '🎯' },
    { id: 'mood', label: 'Mood Tracker', icon: Heart, emoji: '💝' },
    { id: 'progress', label: 'Progress', icon: TrendingUp, emoji: '📈' },
  ];

  const bottomItems = [
    { id: 'settings', label: 'Settings', icon: Settings, emoji: '⚙️' },
  ];

  const MenuItem = ({ item, isBottom = false }) => {
    const isActive = activeTab === item.id;
    const Icon = item.icon;

    return (
      <motion.button
        onClick={() => setActiveTab(item.id)}
        className={`
          w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-300
          ${isActive 
            ? 'bg-warm-brown text-white shadow-lg dark:bg-dark-accent dark:text-gray-900' 
            : 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
          }
          ${isCollapsed ? 'justify-center px-2' : ''}
        `}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3 }}
      >
        {isCollapsed ? (
          <span className="text-xl">{item.emoji}</span>
        ) : (
          <>
            <Icon className="w-5 h-5 flex-shrink-0" />
            <span className="font-medium truncate">{item.label}</span>
          </>
        )}
      </motion.button>
    );
  };

  return (
    <motion.div
      className={`
        bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 
        flex flex-col h-full shadow-lg
        ${isCollapsed ? 'w-16' : 'w-64'}
      `}
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className={`p-6 border-b border-gray-200 dark:border-gray-700 ${isCollapsed ? 'p-4' : ''}`}>
        {isCollapsed ? (
          <div className="flex justify-center">
            <span className="text-2xl">🌟</span>
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h1 className="text-xl font-bold text-warm-brown dark:text-dark-accent flex items-center">
              <span className="mr-2">🌟</span>
              My Mitra
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Your AI companion
            </p>
          </motion.div>
        )}
      </div>

      {/* Main Navigation */}
      <div className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        {menuItems.map((item, index) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 * index }}
          >
            <MenuItem item={item} />
          </motion.div>
        ))}
      </div>

      {/* Bottom Section */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
        {/* Theme Toggle */}
        <motion.button
          onClick={toggleTheme}
          className={`
            w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-300
            text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700
            ${isCollapsed ? 'justify-center px-2' : ''}
          `}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {isCollapsed ? (
            <span className="text-xl">{isDark ? '🌙' : '🌞'}</span>
          ) : (
            <>
              {isDark ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
              <span className="font-medium">{isDark ? 'Dark Mode' : 'Light Mode'}</span>
            </>
          )}
        </motion.button>

        {/* Settings */}
        {bottomItems.map((item) => (
          <MenuItem key={item.id} item={item} isBottom />
        ))}

        {/* User Info */}
        {!isCollapsed && (
          <motion.div
            className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-xl"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
          >
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-warm-brown dark:bg-dark-accent rounded-full flex items-center justify-center">
                <span className="text-white dark:text-gray-900 text-sm font-semibold">R</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                  Raj
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Premium User
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default Sidebar;