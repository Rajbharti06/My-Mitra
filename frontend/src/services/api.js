const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000/api/v1';

// Simple token storage helpers
const getToken = () => {
  try { return localStorage.getItem('access_token') || null; } catch { return null; }
};
const setToken = (t) => { try { localStorage.setItem('access_token', t); } catch {} };
const clearToken = () => { try { localStorage.removeItem('access_token'); } catch {} };

let _onAuthFailure = null;
export const setAuthFailureCallback = (cb) => { _onAuthFailure = cb; };

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
            if (_onAuthFailure) _onAuthFailure();
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

export const createJournalEntry = (content, mood) =>
    request('/journals', { method: 'POST', body: JSON.stringify({ content, mood }) });

export const register = async (username, password) => {
    const resp = await fetch(`${API_BASE}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
    });
    if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.detail || 'Registration failed');
    }
    return resp.json();
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

// Adaptive memory
export const getMemoryPreferences = () => request('/memory/preferences');
export const updateMemoryPreferences = (prefs) =>
  request('/memory/preferences', { method: 'PUT', body: JSON.stringify(prefs) });

// System actions (authorized, allowlisted)
export const getSystemCapabilities = () => request('/system/capabilities');
export const previewSystemAction = (action_type, params = {}) =>
  request('/system/actions/preview', {
    method: 'POST',
    body: JSON.stringify({ action_type, params }),
  });
export const commitSystemAction = (approval_id, approve) =>
  request('/system/actions/commit', {
    method: 'POST',
    body: JSON.stringify({ approval_id, approve }),
  });

// ── Streaming SSE Chat ──────────────────────────────────────────────
/**
 * Stream a chat message via Server-Sent Events.
 * Returns a ReadableStream that yields SSE events:
 *   - thinking: personality-driven thinking indicator
 *   - memory_recall: "I remember…" moment
 *   - emotion: detected user emotion
 *   - token: individual word of AI response
 *   - done: final metadata
 *
 * @param {string} message
 * @param {string} sessionId
 * @param {string} personality
 * @param {function} onEvent - callback(eventType, data)
 * @returns {Promise<object>} - final "done" event data
 */
export const streamMessage = async (message, sessionId, personality, onEvent) => {
    const token = getToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ message, session_id: sessionId, personality }),
    });

    if (!response.ok) {
        throw new Error(`Stream failed: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let finalData = null;

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));
                    if (onEvent) onEvent(data.type, data);
                    if (data.type === 'done') finalData = data;
                } catch (e) {
                    console.warn('SSE parse error:', e);
                }
            }
        }
    }

    return finalData;
};

// ── Slash Commands ──────────────────────────────────────────────────
export const sendSlashCommand = (command, sessionId) => {
    return request('/chat/command', {
        method: 'POST',
        body: JSON.stringify({ command, session_id: sessionId }),
    });
};

// ── AI Initiative (proactive check-ins) ─────────────────────────────
export const checkInitiative = () => request('/chat/initiative');

// ── Emotion Patterns ────────────────────────────────────────────────
export const getEmotionPatterns = () => request('/chat/patterns');

// ── Growth Engine ────────────────────────────────────────────────────
export const getGrowthArc = () => request('/growth/arc');
export const getGrowthTopics = () => request('/growth/topics');
export const recordMilestone = (text) => request(`/growth/milestone?text=${encodeURIComponent(text)}`, { method: 'POST' });

// ── Mood Check-In ─────────────────────────────────────────────────────
export const logMood = (mood, intensity = 'medium', note = null) =>
    request('/mood/log', { method: 'POST', body: JSON.stringify({ mood, intensity, note }) });

export const getMoodHistory = (limit = 30) =>
    request(`/mood/history?limit=${limit}`);
