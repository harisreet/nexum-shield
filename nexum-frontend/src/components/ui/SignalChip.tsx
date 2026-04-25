'use client';

const SIGNAL_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  block_threshold:  { label: 'Block Threshold', color: '#EF4444', bg: 'rgba(239,68,68,0.12)' },
  near_duplicate:   { label: 'Near Duplicate',  color: '#F97316', bg: 'rgba(249,115,22,0.12)' },
  high_similarity:  { label: 'High Similarity', color: '#F59E0B', bg: 'rgba(245,158,11,0.12)' },
  no_matches:       { label: 'No Matches',       color: '#10B981', bg: 'rgba(16,185,129,0.12)' },
};

const DEFAULT = { label: '', color: '#8892B0', bg: 'rgba(136,146,176,0.12)' };

interface Props { signal: string; }

export default function SignalChip({ signal }: Props) {
  const cfg = SIGNAL_CONFIG[signal] ?? { ...DEFAULT, label: signal.replace(/_/g, ' ') };

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '5px',
      padding: '3px 10px',
      borderRadius: '100px',
      background: cfg.bg,
      border: `1px solid ${cfg.color}44`,
      fontSize: '0.72rem',
      fontWeight: 600,
      letterSpacing: '0.04em',
      color: cfg.color,
      textTransform: 'uppercase',
    }}>
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: cfg.color, flexShrink: 0 }} />
      {cfg.label}
    </span>
  );
}
