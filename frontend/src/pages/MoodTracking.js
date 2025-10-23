import React, { useState, useEffect } from 'react';
import MoodTracker from '../components/MoodTracker';
import { motion } from 'framer-motion';
import * as api from '../services/api';

function MoodTracking() {
  const [moodHistory, setMoodHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showTracker, setShowTracker] = useState(true);

  useEffect(() => {
    // In a real implementation, we would fetch mood history from the API
    // For now, we'll use local storage as a simple storage mechanism
    const storedMoods = localStorage.getItem('moodHistory');
    if (storedMoods) {
      setMoodHistory(JSON.parse(storedMoods));
    }
  }, []);

  const handleMoodSubmit = (moodData) => {
    // In a real implementation, we would send this to the API
    // For now, we'll store it in local storage
    const updatedHistory = [moodData, ...moodHistory];
    setMoodHistory(updatedHistory);
    localStorage.setItem('moodHistory', JSON.stringify(updatedHistory));
    
    // Show history after submission
    setShowTracker(false);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-warm-brown dark:text-dark-accent">
          Mood Tracker
        </h1>
        <button
          onClick={() => setShowTracker(!showTracker)}
          className="px-4 py-2 bg-warm-brown text-white rounded-lg hover:bg-warm-brown-dark transition-colors"
        >
          {showTracker ? 'View History' : 'Track New Mood'}
        </button>
      </div>

      {showTracker ? (
        <MoodTracker onSubmit={handleMoodSubmit} />
      ) : (
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold text-warm-brown dark:text-dark-accent mb-4">
            Your Mood History
          </h2>
          
          {moodHistory.length === 0 ? (
            <p className="text-gray-600 dark:text-gray-300">
              You haven't tracked any moods yet. Start by tracking your current mood!
            </p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {moodHistory.map((entry, index) => (
                <motion.div
                  key={index}
                  className="bg-white dark:bg-gray-800 rounded-2xl p-4 shadow-soft"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="text-lg font-medium">
                      {entry.mood && (
                        <span className="mr-2">
                          {entry.mood === 'very_happy' ? '😄' : 
                           entry.mood === 'happy' ? '🙂' : 
                           entry.mood === 'neutral' ? '😐' : 
                           entry.mood === 'sad' ? '😔' : '😢'}
                        </span>
                      )}
                      Score: {entry.avgScore ? entry.avgScore.toFixed(1) : '?'}/5
                    </div>
                    <div className="text-sm text-gray-500">
                      {entry.timestamp ? formatDate(entry.timestamp) : 'Unknown date'}
                    </div>
                  </div>
                  
                  <div className="text-sm text-gray-600 dark:text-gray-300 mt-2">
                    {entry.feedback}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default MoodTracking;