/**
 * Journal — Inspired by Bear Notes (clean typography), Day One (date-first entries),
 * and Reflectly (emotion-aware journaling). Fully uses the MyMitra design system.
 */
import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Save, Trash2, Edit2 } from 'lucide-react';
import { toast } from 'react-toastify';

// Emotion config — inline styles, NOT dynamic Tailwind class names
const EMOTIONS = [
  { id: 'happy',     label: 'Happy',     emoji: '😊', color: '#fbbf24' },
  { id: 'grateful',  label: 'Grateful',  emoji: '🙏', color: '#34d399' },
  { id: 'calm',      label: 'Calm',      emoji: '😌', color: '#60a5fa' },
  { id: 'neutral',   label: 'Neutral',   emoji: '😐', color: '#94a3b8' },
  { id: 'sad',       label: 'Sad',       emoji: '😔', color: '#818cf8' },
  { id: 'anxious',   label: 'Anxious',   emoji: '😰', color: '#c084fc' },
  { id: 'stressed',  label: 'Stressed',  emoji: '😤', color: '#fb923c' },
  { id: 'angry',     label: 'Frustrated',emoji: '😡', color: '#f87171' },
];

function getEmotion(id) {
  return EMOTIONS.find(e => e.id === id) || EMOTIONS[3];
}

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
}

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function EntryCard({ entry, onEdit, onDelete }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const em = getEmotion(entry.emotion);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8, scale: 0.97 }}
      style={{
        background: 'var(--mm-surface-elevated)',
        backdropFilter: 'blur(20px)',
        border: '1px solid var(--mm-border)',
        borderLeft: `3px solid ${em.color}`,
        borderRadius: 'var(--mm-radius-xl)',
        padding: '1.1rem 1.25rem',
        position: 'relative',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '1.25rem' }}>{em.emoji}</span>
          <div>
            <p style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--mm-text-secondary)' }}>
              {formatDate(entry.date)}
            </p>
            <p style={{ fontSize: '0.68rem', color: 'var(--mm-text-muted)' }}>
              {formatTime(entry.timestamp)} · {entry.wordCount || 0} words
            </p>
          </div>
        </div>

        {/* Menu */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setMenuOpen(v => !v)}
            style={{
              background: 'none', border: 'none',
              color: 'var(--mm-text-muted)', cursor: 'pointer',
              padding: 4, borderRadius: 6, opacity: 0.7,
            }}
          >
            •••
          </button>
          <AnimatePresence>
            {menuOpen && (
              <motion.div
                initial={{ opacity: 0, scale: 0.92, y: -4 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                style={{
                  position: 'absolute', right: 0, top: '100%', zIndex: 20,
                  background: 'rgba(15,23,42,0.95)', backdropFilter: 'blur(20px)',
                  border: '1px solid var(--mm-border)', borderRadius: 10,
                  overflow: 'hidden', minWidth: 130, marginTop: 4,
                  boxShadow: 'var(--mm-shadow-md)',
                }}
              >
                <button
                  onClick={() => { setMenuOpen(false); onEdit(entry); }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 8,
                    width: '100%', padding: '0.55rem 0.9rem',
                    background: 'none', border: 'none',
                    color: 'var(--mm-text-secondary)', fontSize: '0.8rem', cursor: 'pointer',
                    textAlign: 'left',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(59,130,246,0.1)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'none'}
                >
                  <Edit2 size={13} /> Edit
                </button>
                <button
                  onClick={() => { setMenuOpen(false); onDelete(entry.id); }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 8,
                    width: '100%', padding: '0.55rem 0.9rem',
                    background: 'none', border: 'none',
                    color: '#f87171', fontSize: '0.8rem', cursor: 'pointer',
                    textAlign: 'left',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(248,113,113,0.08)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'none'}
                >
                  <Trash2 size={13} /> Delete
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Content */}
      <p style={{
        fontSize: '0.875rem', lineHeight: 1.7,
        color: 'var(--mm-text-primary)',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}>
        {entry.content}
      </p>
    </motion.div>
  );
}

function WritePanel({ initial, onSave, onCancel }) {
  const [content, setContent] = useState(initial?.content || '');
  const [emotion, setEmotion] = useState(initial?.emotion || 'neutral');
  const textRef = useRef(null);

  useEffect(() => {
    textRef.current?.focus();
  }, []);

  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;

  const handleSave = () => {
    if (!content.trim()) { toast.error('Write something first'); return; }
    onSave({ content: content.trim(), emotion, id: initial?.id });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className="glass-elevated"
      style={{ borderRadius: 'var(--mm-radius-2xl)', padding: '1.5rem', marginBottom: '1.5rem' }}
    >
      {/* Emotion selector */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem', marginBottom: '1rem' }}>
        {EMOTIONS.map(em => (
          <motion.button
            key={em.id}
            whileHover={{ scale: 1.06 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setEmotion(em.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: 5,
              padding: '0.3rem 0.7rem', borderRadius: 20,
              background: emotion === em.id ? `${em.color}20` : 'rgba(71,85,105,0.12)',
              border: emotion === em.id ? `1px solid ${em.color}50` : '1px solid transparent',
              color: emotion === em.id ? em.color : 'var(--mm-text-muted)',
              fontSize: '0.75rem', fontWeight: 500, cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <span style={{ fontSize: '0.9rem' }}>{em.emoji}</span>
            {em.label}
          </motion.button>
        ))}
      </div>

      {/* Textarea */}
      <textarea
        ref={textRef}
        value={content}
        onChange={e => setContent(e.target.value)}
        placeholder="What's on your mind today?&#10;&#10;This is your safe space. Write freely — Mitra will remember the essence."
        style={{
          width: '100%', minHeight: 180,
          background: 'transparent', border: 'none',
          color: 'var(--mm-text-primary)', fontSize: '0.925rem',
          lineHeight: 1.75, resize: 'none',
          fontFamily: 'inherit', outline: 'none',
          marginBottom: '0.75rem',
        }}
      />

      {/* Footer */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '0.72rem', color: 'var(--mm-text-muted)' }}>
          {wordCount > 0 ? `${wordCount} word${wordCount !== 1 ? 's' : ''}` : 'Start writing…'}
        </span>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={onCancel}
            style={{
              background: 'none', border: 'none',
              color: 'var(--mm-text-muted)', fontSize: '0.82rem',
              cursor: 'pointer', padding: '0.4rem 0.8rem', borderRadius: 8,
            }}
          >
            Cancel
          </button>
          <button
            className="btn-glow"
            onClick={handleSave}
            style={{ padding: '0.4rem 1rem', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: 5 }}
          >
            <Save size={13} />
            {initial ? 'Update' : 'Save'}
          </button>
        </div>
      </div>
    </motion.div>
  );
}

export default function Journal() {
  const [entries, setEntries] = useState(() => {
    try { return JSON.parse(localStorage.getItem('journalEntries') || '[]'); } catch { return []; }
  });
  const [writing, setWriting] = useState(false);
  const [editing, setEditing] = useState(null);

  const persist = (next) => {
    setEntries(next);
    localStorage.setItem('journalEntries', JSON.stringify(next));
  };

  const handleSave = ({ content, emotion, id }) => {
    if (id) {
      const next = entries.map(e =>
        e.id === id
          ? { ...e, content, emotion, wordCount: content.split(/\s+/).length, timestamp: new Date().toISOString() }
          : e
      );
      persist(next);
      toast.success('Entry updated');
      setEditing(null);
    } else {
      const entry = {
        id: Date.now(),
        content, emotion,
        date: new Date().toISOString(),
        timestamp: new Date().toISOString(),
        wordCount: content.split(/\s+/).length,
      };
      persist([entry, ...entries]);
      toast.success('Entry saved');
      setWriting(false);
    }
  };

  const handleDelete = (id) => {
    persist(entries.filter(e => e.id !== id));
    toast.success('Entry deleted');
  };

  const handleEdit = (entry) => {
    setEditing(entry);
    setWriting(false);
  };

  return (
    <div style={{ maxWidth: 680, margin: '0 auto', padding: '1.5rem 1rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <div>
          <h1 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--mm-text-primary)', marginBottom: 2 }}>
            Journal
          </h1>
          <p style={{ fontSize: '0.78rem', color: 'var(--mm-text-muted)' }}>
            {entries.length > 0
              ? `${entries.length} entr${entries.length !== 1 ? 'ies' : 'y'}`
              : 'Your private space'}
          </p>
        </div>

        {!writing && !editing && (
          <motion.button
            className="btn-glow"
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 5 }}
            onClick={() => setWriting(true)}
            whileTap={{ scale: 0.96 }}
          >
            <Plus size={14} />
            Write
          </motion.button>
        )}
      </div>

      {/* Write / Edit panel */}
      <AnimatePresence mode="wait">
        {writing && (
          <WritePanel
            key="new"
            onSave={handleSave}
            onCancel={() => setWriting(false)}
          />
        )}
        {editing && (
          <WritePanel
            key={editing.id}
            initial={editing}
            onSave={handleSave}
            onCancel={() => setEditing(null)}
          />
        )}
      </AnimatePresence>

      {/* Entries */}
      {entries.length === 0 && !writing ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{ textAlign: 'center', padding: '4rem 1rem' }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📔</div>
          <p style={{ color: 'var(--mm-text-secondary)', fontSize: '0.95rem', fontWeight: 500, marginBottom: '0.4rem' }}>
            Your journal is empty
          </p>
          <p style={{ color: 'var(--mm-text-muted)', fontSize: '0.82rem', marginBottom: '1.5rem' }}>
            Writing for 5 minutes a day changes how you see your life.
          </p>
          <button
            className="btn-glow"
            style={{ padding: '0.6rem 1.4rem', fontSize: '0.85rem' }}
            onClick={() => setWriting(true)}
          >
            Write your first entry
          </button>
        </motion.div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
          <AnimatePresence>
            {entries.map(entry => (
              <EntryCard
                key={entry.id}
                entry={entry}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
