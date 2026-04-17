// Theme context and hooks — MyMitra Presence-First Design
import { createContext, useContext, useState, useEffect } from 'react';

// MyMitra is always dark-mode by design (emotional companion = calm dark UI)
export const themes = {
  dark: {
    name: 'dark',
    colors: {
      background: '#050a15',
      surface: 'rgba(15, 23, 42, 0.7)',
      primary: '#3b82f6',
      accent: '#8b5cf6',
      text: '#e2e8f0',
      textSecondary: '#94a3b8',
      border: 'rgba(71, 85, 105, 0.3)',
      chatUser: 'rgba(59, 130, 246, 0.2)',
      chatAI: 'rgba(30, 41, 59, 0.5)',
    }
  }
};

export const emotionColors = {
  happy: '#fbbf24',
  sad: '#6366f1',
  calm: '#3b82f6',
  excited: '#f97316',
  anxious: '#a78bfa',
  neutral: '#64748b',
  motivated: '#10b981',
  stressed: '#ef4444',
  grateful: '#34d399',
  proud: '#f59e0b',
  confused: '#f472b6',
  tired: '#6b7280',
};

export const getEmotionColor = (emotion) => {
  return emotionColors[emotion?.toLowerCase()] || emotionColors.neutral;
};

export const getEmotionEmoji = (emotion) => {
  const emojiMap = {
    happy: '😊',
    sad: '😔',
    calm: '😌',
    excited: '🤩',
    anxious: '😰',
    neutral: '😐',
    motivated: '💪',
    stressed: '😤',
    tired: '😴',
    confused: '🤔',
    grateful: '🙏',
    proud: '😎',
  };
  return emojiMap[emotion?.toLowerCase()] || '😐';
};

const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
  // Always dark — presence-first design
  const isDark = true;

  const [performanceMode, setPerformanceMode] = useState(() => {
    const saved = localStorage.getItem('mitra-performance-mode');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    // Always ensure dark mode class is present
    document.documentElement.classList.add('dark');
    document.documentElement.setAttribute('data-theme', 'dark');
  }, []);

  useEffect(() => {
    localStorage.setItem('mitra-performance-mode', JSON.stringify(performanceMode));
  }, [performanceMode]);

  const toggleTheme = () => {}; // No-op — always dark
  const togglePerformanceMode = () => setPerformanceMode(!performanceMode);
  const currentTheme = themes.dark;

  return (
    <ThemeContext.Provider value={{ isDark, toggleTheme, currentTheme, themes, performanceMode, togglePerformanceMode }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};