'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { pollResult } from '@/lib/api';
import type { PollResponse } from '@/types/nexum';
import DecisionBadge from '@/components/ui/DecisionBadge';
import RiskGauge from '@/components/ui/RiskGauge';
import MatchCard from '@/components/ui/MatchCard';
import SignalChip from '@/components/ui/SignalChip';
import StatusPulse from '@/components/ui/StatusPulse';

const POLL_INTERVAL = 2500;
const MAX_POLLS = 60; // 2.5s × 60 = 2.5 min timeout

export default function ResultPage() {
  const { assetId } = useParams<{ assetId: string }>();
  const [result, setResult] = useState<PollResponse | null>(null);
  const [polls, setPolls] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const poll = useCallback(async () => {
    try {
      const data = await pollResult(assetId);
      setResult(data);
      return data.status === 'complete' || data.status === 'error';
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Could not reach worker service.');
      return true;
    }
  }, [assetId]);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    let count = 0;

    const run = async () => {
      const done = await poll();
      count++;
      setPolls(count);
      if (!done && count < MAX_POLLS) {
        timer = setTimeout(run, POLL_INTERVAL);
      } else if (count >= MAX_POLLS) {
        setError('Processing timeout. Try refreshing the page.');
      }
    };

    run();
    return () => clearTimeout(timer);
  }, [poll]);

  const copyTrace = () => {
    if (!result?.trace_id) return;
    navigator.clipboard.writeText(result.trace_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isComplete = result?.status === 'complete';

  return (
    <main className="page">
      <div className="container" style={{ maxWidth: 860, paddingTop: '48px', paddingBottom: '80px' }}>

        {/* Back */}
        <Link href="/upload" style={{
          display: 'inline-flex', alignItems: 'center', gap: '6px',
          color: '#8892B0', textDecoration: 'none', fontSize: '0.85rem',
          marginBottom: '32px',
          transition: 'color 0.2s',
        }}>
          ← Back to Upload
        </Link>

        {/* Processing state */}
        {!isComplete && !error && (
          <div className="card" style={{ textAlign: 'center', padding: '64px 32px' }}>
            <StatusPulse label={`Running analysis pipeline… (${polls} checks)`} />
            <p style={{ marginTop: '24px', color: '#8892B0', fontSize: '0.85rem' }}>
              Preprocessing → Embedding → Matching → Risk → Decision → Explanation
            </p>
            <div style={{
              marginTop: '32px',
              display: 'flex', flexDirection: 'column', gap: '8px',
              maxWidth: 320, margin: '32px auto 0',
            }}>
              {['Preprocessing', 'CLIP Embedding', 'FAISS Matching', 'Risk Scoring', 'Decision', 'Explainability'].map((step, i) => (
                <div key={step} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{
                    width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                    background: polls > i * 3 ? '#10B981' : polls > i * 2 ? '#7C3AED' : 'rgba(255,255,255,0.1)',
                    boxShadow: polls > i * 3 ? '0 0 6px #10B981' : polls > i * 2 ? '0 0 6px #7C3AED' : 'none',
                    transition: 'all 0.5s',
                  }} />
                  <span style={{ fontSize: '0.8rem', color: polls > i * 2 ? '#F0F2FF' : '#4A5568', transition: 'color 0.5s' }}>
                    {step}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="card" style={{
            borderColor: 'rgba(239,68,68,0.3)',
            background: 'rgba(239,68,68,0.05)',
            textAlign: 'center', padding: '48px 32px',
          }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '16px' }}>⚠</div>
            <h2 style={{ color: '#EF4444', marginBottom: '12px' }}>Analysis Failed</h2>
            <p style={{ color: '#8892B0' }}>{error}</p>
            <Link href="/upload" className="btn btn-primary" style={{ marginTop: '24px', display: 'inline-flex' }}>
              Try Again
            </Link>
          </div>
        )}

        {/* Result */}
        {isComplete && result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', animation: 'fadeIn 0.5s ease' }}>

            {/* Decision hero card */}
            <div className="card" style={{
              background: result.decision === 'BLOCK'
                ? 'rgba(239,68,68,0.06)'
                : result.decision === 'REVIEW'
                ? 'rgba(245,158,11,0.06)'
                : 'rgba(16,185,129,0.06)',
              borderColor: result.decision === 'BLOCK'
                ? 'rgba(239,68,68,0.2)'
                : result.decision === 'REVIEW'
                ? 'rgba(245,158,11,0.2)'
                : 'rgba(16,185,129,0.2)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '24px' }}>
                {/* Left: decision + signals */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <DecisionBadge decision={result.decision!} size="lg" />
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {(result.signals || []).map(s => <SignalChip key={s} signal={s} />)}
                    {(result.signals || []).length === 0 && (
                      <SignalChip signal="no_matches" />
                    )}
                  </div>
                </div>
                {/* Right: gauge */}
                <RiskGauge score={result.risk_score ?? 0} size={160} />
              </div>
            </div>

            {/* Two-col: Explanation + Matches */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>

              {/* Explanation */}
              <div className="card">
                <h3 style={{ fontSize: '0.85rem', color: '#8892B0', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Explanation
                </h3>
                <p style={{ fontSize: '0.875rem', lineHeight: 1.7, color: '#C4B5FD' }}>
                  {result.explanation}
                </p>
              </div>

              {/* Matches */}
              <div className="card">
                <h3 style={{ fontSize: '0.85rem', color: '#8892B0', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Top Matches ({result.matches?.length ?? 0})
                </h3>
                {(result.matches || []).length === 0 ? (
                  <p style={{ color: '#4A5568', fontSize: '0.85rem' }}>No reference matches found in index.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {(result.matches || []).map((m, i) => (
                      <MatchCard key={m.id} match={m} rank={i + 1} />
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Metadata */}
            <div className="card">
              <h3 style={{ fontSize: '0.85rem', color: '#8892B0', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Audit Metadata
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
                {[
                  { label: 'Trace ID',        value: result.trace_id?.slice(0,18) + '…', full: result.trace_id, copyable: true },
                  { label: 'Asset ID',         value: assetId.slice(0,18) + '…' },
                  { label: 'Model Version',    value: result.model_version },
                  { label: 'Index Version',    value: result.index_version },
                  { label: 'Policy Version',   value: result.policy_version },
                  { label: 'Risk Score',       value: ((result.risk_score ?? 0) * 100).toFixed(2) + '%' },
                ].map(m => (
                  <div key={m.label}>
                    <p style={{ fontSize: '0.7rem', color: '#4A5568', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                      {m.label}
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.78rem', color: '#C4B5FD' }}>
                        {m.value || '—'}
                      </span>
                      {m.copyable && (
                        <button
                          onClick={copyTrace}
                          style={{
                            background: 'none', border: 'none', cursor: 'pointer',
                            color: copied ? '#10B981' : '#4A5568', fontSize: '0.75rem',
                          }}
                        >
                          {copied ? '✓' : '⎘'}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <Link href="/audit" className="btn btn-secondary">📋 View Audit Log</Link>
              <Link href="/upload" className="btn btn-primary">🔍 Analyze Another</Link>
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:none; } }
      `}</style>
    </main>
  );
}
