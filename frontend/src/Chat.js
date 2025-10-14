import React, { useState, useEffect, useRef } from 'react';
import './Chat.css';
import ConversationalCard from './components/ConversationalCard'; // Import the new component
import CryptoJS from 'crypto-js';
import * as api from './services/api';

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const chatWindowRef = useRef(null);

  const ENCRYPTION_KEY = 'my_mitra_secret_key'; // In production, use a user-specific key or passphrase

  const encryptData = (data) => {
    return CryptoJS.AES.encrypt(JSON.stringify(data), ENCRYPTION_KEY).toString();
  };
  
  const decryptData = (ciphertext) => {
    try {
      const bytes = CryptoJS.AES.decrypt(ciphertext, ENCRYPTION_KEY);
      const decrypted = bytes.toString(CryptoJS.enc.Utf8);
      return JSON.parse(decrypted);
    } catch {
      return null;
    }
  };
  
  const saveMessageToLocalStorage = (message) => {
    const storedCipher = localStorage.getItem('offlineMessages');
    const storedMessages = storedCipher ? decryptData(storedCipher) : [];
    const newCipher = encryptData([...storedMessages, message]);
    localStorage.setItem('offlineMessages', newCipher);
  };
  
  const getOfflineMessages = () => {
    const storedCipher = localStorage.getItem('offlineMessages');
    return storedCipher ? decryptData(storedCipher) : [];
  };
  
  const clearOfflineMessages = () => {
    localStorage.removeItem('offlineMessages');
  };

  const [isOnline, setIsOnline] = useState(navigator.onLine);

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

  useEffect(() => {
    if (isOnline) {
      const offlineMessages = getOfflineMessages();
      if (offlineMessages.length > 0) {
        // Optionally, display a message to the user that offline messages are being sent
        setMessages(prevMessages => [...prevMessages, { sender: 'system', text: "Sending queued offline messages...", timestamp: new Date().toISOString() }]);
        offlineMessages.forEach(async (msg) => {
          // Re-send each message. This might need a more robust retry mechanism.
          await sendMessage(msg.text, true); // Pass true to indicate it's a re-sent message
        });
        clearOfflineMessages();
      }
    }
  }, [isOnline]);

  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const sendMessage = async (messageText = input, isResending = false) => {
    if (!messageText.trim()) return;

    const userMessage = { sender: 'user', text: messageText, timestamp: new Date().toISOString() };
    if (!isResending) {
      setMessages(prevMessages => [...prevMessages, userMessage]);
    }
    setInput('');
    setIsTyping(true);
    setError(null);
    setIsLoading(true);

    if (!isOnline) {
      saveMessageToLocalStorage(userMessage);
      if (!isResending) {
        setMessages(prevMessages => [...prevMessages, { sender: 'system', text: "You are offline. Message will be sent when online.", timestamp: new Date().toISOString() }]);
      }
      setIsTyping(false);
      setIsLoading(false);
      return;
    }

    try {
      const data = await api.sendMessage(messageText);
      const timestamp = new Date().toISOString();
      const newMessages = [];

      if (data.response) {
        newMessages.push({ sender: 'ai', text: data.response, timestamp });
      }
      if (data.cbt_guidance) {
        newMessages.push({ sender: 'cbt', text: data.cbt_guidance, timestamp });
      }
      // Handle conversational cards
      if (data.card_data && data.card_type) {
        newMessages.push({ sender: 'ai', card_type: data.card_type, card_data: data.card_data, timestamp });
      }

      setMessages(prevMessages => [...prevMessages, ...newMessages]);
    } catch (error) {
      console.error('Error sending message:', error);
      setError(error.message || 'An unexpected error occurred.');
      const errorMessage = { 
        sender: 'system', 
        text: error.message || 'An unexpected error occurred. Please try again.', 
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsTyping(false);
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div style={{ padding: '8px 16px', borderBottom: '1px solid #e6e9ef', background: '#fff' }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {['I’m feeling stressed about exams', 'Can you help me sleep better?', 'I had a tough day', 'Let’s plan a tiny habit'].map((q) => (
            <button key={q} onClick={() => setInput(q)} style={{ border: '1px solid #cdd6e1', background: '#ffffff', color: '#3a6ea5', borderRadius: 16, padding: '6px 10px', cursor: 'pointer' }}>{q}</button>
          ))}
        </div>
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
                  <div>{msg.text}</div>
                )}
                <div style={{ fontSize: '12px', color: '#7a8a9e', marginTop: '8px', textAlign: 'right' }}>
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="message ai">
            <div className="message-content">
              <div className="message-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#7a8a9e" strokeWidth="2"/>
                  <path d="M2 17L12 22L22 17" stroke="#7a8a9e" strokeWidth="2"/>
                  <path d="M2 12L12 17L22 12" stroke="#7a8a9e" strokeWidth="2"/>
                </svg>
              </div>
              <div className="message-bubble typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
      </div>
      <div className="input-area">
        {error && <div className="error-message">{error}</div>}
        <div className="quick-prompts">
          {[
            "How are you feeling today?",
            "I'm feeling anxious about work",
            "Help me challenge negative thoughts",
            "I want to practice gratitude",
            "I'm having trouble sleeping",
            "Help me with social anxiety",
            "I feel overwhelmed",
            "Teach me breathing exercises",
            "I want to build better habits",
            "Help me with self-compassion"
          ].map((prompt, index) => (
            <button
              key={index}
              onClick={() => setInput(prompt)}
              className="prompt-chip"
            >
              {prompt}
            </button>
          ))}
        </div>
        <div className="input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !isLoading && sendMessage(input)}
            placeholder="Message MyMitra..."
            disabled={isLoading}
          />
          <button 
            onClick={() => sendMessage(input)} 
            disabled={isLoading || !input.trim()}
            className={isLoading ? 'loading' : ''}
          >
            {isLoading ? (
              <div className="button-spinner"></div>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13"/>
                <path d="M22 2L15 22L11 13L2 9L22 2Z"/>
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Chat;
