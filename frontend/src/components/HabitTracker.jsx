/**
 * HabitTracker — Inspired by Streaks (Apple Watch rings), Duolingo (streak fire),
 * and Finch (self-care companion feel). Fully uses the MyMitra design system.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, Flame, Check } from 'lucide-react';
import * as api from '../services/api';

const HABIT_EMOJIS = ['⭐', '🧘', '💪', '📚', '💧', '🎯', '🌱', '🔥', '✍️', '🏃', '🎨', '🎵', '🌿', '🧠', '😴'];

function RingProgress({ progress, size = 54, strokeWidth = 5 }) {
  const r = (size - strokeWidth) / 2;
  const circ = 2 * Math.PI * r;
  const clamped = Math.min(100, Math.max(0, progress));
  const offset = circ - (clamped / 100) * circ;
  const color = clamped >= 100 ? '#34d399' : clamped >= 60 ? '#60a5fa' : '#8b5cf6';

  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(71,85,105,0.18)" strokeWidth={strokeWidth} />
      <motion.circle
        cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke={color} strokeWidth={strokeWidth}
        strokeDasharray={circ}
        initial={{ strokeDashoffset: circ }}
        animate={{ strokeDashoffset: offset }}
        transition={{ duration: 1, ease: [0.4, 0, 0.2, 1] }}
        strokeLinecap="round"
      />
    </svg>
  );
}

function HabitCard({ habit, index, onComplete, onDelete }) {
  const [hovered, setHovered] = useState(false);
  const [justDone, setJustDone] = useState(false);

  const handleComplete = () => {
    if (!justDone) {
      setJustDone(true);
      setTimeout(() => setJustDone(false), 800);
    }
    onComplete(habit.id);
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.93, y: 14 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, y: -8 }}
      transition={{ delay: index * 0.055 }}
      whileHover={{ y: -3, transition: { duration: 0.2 } }}
      whileTap={{ scale: 0.97 }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={handleComplete}
      style={{
        position: 'relative',
        background: 'var(--mm-surface-elevated)',
        backdropFilter: 'blur(24px)',
        border: habit.progress >= 100
          ? '1px solid rgba(52,211,153,0.3)'
          : '1px solid var(--mm-border)',
        borderRadius: 'var(--mm-radius-xl)',
        padding: '1.1rem',
        cursor: 'pointer',
        transition: 'border 0.35s',
        boxShadow: habit.progress >= 100
          ? '0 0 20px rgba(52,211,153,0.08)'
          : 'var(--mm-shadow-sm)',
        minHeight: 140,
        display: 'flex',
        flexDirection: 'column',
        gap: '0.6rem',
      }}
    >
      {/* Top: ring + delete */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{ position: 'relative', width: 54, height: 54, flexShrink: 0 }}>
          <RingProgress progress={habit.progress} />
          <AnimatePresence mode="wait">
            {justDone ? (
              <motion.div
                key="check"
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0, opacity: 0 }}
                style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              >
                <Check size={22} style={{ color: '#34d399' }} />
              </motion.div>
            ) : (
              <motion.div
                key="emoji"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.25rem' }}
              >
                {habit.icon}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <motion.button
          onClick={e => { e.stopPropagation(); onDelete(habit.id); }}
          animate={{ opacity: hovered ? 1 : 0 }}
          transition={{ duration: 0.15 }}
          style={{
            background: 'none', border: 'none',
            color: 'var(--mm-text-muted)', cursor: 'pointer',
            padding: 4, borderRadius: 6,
          }}
          whileHover={{ color: '#f87171' }}
        >
          <Trash2 size={13} />
        </motion.button>
      </div>

      {/* Name */}
      <p style={{
        fontSize: '0.84rem', fontWeight: 500,
        color: 'var(--mm-text-primary)', lineHeight: 1.35,
        flex: 1,
      }}>
        {habit.name}
      </p>

      {/* Streak + frequency */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <Flame size={13} style={{ color: habit.streak > 0 ? '#fb923c' : 'var(--mm-text-muted)' }} />
          <span style={{
            fontSize: '0.7rem', fontWeight: 600,
            color: habit.streak > 0 ? '#fb923c' : 'var(--mm-text-muted)',
          }}>
            {habit.streak} day{habit.streak !== 1 ? 's' : ''}
          </span>
        </div>
        <span style={{ fontSize: '0.68rem', color: 'var(--mm-text-muted)', textTransform: 'capitalize' }}>
          {habit.frequency}
        </span>
      </div>
    </motion.div>
  );
}

