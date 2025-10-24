const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000/api/v1';

const request = async (endpoint, options = {}) => {
    const method = (options.method || 'GET').toUpperCase();
    const hasBody = options.body !== undefined && options.body !== null;

    // Only set Content-Type for non-GET or when sending a body to avoid CORS preflight on simple GETs
    const headers = {
        ...(options.headers || {}),
    };
    if (hasBody || method !== 'GET') {
        headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        method,
        headers,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed with status ${response.status}`);
    }

    return response.json();
};

// Chat endpoints
export const sendMessage = (message, sessionId, personality) => {
    return request('/chat/', {
        method: 'POST',
        body: JSON.stringify({ message, session_id: sessionId, personality }),
    });
};

export const getAvailablePersonalities = () => {
    return request('/chat/personalities');
};

export const getChatHistory = (limit = 20, sessionId = null) => {
    const query = sessionId ? `?limit=${limit}&session_id=${encodeURIComponent(sessionId)}` : `?limit=${limit}`;
    return request(`/chat/history${query}`);
};

export const listSessions = () => {
    return request('/chat/sessions');
};

export const deleteSession = (sessionId) => {
    return request(`/chat/session/${encodeURIComponent(sessionId)}`, {
        method: 'DELETE',
    });
};

export const deleteAllChats = () => {
    return request('/chat/all', { method: 'DELETE' });
};

// Habit endpoints
export const createHabit = (title, description, frequency) => {
    return request('/habits', {
        method: 'POST',
        body: JSON.stringify({ title, description, frequency }),
    });
};

export const getHabits = () => {
    return request('/habits');
};

export const completeHabit = (habitId) => {
    return request(`/habits/${habitId}/complete`, {
        method: 'POST',
    });
};

export const updateHabit = (habitId, updates) => {
    return request(`/habits/${habitId}`, {
        method: 'PUT',
        body: JSON.stringify(updates),
    });
};

export const deleteHabit = (habitId) => {
    return request(`/habits/${habitId}`, {
        method: 'DELETE',
    });
};

// Journals
export const getJournals = () => {
    return request('/journals');
};

export const createJournal = (title, content) => {
    // Backend expects JournalCreate: { content, mood? } — mapping title to content if needed
    return request('/journals', {
        method: 'POST',
        body: JSON.stringify({ content: `${title}: ${content}` }),
    });
};

// Insights & health
export const getInsights = () => {
    return request('/insights');
};

export const healthCheck = () => {
    return request('/health');
};

export const exportData = () => {
    return request('/export');
};

// Auth-like helpers (stubs for now)
export const isAuthenticated = () => true;
export const logout = () => Promise.resolve({ message: 'Logged out' });
export const switchPersonality = (type) => request(`/personality/switch/${type}`, { method: 'POST' });
