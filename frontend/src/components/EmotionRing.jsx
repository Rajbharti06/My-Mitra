import React from 'react';
import { motion } from 'framer-motion';
import { getEmotionColor, getEmotionEmoji } from '../utils/theme';

const EmotionRing = ({ mood = 'neutral', intensity = 0.7, size = 'large' }) => {
  const sizeClasses = {
    small: 'w-16 h-16',
    medium: 'w-24 h-24',
    large: 'w-32 h-32',
  };

  const textSizes = {
    small: 'text-lg',
    medium: 'text-2xl',
    large: 'text-4xl',
  };

  const ringColor = getEmotionColor(mood);
  const emoji = getEmotionEmoji(mood);
  const circumference = 2 * Math.PI * 45; // radius of 45
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (intensity * circumference);

  return (
    <div className="flex flex-col items-center space-y-3">
      <motion.div
        className={`relative ${sizeClasses[size]} flex items-center justify-center`}
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ duration: 0.8, type: "spring", bounce: 0.4 }}
      >
        {/* Background circle */}
        <svg className="absolute inset-0 w-full h-full transform -rotate-90">
          <circle
            cx="50%"
            cy="50%"
            r="45"
            stroke="currentColor"
            strokeWidth="4"
            fill="none"
            className="text-gray-200 dark:text-gray-700"
          />
          {/* Progress circle */}
          <motion.circle
            cx="50%"
            cy="50%"
            r="45"
            stroke={ringColor}
            strokeWidth="4"
            fill="none"
            strokeLinecap="round"
            strokeDasharray={strokeDasharray}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            className="drop-shadow-sm"
          />
        </svg>
        
        {/* Emoji in center */}
        <motion.div
          className={`${textSizes[size]} z-10`}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.5, duration: 0.3 }}
        >
          {emoji}
        </motion.div>
      </motion.div>
      
      {/* Mood label */}
      <motion.div
        className="text-center"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8, duration: 0.3 }}
      >
        <p className="text-sm font-medium text-warm-brown dark:text-dark-accent capitalize">
          {mood}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {Math.round(intensity * 100)}% intensity
        </p>
      </motion.div>
    </div>
  );
};

export default EmotionRing;