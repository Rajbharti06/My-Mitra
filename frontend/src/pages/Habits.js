import React, { useEffect, useState, useCallback } from 'react';
import * as api from '../services/api';
import HabitForm from '../components/HabitForm';
import { enqueueHabit, drainHabitsQueue } from '../services/offlineQueue';
import { hasPassphrase } from '../services/security';
import { Edit, Trash2 } from 'lucide-react';

function Habits() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [habitToEdit, setHabitToEdit] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [lastAction, setLastAction] = useState(null); // { type: 'delete'|'update'|'create', habitId?, previous?, next? }

  // Local progress storage: { [habitId]: { [YYYY-MM-DD]: percent } }
  const getProgressStore = () => {
    try {
      const raw = localStorage.getItem('habitProgress');
      return raw ? JSON.parse(raw) : {};
    } catch { return {}; }
  };
  const saveProgressStore = (store) => {
    try { localStorage.setItem('habitProgress', JSON.stringify(store)); } catch {}
  };
  const getToday = () => new Date().toISOString().slice(0, 10);
  const getTodayPercent = (habitId) => {
    const store = getProgressStore();
    return store[habitId]?.[getToday()] ?? null;
  };
  const setTodayPercent = (habitId, percent) => {
    const store = getProgressStore();
    if (!store[habitId]) store[habitId] = {};
    store[habitId][getToday()] = percent;
    saveProgressStore(store);
  };

  // Simple audit logging in localStorage for habit changes
  const getAuditLog = () => {
    try { return JSON.parse(localStorage.getItem('habitAuditLog') || '[]'); } catch { return []; }
  };
  const logAudit = (action, payload) => {
    const log = getAuditLog();
    log.push({ action, payload, ts: new Date().toISOString() });
    try { localStorage.setItem('habitAuditLog', JSON.stringify(log)); } catch {}
  };

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
      const data = await api.getHabits();
      setItems(data);
    } catch (e) {
      setError('Could not load habits');
    }
  }, []);

  useEffect(() => { fetchList(); }, [fetchList]);

  useEffect(() => {
    if (isOnline) {
      drainHabitsQueue().then(fetchList).catch(() => {});
    }
  }, [isOnline, fetchList]);

  const createHabit = async (name, frequency, description = null) => {
    setError('');
    setSuccess('');
    if (!isOnline) {
      if (!hasPassphrase()) {
        setError('Set encryption passphrase in Chat Preferences to enable secure offline queue.');
        throw new Error('Passphrase not set');
      }
      const ok = enqueueHabit(name, frequency, description);
      if (ok) {
        setItems(prev => [...prev, { id: Math.random().toString(36).slice(2), title: name, frequency, description, streak_count: 0 }]);
        setSuccess('Habit queued for creation (offline).');
        logAudit('create_offline', { title: name, frequency, description });
      }
      return;
    }
    try {
      const created = await api.createHabit(name, frequency, description);
      // Request notification permission and schedule notification
      if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
          if (permission === 'granted') {
            // ok
          }
        });
      }
      if ('Notification' in window && Notification.permission === 'granted') {
        navigator.serviceWorker.ready.then(registration => {
          registration.showNotification(`Habit Created: ${name}`, {
            body: `Don't forget to complete your ${frequency} habit!`,
            icon: '/logo192.png',
            tag: `habit-${name}`
          });
        });
      }
      setSuccess('Habit created successfully.');
      setTimeout(() => setSuccess(''), 3000);
      setLastAction({ type: 'create', next: created });
      logAudit('create', created);
      fetchList();
    } catch (e) {
      setError(e.message || 'Could not create habit');
      throw e; // re-throw to be caught by the form
    }
  };

  const updateHabit = async (habitId, name, frequency, description = null) => {
    setError('');
    setSuccess('');
    if (!isOnline) {
      setError('Cannot update habits while offline');
      throw new Error('Offline mode');
    }
    const previous = items.find(x => x.id === habitId);
    try {
      await api.updateHabit(habitId, { title: name, frequency, description });
      setSuccess('Habit updated successfully.');
      setTimeout(() => setSuccess(''), 3000);
      setLastAction({ type: 'update', habitId, previous, next: { title: name, frequency, description } });
      logAudit('update', { habitId, previous, next: { title: name, frequency, description } });
      fetchList();
    } catch (e) {
      const msg = e.message || 'Could not update habit';
      if (msg.includes('status 409') || msg.includes('status 412')) {
        setError('Update conflict detected. Reloading latest data...');
        await fetchList();
      } else {
        setError(msg);
      }
      throw e;
    }
  };

  const deleteHabit = async (habitId) => {
    setError('');
    setSuccess('');
    if (!isOnline) {
      setError('Cannot delete habits while offline');
      return;
    }
    const previous = items.find(x => x.id === habitId);
    try {
      await api.deleteHabit(habitId);
      setSuccess('Habit deleted.');
      setTimeout(() => setSuccess(''), 3000);
      setLastAction({ type: 'delete', previous });
      logAudit('delete', previous);
      fetchList();
    } catch (e) {
      const msg = e.message || 'Could not delete habit';
      if (msg.includes('status 409') || msg.includes('status 412')) {
        setError('Delete conflict detected. Reloading latest data...');
        await fetchList();
      } else {
        setError(msg);
      }
    }
  };

  const undoLastAction = async () => {
    if (!lastAction) return;
    try {
      if (lastAction.type === 'delete' && lastAction.previous) {
        await api.createHabit(lastAction.previous.title, lastAction.previous.frequency, lastAction.previous.description);
        setSuccess('Deletion undone. Habit restored.');
        logAudit('undo_delete', lastAction.previous);
      } else if (lastAction.type === 'update' && lastAction.previous && lastAction.habitId) {
        await api.updateHabit(lastAction.habitId, {
          title: lastAction.previous.title,
          frequency: lastAction.previous.frequency,
          description: lastAction.previous.description
        });
        setSuccess('Update undone. Habit reverted.');
        logAudit('undo_update', { habitId: lastAction.habitId, restored: lastAction.previous });
      } else if (lastAction.type === 'create' && lastAction.next?.id) {
        // If we have the created id, attempt to delete the newly created habit
        try { await api.deleteHabit(lastAction.next.id); } catch {}
        setSuccess('Creation undone. Habit removed.');
        logAudit('undo_create', lastAction.next);
      }
      setTimeout(() => setSuccess(''), 3000);
      setLastAction(null);
      await fetchList();
    } catch (e) {
      setError(e.message || 'Failed to undo last action');
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 20 }}>
      <h2 style={{ color: '#204b72' }}>Habits</h2>
      <HabitForm 
        createHabit={createHabit} 
        updateHabit={updateHabit} 
        habitToEdit={habitToEdit} 
        setHabitToEdit={setHabitToEdit} 
      />
      {error && <p style={{ color: '#c0392b' }}>{error}</p>}
      {success && <p style={{ color: '#2e7d32' }}>{success}</p>}
      {lastAction && (
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 12 }}>
          <span style={{ color: '#7a8a9e', fontSize: 12 }}>Last action: {lastAction.type}. You can undo.</span>
          <button onClick={undoLastAction} style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #3a6ea5', background: '#3a6ea5', color: '#fff', fontSize: 12 }}>Undo</button>
        </div>
      )}
      <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
        {items.map(it => (
          <div key={it.id} style={card}>
            <div style={{ fontSize: 12, color: '#7a8a9e', display: 'flex', justifyContent: 'space-between' }}>
              <span>#{it.id}</span>
              <span>Streak: {it.streak_count || 0} 🔥</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontWeight: 700 }}>{it.title}</div>
              <span style={{ fontSize: 11, color: '#4caf50' }}>Editable</span>
            </div>
            {it.description && (
              <div style={{ fontSize: 13, color: '#555', marginTop: 4 }}>{it.description}</div>
            )}
            <div style={{ fontSize: 12, color: '#7a8a9e' }}>{it.frequency}</div>
            <div style={{ fontSize: 12, color: '#204b72', marginTop: 6 }}>
              Today: {getTodayPercent(it.id) != null ? `${getTodayPercent(it.id)}%` : 'Not logged'}
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button 
                onClick={async () => {
                  try {
                    const input = window.prompt('What percent did you complete today? (0-100)', getTodayPercent(it.id) ?? '');
                    if (input === null) return;
                    const pct = Math.max(0, Math.min(100, Number(input)));
                    if (Number.isNaN(pct)) { setError('Please enter a valid number'); return; }
                    setTodayPercent(it.id, pct);
                    // Optionally mark complete if pct >= 100
                    if (pct >= 100 && isOnline) {
                      try { await api.completeHabit(it.id); } catch {}
                    }
                    // Re-render
                    setItems(prev => [...prev]);
                  } catch (e) {
                    setError('Failed to log progress');
                  }
                }}
                style={{ 
                  flex: 1,
                  padding: '6px 12px', 
                  borderRadius: 6, 
                  border: '1px solid #3a6ea5', 
                  background: '#3a6ea5', 
                  color: '#fff', 
                  fontSize: 12 
                }}
              >
                Log Today's %
              </button>
              <button
                onClick={() => setHabitToEdit(it)}
                style={{
                  padding: '6px 12px',
                  borderRadius: 6,
                  border: '1px solid #4caf50',
                  background: '#4caf50',
                  color: '#fff',
                  fontSize: 12,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <Edit size={14} />
              </button>
              <button
                onClick={() => setConfirmDeleteId(it.id)}
                style={{
                  padding: '6px 12px',
                  borderRadius: 6,
                  border: '1px solid #f44336',
                  background: '#f44336',
                  color: '#fff',
                  fontSize: 12,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <Trash2 size={14} />
              </button>
            </div>
            {confirmDeleteId === it.id && (
              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <button
                  onClick={() => { deleteHabit(it.id); setConfirmDeleteId(null); }}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 6,
                    border: '1px solid #f44336',
                    background: '#f44336',
                    color: '#fff',
                    fontSize: 12
                  }}
                >
                  Confirm Delete
                </button>
                <button
                  onClick={() => setConfirmDeleteId(null)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 6,
                    border: '1px solid #6c757d',
                    background: '#6c757d',
                    color: '#fff',
                    fontSize: 12
                  }}
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

const card = {
  background: '#fff', border: '1px solid #e6e9ef', borderRadius: 12, padding: 12
};

export default Habits;


