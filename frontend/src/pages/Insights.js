import React, { useEffect, useState } from 'react';
import * as api from '../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

function Insights() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [stats, setStats] = useState(null);
  const [recentJournals, setRecentJournals] = useState([]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [insights, journals] = await Promise.all([
          api.getInsights(),
          api.getJournals(),
        ]);
        setRecentJournals(journals);
        // Derive stats locally for last 7 days
        const now = new Date();
        const start = new Date(); start.setDate(now.getDate() - 6);
        const inRange = journals.filter(j => {
          const d = j.created_at ? new Date(j.created_at) : null;
          return d && d >= start && d <= now;
        });
        const uniqueDays = new Set(inRange.map(j => new Date(j.created_at).toISOString().split('T')[0]));
        setStats({
          entries_this_week: inRange.length,
          active_days: uniqueDays.size,
        });
      } catch (e) {
        setError('Could not load insights');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const generateJournalChartData = () => {
    const now = new Date();
    const days = [...Array(7)].map((_, i) => {
      const d = new Date(now);
      d.setDate(now.getDate() - (6 - i));
      return { date: d.toISOString().split('T')[0], label: d.toLocaleDateString(undefined, { weekday: 'short' }), entries: 0 };
    });
    recentJournals.forEach(j => {
      if (!j.created_at) return;
      const dateStr = new Date(j.created_at).toISOString().split('T')[0];
      const day = days.find(x => x.date === dateStr);
      if (day) day.entries += 1;
    });
    return days.map(d => ({ day: d.label, entries: d.entries }));
  };

  const getProgressStore = () => {
    try {
      const raw = localStorage.getItem('habitProgress');
      return raw ? JSON.parse(raw) : {};
    } catch { return {}; }
  };
  const generateWeeklyHabitProgress = () => {
    const store = getProgressStore();
    const today = new Date();
    const days = [...Array(7)].map((_, i) => {
      const d = new Date(today);
      d.setDate(today.getDate() - (6 - i));
      return d.toISOString().split('T')[0];
    });
    const data = days.map(date => {
      let total = 0; let count = 0;
      Object.values(store).forEach(byDate => {
        if (byDate[date] != null) { total += byDate[date]; count += 1; }
      });
      return { day: date.substring(5), percent: count ? Math.round(total / count) : 0 };
    });
    return data;
  };

  const downloadData = () => {
    const dataStr = JSON.stringify({ stats, recentJournals }, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'insights.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return <p>Loading...</p>;
  if (error) return <p style={{ color: '#c0392b' }}>{error}</p>;

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: 20 }}>
      <h2 style={{ color: '#204b72' }}>Insights</h2>
      {stats && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <StatCard title="Journal Entries This Week" value={stats.entries_this_week} />
            <StatCard title="Active Days" value={stats.active_days} />
          </div>

          <div style={{ marginTop: 24 }}>
            <h3 style={{ color: '#204b72' }}>Weekly Journal Activity</h3>
            <BarChart width={600} height={300} data={generateJournalChartData()}>
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="entries" fill="#3a6ea5" />
            </BarChart>
          </div>

          <div style={{ marginTop: 24 }}>
            <h3 style={{ color: '#204b72' }}>Weekly Habit Progress</h3>
            <BarChart width={600} height={300} data={generateWeeklyHabitProgress()}>
              <XAxis dataKey="day" />
              <YAxis domain={[0,100]} tickFormatter={(v) => `${v}%`} />
              <Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="percent" fill="#4caf50" />
            </BarChart>
            <div style={{ fontSize: 12, color: '#7a8a9e' }}>Averages the logged percent across all habits per day.</div>
          </div>

          <div style={{ marginTop: 24 }}>
            <h3 style={{ color: '#204b72' }}>Recent Journals</h3>
            <ul>
              {recentJournals.map(j => (
                <li key={j.id} style={{ marginBottom: 8 }}>
                  <strong>{j.title || 'Untitled'}</strong> — {j.created_at ? new Date(j.created_at).toLocaleString() : 'Unknown time'}
                </li>
              ))}
            </ul>
          </div>

          <div style={{ marginTop: 24 }}>
            <button onClick={downloadData} style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #204b72', background: '#204b72', color: '#fff' }}>
              Export Insights
            </button>
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({ title, value }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e6e9ef', borderRadius: 12, padding: 12 }}>
      <div style={{ fontSize: 12, color: '#7a8a9e' }}>{title}</div>
      <div style={{ fontSize: 24, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

export default Insights;


