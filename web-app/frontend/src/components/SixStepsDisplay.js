import React, { useState } from 'react';

function StepCard({ number, color, title, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="card" style={{ borderLeft: `3px solid ${color}` }}>
      <div className="step-header" onClick={() => setOpen(o => !o)}>
        <div className="step-number" style={{ background: color }}>
          {number}
        </div>
        <div className="step-title">{title}</div>
        <span className="step-chevron">{open ? '▲' : '▼'}</span>
      </div>
      {open && <div className="step-body">{children}</div>}
    </div>
  );
}

// --- Step 1 ---
function Step1({ step }) {
  return (
    <div>
      <p style={{ marginBottom: '0.5rem' }}>{step.description}</p>
      <div className="code-block">
        🔑 {step.key_hex}
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
        <span className="badge badge-blue">{step.algorithm}</span>
        <span className="badge badge-muted">{step.key_length_bytes * 8}-bit key</span>
      </div>
    </div>
  );
}

// --- Step 2 ---
function Step2({ step }) {
  return (
    <div>
      <p style={{ marginBottom: '0.75rem' }}>{step.description}</p>
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
        <div style={{ textAlign: 'center', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', padding: '0.5rem 1rem' }}>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-teal)' }}>{step.num_documents}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>documents</div>
        </div>
        <div style={{ textAlign: 'center', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', padding: '0.5rem 1rem' }}>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-blue)' }}>{step.num_tokens}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>encrypted tokens</div>
        </div>
      </div>
      <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Sample index entries (server view):</div>
      {step.sample_entries.map((e, i) => (
        <div key={i} style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)',
          padding: '0.3rem 0.75rem', marginBottom: '0.25rem', fontSize: '0.82rem',
        }}>
          <code style={{ color: 'var(--accent-teal)' }}>{e.token}</code>
          <span className="badge badge-muted">{e.doc_count} doc{e.doc_count !== 1 ? 's' : ''}</span>
        </div>
      ))}
      <p style={{ fontSize: '0.83rem', marginTop: '0.5rem', color: 'var(--text-muted)' }}>
        ℹ️ {step.observation}
      </p>
    </div>
  );
}

// --- Step 3 ---
function Step3({ step }) {
  return (
    <div>
      <p style={{ marginBottom: '0.75rem' }}>{step.description}</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.88rem' }}>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Keyword searched: </span>
          <strong style={{ color: 'var(--accent-yellow)' }}>«{step.keyword}»</strong>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
            (never sent to server)
          </span>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Trapdoor sent: </span>
          <code style={{ color: 'var(--accent-teal)', fontSize: '0.85rem' }}>{step.trapdoor_preview}</code>
        </div>
      </div>
      <div className={`alert ${step.mode === 'before' ? 'alert-warning' : 'alert-success'} mt-2`} style={{ fontSize: '0.83rem' }}>
        {step.mode === 'before' ? '🔴' : '🟢'} {step.padding_note}
      </div>
    </div>
  );
}

// --- Step 4 ---
function LeakageTypeCard({ label, description, color, children }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{
      background: 'var(--bg-secondary)', border: `1px solid ${color}33`,
      borderRadius: 'var(--radius-sm)', marginBottom: '0.5rem',
    }}>
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: '0.5rem',
          padding: '0.5rem 0.75rem', cursor: 'pointer',
        }}
        onClick={() => setOpen(o => !o)}
      >
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, display: 'inline-block', flexShrink: 0 }} />
        <span style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text-primary)' }}>{label}</span>
        <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: '0.78rem' }}>{open ? '▲' : '▼'}</span>
      </div>
      {open && (
        <div style={{ padding: '0 0.75rem 0.75rem 1.5rem' }}>
          <p style={{ fontSize: '0.82rem', marginBottom: '0.5rem' }}>{description}</p>
          {children}
        </div>
      )}
    </div>
  );
}

function Step4({ step }) {
  const lt = step.leakage_types;
  return (
    <div>
      <p style={{ marginBottom: '0.75rem' }}>{step.description}</p>

      <LeakageTypeCard label={lt.ngram.label} description={lt.ngram.description} color="var(--accent-yellow)">
        {lt.ngram.repeated_count > 0 ? (
          <>
            <div style={{ fontSize: '0.82rem', color: 'var(--accent-yellow)', marginBottom: '0.4rem' }}>
              ⚠️ {lt.ngram.repeated_count} repeated trapdoor(s) detected:
            </div>
            {lt.ngram.entries.map((e, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', padding: '0.2rem 0' }}>
                <code style={{ color: 'var(--accent-teal)' }}>{e.trapdoor}</code>
                <span className="badge badge-yellow">{e.count}×</span>
              </div>
            ))}
          </>
        ) : (
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>No repeated trapdoors yet.</div>
        )}
      </LeakageTypeCard>

      <LeakageTypeCard label={lt.document.label} description={lt.document.description} color="var(--accent-purple)">
        {lt.document.entries.slice(0, 5).map((e, i) => (
          <div key={i} style={{ fontSize: '0.82rem', padding: '0.2rem 0', borderBottom: '1px solid var(--border)' }}>
            <code style={{ color: 'var(--accent-teal)' }}>{e.trapdoor}</code>
            <span style={{ color: 'var(--text-muted)', marginLeft: '0.5rem' }}>→ {e.doc_count} doc(s)</span>
          </div>
        ))}
      </LeakageTypeCard>

      <LeakageTypeCard label={lt.term.label} description={lt.term.description} color="var(--accent-blue)">
        {lt.term.entries.map((e, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', padding: '0.2rem 0' }}>
            <code style={{ color: 'var(--accent-teal)', flex: 1 }}>{e.trapdoor}</code>
            <span style={{ color: 'var(--text-muted)', margin: '0 0.5rem' }}>{e.count}×</span>
            <span style={{ color: 'var(--text-muted)' }}>{e.percentage}%</span>
          </div>
        ))}
      </LeakageTypeCard>

      <LeakageTypeCard label={lt.result.label} description={lt.result.description} color="var(--accent-red)">
        {lt.result.padded && (
          <div style={{ fontSize: '0.82rem', color: 'var(--accent-teal)', marginBottom: '0.4rem' }}>
            🛡 Padded to {lt.result.padded_size} — volume hidden.
          </div>
        )}
        {lt.result.entries.slice(0, 5).map((e, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', padding: '0.2rem 0' }}>
            <code style={{ color: 'var(--accent-teal)' }}>{e.trapdoor}</code>
            <span className="badge badge-muted">{e.result_count} result(s)</span>
          </div>
        ))}
      </LeakageTypeCard>
    </div>
  );
}

