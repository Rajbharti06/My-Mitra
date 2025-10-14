const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

const request = async (endpoint, options = {}) => {
    const token = localStorage.getItem('token');
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        // Redirect to login or handle unauthorized access
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed with status ${response.status}`);
    }

    return response.json();
};

export const login = (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    return request('/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
    });
};

export const register = (username, password) => {
    return request('/register', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
    });
};

export const sendMessage = (userInput) => {
    return request('/chat/', {
        method: 'POST',
        body: JSON.stringify({ user_input: userInput }),
    });
};

export const getHabits = () => {
    return request('/habits');
};

export const createHabit = (title, frequency) => {
    return request('/habits', {
        method: 'POST',
        body: JSON.stringify({ title, frequency }),
    });
};

export const completeHabit = (habitId) => {
    return request(`/habits/${habitId}/complete`, {
        method: 'POST',
    });
};

export const getJournals = () => {
    return request('/journals');
};

export const createJournal = (content, mood) => {
    return request('/journals', {
        method: 'POST',
        body: JSON.stringify({ content, mood }),
    });
};
