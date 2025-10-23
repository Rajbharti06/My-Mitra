import React, { useEffect, useState, useCallback } from 'react';
import * as api from '../services/api';
import HabitForm from '../components/HabitForm';
import { enqueueHabit, drainHabitsQueue } from '../services/offlineQueue';
import { hasPassphrase } from '../services/security';
import { Edit, Trash2 } from 'lucide-react';

function Habits() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [habitToEdit, setHabitToEdit] = useState(null);

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
    if (!isOnline) {
      if (!hasPassphrase()) {
        setError('Set encryption passphrase in Chat Preferences to enable secure offline queue.');
        throw new Error('Passphrase not set');
      }
      const ok = enqueueHabit(name, frequency, description);
      if (ok) {
        setItems(prev => [...prev, { id: Math.random().toString(36).slice(2), title: name, frequency, description, streak_count: 0 }]);
      }
      return;
    }
    try {
      await api.createHabit(name, frequency, description);
      // Request notification permission and schedule notification
      if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
          if (permission === 'granted') {
            console.log('Notification permission granted.');
          } else {
            console.log('Notification permission denied.');
          }
        });
      }
      // Schedule a notification for the new habit (this is a placeholder, actual scheduling will be more complex)
      if ('Notification' in window && Notification.permission === 'granted') {
        navigator.serviceWorker.ready.then(registration => {
          registration.showNotification(`Habit Created: ${name}`, {
            body: `Don't forget to complete your ${frequency} habit!`,
            icon: '/logo192.png',
            tag: `habit-${name}`
          });
        });
      }
      fetchList();
    } catch (e) {
      setError(e.message || 'Could not create habit');
      throw e; // re-throw to be caught by the form
    }
  };
  
  const updateHabit = async (habitId, name, frequency, description = null) => {
    setError('');
    if (!isOnline) {
      setError('Cannot update habits while offline');
      throw new Error('Offline mode');
    }
    try {
      await api.updateHabit(habitId, { title: name, frequency, description });
      fetchList();
    } catch (e) {
      setError(e.message || 'Could not update habit');
      throw e;
    }
  };
  
  const deleteHabit = async (habitId) => {
    setError('');
    if (!isOnline) {
      setError('Cannot delete habits while offline');
      return;
    }
    try {
      await api.deleteHabit(habitId);
      fetchList();
    } catch (e) {
      setError(e.message || 'Could not delete habit');
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
      <div style={{ display: 'grid', gap: 12 }}>
        {items.map(it => (
          <div key={it.id} style={card}>
            <div style={{ fontSize: 12, color: '#7a8a9e', display: 'flex', justifyContent: 'space-between' }}>
              <span>#{it.id}</span>
              <span>Streak: {it.streak_count || 0} 🔥</span>
            </div>
            <div style={{ fontWeight: 700 }}>{it.title}</div>
            {it.description && (
              <div style={{ fontSize: 13, color: '#555', marginTop: 4 }}>{it.description}</div>
            )}
            <div style={{ fontSize: 12, color: '#7a8a9e' }}>{it.frequency}</div>
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button 
                onClick={async () => {
                  try {
                    await api.completeHabit(it.id);
                    fetchList();
                  } catch (e) {
                    setError('Failed to complete habit');
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
                Complete Today
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
                onClick={() => {
                  if (window.confirm('Are you sure you want to delete this habit?')) {
                    deleteHabit(it.id);
                  }
                }}
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


