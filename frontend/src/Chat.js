import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Settings, Smile, Heart, Frown, Meh, Angry, Trash2, PlusCircle } from 'lucide-react';
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
  // Add display name state for personalization
  const [displayName, setDisplayName] = useState(() => localStorage.getItem('displayName') || '');
  const chatWindowRef = useRef(null);

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
    // Attempt server-side deletion if available
    try {
      const resp = await api.deleteSession(sid);
      if (resp?.verified) {
        toast.success('Session deleted on server');
      }
    } catch (err) {
      // Continue with local deletion
      console.warn('Server deletion failed or unauthorized:', err.message);
    }

    const next = sessions.filter(s => s.id !== sid);
    saveSessions(next);
    localStorage.removeItem(`chat_messages_${sid}`);
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
            timestamp: new Date().toISOString(),
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

    // Removed: name prompt in chat. Personalization occurs on Dashboard.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
    setInput('');
    setIsTyping(true);
    setError(null);

    try {
      const response = await api.sendMessage(input.trim(), sessionId, currentPersonality);
      
      const aiMessage = {
        sender: 'ai',
        text: response.response || response.message || 'I apologize, but I couldn\'t process your message.',
        timestamp: new Date().toISOString(),
        emotion: response.detected_emotion || 'neutral'
      };

      setMessages(prev => [...prev, aiMessage]);
      
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
    } finally {
      setIsTyping(false);
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
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={(e) => { e.stopPropagation(); deleteSession(s.id); }}
                  className="p-1 rounded bg-red-100 dark:bg-red-900 text-red-600 dark:text-red-300 opacity-0 group-hover:opacity-100"
                  title="Delete"
                >
                  <Trash2 size={14} />
                </motion.button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
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
