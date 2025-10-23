const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000/api/v1';

const request = async (endpoint, options = {}) => {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed with status ${response.status}`);
    }

    return response.json();
};

export const login = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await request('/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
    });

    // Store tokens in localStorage
    if (response.access_token) {
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('token_type', response.token_type);
    }

    return response;
};

export const register = (username, email, password) => {
    return request('/register', {
        method: 'POST',
        body: JSON.stringify({ username, email, password }),
    });
};

export const sendMessage = (message, personality = 'mitra', sessionId = null, emotion = 'neutral') => {
    return request('/chat/', {
        method: 'POST',
        body: JSON.stringify({ 
            message, 
            personality,
            session_id: sessionId,
            user_emotion: emotion
        }),
    });
};

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

export const getJournals = () => {
    return request('/journals');
};

// Enhanced journal API with emotion support
export const createJournal = (content, mood, date = null) => {
    return request('/journals', {
        method: 'POST',
        body: JSON.stringify({ 
            content, 
            mood, 
            date: date || new Date().toISOString().split('T')[0]
        }),
    });
};

// Get journal entries with filtering
export const getJournalEntries = (limit = 50, emotion = null) => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (emotion) params.append('emotion', emotion);
    return request(`/journals?${params.toString()}`);
};

// Emotion tracking
export const trackEmotion = (emotion, intensity = 'medium', context = null) => {
    return request('/emotions/track', {
        method: 'POST',
        body: JSON.stringify({
            emotion,
            intensity,
            context,
            timestamp: new Date().toISOString()
        }),
    });
};

export const getEmotionHistory = (days = 7) => {
    return request(`/emotions/history?days=${days}`);
};

// Enhanced habits with emotion correlation
export const updateHabitProgress = (habitId, completed = true, emotion = null) => {
    return request(`/habits/${habitId}/progress`, {
        method: 'POST',
        body: JSON.stringify({ 
            completed, 
            emotion,
            timestamp: new Date().toISOString()
        }),
    });
};

export const getAvailablePersonalities = () => {
    return request('/chat/personalities');
};

// Authentication helpers
export const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
};

export const isAuthenticated = () => {
    return true; // Always authenticated for open access
};

// Chat management
export const getChatHistory = (limit = 20) => {
    return request(`/chat/history?limit=${limit}`);
};

export const switchPersonality = (personality) => {
    return request('/chat/personality', {
        method: 'POST',
        body: JSON.stringify({ personality }),
    });
};

// Insights
export const getInsights = () => {
    return request('/insights');
};

// Health check
export const healthCheck = () => {
    return fetch('http://localhost:8000/health').then(res => res.json());
};

// Export data
export const exportData = () => {
    return request('/me/export');
};
