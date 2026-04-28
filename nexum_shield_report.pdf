# NEXUM SHIELD — Full Project Report

## Project Overview

**Project Name:** Nexum Shield  
**Category:** AI-Powered Media Integrity Platform  
**Type:** Cloud-Native Web Application (MVP)  
**Repository:** https://github.com/harisreet/nexum-shield  
**Deployment:** Render (Backend) + Vercel/Render (Frontend) + MongoDB Atlas (Database)

---

## Problem Statement

In today's digital landscape, unauthorized reproduction and distribution of copyrighted media assets is a significant problem for content creators, publishers, and enterprises. Manual detection is slow, inconsistent, and unable to scale. Nexum Shield addresses this by providing an automated, real-time media integrity verification platform that can detect near-duplicate or unauthorized copies of protected content using perceptual fingerprinting.

---

## Proposed Solution

Nexum Shield is a decoupled, microservices-based AI platform that:
1. Accepts image uploads through a modern web interface.
2. Computes a perceptual fingerprint (pHash) of the uploaded image in under 10 milliseconds.
3. Compares the fingerprint against a known reference database using Hamming Distance.
4. Produces a deterministic **ALLOW**, **REVIEW**, or **BLOCK** decision based on a configurable policy threshold.
5. Generates a human-readable explanation using the Google Gemini API, with an automatic fallback to a rule-based template if the API is unavailable.

---

## Architecture

The platform follows a **decoupled 3-tier microservices architecture**:

```
[User Browser]
      │
      ▼
[Next.js Frontend — Vercel/Render]
      │  HTTP (via proxy rewrites)
      ▼
[Ingestion API — FastAPI on Render]
      │  HTTP POST (base64 image payload)
      ▼
[Worker Engine — FastAPI on Render]
      │  Reads/Writes
      ▼
[MongoDB Atlas — Free Tier Database]
```

### Why Decoupled?
- The Ingestion API is stateless and handles only upload validation and forwarding. It can scale independently.
- The Worker Engine handles all AI computation and is independently deployable.
- There is no shared filesystem — images are passed as base64 strings in HTTP payloads, eliminating the need for any external cloud storage bucket.

---

## Technology Stack

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| Next.js | 14 | React framework with server-side rendering |
| TypeScript | 5.x | Type-safe JavaScript |
| Axios | 1.x | HTTP client |
| Vanilla CSS | — | Custom design system |

### Backend — Ingestion API
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11 | Runtime |
| FastAPI | 0.115 | Web framework |
| Pydantic | 2.8 | Data validation |
| Uvicorn | 0.30 | ASGI server |
| Requests | 2.32 | HTTP client for Worker calls |

### Backend — Worker Engine
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11 | Runtime |
| FastAPI | 0.115 | Web framework |
| Pillow | 10.4 | Image processing |
| ImageHash | 4.3 | Perceptual hashing (pHash) |
| NumPy | 1.26 | Numerical operations |
| PyMongo | 4.8 | MongoDB client |
| Google GenAI | 0.3 | Gemini API for Explainable AI |

### Infrastructure & Deployment
| Service | Purpose |
|---|---|
| Render | Backend hosting (Ingestion + Worker) |
| Vercel / Render | Frontend hosting |
| MongoDB Atlas | Database (decisions, known assets, pHash index) |
| GitHub | Source control and CI/CD trigger |
| Docker | Containerization (~80MB image) |

---

## AI Engine — How the Pipeline Works

The Worker service runs a **6-stage sequential pipeline** for every uploaded image:

### Stage 1: Preprocessing Engine
- Validates the image file (format, size, corruption check).
- Converts all images to RGB color space for consistency.
- Accepts: JPEG, PNG, WEBP — Max 20MB.

### Stage 2: Embedding Engine (pHash)
- Computes a **Perceptual Hash (pHash)** fingerprint of the image.
- pHash shrinks the image to an 8×8 grayscale grid and converts pixel intensities into a 64-bit binary string (e.g., `a1b2c3d4e5f6...`).
- This fingerprint is structurally stable — cropping, slight color grading, watermarks, and minor edits will not change the hash significantly.
- **Speed:** ~5 milliseconds per image on a standard CPU.
- **Size:** Zero model download required. The entire engine is ~15 lines of Python.

### Stage 3: Matching Engine (Hamming Distance)
- Compares the query pHash against every known reference pHash stored in the database.
- Uses **Hamming Distance** — counts the number of bit positions where the two hashes differ (0 = identical, 64 = completely different).
- A match is reported when the Hamming Distance is ≤ 10 bits (≥ ~84% similar).
- Converts distance to a normalized similarity score: `score = 1.0 - (hamming / 64.0)`

