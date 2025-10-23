import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Settings, Smile, Heart, Frown, Meh, Angry } from 'lucide-react';
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
        toast.error('Failed to load personalities');
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
          timestamp: new Date().toISOString(),
          emotion: m.emotion || 'neutral'
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

  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

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
      const response = await api.sendMessage(input.trim(), currentPersonality, sessionId, currentEmotion.emotion);
      
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

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const EmotionButton = ({ emotion, icon: Icon }) => (
    <motion.button
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
      onClick={() => setCurrentEmotion({ emotion, intensity: 'medium' })}
      className={`p-2 rounded-full transition-all duration-200 ${
        currentEmotion.emotion === emotion
          ? `bg-${getEmotionColor(emotion)}-100 text-${getEmotionColor(emotion)}-600 dark:bg-${getEmotionColor(emotion)}-900 dark:text-${getEmotionColor(emotion)}-300`
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
      }`}
      title={`I'm feeling ${emotion}`}
    >
      <Icon size={16} />
    </motion.button>
  );

  const MessageBubble = ({ message, index }) => {
    const isUser = message.sender === 'user';
    const emotion = message.emotion || 'neutral';
    const emotionColor = getEmotionColor(emotion);
    const emotionEmoji = getEmotionEmoji(emotion);

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: index * 0.1 }}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
          <div
            className={`px-4 py-3 rounded-2xl shadow-soft ${
              isUser
                ? 'bg-warm-brown text-white ml-4'
                : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 mr-4'
            }`}
          >
            <div className="flex items-start gap-2">
              {!isUser && (
                <span className="text-lg" title={`Detected emotion: ${emotion}`}>
                  {emotionEmoji}
                </span>
              )}
              <p className="text-sm leading-relaxed">{message.text}</p>
              {isUser && (
                <span className="text-lg opacity-70" title={`Your mood: ${emotion}`}>
                  {emotionEmoji}
                </span>
              )}
            </div>
          </div>
          <div className={`text-xs text-gray-500 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-cream dark:bg-dark-bg">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-soft px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-warm-brown to-autumn-orange rounded-full flex items-center justify-center">
              <span className="text-white font-semibold">M</span>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                Mitra AI
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Your emotional wellness companion
              </p>
            </div>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setPreferencesOpen(!preferencesOpen)}
            className="p-2 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            <Settings size={20} />
          </motion.button>
        </div>
      </div>

      {/* Chat Messages */}
      <div 
        ref={chatWindowRef}
        className="flex-1 overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-cream to-white dark:from-dark-bg dark:to-gray-900"
      >
        <AnimatePresence>
          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} index={index} />
          ))}
        </AnimatePresence>
        
        {isTyping && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start mb-4"
          >
            <div className="bg-white dark:bg-gray-800 rounded-2xl px-4 py-3 shadow-soft mr-4">
              <div className="flex items-center gap-2">
                <span className="text-lg">🤔</span>
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Input Area */}
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-6">
        {/* Emotion Selector */}
        <div className="flex items-center gap-2 mb-4">
          <span className="text-sm text-gray-600 dark:text-gray-400 mr-2">How are you feeling?</span>
          <EmotionButton emotion="happy" icon={Smile} />
          <EmotionButton emotion="love" icon={Heart} />
          <EmotionButton emotion="neutral" icon={Meh} />
          <EmotionButton emotion="sad" icon={Frown} />
          <EmotionButton emotion="angry" icon={Angry} />
        </div>

        {/* Message Input */}
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Talk to Mitra... Share what's on your mind 💭"
              className="w-full p-4 rounded-2xl border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-warm-brown dark:focus:ring-dark-accent transition-all duration-200"
              rows={1}
              style={{ minHeight: '52px', maxHeight: '120px' }}
            />
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="p-4 bg-warm-brown hover:bg-warm-brown/90 disabled:bg-gray-300 dark:disabled:bg-gray-600 text-white rounded-2xl transition-all duration-200 shadow-soft disabled:cursor-not-allowed"
          >
            <Send size={20} />
          </motion.button>
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-3 p-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-xl text-sm"
          >
            {error}
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default Chat;
