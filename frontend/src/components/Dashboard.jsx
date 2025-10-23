import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { MessageCircle, Calendar, Sparkles } from 'lucide-react';
import EmotionRing from './EmotionRing';
import QuoteCard from './QuoteCard';
import HabitTracker from './HabitTracker';

const Dashboard = ({ onNavigate }) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [userName] = useState('Raj'); // This would come from user context
  const [currentMood] = useState('happy'); // This would come from mood tracking
  const [moodIntensity] = useState(0.8);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const getGreeting = () => {
    const hour = currentTime.getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  };

  const getGreetingEmoji = () => {
    const hour = currentTime.getHours();
    if (hour < 12) return '🌞';
    if (hour < 17) return '☀️';
    return '🌙';
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5 },
    },
  };

  return (
    <motion.div
      className="min-h-screen bg-gradient-to-br from-cream via-soft-white to-card-light 
                 dark:from-dark-bg dark:via-gray-900 dark:to-gray-800 p-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header Section */}
        <motion.div
          className="text-center space-y-4"
          variants={itemVariants}
        >
          <motion.h1
            className="text-4xl font-bold text-warm-brown dark:text-dark-accent"
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5, type: "spring" }}
          >
            {getGreeting()}, {userName} {getGreetingEmoji()}
          </motion.h1>
          
          <motion.p
            className="text-lg text-gray-600 dark:text-gray-300"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            {currentTime.toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </motion.p>
        </motion.div>

        {/* Emotion Ring Section */}
        <motion.div
          className="flex justify-center"
          variants={itemVariants}
        >
          <EmotionRing mood={currentMood} intensity={moodIntensity} size="large" />
        </motion.div>

        {/* Main Content Grid */}
        <motion.div
          className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          variants={itemVariants}
        >
          {/* Quote Card */}
          <QuoteCard />
          
          {/* Compact Habit Tracker */}
          <HabitTracker compact />
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
          variants={itemVariants}
        >
          <motion.button
            onClick={() => onNavigate('chat')}
            className="group bg-gradient-to-r from-warm-brown to-autumn-orange 
                       dark:from-dark-accent dark:to-dark-orange
                       text-white rounded-2xl px-6 py-4 shadow-warm 
                       hover:shadow-xl transition-all duration-300 flex items-center justify-center space-x-3"
            whileHover={{ scale: 1.05, y: -2 }}
            whileTap={{ scale: 0.95 }}
          >
            <MessageCircle className="w-5 h-5" />
            <span className="font-semibold">Talk to Mitra</span>
          </motion.button>

          <motion.button
            onClick={() => onNavigate('journal')}
            className="group bg-white dark:bg-gray-800 border-2 border-warm-brown dark:border-dark-accent
                       text-warm-brown dark:text-dark-accent rounded-2xl px-6 py-4 shadow-soft
                       hover:bg-warm-brown hover:text-white dark:hover:bg-dark-accent dark:hover:text-gray-900
                       transition-all duration-300 flex items-center justify-center space-x-3"
            whileHover={{ scale: 1.05, y: -2 }}
            whileTap={{ scale: 0.95 }}
          >
            <Calendar className="w-5 h-5" />
            <span className="font-semibold">Journal Entry</span>
          </motion.button>

          <motion.button
            onClick={() => onNavigate('mood')}
            className="group bg-gradient-to-r from-purple-500 to-pink-500
                       text-white rounded-2xl px-6 py-4 shadow-soft
                       hover:shadow-xl transition-all duration-300 flex items-center justify-center space-x-3"
            whileHover={{ scale: 1.05, y: -2 }}
            whileTap={{ scale: 0.95 }}
          >
            <Sparkles className="w-5 h-5" />
            <span className="font-semibold">Track Mood</span>
          </motion.button>
        </motion.div>

        {/* Today's Summary */}
        <motion.div
          className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-soft border border-gray-100 dark:border-gray-700"
          variants={itemVariants}
        >
          <h2 className="text-xl font-semibold text-warm-brown dark:text-dark-accent mb-4 flex items-center">
            <Sparkles className="w-5 h-5 mr-2" />
            Today's Highlights
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-xl">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">3</div>
              <div className="text-sm text-green-700 dark:text-green-300">Habits Completed</div>
            </div>
            
            <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">2</div>
              <div className="text-sm text-blue-700 dark:text-blue-300">Journal Entries</div>
            </div>
            
            <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl">
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">5</div>
              <div className="text-sm text-purple-700 dark:text-purple-300">Mitra Conversations</div>
            </div>
          </div>
        </motion.div>

        {/* Motivational Footer */}
        <motion.div
          className="text-center py-8"
          variants={itemVariants}
        >
          <motion.p
            className="text-lg font-medium text-warm-brown dark:text-dark-accent"
            animate={{ 
              scale: [1, 1.02, 1],
            }}
            transition={{ 
              duration: 2,
              repeat: Infinity,
              repeatType: "reverse"
            }}
          >
            ✨ You're doing amazing! Keep growing with Mitra ✨
          </motion.p>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default Dashboard;