import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import * as api from '../services/api';

// ─── Mood config ────────────────────────────────────────────────────────
const MOODS = [
  { id: 'happy',     label: 'Happy',     emoji: '😊', color: '#34d399' },
  { id: 'motivated', label: 'Motivated', emoji: '💪', color: '#fbbf24' },
  { id: 'calm',      label: 'Calm',      emoji: '😌', color: '#60a5fa' },
  { id: 'neutral',   label: 'Neutral',   emoji: '😐', color: '#94a3b8' },
  { id: 'sad',       label: 'Sad',       emoji: '😢', color: '#818cf8' },
  { id: 'anxious',   label: 'Anxious',   emoji: '😰', color: '#c084fc' },
  { id: 'stressed',  label: 'Stressed',  emoji: '😤', color: '#fb923c' },
  { id: 'angry',     label: 'Angry',     emoji: '😡', color: '#f87171' },
];

const INTENSITIES = [
  { id: 'low',    label: 'Mild',    dots: 1 },
  { id: 'medium', label: 'Moderate', dots: 2 },
  { id: 'high',   label: 'Strong',  dots: 3 },
];

const MOOD_SCORE = { happy: 9, motivated: 8, calm: 8, neutral: 5, sad: 3, anxious: 3, stressed: 3, angry: 2 };
const INTENSITY_MULT = { low: 0.8, medium: 1, high: 1.2 };

function moodScore(mood, intensity) {
  const base = MOOD_SCORE[mood] ?? 5;
  return Math.round(base * (INTENSITY_MULT[intensity] ?? 1));
}

function formatRelative(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  const now = new Date();
  const diff = (now - d) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
}

