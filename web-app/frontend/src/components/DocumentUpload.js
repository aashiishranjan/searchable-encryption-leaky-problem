import React, { useState, useEffect, useCallback } from 'react';
import { getDocuments, loadSampleDocuments, uploadDocuments, resetSession } from '../services/api';

export default function DocumentUpload({ onDocsChange }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const [success, setSuccess]   = useState(null);
  const [customId, setCustomId]   = useState('');
  const [customText, setCustomText] = useState('');
  const [customDocs, setCustomDocs] = useState([]);

  const fetchDocs = useCallback(async () => {
    try {
      const res = await getDocuments();
      setDocuments(res.data.documents || []);
      if (onDocsChange) onDocsChange(res.data.initialized);
    } catch {/* ignore */}
  }, [onDocsChange]);

  useEffect(() => { fetchDocs(); }, [fetchDocs]);

  const flash = (msg, isError = false) => {
    if (isError) { setError(msg); setSuccess(null); }
    else         { setSuccess(msg); setError(null); }
    setTimeout(() => { setError(null); setSuccess(null); }, 4000);
  };

  const handleLoadSamples = async () => {
    setLoading(true);
    try {
      const res = await loadSampleDocuments();
      setDocuments(res.data.documents || []);
      flash(`✅ Loaded ${res.data.count} sample documents.`);
      if (onDocsChange) onDocsChange(true);
    } catch (e) {
      flash(e.response?.data?.error || 'Failed to load samples.', true);
    } finally { setLoading(false); }
  };

  const handleAddCustom = () => {
    if (!customId.trim() || !customText.trim()) {
      flash('Both ID and content are required.', true);
      return;
    }
    const exists = customDocs.find(d => d.id === customId.trim());
    if (exists) { flash('A document with that ID is already in the list.', true); return; }
    setCustomDocs(prev => [...prev, { id: customId.trim(), content: customText.trim() }]);
    setCustomId('');
    setCustomText('');
  };

  const handleRemoveCustom = (id) => {
    setCustomDocs(prev => prev.filter(d => d.id !== id));
  };

  const handleUploadCustom = async () => {
    if (customDocs.length === 0) { flash('Add at least one document first.', true); return; }
    setLoading(true);
    try {
      const res = await uploadDocuments(customDocs);
      setCustomDocs([]);
      await fetchDocs();
      flash(`✅ Uploaded ${customDocs.length} document(s). Total: ${res.data.count}.`);
    } catch (e) {
      flash(e.response?.data?.error || 'Upload failed.', true);
    } finally { setLoading(false); }
  };

  const handleReset = async () => {
    if (!window.confirm('Reset session? All documents and history will be cleared.')) return;
    setLoading(true);
    try {
      await resetSession();
      setDocuments([]);
      setCustomDocs([]);
      flash('✅ Session reset.');
      if (onDocsChange) onDocsChange(false);
    } catch { flash('Reset failed.', true); }
    finally { setLoading(false); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Alert bar */}
      {error   && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {/* Quick-load panel */}
      <div className="card">
        <div className="card-title">📦 Sample Corpus</div>
        <p style={{ marginBottom: '1rem', fontSize: '0.9rem' }}>
          Load the built-in 10-document cybersecurity corpus to get started immediately.
        </p>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button className="btn btn-success" onClick={handleLoadSamples} disabled={loading}>
            {loading ? <span className="spinner" /> : '📥'} Load 10 Sample Documents
          </button>
          <button className="btn btn-danger btn-sm" onClick={handleReset} disabled={loading}>
            🗑 Reset Session
          </button>
        </div>
      </div>

      {/* Custom upload panel */}
      <div className="card">
        <div className="card-title">📝 Upload Custom Documents</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', marginBottom: '0.75rem' }}>
          <input
            className="input-field"
            placeholder="Document ID (e.g. my_doc_1)"
            value={customId}
            onChange={e => setCustomId(e.target.value)}
          />
          <textarea
            className="input-field"
            placeholder="Document content (plain text)..."
            value={customText}
            onChange={e => setCustomText(e.target.value)}
            style={{ minHeight: 90 }}
          />
          <button className="btn btn-primary btn-sm" onClick={handleAddCustom}>
            ＋ Add to Upload List
          </button>
        </div>

        {/* Pending upload list */}
        {customDocs.length > 0 && (
          <div style={{ marginBottom: '0.75rem' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
              Pending upload ({customDocs.length}):
            </div>
            {customDocs.map(d => (
              <div key={d.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)',
                padding: '0.35rem 0.75rem', marginBottom: '0.25rem', fontSize: '0.85rem',
              }}>
                <span style={{ color: 'var(--accent-blue)', fontFamily: 'monospace' }}>{d.id}</span>
                <span style={{ color: 'var(--text-muted)', marginLeft: '0.75rem', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {d.content.slice(0, 60)}…
                </span>
                <button className="btn btn-ghost btn-sm" onClick={() => handleRemoveCustom(d.id)} style={{ marginLeft: '0.5rem' }}>✕</button>
              </div>
            ))}
            <button className="btn btn-primary mt-1" onClick={handleUploadCustom} disabled={loading}>
              {loading ? <span className="spinner" /> : '⬆️'} Upload {customDocs.length} Document(s)
            </button>
          </div>
        )}
      </div>

      {/* Loaded documents list */}
      {documents.length > 0 && (
        <div className="card">
          <div className="card-title">
            📂 Loaded Documents
            <span className="badge badge-teal" style={{ marginLeft: 'auto' }}>{documents.length}</span>
          </div>
          <div style={{ maxHeight: 320, overflowY: 'auto' }}>
            {documents.map((doc, i) => (
              <div key={doc.id} style={{
                padding: '0.5rem 0',
                borderBottom: i < documents.length - 1 ? '1px solid var(--border)' : 'none',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                  <span className="badge badge-blue" style={{ fontFamily: 'monospace' }}>{doc.id}</span>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                  {doc.content.slice(0, 120)}{doc.content.length > 120 ? '…' : ''}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
