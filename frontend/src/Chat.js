import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Settings, Trash2, PlusCircle, Wifi, WifiOff, Sparkles, Lock, Zap, Brain, X, Moon, Target, Eye, Heart, Volume2, VolumeX } from 'lucide-react';
import { toast } from 'react-toastify';
import * as api from './services/api';
import VoiceInput from './components/VoiceInput';

// ─── Thinking messages (per-personality) ────────────────────────────────
const THINKING_MESSAGES = {
  mitra: ["Hmm… let me sit with that…", "I hear you…", "Taking that in…"],
  default: ["Hmm…", "Give me a sec…", "Let me think…"],
  mentor: ["Let me reflect on that…", "Hmm…", "One sec…"],
  motivator: ["Okay…", "Yeah…", "Alright…"],
  coach: ["Right…", "Got it…", "Okay…"],
};

const QUICK_PROMPTS = [
  { text: "I'm feeling overwhelmed", emoji: "😮‍💨" },
  { text: "I need to talk", emoji: "💬" },
  { text: "Help me focus", emoji: "🎯" },
  { text: "I feel lost today", emoji: "🌫️" },
  { text: "Give me some motivation", emoji: "💪" },
];

// ─── TTS: Emotion-tuned voice via Web SpeechSynthesis (fully local, private) ──
const EMOTION_VOICE = {
  sad:       { rate: 0.88, pitch: 0.92, volume: 0.85 },
  stressed:  { rate: 0.92, pitch: 1.02, volume: 0.88 },
  anxious:   { rate: 0.90, pitch: 1.00, volume: 0.85 },
  angry:     { rate: 0.95, pitch: 0.96, volume: 0.90 },
  happy:     { rate: 1.05, pitch: 1.08, volume: 0.95 },
  motivated: { rate: 1.08, pitch: 1.10, volume: 0.95 },
  neutral:   { rate: 0.95, pitch: 1.00, volume: 0.88 },
};

