import React, { useEffect, useState, useCallback } from 'react';
import * as api from '../services/api';
import { enqueueJournal, drainJournalsQueue } from '../services/offlineQueue';
import { hasPassphrase } from '../services/security';

function Journals() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const fetchList = useCallback(async () => {
    try {
      const data = await api.getJournals();
      setItems(data);
    } catch (e) {
      setError('Could not load journals');
    }
  }, []);

  useEffect(() => { fetchList(); }, [fetchList]);

  useEffect(() => {
    if (isOnline) {
      drainJournalsQueue().then(fetchList).catch(() => {});
    }
  }, [isOnline, fetchList]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const form = e.target;
    const title = form.title.value.trim();
    const content = form.content.value.trim();
    setError('');
    if (!title || !content) {
      setError('Please provide title and content');
      return;
    }
    if (!isOnline) {
      if (!hasPassphrase()) {
        setError('Set encryption passphrase in Chat Preferences to enable secure offline queue.');
        return;
      }
      const ok = enqueueJournal(title, content);
      if (ok) {
        setItems(prev => [{ id: Math.random().toString(36).slice(2), title, content, created_at: new Date().toISOString() }, ...prev]);
        form.reset();
      }
      return;
    }
    try {
      await api.createJournal(title, content);
      form.reset();
      fetchList();
    } catch (e) {
      setError(e.message || 'Could not create journal');
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 20 }}>
      <h2 style={{ color: '#204b72' }}>Journals</h2>
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 8, marginBottom: 16 }}>
        <input name="title" placeholder="Title" style={input} />
        <textarea name="content" placeholder="Write your thoughts..." rows={5} style={textarea} />
        <button type="submit" style={button}>Save Entry</button>
      </form>
      {error && <p style={{ color: '#c0392b' }}>{error}</p>}
      <div style={{ display: 'grid', gap: 12 }}>
        {items.map(it => (
          <div key={it.id} style={card}>
            <div style={{ fontSize: 12, color: '#7a8a9e', display: 'flex', justifyContent: 'space-between' }}>
              <span>#{it.id}</span>
              <span>{new Date(it.created_at || Date.now()).toLocaleString()}</span>
            </div>
            <div style={{ fontWeight: 700 }}>{it.title}</div>
            <div style={{ whiteSpace: 'pre-wrap', fontSize: 13, color: '#555', marginTop: 4 }}>{it.content}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

const input = { padding: '8px 10px', borderRadius: 8, border: '1px solid #d7dde6' };
const textarea = { padding: '8px 10px', borderRadius: 8, border: '1px solid #d7dde6', resize: 'vertical' };
const button = { padding: '8px 12px', borderRadius: 8, border: '1px solid #3a6ea5', background: '#3a6ea5', color: '#fff' };
const card = { background: '#fff', border: '1px solid #e6e9ef', borderRadius: 12, padding: 12 };

export default Journals;


