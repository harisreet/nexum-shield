import type { Metadata } from 'next';
import './globals.css';
import Navbar from '@/components/layout/Navbar';

export const metadata: Metadata = {
  title: 'NEXUM SHIELD — Media Integrity Platform',
  description:
    'Deterministic, auditable AI system for detecting unauthorized media using embeddings, similarity search, and risk-based decisions.',
  keywords: ['media integrity', 'CLIP', 'FAISS', 'AI', 'copyright detection'],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        {children}
      </body>
    </html>
  );
}
