FROM python:3.11-slim

# ── System deps for Pillow + torch ────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Install Python deps (layer-cached) ────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Pre-download CLIP model into image (avoids cold-start download) ─
RUN python -c "from transformers import CLIPModel, CLIPProcessor; \
    CLIPModel.from_pretrained('openai/clip-vit-base-patch32'); \
    CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')"

# ── Copy source ───────────────────────────────────────────────────
COPY . .

# ── Create required directories ───────────────────────────────────
RUN mkdir -p /tmp /app/logs

ENV PORT=8002
EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

CMD ["python", "main.py"]
