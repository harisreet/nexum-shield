'use client';

import { useEffect, useState } from 'react';

interface Props {
  score: number;  // 0.0 – 1.0
  size?: number;
}

function getColor(score: number) {
  if (score >= 0.90) return '#EF4444';
  if (score >= 0.70) return '#F59E0B';
  return '#10B981';
}

export default function RiskGauge({ score, size = 140 }: Props) {
  const [animated, setAnimated] = useState(0);

  useEffect(() => {
    let frame: number;
    let start: number | null = null;
    const duration = 900;
    const target = score;

    function step(ts: number) {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      // ease-out-cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimated(eased * target);
      if (progress < 1) frame = requestAnimationFrame(step);
    }
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [score]);

  const color = getColor(score);
  const cx = size / 2;
  const cy = size / 2;
  const radius = (size / 2) - 14;
  const strokeWidth = 10;

  // Arc: 220° sweep from 160° to 380° (bottom-left to bottom-right)
  const startAngle = 160;
  const totalAngle = 220;
  const currentAngle = startAngle + totalAngle * animated;

  function polarToXY(angleDeg: number, r: number) {
    const rad = (angleDeg * Math.PI) / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
  }

  const start = polarToXY(startAngle, radius);
  const end   = polarToXY(currentAngle, radius);
  const full  = polarToXY(startAngle + totalAngle, radius);
  const largeArc = currentAngle - startAngle > 180 ? 1 : 0;
  const fullLargeArc = totalAngle > 180 ? 1 : 0;

  const trackPath = [
    `M ${start.x} ${start.y}`,
    `A ${radius} ${radius} 0 ${fullLargeArc} 1 ${full.x} ${full.y}`,
  ].join(' ');

  const fillPath = animated > 0.001 ? [
    `M ${start.x} ${start.y}`,
    `A ${radius} ${radius} 0 ${largeArc} 1 ${end.x} ${end.y}`,
  ].join(' ') : '';

  return (
    <div style={{ textAlign: 'center', userSelect: 'none' }}>
      <svg width={size} height={size} style={{ overflow: 'visible' }}>
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Track */}
        <path
          d={trackPath}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Filled arc */}
        {fillPath && (
          <path
            d={fillPath}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            filter="url(#glow)"
            style={{ transition: 'stroke 0.4s' }}
          />
        )}

        {/* Score text */}
        <text
          x={cx} y={cy - 4}
          textAnchor="middle"
          fill={color}
          fontSize={size * 0.2}
          fontWeight="800"
          fontFamily="'JetBrains Mono', monospace"
          style={{ transition: 'fill 0.4s' }}
        >
          {(animated * 100).toFixed(0)}%
        </text>
        <text
          x={cx} y={cy + size * 0.12}
          textAnchor="middle"
          fill="rgba(255,255,255,0.35)"
          fontSize={size * 0.1}
          fontFamily="Inter, sans-serif"
          fontWeight="500"
        >
          RISK SCORE
        </text>

        {/* Min / Max labels */}
        <text x={start.x - 4} y={start.y + 16} fill="rgba(255,255,255,0.25)" fontSize="10" fontFamily="Inter">0%</text>
        <text x={full.x - 24} y={full.y + 16}  fill="rgba(255,255,255,0.25)" fontSize="10" fontFamily="Inter">100%</text>
      </svg>
    </div>
  );
}
