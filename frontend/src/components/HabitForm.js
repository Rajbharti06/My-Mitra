import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';

function HabitForm({ createHabit, updateHabit, habitToEdit, setHabitToEdit }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [frequency, setFrequency] = useState('daily');
  const [reminder, setReminder] = useState('');
  const [category, setCategory] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');
  const [validationErrors, setValidationErrors] = useState({});

  useEffect(() => {
    if (habitToEdit) {
      setName(habitToEdit.title || '');
      setDescription(habitToEdit.description || '');
      setFrequency(habitToEdit.frequency || 'daily');
      // Best-effort: try loading metadata if provided via habitToEdit.meta
      setReminder(habitToEdit.meta?.reminder || '');
      setCategory(habitToEdit.meta?.category || '');
      setIsEditing(true);
      // Clear any previous errors when editing
      setValidationErrors({});
      setFormError('');
    } else {
      setIsEditing(false);
      // Load draft for new habit if available
      try {
        const draftRaw = localStorage.getItem('habitFormDraft');
        if (draftRaw) {
          const draft = JSON.parse(draftRaw);
          setName(draft.name || '');
          setDescription(draft.description || '');
          setFrequency(draft.frequency || 'daily');
          setReminder(draft.reminder || '');
          setCategory(draft.category || '');
        }
      } catch {}
    }
  }, [habitToEdit]);

  // Auto-save draft for create flow (non-editing)
  useEffect(() => {
    if (!isEditing) {
      try {
        const draft = { name, description, frequency, reminder, category };
        localStorage.setItem('habitFormDraft', JSON.stringify(draft));
      } catch {}
    }
  }, [name, description, frequency, reminder, category, isEditing]);

  const validate = () => {
    const errors = {};
    let isValid = true;

    if (!name.trim()) {
      errors.name = 'Habit name is required';
      isValid = false;
    } else if (name.trim().length > 100) {
      errors.name = 'Habit name is too long (max 100 characters)';
      isValid = false;
    } else if (name.trim().length < 3) {
      errors.name = 'Habit name must be at least 3 characters';
      isValid = false;
    } else if (/^\s+|\s+$/.test(name)) {
      errors.name = 'Habit name cannot start or end with whitespace';
      isValid = false;
    }

    if (description) {
      if (description.length > 300) {
        errors.description = 'Description should be 300 characters or less';
        isValid = false;
      } else if (/^\s+$/.test(description)) {
        errors.description = 'Description cannot be only whitespace';
        isValid = false;
      }
    }

    if (!['daily', 'weekly', 'monthly'].includes(frequency)) {
      errors.frequency = 'Please select a valid frequency';
      isValid = false;
    }

    if (reminder) {
      const timeRegex = /^([01]?\d|2[0-3]):[0-5]\d$/; // HH:MM
      if (!timeRegex.test(reminder.trim())) {
        errors.reminder = 'Reminder must be HH:MM (24h)';
        isValid = false;
      }
    }

    if (category) {
      if (category.trim().length > 30) {
        errors.category = 'Category too long (max 30 characters)';
        isValid = false;
      } else if (/^\s+$/.test(category)) {
        errors.category = 'Category cannot be only whitespace';
        isValid = false;
      } else if (/[<>\/\\&]/.test(category)) {
        errors.category = 'Category contains invalid characters';
        isValid = false;
      }
    }

    setValidationErrors(errors);
    return isValid;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setFormError('');
    setFormSuccess('');
    
    if (!validate()) {
      setFormError('Please correct the errors in the form');
      toast.error('Please correct the errors in the form');
      setIsLoading(false);
      return;
    }
    
    try {
      const meta = { reminder: reminder.trim() || '', category: category.trim() || '' };
      if (isEditing && habitToEdit) {
        await updateHabit(habitToEdit.id, name.trim(), frequency, description ? description.trim() : null, meta);
        setFormSuccess('Habit updated successfully');
        toast.success('Habit updated successfully');
      } else {
        await createHabit(name.trim(), frequency, description ? description.trim() : null, meta);
        setFormSuccess('Habit created successfully');
        toast.success('Habit created successfully');
      }
      setTimeout(() => setFormSuccess(''), 3000);
      setName('');
      setDescription('');
      setFrequency('daily');
      setReminder('');
      setCategory('');
      try { localStorage.removeItem('habitFormDraft'); } catch {}
      setValidationErrors({});
      if (setHabitToEdit) setHabitToEdit(null);
    } catch (error) {
      console.error('Habit save error:', error);
      const errorMsg = error.message || 'Failed to save habit. Please try again.';
      setFormError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
      if (!formError) setIsEditing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', marginBottom: 8 }}>
        <input 
          value={name} 
          onChange={(e) => setName(e.target.value)} 
          placeholder="Add a habit (e.g., 5-min breath)" 
          style={{
            ...input,
            borderColor: validationErrors.name ? '#f44336' : '#cdd6e1'
          }} 
          aria-invalid={!!validationErrors.name} 
        />
        {validationErrors.name && (
          <div style={{ color: '#f44336', fontSize: 12, marginTop: 4 }}>{validationErrors.name}</div>
        )}
      </div>
      
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', marginBottom: 8 }}>
        <input 
          value={description} 
          onChange={(e) => setDescription(e.target.value)} 
          placeholder="Optional description (e.g., 3 deep breaths)" 
          style={{
            ...input,
            borderColor: validationErrors.description ? '#f44336' : '#cdd6e1'
          }}
        />
        {validationErrors.description && (
          <div style={{ color: '#f44336', fontSize: 12, marginTop: 4 }}>{validationErrors.description}</div>
        )}
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', marginBottom: 8 }}>
        <select 
          value={frequency} 
          onChange={(e) => setFrequency(e.target.value)} 
          style={{
            ...select,
            borderColor: validationErrors.frequency ? '#f44336' : '#cdd6e1'
          }}
        >
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
        </select>
        {validationErrors.frequency && (
          <div style={{ color: '#f44336', fontSize: 12, marginTop: 4 }}>{validationErrors.frequency}</div>
        )}
      </div>

      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', marginBottom: 8 }}>
        <input
          value={reminder}
          onChange={(e) => setReminder(e.target.value)}
          placeholder="Reminder (HH:MM, optional)"
          style={{
            ...input,
            borderColor: validationErrors.reminder ? '#f44336' : '#cdd6e1'
          }}
        />
        {validationErrors.reminder && (
          <div style={{ color: '#f44336', fontSize: 12, marginTop: 4 }}>{validationErrors.reminder}</div>
        )}
      </div>

      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', marginBottom: 8 }}>
        <input
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder="Category/tag (optional)"
          style={{
            ...input,
            borderColor: validationErrors.category ? '#f44336' : '#cdd6e1'
          }}
        />
        {validationErrors.category && (
          <div style={{ color: '#f44336', fontSize: 12, marginTop: 4 }}>{validationErrors.category}</div>
        )}
      </div>
      
      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
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
              setReminder('');
              setCategory('');
              setValidationErrors({});
              if (setHabitToEdit) setHabitToEdit(null);
              setIsEditing(false);
            }}
            style={{...button, background: '#6c757d', border: '1px solid #6c757d'}}
          >
            Cancel
          </button>
        )}
      </div>
      
      {formError && <div style={{ width: '100%', color: '#c0392b', fontSize: 12, marginTop: 8 }}>{formError}</div>}
      {formSuccess && <div style={{ width: '100%', color: '#2e7d32', fontSize: 12, marginTop: 8 }}>{formSuccess}</div>}
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
