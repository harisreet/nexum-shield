"""
NEXUM SHIELD — Embedding Engine (CLIP ViT-B/32)
Converts a preprocessed PIL image into a normalized 512-d float vector.
Model is loaded ONCE at module level — never per-request.
"""
from typing import Any

import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from config import settings
from engines.base import Engine, EngineError

# ─── Singleton model state ────────────────────────────────────────
_model: CLIPModel | None = None
_processor: CLIPProcessor | None = None
_device: str = "cuda" if torch.cuda.is_available() else "cpu"


def load_clip_model() -> None:
    """Load CLIP model into memory. Called once at app startup."""
    global _model, _processor
    if _model is not None:
        return  # already loaded

    _model = CLIPModel.from_pretrained(settings.CLIP_MODEL_NAME)
    _processor = CLIPProcessor.from_pretrained(settings.CLIP_MODEL_NAME)
    _model.to(_device)
    _model.eval()


def get_model() -> tuple[CLIPModel, CLIPProcessor]:
    if _model is None or _processor is None:
        raise RuntimeError("CLIP model not loaded. Call load_clip_model() at startup.")
    return _model, _processor


class EmbeddingEngine(Engine):
    """
    Input:  { "image": PIL.Image }
    Output: { "vector": list[float], "model": str, "embedding_version": str }

    Determinism guarantee: identical image bytes → identical vector.
    torch.no_grad() + eval mode + CPU/GPU pinned at startup.
    """

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        image: Image.Image = input_data.get("image")
        if image is None:
            raise EngineError(self.name, "No image provided — expected PIL.Image.")

        model, processor = get_model()

        try:
            inputs = processor(images=image, return_tensors="pt").to(_device)

            with torch.no_grad():
                features = model.get_image_features(**inputs)
                # L2 normalization — makes dot product == cosine similarity
                features = features / features.norm(dim=-1, keepdim=True)

            vector: list[float] = features.squeeze().cpu().numpy().tolist()

        except Exception as e:
            raise EngineError(self.name, f"CLIP inference failed: {e}", original=e)

        return {
            "vector": vector,
            "model": settings.CLIP_MODEL_NAME,
            "embedding_version": settings.MODEL_VERSION,
        }
