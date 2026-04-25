# NEXUM SHIELD — Implementation Plan (v3, Event-Driven GCP)

## Overview

**NEXUM SHIELD** is a zero-cost, event-driven media integrity platform deployed on GCP free tier.

A user uploads an image → Ingestion API stores it in GCS and fires a Pub/Sub event → Worker processes it through the 6-stage AI pipeline (CLIP → FAISS → Risk → Decision → Explanation) → Results land in Firestore → Next.js dashboard polls and displays results.

```
User
 └─ POST /upload
       │
       ▼
[Ingestion API — Cloud Run]
  ├─ Store image → Cloud Storage
  └─ Publish event → Pub/Sub topic: "media-events"
                           │
                    (Push subscription)
                           │
                           ▼
              [Worker — Cloud Run]
               ├─ Preprocess image
               ├─ CLIP Embedding
               ├─ FAISS Search  ← index from GCS
               ├─ Risk Engine
               ├─ Decision Engine
               └─ Write results → Firestore
                                       │
                                       ▼
                           [Next.js Dashboard]
                            ├─ /upload
                            ├─ /result/[assetId]
                            └─ /audit
```

---

## User Review Required

> [!IMPORTANT]
> **GCP Project Required**: You need a GCP project with billing enabled (even for free tier, billing account is mandatory). Services: Cloud Run, Cloud Storage, Pub/Sub, Firestore. All stay within Always Free limits for hackathon usage.

> [!IMPORTANT]
> **FAISS Index Strategy**: The FAISS index lives in Cloud Storage and is downloaded by the Worker at cold-start. For MVP, the index is small (~10–100MB). Worker caches it in `/tmp` (Cloud Run ephemeral disk). Index is rebuilt/re-uploaded by a separate `seed` admin endpoint.

> [!WARNING]
> **Cloud Run Memory**: CLIP ViT-B/32 loads ~350MB into RAM. Worker service needs `--memory 2Gi`. The Always Free tier gives 360,000 GiB-seconds/month. At 2Gi x ~100 requests x ~5s each = 1,000 GiB-seconds — well within free tier for hackathon use.

