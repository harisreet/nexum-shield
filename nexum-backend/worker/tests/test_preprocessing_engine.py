"""
NEXUM SHIELD — Unit Tests: Preprocessing Engine
Tests validation, format checks, resize, pHash — no CLIP required.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import io
import pytest
from PIL import Image
from engines.preprocessing.processor import PreprocessingEngine
from engines.base import EngineError

engine = PreprocessingEngine()


def make_image_bytes(width=400, height=300, fmt="JPEG", color=(120, 80, 200)) -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


# ── Happy path ────────────────────────────────────────────────────

def test_jpeg_processes_successfully():
    result = engine.process({"image_bytes": make_image_bytes(fmt="JPEG"), "filename": "test.jpg"})
    assert result["phash"] is not None
    assert result["width"] == 400
    assert result["height"] == 300
    assert result["format"] == "JPEG"
    assert os.path.exists(result["local_path"])
    # cleanup
    os.remove(result["local_path"])


def test_png_processes_successfully():
    result = engine.process({"image_bytes": make_image_bytes(fmt="PNG"), "filename": "test.png"})
    assert result["format"] == "PNG"
    os.remove(result["local_path"])


def test_phash_is_string():
    result = engine.process({"image_bytes": make_image_bytes(), "filename": "test.jpg"})
    assert isinstance(result["phash"], str)
    assert len(result["phash"]) > 0
    os.remove(result["local_path"])


def test_image_resized_to_224():
    """CLIP input must be 224×224."""
    result = engine.process({"image_bytes": make_image_bytes(800, 600), "filename": "big.jpg"})
    img = result["image"]
    assert img.size == (224, 224)
    os.remove(result["local_path"])


# ── Validation failures ───────────────────────────────────────────

def test_no_bytes_raises_engine_error():
    with pytest.raises(EngineError):
        engine.process({"image_bytes": None, "filename": "test.jpg"})


def test_empty_bytes_raises_engine_error():
    with pytest.raises(EngineError):
        engine.process({"image_bytes": b"", "filename": "test.jpg"})


def test_corrupt_bytes_raises_engine_error():
    with pytest.raises(EngineError):
        engine.process({"image_bytes": b"not-an-image", "filename": "bad.jpg"})


def test_oversized_file_raises_engine_error():
    # 21 MB of zeros
    with pytest.raises(EngineError, match="too large"):
        engine.process({"image_bytes": b"\x00" * (21 * 1024 * 1024), "filename": "huge.jpg"})


# ── Determinism ───────────────────────────────────────────────────

def test_same_image_same_phash():
    data = make_image_bytes()
    r1 = engine.process({"image_bytes": data, "filename": "a.jpg"})
    r2 = engine.process({"image_bytes": data, "filename": "a.jpg"})
    assert r1["phash"] == r2["phash"]
    os.remove(r1["local_path"])
    os.remove(r2["local_path"])
