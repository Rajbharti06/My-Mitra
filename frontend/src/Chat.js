import React, { useState, useEffect, useRef } from 'react';
import './Chat.css';
import ConversationalCard from './components/ConversationalCard'; // Import the new component
import * as api from './services/api';
import { setPassphrase } from './services/security';

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentPersonality, setCurrentPersonality] = useState(() => localStorage.getItem('defaultPersonality') || 'default');
  const [availablePersonalities, setAvailablePersonalities] = useState([]);
  const [preferencesOpen, setPreferencesOpen] = useState(false);
  const [localPassphraseInput, setLocalPassphraseInput] = useState('');
  const [sessionId] = useState(() => {
    const existing = localStorage.getItem('sessionId');
    if (existing) return existing;
    const newId = (window.crypto && window.crypto.randomUUID) ? window.crypto.randomUUID() : Math.random().toString(36).slice(2);
    localStorage.setItem('sessionId', newId);
    return newId;
  });
  const chatWindowRef = useRef(null);

  useEffect(() => {
    // Load available personalities on component mount
    const loadPersonalities = async () => {
      try {
        const personalities = await api.getAvailablePersonalities();
        setAvailablePersonalities(personalities);
      } catch (error) {
        console.error('Error loading personalities:', error);
      }
    };
    loadPersonalities();
    // Load recent chat history for continuity
    const loadHistory = async () => {
      try {
        const resp = await api.getChatHistory(50);
        const history = Array.isArray(resp?.messages) ? resp.messages : [];
        const mapped = history.map((m) => ({
          sender: m.role === 'assistant' ? 'ai' : (m.role === 'user' ? 'user' : 'system'),
          text: m.content,
          timestamp: new Date().toISOString()
        }));
        if (mapped.length) {
          setMessages(mapped);
        }
      } catch (error) {
        console.error('Error loading chat history:', error);
      }
    };
    loadHistory();
  }, []);

  const handleSend = async () => {
    if (!input.trim()) return;
    setIsLoading(true);
    setError(null);
    setIsTyping(true);
    const userMessage = { sender: 'user', text: input, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch(`${process.env.REACT_APP_API_BASE || 'http://localhost:8000/api/v1'}/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, personality: currentPersonality, session_id: sessionId })
      });
      const data = await response.json();
      const aiMessage = { sender: 'ai', text: data.response, timestamp: new Date().toISOString(), card_type: data.card_type || null, card_data: data.card_data || null };
      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      console.error(err);
      setError('Unable to reach the assistant. Please try again.');
    } finally {
      setIsLoading(false);
      setIsTyping(false);
      setInput('');
      chatWindowRef.current?.scrollTo({ top: chatWindowRef.current.scrollHeight, behavior: 'smooth' });
    }
  };

  const handlePersonalitySwitch = async (personality) => {
    try {
      await api.switchPersonality(personality);
      setCurrentPersonality(personality);
      localStorage.setItem('defaultPersonality', personality);
      const systemMessage = {
        sender: 'system',
        text: `Switched to ${personality} personality`,
        timestamp: new Date().toISOString()
      };
      setMessages(prevMessages => [...prevMessages, systemMessage]);
    } catch (error) {
      console.error('Error switching personality:', error);
      setError(`Failed to switch to ${personality} personality`);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-toolbar">
        <div className="toolbar-inner">
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span className="toolbar-label">Personality:</span>
            {availablePersonalities.map((p) => (
              <button
                key={p.type}
                onClick={() => handlePersonalitySwitch(p.type)}
                className={`persona-chip ${currentPersonality === p.type ? 'persona-chip--active' : ''}`}
              >
                {p.name || p.type}
              </button>
            ))}
            <button onClick={() => setPreferencesOpen(v => !v)} className="persona-chip">Preferences</button>
          </div>
        </div>
        {preferencesOpen && (
          <div className="preferences-panel container">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 12, color: '#666' }}>Default personality:</span>
              <select
                value={currentPersonality}
                onChange={(e) => handlePersonalitySwitch(e.target.value)}
                style={{ border: '1px solid #cdd6e1', borderRadius: 8, padding: '4px 8px', color: '#3a6ea5' }}
              >
                {availablePersonalities.map((p) => (
                  <option key={p.type} value={p.type}>{p.name || p.type}</option>
                ))}
              </select>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 12, color: '#666' }}>Encryption passphrase:</span>
              <input
                type="password"
                value={localPassphraseInput}
                onChange={(e) => setLocalPassphraseInput(e.target.value)}
                placeholder="Set passphrase"
                style={{ border: '1px solid #cdd6e1', borderRadius: 8, padding: '4px 8px' }}
              />
              <button
                onClick={() => setPassphrase(localPassphraseInput)}
                className="persona-chip"
              >
                Save
              </button>
            </div>
          </div>
        )}
      </div>
      <div className="chat-window" ref={chatWindowRef}>
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            <div className="message-content">
              <div className="message-icon">
                {msg.sender === 'user' ? (
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="11" stroke="#7a8a9e" strokeWidth="2"/>
                    <circle cx="12" cy="10" r="4" stroke="#7a8a9e" strokeWidth="2"/>
                    <path d="M4 19C4 16 8 13 12 13C16 13 20 16 20 19" stroke="#7a8a9e" strokeWidth="2"/>
                  </svg>
                ) : msg.sender === 'ai' ? (
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#7a8a9e" strokeWidth="2"/>
                    <path d="M2 17L12 22L22 17" stroke="#7a8a9e" strokeWidth="2"/>
                    <path d="M2 12L12 17L22 12" stroke="#7a8a9e" strokeWidth="2"/>
                  </svg>
                ) : (
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2Z" stroke="#7a8a9e" strokeWidth="2"/>
                    <path d="M12 6V12L16 14" stroke="#7a8a9e" strokeWidth="2"/>
                  </svg>
                )}
              </div>
              <div className="message-bubble">
                {msg.card_type ? (
                  <ConversationalCard type={msg.card_type} data={msg.card_data} />
                ) : (
                  msg.text
                )}
              </div>
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="message ai">
            <div className="message-content">
              <div className="message-icon" />
              <div className="message-bubble typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
      </div>
      {error && <div className="error-message">{error}</div>}
      <div className="input-area">
        <div className="quick-prompts">
          {['Feeling stressed', 'Give me a journal prompt', 'Suggest a small habit'].map(p => (
            <button key={p} className="prompt-chip" onClick={() => setInput(p)}>{p}</button>
          ))}
        </div>
        <div className="input-container">
          <input
            type="text"
            placeholder="Type your message…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
          <button onClick={handleSend} disabled={isLoading} aria-label="Send message">
            {isLoading ? <div className="button-spinner" /> : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Chat;
