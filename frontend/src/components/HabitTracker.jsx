import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, Target, TrendingUp, Trash2, Plus } from 'lucide-react';
import * as api from '../services/api';

const defaultHabits = [
  { id: 1, name: 'Morning Meditation', progress: 85, target: 100, icon: '🧘' },
  { id: 2, name: 'Daily Exercise', progress: 60, target: 100, icon: '💪' },
  { id: 3, name: 'Read for 30min', progress: 40, target: 100, icon: '📚' },
  { id: 4, name: 'Drink 8 glasses water', progress: 75, target: 100, icon: '💧' },
  { id: 5, name: 'Practice gratitude', progress: 90, target: 100, icon: '🙏' },
];

const HabitTracker = ({ habits = defaultHabits, compact = false }) => {
  const [localHabits, setLocalHabits] = useState(habits);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [newTitle, setNewTitle] = useState('');
  const [newFrequency, setNewFrequency] = useState('daily');
  const [newDescription, setNewDescription] = useState('');

  const toggleHabit = async (habitId) => {
    setLocalHabits(prev =>
      prev.map(habit =>
        habit.id === habitId
          ? { ...habit, progress: habit.progress >= 100 ? 0 : 100 }
          : habit
      )
    );
    // Try to mark complete in backend if this is a real habit id
    try {
      await api.completeHabit(habitId);
    } catch (e) {
      // ignore; completion not critical for add/delete feature
    }
  };

  // Map backend habit data to chart items
  const mapHabitsToChart = useCallback((items) => (
    items.map(h => ({
      id: h.id,
      name: h.title,
      progress: Math.min(100, (h.streak_count || 0) * 10),
      target: 100,
      icon: '⭐'
    }))
  ), []);

  const fetchHabits = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getHabits();
      setLocalHabits(mapHabitsToChart(data));
    } catch (e) {
      setError('Could not load habits');
    } finally {
      setLoading(false);
    }
  }, [mapHabitsToChart]);

  useEffect(() => { fetchHabits(); }, [fetchHabits]);

  const handleAddHabit = async () => {
    if (!newTitle.trim()) {
      setError('Please enter habit title');
      return;
    }
    setError('');
    try {
      await api.createHabit(newTitle.trim(), newFrequency, newDescription || null);
      setNewTitle('');
      setNewFrequency('daily');
      setNewDescription('');
      await fetchHabits();
    } catch (e) {
      setError(e.message || 'Could not create habit');
    }
  };

  const handleDeleteHabit = async (habitId) => {
    setError('');
    try {
      await api.deleteHabit(habitId);
      await fetchHabits();
    } catch (e) {
      setError(e.message || 'Could not delete habit');
    } finally {
      setConfirmDeleteId(null);
    }
  };

  const getProgressColor = (progress) => {
    if (progress >= 100) return 'text-green-500';
    if (progress >= 75) return 'text-yellow-500';
    if (progress >= 50) return 'text-orange-500';
    return 'text-red-400';
  };

  const getProgressBg = (progress) => {
    if (progress >= 100) return 'bg-green-500';
    if (progress >= 75) return 'bg-yellow-500';
    if (progress >= 50) return 'bg-orange-500';
    return 'bg-red-400';
  };

  if (compact) {
    return (
      <motion.div
        className="bg-gradient-to-br from-soft-white to-card-light dark:from-gray-800 dark:to-gray-700 
                   rounded-2xl p-4 shadow-soft border border-gray-100 dark:border-gray-600"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-warm-brown dark:text-dark-accent flex items-center">
            <Target className="w-4 h-4 mr-2" />
            Today's Habits
          </h3>
          <span className="text-xs text-gray-500">
            {localHabits.filter(h => h.progress >= 100).length}/{localHabits.length}
          </span>
        </div>
        
        <div className="space-y-2">
          {localHabits.slice(0, 3).map((habit, index) => (
            <motion.div
              key={habit.id}
              className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors cursor-pointer"
              onClick={() => toggleHabit(habit.id)}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="flex items-center space-x-2">
                <span className="text-sm">{habit.icon}</span>
                <span className="text-xs font-medium text-gray-700 dark:text-gray-200 truncate">
                  {habit.name}
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <div className="w-12 h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full ${getProgressBg(habit.progress)} rounded-full`}
                    initial={{ width: 0 }}
                    animate={{ width: `${habit.progress}%` }}
                    transition={{ duration: 0.8, delay: index * 0.1 }}
                  />
                </div>
                {habit.progress >= 100 ? (
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                ) : (
                  <Circle className="w-4 h-4 text-gray-400" />
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="bg-gradient-to-br from-soft-white to-card-light dark:from-gray-800 dark:to-gray-700 
                 rounded-2xl p-6 shadow-soft border border-gray-100 dark:border-gray-600"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-warm-brown dark:text-dark-accent flex items-center">
          <Target className="w-5 h-5 mr-2" />
          Daily Habits
        </h2>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <TrendingUp className="w-4 h-4" />
          <span>{localHabits.filter(h => h.progress >= 100).length}/{localHabits.length} completed</span>
        </div>
      </div>

      {error && (
        <div className="mb-4 text-sm text-red-600">{error}</div>
      )}

      {/* Inline Add New Habit */}
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <input
          className="flex-1 min-w-52 px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-warm-brown"
          placeholder="New habit title"
          value={newTitle}
          onChange={e => setNewTitle(e.target.value)}
        />
        <select
          className="px-3 py-2 rounded-lg border border-gray-300"
          value={newFrequency}
          onChange={e => setNewFrequency(e.target.value)}
        >
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
        </select>
        <input
          className="flex-1 min-w-52 px-3 py-2 rounded-lg border border-gray-300"
          placeholder="Description (optional)"
          value={newDescription}
          onChange={e => setNewDescription(e.target.value)}
        />
        <button
          onClick={handleAddHabit}
          className="px-4 py-2 rounded-lg bg-warm-brown text-white font-semibold flex items-center gap-2 hover:bg-warm-brown/90"
        >
          <Plus className="w-4 h-4" /> Add
        </button>
      </div>

      <div className="space-y-4">
        {localHabits.map((habit, index) => (
          <motion.div
            key={habit.id}
            className="group p-4 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-600 transition-all duration-300 cursor-pointer"
            onClick={() => toggleHabit(habit.id)}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{habit.icon}</span>
                <div>
                  <h3 className="font-medium text-gray-800 dark:text-gray-200">
                    {habit.name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {habit.progress}% complete
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <span className={`text-sm font-semibold ${getProgressColor(habit.progress)}`}>
                  {habit.progress}%
                </span>
                {habit.progress >= 100 ? (
                  <CheckCircle2 className="w-6 h-6 text-green-500" />
                ) : (
                  <Circle className="w-6 h-6 text-gray-400 group-hover:text-warm-brown dark:group-hover:text-dark-accent transition-colors" />
                )}
                <button
                  className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-600 transition"
                  onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(habit.id); }}
                  title="Delete habit"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2 overflow-hidden">
              <motion.div
                className={`h-full ${getProgressBg(habit.progress)} rounded-full`}
                initial={{ width: 0 }}
                animate={{ width: `${habit.progress}%` }}
                transition={{ duration: 0.8, delay: index * 0.1 }}
              />
            </div>

            {confirmDeleteId === habit.id && (
              <div className="mt-3 flex justify-end gap-2">
                <button
                  className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200"
                  onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(null); }}
                >
                  Cancel
                </button>
                <button
                  className="px-3 py-1 rounded bg-red-500 text-white"
                  onClick={(e) => { e.stopPropagation(); handleDeleteHabit(habit.id); }}
                >
                  Delete
                </button>
              </div>
            )}
          </motion.div>
        ))}
      </div>

      <motion.div
        className="mt-6 p-4 bg-warm-brown/5 dark:bg-dark-accent/5 rounded-xl border border-warm-brown/10 dark:border-dark-accent/10"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
      >
        <p className="text-sm text-center text-warm-brown dark:text-dark-accent">
          🌟 Keep going! Small steps lead to big changes.
        </p>
      </motion.div>
    </motion.div>
  );
};

export default HabitTracker;