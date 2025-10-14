import React, { useState } from 'react';

function JournalForm({ createJournal }) {
  const [content, setContent] = useState('');
  const [mood, setMood] = useState(5);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await createJournal(content, mood);
      setContent('');
      setMood(5);
    } catch (error) {
      // The parent component will handle the error display
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
      <input value={content} onChange={(e) => setContent(e.target.value)} placeholder="Write a quick reflection..." style={input} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <label style={{ fontSize: 14, color: '#204b72' }}>Mood:</label>
        <select value={mood} onChange={(e) => setMood(parseInt(e.target.value))} style={{ padding: '8px', borderRadius: 6, border: '1px solid #cdd6e1' }}>
          {[1,2,3,4,5,6,7,8,9,10].map(n => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>
      <button type="submit" style={button} disabled={isLoading}>
        {isLoading ? 'Saving...' : 'Save'}
      </button>
    </form>
  );
}

const input = {
  flex: 1, padding: '10px 12px', borderRadius: 10, border: '1px solid #cdd6e1'
};
const button = {
  padding: '10px 14px', borderRadius: 10, border: '1px solid #3a6ea5', background: '#3a6ea5', color: '#fff', fontWeight: 700
};

export default JournalForm;
