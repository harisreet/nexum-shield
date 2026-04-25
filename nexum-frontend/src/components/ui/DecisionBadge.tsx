'use client';

import type { Decision } from '@/types/nexum';

const CONFIG: Record<Decision, { label: string; color: string; bg: string; border: string; icon: string; glow: string }> = {
  ALLOW:  { label: 'ALLOW',  color: '#10B981', bg: 'rgba(16,185,129,0.12)',  border: 'rgba(16,185,129,0.3)',  icon: '✓', glow: 'rgba(16,185,129,0.25)'  },
  REVIEW: { label: 'REVIEW', color: '#F59E0B', bg: 'rgba(245,158,11,0.12)',  border: 'rgba(245,158,11,0.3)',  icon: '!', glow: 'rgba(245,158,11,0.25)'  },
  BLOCK:  { label: 'BLOCK',  color: '#EF4444', bg: 'rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.3)',   icon: '✕', glow: 'rgba(239,68,68,0.25)'   },
};

interface Props {
  decision: Decision;
  size?: 'sm' | 'md' | 'lg';
}

export default function DecisionBadge({ decision, size = 'md' }: Props) {
  const c = CONFIG[decision];

  const padding  = size === 'sm' ? '3px 10px' : size === 'lg' ? '10px 24px' : '5px 16px';
  const fontSize = size === 'sm' ? '0.7rem'   : size === 'lg' ? '1rem'      : '0.8rem';
  const iconSize = size === 'sm' ? '14px'     : size === 'lg' ? '22px'      : '18px';

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: size === 'lg' ? '10px' : '6px',
      padding,
      borderRadius: '100px',
      background: c.bg,
      border: `1px solid ${c.border}`,
      boxShadow: `0 0 16px ${c.glow}`,
      fontFamily: "'JetBrains Mono', monospace",
      fontSize,
      fontWeight: 700,
      letterSpacing: '0.08em',
      color: c.color,
      userSelect: 'none',
    }}>
      <div style={{
        width: iconSize,
        height: iconSize,
        borderRadius: '50%',
        background: c.color,
        color: '#fff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: size === 'lg' ? '13px' : '11px',
        fontWeight: 900,
        flexShrink: 0,
      }}>
        {c.icon}
      </div>
      {c.label}
    </div>
  );
}