function speakText(text, emotion = 'neutral', onStart, onEnd) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text.replace(/[*_~`#]/g, ''));
  const params = EMOTION_VOICE[emotion] || EMOTION_VOICE.neutral;
  utterance.rate = params.rate;
  utterance.pitch = params.pitch;
  utterance.volume = params.volume;

  // Pick a warm female voice if available
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v =>
    /female|zira|samantha|victoria|fiona|moira/i.test(v.name)
  ) || voices.find(v => v.lang === 'en-US') || voices[0];
  if (preferred) utterance.voice = preferred;

  utterance.onstart = onStart;
  utterance.onend = onEnd;
  utterance.onerror = onEnd;
  window.speechSynthesis.speak(utterance);
}

// Emotion -> subtle glow color (for breathing aura)
const EMOTION_GLOW = {
  sad: 'rgba(96, 165, 250, 0.12)',
  stressed: 'rgba(251, 146, 60, 0.10)',
  anxious: 'rgba(167, 139, 250, 0.10)',
  angry: 'rgba(248, 113, 113, 0.08)',
  happy: 'rgba(52, 211, 153, 0.10)',
  motivated: 'rgba(250, 204, 21, 0.10)',
  neutral: 'rgba(148, 163, 184, 0.05)',
};

function Chat({ onEmotionChange }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamPhase, setStreamPhase] = useState('');
  const [thinkingMessage, setThinkingMessage] = useState('');
  const [silenceMessage, setSilenceMessage] = useState(null);
  const [emotionPattern, setEmotionPattern] = useState(null);
  const [initiativeMessage, setInitiativeMessage] = useState(null);
  const [deepPresenceMode, setDeepPresenceMode] = useState(false);
  const [hasMeaningMoment, setHasMeaningMoment] = useState(false);
  const [careMode, setCareMode] = useState(false);
  const [automationOffer, setAutomationOffer] = useState(null);
  const [currentPersonality, setCurrentPersonality] = useState(() => localStorage.getItem('defaultPersonality') || 'mitra');
  const [availablePersonalities, setAvailablePersonalities] = useState([]);
  const [preferencesOpen, setPreferencesOpen] = useState(false);
  const [currentEmotion, setCurrentEmotion] = useState({ emotion: 'neutral', intensity: 'medium' });
  const [ttsEnabled, setTtsEnabled] = useState(() => localStorage.getItem('ttsEnabled') !== 'false');
  const [isSpeaking, setIsSpeaking] = useState(false);

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
  const [showSessions, setShowSessions] = useState(false);

  // WebSocket
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [remoteTyping, setRemoteTyping] = useState(false);
  // eslint-disable-next-line no-unused-vars
  const [messageQueue, setMessageQueue] = useState([]);

  const [userName, setUserName] = useState(() => {
    try { return localStorage.getItem('username') || ''; } catch { return ''; }
  });

  const chatWindowRef = useRef(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const inputRef = useRef(null);
  const initiativeTimerRef = useRef(null);

  const saveSessions = (next) => { setSessions(next); localStorage.setItem('chat_sessions', JSON.stringify(next)); };
  const saveMessagesForSession = (sid, msgs) => { localStorage.setItem(`chat_messages_${sid}`, JSON.stringify(msgs)); };
  const loadMessagesForSession = (sid) => { const raw = localStorage.getItem(`chat_messages_${sid}`); return raw ? JSON.parse(raw) : []; };

  const setPersonality = (type) => {
    setCurrentPersonality(type);
    localStorage.setItem('defaultPersonality', type);
    toast.success(`Switched to ${type}`);
    setPreferencesOpen(false);
  };

  // ─── WebSocket ────────────────────────────────────────────────────
  const connectWebSocket = useCallback(() => {
    if (!api.isAuthenticated || !api.isAuthenticated()) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    setConnectionStatus('connecting');
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/chat/${sessionId}`;
      const token = localStorage.getItem('access_token');
      const ws = new WebSocket(`${wsUrl}?token=${encodeURIComponent(token)}`);
      ws.onopen = () => { setConnectionStatus('connected'); wsRef.current = ws; reconnectAttemptsRef.current = 0; };
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'message') setMessages(prev => [...prev, { sender: 'ai', text: data.message, timestamp: data.timestamp || new Date().toISOString(), emotion: data.emotion || 'neutral' }]);
          else if (data.type === 'typing_indicator') setRemoteTyping(data.typing);
        } catch (e) { console.error('WS error:', e); }
      };
      ws.onclose = (event) => {
        setConnectionStatus('disconnected'); wsRef.current = null; setRemoteTyping(false);
        if (event.code !== 1000 && reconnectAttemptsRef.current < 5) {
          reconnectTimeoutRef.current = setTimeout(() => { reconnectAttemptsRef.current++; connectWebSocket(); }, Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000));
        }
      };
      ws.onerror = () => setConnectionStatus('error');
    } catch { setConnectionStatus('error'); }
  }, [sessionId]);

  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) { clearTimeout(reconnectTimeoutRef.current); reconnectTimeoutRef.current = null; }
    if (wsRef.current) { wsRef.current.close(1000); wsRef.current = null; }
    setConnectionStatus('disconnected'); setRemoteTyping(false);
  }, []);

  const sendWebSocketMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) { wsRef.current.send(JSON.stringify(message)); return true; }
    setMessageQueue(prev => [...prev, message]); return false;
  }, []);

  // ─── Session management ───────────────────────────────────────────
  const createNewSession = () => {
    const newId = (window.crypto && window.crypto.randomUUID) ? window.crypto.randomUUID() : Math.random().toString(36).slice(2);
    saveSessions([{ id: newId, title: 'New Chat', createdAt: new Date().toISOString() }, ...sessions]);
    setSessionId(newId); localStorage.setItem('sessionId', newId);
    setMessages([]); saveMessagesForSession(newId, []);
  };

  const deleteSession = async (sid) => {
    const next = sessions.filter(s => s.id !== sid);
    saveSessions(next); localStorage.removeItem(`chat_messages_${sid}`); setConfirmDeleteSessionId(null);
    if (sid === sessionId) { next.length ? openSession(next[0].id) : createNewSession(); }
    if (api.isAuthenticated && api.isAuthenticated()) { try { await api.deleteSession(sid); } catch {} }
  };

  const openSession = (sid) => { setSessionId(sid); localStorage.setItem('sessionId', sid); setMessages(loadMessagesForSession(sid)); setShowSessions(false); };

  // ─── Slash commands (invisible — triggered via UI buttons) ────────
  const handleSlashCommand = async (cmd) => {
    try {
      const result = await api.sendSlashCommand(cmd, sessionId);
      if (result.action === 'clear_messages') { setMessages([]); saveMessagesForSession(sessionId, []); toast.success('Chat cleared'); return; }
      if (result.action === 'set_personality' && result.personality) { setPersonality(result.personality); }
      if (result.response) {
        setMessages(prev => [...prev, { sender: 'ai', text: result.response, timestamp: new Date().toISOString(), isSystemMessage: true }]);
      }
    } catch { toast.error('Command failed'); }
  };

  // ─── AI Initiative (proactive check-ins) ──────────────────────────
  const checkForInitiative = useCallback(async () => {
    try {
      const result = await api.checkInitiative();
      if (result?.initiative?.message) {
        setInitiativeMessage(result.initiative);
      }
    } catch { /* silent */ }
  }, []);

  // ─── Main send handler ────────────────────────────────────────────
  const handleSend = async (text) => {
    const messageText = (text || input).trim();
    if (!messageText) return;

    // Background: check if this message contains a growth milestone
    if (api.isAuthenticated && api.isAuthenticated()) {
      api.recordMilestone(messageText).catch(() => {});
    }

    // Dismiss any initiative message
    setInitiativeMessage(null);

    const userMessage = { sender: 'user', text: messageText, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);
    setStreamPhase('thinking');
    setSilenceMessage(null);
    setEmotionPattern(null);
    setCareMode(false);
    setAutomationOffer(null);

    const personalityMsgs = THINKING_MESSAGES[currentPersonality] || THINKING_MESSAGES.default;
    setThinkingMessage(personalityMsgs[Math.floor(Math.random() * personalityMsgs.length)]);
    sendWebSocketMessage({ type: 'typing_indicator', typing: true });

    try {
      await api.streamMessage(
        messageText, sessionId, currentPersonality,
        (eventType, data) => {
          switch (eventType) {
            case 'thinking':
              setStreamPhase('thinking');
              setThinkingMessage(data.message || 'Thinking…');
              break;

            case 'silence':
              setStreamPhase('silence');
              setSilenceMessage(data.message);
              break;

            case 'emotion':
              if (data.primary_emotion) {
                setCurrentEmotion({ emotion: data.primary_emotion, intensity: data.primary_intensity || 'medium' });
                if (onEmotionChange) onEmotionChange(data.primary_emotion);
                if (data.care_mode) setCareMode(true);
              }
              break;

            case 'automation':
              if (data.offer) setAutomationOffer(data.offer);
              break;

            case 'soul':
              // Soul layer metadata — meaning moment glow, interjection indicator
              if (data.has_meaning_moment) setHasMeaningMoment(true);
              break;

            case 'token':
              setStreamPhase('streaming');
              setSilenceMessage(null);
              setMessages(prev => {
                const updated = [...prev];
                const lastIdx = updated.length - 1;
                if (lastIdx >= 0 && updated[lastIdx].sender === 'ai' && updated[lastIdx]._streaming) {
                  updated[lastIdx] = { ...updated[lastIdx], text: updated[lastIdx].text + data.text };
                } else {
                  updated.push({ sender: 'ai', text: data.text, timestamp: new Date().toISOString(), _streaming: true });
                }
                return updated;
              });
              break;

            case 'pattern':
              if (data.insight) setEmotionPattern(data);
              break;

            case 'done': {
              setStreamPhase('done');
              const finalText = data.full_response;
              setMessages(prev => {
                const updated = [...prev];
                const lastIdx = updated.length - 1;
                if (lastIdx >= 0 && updated[lastIdx]._streaming) {
                  updated[lastIdx] = { ...updated[lastIdx], text: finalText || updated[lastIdx].text, _streaming: false };
                }
                return updated;
              });
              // Speak the response if TTS is on
              if (ttsEnabled && finalText) {
                speakText(
                  finalText,
                  currentEmotion.emotion,
                  () => setIsSpeaking(true),
                  () => setIsSpeaking(false),
                );
              }
              break;
            }

            default: break;
          }
        }
      );
    } catch (streamErr) {
      // Fallback to non-streaming
      try {
        const response = await api.sendMessage(messageText, sessionId, currentPersonality);
        await new Promise(r => setTimeout(r, 400));
        setMessages(prev => [...prev, { sender: 'ai', text: response.response || "I'm here with you.", timestamp: new Date().toISOString() }]);
        if (response.emotion?.primary_emotion) {
          setCurrentEmotion({ emotion: response.emotion.primary_emotion, intensity: response.emotion.primary_intensity || 'medium' });
          if (onEmotionChange) onEmotionChange(response.emotion.primary_emotion);
        }
      } catch {
        setMessages(prev => [...prev, { sender: 'ai', text: "I'm having trouble, but I'm still here with you.", timestamp: new Date().toISOString() }]);
      }
    } finally {
      setIsStreaming(false); setStreamPhase(''); setSilenceMessage(null);
      sendWebSocketMessage({ type: 'typing_indicator', typing: false });
      if (hasMeaningMoment) setTimeout(() => setHasMeaningMoment(false), 8000);
      inputRef.current?.focus();
    }
  };

  // ─── Effects ──────────────────────────────────────────────────────
  useEffect(() => {
    api.getAvailablePersonalities().then(setAvailablePersonalities).catch(() => {});
    const existing = loadMessagesForSession(sessionId);
    if (existing.length) setMessages(existing);
    else {
      api.getChatHistory(50, sessionId).then(resp => {
        const mapped = (resp?.messages || []).map(m => ({ sender: m.role === 'assistant' ? 'ai' : 'user', text: m.content, timestamp: m.timestamp || new Date().toISOString() }));
        if (mapped.length) { setMessages(mapped); saveMessagesForSession(sessionId, mapped); }
      }).catch(() => {});
    }
    connectWebSocket();

    // Start initiative polling (every 5 minutes)
    initiativeTimerRef.current = setInterval(checkForInitiative, 5 * 60 * 1000);
    // Check once after 30s
    setTimeout(checkForInitiative, 30000);

    // First-time welcome: if the user has never chatted, Mitra greets them
    const hasGreeted = localStorage.getItem('mitra_greeted');
    if (!hasGreeted) {
      const name = localStorage.getItem('username') || '';
      const greeting = name
        ? `Hi ${name} — I'm Mitra. I'm really glad you're here. What's on your mind today?`
        : `Hey — I'm Mitra. I'm here whenever you're ready to talk. What's going on?`;
      setTimeout(() => {
        setInitiativeMessage({ message: greeting, tier: 'welcome' });
        localStorage.setItem('mitra_greeted', 'true');
      }, 1800);
    }

    return () => { disconnectWebSocket(); if (initiativeTimerRef.current) clearInterval(initiativeTimerRef.current); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (api.isAuthenticated && api.isAuthenticated()) { disconnectWebSocket(); setTimeout(connectWebSocket, 100); }
  }, [sessionId, connectWebSocket, disconnectWebSocket]);

  useEffect(() => { return () => disconnectWebSocket(); }, [disconnectWebSocket]);

  // Focus on mount
  useEffect(() => { setTimeout(() => inputRef.current?.focus(), 100); }, []);

  // Refocus when streaming ends
  useEffect(() => { if (!isStreaming) inputRef.current?.focus(); }, [isStreaming]);

  useEffect(() => {
    if (chatWindowRef.current) chatWindowRef.current.scrollTo({ top: chatWindowRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, isStreaming, silenceMessage]);

  useEffect(() => {
    saveMessagesForSession(sessionId, messages);
    const firstUser = messages.find(m => m.sender === 'user');
    if (firstUser) saveSessions(sessions.map(s => s.id === sessionId ? { ...s, title: firstUser.text.slice(0, 30) } : s));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, sessionId]);

  const handleKeyDown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } };
  const emptyState = messages.length === 0 && !isStreaming;
  const emotionGlow = EMOTION_GLOW[currentEmotion.emotion] || EMOTION_GLOW.neutral;

  const careBg = careMode
    ? 'radial-gradient(ellipse at 50% 40%, rgba(251,191,36,0.06), rgba(249,115,22,0.04), transparent 70%)'
    : `radial-gradient(ellipse at 50% 30%, ${emotionGlow}, transparent 70%)`;

  return (
    <div className={`flex h-full transition-all duration-1000 ${careMode ? 'care-active' : ''}`}
      style={{ background: careBg }}>
      {/* Sessions Panel */}
      <AnimatePresence>
        {showSessions && (
          <motion.div initial={{ width: 0, opacity: 0 }} animate={{ width: 240, opacity: 1 }} exit={{ width: 0, opacity: 0 }} transition={{ duration: 0.25 }}
            className="h-full glass-strong flex flex-col overflow-hidden border-r border-white/5">
            <div className="flex items-center justify-between p-3 border-b border-white/5">
              <span className="text-xs font-semibold" style={{ color: 'var(--mm-text-secondary)' }}>Conversations</span>
              <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }} onClick={createNewSession} className="p-1.5 rounded-lg hover:bg-white/5" style={{ color: 'var(--mm-text-muted)' }}>
                <PlusCircle size={14} />
              </motion.button>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {sessions.length === 0 ? (
                <div className="text-[11px] p-3 text-center" style={{ color: 'var(--mm-text-muted)' }}>No conversations yet</div>
              ) : sessions.map(s => (
                <div key={s.id} className={`group flex items-center justify-between px-2.5 py-2 rounded-lg cursor-pointer transition-all ${sessionId === s.id ? 'bg-blue-500/10 border border-blue-500/20' : 'hover:bg-white/5 border border-transparent'}`}
                  onClick={() => openSession(s.id)}>
                  <div className="text-[11px] truncate pr-2" style={{ color: sessionId === s.id ? 'var(--mm-accent)' : 'var(--mm-text-secondary)' }}>{s.title}</div>
                  {confirmDeleteSessionId === s.id ? (
                    <div className="flex items-center gap-1" onClick={e => e.stopPropagation()}>
                      <button className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/80 text-white" onClick={() => deleteSession(s.id)}>Yes</button>
                      <button className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-gray-300" onClick={() => setConfirmDeleteSessionId(null)}>No</button>
                    </div>
                  ) : (
                    <motion.button whileHover={{ scale: 1.1 }} onClick={e => { e.stopPropagation(); setConfirmDeleteSessionId(s.id); }}
                      className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-500/20 transition-all" style={{ color: 'var(--mm-text-muted)' }}>
                      <Trash2 size={11} />
                    </motion.button>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Chat */}
      <div className="flex-1 flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-white/5" style={{ background: 'rgba(10, 14, 26, 0.5)', backdropFilter: 'blur(20px)' }}>
          <div className="flex items-center gap-3">
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={() => setShowSessions(!showSessions)}
              className="p-1.5 rounded-lg hover:bg-white/5" style={{ color: 'var(--mm-text-muted)' }}>
              <PlusCircle size={16} />
            </motion.button>

            {/* Mitra avatar orb */}
            <div className={`mitra-header-avatar ${isSpeaking ? 'speaking-pulse' : ''}`}>
              <Sparkles size={14} style={{ color: isSpeaking ? 'rgba(134,239,172,0.9)' : 'rgba(139,92,246,0.8)', filter: isSpeaking ? 'drop-shadow(0 0 4px rgba(134,239,172,0.6))' : 'drop-shadow(0 0 4px rgba(139,92,246,0.5))' }} />
              <span className="presence-dot" />
            </div>

            <div>
              <h1 className="text-sm font-medium" style={{ color: 'var(--mm-text-primary)', letterSpacing: '-0.01em' }}>
                Mitra
                <span className="ml-1.5 text-[10px] font-normal opacity-50">
                  {currentPersonality !== 'mitra' ? `· ${currentPersonality}` : ''}
                </span>
              </h1>
              <AnimatePresence mode="wait">
                {isSpeaking ? (
                  <motion.p key="speaking" initial={{ opacity: 0, y: -3 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                    className="text-[10px] italic flex items-center gap-1"
                    style={{ color: '#86efac' }}>
                    <Volume2 size={9} />
                    Speaking…
                  </motion.p>
                ) : isStreaming || remoteTyping ? (
                  <motion.p key="streaming" initial={{ opacity: 0, y: -3 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                    className="text-[10px] italic flex items-center gap-1"
                    style={{ color: streamPhase === 'silence' ? '#a78bfa' : 'var(--mm-accent)' }}>
                    {streamPhase === 'silence' && <Moon size={9} />}
                    {streamPhase === 'streaming' && <Zap size={9} />}
                    {streamPhase === 'silence' ? silenceMessage || 'Listening…' :
                     streamPhase === 'streaming' ? 'Thinking…' :
                     thinkingMessage || 'Thinking…'}
                  </motion.p>
                ) : (
                  <motion.p key="status" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    className="text-[10px]" style={{ color: 'var(--mm-text-muted)' }}>
                    here with you
                  </motion.p>
                )}
              </AnimatePresence>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {connectionStatus === 'connected' ? <Wifi size={12} className="text-emerald-400" /> :
             connectionStatus === 'connecting' ? <div className="w-3 h-3 rounded-full border border-yellow-400 border-t-transparent animate-spin" /> :
             <WifiOff size={12} style={{ color: 'var(--mm-text-muted)' }} />}

            <div className="flex items-center gap-1 px-2 py-1 rounded-md" style={{ background: 'rgba(34, 197, 94, 0.08)', border: '1px solid rgba(34, 197, 94, 0.15)' }}>
              <Lock size={10} className="text-emerald-400" /><span className="text-[9px] font-medium text-emerald-400">Encrypted</span>
            </div>

            {/* Action buttons — replacing slash commands */}
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={() => setDeepPresenceMode(!deepPresenceMode)}
              className={`p-1.5 rounded-lg transition-colors ${deepPresenceMode ? 'bg-blue-500/15' : 'hover:bg-blue-500/10'}`}
              style={{ color: deepPresenceMode ? 'var(--mm-accent)' : 'var(--mm-text-muted)' }} title="Deep Presence">
              <Eye size={14} />
            </motion.button>
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={() => handleSlashCommand('/calm')}
              className="p-1.5 rounded-lg hover:bg-purple-500/10 transition-colors" style={{ color: 'var(--mm-text-muted)' }} title="Calm mode">
              <Moon size={14} />
            </motion.button>
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={() => handleSlashCommand('/focus')}
              className="p-1.5 rounded-lg hover:bg-blue-500/10 transition-colors" style={{ color: 'var(--mm-text-muted)' }} title="Focus mode">
              <Target size={14} />
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={() => {
                const next = !ttsEnabled;
                setTtsEnabled(next);
                localStorage.setItem('ttsEnabled', String(next));
                if (!next && window.speechSynthesis) { window.speechSynthesis.cancel(); setIsSpeaking(false); }
              }}
              className={`p-1.5 rounded-lg transition-colors ${ttsEnabled ? 'bg-emerald-500/10' : 'hover:bg-white/5'}`}
              style={{ color: ttsEnabled ? '#86efac' : 'var(--mm-text-muted)' }}
              title={ttsEnabled ? 'Voice on — tap to mute' : 'Voice off — tap to enable'}
            >
              {ttsEnabled ? <Volume2 size={14} /> : <VolumeX size={14} />}
            </motion.button>

            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={() => setPreferencesOpen(!preferencesOpen)}
              className="p-1.5 rounded-lg hover:bg-white/5" style={{ color: 'var(--mm-text-muted)' }}>
              <Settings size={14} />
            </motion.button>
          </div>
        </div>

        {/* Personality Modal */}
        <AnimatePresence>
          {preferencesOpen && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center"
              style={{ background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }} onClick={() => setPreferencesOpen(false)}>
              <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
                className="glass-elevated rounded-2xl w-96 p-5" onClick={e => e.stopPropagation()}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold" style={{ color: 'var(--mm-text-primary)' }}>Choose Personality</h3>
                  <button onClick={() => setPreferencesOpen(false)} className="text-xs" style={{ color: 'var(--mm-text-muted)' }}>Close</button>
                </div>
                <div className="space-y-2">
                  {availablePersonalities.length === 0 ? <div className="text-xs" style={{ color: 'var(--mm-text-muted)' }}>Loading...</div> :
                    availablePersonalities.map(p => (
                      <motion.button key={p.type} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }} onClick={() => setPersonality(p.type)}
                        className={`w-full text-left px-4 py-3 rounded-xl border transition-all ${currentPersonality === p.type ? 'border-blue-500/40 bg-blue-500/10' : 'border-white/5 hover:border-white/10'}`}>
                        <div className="text-xs font-medium" style={{ color: currentPersonality === p.type ? 'var(--mm-accent)' : 'var(--mm-text-primary)' }}>{p.name || p.type}</div>
                        <div className="text-[10px] mt-0.5" style={{ color: 'var(--mm-text-muted)' }}>{p.description || `Switch to ${p.type}`}</div>
                      </motion.button>
                    ))
                  }
                </div>

                {/* Memory + Clear actions inside settings */}
                <div className="mt-4 pt-3 border-t border-white/5 space-y-2">
                  <motion.button whileHover={{ scale: 1.01 }} onClick={() => { handleSlashCommand('/memory'); setPreferencesOpen(false); }}
                    className="w-full text-left px-4 py-2.5 rounded-xl border border-white/5 hover:border-purple-500/20 hover:bg-purple-500/5 transition-all flex items-center gap-2">
                    <Brain size={14} className="text-purple-400" />
                    <div>
                      <div className="text-xs font-medium" style={{ color: 'var(--mm-text-primary)' }}>What I remember</div>
                      <div className="text-[10px]" style={{ color: 'var(--mm-text-muted)' }}>View stored memories</div>
                    </div>
                  </motion.button>
                  <motion.button whileHover={{ scale: 1.01 }} onClick={() => { handleSlashCommand('/clear'); setPreferencesOpen(false); }}
                    className="w-full text-left px-4 py-2.5 rounded-xl border border-white/5 hover:border-red-500/20 hover:bg-red-500/5 transition-all flex items-center gap-2">
                    <Trash2 size={14} className="text-red-400" />
                    <div>
                      <div className="text-xs font-medium" style={{ color: 'var(--mm-text-primary)' }}>Clear chat</div>
                      <div className="text-[10px]" style={{ color: 'var(--mm-text-muted)' }}>Start fresh</div>
                    </div>
                  </motion.button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Chat Area */}
        <div ref={chatWindowRef} className="flex-1 overflow-y-auto px-6 py-4">
          {/* Initiative Message (AI reaches out first) */}
          <AnimatePresence>
            {initiativeMessage && emptyState && (
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.6 }}
                className="mb-6 flex justify-start">
                <div className="max-w-[70%] px-4 py-3 bubble-mitra relative">
                  <button onClick={() => setInitiativeMessage(null)} className="absolute top-2 right-2 p-0.5 rounded-full hover:bg-white/10" style={{ color: 'var(--mm-text-muted)' }}>
                    <X size={10} />
                  </button>
                  <p className="text-[13px] leading-relaxed pr-4" style={{ color: 'var(--mm-text-primary)' }}>{initiativeMessage.message}</p>
                  <p className="text-[9px] mt-1.5 opacity-40">
                    Mitra checked in • {initiativeMessage.tier === 'reflection' ? 'thinking about you' : initiativeMessage.tier === 'next_morning' ? 'good morning' : 'just now'}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Deep Presence Mode overlay */}
          <AnimatePresence>
            {deepPresenceMode && emptyState && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 1.5 }}
                className="h-full flex flex-col items-center justify-center text-center deep-presence-container">
                <motion.div animate={{ scale: [1, 1.06, 1], opacity: [0.4, 0.8, 0.4] }}
                  transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
                  className="w-24 h-24 mx-auto rounded-full flex items-center justify-center mb-8"
                  style={{ background: 'radial-gradient(circle, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.08), transparent)', boxShadow: '0 0 60px rgba(59, 130, 246, 0.12)' }}>
                  <Heart size={28} className="text-blue-400" style={{ opacity: 0.5, filter: 'drop-shadow(0 0 8px rgba(59,130,246,0.3))' }} />
                </motion.div>
                <motion.p initial={{ opacity: 0 }} animate={{ opacity: [0.3, 0.6, 0.3] }} transition={{ duration: 4, repeat: Infinity }}
                  className="text-sm font-light" style={{ color: 'var(--mm-text-muted)', letterSpacing: '0.05em' }}>
                  I'm here
                </motion.p>
                <motion.button initial={{ opacity: 0 }} animate={{ opacity: 0.3 }} whileHover={{ opacity: 0.7 }}
                  onClick={() => setDeepPresenceMode(false)}
                  className="mt-12 text-[10px] px-3 py-1.5 rounded-full border border-white/5 hover:border-white/10 transition-all"
                  style={{ color: 'var(--mm-text-muted)' }}>
                  Start talking
                </motion.button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Empty State — cinematic presence */}
          {emptyState && !initiativeMessage && !deepPresenceMode && (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <motion.div
                initial={{ opacity: 0, scale: 0.92 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 1, ease: [0.4, 0, 0.2, 1] }}
                className="space-y-8 max-w-sm w-full px-4"
              >
                {/* Layered breathing orb */}
                <div className="welcome-orb-outer mx-auto">
                  <div className="welcome-orb-inner">
                    <Sparkles size={28} style={{ color: 'rgba(139,92,246,0.75)', filter: 'drop-shadow(0 0 8px rgba(139,92,246,0.5))' }} />
                  </div>
                </div>

                {/* Personalized greeting */}
                <motion.div
                  initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4, duration: 0.7 }}
                >
                  <p className="welcome-greeting mb-3">
                    {userName
                      ? `Hey ${userName}…`
                      : "Hey…"}
                  </p>
                  <p className="text-sm font-light mb-1" style={{ color: 'var(--mm-text-secondary)' }}>
                    {userName ? "I'm here whenever you need me." : "I'm right here, whenever you're ready."}
                  </p>
                  <motion.p
                    animate={{ opacity: [0.4, 0.7, 0.4] }}
                    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                    className="text-xs mt-2"
                    style={{ color: 'var(--mm-text-muted)', letterSpacing: '0.02em' }}
                  >
                    {currentEmotion.emotion !== 'neutral'
                      ? `You seem ${currentEmotion.emotion}. I'm listening.`
                      : "Everything you share stays between us."}
                  </motion.p>
                </motion.div>

                {/* Quick prompts */}
                <motion.div
                  className="flex flex-wrap justify-center gap-2"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.75, duration: 0.6 }}
                >
                  {QUICK_PROMPTS.map((prompt, i) => (
                    <motion.button
                      key={i}
                      className="prompt-chip"
                      whileHover={{ scale: 1.04, y: -1 }}
                      whileTap={{ scale: 0.97 }}
                      onClick={() => handleSend(prompt.text)}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.85 + i * 0.07 }}
                    >
                      <span>{prompt.emoji}</span><span>{prompt.text}</span>
                    </motion.button>
                  ))}
                </motion.div>
              </motion.div>
            </div>
          )}

          {/* Messages */}
          <AnimatePresence>
            {messages.map((msg, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
                className={`mb-5 flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.sender !== 'user' && !msg.isSystemMessage && (
                  <div className="mitra-presence-dot mr-2.5 mt-1">
                    <Sparkles size={11} style={{ color: 'rgba(139,92,246,0.7)' }} />
                  </div>
                )}
                <div className={`max-w-[62%] px-4 py-3.5 relative ${
                  msg.isSystemMessage ? 'bubble-system' : msg.sender === 'user' ? 'bubble-user' : 'bubble-mitra'
                } ${msg._streaming ? 'streaming-cursor' : ''} ${hasMeaningMoment && idx === messages.length - 1 && msg.sender === 'ai' ? 'meaning-glow' : ''}`}>
                  <p className="text-[13.5px] leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--mm-text-primary)', letterSpacing: '-0.005em' }}>{msg.text}</p>
                  <p className="text-[9px] mt-2 opacity-30">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Silence indicator (replaces typing dots for heavy emotions) */}
          <AnimatePresence>
            {isStreaming && streamPhase === 'silence' && silenceMessage && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="mb-4 flex justify-start items-start gap-2.5">
                <div className="mitra-presence-dot mt-1">
                  <Sparkles size={11} style={{ color: 'rgba(139,92,246,0.7)' }} />
                </div>
                <div className="bubble-mitra px-4 py-3">
                  <p className="text-[12px] italic" style={{ color: '#a78bfa' }}>{silenceMessage}</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Typing dots (only during thinking phase) */}
          <AnimatePresence>
            {isStreaming && streamPhase === 'thinking' && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} className="mb-4 flex justify-start items-start gap-2.5">
                <div className="mitra-presence-dot mt-1">
                  <Sparkles size={11} style={{ color: 'rgba(139,92,246,0.7)' }} />
                </div>
                <div className="bubble-mitra">
                  <div className="typing-indicator"><div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" /></div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Emotion Pattern Insight (inline, natural) */}
        <AnimatePresence>
          {emotionPattern && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="mx-5 mb-2">
              <div className="px-4 py-2.5 rounded-xl flex items-start gap-2"
                style={{ background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.06), rgba(59, 130, 246, 0.04))', border: '1px solid rgba(139, 92, 246, 0.12)' }}>
                <Brain size={12} className="text-purple-400 mt-0.5 flex-shrink-0" />
                <p className="text-[11px] leading-relaxed" style={{ color: 'var(--mm-text-secondary)' }}>{emotionPattern.insight}</p>
                <button onClick={() => setEmotionPattern(null)} className="p-0.5 rounded-full hover:bg-white/10 flex-shrink-0" style={{ color: 'var(--mm-text-muted)' }}>
                  <X size={10} />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Automation Offer Card — gentle collaboration, not tool push */}
        <AnimatePresence>
          {automationOffer && !isStreaming && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.97 }}
              transition={{ duration: 0.4 }}
              className="mx-5 mb-2"
            >
              <div className="automation-card px-4 py-3 rounded-2xl flex items-start gap-3"
                style={{
                  background: 'linear-gradient(135deg, rgba(139,92,246,0.08), rgba(59,130,246,0.06))',
                  border: '1px solid rgba(139,92,246,0.18)',
                }}>
                <Sparkles size={14} className="text-purple-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-[12px] leading-relaxed" style={{ color: 'var(--mm-text-secondary)' }}>
                    {automationOffer.text}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <motion.button
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                      onClick={() => {
                        handleSend(automationOffer.button_label);
                        setAutomationOffer(null);
                      }}
                      className="text-[11px] px-3 py-1.5 rounded-lg font-medium"
                      style={{
                        background: 'linear-gradient(135deg, rgba(139,92,246,0.3), rgba(59,130,246,0.3))',
                        border: '1px solid rgba(139,92,246,0.3)',
                        color: '#c4b5fd',
                      }}
                    >
                      {automationOffer.button_label}
                    </motion.button>
                    <button
                      onClick={() => setAutomationOffer(null)}
                      className="text-[10px] px-2 py-1.5 rounded-lg"
                      style={{ color: 'var(--mm-text-muted)' }}
                    >
                      Maybe later
                    </button>
                  </div>
                </div>
                <button
                  onClick={() => setAutomationOffer(null)}
                  className="p-0.5 rounded-full hover:bg-white/10 flex-shrink-0"
                  style={{ color: 'var(--mm-text-muted)' }}
                >
                  <X size={10} />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Quick prompts (early in conversation) */}
        {messages.length > 0 && messages.length < 4 && !isStreaming && (
          <div className="px-5 pb-2">
            <div className="flex gap-2 overflow-x-auto" style={{ scrollbarWidth: 'none' }}>
              {QUICK_PROMPTS.map((prompt, i) => (
                <motion.button key={i} className="prompt-chip text-[11px] flex-shrink-0" whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} onClick={() => handleSend(prompt.text)}>
                  <span>{prompt.emoji}</span><span>{prompt.text}</span>
                </motion.button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="px-5 py-4 border-t border-white/5" style={{ background: 'rgba(10, 14, 26, 0.55)', backdropFilter: 'blur(24px)' }}>
          <div className="flex items-center gap-3">
            <VoiceInput
              onTranscript={text => {
                setInput(prev => (prev ? prev + ' ' + text : text));
                setTimeout(() => inputRef.current?.focus(), 50);
              }}
              disabled={isStreaming}
            />
            <input
              ref={inputRef}
              value={input}
              onChange={e => {
                setInput(e.target.value);
                // Stop TTS when user starts typing a new message
                if (isSpeaking && window.speechSynthesis) { window.speechSynthesis.cancel(); setIsSpeaking(false); }
              }}
              onKeyDown={handleKeyDown}
              placeholder={isStreaming ? "Mitra is with you…" : "Say anything…"}
              className="input-glass"
              style={{ flex: 1, width: 'auto' }}
              disabled={isStreaming}
              autoFocus
            />
            <motion.button
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.94 }}
              onClick={() => handleSend()}
              disabled={!input.trim() || isStreaming}
              className="send-btn"
              style={{ opacity: input.trim() && !isStreaming ? 1 : 0.35 }}
            >
              <Send size={15} color="white" />
            </motion.button>
          </div>
          <div className="relative mt-2.5">
            <div className={`heartbeat-line ${isStreaming ? 'streaming-active' : ''}`} />
          </div>
          {/* Privacy reminder */}
          <p className="text-center text-[9px] mt-1.5 opacity-20" style={{ color: 'var(--mm-text-muted)' }}>
            Voice processed locally · Nothing leaves your device
          </p>
        </div>
      </div>
    </div>
  );
}

export default Chat;
