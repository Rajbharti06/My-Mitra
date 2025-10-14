import React, { useState } from 'react';

function HabitForm({ createHabit }) {
  const [name, setName] = useState('');
  const [frequency, setFrequency] = useState('daily');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await createHabit(name, frequency);
      setName('');
      setFrequency('daily');
    } catch (error) {
      // The parent component will handle the error display
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Add a habit (e.g., 5-min breath)" style={input} />
      <select value={frequency} onChange={(e) => setFrequency(e.target.value)} style={select}>
        <option value="daily">Daily</option>
        <option value="weekly">Weekly</option>
        <option value="monthly">Monthly</option>
      </select>
      <button type="submit" style={button} disabled={isLoading}>
        {isLoading ? 'Saving...' : 'Save'}
      </button>
    </form>
  );
}

const input = {
  flex: 1, minWidth: 220, padding: '10px 12px', borderRadius: 10, border: '1px solid #cdd6e1'
};
const select = {
  padding: '10px 12px', borderRadius: 10, border: '1px solid #cdd6e1'
};
const button = {
  padding: '10px 14px', borderRadius: 10, border: '1px solid #3a6ea5', background: '#3a6ea5', color: '#fff', fontWeight: 700
};

export default HabitForm;
