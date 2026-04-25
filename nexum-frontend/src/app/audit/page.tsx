'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { listDecisions } from '@/lib/api';
import type { AuditDecision, Decision } from '@/types/nexum';
import DecisionBadge from '@/components/ui/DecisionBadge';
import SignalChip from '@/components/ui/SignalChip';

export default function AuditPage() {
  const [decisions, setDecisions] = useState<AuditDecision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'ALL' | Decision>('ALL');
  const [search, setSearch] = useState('');

  useEffect(() => {
    listDecisions(100)
      .then(setDecisions)
      .catch(e => setError(e?.response?.data?.detail || 'Could not load audit log.'))
      .finally(() => setLoading(false));
  }, []);

  const filtered = decisions.filter(d => {
    const matchDecision = filter === 'ALL' || d.decision === filter;
    const matchSearch = !search ||
      d.trace_id.includes(search) ||
      d.asset_id.includes(search) ||
      d.decision.includes(search.toUpperCase());
    return matchDecision && matchSearch;
  });

  const counts = {
    ALL:    decisions.length,
    ALLOW:  decisions.filter(d => d.decision === 'ALLOW').length,
    REVIEW: decisions.filter(d => d.decision === 'REVIEW').length,
    BLOCK:  decisions.filter(d => d.decision === 'BLOCK').length,
  };

  return (
    <main className="page">
      <div className="container" style={{ paddingTop: '48px', paddingBottom: '80px' }}>

        {/* Header */}
        <div style={{ marginBottom: '32px' }}>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '8px' }}>Audit Log</h1>
          <p style={{ color: '#8892B0', fontSize: '0.9rem' }}>
            Immutable decision record. Every entry is append-only and reproducible.
          </p>
        </div>

        {/* Stats strip */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '24px' }}>
          {([['ALL', '#7C3AED', 'rgba(124,58,237,0.15)'], ['ALLOW', '#10B981', 'rgba(16,185,129,0.12)'], ['REVIEW', '#F59E0B', 'rgba(245,158,11,0.12)'], ['BLOCK', '#EF4444', 'rgba(239,68,68,0.12)']] as const).map(([key, color, bg]) => (
            <button
              key={key}
              onClick={() => setFilter(key as typeof filter)}
              style={{
                padding: '16px',
                background: filter === key ? bg : 'rgba(255,255,255,0.02)',
                border: `1px solid ${filter === key ? color + '44' : 'rgba(255,255,255,0.07)'}`,
                borderRadius: '12px',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.2s',
              }}
            >
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color, fontFamily: "'JetBrains Mono', monospace" }}>
                {counts[key as keyof typeof counts]}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#8892B0', textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: '4px' }}>
                {key}
              </div>
            </button>
          ))}
        </div>

        {/* Search + filter bar */}
        <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
          <input
            type="text"
            placeholder="Search by trace ID or asset ID…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ flex: 1 }}
          />
        </div>

        {/* Table */}
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="skeleton" style={{ height: '62px', borderRadius: '10px' }} />
            ))}
          </div>
        ) : error ? (
          <div className="card" style={{ textAlign: 'center', padding: '48px', borderColor: 'rgba(239,68,68,0.25)' }}>
            <p style={{ color: '#EF4444' }}>⚠ {error}</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '64px' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '16px' }}>📭</div>
            <h3 style={{ marginBottom: '8px' }}>No decisions found</h3>
            <p style={{ color: '#8892B0', marginBottom: '24px' }}>
              {decisions.length === 0
                ? 'Upload an image to run your first analysis.'
                : 'No results match your current filter.'}
            </p>
            <Link href="/upload" className="btn btn-primary" style={{ display: 'inline-flex' }}>
              Analyze an Asset
            </Link>
          </div>
        ) : (
          <>
            <div style={{
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: '14px',
              overflow: 'hidden',
            }}>
              {/* Table header */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: '90px 1fr 1fr 100px 80px',
                padding: '12px 20px',
                background: 'rgba(255,255,255,0.03)',
                borderBottom: '1px solid rgba(255,255,255,0.06)',
                gap: '16px',
              }}>
                {['Decision', 'Trace ID', 'Signals', 'Risk', 'Time'].map(h => (
                  <span key={h} style={{ fontSize: '0.7rem', color: '#4A5568', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    {h}
                  </span>
                ))}
              </div>

              {/* Rows */}
              {filtered.map((d, idx) => (
                <div
                  key={d.trace_id}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '90px 1fr 1fr 100px 80px',
                    padding: '14px 20px',
                    gap: '16px',
                    alignItems: 'center',
                    borderBottom: idx < filtered.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.02)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <DecisionBadge decision={d.decision} size="sm" />

                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.75rem', color: '#8892B0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {d.trace_id?.slice(0, 24)}…
                  </span>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                    {(d.signals || []).slice(0, 2).map(s => <SignalChip key={s} signal={s} />)}
                    {(d.signals || []).length === 0 && <span style={{ fontSize: '0.75rem', color: '#4A5568' }}>—</span>}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <div style={{
                      height: '4px',
                      width: '48px',
                      background: 'rgba(255,255,255,0.06)',
                      borderRadius: '2px',
                      overflow: 'hidden',
                    }}>
                      <div style={{
                        height: '100%',
                        width: `${(d.risk_score ?? 0) * 100}%`,
                        background: d.risk_score >= 0.9 ? '#EF4444' : d.risk_score >= 0.7 ? '#F59E0B' : '#10B981',
                        borderRadius: '2px',
                      }} />
                    </div>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.75rem', color: '#8892B0' }}>
                      {((d.risk_score ?? 0) * 100).toFixed(0)}%
                    </span>
                  </div>

                  <span style={{ fontSize: '0.72rem', color: '#4A5568' }}>
                    {d.created_at ? new Date(d.created_at).toLocaleTimeString() : '—'}
                  </span>
                </div>
              ))}
            </div>

            <p style={{ fontSize: '0.75rem', color: '#4A5568', marginTop: '12px', textAlign: 'right' }}>
              Showing {filtered.length} of {decisions.length} records
            </p>
          </>
        )}
      </div>
    </main>
  );
}
