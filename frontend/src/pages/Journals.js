import React, { useEffect, useState, useCallback } from 'react';
import * as api from '../services/api';
import JournalForm from '../components/JournalForm';

function Journals() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');

  const fetchList = useCallback(async () => {
    try {
      const data = await api.getJournals();
      setItems(data);
    } catch (e) {
      setError('Could not load journals');
    }
  }, []);

  const createJournal = async (content, mood) => {
    setError('');
    try {
      await api.createJournal(content, mood);
      fetchList();
    } catch (e) {
      setError(e.message || 'Could not create journal');
      throw e; // re-throw to be caught by the form
    }
  };

  useEffect(() => { fetchList(); }, [fetchList]);

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 20 }}>
      <h2 style={{ color: '#204b72' }}>Journals</h2>
      <JournalForm createJournal={createJournal} />
      {error && <p style={{ color: '#c0392b' }}>{error}</p>}
      <div style={{ display: 'grid', gap: 12 }}>
        {items.map(it => (
          <div key={it.id} style={card}>
            <div style={{ fontSize: 12, color: '#7a8a9e', display: 'flex', justifyContent: 'space-between' }}>
              <span>#{it.id}</span>
              {it.mood && <span>Mood: {it.mood}/10</span>}
            </div>
            <div>{it.content}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

const card = {
  background: '#fff', border: '1px solid #e6e9ef', borderRadius: 12, padding: 12
};

export default Journals;


