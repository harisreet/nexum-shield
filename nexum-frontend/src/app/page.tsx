import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="page">
      {/* Hero */}
      <section style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        padding: '80px 24px 60px',
        position: 'relative',
      }}>
        {/* Glow orbs */}
        <div style={{
          position: 'absolute', top: '20%', left: '50%',
          transform: 'translateX(-50%)',
          width: 600, height: 400,
          background: 'radial-gradient(ellipse, rgba(124,58,237,0.15) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        {/* Status tag */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '8px',
          padding: '6px 16px',
          borderRadius: '100px',
          background: 'rgba(124,58,237,0.1)',
          border: '1px solid rgba(124,58,237,0.25)',
          marginBottom: '32px',
          fontSize: '0.78rem',
          color: '#9F67FF',
          fontWeight: 600,
          letterSpacing: '0.06em',
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10B981', display: 'inline-block', boxShadow: '0 0 6px #10B981' }} />
          MEDIA INTEGRITY PLATFORM — v1.0
        </div>

        {/* Headline */}
        <h1 style={{ maxWidth: '800px', marginBottom: '24px', lineHeight: 1.1 }}>
          Detect Unauthorized Media{' '}
          <span style={{
            background: 'linear-gradient(135deg, #7C3AED, #9F67FF, #C4B5FD)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            with Certainty
          </span>
        </h1>

        <p style={{ maxWidth: '560px', fontSize: '1.1rem', lineHeight: 1.7, marginBottom: '48px', color: '#8892B0' }}>
          A <strong style={{ color: '#C4B5FD' }}>deterministic, auditable</strong> AI decision engine using
          CLIP embeddings and FAISS similarity search.
          Every decision is reproducible, logged, and explainable.
        </p>

        {/* CTAs */}
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', justifyContent: 'center', marginBottom: '80px' }}>
          <Link href="/upload" className="btn btn-primary" style={{ fontSize: '1rem', padding: '14px 32px' }}>
            🔍 Analyze an Asset
          </Link>
          <Link href="/audit" className="btn btn-secondary" style={{ fontSize: '1rem', padding: '14px 32px' }}>
            📋 View Audit Log
          </Link>
        </div>

        {/* Feature cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
          maxWidth: '900px',
          width: '100%',
        }}>
          {FEATURES.map(f => (
            <div key={f.title} className="card" style={{ textAlign: 'left' }}>
              <div style={{ fontSize: '1.8rem', marginBottom: '12px' }}>{f.icon}</div>
              <h3 style={{ fontSize: '0.95rem', marginBottom: '8px' }}>{f.title}</h3>
              <p style={{ fontSize: '0.82rem', lineHeight: 1.6, color: '#8892B0' }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pipeline section */}
      <section style={{ padding: '80px 24px', maxWidth: '900px', margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '12px' }}>Detection Pipeline</h2>
        <p style={{ textAlign: 'center', color: '#8892B0', marginBottom: '48px', fontSize: '0.9rem' }}>
          Six deterministic stages. Every output is verifiable.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {PIPELINE.map((step, i) => (
            <div key={step.name} style={{ display: 'flex', alignItems: 'stretch', gap: '0' }}>
              {/* Connector */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '48px', flexShrink: 0 }}>
                <div style={{
                  width: '36px', height: '36px', borderRadius: '50%',
                  background: 'rgba(124,58,237,0.15)',
                  border: '1px solid rgba(124,58,237,0.35)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.85rem', fontWeight: 700, color: '#9F67FF',
                  flexShrink: 0, marginTop: '12px',
                }}>
                  {i + 1}
                </div>
                {i < PIPELINE.length - 1 && (
                  <div style={{ width: '1px', flex: 1, minHeight: '16px', background: 'rgba(124,58,237,0.2)', margin: '4px 0' }} />
                )}
              </div>
              {/* Content */}
              <div className="card" style={{ flex: 1, marginBottom: '4px', padding: '16px 20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h3 style={{ fontSize: '0.9rem', marginBottom: '4px' }}>{step.name}</h3>
                    <p style={{ fontSize: '0.8rem', color: '#8892B0', margin: 0 }}>{step.desc}</p>
                  </div>
                  <span style={{ fontSize: '0.7rem', fontFamily: 'JetBrains Mono', color: '#4A5568', marginLeft: '16px', flexShrink: 0 }}>
                    {step.output}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture tag */}
      <section style={{ textAlign: 'center', padding: '40px 24px 80px' }}>
        <p style={{ fontSize: '0.8rem', color: '#4A5568', fontFamily: 'JetBrains Mono', maxWidth: '700px', margin: '0 auto', lineHeight: 2 }}>
          Cloud Run → Cloud Storage → Pub/Sub → Worker → CLIP → FAISS → Risk → Decision → Firestore
        </p>
      </section>
    </main>
  );
}

const FEATURES = [
  { icon: '🧠', title: 'CLIP Embeddings',     desc: 'OpenAI ViT-B/32 generates 512-d vectors. Same image always produces the same vector.' },
  { icon: '⚡', title: 'FAISS Search',         desc: 'IndexFlatIP cosine similarity search across your reference dataset in milliseconds.' },
  { icon: '🎯', title: 'Deterministic Risk',   desc: 'risk_score = max(candidates). No randomness. Identical inputs produce identical outputs.' },
  { icon: '📋', title: 'Full Audit Trail',     desc: 'Every decision is immutably logged in Firestore with trace_id, versions, and explanation.' },
  { icon: '🔄', title: 'Event-Driven',         desc: 'Pub/Sub decouples ingestion from analysis. Upload returns instantly; results arrive async.' },
  { icon: '☁️',  title: 'Zero Cost GCP',       desc: 'Cloud Run, Storage, Pub/Sub, Firestore — all within GCP Always Free tier limits.' },
];

const PIPELINE = [
  { name: 'Preprocessing',    desc: 'Validate format, detect corruption, resize to 224×224, compute pHash', output: 'PIL.Image + pHash' },
  { name: 'Embedding',        desc: 'CLIP ViT-B/32 → L2 normalized 512-d float vector', output: 'vector[512]' },
  { name: 'Matching',         desc: 'FAISS IndexFlatIP top-K cosine similarity search', output: 'candidates[]' },
  { name: 'Risk Scoring',     desc: 'risk_score = max(candidate_scores). Signals from threshold crossings', output: 'risk_score, signals' },
  { name: 'Decision',         desc: 'Policy table: ≥0.90 BLOCK, ≥0.70 REVIEW, else ALLOW', output: 'ALLOW|REVIEW|BLOCK' },
  { name: 'Explainability',   desc: 'Rule-based template explanation. Zero hallucination. Fully reproducible', output: 'explanation' },
];
