import React, { useState } from 'react';
import { compareKeyword } from '../services/api';
import ResultsDisplay from './ResultsDisplay';

const SUGGESTED = ['encryption', 'malware', 'ransomware', 'firewall', 'phishing'];

export default function ComparisonView({ docsLoaded }) {
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData]       = useState(null);
  const [error, setError]     = useState(null);

  const doCompare = async (kw = keyword) => {
    const q = (kw || keyword).trim().toLowerCase();
    if (!q) { setError('Enter a keyword.'); return; }
    if (!docsLoaded) { setError('Load documents first (Documents tab).'); return; }
    setError(null);
    setLoading(true);
    try {
      const res = await compareKeyword(q);
      setData(res.data);
    } catch (e) {
      setError(e.response?.data?.error || 'Comparison failed.');
    } finally { setLoading(false); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header */}
      <div className="card">
        <div className="card-title">⚖️ Before / After Comparison</div>
        <p style={{ marginBottom: '1rem', fontSize: '0.9rem' }}>
          Run the same keyword in both modes side-by-side to see how result-padding mitigation
          hides the true match count from the server.
        </p>

        {!docsLoaded && (
          <div className="alert alert-warning mb-2">
            ⚠️ Load documents first (Documents tab).
          </div>
        )}

        <div style={{ display: 'flex', gap: '0.6rem' }}>
          <input
            className="input-field"
            placeholder="Keyword to compare (e.g. encryption)"
            value={keyword}
            onChange={e => setKeyword(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && doCompare()}
          />
          <button
            className="btn btn-primary"
            onClick={() => doCompare()}
            disabled={loading || !docsLoaded}
            style={{ flexShrink: 0 }}
          >
            {loading ? <span className="spinner" /> : '⚖️'} Compare
          </button>
        </div>

        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.65rem' }}>
          {SUGGESTED.map(s => (
            <button key={s} className="btn btn-ghost btn-sm" onClick={() => { setKeyword(s); doCompare(s); }} disabled={loading || !docsLoaded}>
              {s}
            </button>
          ))}
        </div>

        {error && <div className="alert alert-danger mt-2">{error}</div>}
      </div>

      {/* Side-by-side comparison */}
      {data && (
        <>
          <div className="alert alert-info" style={{ fontSize: '0.88rem' }}>
            Comparing keyword <strong>«{data.keyword}»</strong> in BEFORE vs AFTER mode.
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <div style={{ marginBottom: '0.6rem' }}>
                <span className="badge badge-red" style={{ fontSize: '0.88rem' }}>🔴 BEFORE — Full Leakage</span>
              </div>
              <ResultsDisplay result={data.before} />
              <CompareMetrics result={data.before} />
            </div>
            <div>
              <div style={{ marginBottom: '0.6rem' }}>
                <span className="badge badge-teal" style={{ fontSize: '0.88rem' }}>🟢 AFTER — With Mitigation</span>
              </div>
              <ResultsDisplay result={data.after} />
              <CompareMetrics result={data.after} />
            </div>
          </div>
          <DiffSummary before={data.before} after={data.after} />
        </>
      )}
    </div>
  );
}

function CompareMetrics({ result }) {
  const step4 = result.steps?.step4;
  if (!step4) return null;
  const { ngram, document: doc, term, result: res } = step4.leakage_types;
  const isAfter = result.mode === 'after';

  return (
    <div className="card mt-2" style={{ fontSize: '0.85rem' }}>
      <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Leakage Metrics</div>
      <MetricRow label="Repeated trapdoors" value={ngram.repeated_count} bad={ngram.repeated_count > 0} />
      <MetricRow label="Unique trapdoors" value={doc.entries.length} />
      <MetricRow label="Volume visible to server"
        value={isAfter ? `${result.padded_count} (padded)` : `${result.real_count} (exact)`}
        bad={!isAfter}
        good={isAfter}
      />
      <MetricRow label="True match count" value={result.real_count} />
    </div>
  );
}

function MetricRow({ label, value, bad, good }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.2rem 0', borderBottom: '1px solid var(--border)' }}>
      <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
      <span style={{ color: bad ? 'var(--accent-red)' : good ? 'var(--accent-teal)' : 'var(--text-primary)', fontWeight: 600 }}>
        {String(value)}
      </span>
    </div>
  );
}

function DiffSummary({ before, after }) {
  const beforeCount = before.real_count;
  const afterPadded = after.padded_count ?? after.real_count;
  const hidden = afterPadded !== beforeCount;

  return (
    <div className="card" style={{ borderLeft: '3px solid var(--accent-teal)' }}>
      <div className="card-title">📊 Summary</div>
      <div style={{ fontSize: '0.88rem', lineHeight: 1.8 }}>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Real matching docs: </span>
          <strong style={{ color: 'var(--accent-blue)' }}>{beforeCount}</strong>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>BEFORE — server sees: </span>
          <strong style={{ color: 'var(--accent-red)' }}>{beforeCount} (exact count)</strong>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>AFTER — server sees: </span>
          <strong style={{ color: 'var(--accent-teal)' }}>{afterPadded} (padded)</strong>
        </div>
        {hidden ? (
          <div className="alert alert-success mt-2" style={{ fontSize: '0.83rem' }}>
            ✅ <strong>Mitigation effective:</strong> The server cannot distinguish whether the keyword
            matched {beforeCount} or {afterPadded} documents.
          </div>
        ) : (
          <div className="alert alert-warning mt-2" style={{ fontSize: '0.83rem' }}>
            ⚠️ Padding has no effect when the real count already equals the pad size ({beforeCount}).
          </div>
        )}
      </div>
    </div>
  );
}
