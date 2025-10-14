import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

function Insights() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

  useEffect(() => {
    const load = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${API_BASE}/insights`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to load insights');
        const d = await res.json();
        setData(d);
      } catch (e) {
        setError('Could not fetch insights');
      }
    };
    load();
  }, [API_BASE]);

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: 20 }}>
      <h2 style={{ color: '#204b72' }}>Insights</h2>
      {error && <p style={{ color: '#c0392b' }}>{error}</p>}
      {!data ? <p>Loading...</p> : (
        <>
          <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
            <StatCard label="Habits" value={data.summary?.habit_count ?? 0} />
            <StatCard label="Journals" value={data.summary?.journal_count ?? 0} />
          </div>
          <div style={{ background: '#fff', border: '1px solid #e6e9ef', borderRadius: 12, padding: 12, marginBottom: 12 }}>
            <h3 style={{ marginTop: 0 }}>Journal Activity (Last 7 Days)</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={generateJournalChartData(data.journals || [])}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3a6ea5" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div style={{ background: '#fff', border: '1px solid #e6e9ef', borderRadius: 12, padding: 12, marginBottom: 12 }}>
            <h3 style={{ marginTop: 0 }}>Recent Journals</h3>
            {(data.journals || []).slice(0, 5).map(j => (
              <div key={j.id} style={{ borderTop: '1px solid #eef2f7', padding: '8px 0' }}>
                <div style={{ fontSize: 12, color: '#7a8a9e' }}>#{j.id} • {j.created_at ? new Date(j.created_at).toLocaleDateString() : 'No date'}</div>
                <div>{j.content}</div>
              </div>
            ))}
          </div>
          <button onClick={async () => {
            try {
              const token = localStorage.getItem('token');
              const res = await fetch(`${API_BASE}/me/export`, { headers: { 'Authorization': `Bearer ${token}` } });
              const blob = new Blob([JSON.stringify(await res.json(), null, 2)], { type: 'application/json' });
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url; a.download = 'mymitra_export.json'; a.click();
              window.URL.revokeObjectURL(url);
            } catch (e) {
              setError('Failed to export data');
            }
          }} style={{ padding: '10px 14px', borderRadius: 10, border: '1px solid #3a6ea5', background: '#3a6ea5', color: '#fff', fontWeight: 700 }}>
            Download your data
          </button>
        </>
      )}
    </div>
  );
}

function generateJournalChartData(journals) {
  const last7Days = [];
  for (let i = 6; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
    last7Days.push({ day: dayName, count: 0 });
  }
  
  journals.forEach(journal => {
    if (journal.created_at) {
      const journalDate = new Date(journal.created_at);
      const today = new Date();
      const diffTime = Math.abs(today - journalDate);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays <= 6) {
        const dayIndex = 6 - diffDays;
        last7Days[dayIndex].count++;
      }
    }
  });
  
  return last7Days;
}

function StatCard({ label, value }) {
  return (
    <div style={{ flex: 1, background: '#fff', border: '1px solid #e6e9ef', borderRadius: 12, padding: 16 }}>
      <div style={{ color: '#7a8a9e', fontSize: 12 }}>{label}</div>
      <div style={{ color: '#204b72', fontSize: 24, fontWeight: 800 }}>{value}</div>
    </div>
  );
}

export default Insights;


