import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import cv2
import pytest
from dl_model import predict_bubble_dl


# ── Basic filled / empty ──────────────────────────────────────────────────────

def test_predict_bubble_dl_filled():
    """Clearly filled bubble → probability ≥ 0.7."""
    img = np.ones((28, 28), dtype=np.uint8) * 230
    cv2.circle(img, (14, 14), 10, 40, 2)   # outer ring
    cv2.circle(img, (14, 14), 8,  30, -1)  # solid fill
    cv2.ellipse(img, (14, 14), (7, 5), 45, 0, 360, 50, -1)

    probability = predict_bubble_dl(img)
    assert probability >= 0.7, f"Expected ≥ 0.7 for filled bubble, got {probability:.3f}"


def test_predict_bubble_dl_empty():
    """Ring-only bubble → probability < 0.3."""
    img = np.ones((28, 28), dtype=np.uint8) * 230
    cv2.circle(img, (14, 14), 10, 40, 2)

    probability = predict_bubble_dl(img)
    assert probability < 0.3, f"Expected < 0.3 for empty bubble, got {probability:.3f}"


def test_predict_bubble_dl_normal_image_filled():
    """White background + dark fill → ≥ 0.7."""
    img = np.ones((28, 28), dtype=np.uint8) * 255
    cv2.circle(img, (14, 14), 10, 50, 2)
    cv2.circle(img, (14, 14), 8,  30, -1)

    probability = predict_bubble_dl(img)
    assert probability >= 0.7, f"Expected ≥ 0.7 for filled normal bubble, got {probability:.3f}"


def test_predict_bubble_dl_normal_image_empty():
    """White background + ring only → < 0.3."""
    img = np.ones((28, 28), dtype=np.uint8) * 255
    cv2.circle(img, (14, 14), 10, 50, 2)

    probability = predict_bubble_dl(img)
    assert probability < 0.3, f"Expected < 0.3 for empty normal bubble, got {probability:.3f}"


def test_predict_bubble_dl_accepts_color_image():
    """3-channel colour image must not crash."""
    img = np.ones((28, 28, 3), dtype=np.uint8) * 255
    probability = predict_bubble_dl(img)
    assert 0.0 <= probability <= 1.0, f"Probability out of range: {probability}"


# ── Property tests (output always in [0, 1]) ─────────────────────────────────

@pytest.mark.parametrize("seed", range(20))
def test_output_always_in_range_random(seed):
    """Property: predict_bubble_dl(random_img) ∈ [0.0, 1.0] for 20 random seeds."""
    rng = np.random.default_rng(seed)
    img = rng.integers(0, 256, (28, 28), dtype=np.uint8)
    prob = predict_bubble_dl(img)
    assert 0.0 <= prob <= 1.0, f"Seed {seed}: probability {prob} out of range"


# ── Edge case: unusual sizes ──────────────────────────────────────────────────

def test_predict_bubble_1x1_does_not_crash():
    """1×1 pixel image should not crash."""
    img = np.array([[128]], dtype=np.uint8)
    prob = predict_bubble_dl(img)
    assert 0.0 <= prob <= 1.0


def test_predict_bubble_large_image():
    """200×200 image (much larger than training size) should still work."""
    img = np.ones((200, 200), dtype=np.uint8) * 200
    cv2.circle(img, (100, 100), 50, 30, -1)
    prob = predict_bubble_dl(img)
    assert 0.0 <= prob <= 1.0


def test_predict_bubble_all_white():
    """All-white (empty paper) image → very low probability."""
    img = np.ones((28, 28), dtype=np.uint8) * 255
    prob = predict_bubble_dl(img)
    assert prob < 0.4, f"All-white image should have low prob, got {prob:.3f}"


def test_predict_bubble_all_black():
    """All-black (fully filled) image → high probability."""
    img = np.zeros((28, 28), dtype=np.uint8)
    prob = predict_bubble_dl(img)
    assert prob > 0.6, f"All-black image should have high prob, got {prob:.3f}"


def test_predict_bubble_lightly_filled():
    """Lightly pencil-filled bubble (gray fill, not solid black) → prob > 0.3."""
    img = np.ones((28, 28), dtype=np.uint8) * 230
    cv2.circle(img, (14, 14), 10, 60, 2)   # ring
    cv2.circle(img, (14, 14), 7, 140, -1)  # light gray fill (pencil-like)
    prob = predict_bubble_dl(img)
    assert prob > 0.3, f"Lightly filled bubble should score > 0.3, got {prob:.3f}"


def test_predict_bubble_color_filled():
    """BGR colour filled bubble → prob in valid range."""
    img = np.ones((28, 28, 3), dtype=np.uint8) * 220
    cv2.circle(img, (14, 14), 9, (30, 30, 30), -1)
    prob = predict_bubble_dl(img)
    assert 0.0 <= prob <= 1.0
