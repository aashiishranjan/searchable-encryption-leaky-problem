import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  PieChart, Pie, Cell, ResponsiveContainer, Legend,
} from 'recharts';
import { getAnalysis } from '../services/api';

const COLORS = [
  '#4a9eff', '#1dd3b0', '#e74c3c', '#f39c12',
  '#9b59b6', '#2ecc71', '#e67e22', '#1abc9c',
  '#3498db', '#e91e63',
];

const LEAKAGE_COLORS = {
  ngram:    '#f39c12',
  document: '#9b59b6',
  term:     '#4a9eff',
  result:   '#e74c3c',
};

export default function LeakageCharts({ docsLoaded }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);

  const fetchAnalysis = useCallback(async () => {
    if (!docsLoaded) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getAnalysis();
      setAnalysis(res.data);
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to load analysis.');
    } finally { setLoading(false); }
  }, [docsLoaded]);

  useEffect(() => { fetchAnalysis(); }, [fetchAnalysis]);

  if (!docsLoaded) {
    return (
      <div className="card">
        <div className="alert alert-warning">
          ⚠️ Load documents and perform at least one search to see charts.
        </div>
      </div>
    );
  }

  if (loading) {
    return <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
      <span className="spinner" /> Loading analysis…
    </div>;
  }

  if (error) return <div className="alert alert-danger">{error}</div>;

  if (!analysis || analysis.total_queries === 0) {
    return (
      <div className="card">
        <div className="alert alert-info">
          ℹ️ No queries logged yet. Perform a search in the <strong>Search</strong> tab first.
        </div>
        <button className="btn btn-primary mt-2" onClick={fetchAnalysis}>🔄 Refresh</button>
      </div>
    );
  }

  // Frequency bar chart data
  const freqData = (analysis.frequency?.entries || []).slice(0, 10).map((e, i) => ({
    name: `T${i + 1}`,
    count: e.count,
    trapdoor: e.trapdoor,
    pct: e.percentage,
  }));

  // Attack results bar chart
  const attackData = (analysis.attack_results || []).slice(0, 10).map(r => ({
    keyword: r.guessed_keyword,
    confidence: r.confidence_pct,
    freq: r.trapdoor_frequency,
  }));

  // Volume pie chart
  const volData = (analysis.volume?.entries || []).slice(0, 8).map((e, i) => ({
    name: `T${i + 1}`,
    value: e.result_count,
    trapdoor: e.trapdoor,
  }));

  // Leakage type summary pie
  const leakageSummary = [
    { name: '3-gram / Search Pattern', value: analysis.search_pattern?.repeated_count || 0, color: LEAKAGE_COLORS.ngram },
    { name: 'Access Pattern', value: (analysis.access_pattern?.entries || []).length, color: LEAKAGE_COLORS.document },
    { name: 'Frequency / Term', value: (analysis.frequency?.entries || []).length, color: LEAKAGE_COLORS.term },
    { name: 'Volume / Result', value: (analysis.volume?.entries || []).length, color: LEAKAGE_COLORS.result },
  ].filter(d => d.value > 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3>📊 Leakage Visualisation</h3>
        <button className="btn btn-ghost btn-sm" onClick={fetchAnalysis}>🔄 Refresh</button>
      </div>

      <div className="alert alert-info" style={{ fontSize: '0.85rem' }}>
        Session total: <strong>{analysis.total_queries}</strong> queries logged.
      </div>

      {/* Row 1: Frequency bar + Leakage-type pie */}
      <div className="grid-2">
        {/* Trapdoor Frequency */}
        <div className="card">
          <div className="card-title">📈 Trapdoor Query Frequency</div>
          <p style={{ fontSize: '0.82rem', marginBottom: '0.75rem' }}>
            How often each encrypted trapdoor token was observed (top 10).
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={freqData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d4a62" />
              <XAxis dataKey="name" tick={{ fill: '#8fa8c0', fontSize: 11 }} />
              <YAxis tick={{ fill: '#8fa8c0', fontSize: 11 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{ background: '#1e3448', border: '1px solid #2d4a62', borderRadius: 6, fontSize: 12 }}
                labelStyle={{ color: '#e8f0f8' }}
                formatter={(val, _, props) => {
                  const payload = props && props.payload;
                  return [`${val} queries (${payload?.pct ?? 0}%)`, payload?.trapdoor ?? ''];
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {freqData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Leakage type distribution */}
        <div className="card">
          <div className="card-title">🥧 Leakage Type Distribution</div>
          <p style={{ fontSize: '0.82rem', marginBottom: '0.75rem' }}>
            Number of distinct entries per leakage type.
          </p>
          {leakageSummary.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={leakageSummary}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, value }) => `${name.split('/')[0].trim()}: ${value}`}
                  labelLine={{ stroke: '#5a7a96' }}
                >
                  {leakageSummary.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#1e3448', border: '1px solid #2d4a62', borderRadius: 6, fontSize: 12 }}
                  formatter={(val, name) => [val, name]}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '2rem' }}>
              No leakage data yet.
            </div>
          )}
        </div>
      </div>

      {/* Row 2: Attack confidence + Volume */}
      <div className="grid-2">
        {/* Attack confidence */}
        <div className="card">
          <div className="card-title">⚠️ Frequency Attack Confidence</div>
          <p style={{ fontSize: '0.82rem', marginBottom: '0.75rem' }}>
            How confident the adversary's keyword guesses are (higher = more dangerous).
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={attackData} layout="vertical" margin={{ top: 5, right: 30, left: 60, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d4a62" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={{ fill: '#8fa8c0', fontSize: 11 }} tickFormatter={v => `${v}%`} />
              <YAxis type="category" dataKey="keyword" tick={{ fill: '#f39c12', fontSize: 11 }} width={55} />
              <Tooltip
                contentStyle={{ background: '#1e3448', border: '1px solid #2d4a62', borderRadius: 6, fontSize: 12 }}
                formatter={(val) => [`${val}%`, 'Confidence']}
              />
              <Bar dataKey="confidence" radius={[0, 4, 4, 0]}>
                {attackData.map((d, i) => (
                  <Cell key={i} fill={d.confidence > 70 ? '#e74c3c' : d.confidence > 40 ? '#f39c12' : '#4a9eff'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Volume per trapdoor */}
        <div className="card">
          <div className="card-title">📦 Result Volume per Trapdoor</div>
          <p style={{ fontSize: '0.82rem', marginBottom: '0.75rem' }}>
            Number of documents returned per unique trapdoor (volume leakage).
          </p>
          {volData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={volData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {volData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#1e3448', border: '1px solid #2d4a62', borderRadius: 6, fontSize: 12 }}
                  formatter={(val, name, props) => [`${val} results`, props.payload?.trapdoor]}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '2rem' }}>
              No volume data yet.
            </div>
          )}
        </div>
      </div>

      {/* Attack results table */}
      <div className="card">
        <div className="card-title">🕵️ Frequency Analysis Attack — Full Results</div>
        <div className="scrollable">
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                <th>Trapdoor (preview)</th>
                <th>Guessed Keyword</th>
                <th>Observed Freq.</th>
                <th>Known Freq.</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {(analysis.attack_results || []).map((r, i) => (
                <tr key={i}>
                  <td style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                  <td><code style={{ color: 'var(--accent-teal)', fontSize: '0.82rem' }}>{r.trapdoor}</code></td>
                  <td style={{ color: 'var(--accent-yellow)', fontWeight: 600 }}>{r.guessed_keyword}</td>
                  <td>{r.trapdoor_frequency}×</td>
                  <td>{(r.known_frequency * 100).toFixed(1)}%</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span style={{
                        minWidth: 40, fontWeight: 600,
                        color: r.confidence > 0.7 ? 'var(--accent-red)' : r.confidence > 0.4 ? 'var(--accent-yellow)' : 'var(--text-muted)',
                      }}>
                        {r.confidence_pct}%
                      </span>
                      <div className="conf-bar-wrapper" style={{ width: 60 }}>
                        <div className="conf-bar" style={{
                          width: `${r.confidence_pct}%`,
                          background: r.confidence > 0.7 ? 'var(--accent-red)' : 'var(--accent-blue)',
                        }} />
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
