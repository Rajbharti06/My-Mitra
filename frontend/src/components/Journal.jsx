import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, Save, BookOpen, Heart, Smile, Frown, Meh, Angry, Plus } from 'lucide-react';
import { toast } from 'react-toastify';
import { getEmotionColor, getEmotionEmoji } from '../utils/theme';

const Journal = () => {
  const [entries, setEntries] = useState([]);
  const [currentEntry, setCurrentEntry] = useState('');
  const [selectedEmotion, setSelectedEmotion] = useState('neutral');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [isWriting, setIsWriting] = useState(false);

  useEffect(() => {
    // Load journal entries from localStorage
    const savedEntries = localStorage.getItem('journalEntries');
    if (savedEntries) {
      setEntries(JSON.parse(savedEntries));
    }
  }, []);

  const saveEntry = () => {
    if (!currentEntry.trim()) {
      toast.error('Please write something before saving');
      return;
    }

    const newEntry = {
      id: Date.now(),
      date: selectedDate,
      content: currentEntry.trim(),
      emotion: selectedEmotion,
      timestamp: new Date().toISOString(),
      wordCount: currentEntry.trim().split(/\s+/).length
    };

    const updatedEntries = [newEntry, ...entries];
    setEntries(updatedEntries);
    localStorage.setItem('journalEntries', JSON.stringify(updatedEntries));
    
    setCurrentEntry('');
    setSelectedEmotion('neutral');
    setIsWriting(false);
    
    toast.success('Journal entry saved! 📝');
  };

  const EmotionSelector = () => {
    const emotions = [
      { name: 'happy', icon: Smile, label: 'Happy' },
      { name: 'love', icon: Heart, label: 'Grateful' },
      { name: 'neutral', icon: Meh, label: 'Neutral' },
      { name: 'sad', icon: Frown, label: 'Sad' },
      { name: 'angry', icon: Angry, label: 'Frustrated' }
    ];

    return (
      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm text-gray-600 dark:text-gray-400 mr-2">Today's mood:</span>
        {emotions.map(({ name, icon: Icon, label }) => (
          <motion.button
            key={name}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setSelectedEmotion(name)}
            className={`p-2 rounded-full transition-all duration-200 ${
              selectedEmotion === name
                ? `bg-${getEmotionColor(name)}-100 text-${getEmotionColor(name)}-600 dark:bg-${getEmotionColor(name)}-900 dark:text-${getEmotionColor(name)}-300 ring-2 ring-${getEmotionColor(name)}-300`
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
            title={label}
          >
            <Icon size={16} />
          </motion.button>
        ))}
      </div>
    );
  };

  const JournalEntry = ({ entry }) => {
    const emotionColor = getEmotionColor(entry.emotion);
    const emotionEmoji = getEmotionEmoji(entry.emotion);

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-soft border-l-4"
        style={{ borderLeftColor: `var(--color-${emotionColor}-500)` }}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-xl">{emotionEmoji}</span>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {new Date(entry.date).toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </span>
          </div>
          <div className="text-xs text-gray-400 dark:text-gray-500">
            {entry.wordCount} words
          </div>
        </div>
        <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
          {entry.content}
        </p>
        <div className="text-xs text-gray-400 dark:text-gray-500 mt-3">
          {new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </motion.div>
    );
  };

  return (
    <div className="min-h-screen bg-cream dark:bg-dark-bg p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="flex items-center justify-center gap-3 mb-2">
            <BookOpen className="text-warm-brown dark:text-dark-accent" size={32} />
            <h1 className="text-3xl font-bold text-warm-brown dark:text-dark-accent">
              Reflection Journal
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            A safe space for your thoughts, feelings, and daily reflections
          </p>
        </motion.div>

        {/* Writing Area */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-white to-cream dark:from-gray-800 dark:to-gray-900 rounded-2xl p-6 shadow-soft mb-8"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center gap-2">
              <Calendar size={20} className="text-gray-500 dark:text-gray-400" />
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="bg-transparent border-none text-gray-700 dark:text-gray-300 focus:outline-none"
              />
            </div>
            {!isWriting && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsWriting(true)}
                className="ml-auto flex items-center gap-2 px-4 py-2 bg-warm-brown text-white rounded-xl hover:bg-warm-brown/90 transition-colors"
              >
                <Plus size={16} />
                New Entry
              </motion.button>
            )}
          </div>

          <AnimatePresence>
            {isWriting && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-4"
              >
                <EmotionSelector />
                
                <textarea
                  value={currentEntry}
                  onChange={(e) => setCurrentEntry(e.target.value)}
                  placeholder="What's on your mind today? Share your thoughts, feelings, experiences, or anything you'd like to reflect on..."
                  className="w-full h-48 p-4 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-warm-brown dark:focus:ring-dark-accent text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400 leading-relaxed"
                  style={{ fontFamily: 'inherit' }}
                />
                
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {currentEntry.trim() ? `${currentEntry.trim().split(/\s+/).length} words` : '0 words'}
                  </div>
                  <div className="flex gap-2">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => {
                        setIsWriting(false);
                        setCurrentEntry('');
                        setSelectedEmotion('neutral');
                      }}
                      className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
                    >
                      Cancel
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={saveEntry}
                      className="flex items-center gap-2 px-6 py-2 bg-warm-brown text-white rounded-xl hover:bg-warm-brown/90 transition-colors"
                    >
                      <Save size={16} />
                      Save Entry
                    </motion.button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Journal Entries */}
        <div className="space-y-6">
          {entries.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12"
            >
              <BookOpen size={48} className="mx-auto text-gray-400 dark:text-gray-600 mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 dark:text-gray-400 mb-2">
                Your journal is empty
              </h3>
              <p className="text-gray-500 dark:text-gray-500 mb-4">
                Start writing your first entry to begin your reflection journey
              </p>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsWriting(true)}
                className="px-6 py-3 bg-warm-brown text-white rounded-xl hover:bg-warm-brown/90 transition-colors"
              >
                Write Your First Entry
              </motion.button>
            </motion.div>
          ) : (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">
                Your Reflections ({entries.length} entries)
              </h2>
              {entries.map((entry) => (
                <JournalEntry key={entry.id} entry={entry} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Journal;