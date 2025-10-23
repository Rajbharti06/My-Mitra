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

export const getChatHistory = (limit = 20) => {
    return request(`/chat/history?limit=${limit}`);
};

export const switchPersonality = (personality) => {
    return request('/chat/personality', {
        method: 'POST',
        body: JSON.stringify({ personality }),
    });
};

// Habits
export const getHabits = () => {
    return request('/habits');
};

export const createHabit = (title, frequency, description = null) => {
    return request('/habits', {
        method: 'POST',
        body: JSON.stringify({ title, frequency, description }),
    });
};

export const completeHabit = (habitId) => {
    return request(`/habits/${habitId}/complete`, {
        method: 'POST',
    });
};

export const updateHabit = (habitId, habitData) => {
    return request(`/habits/${habitId}`, {
        method: 'PUT',
        body: JSON.stringify(habitData),
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

// Insights
export const getInsights = () => {
    return request('/insights');
};

// Authentication helpers (open access defaults)
export const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
};

export const isAuthenticated = () => {
    return true; // Always authenticated for open access
};

// Health check
export const healthCheck = () => {
    return request('/health');
};

// Export data
export const exportData = () => {
    return request('/me/export');
};
