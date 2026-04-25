/**
 * NEXUM SHIELD — API Client
 * All HTTP calls go through here. No fetch() scattered in components.
 */
import axios from 'axios';
import type { UploadResponse, PollResponse, AuditDecision, IndexStats } from '@/types/nexum';

const INGESTION_URL = process.env.NEXT_PUBLIC_INGESTION_API_URL || 'http://localhost:8001';
const WORKER_URL = process.env.NEXT_PUBLIC_WORKER_API_URL || 'http://localhost:8002';

const ingestion = axios.create({ baseURL: INGESTION_URL });
const worker = axios.create({ baseURL: WORKER_URL });

// ─── Upload ──────────────────────────────────────────────────────

export async function uploadAsset(
  file: File,
  source: string = 'ui'
): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  form.append('source', source);

  const { data } = await ingestion.post<UploadResponse>('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

// ─── Poll for result ─────────────────────────────────────────────

export async function pollResult(assetId: string): Promise<PollResponse> {
  const { data } = await worker.get<PollResponse>('/admin/result', {
    params: { asset_id: assetId },
  });
  return data;
}

// ─── Audit log ───────────────────────────────────────────────────

export async function listDecisions(limit = 50): Promise<AuditDecision[]> {
  const { data } = await worker.get<{ decisions: AuditDecision[]; count: number }>(
    '/admin/decisions',
    { params: { limit } }
  );
  return data.decisions;
}

// ─── Index stats ─────────────────────────────────────────────────

export async function getIndexStats(): Promise<IndexStats> {
  const { data } = await worker.get<IndexStats>('/admin/index-stats');
  return data;
}

// ─── Seed asset ──────────────────────────────────────────────────

export async function seedAsset(file: File, name?: string): Promise<{ asset_id: string; message: string }> {
  const form = new FormData();
  form.append('file', file);
  const params = name ? `?name=${encodeURIComponent(name)}` : '';
  const { data } = await worker.post(`/admin/seed${params}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}
