import React, { useState } from 'react';

const TABS = [
  { id: 'upload',   label: '📁 Documents' },
  { id: 'search',   label: '🔍 Search' },
  { id: 'compare',  label: '⚖️ Compare' },
  { id: 'charts',   label: '📊 Charts' },
  { id: 'history',  label: '🕓 History' },
];

export default function NavBar({ activeTab, onTabChange, docsLoaded }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav style={{
      background: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <div style={{
        maxWidth: 1400,
        margin: '0 auto',
        padding: '0 2rem',
        display: 'flex',
        alignItems: 'center',
        gap: '2rem',
        height: 56,
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
          <span style={{ fontSize: '1.3rem' }}>🔐</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)', lineHeight: 1.2 }}>
              SE Leaky Problem
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              SSE Leakage Demo
            </div>
          </div>
        </div>

        {/* Desktop tabs */}
        <div style={{ display: 'flex', gap: 0, flex: 1 }} className="desktop-tabs">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              style={{ padding: '0 1rem', height: 56, borderRadius: 0 }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Status indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%',
            background: docsLoaded ? 'var(--accent-teal)' : 'var(--accent-red)',
            display: 'inline-block',
          }} />
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            {docsLoaded ? 'Corpus loaded' : 'No corpus'}
          </span>
        </div>
      </div>
    </nav>
  );
}
