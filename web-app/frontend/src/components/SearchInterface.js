import React, { useState } from 'react';
import { searchKeyword } from '../services/api';
import ResultsDisplay from './ResultsDisplay';
import SixStepsDisplay from './SixStepsDisplay';

const SUGGESTED = ['encryption', 'malware', 'ransomware', 'firewall', 'phishing', 'security', 'data', 'network'];

export default function SearchInterface({ docsLoaded }) {
  const [keyword, setKeyword] = useState('');
  const [mode, setMode]       = useState('before');
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState(null);

  const doSearch = async (kw = keyword, m = mode) => {
    const q = kw.trim().toLowerCase();
    if (!q) { setError('Enter a keyword to search.'); return; }
    if (!docsLoaded) { setError('Load documents first (Documents tab).'); return; }
    setError(null);
    setLoading(true);
    try {
      const res = await searchKeyword(q, m);
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.error || 'Search failed.');
    } finally { setLoading(false); }
  };

  const handleKey = (e) => { if (e.key === 'Enter') doSearch(); };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Search box */}
      <div className="card">
        <div className="card-title">🔍 Keyword Search</div>

        {!docsLoaded && (
          <div className="alert alert-warning mb-2">
            ⚠️ No document corpus loaded. Go to the <strong>Documents</strong> tab and load samples first.
          </div>
        )}

        {/* Mode toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Mode:</span>
          <div className="mode-toggle">
            <button
              className={mode === 'before' ? 'active-before' : ''}
              onClick={() => setMode('before')}
            >
              🔴 BEFORE
            </button>
            <button
              className={mode === 'after' ? 'active-after' : ''}
              onClick={() => setMode('after')}
            >
              🟢 AFTER
            </button>
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {mode === 'before'
              ? 'Full leakage — server sees exact result counts and patterns.'
              : 'Mitigated — results padded to hide volume leakage.'}
          </span>
        </div>

        {/* Input row */}
        <div style={{ display: 'flex', gap: '0.6rem' }}>
          <input
            className="input-field"
            placeholder="Enter keyword (e.g. encryption)"
            value={keyword}
            onChange={e => setKeyword(e.target.value)}
            onKeyDown={handleKey}
            autoFocus
          />
          <button
            className="btn btn-primary"
            onClick={() => doSearch()}
            disabled={loading || !docsLoaded}
            style={{ flexShrink: 0 }}
          >
            {loading ? <span className="spinner" /> : '🔍'} Search
          </button>
        </div>

        {/* Suggestions */}
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.65rem' }}>
          {SUGGESTED.map(s => (
            <button
              key={s}
              className="btn btn-ghost btn-sm"
              onClick={() => { setKeyword(s); doSearch(s); }}
              disabled={loading || !docsLoaded}
            >
              {s}
            </button>
          ))}
        </div>

        {error && <div className="alert alert-danger mt-2">{error}</div>}
      </div>

      {/* Results */}
      {result && (
        <>
          <ResultsDisplay result={result} />
          <SixStepsDisplay steps={result.steps} mode={result.mode} />
        </>
      )}
    </div>
  );
}
