import React, { useState, useEffect } from 'react';

function HabitForm({ createHabit, updateHabit, habitToEdit, setHabitToEdit }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [frequency, setFrequency] = useState('daily');
  const [isLoading, setIsLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');

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

  const validate = () => {
    if (!name.trim()) {
      return 'Habit name is required';
    }
    if (name.trim().length > 100) {
      return 'Habit name is too long';
    }
    if (description && description.length > 300) {
      return 'Description should be 300 characters or less';
    }
    if (!['daily', 'weekly', 'monthly'].includes(frequency)) {
      return 'Please select a valid frequency';
    }
    return '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setFormError('');
    setFormSuccess('');
    const err = validate();
    if (err) {
      setFormError(err);
      setIsLoading(false);
      return;
    }
    try {
      if (isEditing && habitToEdit) {
        await updateHabit(habitToEdit.id, name.trim(), frequency, description ? description.trim() : null);
        setFormSuccess('Habit updated');
      } else {
        await createHabit(name.trim(), frequency, description ? description.trim() : null);
        setFormSuccess('Habit created');
      }
      setTimeout(() => setFormSuccess(''), 3000);
      setName('');
      setDescription('');
      setFrequency('daily');
      if (setHabitToEdit) setHabitToEdit(null);
    } catch (error) {
      // The parent component will handle the error display
      setFormError(error.message || 'Failed to save habit');
    } finally {
      setIsLoading(false);
      setIsEditing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
      <input 
        value={name} 
        onChange={(e) => setName(e.target.value)} 
        placeholder="Add a habit (e.g., 5-min breath)" 
        style={input} 
        aria-invalid={!!formError && !name.trim()} 
      />
      <input 
        value={description} 
        onChange={(e) => setDescription(e.target.value)} 
        placeholder="Optional description (e.g., 3 deep breaths)" 
        style={input} 
      />
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
      {formError && <div style={{ width: '100%', color: '#c0392b', fontSize: 12 }}>{formError}</div>}
      {formSuccess && <div style={{ width: '100%', color: '#2e7d32', fontSize: 12 }}>{formSuccess}</div>}
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
