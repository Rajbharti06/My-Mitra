import React, { useState, useEffect } from 'react';

function HabitForm({ createHabit, updateHabit, habitToEdit, setHabitToEdit }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [frequency, setFrequency] = useState('daily');
  const [isLoading, setIsLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    if (habitToEdit) {
      setName(habitToEdit.title || '');
      setDescription(habitToEdit.description || '');
      setFrequency(habitToEdit.frequency || 'daily');
      setIsEditing(true);
    } else {
      setIsEditing(false);
    }
  }, [habitToEdit]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      if (isEditing && habitToEdit) {
        await updateHabit(habitToEdit.id, name, frequency, description || null);
      } else {
        await createHabit(name, frequency, description || null);
      }
      setName('');
      setDescription('');
      setFrequency('daily');
      if (setHabitToEdit) setHabitToEdit(null);
    } catch (error) {
      // The parent component will handle the error display
    } finally {
      setIsLoading(false);
      setIsEditing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Add a habit (e.g., 5-min breath)" style={input} />
      <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description (e.g., 3 deep breaths)" style={input} />
      <select value={frequency} onChange={(e) => setFrequency(e.target.value)} style={select}>
        <option value="daily">Daily</option>
        <option value="weekly">Weekly</option>
        <option value="monthly">Monthly</option>
      </select>
      <button type="submit" style={button} disabled={isLoading}>
        {isLoading ? 'Saving...' : (isEditing ? 'Update' : 'Save')}
      </button>
      {isEditing && (
        <button 
          type="button" 
          onClick={() => {
            setName('');
            setDescription('');
            setFrequency('daily');
            if (setHabitToEdit) setHabitToEdit(null);
            setIsEditing(false);
          }}
          style={{...button, background: '#6c757d', border: '1px solid #6c757d'}}
        >
          Cancel
        </button>
      )}
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
