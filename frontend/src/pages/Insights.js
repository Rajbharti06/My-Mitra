import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Download, BookOpen, Target } from 'lucide-react';
import GrowthTimeline from '../components/GrowthTimeline';
import * as api from '../services/api';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-lg px-3 py-2 text-xs" style={{ color: 'var(--mm-text-primary)' }}>
      <p className="font-medium mb-0.5">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.fill }}>{p.name}: {p.value}{p.name === 'habit %' ? '%' : ''}</p>
      ))}
    </div>
  );
};

function StatCard({ title, value, sub }) {
  return (
    <motion.div
      className="glass rounded-xl p-4 space-y-1"
      whileHover={{ scale: 1.01 }}
    >
      <p className="text-[10px] uppercase tracking-wide" style={{ color: 'var(--mm-text-muted)' }}>{title}</p>
      <p className="text-2xl font-bold" style={{ color: 'var(--mm-text-primary)' }}>{value}</p>
      {sub && <p className="text-[10px]" style={{ color: 'var(--mm-text-muted)' }}>{sub}</p>}
    </motion.div>
  );
}

function Insights() {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [recentJournals, setRecentJournals] = useState([]);
  const [activeSection, setActiveSection] = useState('growth');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [, journals] = await Promise.all([
          api.getInsights().catch(() => null),
          api.getJournals().catch(() => []),
        ]);
        const jList = Array.isArray(journals) ? journals : [];
        setRecentJournals(jList);
        const now = new Date();
        const start = new Date(); start.setDate(now.getDate() - 6);
        const inRange = jList.filter(j => {
          const d = j.created_at ? new Date(j.created_at) : null;
          return d && d >= start && d <= now;
        });
        const uniqueDays = new Set(inRange.map(j => new Date(j.created_at).toISOString().split('T')[0]));
        setStats({ entries_this_week: inRange.length, active_days: uniqueDays.size });
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const journalChartData = () => {
    const now = new Date();
    const days = [...Array(7)].map((_, i) => {
      const d = new Date(now);
      d.setDate(now.getDate() - (6 - i));
      return { date: d.toISOString().split('T')[0], day: d.toLocaleDateString(undefined, { weekday: 'short' }), entries: 0 };
    });
    recentJournals.forEach(j => {
      if (!j.created_at) return;
      const dateStr = new Date(j.created_at).toISOString().split('T')[0];
      const slot = days.find(x => x.date === dateStr);
      if (slot) slot.entries += 1;
    });
    return days.map(({ day, entries }) => ({ day, entries }));
  };

  const habitChartData = () => {
    try {
      const store = JSON.parse(localStorage.getItem('habitProgress') || '{}');
      const now = new Date();
      return [...Array(7)].map((_, i) => {
        const d = new Date(now);
        d.setDate(now.getDate() - (6 - i));
        const date = d.toISOString().split('T')[0];
        let total = 0; let count = 0;
        Object.values(store).forEach(byDate => {
          if (byDate[date] != null) { total += byDate[date]; count += 1; }
        });
        return { day: d.toLocaleDateString(undefined, { weekday: 'short' }), 'habit %': count ? Math.round(total / count) : 0 };
      });
    } catch { return []; }
  };

  const downloadData = () => {
    const blob = new Blob([JSON.stringify({ stats, recentJournals }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'mymitra-insights.json'; a.click();
    URL.revokeObjectURL(url);
  };

  const sections = [
    { id: 'growth', label: 'Your Journey' },
    { id: 'activity', label: 'Activity' },
  ];

  return (
    <div className="max-w-2xl mx-auto px-6 py-6 space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-base font-semibold" style={{ color: 'var(--mm-text-primary)' }}>
          Insights
        </h1>
        <motion.button
          onClick={downloadData}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px]"
          style={{ background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.15)', color: 'var(--mm-accent)' }}
        >
          <Download size={12} />
          Export
        </motion.button>
      </div>

      {/* Section tabs */}
      <div className="flex gap-2">
        {sections.map(s => (
          <button key={s.id} onClick={() => setActiveSection(s.id)}
            className="px-3 py-1.5 rounded-lg text-[11px] font-medium transition-all"
            style={{
              background: activeSection === s.id ? 'rgba(59,130,246,0.15)' : 'transparent',
              border: `1px solid ${activeSection === s.id ? 'rgba(59,130,246,0.3)' : 'rgba(71,85,105,0.2)'}`,
              color: activeSection === s.id ? 'var(--mm-accent)' : 'var(--mm-text-muted)',
            }}>
            {s.label}
          </button>
        ))}
      </div>

      {/* Growth Journey Section */}
      {activeSection === 'growth' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <GrowthTimeline />
        </motion.div>
      )}

      {/* Activity Section */}
      {activeSection === 'activity' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-5 h-5 rounded-full border border-t-transparent animate-spin" style={{ borderColor: 'var(--mm-accent)', borderTopColor: 'transparent' }} />
            </div>
          ) : (
            <>
              {/* Stats row */}
              {stats && (
                <div className="grid grid-cols-2 gap-3">
                  <StatCard title="Journal entries this week" value={stats.entries_this_week} sub="Keep writing" />
                  <StatCard title="Active days" value={stats.active_days} sub="Out of 7" />
                </div>
              )}

              {/* Journal chart */}
              <div className="glass-elevated rounded-2xl p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <BookOpen size={13} style={{ color: 'var(--mm-accent)' }} />
                  <span className="text-[11px] font-semibold" style={{ color: 'var(--mm-text-secondary)' }}>
                    Journal Activity (7 days)
                  </span>
                </div>
                <ResponsiveContainer width="100%" height={140}>
                  <BarChart data={journalChartData()} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                    <XAxis dataKey="day" tick={{ fontSize: 10, fill: 'var(--mm-text-muted)' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: 'var(--mm-text-muted)' }} axisLine={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(59,130,246,0.05)' }} />
                    <Bar dataKey="entries" fill="rgba(59,130,246,0.6)" radius={[4, 4, 0, 0]} name="entries" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Habit chart */}
              <div className="glass-elevated rounded-2xl p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <Target size={13} style={{ color: '#34d399' }} />
                  <span className="text-[11px] font-semibold" style={{ color: 'var(--mm-text-secondary)' }}>
                    Habit Completion (7 days)
                  </span>
                </div>
                <ResponsiveContainer width="100%" height={140}>
                  <BarChart data={habitChartData()} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                    <XAxis dataKey="day" tick={{ fontSize: 10, fill: 'var(--mm-text-muted)' }} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--mm-text-muted)' }} axisLine={false} tickLine={false} tickFormatter={v => `${v}%`} />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(52,211,153,0.05)' }} />
                    <Bar dataKey="habit %" fill="rgba(52,211,153,0.6)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
                <p className="text-[9px]" style={{ color: 'var(--mm-text-muted)' }}>
                  Average completion across all habits per day.
                </p>
              </div>

              {/* Recent journals */}
              {recentJournals.length > 0 && (
                <div className="glass rounded-2xl p-4 space-y-2">
                  <p className="text-[11px] font-semibold" style={{ color: 'var(--mm-text-secondary)' }}>Recent Journals</p>
                  {recentJournals.slice(0, 5).map(j => (
                    <div key={j.id} className="flex items-center justify-between py-1.5 border-b border-white/5 last:border-0">
                      <p className="text-[11px] truncate flex-1 pr-2" style={{ color: 'var(--mm-text-primary)' }}>
                        {j.content ? j.content.slice(0, 40) + '…' : 'Entry'}
                      </p>
                      <p className="text-[9px] flex-shrink-0" style={{ color: 'var(--mm-text-muted)' }}>
                        {j.created_at ? new Date(j.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' }) : ''}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </motion.div>
      )}
    </div>
  );
}

export default Insights;