// --- Step 5 ---
function Step5({ step }) {
  return (
    <div>
      <p style={{ marginBottom: '0.75rem' }}>{step.description}</p>
      <div className="scrollable">
        <table className="table" style={{ minWidth: 480 }}>
          <thead>
            <tr>
              <th>Trapdoor</th>
              <th>Guessed Keyword</th>
              <th>Obs. Freq.</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {step.attack_results.map((r, i) => (
              <tr key={i}>
                <td><code style={{ color: 'var(--accent-teal)' }}>{r.trapdoor}</code></td>
                <td>
                  <span style={{ color: 'var(--accent-yellow)', fontWeight: 600 }}>
                    {r.guessed_keyword}
                  </span>
                </td>
                <td>{r.trapdoor_frequency}×</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{
                      minWidth: 42, fontSize: '0.82rem', fontWeight: 600,
                      color: r.confidence > 0.7 ? 'var(--accent-red)' : r.confidence > 0.4 ? 'var(--accent-yellow)' : 'var(--text-muted)',
                    }}>
                      {r.confidence_pct}%
                    </span>
                    <div className="conf-bar-wrapper" style={{ flex: 1, minWidth: 60 }}>
                      <div
                        className="conf-bar"
                        style={{
                          width: `${r.confidence_pct}%`,
                          background: r.confidence > 0.7 ? 'var(--accent-red)' : r.confidence > 0.4 ? 'var(--accent-yellow)' : 'var(--accent-blue)',
                        }}
                      />
                    </div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="alert alert-warning mt-2" style={{ fontSize: '0.83rem' }}>
        ⚠️ The adversary guesses keywords using <em>only encrypted trapdoor frequencies</em> — no plaintext is seen.
      </div>
    </div>
  );
}

// --- Step 6 ---
function Step6({ step }) {
  return (
    <div>
      <p style={{ marginBottom: '0.75rem' }}>{step.description}</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {step.strategies.map((s, i) => (
          <div key={i} style={{
            background: s.active ? 'rgba(29,211,176,0.08)' : 'var(--bg-secondary)',
            border: `1px solid ${s.active ? 'var(--accent-teal)' : 'var(--border)'}`,
            borderRadius: 'var(--radius-sm)',
            padding: '0.65rem 0.9rem',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span style={{ fontWeight: 600, fontSize: '0.9rem', color: s.active ? 'var(--accent-teal)' : 'var(--text-primary)' }}>
                {s.name}
              </span>
              {s.active && <span className="badge badge-teal">✓ ACTIVE</span>}
            </div>
            <p style={{ margin: 0, fontSize: '0.82rem' }}>{s.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Main component ---
export default function SixStepsDisplay({ steps, mode }) {
  if (!steps) return null;

  const colors = ['var(--accent-blue)', 'var(--accent-teal)', 'var(--accent-purple)', 'var(--accent-yellow)', 'var(--accent-red)', 'var(--accent-blue)'];

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
        <h3>📋 6-Step Process Breakdown</h3>
        <span className={`badge ${mode === 'before' ? 'badge-red' : 'badge-teal'}`}>
          {mode === 'before' ? '🔴 BEFORE' : '🟢 AFTER'}
        </span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        <StepCard number={1} color={colors[0]} title={steps.step1.title} defaultOpen>
          <Step1 step={steps.step1} />
        </StepCard>
        <StepCard number={2} color={colors[1]} title={steps.step2.title}>
          <Step2 step={steps.step2} />
        </StepCard>
        <StepCard number={3} color={colors[2]} title={steps.step3.title} defaultOpen>
          <Step3 step={steps.step3} />
        </StepCard>
        <StepCard number={4} color={colors[3]} title={steps.step4.title} defaultOpen>
          <Step4 step={steps.step4} />
        </StepCard>
        <StepCard number={5} color={colors[4]} title={steps.step5.title}>
          <Step5 step={steps.step5} />
        </StepCard>
        <StepCard number={6} color={colors[5]} title={steps.step6.title}>
          <Step6 step={steps.step6} />
        </StepCard>
      </div>
    </div>
  );
}
