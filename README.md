# NEXUM SHIELD 🛡️

**A self-contained, high-speed media integrity platform.**

NEXUM SHIELD detects unauthorized media copies instantly using a deterministic AI pipeline. It uses CLIP embeddings and FAISS similarity search to generate transparent risk scores and enforce an auditable **ALLOW / REVIEW / BLOCK** decision. 

Built specifically for high-speed local hackathon execution with zero friction.

![Platform Demo](https://img.shields.io/badge/Platform-Live-success?style=for-the-badge) ![Tech Stack](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20PyTorch-black?style=for-the-badge)

---

## The AI Pipeline Architecture

The platform features a highly modular architecture completely self-contained for local execution (no cloud accounts or Docker required for testing!):

1. **Next.js Dashboard (:3000)**
   - Uploads assets and polls real-time analytical responses.
2. **Ingestion API (:8001)**
   - Fast traffic coordinator. Validates the image, stores it on the filesystem, and uses an HTTP Push to trigger the worker.
3. **Worker Engine (:8002)**
   - Heavy AI lifting executing a 6-stage pipeline:
     1. **Preprocessing** (Validation, hash extraction)
     2. **Embedding** (PyTorch CLIP ViT-B/32 generates a 512-dimension vector)
     3. **Matching** (FAISS IndexFlatIP executes rapid similarity searches)
     4. **Risk** (Compute confidence score and deterministic risk profile)
     5. **Decision** (Consult strict Policy table)
     6. **Explanation** (Generate human-readable justification log)

All mock storage and mock "cloud" objects are securely mapped directly to your local `C:\tmp\nexum-storage\` folder for instant results.

---

## 🚀 Quick Start (Native Execution)

No Docker. No Cloud Accounts. 100% Native Speed.

### Prerequisites
- Python 3.11+
- Node.js 20+

### 1. Start the Worker Brain
*On its first run, it will automatically download the 350MB CLIP model.*
```bash
cd nexum-backend/worker
pip install -r requirements.txt
python main.py
```

### 2. Start the Ingestion API
Open a second terminal window:
```bash
cd nexum-backend/ingestion
pip install -r requirements.txt
python main.py
```

### 3. Start the UI Dashboard
Open a third terminal window:
```bash
cd nexum-frontend
npm install
npm run dev
```

---

## 🎯 How to Demo the Platform

### 1. Train the Engine (Seed an Image)
Open the administrative Swagger UI at **http://localhost:8002/docs**. 
Expand `POST /admin/seed` and upload any reference image (e.g., an original artwork or identity document). This instantly saves the image's mathematical signature into the FAISS memory core.

### 2. Watch the Enforcer Fire
Go to the main dashboard at **http://localhost:3000/upload**. 
Drag and drop that **exact same image** (or a mildly cropped version) into the analyzer. 
The AI will calculate the mathematical drift, recognize the signature from the Seed database, and automatically slap it with a massive risk score and a **BLOCK** decision.

### 3. See the Bypass
Upload a completely unrelated picture. The risk core will see no match, produce a sub-threshold (< 0.70) score, and securely issue an **ALLOW** decision. 

Go to the **Audit Log** tab in the dashboard to see an immutable record of every decision safely captured for compliance.

---

## Strict Policy Enforcement (v1)

We don't use "black box AI" to make decisions. The AI generates the embeddings, but the actual decision is dictated legally by a strict enforcement table:

| Max Vector Score | Assigned Decision | Explanation Rule |
|---|---|---|
| ≥ 0.90 | **BLOCK** | Direct signature match detected in FAISS database. |
| 0.85 – 0.90 | **REVIEW** | Elevated uncertainty boundary breached (requires human verification). |
| 0.70 – 0.85 | **REVIEW** | Standard review threshold. |
| < 0.70 | **ALLOW** | No significant vector match. Safe for ingestion. |

---

## Advanced: Deploying to Production GCP

If you wish to exit Native Dev mode and deploy this onto authentic Google Cloud Platform infrastructure:

1. Create a Firebase project and a standard GCP project.
2. Go to `ingestion/config.py` and `worker/config.py` and implement standard Google Cloud libraries.
3. Build the backend using Docker:
   ```bash
   gcloud builds submit --tag us-central1-docker.pkg.dev/$PROJECT_ID/nexum/worker:latest nexum-backend/worker
   ```
4. Map the Cloud Run endpoints cleanly with Pub/Sub push topologies. 

For the hackathon, we keep these fully local to guarantee presentation execution speed!
