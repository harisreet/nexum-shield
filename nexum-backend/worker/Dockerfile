FROM python:3.11-slim

# ── System deps for Pillow only (no torch/CUDA required) ──────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Install Python deps (layer-cached, ~80MB total) ───────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy source ───────────────────────────────────────────────────
COPY . .

# ── Create required directories ───────────────────────────────────
RUN mkdir -p /tmp /app/logs

ENV PORT=8002
EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

CMD ["python", "main.py"]
