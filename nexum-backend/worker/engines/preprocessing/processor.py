"""
NEXUM SHIELD — Preprocessing Engine
Validates, normalizes, and hashes incoming images.
Fails fast on corrupt or invalid input — no partial processing.
"""
import io
import os
import uuid
from pathlib import Path
from typing import Any

import imagehash
from PIL import Image, UnidentifiedImageError

from engines.base import Engine, EngineError

# CLIP input dimensions
TARGET_SIZE = (224, 224)
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_FILE_SIZE_MB = 20


class PreprocessingEngine(Engine):
    """
    Input:  { "image_bytes": bytes, "filename": str }
    Output: { "image": PIL.Image, "phash": str, "width": int, "height": int,
              "format": str, "local_path": str }
    """

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        image_bytes: bytes = input_data.get("image_bytes")
        filename: str = input_data.get("filename", "upload.jpg")

        if not image_bytes:
            raise EngineError(self.name, "No image bytes provided.")

        # ── Size Guard ────────────────────────────────────────────
        size_mb = len(image_bytes) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise EngineError(self.name, f"File too large: {size_mb:.1f}MB (max {MAX_FILE_SIZE_MB}MB)")

        # ── Open + Validate ───────────────────────────────────────
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()  # corruption check
            # Re-open after verify (verify closes the file object)
            image = Image.open(io.BytesIO(image_bytes))
        except (UnidentifiedImageError, Exception) as e:
            raise EngineError(self.name, f"Corrupt or unreadable image: {e}", original=e)

        # ── Format Check ──────────────────────────────────────────
        fmt = image.format or "UNKNOWN"
        if fmt.upper() not in ALLOWED_FORMATS:
            raise EngineError(self.name, f"Unsupported format: {fmt}. Allowed: {ALLOWED_FORMATS}")

        # ── Convert to RGB (handles RGBA, palette, etc.) ──────────
        image = image.convert("RGB")
        orig_width, orig_height = image.size

        # ── Perceptual Hash (before resize for accuracy) ──────────
        phash = str(imagehash.phash(image))

        # ── Resize to CLIP input dims ─────────────────────────────
        image = image.resize(TARGET_SIZE, Image.LANCZOS)

        # ── Save to temp path ─────────────────────────────────────
        local_path = f"/tmp/{uuid.uuid4().hex}.jpg"
        image.save(local_path, format="JPEG", quality=95)

        return {
            "image": image,
            "phash": phash,
            "width": orig_width,
            "height": orig_height,
            "format": fmt,
            "local_path": local_path,
        }