### Stage 4: Risk Engine
- Takes the highest-scoring candidate match.
- `risk_score = max(candidate_scores)` — deterministic, no randomness.
- Appends signals: `high_similarity`, `near_duplicate`, `block_threshold`, `no_matches`.

### Stage 5: Decision Engine (Policy Table)
The policy table is locked at `v1`:

| Condition | Decision |
|---|---|
| `risk_score >= 0.90` | **BLOCK** |
| `0.85 <= risk_score < 0.90` | **REVIEW** (Uncertainty Band) |
| `0.70 <= risk_score < 0.85` | **REVIEW** |
| `risk_score < 0.70` | **ALLOW** |

### Stage 6: Explainability Engine
- **Primary:** Calls the Google Gemini 2.5 Flash API with a structured prompt containing the risk score, signals, and decision.
- **Fallback:** If `GEMINI_API_KEY` is not set, is invalid, or the API quota is exhausted, the engine automatically falls back to a deterministic rule-based text template.
- The pipeline **never crashes** due to an AI API failure.

---

## API Reference

### Ingestion API (`Port 8001`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/upload` | Upload an image for analysis |

**POST /upload — Request:**
```
Content-Type: multipart/form-data
file: <image file>
source: "ui" (optional)
```

**POST /upload — Response:**
```json
{
  "asset_id": "uuid",
  "trace_id": "uuid",
  "status": "processing",
  "message": "Asset received. Processing pipeline started."
}
```

---

### Worker API (`Port 8002`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/process` | Internal: receive and process image event |
| `GET` | `/admin/result?asset_id=` | Poll for decision result |
| `GET` | `/admin/decisions` | Audit log of all decisions |
| `GET` | `/admin/index-stats` | pHash index statistics |
| `POST` | `/admin/seed` | Add a known reference image to the database |

**GET /admin/result — Response:**
```json
{
  "status": "complete",
  "trace_id": "uuid",
  "asset_id": "uuid",
  "risk_score": 0.953125,
  "decision": "BLOCK",
  "signals": ["block_threshold", "near_duplicate", "high_similarity"],
  "explanation": "The submitted asset was flagged...",
  "matches": [{ "id": "asset-uuid", "score": 0.953125 }],
  "model_version": "phash_v1",
  "policy_version": "v1"
}
```

---

## Database Schema

### Collection: `decisions`
| Field | Type | Description |
|---|---|---|
| `trace_id` | String | Unique request ID |
| `asset_id` | String | Unique asset ID |
| `risk_score` | Float | 0.0 to 1.0 |
| `decision` | Enum | `ALLOW`, `REVIEW`, `BLOCK` |
| `signals` | Array | Active risk signals |
| `explanation` | String | Human-readable explanation |
| `matches` | Array | `[{id, score}]` |
| `model_version` | String | `phash_v1` |
| `policy_version` | String | `v1` |
| `created_at` | ISO Datetime | Timestamp |

### Collection: `known_assets`
| Field | Type | Description |
|---|---|---|
| `id` | String | UUID |
| `name` | String | Human-readable label |
| `phash` | String | 64-bit pHash fingerprint |
| `created_at` | ISO Datetime | Timestamp |

---

## Environment Variables

### Worker Service (Render)
| Variable | Required | Description |
|---|---|---|
| `MONGODB_URI` | Yes | MongoDB Atlas connection string |
| `GEMINI_API_KEY` | No | Google Gemini API key for Explainable AI |

### Ingestion Service (Render)
| Variable | Required | Description |
|---|---|---|
| `WORKER_URL` | Yes | Full URL of the deployed Worker service |

### Frontend (Render/Vercel)
| Variable | Required | Description |
|---|---|---|
| `INGESTION_API_URL` | Yes | Full URL of the deployed Ingestion service |
| `WORKER_API_URL` | Yes | Full URL of the deployed Worker service |

> **Note:** The frontend uses Next.js proxy rewrites — all API calls go through `/api/ingestion/*` and `/api/worker/*` on the same origin. This eliminates CORS issues and removes the need for `NEXT_PUBLIC_` environment variables that get baked into the build.

---

## Key Design Decisions

### 1. pHash Instead of Deep Learning
The original design used OpenAI CLIP (ViT-B/32) + FAISS for semantic vector search. This produced a ~3GB Docker container that took over 2 hours to build and required 350MB of model download at every startup.

