'use client';

import { useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { uploadAsset } from '@/lib/api';

const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp'];

export default function UploadPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── File handling ─────────────────────────────────────────────
  const handleFile = useCallback((f: File) => {
    setError(null);
    if (!ACCEPTED.includes(f.type)) {
      setError('Unsupported format. Please upload JPEG, PNG, or WEBP.');
      return;
    }
    if (f.size > 20 * 1024 * 1024) {
      setError('File too large. Maximum 20MB.');
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  };

  // ── Submit ────────────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const res = await uploadAsset(file, 'ui');
      router.push(`/result/${res.asset_id}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Upload failed. Is the backend running?');
      setUploading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <main className="page">
      <div className="container" style={{ maxWidth: 680, paddingTop: '60px', paddingBottom: '80px' }}>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ fontSize: '2rem', marginBottom: '12px' }}>Analyze an Asset</h1>
          <p style={{ color: '#8892B0' }}>
            Upload an image to run it through the full CLIP → FAISS → Risk → Decision pipeline.
          </p>
        </div>

        {/* Drop zone */}
        <div
          onClick={() => !file && inputRef.current?.click()}
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          style={{
            border: `2px dashed ${dragging ? '#7C3AED' : file ? 'rgba(124,58,237,0.4)' : 'rgba(255,255,255,0.1)'}`,
            borderRadius: '16px',
            background: dragging
              ? 'rgba(124,58,237,0.08)'
              : file
              ? 'rgba(124,58,237,0.04)'
              : 'rgba(255,255,255,0.02)',
            minHeight: '300px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: file ? 'default' : 'pointer',
            transition: 'all 0.25s',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED.join(',')}
            onChange={onInputChange}
            style={{ display: 'none' }}
          />

          {!file ? (
            /* Empty state */
            <div style={{ textAlign: 'center', padding: '40px 24px' }}>
              <div style={{
                fontSize: '3rem',
                marginBottom: '16px',
                animation: 'float 3s ease-in-out infinite',
                display: 'inline-block',
              }}>
                🖼️
              </div>
              <p style={{ fontSize: '1rem', color: '#F0F2FF', fontWeight: 600, marginBottom: '8px' }}>
                Drop an image here
              </p>
              <p style={{ fontSize: '0.85rem', color: '#8892B0', marginBottom: '20px' }}>
                or click to browse
              </p>
              <span style={{
                padding: '6px 16px',
                borderRadius: '100px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                fontSize: '0.72rem',
                color: '#4A5568',
                letterSpacing: '0.04em',
              }}>
                JPEG · PNG · WEBP &nbsp;|&nbsp; Max 20MB
              </span>
            </div>
          ) : (
            /* Preview state */
            <div style={{ width: '100%', position: 'relative' }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={preview!}
                alt="Preview"
                style={{
                  width: '100%',
                  maxHeight: '380px',
                  objectFit: 'contain',
                  borderRadius: '14px',
                  display: 'block',
                }}
              />
              {/* Remove button */}
              <button
                onClick={e => { e.stopPropagation(); reset(); }}
                style={{
                  position: 'absolute', top: 12, right: 12,
                  width: 32, height: 32,
                  borderRadius: '50%',
                  background: 'rgba(0,0,0,0.6)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: '#fff',
                  cursor: 'pointer',
                  fontSize: '16px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  backdropFilter: 'blur(8px)',
                }}
              >
                ×
              </button>
            </div>
          )}
        </div>

        {/* File info */}
        {file && (
          <div style={{
            marginTop: '16px',
            padding: '12px 16px',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: '10px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <div>
              <p style={{ fontSize: '0.85rem', color: '#F0F2FF', fontWeight: 500, margin: 0 }}>{file.name}</p>
              <p style={{ fontSize: '0.75rem', color: '#8892B0', margin: '2px 0 0' }}>
                {(file.size / 1024 / 1024).toFixed(2)} MB · {file.type}
              </p>
            </div>
            <div style={{
              width: 10, height: 10, borderRadius: '50%',
              background: '#10B981',
              boxShadow: '0 0 8px rgba(16,185,129,0.5)',
            }} />
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{
            marginTop: '16px',
            padding: '12px 16px',
            background: 'rgba(239,68,68,0.1)',
            border: '1px solid rgba(239,68,68,0.25)',
            borderRadius: '10px',
            color: '#EF4444',
            fontSize: '0.85rem',
          }}>
            ⚠ {error}
          </div>
        )}

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={!file || uploading}
          className="btn btn-primary"
          style={{ width: '100%', marginTop: '24px', padding: '16px', fontSize: '1rem', justifyContent: 'center' }}
        >
          {uploading ? (
            <>
              <span style={{ animation: 'spin-slow 1s linear infinite', display: 'inline-block' }}>⟳</span>
              Uploading & Processing…
            </>
          ) : (
            '🔍  Run Analysis'
          )}
        </button>

        {/* Info strip */}
        <div style={{
          marginTop: '24px',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: '12px',
        }}>
          {[
            { icon: '⚡', label: 'Async pipeline', sub: 'Returns instantly' },
            { icon: '🔒', label: 'Deterministic', sub: 'Same input = same output' },
            { icon: '📋', label: 'Audit logged', sub: 'Immutable Firestore record' },
          ].map(i => (
            <div key={i.label} style={{
              padding: '12px',
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: '10px',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '1.2rem', marginBottom: '4px' }}>{i.icon}</div>
              <p style={{ fontSize: '0.75rem', fontWeight: 600, color: '#F0F2FF', margin: '0 0 2px' }}>{i.label}</p>
              <p style={{ fontSize: '0.7rem', color: '#8892B0', margin: 0 }}>{i.sub}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
