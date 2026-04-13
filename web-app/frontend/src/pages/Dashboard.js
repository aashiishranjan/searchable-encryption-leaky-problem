import React, { useState } from 'react';
import NavBar from '../components/NavBar';
import DocumentUpload from '../components/DocumentUpload';
import SearchInterface from '../components/SearchInterface';
import ComparisonView from '../components/ComparisonView';
import LeakageCharts from '../components/LeakageCharts';
import QueryHistory from '../components/QueryHistory';

export default function Dashboard() {
  const [tab, setTab]         = useState('upload');
  const [docsLoaded, setDocsLoaded] = useState(false);

  const handleDocsChange = (loaded) => {
    setDocsLoaded(!!loaded);
  };

  const renderTab = () => {
    switch (tab) {
      case 'upload':  return <DocumentUpload onDocsChange={handleDocsChange} />;
      case 'search':  return <SearchInterface docsLoaded={docsLoaded} />;
      case 'compare': return <ComparisonView docsLoaded={docsLoaded} />;
      case 'charts':  return <LeakageCharts docsLoaded={docsLoaded} />;
      case 'history': return <QueryHistory docsLoaded={docsLoaded} />;
      default:        return null;
    }
  };

  return (
    <div className="app-wrapper">
      <NavBar activeTab={tab} onTabChange={setTab} docsLoaded={docsLoaded} />
      <main className="main-content">
        {/* Page title */}
        <div style={{ marginBottom: '1.5rem' }}>
          <h1 style={{ fontSize: '1.4rem', marginBottom: '0.25rem' }}>
            🔐 Searchable Encryption Leaky Problem
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
            Interactive demonstration of SSE leakage types, frequency analysis attacks,
            and mitigation strategies. &nbsp;
            <a href="https://github.com/aashiishranjan/searchable-encryption-leaky-problem" target="_blank" rel="noreferrer">
              GitHub ↗
            </a>
          </p>
        </div>

        {/* Quick-start banner when no corpus loaded */}
        {!docsLoaded && tab !== 'upload' && (
          <div className="alert alert-warning mb-2" style={{ marginBottom: '1rem' }}>
            📁 No document corpus loaded yet.{' '}
            <button
              className="btn btn-success btn-sm"
              style={{ marginLeft: '0.5rem' }}
              onClick={() => setTab('upload')}
            >
              Go to Documents
            </button>
          </div>
        )}

        {renderTab()}
      </main>
    </div>
  );
}