We replaced this with Perceptual Hashing (`imagehash` library), which:
- Requires zero model downloads.
- Processes images in ~5ms vs ~300ms.
- Shrinks the Docker container to ~80MB.
- Still correctly detects near-duplicate images, crops, and minor edits — which is the core use case.

### 2. In-Memory Image Transport (No Cloud Storage)
Instead of uploading images to a cloud storage bucket and having the Worker download them, the Ingestion API encodes the image as a base64 string and includes it directly in the HTTP payload to the Worker. The Worker decodes it in memory and processes it without touching disk.

This eliminates the need for Google Cloud Storage, AWS S3, or any other object storage service.

### 3. Auto-Detection for Dev vs Production
All service-layer code detects the deployment environment automatically:
- If `MONGODB_URI` is set → use MongoDB Atlas.
- If `MONGODB_URI` is empty → use local JSON files in `C:/tmp/nexum-storage/`.
- If `GEMINI_API_KEY` is set → use Gemini AI for explanations.
- If `GEMINI_API_KEY` is empty or API fails → use rule-based text templates.

This means the entire platform runs on a developer's laptop with zero configuration.

### 4. Graceful Degradation
Every external dependency has a fallback:
- Gemini API failure → rule-based explanation.
- MongoDB failure → local JSON storage.
- Worker timeout → Ingestion API returns a user-friendly error, not a crash.

---

## Performance Characteristics

| Metric | Value |
|---|---|
| Docker image size | ~80 MB |
| Docker build time | ~3 minutes |
| Worker startup time | < 1 second |
| Image processing time | ~10–50 ms |
| End-to-end pipeline latency | ~200–500 ms (including network) |
| Free tier compatibility | ✅ Render, Vercel, MongoDB Atlas |
| Requires GPU | ❌ No |
| Requires model download | ❌ No |

---

## Local Development Guide

### Prerequisites
- Python 3.11+
- Node.js 18+
- No Docker required

### Running Locally

**Terminal 1 — Worker Engine:**
```bash
cd nexum-backend/worker
pip install -r requirements.txt
python main.py
# Running on http://localhost:8002
```

**Terminal 2 — Ingestion API:**
```bash
cd nexum-backend/ingestion
pip install -r requirements.txt
python main.py
# Running on http://localhost:8001
```

**Terminal 3 — Frontend:**
```bash
cd nexum-frontend
npm install
npm run dev
# Running on http://localhost:3000
```

No environment variables are needed for local development. All data is stored in `C:/tmp/nexum-storage/`.

---

## Deployment Guide

### Step 1: Deploy Worker to Render
1. Connect GitHub repo to Render.
2. Create a Web Service with Root Directory: `nexum-backend/worker`.
3. Render auto-detects the `Dockerfile`.
4. Add environment variables: `MONGODB_URI`, `GEMINI_API_KEY`.

### Step 2: Deploy Ingestion API to Render
1. Create another Web Service with Root Directory: `nexum-backend/ingestion`.
2. Add environment variable: `WORKER_URL = <Worker URL from Step 1>`.

### Step 3: Deploy Frontend to Render/Vercel
1. Deploy `nexum-frontend` folder.
2. Add environment variables: `INGESTION_API_URL`, `WORKER_API_URL`.
3. The Next.js proxy rewrites handle all routing — no CORS configuration needed.

---

## Future Enhancements

| Feature | Priority | Description |
|---|---|---|
| Video fingerprinting | High | Extend pHash to work on video keyframes |
| Audio fingerprinting | Medium | Integrate acoustic fingerprinting (chromaprint) |
| Bulk upload API | Medium | Process ZIP archives of multiple assets |
| Webhook notifications | Medium | Push decision results to third-party systems |
| Role-based access | Low | Admin vs viewer permissions on the dashboard |
| Analytics dashboard | Low | Decision trend graphs and statistics |

---

## Conclusion

Nexum Shield demonstrates that an AI-powered media integrity platform does not require expensive GPU infrastructure or heavy deep learning models to be effective. By leveraging perceptual hashing — the same fundamental technology used by YouTube's Content ID — the platform achieves:

- **Accuracy:** Near-duplicate detection with ≥84% similarity threshold.
- **Speed:** Sub-50ms image processing.
- **Cost:** Fully deployable on free-tier cloud infrastructure.
- **Resilience:** Auto-fallback for every external dependency.
- **Scalability:** Decoupled microservices ready for horizontal scaling on demand.

The platform is production-ready as an MVP and serves as a strong foundation for a full-scale content moderation and IP protection product.
