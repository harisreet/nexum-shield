'use client';

export default function StatusPulse({ label = 'Processing' }: { label?: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
      <div style={{ position: 'relative', width: 16, height: 16 }}>
        <div style={{
          position: 'absolute',
          inset: 0,
          borderRadius: '50%',
          background: '#7C3AED',
          opacity: 0.7,
          animation: 'pulse-ring 1.4s ease-out infinite',
        }} />
        <div style={{
          position: 'absolute',
          inset: '3px',
          borderRadius: '50%',
          background: '#7C3AED',
        }} />
      </div>
      <span style={{ color: '#8892B0', fontSize: '0.9rem' }}>{label}</span>
    </div>
  );
}
