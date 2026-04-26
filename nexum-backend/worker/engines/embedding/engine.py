"""
NEXUM SHIELD — Embedding Engine (pHash)
Replaces PyTorch/CLIP with lightweight perceptual hashing.
Generates a 64-bit pHash fingerprint from a PIL image.
Zero external AI model downloads required.
"""
from typing import Any

import imagehash
from PIL import Image

from engines.base import Engine, EngineError


def load_clip_model() -> None:
    """No-op: pHash requires no model loading."""
    pass


class EmbeddingEngine(Engine):
    """
    Input:  { "image": PIL.Image }
    Output: { "phash": str, "model": str, "embedding_version": str }

    Uses perceptual hashing (pHash) — deterministic, lightweight, CPU-only.
    No PyTorch, no CLIP, no GPU required.
    """

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        image: Image.Image = input_data.get("image")
        if image is None:
            raise EngineError(self.name, "No image provided — expected PIL.Image.")

        try:
            phash_value = str(imagehash.phash(image))
        except Exception as e:
            raise EngineError(self.name, f"pHash computation failed: {e}", original=e)

        return {
            "phash": phash_value,
            "model": "phash-v1",
            "embedding_version": "phash_v1",
        }
