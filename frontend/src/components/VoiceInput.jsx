import React, { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Loader } from 'lucide-react';

const BACKEND = (process.env.REACT_APP_API_BASE || 'http://localhost:8000/api/v1').replace(/\/api\/v1\/?$/, '');

const VoiceInput = ({ onTranscript, disabled }) => {
  const [state, setState] = useState('idle'); // idle | recording | processing
  const [errorMsg, setErrorMsg] = useState('');
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);

  const stopRecording = useCallback(async () => {
    if (!mediaRecorderRef.current) return;
    setState('processing');

    await new Promise(resolve => {
      mediaRecorderRef.current.onstop = resolve;
      mediaRecorderRef.current.stop();
    });

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }

    const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
    chunksRef.current = [];

    try {
      const form = new FormData();
      form.append('audio', blob, 'voice.webm');
      const res = await fetch(`${BACKEND}/api/v1/voice/transcribe`, {
        method: 'POST',
        body: form,
      });
      if (!res.ok) throw new Error('transcription failed');
      const { text } = await res.json();
      if (text && text.trim()) {
        onTranscript(text.trim());
        setErrorMsg('');
      } else {
        setErrorMsg("Couldn't catch that — try again?");
        setTimeout(() => setErrorMsg(''), 3000);
      }
    } catch {
      setErrorMsg("Couldn't reach transcription. Try typing?");
      setTimeout(() => setErrorMsg(''), 3000);
    } finally {
      setState('idle');
    }
  }, [onTranscript]);

  const startRecording = useCallback(async () => {
    setErrorMsg('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      chunksRef.current = [];
      mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.start(250);
      mediaRecorderRef.current = mr;
      setState('recording');
    } catch {
      setErrorMsg('Microphone access denied');
      setTimeout(() => setErrorMsg(''), 3000);
    }
  }, []);

  const handleClick = () => {
    if (disabled) return;
    if (state === 'recording') stopRecording();
    else if (state === 'idle') startRecording();
  };

  const isRecording = state === 'recording';
  const isProcessing = state === 'processing';

  return (
    <div className="relative flex-shrink-0">
      <motion.button
        type="button"
        onClick={handleClick}
        disabled={disabled || isProcessing}
        title={isRecording ? 'Tap to stop' : 'Speak to Mitra'}
        className="relative flex items-center justify-center rounded-full transition-all"
        style={{
          width: 42,
          height: 42,
          background: isRecording
            ? 'linear-gradient(135deg, rgba(239,68,68,0.35), rgba(220,38,38,0.25))'
            : 'rgba(255,255,255,0.06)',
          border: isRecording
            ? '1px solid rgba(239,68,68,0.5)'
            : '1px solid rgba(255,255,255,0.08)',
          boxShadow: isRecording ? '0 0 14px rgba(239,68,68,0.3)' : 'none',
          opacity: disabled ? 0.3 : 1,
        }}
        whileHover={!disabled && !isProcessing ? { scale: 1.08 } : {}}
        whileTap={!disabled && !isProcessing ? { scale: 0.93 } : {}}
      >
        {/* Pulse rings when recording */}
        <AnimatePresence>
          {isRecording && (
            <>
              <motion.span
                key="ring1"
                className="absolute inset-0 rounded-full"
                style={{ border: '1px solid rgba(239,68,68,0.4)' }}
                initial={{ scale: 1, opacity: 0.6 }}
                animate={{ scale: 1.7, opacity: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 1.4, repeat: Infinity, ease: 'easeOut' }}
              />
              <motion.span
                key="ring2"
                className="absolute inset-0 rounded-full"
                style={{ border: '1px solid rgba(239,68,68,0.3)' }}
                initial={{ scale: 1, opacity: 0.5 }}
                animate={{ scale: 2.2, opacity: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 1.4, repeat: Infinity, ease: 'easeOut', delay: 0.4 }}
              />
            </>
          )}
        </AnimatePresence>

        {isProcessing ? (
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
            <Loader size={16} style={{ color: 'var(--mm-accent)' }} />
          </motion.div>
        ) : isRecording ? (
          <MicOff size={16} style={{ color: '#f87171' }} />
        ) : (
          <Mic size={16} style={{ color: 'var(--mm-text-muted)' }} />
        )}
      </motion.button>

      {/* Error / feedback tooltip */}
      <AnimatePresence>
        {errorMsg && (
          <motion.div
            initial={{ opacity: 0, y: 6, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.95 }}
            className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 px-3 py-1.5 rounded-lg text-[10px] whitespace-nowrap z-50"
            style={{
              background: 'rgba(30,30,40,0.95)',
              border: '1px solid rgba(255,255,255,0.08)',
              color: 'var(--mm-text-secondary)',
            }}
          >
            {errorMsg}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default VoiceInput;
