import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Settings, Smile, Heart, Frown, Meh, Angry, Trash2, PlusCircle, Wifi, WifiOff } from 'lucide-react';
import { toast } from 'react-toastify';
import { getEmotionColor, getEmotionEmoji } from './utils/theme';
import * as api from './services/api';
import { setPassphrase } from './services/security';

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentPersonality, setCurrentPersonality] = useState(() => localStorage.getItem('defaultPersonality') || 'mitra');
  const [availablePersonalities, setAvailablePersonalities] = useState([]);
  const [preferencesOpen, setPreferencesOpen] = useState(false);
  const [localPassphraseInput, setLocalPassphraseInput] = useState('');
  const [currentEmotion, setCurrentEmotion] = useState({ emotion: 'neutral', intensity: 'medium' });
  const [sessionId, setSessionId] = useState(() => {
    const existing = localStorage.getItem('sessionId');
    if (existing) return existing;
    const newId = (window.crypto && window.crypto.randomUUID) ? window.crypto.randomUUID() : Math.random().toString(36).slice(2);
    localStorage.setItem('sessionId', newId);
    return newId;
  });
  const [sessions, setSessions] = useState(() => {
    const raw = localStorage.getItem('chat_sessions');
    return raw ? JSON.parse(raw) : [];
  });
  const [confirmDeleteSessionId, setConfirmDeleteSessionId] = useState(null);
  // Add display name state for personalization
  const [displayName, setDisplayName] = useState(() => localStorage.getItem('displayName') || '');
  
  // WebSocket related state
  const [wsConnection, setWsConnection] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected'); // 'connected', 'connecting', 'disconnected', 'error'
  const [remoteTyping, setRemoteTyping] = useState(false);
  const [messageQueue, setMessageQueue] = useState([]);
  
  const chatWindowRef = useRef(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const saveSessions = (next) => {
    setSessions(next);
    localStorage.setItem('chat_sessions', JSON.stringify(next));
  };

  const saveMessagesForSession = (sid, msgs) => {
    localStorage.setItem(`chat_messages_${sid}`, JSON.stringify(msgs));
  };

  const loadMessagesForSession = (sid) => {
    const raw = localStorage.getItem(`chat_messages_${sid}`);
    return raw ? JSON.parse(raw) : [];
  };

  const setPersonality = (type) => {
    try {
      setCurrentPersonality(type);
      localStorage.setItem('defaultPersonality', type);
      toast.success(`Personality switched to ${type}`);
      setPreferencesOpen(false);
    } catch (err) {
      console.error('Failed to set personality:', err);
      toast.error('Failed to switch personality');
    }
  };

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (!api.isAuthenticated || !api.isAuthenticated()) {
      return; // Only connect WebSocket for authenticated users
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    setConnectionStatus('connecting');
    
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/chat/${sessionId}`;
      
      const token = localStorage.getItem('token');
      const ws = new WebSocket(`${wsUrl}?token=${encodeURIComponent(token)}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        setWsConnection(ws);
        wsRef.current = ws;
        reconnectAttemptsRef.current = 0;
        
        // Process queued messages
        if (messageQueue.length > 0) {
          messageQueue.forEach(msg => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify(msg));
            }
          });
          setMessageQueue([]);
        }
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setConnectionStatus('disconnected');
        setWsConnection(null);
        wsRef.current = null;
        setRemoteTyping(false);
        
        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connectWebSocket();
          }, delay);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
        setError('Connection error. Messages will be sent via HTTP.');
      };
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus('error');
    }
  }, [sessionId, messageQueue]);

  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
    
    setWsConnection(null);
    setConnectionStatus('disconnected');
    setRemoteTyping(false);
  }, []);

  const handleWebSocketMessage = useCallback((data) => {
    switch (data.type) {
      case 'message':
        const aiMessage = {
          sender: 'ai',
          text: data.message,
          timestamp: data.timestamp || new Date().toISOString(),
          emotion: data.emotion || 'neutral'
        };
        setMessages(prev => [...prev, aiMessage]);
        break;
        
      case 'typing_indicator':
        setRemoteTyping(data.typing);
        break;
        
      case 'message_status':
        if (data.status === 'error') {
          setError(data.message || 'Message delivery failed');
          toast.error('Message delivery failed');
        }
        break;
        
      case 'pong':
        // Handle ping/pong for connection health
        break;
        
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  }, []);

  const sendWebSocketMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    } else {
      // Queue message for later delivery
      setMessageQueue(prev => [...prev, message]);
      return false;
    }
  }, []);

  const sendTypingIndicator = useCallback((typing) => {
    sendWebSocketMessage({
      type: 'typing_indicator',
      typing: typing
    });
  }, [sendWebSocketMessage]);

  const createNewSession = () => {
    const newId = (window.crypto && window.crypto.randomUUID) ? window.crypto.randomUUID() : Math.random().toString(36).slice(2);
    const newSession = { id: newId, title: 'New Chat', createdAt: new Date().toISOString() };
    const next = [newSession, ...sessions];
    saveSessions(next);
    setSessionId(newId);
    localStorage.setItem('sessionId', newId);
    setMessages([]);
    saveMessagesForSession(newId, []);
  };

  const deleteSession = async (sid) => {
    // Keep a snapshot of previous sessions for potential restore
    const prevSessions = [...sessions];

    // Immediately update UI and local storage to reflect deletion
    const next = sessions.filter(s => s.id !== sid);
    saveSessions(next);
    localStorage.removeItem(`chat_messages_${sid}`);
    setConfirmDeleteSessionId(null);

    // Handle current session deletion by switching or creating a new one
    if (sid === sessionId) {
      if (next.length) {
        const first = next[0];
        setSessionId(first.id);
        localStorage.setItem('sessionId', first.id);
        setMessages(loadMessagesForSession(first.id));
      } else {
        createNewSession();
      }
    }

    // If not authenticated, perform local-only deletion and inform the user
    const authenticated = (api.isAuthenticated && api.isAuthenticated());
    if (!authenticated) {
      toast.info('Chat deleted locally. Log in to delete server history.');
      return;
    }

    try {
      await api.deleteSession(sid);
      toast.success('Chat session permanently deleted');
    } catch (err) {
      console.error('Error deleting session:', err);
      // Keep local deletion, but inform user that server-side removal failed
      toast.error('Server deletion failed. Chat removed locally only.');
      // Optional: If you prefer to restore UI on failure, uncomment below:
      // saveSessions(prevSessions);
    }
  };

  const openSession = (sid) => {
    setSessionId(sid);
    localStorage.setItem('sessionId', sid);
    const msgs = loadMessagesForSession(sid);
    setMessages(msgs);
  };

  useEffect(() => {
    // Load available personalities on component mount
    const loadPersonalities = async () => {
      try {
        const personalities = await api.getAvailablePersonalities();
        setAvailablePersonalities(personalities);
      } catch (error) {
        console.error('Error loading personalities:', error);
        toast.error('Failed to load personalities');
      }
    };
    loadPersonalities();
    
    // Load session messages or session-scoped chat history
    const existingMsgs = loadMessagesForSession(sessionId);
    if (existingMsgs.length) {
      setMessages(existingMsgs);
    } else {
      const loadHistory = async () => {
        try {
          const resp = await api.getChatHistory(50, sessionId);
          const history = Array.isArray(resp?.messages) ? resp.messages : [];
          const mapped = history.map((m) => ({
            sender: m.role === 'assistant' ? 'ai' : (m.role === 'user' ? 'user' : 'system'),
            text: m.content,
            timestamp: m.timestamp || new Date().toISOString(),
            emotion: m.emotion || 'neutral'
          }));
          if (mapped.length) {
            setMessages(mapped);
            saveMessagesForSession(sessionId, mapped);
            // initialize a session if none
            if (!sessions.find(s => s.id === sessionId)) {
              const title = mapped.find(m => m.sender === 'user')?.text?.slice(0, 30) || 'New Chat';
              saveSessions([{ id: sessionId, title, createdAt: new Date().toISOString() }, ...sessions]);
            }
          }
        } catch (error) {
          console.error('Error loading chat history:', error);
        }
      };
      loadHistory();
    }

    // Optional: fetch server sessions (if authenticated)
    (async () => {
      try {
        const serverSessions = await api.listSessions();
        if (Array.isArray(serverSessions?.sessions)) {
          const merged = [...serverSessions.sessions.map(s => ({ id: s.id, title: 'Chat', createdAt: s.last_activity || new Date().toISOString() })), ...sessions];
          // Deduplicate by id
          const dedup = merged.reduce((acc, s) => acc.some(x => x.id === s.id) ? acc : [...acc, s], []);
          saveSessions(dedup);
        }
      } catch (e) {
        // Ignore if not authenticated
      }
    })();

    // Initialize WebSocket connection for authenticated users
    connectWebSocket();

    // Cleanup on unmount
    return () => {
      disconnectWebSocket();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // WebSocket connection effect for session changes
  useEffect(() => {
    if (api.isAuthenticated && api.isAuthenticated()) {
      disconnectWebSocket();
      setTimeout(() => connectWebSocket(), 100); // Small delay to ensure clean reconnection
    }
  }, [sessionId, connectWebSocket, disconnectWebSocket]);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, [disconnectWebSocket]);

  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    // persist messages to session
    saveMessagesForSession(sessionId, messages);
    // update session title from first user message
    const firstUserMsg = messages.find(m => m.sender === 'user');
    if (firstUserMsg) {
      const title = firstUserMsg.text.slice(0, 30);
      const next = sessions.map(s => s.id === sessionId ? { ...s, title } : s);
      saveSessions(next);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, sessionId]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = {
      sender: 'user',
      text: input.trim(),
      timestamp: new Date().toISOString(),
      emotion: currentEmotion.emotion
    };

    setMessages(prev => [...prev, userMessage]);
    const messageText = input.trim();
    setInput('');
    setIsTyping(true);
    setError(null);

    // Send typing indicator via WebSocket
    sendTypingIndicator(true);

    try {
      // Try WebSocket first for real-time delivery
      const wsMessage = {
        type: 'user_message',
        message: messageText,
        personality: currentPersonality,
        session_id: sessionId,
        emotion: currentEmotion.emotion
      };

      const wsDelivered = sendWebSocketMessage(wsMessage);
      
      // Always send via HTTP API as fallback and for persistence
      const response = await api.sendMessage(messageText, sessionId, currentPersonality);
      
      // If WebSocket wasn't available, add AI response from HTTP
      if (!wsDelivered) {
        const aiMessage = {
          sender: 'ai',
          text: response.response || response.message || 'I apologize, but I couldn\'t process your message.',
          timestamp: response.created_at || new Date().toISOString(),
          emotion: response.detected_emotion || 'neutral'
        };
        setMessages(prev => [...prev, aiMessage]);
      }

      // Align session ID with server in case it generated a new one
      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id);
        localStorage.setItem('sessionId', response.session_id);
        // Ensure session list contains the server session
        if (!sessions.find(s => s.id === response.session_id)) {
          const title = userMessage.text.slice(0, 30) || 'New Chat';
          saveSessions([{ id: response.session_id, title, createdAt: response.created_at || new Date().toISOString() }, ...sessions]);
        }
      }
      
      if (response.detected_emotion) {
        setCurrentEmotion({
          emotion: response.detected_emotion,
          intensity: response.emotion_intensity || 'medium'
        });
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
      toast.error('Failed to send message');
      
      // Send error status via WebSocket if connected
      if (connectionStatus === 'connected') {
        sendWebSocketMessage({
          type: 'error',
          message: 'Failed to process message'
        });
      }

      // Client-side fallback reply to keep conversation flowing
      const fallbackText = "I'm having a bit of trouble right now, but I'm still here with you. What's on your mind?";
      const aiMessage = {
        sender: 'ai',
        text: fallbackText,
        timestamp: new Date().toISOString(),
        emotion: 'neutral'
      };
      const nextMsgs = [...messages, aiMessage];
      setMessages(nextMsgs);
      saveMessagesForSession(sessionId, nextMsgs);
    } finally {
      setIsTyping(false);
      sendTypingIndicator(false);
    }
  };

  return (
    <div className="flex h-screen bg-cream dark:bg-dark-bg">
      {/* Sidebar: Chat Sessions */}
      <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-4 flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Chats</h2>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={createNewSession}
            className="p-2 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
            title="New Chat"
          >
            <PlusCircle size={16} />
          </motion.button>
        </div>
        <div className="flex-1 overflow-y-auto space-y-2">
          {sessions.length === 0 ? (
            <div className="text-xs text-gray-500 dark:text-gray-400">No chats yet</div>
          ) : (
            sessions.map(s => (
              <div key={s.id} className={`group flex items-center justify-between px-2 py-2 rounded-lg cursor-pointer ${sessionId === s.id ? 'bg-cream dark:bg-gray-700' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}`} onClick={() => openSession(s.id)}>
                <div className="text-xs text-gray-700 dark:text-gray-300 truncate pr-2">{s.title}</div>
                {confirmDeleteSessionId === s.id ? (
                  <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                    <button
                      className="text-xs px-2 py-1 rounded bg-red-600 text-white"
                      onClick={() => { deleteSession(s.id); setConfirmDeleteSessionId(null); }}
                    >
                      Confirm
                    </button>
                    <button
                      className="text-xs px-2 py-1 rounded bg-gray-300 dark:bg-gray-600 text-gray-800 dark:text-gray-200"
                      onClick={() => setConfirmDeleteSessionId(null)}
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={(e) => { e.stopPropagation(); setConfirmDeleteSessionId(s.id); }}
                    className="p-1 rounded bg-red-100 dark:bg-red-900 text-red-600 dark:text-red-300 opacity-0 group-hover:opacity-100"
                    title="Delete"
                  >
                    <Trash2 size={14} />
                  </motion.button>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header with Connection Status */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
              Chat with {currentPersonality === 'mitra' ? 'Mitra' : currentPersonality}
            </h1>
            {remoteTyping && (
              <div className="text-xs text-gray-500 dark:text-gray-400 italic">
                Mitra is typing...
              </div>
            )}
        </div>
        <div className="flex items-center gap-2">
            {/* Connection Status Indicator */}
            <div className="flex items-center gap-2">
              {connectionStatus === 'connected' ? (
                <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
                  <Wifi size={16} />
                  <span className="text-xs">Connected</span>
                </div>
              ) : connectionStatus === 'connecting' ? (
                <div className="flex items-center gap-1 text-yellow-600 dark:text-yellow-400">
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-yellow-600 border-t-transparent"></div>
                  <span className="text-xs">Connecting...</span>
                </div>
              ) : connectionStatus === 'error' ? (
                <div className="flex items-center gap-1 text-red-600 dark:text-red-400">
                  <WifiOff size={16} />
                  <span className="text-xs">Error</span>
                </div>
              ) : (
                <div className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
                  <WifiOff size={16} />
                  <span className="text-xs">Offline</span>
                </div>
              )}
            </div>
            {/* Settings Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setPreferencesOpen(!preferencesOpen)}
              className="p-2 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
              title="Settings"
            >
              <Settings size={16} />
            </motion.button>
          </div>
        </div>

        {/* Preferences Modal: Personality selection */}
        {preferencesOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg w-96 p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Choose Personality</h3>
                <button
                  onClick={() => setPreferencesOpen(false)}
                  className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                >Close</button>
              </div>
              <div className="space-y-2">
                {availablePersonalities.length === 0 ? (
                  <div className="text-xs text-gray-500 dark:text-gray-400">Loading...</div>
                ) : (
                  availablePersonalities.map((p) => (
                    <button
                      key={p.type}
                      onClick={() => setPersonality(p.type)}
                      className={`w-full text-left px-3 py-2 rounded border text-xs ${currentPersonality === p.type ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300' : 'border-gray-300 dark:border-gray-600 text-gray-800 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                      title={p.description}
                    >
                      <div className="font-medium">{p.name || p.type}</div>
                      <div className="text-[11px] text-gray-500 dark:text-gray-400">{p.description || `Switch to ${p.type}`}</div>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
        
        {/* Chat window */}
        <div ref={chatWindowRef} className="flex-1 overflow-y-auto p-6">
          {messages.length === 0 ? (
            <div className="text-center text-xs text-gray-500 dark:text-gray-400">Start a conversation with Mitra ✨</div>
          ) : (
            <AnimatePresence>
              {messages.map((msg, idx) => (
                <motion.div key={idx} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} className={`mb-3 flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[70%] px-3 py-2 rounded-lg text-xs ${msg.sender === 'user' ? 'bg-blue-100 text-blue-900' : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'}`}>
                    {msg.text}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              className="flex-1 text-xs px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200"
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSend}
              className="px-3 py-2 rounded bg-blue-600 text-white text-xs"
            >
              <Send size={14} />
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Chat;

// Preferences Modal UI
// Rendered above return for clarity; using conditional within JSX
