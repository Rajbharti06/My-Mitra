/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Light theme colors
        cream: '#F6EEE3',
        'warm-brown': '#6B4F4F',
        'autumn-orange': '#DDA15E',
        'text-dark': '#2B2B2B',
        'soft-white': '#FFFAF4',
        'card-light': '#FFF8F2',
        
        // Dark theme colors
        'dark-bg': '#1E1E1E',
        'dark-accent': '#E8C4A2',
        'dark-orange': '#BC6C25',
        'text-light': '#F9F9F9',
        
        // Emotion colors
        'emotion-happy': '#FFD93D',
        'emotion-sad': '#6B9BD1',
        'emotion-calm': '#A8E6CF',
        'emotion-excited': '#FF8C94',
        'emotion-anxious': '#B19CD9',
      },
      fontFamily: {
        'poppins': ['Poppins', 'sans-serif'],
        'nunito': ['Nunito', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'fall': 'fall 10s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseSoft: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.05)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        fall: {
          '0%': { transform: 'translateY(-10%) rotate(0deg)' },
          '100%': { transform: 'translateY(110vh) rotate(360deg)' },
        },
      },
      boxShadow: {
        'soft': '0 4px 12px rgba(0, 0, 0, 0.1)',
        'warm': '0 8px 25px rgba(107, 79, 79, 0.15)',
        'inner-soft': 'inset 0 2px 4px rgba(0, 0, 0, 0.06)',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
    },
  },
  plugins: [],
}