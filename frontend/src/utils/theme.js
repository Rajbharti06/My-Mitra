// Theme context and hooks
import { createContext, useContext, useState, useEffect } from 'react';

// Theme management utility
export const themes = {
  light: {
    name: 'light',
    colors: {
      background: '#F6EEE3',
      surface: '#FFFFFF',
      primary: '#6B4F4F',
      accent: '#DDA15E',
      text: '#2B2B2B',
      textSecondary: '#6B4F4F',
      border: '#EADBCF',
      chatUser: '#E8C4A2',
      chatAI: '#FFF8F0',
    }
  },
  dark: {
    name: 'dark',
    colors: {
      background: '#1E1E1E',
      surface: '#2A2A2A',
      primary: '#E8C4A2',
      accent: '#BC6C25',
      text: '#F9F9F9',
      textSecondary: '#C9B6A6',
      border: '#3A3A3A',
      chatUser: '#BC6C25',
      chatAI: '#2A2A2A',
    }
  }
};

export const emotionColors = {
  happy: '#FFD93D',
  sad: '#6B9BD1',
  calm: '#A8E6CF',
  excited: '#FF8C94',
  anxious: '#B19CD9',
  neutral: '#D1D5DB',
  motivated: '#10B981',
  stressed: '#EF4444',
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
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('mitra-theme');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    localStorage.setItem('mitra-theme', JSON.stringify(isDark));
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  const toggleTheme = () => setIsDark(!isDark);
  const currentTheme = isDark ? themes.dark : themes.light;

  return (
    <ThemeContext.Provider value={{ isDark, toggleTheme, currentTheme, themes }}>
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