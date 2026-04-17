import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, TrendingUp, TrendingDown, Minus, Star, Zap, Heart, Brain, Target } from 'lucide-react';
import * as api from '../services/api';

const PHASE_COLORS = {
  beginning:     { bg: 'rgba(59,130,246,0.08)',  border: 'rgba(59,130,246,0.2)',  text: '#60a5fa' },
  building_trust:{ bg: 'rgba(139,92,246,0.08)',  border: 'rgba(139,92,246,0.2)',  text: '#a78bfa' },
  deepening:     { bg: 'rgba(236,72,153,0.08)',  border: 'rgba(236,72,153,0.2)',  text: '#f472b6' },
  growing:       { bg: 'rgba(52,211,153,0.08)',  border: 'rgba(52,211,153,0.2)',  text: '#34d399' },
  companion:     { bg: 'rgba(251,191,36,0.08)',  border: 'rgba(251,191,36,0.2)',  text: '#fbbf24' },
};

const MILESTONE_ICONS = {
  achievement: Star,
  growth:      TrendingUp,
  insight:     Brain,
  decision:    Target,
  courage:     Heart,
  connection:  Sparkles,
};

const EMOTION_COLORS = {
  happy:     '#34d399',
  motivated: '#fbbf24',
  calm:      '#60a5fa',
  neutral:   '#94a3b8',
  sad:       '#818cf8',
  anxious:   '#a78bfa',
  stressed:  '#fb923c',
  angry:     '#f87171',
};

function TrendIcon({ trend }) {
  if (trend === 'improving') return <TrendingUp size={14} className="text-emerald-400" />;
  if (trend === 'struggling') return <TrendingDown size={14} className="text-red-400" />;
  return <Minus size={14} style={{ color: 'var(--mm-text-muted)' }} />;
}

function GrowthScoreBar({ score }) {
  const pct = Math.round(((score + 10) / 20) * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-[10px]" style={{ color: 'var(--mm-text-muted)' }}>Growth Score</span>
        <span className="text-[10px] font-semibold" style={{
          color: score > 3 ? '#34d399' : score < -3 ? '#f87171' : 'var(--mm-text-secondary)'
        }}>{score > 0 ? `+${score}` : score}</span>
      </div>
      <div className="h-1.5 rounded-full" style={{ background: 'rgba(71,85,105,0.3)' }}>
        <motion.div
          className="h-full rounded-full"
          style={{
            background: score > 3 ? 'linear-gradient(90deg,#34d399,#6ee7b7)' :
                        score < -3 ? 'linear-gradient(90deg,#f87171,#fca5a5)' :
                                     'linear-gradient(90deg,#60a5fa,#818cf8)',
          }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: [0.4, 0, 0.2, 1] }}
        />
      </div>
    </div>
  );
}

