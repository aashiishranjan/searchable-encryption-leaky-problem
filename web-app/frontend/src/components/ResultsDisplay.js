import React from 'react';

export default function ResultsDisplay({ result }) {
  if (!result) return null;

  const { keyword, mode, real_count, padded_count, results } = result;

  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
        <div className="card-title" style={{ margin: 0 }}>
          🗂 Results for &quot;{keyword}&quot;
        </div>
        <span className={`badge ${mode === 'before' ? 'badge-red' : 'badge-teal'}`}>
          {mode === 'before' ? '🔴 BEFORE' : '🟢 AFTER'}
        </span>
        <span className="badge badge-blue">
          {real_count} match{real_count !== 1 ? 'es' : ''}
        </span>
        {mode === 'after' && padded_count != null && (
          <span className="badge badge-yellow">
            Server sees: {padded_count} (padded)
          </span>
        )}
      </div>

      {mode === 'after' && (
        <div className="alert alert-success mb-2" style={{ fontSize: '0.85rem' }}>
          🛡 Volume-leakage mitigation active: server receives {padded_count} entries
          instead of {real_count} — hiding the true match count.
        </div>
      )}

      {results.length === 0 ? (
        <div className="alert alert-info">No documents matched &quot;{keyword}&quot;.</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          {results.map((doc, i) => (
            <div key={doc.id} style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.75rem 1rem',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>#{i + 1}</span>
                <span className="badge badge-blue" style={{ fontFamily: 'monospace' }}>{doc.id}</span>
              </div>
              <p style={{ margin: 0, fontSize: '0.88rem', lineHeight: 1.55 }}>
                {doc.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
