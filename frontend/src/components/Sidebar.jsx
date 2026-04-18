import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageCircle, 
  BookOpen, 
  Target, 
  Settings, 
  Heart,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  Sparkles
} from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab, isCollapsed: externalCollapsed }) => {
  const [isCollapsed, setIsCollapsed] = useState(externalCollapsed !== undefined ? externalCollapsed : true);

  const menuItems = [
    { id: 'chat', label: 'Chat', icon: MessageCircle, emoji: '💬' },
    { id: 'journal', label: 'Journal', icon: BookOpen, emoji: '📔' },
    { id: 'habits', label: 'Habits', icon: Target, emoji: '🎯' },
    { id: 'mood', label: 'Mood', icon: Heart, emoji: '💝' },
    { id: 'progress', label: 'Insights', icon: TrendingUp, emoji: '📈' },
  ];

  const bottomItems = [
    { id: 'settings', label: 'Settings', icon: Settings, emoji: '⚙️' },
  ];

  const MenuItem = ({ item }) => {
    const isActive = activeTab === item.id;
    const Icon = item.icon;

    return (
      <motion.button
        onClick={() => setActiveTab(item.id)}
        className={`sidebar-item w-full ${isActive ? 'active' : ''} ${isCollapsed ? 'justify-center' : ''}`}
        whileHover={{ x: isCollapsed ? 0 : 3 }}
        whileTap={{ scale: 0.97 }}
        title={isCollapsed ? item.label : undefined}
      >
        <Icon 
          size={18} 
          strokeWidth={isActive ? 2.2 : 1.8}
          style={{ 
            filter: isActive ? 'drop-shadow(0 0 6px rgba(59, 130, 246, 0.4))' : 'none',
            flexShrink: 0
          }} 
        />
        {!isCollapsed && (
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="truncate"
          >
            {item.label}
          </motion.span>
        )}
        {isActive && !isCollapsed && (
          <motion.div
            layoutId="activeIndicator"
            className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-400"
            style={{ boxShadow: '0 0 8px rgba(59, 130, 246, 0.5)' }}
          />
        )}
      </motion.button>
    );
  };

  return (
    <motion.div
      className={`sidebar-mitra flex flex-col h-full relative z-20 ${isCollapsed ? 'w-16' : 'w-56'}`}
      animate={{ width: isCollapsed ? 64 : 224 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
    >
      {/* Header */}
      <div className={`flex items-center ${isCollapsed ? 'justify-center p-3' : 'justify-between px-4'} py-5 border-b border-white/5`}>
        {isCollapsed ? (
          <motion.div 
            className="flex items-center justify-center"
            whileHover={{ scale: 1.1, rotate: 5 }}
          >
            <Sparkles size={20} className="text-blue-400" style={{ filter: 'drop-shadow(0 0 8px rgba(59, 130, 246, 0.4))' }} />
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-2.5"
          >
            <Sparkles size={18} className="text-blue-400" style={{ filter: 'drop-shadow(0 0 8px rgba(59, 130, 246, 0.4))' }} />
            <div>
              <h1 className="text-sm font-semibold tracking-wide" style={{ color: 'var(--mm-text-primary)' }}>
                MyMitra
              </h1>
              <p className="text-[10px] font-medium" style={{ color: 'var(--mm-text-muted)' }}>
                Always here for you
              </p>
            </div>
          </motion.div>
        )}

        {!isCollapsed && (
          <motion.button
            onClick={() => setIsCollapsed(true)}
            className="p-1 rounded-md hover:bg-white/5 transition-colors"
            style={{ color: 'var(--mm-text-muted)' }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <ChevronLeft size={14} />
          </motion.button>
        )}
      </div>

      {/* Collapse expand button */}
      {isCollapsed && (
        <motion.button
          onClick={() => setIsCollapsed(false)}
          className="mx-auto mt-2 p-1.5 rounded-md hover:bg-white/5 transition-colors"
          style={{ color: 'var(--mm-text-muted)' }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          <ChevronRight size={14} />
        </motion.button>
      )}

      {/* Navigation */}
      <nav className={`flex-1 ${isCollapsed ? 'px-2' : 'px-3'} py-4 space-y-1 overflow-y-auto`}>
        {menuItems.map((item, index) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05 * index, duration: 0.3 }}
          >
            <MenuItem item={item} />
          </motion.div>
        ))}
      </nav>

      {/* Bottom Section */}
      <div className={`${isCollapsed ? 'px-2' : 'px-3'} py-3 border-t border-white/5 space-y-1`}>
        {bottomItems.map((item) => (
          <MenuItem key={item.id} item={item} />
        ))}

        {/* User avatar area */}
        {!isCollapsed && (
          <motion.div
            className="mt-3 p-2.5 rounded-xl"
            style={{ background: 'rgba(59, 130, 246, 0.06)', border: '1px solid rgba(59, 130, 246, 0.1)' }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <div className="flex items-center gap-2.5">
              <div 
                className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold"
                style={{
                  background: 'linear-gradient(135deg, var(--mm-accent), var(--mm-accent-purple))',
                  color: 'white',
                  fontSize: '11px'
                }}
              >
                {(() => { try { return (localStorage.getItem('username') || 'M').charAt(0).toUpperCase(); } catch { return 'M'; } })()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate" style={{ color: 'var(--mm-text-primary)' }}>
                  {(() => { try { return localStorage.getItem('username') || 'User'; } catch { return 'User'; } })()}
                </p>
                <p className="text-[10px]" style={{ color: 'var(--mm-text-muted)' }}>
                  🔒 Private & Encrypted
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