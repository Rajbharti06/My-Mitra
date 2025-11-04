import React, { useEffect, useState, useCallback, useMemo } from 'react';
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
  const [confirmArchiveId, setConfirmArchiveId] = useState(null);
  const [lastAction, setLastAction] = useState(null); // { type: 'delete'|'update'|'create'|'archive', habitId?, previous?, next? }
  // UI controls
  const [searchQuery, setSearchQuery] = useState('');
  const [filterFrequency, setFilterFrequency] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [showArchived, setShowArchived] = useState(false);
  const [sortBy, setSortBy] = useState('title'); // 'title' | 'frequency' | 'streak' | 'created'
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);

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

  // Local metadata (reminder, category) keyed by habit id
  const getMetaStore = () => {
    try { return JSON.parse(localStorage.getItem('habitMeta') || '{}'); } catch { return {}; }
  };
  const saveMetaStore = (store) => {
    try { localStorage.setItem('habitMeta', JSON.stringify(store)); } catch {}
  };

  // Cache habits for offline access
  const getHabitsCache = () => {
    try { return JSON.parse(localStorage.getItem('habitsCache') || '[]'); } catch { return []; }
  };
  const saveHabitsCache = (list) => {
    try { localStorage.setItem('habitsCache', JSON.stringify(list)); } catch {}
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
      // Attach local metadata
      const meta = getMetaStore();
      const withMeta = Array.isArray(data) ? data.map(h => ({ ...h, meta: meta[h.id] || {} })) : [];
      setItems(withMeta);
      saveHabitsCache(withMeta);
    } catch (e) {
      const msg = e?.message || '';
      if (msg === 'Not authenticated') {
        setError('Please log in to view your habits.');
      } else {
        // Fallback to cache
        const cached = getHabitsCache();
        if (cached.length) {
          setItems(cached);
          setError('Loaded cached habits (offline).');
        } else {
          setError('Could not load habits');
        }
      }
    }
  }, []);

  // Real-time synchronization setup
  useEffect(() => {
    // Set up WebSocket connection for real-time updates
    let ws = null;
    
    const setupWebSocket = () => {
      // Close any existing connection
      if (ws) {
        ws.close();
      }
      
      // Create new WebSocket connection with authentication
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const token = localStorage.getItem('token');
      const wsUrl = `${protocol}//${window.location.host}/ws/habits${token ? `?token=${encodeURIComponent(token)}` : ''}`;
      
      ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connection established for habit synchronization');
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'habit_update' || data.type === 'habit_created' || 
              data.type === 'habit_completed' || data.type === 'habit_updated' || 
              data.type === 'habit_deleted' || data.type === 'habit_archived') {
            // Refresh habits list when changes are detected
            fetchList();
          } else if (data.type === 'habit_sync_connected') {
            console.log('Habit sync WebSocket connected successfully');
          }
        } catch (error) {
          console.error('Error processing WebSocket message:', error);
        }
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket connection closed:', event.code, event.reason);
        // Attempt to reconnect after a delay
        setTimeout(() => {
          if (navigator.onLine) {
            setupWebSocket();
          }
        }, 3000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
      };
    };
    
    // Only set up WebSocket if online
    if (isOnline) {
      setupWebSocket();
    }
    
    // Clean up WebSocket on component unmount
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [isOnline, fetchList]);

  useEffect(() => { fetchList(); }, [fetchList]);

  useEffect(() => {
    if (isOnline) {
      drainHabitsQueue().then(fetchList).catch(() => {});
    }
  }, [isOnline, fetchList]);

  const createHabit = async (name, frequency, description = null, meta = { reminder: '', category: '' }) => {
    setError('');
    setSuccess('');
    // Duplicate prevention
    const exists = items.some(h => (h.title || '').trim().toLowerCase() === (name || '').trim().toLowerCase());
    if (exists) {
      const msg = 'A habit with this name already exists.';
      setError(msg);
      throw new Error(msg);
    }
    if (!isOnline) {
      if (!hasPassphrase()) {
        setError('Set encryption passphrase in Chat Preferences to enable secure offline queue.');
        throw new Error('Passphrase not set');
      }
      const ok = enqueueHabit(name, frequency, description);
      if (ok) {
        const tempId = Math.random().toString(36).slice(2);
        // Store metadata locally
        const metaStore = getMetaStore();
        metaStore[tempId] = { reminder: meta.reminder || '', category: meta.category || '' };
        saveMetaStore(metaStore);
        setItems(prev => [...prev, { id: tempId, title: name, frequency, description, streak_count: 0, meta: metaStore[tempId] }]);
        setSuccess('Habit queued for creation (offline).');
        logAudit('create_offline', { title: name, frequency, description });
      }
      return;
    }
    try {
      const created = await api.createHabit(name, frequency, description);
      // Persist metadata for created habit
      const metaStore = getMetaStore();
      metaStore[created.id] = { reminder: meta.reminder || '', category: meta.category || '' };
      saveMetaStore(metaStore);
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
      setLastAction({ type: 'create', next: { ...created, meta: metaStore[created.id] } });
      logAudit('create', { ...created, meta: metaStore[created.id] });
      fetchList();
    } catch (e) {
      setError(e.message || 'Could not create habit');
      throw e; // re-throw to be caught by the form
    }
  };

  const updateHabit = async (habitId, name, frequency, description = null, meta = { reminder: '', category: '' }) => {
    setError('');
    setSuccess('');
    if (!isOnline) {
      setError('Cannot update habits while offline');
      throw new Error('Offline mode');
    }
    // Duplicate prevention (ignore current habit)
    const exists = items.some(h => h.id !== habitId && (h.title || '').trim().toLowerCase() === (name || '').trim().toLowerCase());
    if (exists) {
      const msg = 'A habit with this name already exists.';
      setError(msg);
      throw new Error(msg);
    }
    const previous = items.find(x => x.id === habitId);
    try {
      await api.updateHabit(habitId, { title: name, frequency, description });
      // Update local metadata
      const metaStore = getMetaStore();
      metaStore[habitId] = { reminder: meta.reminder || '', category: meta.category || '' };
      saveMetaStore(metaStore);
      setSuccess('Habit updated successfully.');
      setTimeout(() => setSuccess(''), 3000);
      setLastAction({ type: 'update', habitId, previous, next: { title: name, frequency, description, meta: metaStore[habitId] } });
      logAudit('update', { habitId, previous, next: { title: name, frequency, description, meta: metaStore[habitId] } });
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

  const archiveHabit = async (habitId) => {
    setError('');
    setSuccess('');
    
    const previous = items.find(x => x.id === habitId);
    if (!previous) {
      setError('Habit not found');
      setConfirmArchiveId(null);
      return;
    }
    
    // Maximum retries for network operations
    const MAX_RETRIES = 3;
    let retries = 0;
    let success = false;
    
    while (retries < MAX_RETRIES && !success) {
      try {
        // Immediately update UI to reflect archiving
        setItems(prevItems => prevItems.map(item => 
          item.id === habitId ? { ...item, archived: true } : item
        ));
        
        // Send archive request to backend
        await api.archiveHabit(habitId);
        
        // Show success message
        setSuccess('Habit archived successfully.');
        setTimeout(() => setSuccess(''), 3000);
        
        // Record action for audit and potential undo
        setLastAction({ type: 'archive', habitId, previous });
        logAudit('archive', previous);
        
        success = true;
      } catch (e) {
        console.error(`Archive habit error (attempt ${retries + 1}):`, e);
        retries++;
        
        if (retries >= MAX_RETRIES) {
          // If archiving fails after all retries, restore the item in the UI
          setItems(prevItems => prevItems.map(item => 
            item.id === habitId ? { ...item, archived: false } : item
          ));
          
          const msg = e.message || 'Could not archive habit';
          setError(`Failed to archive habit: ${msg}. Please try again later.`);
        } else {
          // Wait before retrying (exponential backoff)
          await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retries)));
        }
      } finally {
        if (retries >= MAX_RETRIES || success) {
          // Clear confirmation state
          setConfirmArchiveId(null);
        }
      }
    }
  };

  const deleteHabit = async (habitId) => {
    setError('');
    setSuccess('');
    if (!isOnline) {
      // Allow local deletion even when offline
      const previous = items.find(x => x.id === habitId);
      setItems(prevItems => prevItems.filter(item => item.id !== habitId));
      setSuccess('Habit deleted locally. Will sync when online.');
      setTimeout(() => setSuccess(''), 3000);
      
      // Remove from local progress store
      const progressStore = getProgressStore();
      if (progressStore[habitId]) {
        delete progressStore[habitId];
        saveProgressStore(progressStore);
      }
      
      // Remove from metadata store
      const metaStore = getMetaStore();
      if (metaStore[habitId]) {
        delete metaStore[habitId];
        saveMetaStore(metaStore);
      }
      
      setConfirmDeleteId(null);
      return;
    }
    
    const previous = items.find(x => x.id === habitId);
    if (!previous) {
      setError('Habit not found');
      setConfirmDeleteId(null);
      return;
    }
    
    // Maximum retries for network operations
    const MAX_RETRIES = 3;
    let retries = 0;
    let success = false;
    
    while (retries < MAX_RETRIES && !success) {
      try {
        // Immediately update UI to reflect deletion
        setItems(prevItems => prevItems.filter(item => item.id !== habitId));
        
        // Send delete request to backend
        await api.deleteHabit(habitId);
        
        // Show success message
        setSuccess('Habit permanently deleted.');
        setTimeout(() => setSuccess(''), 3000);
        
        // Record action for audit and potential undo
        setLastAction({ type: 'delete', previous });
        logAudit('delete', previous);
        
        // Remove from local progress store
        const progressStore = getProgressStore();
        if (progressStore[habitId]) {
          delete progressStore[habitId];
          saveProgressStore(progressStore);
        }
        
        // Remove from metadata store
        const metaStore = getMetaStore();
        if (metaStore[habitId]) {
          delete metaStore[habitId];
          saveMetaStore(metaStore);
        }
        
        success = true;
      } catch (e) {
        console.error(`Delete habit error (attempt ${retries + 1}):`, e);
        retries++;
        
        if (retries >= MAX_RETRIES) {
          // If deletion fails after all retries, restore the item in the UI
          setItems(prevItems => [...prevItems, previous].sort((a, b) => (a.title || '').localeCompare(b.title || '')));
          
          const msg = e.message || 'Could not delete habit';
          if (msg.includes('status 409') || msg.includes('status 412')) {
            setError('Delete conflict detected. Reloading latest data...');
            await fetchList();
          } else {
            setError(`Failed to delete habit: ${msg}. Please try again later.`);
          }
        } else {
          // Wait before retrying (exponential backoff)
          await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retries)));
        }
      } finally {
        if (retries >= MAX_RETRIES || success) {
          // Clear confirmation state
          setConfirmDeleteId(null);
        }
      }
    }
  };

  // Bulk deletion with confirmation
  const deleteSelected = async () => {
    if (selectedIds.length === 0) return;
    
    const ok = window.confirm(`Delete ${selectedIds.length} selected habit(s) permanently?`);
    if (!ok) return;
    
    setError('');
    setSuccess('');
    
    // Optimistic UI removal
    const prevItems = items;
    setItems(prev => prev.filter(h => !selectedIds.includes(h.id)));
    
    // Remove progress and metadata regardless of online status
    const progressStore = getProgressStore();
    const metaStore = getMetaStore();
    selectedIds.forEach(id => {
      if (progressStore[id]) delete progressStore[id];
      if (metaStore[id]) delete metaStore[id];
    });
    saveProgressStore(progressStore);
    saveMetaStore(metaStore);
    
    if (!isOnline) {
      setSuccess(`Deleted ${selectedIds.length} habit(s) locally. Will sync when online.`);
      setTimeout(() => setSuccess(''), 3000);
      setSelectedIds([]);
      setSelectionMode(false);
      return;
    }
    
    try {
      await Promise.all(selectedIds.map(id => api.deleteHabit(id)));
      setSuccess(`Deleted ${selectedIds.length} habit(s).`);
      setTimeout(() => setSuccess(''), 3000);
      setSelectedIds([]);
      setSelectionMode(false);
      logAudit('bulk_delete', { ids: selectedIds });
    } catch (e) {
      setItems(prevItems);
      setError(e.message || 'Failed to delete selected habits');
    }
  };

  // Derived list with search, filter, and sort
  const filteredItems = useMemo(() => {
    let list = [...items];
    // Search by title or description
    const q = searchQuery.trim().toLowerCase();
    if (q) {
      list = list.filter(h => (h.title || '').toLowerCase().includes(q) || (h.description || '').toLowerCase().includes(q));
    }
    // Filter frequency
    if (filterFrequency) {
      list = list.filter(h => (h.frequency || '') === filterFrequency);
    }
    // Filter category
    if (filterCategory) {
      list = list.filter(h => (h.meta?.category || '') === filterCategory);
    }
    // Filter archived
    if (!showArchived) {
      list = list.filter(h => !h.archived);
    }
    // Sort
    list.sort((a, b) => {
      switch (sortBy) {
        case 'frequency':
          return (a.frequency || '').localeCompare(b.frequency || '');
        case 'streak':
          return (b.streak_count || 0) - (a.streak_count || 0);
        case 'created':
          return new Date(b.created_at || 0) - new Date(a.created_at || 0);
        case 'title':
        default:
          return (a.title || '').localeCompare(b.title || '');
      }
    });
    return list;
  }, [items, searchQuery, filterFrequency, filterCategory, sortBy, showArchived]);

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
      {error && (
        <div style={{ 
          padding: '12px 16px', 
          backgroundColor: '#ffebee', 
          color: '#c0392b', 
          borderRadius: 8, 
          marginBottom: 16,
          display: 'flex',
          alignItems: 'center',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 12 }}>
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          {error}
        </div>
      )}
      {success && (
        <div style={{ 
          padding: '12px 16px', 
          backgroundColor: '#e8f5e9', 
          color: '#2e7d32', 
          borderRadius: 8, 
          marginBottom: 16,
          display: 'flex',
          alignItems: 'center',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 12 }}>
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
          {success}
        </div>
      )}
      {/* Controls: search, filters, sort, selection */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
        <input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search habits"
          style={{ flex: 2, minWidth: 180, padding: '8px 10px', borderRadius: 8, border: '1px solid #cdd6e1' }}
        />
        <select
          value={filterFrequency}
          onChange={(e) => setFilterFrequency(e.target.value)}
          style={{ padding: '8px 10px', borderRadius: 8, border: '1px solid #cdd6e1' }}
        >
          <option value="">All frequencies</option>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          style={{ padding: '8px 10px', borderRadius: 8, border: '1px solid #cdd6e1' }}
        >
          <option value="title">Sort by Title</option>
          <option value="frequency">Sort by Frequency</option>
          <option value="streak">Sort by Streak</option>
          <option value="created">Sort by Created</option>
        </select>
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          style={{ padding: '8px 10px', borderRadius: 8, border: '1px solid #cdd6e1' }}
        >
          <option value="">All categories</option>
          {Array.from(new Set(items.map(h => h.meta?.category).filter(Boolean))).map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
        <label style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
          />
          Show Archived
        </label>
        <button
          type="button"
          onClick={() => { setSelectionMode(m => !m); setSelectedIds([]); }}
          style={{ padding: '8px 10px', borderRadius: 8, border: '1px solid #3a6ea5', background: selectionMode ? '#3a6ea5' : '#fff', color: selectionMode ? '#fff' : '#3a6ea5' }}
        >
          {selectionMode ? 'Done Selecting' : 'Select'}
        </button>
        {selectionMode && (
          <button
            type="button"
            onClick={deleteSelected}
            disabled={selectedIds.length === 0}
            style={{ padding: '8px 10px', borderRadius: 8, border: '1px solid #f44336', background: selectedIds.length ? '#f44336' : '#fff', color: selectedIds.length ? '#fff' : '#f44336' }}
          >
            Delete Selected ({selectedIds.length})
          </button>
        )}
      </div>
      {lastAction && (
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 12 }}>
          <span style={{ color: '#7a8a9e', fontSize: 12 }}>Last action: {lastAction.type}. You can undo.</span>
          <button onClick={undoLastAction} style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #3a6ea5', background: '#3a6ea5', color: '#fff', fontSize: 12 }}>Undo</button>
        </div>
      )}
      <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
        {filteredItems.map(it => (
          <div key={it.id} style={card}>
            {/* Selection checkbox */}
            {selectionMode && (
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <input
                  type="checkbox"
                  checked={selectedIds.includes(it.id)}
                  onChange={(e) => {
                    const checked = e.target.checked;
                    setSelectedIds(prev => checked ? [...prev, it.id] : prev.filter(id => id !== it.id));
                  }}
                />
              </div>
            )}
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
            {/* Category and reminder */}
            {(it.meta?.category || it.meta?.reminder) && (
              <div style={{ fontSize: 12, color: '#7a8a9e', marginTop: 4 }}>
                {it.meta?.category && <span>Category: {it.meta.category}</span>}
                {it.meta?.category && it.meta?.reminder && <span> • </span>}
                {it.meta?.reminder && <span>Reminder: {it.meta.reminder}</span>}
              </div>
            )}
            <div style={{ fontSize: 12, color: '#204b72', marginTop: 6 }}>
              Today: {getTodayPercent(it.id) != null ? `${getTodayPercent(it.id)}%` : 'Not logged'}
            </div>
            {/* Progress bar visualization */}
            <div style={{ height: 8, background: '#eef3f8', borderRadius: 6, overflow: 'hidden', marginTop: 6 }} aria-label={`Progress ${getTodayPercent(it.id) || 0}%`}>
              <div style={{ width: `${Math.min(100, Math.max(0, getTodayPercent(it.id) || 0))}%`, height: '100%', background: '#3a6ea5' }} />
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
              {!it.archived && (
                <button
                  onClick={() => setConfirmArchiveId(it.id)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 6,
                    border: '1px solid #ff9800',
                    background: '#fff',
                    color: '#ff9800',
                    fontSize: 12,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="21 8 21 21 3 21 3 8"></polyline>
                    <rect x="1" y="3" width="22" height="5"></rect>
                    <line x1="10" y1="12" x2="14" y2="12"></line>
                  </svg>
                </button>
              )}
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
            {it.archived && (
              <div style={{ 
                marginTop: 8, 
                padding: '4px 8px', 
                backgroundColor: '#fff3e0', 
                color: '#e65100', 
                borderRadius: 4, 
                fontSize: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 4
              }}>
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="21 8 21 21 3 21 3 8"></polyline>
                  <rect x="1" y="3" width="22" height="5"></rect>
                  <line x1="10" y1="12" x2="14" y2="12"></line>
                </svg>
                Archived
              </div>
            )}
            {confirmDeleteId === it.id && (
              <div style={{ 
                marginTop: 8, 
                display: 'flex', 
                flexDirection: 'column', 
                gap: 8, 
                padding: 10, 
                backgroundColor: '#fff9f9', 
                borderRadius: 8, 
                border: '1px solid #ffebee' 
              }}>
                <div style={{ fontSize: 14, fontWeight: 500, color: '#d32f2f' }}>
                  Are you sure you want to delete this habit?
                </div>
                <div style={{ fontSize: 12, color: '#757575', marginBottom: 4 }}>
                  This action cannot be undone.
                </div>
                <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                  <button 
                    onClick={() => setConfirmDeleteId(null)}
                    style={{
                      padding: '8px 16px',
                      borderRadius: 6,
                      border: '1px solid #e0e0e0',
                      background: '#ffffff',
                      color: '#757575',
                      fontSize: 13,
                      fontWeight: 500,
                      cursor: 'pointer'
                    }}
                  >
                    Cancel
                  </button>
                  <button 
                    onClick={() => deleteHabit(it.id)}
                    style={{
                      padding: '8px 16px',
                      borderRadius: 6,
                      border: '1px solid #f44336',
                      background: '#f44336',
                      color: '#fff',
                      fontSize: 13,
                      fontWeight: 500,
                      cursor: 'pointer',
                      boxShadow: '0 2px 4px rgba(244, 67, 54, 0.2)'
                    }}
                  >
                    Delete Habit
                  </button>
                </div>
              </div>
            )}
            {confirmArchiveId === it.id && (
              <div style={{ 
                marginTop: 8, 
                display: 'flex', 
                flexDirection: 'column', 
                gap: 8, 
                padding: 10, 
                backgroundColor: '#fff9c4', 
                borderRadius: 8, 
                border: '1px solid #fff59d' 
              }}>
                <div style={{ fontSize: 14, fontWeight: 500, color: '#ff8f00' }}>
                  Are you sure you want to archive this habit?
                </div>
                <div style={{ fontSize: 12, color: '#757575', marginBottom: 4 }}>
                  You can still view archived habits by enabling "Show Archived" filter.
                </div>
                <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                  <button 
                    onClick={() => setConfirmArchiveId(null)}
                    style={{
                      padding: '8px 16px',
                      borderRadius: 6,
                      border: '1px solid #e0e0e0',
                      background: '#ffffff',
                      color: '#757575',
                      fontSize: 13,
                      fontWeight: 500,
                      cursor: 'pointer'
                    }}
                  >
                    Cancel
                  </button>
                  <button 
                    onClick={() => archiveHabit(it.id)}
                    style={{
                      padding: '8px 16px',
                      borderRadius: 6,
                      border: '1px solid #ff9800',
                      background: '#ff9800',
                      color: '#fff',
                      fontSize: 13,
                      fontWeight: 500,
                      cursor: 'pointer',
                      boxShadow: '0 2px 4px rgba(255, 152, 0, 0.2)'
                    }}
                  >
                    Archive Habit
                  </button>
                </div>
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


