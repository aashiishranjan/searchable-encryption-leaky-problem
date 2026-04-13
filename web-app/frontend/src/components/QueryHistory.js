import React, { useState, useEffect, useCallback } from 'react';
import { getHistory, resetSession } from '../services/api';

export default function QueryHistory({ docsLoaded }) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getHistory();
      setData(res.data);
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to load history.');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  const handleReset = async () => {
    if (!window.confirm('Clear all session data and history?')) return;
    try {
      await resetSession();
      setData(null);
    } catch (err) {
      console.error('Session reset failed:', err);
      setError('Failed to reset session. Please try again.');
    }
  };

  if (loading) return (
    <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
      <span className="spinner" /> Loading history…
    </div>
  );

  if (error) return <div className="alert alert-danger">{error}</div>;

  const total = data?.total || 0;
  const history = data?.history || [];
  const stats = data?.statistics;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Stats */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <div className="card-title" style={{ margin: 0 }}>🕓 Query History</div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-ghost btn-sm" onClick={fetchHistory}>🔄 Refresh</button>
            <button className="btn btn-danger btn-sm" onClick={handleReset}>🗑 Reset</button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', marginBottom: '0.75rem' }}>
          <StatCard label="Total Queries" value={total} color="var(--accent-blue)" />
          <StatCard label="Unique Keywords" value={stats?.unique_keywords || 0} color="var(--accent-teal)" />
          <StatCard label="BEFORE / AFTER"
            value={`${stats?.mode_breakdown?.before || 0} / ${stats?.mode_breakdown?.after || 0}`}
            color="var(--accent-yellow)"
          />
        </div>

        {/* Top keywords */}
        {stats?.top_keywords?.length > 0 && (
          <div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
              Most searched keywords:
            </div>
            <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
              {stats.top_keywords.map(({ keyword, count }) => (
                <span key={keyword} className="badge badge-blue">
                  {keyword} ({count}×)
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* History table */}
      {history.length === 0 ? (
        <div className="card">
          <div className="alert alert-info">
            ℹ️ No queries yet. Use the <strong>Search</strong> tab to run your first search.
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="card-title">All Queries</div>
          <div className="scrollable">
            <table className="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Timestamp</th>
                  <th>Keyword</th>
                  <th>Mode</th>
                  <th>Matches</th>
                  <th>Server Sees</th>
                </tr>
              </thead>
              <tbody>
                {[...history].reverse().map((entry, i) => (
                  <tr key={i}>
                    <td style={{ color: 'var(--text-muted)' }}>{history.length - i}</td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {formatTs(entry.timestamp)}
                    </td>
                    <td>
                      <span style={{ color: 'var(--accent-yellow)', fontWeight: 600 }}>
                        {entry.keyword}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${entry.mode === 'before' ? 'badge-red' : 'badge-teal'}`}>
                        {entry.mode === 'before' ? '🔴 BEFORE' : '🟢 AFTER'}
                      </span>
                    </td>
                    <td>{entry.result_count}</td>
                    <td>
                      {entry.mode === 'after' && entry.padded_count != null ? (
                        <span style={{ color: 'var(--accent-teal)' }}>
                          {entry.padded_count} (padded)
                        </span>
                      ) : (
                        <span style={{ color: 'var(--accent-red)' }}>
                          {entry.result_count} (exact)
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: 'var(--bg-secondary)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-sm)',
      padding: '0.6rem 0.85rem',
      textAlign: 'center',
    }}>
      <div style={{ fontSize: '1.5rem', fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>{label}</div>
    </div>
  );
}

function formatTs(ts) {
  if (!ts) return '—';
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' }) +
           ' ' + d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch { return ts; }
}
