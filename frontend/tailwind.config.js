/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Presence-first dark palette
        'mm-deep': '#050a15',
        'mm-primary': '#0a0e1a',
        'mm-secondary': '#0f172a',
        'mm-accent': '#3b82f6',
        'mm-accent-purple': '#8b5cf6',

        // Legacy compatibility
        cream: '#0a0e1a',
        'warm-brown': '#3b82f6',
        'dark-bg': '#050a15',
        'dark-accent': '#3b82f6',
        'text-dark': '#e2e8f0',
        'text-light': '#e2e8f0',

        // Emotion colors
        'emotion-happy': '#fbbf24',
        'emotion-sad': '#6366f1',
        'emotion-calm': '#3b82f6',
        'emotion-excited': '#f97316',
        'emotion-anxious': '#a78bfa',
      },
      fontFamily: {
        'inter': ['Inter', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'fade-in-up': 'fadeInUp 0.5s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'breathe': 'breathe 15s ease-in-out infinite',
        'glow-pulse': 'glowPulse 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseSoft: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.03)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        breathe: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.4' },
          '50%': { transform: 'scale(1.15)', opacity: '0.6' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 12px rgba(139, 92, 246, 0.1)' },
          '50%': { boxShadow: '0 0 20px rgba(139, 92, 246, 0.2)' },
        },
      },
      boxShadow: {
        'soft': '0 4px 12px rgba(0, 0, 0, 0.3)',
        'glow': '0 0 20px rgba(59, 130, 246, 0.15)',
        'glow-purple': '0 0 20px rgba(139, 92, 246, 0.12)',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      backdropBlur: {
        'glass': '20px',
      },
    },
  },
  plugins: [],
}