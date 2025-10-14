import React, { useEffect, useState, useCallback } from 'react';
import * as api from '../services/api';
import HabitForm from '../components/HabitForm';

function Habits() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');

  const fetchList = useCallback(async () => {
    try {
      const data = await api.getHabits();
      setItems(data);
    } catch (e) {
      setError('Could not load habits');
    }
  }, []);

  const createHabit = async (name, frequency) => {
    setError('');
    try {
      await api.createHabit(name, frequency);
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

  useEffect(() => { fetchList(); }, [fetchList]);

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 20 }}>
      <h2 style={{ color: '#204b72' }}>Habits</h2>
      <HabitForm createHabit={createHabit} />
      {error && <p style={{ color: '#c0392b' }}>{error}</p>}
      <div style={{ display: 'grid', gap: 12 }}>
        {items.map(it => (
          <div key={it.id} style={card}>
            <div style={{ fontSize: 12, color: '#7a8a9e', display: 'flex', justifyContent: 'space-between' }}>
              <span>#{it.id}</span>
              <span>Streak: {it.streak_count || 0} 🔥</span>
            </div>
            <div style={{ fontWeight: 700 }}>{it.title}</div>
            <div style={{ fontSize: 12, color: '#7a8a9e' }}>{it.frequency}</div>
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
                marginTop: 8, 
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


