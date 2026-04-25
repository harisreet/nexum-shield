import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  output: 'standalone',
  env: {
    NEXT_PUBLIC_INGESTION_API_URL: process.env.NEXT_PUBLIC_INGESTION_API_URL || 'http://localhost:8001',
    NEXT_PUBLIC_WORKER_API_URL: process.env.NEXT_PUBLIC_WORKER_API_URL || 'http://localhost:8002',
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
        ],
      },
    ];
  },
};

export default nextConfig;
