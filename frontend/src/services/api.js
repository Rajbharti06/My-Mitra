const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000/api/v1';

// Simple token storage helpers
const getToken = () => {
  try { return localStorage.getItem('access_token') || null; } catch { return null; }
};
const setToken = (t) => { try { localStorage.setItem('access_token', t); } catch {} };
const clearToken = () => { try { localStorage.removeItem('access_token'); } catch {} };

// Dev-only: ensure a token exists to access protected endpoints during local testing
// This uses the backend's built-in "test_token" accepted in development.
if (process.env.NODE_ENV === 'development') {
  try {
    const existing = localStorage.getItem('access_token');
    if (!existing) {
      localStorage.setItem('access_token', 'test_token');
      // Optional: surface in console for awareness
      // eslint-disable-next-line no-console
      console.info('[dev] Using test_token for local API access');
    }
  } catch {}
}

const request = async (endpoint, options = {}) => {
    const method = (options.method || 'GET').toUpperCase();
    const hasBody = options.body !== undefined && options.body !== null;

    // Only set Content-Type for non-GET or when sending a body to avoid CORS preflight on simple GETs
    const headers = {
        ...(options.headers || {}),
    };
    // Attach auth header if token exists
    const token = getToken();
    if (token) {
        headers['Authorization'] = headers['Authorization'] || `Bearer ${token}`;
    }
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
        const message = errorData.detail || `Request failed with status ${response.status}`;
        // Normalize auth errors for nicer UI messaging
        if (response.status === 401) {
            throw new Error('Not authenticated');
        }
        throw new Error(message);
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

// Auth
export const login = async (username, password) => {
    // Backend expects form-encoded data for OAuth2PasswordRequestForm
    const body = new URLSearchParams();
    body.append('username', username);
    body.append('password', password);
    const resp = await fetch(`${API_BASE}/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body
    });
    if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.detail || 'Login failed');
    }
    const data = await resp.json();
    if (data && data.access_token) {
        setToken(data.access_token);
        return { access_token: data.access_token, token_type: data.token_type };
    }
    throw new Error('Login response missing token');
};

// Habit endpoints
export const createHabit = (habitData) => {
    return request('/habits', {
        method: 'POST',
        body: JSON.stringify(habitData),
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

export const updateHabit = (habitId, habitData) => {
    return request(`/habits/${habitId}`, {
        method: 'PUT',
        body: JSON.stringify(habitData),
    });
};

export const archiveHabit = (habitId) => {
    return request(`/habits/${habitId}/archive`, {
        method: 'PUT'
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

export const isAuthenticated = () => !!getToken();
export const logout = async () => { clearToken(); return { message: 'Logged out' }; };
export const switchPersonality = (type) => request(`/personality/switch/${type}`, { method: 'POST' });
