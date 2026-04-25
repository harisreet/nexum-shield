'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_LINKS = [
  { href: '/',         label: 'Home'      },
  { href: '/upload',   label: 'Analyze'   },
  { href: '/audit',    label: 'Audit Log' },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav style={{
      position: 'fixed',
      top: 0, left: 0, right: 0,
      height: '64px',
      zIndex: 100,
      background: 'rgba(8, 11, 20, 0.85)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid rgba(255,255,255,0.06)',
      display: 'flex',
      alignItems: 'center',
      padding: '0 32px',
      justifyContent: 'space-between',
    }}>
      {/* Logo */}
      <Link href="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{
          width: 32, height: 32,
          background: 'linear-gradient(135deg, #7C3AED, #5B21B6)',
          borderRadius: '8px',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 0 16px rgba(124,58,237,0.5)',
          fontSize: '16px',
        }}>
          🛡
        </div>
        <span style={{
          fontWeight: 800,
          fontSize: '1rem',
          letterSpacing: '0.05em',
          color: '#F0F2FF',
        }}>
          NEXUM <span style={{ color: '#7C3AED' }}>SHIELD</span>
        </span>
      </Link>

      {/* Nav links */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        {NAV_LINKS.map(({ href, label }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              style={{
                padding: '6px 16px',
                borderRadius: '8px',
                textDecoration: 'none',
                fontSize: '0.875rem',
                fontWeight: active ? 600 : 400,
                color: active ? '#F0F2FF' : '#8892B0',
                background: active ? 'rgba(124,58,237,0.15)' : 'transparent',
                border: active ? '1px solid rgba(124,58,237,0.3)' : '1px solid transparent',
                transition: 'all 0.2s',
              }}
            >
              {label}
            </Link>
          );
        })}
      </div>

      {/* Status dot */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{
          width: 8, height: 8,
          borderRadius: '50%',
          background: '#10B981',
          boxShadow: '0 0 8px rgba(16,185,129,0.6)',
        }} />
        <span style={{ fontSize: '0.75rem', color: '#8892B0' }}>System Online</span>
      </div>
    </nav>
  );
}