// 30-day mood calendar heatmap — inspired by Daylio
function MoodCalendar({ history }) {
  const [hovered, setHovered] = useState(null);

  const calDays = React.useMemo(() => {
    const days = [];
    const now = new Date();
    for (let i = 29; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(now.getDate() - i);
      const dateStr = d.toISOString().split('T')[0];
      const dayEntries = history.filter(h => h.timestamp?.startsWith(dateStr));
      const primary = dayEntries[0]?.mood ?? null;
      const cfg = primary ? MOODS.find(m => m.id === primary) : null;
      days.push({
        date: dateStr,
        dayNum: d.getDate(),
        isToday: i === 0,
        isSunday: d.getDay() === 0,
        entries: dayEntries.length,
        mood: primary,
        color: cfg?.color ?? null,
        emoji: cfg?.emoji ?? null,
        label: d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' }),
        allMoods: dayEntries.map(e => MOODS.find(m => m.id === e.mood)?.emoji).filter(Boolean).join(' '),
      });
    }
    return days;
  }, [history]);

  const weeks = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

  return (
    <div style={{ position: 'relative' }}>
      {/* Day-of-week labels */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 3, marginBottom: 4 }}>
        {weeks.map((w, i) => (
          <div key={i} style={{ textAlign: 'center', fontSize: '0.58rem', color: 'var(--mm-text-muted)', fontWeight: 500 }}>{w}</div>
        ))}
      </div>

      {/* Calendar grid — 30 days laid out by weekday */}
      {(() => {
        // Fill offset so days start on correct weekday
        const firstDay = new Date(calDays[0].date).getDay(); // 0=Sun
        const cells = [...Array(firstDay).fill(null), ...calDays];
        return (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 3 }}>
            {cells.map((day, idx) => (
              <motion.div
                key={idx}
                whileHover={day ? { scale: 1.18 } : {}}
                onMouseEnter={() => day?.entries > 0 && setHovered(day)}
                onMouseLeave={() => setHovered(null)}
                style={{
                  aspectRatio: '1',
                  borderRadius: 5,
                  background: day?.color
                    ? `${day.color}44`
                    : day ? 'rgba(71,85,105,0.12)' : 'transparent',
                  border: day?.isToday
                    ? `1.5px solid ${day.color || 'var(--mm-accent)'}99`
                    : '1px solid transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: day?.emoji ? '0.75rem' : '0.6rem',
                  color: day?.color ?? 'var(--mm-text-muted)',
                  cursor: day?.entries > 0 ? 'pointer' : 'default',
                  opacity: day ? 1 : 0,
                  fontWeight: day?.isToday ? 700 : 400,
                  position: 'relative',
                  transition: 'background 0.2s',
                }}
              >
                {day?.emoji || (day ? day.dayNum : '')}
              </motion.div>
            ))}
          </div>
        );
      })()}

      {/* Hover tooltip */}
      <AnimatePresence>
        {hovered && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'absolute', bottom: '110%', left: '50%', transform: 'translateX(-50%)',
              background: 'rgba(15,23,42,0.95)', backdropFilter: 'blur(12px)',
              border: '1px solid var(--mm-border)', borderRadius: 10,
              padding: '0.5rem 0.85rem', zIndex: 10, whiteSpace: 'nowrap',
              boxShadow: 'var(--mm-shadow-md)',
            }}
          >
            <p style={{ fontSize: '0.72rem', fontWeight: 500, color: 'var(--mm-text-primary)', marginBottom: 2 }}>{hovered.label}</p>
            <p style={{ fontSize: '0.68rem', color: hovered.color ?? 'var(--mm-text-muted)' }}>
              {hovered.allMoods} {hovered.entries} check-in{hovered.entries !== 1 ? 's' : ''}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Legend */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.75rem' }}>
        {MOODS.map(m => (
          <div key={m.id} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 10, height: 10, borderRadius: 3, background: `${m.color}55`, border: `1px solid ${m.color}44` }} />
            <span style={{ fontSize: '0.62rem', color: 'var(--mm-text-muted)' }}>{m.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const MoodTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const entry = payload[0];
  const mood = MOODS.find(m => m.id === entry?.payload?.mood);
  return (
    <div className="glass rounded-xl px-3 py-2 text-xs" style={{ color: 'var(--mm-text-primary)' }}>
      <p style={{ color: 'var(--mm-text-muted)' }}>{entry?.payload?.day}</p>
      <p className="font-medium">{mood ? `${mood.emoji} ${mood.label}` : `Score ${entry.value}`}</p>
    </div>
  );
};

export default function MoodTracking() {
  const [selectedMood, setSelectedMood] = useState(null);
  const [selectedIntensity, setSelectedIntensity] = useState('medium');
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [view, setView] = useState('checkin');

  const loadHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const data = await api.getMoodHistory(20);
      setHistory(data?.moods || []);
    } catch {
      const raw = localStorage.getItem('moodHistory');
      if (raw) setHistory(JSON.parse(raw));
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const handleSave = async () => {
    if (!selectedMood) return;
    setSaving(true);
    const entry = { mood: selectedMood, intensity: selectedIntensity, note: note.trim() || null, timestamp: new Date().toISOString() };
    try {
      await api.logMood(entry.mood, entry.intensity, entry.note);
    } catch {
      const cached = JSON.parse(localStorage.getItem('moodHistory') || '[]');
      cached.unshift({ ...entry, id: Date.now() });
      localStorage.setItem('moodHistory', JSON.stringify(cached.slice(0, 50)));
    }
    setSaved(true);
    setNote('');
    setSelectedMood(null);
    setSelectedIntensity('medium');
    await loadHistory();
    setTimeout(() => { setSaved(false); setSaving(false); }, 2000);
  };

  const chartData = (() => {
    const now = new Date();
    return [...Array(7)].map((_, i) => {
      const d = new Date(now);
      d.setDate(now.getDate() - (6 - i));
      const dateStr = d.toISOString().split('T')[0];
      const dayEntries = history.filter(h => h.timestamp?.startsWith(dateStr));
      const avg = dayEntries.length
        ? Math.round(dayEntries.reduce((s, e) => s + moodScore(e.mood, e.intensity), 0) / dayEntries.length)
        : null;
      return { day: d.toLocaleDateString(undefined, { weekday: 'short' }), score: avg, mood: dayEntries[0]?.mood ?? null };
    });
  })();

  const todayEntries = history.filter(h => h.timestamp?.startsWith(new Date().toISOString().split('T')[0]));
  const moodConfig = selectedMood ? MOODS.find(m => m.id === selectedMood) : null;

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold" style={{ color: 'var(--mm-text-primary)' }}>Mood Check-In</h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--mm-text-muted)' }}>How are you feeling right now?</p>
        </div>
        <div className="flex gap-2">
          {['checkin', 'history'].map(v => (
            <button
              key={v}
              onClick={() => setView(v)}
              className="px-3 py-1.5 rounded-xl text-xs transition-all"
              style={{
                background: view === v ? 'var(--mm-accent)' : 'rgba(255,255,255,0.04)',
                color: view === v ? '#0f172a' : 'var(--mm-text-muted)',
                fontWeight: view === v ? 600 : 400,
              }}
            >
              {v === 'checkin' ? 'Check In' : 'History'}
            </button>
          ))}
        </div>
      </div>

      <AnimatePresence mode="wait">
        {view === 'checkin' && (
          <motion.div key="checkin" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="space-y-4">
            {/* Today's last entry */}
            {todayEntries.length > 0 && (
              <div className="glass rounded-2xl px-4 py-3 flex items-center gap-3">
                <span className="text-2xl">{MOODS.find(m => m.id === todayEntries[0].mood)?.emoji ?? '😐'}</span>
                <div>
                  <p className="text-xs font-medium" style={{ color: 'var(--mm-text-primary)' }}>
                    Last logged: {MOODS.find(m => m.id === todayEntries[0].mood)?.label}
                  </p>
                  <p className="text-[11px]" style={{ color: 'var(--mm-text-muted)' }}>
                    {formatRelative(todayEntries[0].timestamp)} · {todayEntries.length} check-in{todayEntries.length > 1 ? 's' : ''} today
                  </p>
                </div>
              </div>
            )}

            {/* Mood grid */}
            <div className="glass-elevated rounded-2xl p-4 space-y-3">
              <p className="text-[11px] uppercase tracking-wide font-medium" style={{ color: 'var(--mm-text-muted)' }}>Select your mood</p>
              <div className="grid grid-cols-4 gap-2">
                {MOODS.map(m => (
                  <motion.button
                    key={m.id}
                    onClick={() => setSelectedMood(m.id)}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="flex flex-col items-center gap-1 rounded-xl py-3 px-1 transition-all"
                    style={{
                      background: selectedMood === m.id ? `${m.color}22` : 'rgba(255,255,255,0.03)',
                      border: `1.5px solid ${selectedMood === m.id ? m.color : 'transparent'}`,
                      boxShadow: selectedMood === m.id ? `0 0 12px ${m.color}44` : 'none',
                    }}
                  >
                    <span className="text-2xl">{m.emoji}</span>
                    <span className="text-[10px] font-medium" style={{ color: selectedMood === m.id ? m.color : 'var(--mm-text-muted)' }}>
                      {m.label}
                    </span>
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Intensity + note + save */}
            <AnimatePresence>
              {selectedMood && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="glass-elevated rounded-2xl p-4 space-y-3"
                >
                  <p className="text-[11px] uppercase tracking-wide font-medium" style={{ color: 'var(--mm-text-muted)' }}>How intense?</p>
                  <div className="flex gap-2">
                    {INTENSITIES.map(int => (
                      <button
                        key={int.id}
                        onClick={() => setSelectedIntensity(int.id)}
                        className="flex-1 rounded-xl py-2.5 text-xs transition-all"
                        style={{
                          background: selectedIntensity === int.id ? `${moodConfig?.color}22` : 'rgba(255,255,255,0.03)',
                          border: `1.5px solid ${selectedIntensity === int.id ? (moodConfig?.color ?? 'var(--mm-accent)') : 'transparent'}`,
                          color: selectedIntensity === int.id ? (moodConfig?.color ?? 'var(--mm-accent)') : 'var(--mm-text-muted)',
                          fontWeight: selectedIntensity === int.id ? 600 : 400,
                        }}
                      >
                        {'●'.repeat(int.dots)}{'○'.repeat(3 - int.dots)} {int.label}
                      </button>
                    ))}
                  </div>

                  <input
                    type="text"
                    value={note}
                    onChange={e => setNote(e.target.value)}
                    placeholder="Add a quick note… (optional)"
                    className="input-glass w-full text-xs"
                    maxLength={160}
                  />

                  <motion.button
                    onClick={handleSave}
                    disabled={saving}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.97 }}
                    className="btn-glow w-full py-3 text-sm font-medium rounded-xl"
                    style={{ background: saved ? 'rgba(52,211,153,0.2)' : undefined, color: saved ? '#34d399' : undefined }}
                  >
                    {saved ? '✓ Saved' : saving ? 'Saving…' : `Log ${moodConfig?.emoji ?? ''} ${moodConfig?.label ?? ''}`}
                  </motion.button>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {view === 'history' && (
          <motion.div key="history" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="space-y-4">
            {/* 30-day calendar heatmap */}
            <div className="glass-elevated rounded-2xl p-4 space-y-3">
              <p className="text-[11px] uppercase tracking-wide font-medium" style={{ color: 'var(--mm-text-muted)' }}>30-day overview</p>
              {history.length === 0 ? (
                <p className="text-xs py-4 text-center" style={{ color: 'var(--mm-text-muted)' }}>No check-ins yet — start logging your mood!</p>
              ) : (
                <MoodCalendar history={history} />
              )}
            </div>

            {/* 7-day trend */}
            <div className="glass-elevated rounded-2xl p-4 space-y-3">
              <p className="text-[11px] uppercase tracking-wide font-medium" style={{ color: 'var(--mm-text-muted)' }}>7-day trend</p>
              {chartData.some(d => d.score !== null) ? (
                <ResponsiveContainer width="100%" height={110}>
                  <LineChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -28 }}>
                    <XAxis dataKey="day" tick={{ fontSize: 10, fill: 'var(--mm-text-muted)' }} axisLine={false} tickLine={false} />
                    <YAxis domain={[1, 10]} hide />
                    <Tooltip content={<MoodTooltip />} />
                    <Line type="monotoneX" dataKey="score" stroke="var(--mm-accent)" strokeWidth={2} dot={{ r: 3, fill: 'var(--mm-accent)', strokeWidth: 0 }} connectNulls />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-xs py-6 text-center" style={{ color: 'var(--mm-text-muted)' }}>No data yet — start checking in!</p>
              )}
            </div>

            {/* List */}
            <div className="glass-elevated rounded-2xl p-4 space-y-2">
              <p className="text-[11px] uppercase tracking-wide font-medium" style={{ color: 'var(--mm-text-muted)' }}>Recent check-ins</p>
              {loadingHistory ? (
                <p className="text-xs py-4 text-center" style={{ color: 'var(--mm-text-muted)' }}>Loading…</p>
              ) : history.length === 0 ? (
                <p className="text-xs py-4 text-center" style={{ color: 'var(--mm-text-muted)' }}>No check-ins yet.</p>
              ) : (
                <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                  {history.map((entry, i) => {
                    const cfg = MOODS.find(m => m.id === entry.mood);
                    return (
                      <motion.div
                        key={entry.id ?? i}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.03 }}
                        className="flex items-center gap-3 rounded-xl px-3 py-2.5"
                        style={{ background: `${cfg?.color ?? '#94a3b8'}11` }}
                      >
                        <span className="text-xl">{cfg?.emoji ?? '😐'}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-medium" style={{ color: cfg?.color ?? 'var(--mm-text-primary)' }}>{cfg?.label ?? entry.mood}</span>
                            <span className="text-[10px]" style={{ color: 'var(--mm-text-muted)' }}>· {entry.intensity}</span>
                          </div>
                          {entry.note && entry.note !== `Manual check-in: ${entry.mood}` && (
                            <p className="text-[11px] truncate" style={{ color: 'var(--mm-text-muted)' }}>{entry.note}</p>
                          )}
                        </div>
                        <span className="text-[10px] flex-shrink-0" style={{ color: 'var(--mm-text-muted)' }}>{formatRelative(entry.timestamp)}</span>
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
