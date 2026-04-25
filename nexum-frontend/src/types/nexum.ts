/**
 * NEXUM SHIELD — Shared TypeScript types
 * Mirrors the backend DecisionRecord schema exactly.
 */

export type Decision = 'ALLOW' | 'REVIEW' | 'BLOCK';

export interface Candidate {
  id: string;
  score: number;
}

export interface AnalysisResult {
  trace_id: string;
  asset_id: string;
  risk_score: number;
  decision: Decision;
  signals: string[];
  explanation: string;
  matches: Candidate[];
  model_version: string;
  index_version: string;
  policy_version: string;
  created_at: string;
}

export interface UploadResponse {
  asset_id: string;
  trace_id: string;
  status: 'processing';
  message: string;
}

export interface PollResponse {
  status: 'processing' | 'complete' | 'error';
  asset_id: string;
  trace_id?: string;
  risk_score?: number;
  decision?: Decision;
  signals?: string[];
  explanation?: string;
  matches?: Candidate[];
  model_version?: string;
  index_version?: string;
  policy_version?: string;
  created_at?: string;
}

export interface AuditDecision extends AnalysisResult {}

export interface IndexStats {
  total_vectors: number;
  index_version: string;
  model_version: string;
  index_on_disk: boolean;
}