> [!WARNING]
> **Push vs Pull Pub/Sub**: We use **Push subscriptions** (Pub/Sub POSTs directly to Worker's `/process` endpoint). This is the Cloud Run-native pattern — no always-on polling process, scales to zero between requests, costs nothing when idle.

> [!NOTE]
> **No Gemini API**: Per constraints, no paid APIs. Explanation engine uses a deterministic rule-based template — auditable, reproducible, zero cost.

> [!NOTE]
> **Local Development**: The entire stack runs locally via Docker Compose using **Pub/Sub emulator**, **Firestore emulator**, and a **GCS emulator (fake-gcs-server)**. No GCP account needed to develop/test.

---

## Architecture — Detailed

### Services

| Service | Type | Purpose |
|---|---|---|
| `nexum-ingestion` | Cloud Run (HTTP) | Accept uploads, store to GCS, publish event |
| `nexum-worker` | Cloud Run (HTTP) | Receive Pub/Sub push, run full pipeline |
| `nexum-frontend` | Vercel / Cloud Run | Next.js UI |

### GCP Resources

| Resource | Usage | Free Limit |
|---|---|---|
| Cloud Storage bucket | Raw image uploads + FAISS index | 5 GB/month |
| Pub/Sub topic `media-events` | Upload events | 10 GB messages/month |
| Pub/Sub push subscription | Triggers worker | Included |
| Firestore (Native mode) | `assets` + `decisions` collections | 1 GiB + 50K reads/day |
| Artifact Registry | Docker images for both services | 0.5 GB free |
| Cloud Run (2 services) | Ingestion + Worker | 2M req + 180K vCPU-sec/month |

---

## Proposed Changes

### Infrastructure

#### [NEW] `infra/setup.sh`
One-shot GCP setup script:
```bash
gcloud pubsub topics create media-events
gcloud pubsub subscriptions create media-worker-sub \
  --topic media-events \
  --push-endpoint https://WORKER_URL/process \
  --push-auth-service-account nexum-worker@PROJECT.iam.gserviceaccount.com

gcloud storage buckets create gs://nexum-assets --location=us-central1
gcloud firestore databases create --location=us-central1
```

#### [NEW] `docker-compose.yml`
Local dev stack:
- `fake-gcs-server` — GCS emulator on port 4443
- `pubsub-emulator` — Pub/Sub emulator on port 8085
- `firestore-emulator` — Firestore emulator on port 8080
- `nexum-ingestion` — Ingestion API on port 8001
- `nexum-worker` — Worker on port 8002
- `nexum-frontend` — Next.js on port 3000

---

### Backend — `nexum-backend/`

```
nexum-backend/
├── ingestion/                  ← Service 1: Ingestion API
│   ├── main.py
│   ├── routes/
│   │   ├── upload.py
│   │   └── health.py
│   ├── services/
│   │   ├── gcs.py              ← GCS upload wrapper
│   │   └── pubsub.py           ← Pub/Sub publish wrapper
│   ├── schemas.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── worker/                     ← Service 2: Worker (pipeline)
│   ├── main.py
│   ├── routes/
│   │   ├── process.py          ← Pub/Sub push endpoint
│   │   ├── admin.py            ← seed + stats
│   │   └── health.py
│   ├── engines/
│   │   ├── base.py             ← Engine ABC
│   │   ├── preprocessing/
│   │   │   └── processor.py
│   │   ├── embedding/
│   │   │   └── engine.py       ← CLIP ViT-B/32
│   │   ├── matching/
│   │   │   └── engine.py       ← FAISS IndexFlatIP
│   │   ├── risk/
│   │   │   └── engine.py       ← Deterministic scoring
│   │   ├── decision/
│   │   │   └── engine.py       ← Policy table
│   │   └── explainability/
│   │       └── engine.py       ← Rule-based template
│   ├── services/
│   │   ├── gcs.py              ← GCS download wrapper
│   │   └── firestore.py        ← Firestore write wrapper
│   ├── pipeline.py             ← Orchestrates all engines
│   ├── config.py               ← Centralized config
│   ├── schemas.py
│   ├── Dockerfile
│   └── requirements.txt
│
└── shared/                     ← Shared schemas/types
    └── models.py
```

---

#### Ingestion API — Key Details

**`POST /upload`**
```
Input:  multipart/form-data { file, source? }
Action: validate → upload GCS → publish Pub/Sub → return asset_id
Output: { asset_id, trace_id, status: "processing" }
```

**Pub/Sub message payload:**
```json
{
  "trace_id": "uuid",
  "asset_id": "uuid",
  "gcs_path": "gs://nexum-assets/uploads/uuid.jpg",
  "source": "api",
  "timestamp": "ISO8601"
}
```

---

#### Worker — Engine Pipeline

**`POST /process`** (Pub/Sub push endpoint)
```
1. Decode Pub/Sub message
2. Download image from GCS → /tmp
3. PreprocessingEngine    → { image_tensor, phash }
4. EmbeddingEngine        → { vector[512], model_version }
5. MatchingEngine         → { candidates: [{id, score}] }
6. RiskEngine             → { risk_score, signals }
7. DecisionEngine         → { decision, policy_version }
8. ExplainabilityEngine   → { explanation }
9. Write to Firestore     → assets/{asset_id}, decisions/{trace_id}
10. Return 200 OK (ACKs Pub/Sub message)
```

**Engine Contracts (LOCKED):**

| Engine | Input | Output |
|---|---|---|
| Preprocessing | `{ gcs_path, phash_check }` | `{ tensor, phash, width, height }` |
| Embedding | `{ tensor }` | `{ vector: float[512], model: str, version: str }` |
| Matching | `{ vector }` | `{ candidates: [{id, score}], index_version }` |
| Risk | `{ candidates }` | `{ risk_score: float, signals: str[] }` |
| Decision | `{ risk_score }` | `{ decision: ALLOW\|REVIEW\|BLOCK, policy_version }` |
| Explainability | `{ risk_score, signals, candidates }` | `{ explanation: str }` |

**Risk Engine (HARD RULE):**
```python
risk_score = max(c["score"] for c in candidates) if candidates else 0.0
```

**Decision Engine (POLICY TABLE):**
```
risk_score >= 0.90          → BLOCK
0.85 <= risk_score < 0.90   → REVIEW  (uncertainty guard)
0.70 <= risk_score < 0.85   → REVIEW
risk_score < 0.70           → ALLOW
```

---

#### Firestore Schema

**Collection: `assets`**
```
assets/{asset_id}
  ├─ asset_id: str
  ├─ trace_id: str
  ├─ gcs_path: str
  ├─ phash: str
  ├─ source: str
  ├─ status: "processing" | "complete" | "error"
  └─ created_at: timestamp
```

**Collection: `decisions`**
```
decisions/{trace_id}
  ├─ trace_id: str
  ├─ asset_id: str
  ├─ risk_score: float
  ├─ decision: "ALLOW" | "REVIEW" | "BLOCK"
  ├─ signals: str[]
  ├─ explanation: str
  ├─ matches: [{id, score}]
  ├─ model_version: str
  ├─ index_version: str
  ├─ policy_version: str
  └─ created_at: timestamp
```

**Collection: `known_assets`** (the reference dataset)
```
known_assets/{id}
  ├─ id: str
  ├─ name: str
  ├─ gcs_path: str
  ├─ faiss_index: int   ← internal FAISS ID
  └─ created_at: timestamp
```

---

#### FAISS Index Management

- Index file: `gs://nexum-assets/index/faiss.index`
- ID map file: `gs://nexum-assets/index/id_map.json` (FAISS int ID → asset UUID)
- Worker downloads index at cold-start INTO `/tmp/faiss.index`
- `GET /admin/index-stats` — returns index size and version
- `POST /admin/seed` — accepts image, adds to FAISS + GCS + Firestore, re-uploads index

---

### Frontend — `nexum-frontend/`

Next.js 14 App Router, TypeScript, dark-mode glassmorphism.

```
nexum-frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx              ← Landing / Hero
│   │   ├── upload/page.tsx       ← Drag & drop upload
│   │   ├── result/
│   │   │   └── [assetId]/
│   │   │       └── page.tsx      ← Result + polling
│   │   └── audit/page.tsx        ← Decision log table
│   ├── components/
│   │   ├── ui/
│   │   │   ├── DecisionBadge.tsx
│   │   │   ├── RiskGauge.tsx
│   │   │   ├── MatchCard.tsx
│   │   │   ├── SignalChip.tsx
│   │   │   ├── StatusPulse.tsx   ← "Processing..." animation
│   │   │   └── TraceIdBadge.tsx
│   │   └── layout/
│   │       ├── Navbar.tsx
│   │       └── PageWrapper.tsx
│   ├── lib/
│   │   ├── api.ts                ← API client (Ingestion + Worker)
│   │   └── firestore.ts          ← Direct Firestore reads (optional)
│   └── types/
│       └── nexum.ts              ← Shared TS types
├── public/
│   └── nexum-logo.svg
└── next.config.ts
```

**`/upload` Flow:**
1. User drags image → preview shown
2. POST to Ingestion API → get `{ asset_id, trace_id, status: "processing" }`
3. Redirect to `/result/[asset_id]`
4. Page polls `GET /result?asset_id=...` every 2s
5. When `status === "complete"` — animate in the full decision card

**Design System:**
- Background: `#080B14` (deep dark navy)
- Primary accent: `#7C3AED` (violet)
- ALLOW color: `#10B981` (emerald)
- REVIEW color: `#F59E0B` (amber)
- BLOCK color: `#EF4444` (red)
- Font: `Inter` + `JetBrains Mono` (for IDs/scores)
- Cards: `rgba(255,255,255,0.04)` + `border: 1px solid rgba(255,255,255,0.08)`
- Animations: Framer Motion page transitions, gauge fill animation, result reveal

---

## Build Order (STRICT)

```
Phase 0: Infra + Local Dev
  [ ] docker-compose.yml with all emulators
  [ ] GCP setup script (infra/setup.sh)

Phase 1: Worker Service (core pipeline)
  [ ] config.py
  [ ] engines/base.py (Engine ABC)
  [ ] engines/preprocessing/processor.py  + test
  [ ] engines/embedding/engine.py          + test
  [ ] engines/matching/engine.py           + test
  [ ] engines/risk/engine.py               + test
  [ ] engines/decision/engine.py           + test
  [ ] engines/explainability/engine.py     + test
  [ ] pipeline.py (orchestrator)
  [ ] services/gcs.py + services/firestore.py
  [ ] routes/process.py (Pub/Sub push handler)
  [ ] routes/admin.py (seed + stats)
  [ ] main.py
  [ ] Dockerfile

Phase 2: Ingestion API
  [ ] routes/upload.py
  [ ] services/gcs.py + services/pubsub.py
  [ ] main.py
  [ ] Dockerfile

Phase 3: Integration Test (local Docker Compose)
  [ ] Upload image → verify Firestore decision created

Phase 4: Frontend
  [ ] Design system + layout
  [ ] Landing page
  [ ] Upload page
  [ ] Result page (with polling)
  [ ] Audit log page

Phase 5: GCP Deployment
  [ ] Build + push Docker images to Artifact Registry
  [ ] Deploy nexum-ingestion to Cloud Run
  [ ] Deploy nexum-worker to Cloud Run
  [ ] Configure Pub/Sub push subscription
  [ ] Deploy frontend to Vercel or Cloud Run
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Ingestion API | FastAPI + Uvicorn (Cloud Run) |
| Worker | FastAPI + Uvicorn (Cloud Run) |
| Embeddings | HuggingFace `transformers` (CLIP ViT-B/32) + PyTorch |
| Vector search | `faiss-cpu` |
| Perceptual hash | `imagehash` (dedup) |
| Event bus | Google Cloud Pub/Sub |
| Object storage | Google Cloud Storage |
| Database | Google Cloud Firestore (Native) |
| Frontend | Next.js 14 (App Router) + TypeScript |
| Animations | Framer Motion |
| HTTP client | Axios |
| Containerization | Docker + Docker Compose |
| Local emulators | `fake-gcs-server`, `gcloud beta emulators pubsub`, `gcloud beta emulators firestore` |

---

## GCP Free Tier Risk Analysis

| Metric | MVP Usage (hackathon) | Free Limit | Status |
|---|---|---|---|
| Cloud Run requests | ~500 | 2,000,000/month | ✅ Safe |
| Cloud Run memory (2Gi @ 5s) | ~5,000 GiB-sec | 360,000 GiB-sec | ✅ Safe |
| Cloud Storage | ~100MB | 5 GB | ✅ Safe |
| Pub/Sub messages | ~500 × 1KB | 10 GB | ✅ Safe |
| Firestore reads | ~2,000 | 50,000/day | ✅ Safe |
| Firestore writes | ~500 | 20,000/day | ✅ Safe |

---

## Verification Plan

### Unit Tests (per engine)
```bash
cd nexum-backend/worker
pytest tests/ -v --cov=engines
```

### Integration Test (local emulators)
```bash
docker compose up -d
curl -X POST http://localhost:8001/upload \
  -F "file=@test.jpg" | jq .
# → { asset_id, trace_id, status: "processing" }

# Poll until complete:
curl http://localhost:8001/result?asset_id=UUID | jq .
# → { decision, risk_score, signals, explanation, matches }
```

### Frontend Test
- Upload a near-duplicate → see BLOCK badge, high risk gauge
- Upload unrelated image → see ALLOW badge, low score
- Check `/audit` page → all decisions listed with trace IDs

### GCP Smoke Test (post-deploy)
- POST to ingestion Cloud Run URL
- Watch Worker Cloud Run logs for pipeline execution
- Check Firestore console for decision document