function MilestoneItem({ milestone, index }) {
  const Icon = MILESTONE_ICONS[milestone.type] || Star;
  const isMajor = milestone.weight >= 3;
  return (
    <motion.div
      className="growth-node"
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08 }}
    >
      <div className={`growth-dot ${isMajor ? 'milestone' : ''}`} />
      <div className="pb-6">
        <div className="glass rounded-xl p-3 space-y-1.5">
          <div className="flex items-center gap-2">
            <Icon size={12} style={{ color: isMajor ? '#a78bfa' : 'var(--mm-accent)' }} />
            <span className="text-[11px] font-semibold capitalize" style={{
              color: isMajor ? '#a78bfa' : 'var(--mm-text-primary)'
            }}>
              {milestone.type}
            </span>
            <span className="ml-auto text-[9px]" style={{ color: 'var(--mm-text-muted)' }}>
              {milestone.created_at
                ? new Date(milestone.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' })
                : 'Recently'}
            </span>
          </div>
          {milestone.recognition && (
            <p className="text-[11px] italic leading-relaxed" style={{ color: 'var(--mm-text-secondary)' }}>
              "{milestone.recognition}"
            </p>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function TopicPill({ topic }) {
  const arcColors = {
    improving: { bg: 'rgba(52,211,153,0.1)', border: 'rgba(52,211,153,0.2)', text: '#34d399' },
    struggling: { bg: 'rgba(248,113,113,0.1)', border: 'rgba(248,113,113,0.2)', text: '#f87171' },
    neutral: { bg: 'rgba(148,163,184,0.08)', border: 'rgba(148,163,184,0.15)', text: '#94a3b8' },
  };
  const c = arcColors[topic.arc] || arcColors.neutral;
  return (
    <motion.div
      className="flex items-center gap-2 px-3 py-2 rounded-xl"
      style={{ background: c.bg, border: `1px solid ${c.border}` }}
      whileHover={{ scale: 1.02 }}
    >
      <span className="text-base leading-none">{topic.icon}</span>
      <div className="flex-1 min-w-0">
        <p className="text-[11px] font-medium truncate" style={{ color: c.text }}>{topic.label}</p>
        <p className="text-[9px]" style={{ color: 'var(--mm-text-muted)' }}>
          {topic.mentions} mention{topic.mentions !== 1 ? 's' : ''} · {topic.arc}
        </p>
      </div>
      {topic.arc === 'improving' && <TrendingUp size={11} style={{ color: c.text, flexShrink: 0 }} />}
      {topic.arc === 'struggling' && <TrendingDown size={11} style={{ color: c.text, flexShrink: 0 }} />}
    </motion.div>
  );
}

export default function GrowthTimeline() {
  const [arc, setArc] = useState(null);
  const [milestones, setMilestones] = useState([]);
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('journey');

  useEffect(() => {
    if (!api.isAuthenticated || !api.isAuthenticated()) { setLoading(false); return; }
    Promise.all([
      api.getGrowthArc().catch(() => null),
      api.getGrowthTopics().catch(() => null),
    ]).then(([arcData, topicsData]) => {
      if (arcData?.arc) { setArc(arcData.arc); setMilestones(arcData.milestones || []); }
      if (topicsData?.topics) setTopics(topicsData.topics);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          className="w-6 h-6 rounded-full border border-t-transparent"
          style={{ borderColor: 'var(--mm-accent)', borderTopColor: 'transparent' }}
        />
      </div>
    );
  }

  if (!api.isAuthenticated || !api.isAuthenticated()) {
    return (
      <div className="glass rounded-2xl p-6 text-center">
        <Sparkles size={24} className="mx-auto mb-3 text-blue-400" />
        <p className="text-sm" style={{ color: 'var(--mm-text-secondary)' }}>
          Sign in to see your growth journey with Mitra.
        </p>
      </div>
    );
  }

  const phaseColors = PHASE_COLORS[arc?.phase] || PHASE_COLORS.beginning;

  return (
    <div className="space-y-4">
      {/* Relationship Arc Card */}
      {arc && (
        <motion.div
          className="arc-card glass-elevated rounded-2xl p-5 space-y-4"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full"
                  style={{ background: phaseColors.bg, border: `1px solid ${phaseColors.border}`, color: phaseColors.text }}>
                  {arc.label}
                </span>
                <TrendIcon trend={arc.trend} />
              </div>
              <p className="text-[12px] leading-relaxed" style={{ color: 'var(--mm-text-secondary)' }}>
                {arc.description}
              </p>
            </div>
            <div className="text-right space-y-1 flex-shrink-0">
              <p className="text-xl font-bold" style={{ color: 'var(--mm-text-primary)' }}>
                {arc.stats?.days || 0}
              </p>
              <p className="text-[9px]" style={{ color: 'var(--mm-text-muted)' }}>days together</p>
            </div>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Messages', value: arc.stats?.messages || 0, icon: '💬' },
              { label: 'Milestones', value: arc.stats?.milestones || 0, icon: '⭐' },
              { label: 'Feeling now', value: arc.dominant_emotion || 'calm', icon: EMOTION_COLORS[arc.dominant_emotion] ? '●' : '○' },
            ].map(({ label, value, icon }) => (
              <div key={label} className="glass rounded-xl p-2.5 text-center space-y-0.5">
                <p className="text-[11px]">{icon} <span className="font-semibold" style={{ color: 'var(--mm-text-primary)' }}>{value}</span></p>
                <p className="text-[9px]" style={{ color: 'var(--mm-text-muted)' }}>{label}</p>
              </div>
            ))}
          </div>

          <GrowthScoreBar score={arc.growth_score || 0} />
        </motion.div>
      )}

      {/* Tab selector */}
      <div className="flex gap-2">
        {[
          { id: 'journey', label: 'Milestones' },
          { id: 'topics', label: 'Life Topics' },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className="px-3 py-1.5 rounded-lg text-[11px] font-medium transition-all"
            style={{
              background: tab === t.id ? 'rgba(59,130,246,0.15)' : 'rgba(15,23,42,0.4)',
              border: `1px solid ${tab === t.id ? 'rgba(59,130,246,0.3)' : 'rgba(71,85,105,0.2)'}`,
              color: tab === t.id ? 'var(--mm-accent)' : 'var(--mm-text-muted)',
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {tab === 'journey' && (
          <motion.div key="journey" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            {milestones.length === 0 ? (
              <div className="glass rounded-2xl p-6 text-center space-y-3">
                <Zap size={20} className="mx-auto" style={{ color: 'var(--mm-text-muted)' }} />
                <p className="text-sm" style={{ color: 'var(--mm-text-secondary)' }}>
                  Your milestones will appear here as we talk.
                </p>
                <p className="text-[11px]" style={{ color: 'var(--mm-text-muted)' }}>
                  Every breakthrough, every "I finally did it", every insight — Mitra witnesses it.
                </p>
              </div>
            ) : (
              <div className="glass rounded-2xl p-4 pt-5">
                {milestones.map((m, i) => <MilestoneItem key={m.id || i} milestone={m} index={i} />)}
              </div>
            )}
          </motion.div>
        )}

        {tab === 'topics' && (
          <motion.div key="topics" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            {topics.length === 0 ? (
              <div className="glass rounded-2xl p-6 text-center space-y-3">
                <Brain size={20} className="mx-auto" style={{ color: 'var(--mm-text-muted)' }} />
                <p className="text-sm" style={{ color: 'var(--mm-text-secondary)' }}>
                  Topics you discuss will appear here over time.
                </p>
              </div>
            ) : (
              <div className="glass rounded-2xl p-4 grid grid-cols-1 gap-2">
                {topics.map((t, i) => (
                  <motion.div key={t.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}>
                    <TopicPill topic={t} />
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