export default function HabitTracker() {
  const [habits, setHabits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newTitle, setNewTitle] = useState('');
  const [newFrequency, setNewFrequency] = useState('daily');
  const [addingOpen, setAddingOpen] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  const mapHabits = useCallback((items) =>
    items.map((h, i) => ({
      id: h.id,
      name: h.title || h.name || 'Habit',
      progress: Math.min(100, (h.streak_count || 0) * 15),
      streak: h.streak_count || 0,
      frequency: h.frequency || 'daily',
      icon: HABIT_EMOJIS[i % HABIT_EMOJIS.length],
    }))
  , []);

  const fetchHabits = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getHabits();
      setHabits(mapHabits(data));
    } catch {
      setError('Could not load habits.');
    } finally {
      setLoading(false);
    }
  }, [mapHabits]);

  useEffect(() => { fetchHabits(); }, [fetchHabits]);

  const handleComplete = async (id) => {
    setHabits(prev => prev.map(h =>
      h.id === id
        ? { ...h, progress: Math.min(100, h.progress + 15), streak: h.streak + 1 }
        : h
    ));
    try { await api.completeHabit(id); } catch {}
  };

  const handleAdd = async () => {
    if (!newTitle.trim()) return;
    setError('');
    try {
      await api.createHabit({ title: newTitle.trim(), frequency: newFrequency });
      setNewTitle('');
      setAddingOpen(false);
      await fetchHabits();
    } catch (e) {
      setError(e.message || 'Could not create habit');
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.deleteHabit(id);
      setHabits(prev => prev.filter(h => h.id !== id));
    } catch (e) {
      setError(e.message || 'Could not delete');
    } finally {
      setConfirmDeleteId(null);
    }
  };

  const completedCount = habits.filter(h => h.progress >= 100).length;
  const totalStreak = habits.reduce((s, h) => s + h.streak, 0);

  return (
    <div style={{ maxWidth: 680, margin: '0 auto', padding: '1.5rem 1rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <div>
          <h1 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--mm-text-primary)', marginBottom: 2 }}>
            Habits
          </h1>
          {habits.length > 0 && (
            <p style={{ fontSize: '0.78rem', color: 'var(--mm-text-muted)' }}>
              {completedCount}/{habits.length} today
              {totalStreak > 0 && <span style={{ marginLeft: 8, color: '#fb923c' }}>🔥 {totalStreak} total streak</span>}
            </p>
          )}
        </div>

        <motion.button
          className="btn-glow"
          style={{ padding: '0.45rem 0.9rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 5 }}
          onClick={() => setAddingOpen(v => !v)}
          whileTap={{ scale: 0.96 }}
        >
          <Plus size={14} />
          Add
        </motion.button>
      </div>

      {/* Add form */}
      <AnimatePresence>
        {addingOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            style={{ overflow: 'hidden', marginBottom: '1rem' }}
          >
            <div
              className="glass-elevated"
              style={{ borderRadius: 'var(--mm-radius-xl)', padding: '1rem 1.1rem', display: 'flex', gap: '0.6rem', flexWrap: 'wrap', alignItems: 'center' }}
            >
              <input
                className="input-glass"
                style={{ flex: 1, minWidth: 160, fontSize: '0.85rem' }}
                placeholder="What habit do you want to build?"
                value={newTitle}
                onChange={e => setNewTitle(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleAdd()}
                autoFocus
              />
              <select
                value={newFrequency}
                onChange={e => setNewFrequency(e.target.value)}
                style={{
                  background: 'rgba(15,23,42,0.6)', border: '1px solid var(--mm-border)',
                  color: 'var(--mm-text-secondary)', borderRadius: 10,
                  padding: '0.5rem 0.7rem', fontSize: '0.8rem', cursor: 'pointer',
                }}
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
              </select>
              <button
                className="btn-glow"
                style={{ padding: '0.5rem 1rem', fontSize: '0.82rem' }}
                onClick={handleAdd}
              >
                Save
              </button>
            </div>
            {error && (
              <p style={{ marginTop: '0.4rem', fontSize: '0.75rem', color: '#f87171', paddingLeft: '0.2rem' }}>{error}</p>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Habit grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem 0' }}>
          <motion.p
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 2, repeat: Infinity }}
            style={{ color: 'var(--mm-text-muted)', fontSize: '0.85rem' }}
          >
            Loading your habits…
          </motion.p>
        </div>
      ) : habits.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{ textAlign: 'center', padding: '4rem 1rem' }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🌱</div>
          <p style={{ color: 'var(--mm-text-secondary)', fontSize: '0.95rem', marginBottom: '0.4rem', fontWeight: 500 }}>
            No habits yet
          </p>
          <p style={{ color: 'var(--mm-text-muted)', fontSize: '0.82rem' }}>
            Start small — even one habit changes everything.
          </p>
        </motion.div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(190px, 1fr))', gap: '0.85rem' }}>
          <AnimatePresence>
            {habits.map((habit, index) => (
              <div key={habit.id} style={{ position: 'relative' }}>
                <HabitCard
                  habit={habit}
                  index={index}
                  onComplete={handleComplete}
                  onDelete={(id) => setConfirmDeleteId(id)}
                />

                {/* Delete confirm overlay */}
                <AnimatePresence>
                  {confirmDeleteId === habit.id && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      style={{
                        position: 'absolute', inset: 0,
                        borderRadius: 'var(--mm-radius-xl)',
                        background: 'rgba(10,14,26,0.92)',
                        backdropFilter: 'blur(12px)',
                        display: 'flex', flexDirection: 'column',
                        alignItems: 'center', justifyContent: 'center',
                        gap: 10, padding: '1rem', zIndex: 5,
                      }}
                    >
                      <p style={{ fontSize: '0.82rem', color: 'var(--mm-text-primary)', textAlign: 'center', lineHeight: 1.4 }}>
                        Remove "{habit.name}"?
                      </p>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button
                          onClick={() => setConfirmDeleteId(null)}
                          style={{
                            padding: '0.3rem 0.7rem', borderRadius: 8,
                            background: 'rgba(71,85,105,0.3)', border: '1px solid var(--mm-border)',
                            color: 'var(--mm-text-secondary)', fontSize: '0.75rem', cursor: 'pointer',
                          }}
                        >
                          Keep
                        </button>
                        <button
                          onClick={() => handleDelete(habit.id)}
                          style={{
                            padding: '0.3rem 0.7rem', borderRadius: 8,
                            background: 'rgba(248,113,113,0.15)', border: '1px solid rgba(248,113,113,0.3)',
                            color: '#f87171', fontSize: '0.75rem', cursor: 'pointer',
                          }}
                        >
                          Remove
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
