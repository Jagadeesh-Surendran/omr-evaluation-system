"""
generate_bubble_dataset.py
--------------------------
Generates a REALISTIC synthetic OMR bubble dataset for training BubbleCNN-V2.

Improvements over v1:
  - 15,000 per class (30,000 total) for better generalisation
  - Pen-mark variants (ballpoint, felt-tip) — not just pencil
  - Heavier smear / erasure simulation
  - More aggressive scan artifacts

Output layout:
    bubble_dataset/
        filled/    → 15,000 filled bubble images
        empty/     → 15,000 empty bubble images

Run: python generate_bubble_dataset.py
"""

import cv2
import numpy as np
import os
import random
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
NUM_FILLED = 15_000
NUM_EMPTY  = 15_000
IMG_SIZE   = 28
OUT_DIR    = Path(__file__).parent / "bubble_dataset"
FILLED_DIR = OUT_DIR / "filled"
EMPTY_DIR  = OUT_DIR / "empty"

FILLED_DIR.mkdir(parents=True, exist_ok=True)
EMPTY_DIR.mkdir(parents=True, exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def paper_background(size: int = 64) -> np.ndarray:
    base_val = random.randint(215, 255)
    bg = np.ones((size, size), dtype=np.float32) * base_val
    noise_sigma = random.uniform(2.0, 9.0)
    bg = np.clip(bg + np.random.normal(0, noise_sigma, (size, size)), 0, 255)
    # Shadow stripe
    if random.random() < 0.18:
        smear_y = random.randint(0, size)
        bg[smear_y:, :] = np.clip(bg[smear_y:, :] + random.uniform(-35, -8), 0, 255)
    return bg


def draw_bubble_ring(canvas, cx, cy, outer_r, thickness, color):
    t = max(1, thickness + random.randint(-1, 1))
    cv2.circle(canvas, (cx, cy), outer_r, int(color), t)
    return canvas


def draw_pencil_fill(canvas, cx, cy, inner_r, fill_fraction):
    """Multi-stroke pencil shading (HB/2B simulation)."""
    n_strokes = int(random.uniform(8, 28) * fill_fraction)
    intensity_base = random.randint(15, 100)
    for _ in range(n_strokes):
        a = int(inner_r * random.uniform(0.5, 1.0) * fill_fraction)
        b = int(inner_r * random.uniform(0.1, 0.45))
        angle = random.randint(0, 180)
        ox = random.randint(-inner_r // 3, inner_r // 3)
        oy = random.randint(-inner_r // 3, inner_r // 3)
        intensity = max(8, intensity_base + random.randint(-25, 25))
        cv2.ellipse(canvas, (cx + ox, cy + oy),
                    (max(1, a), max(1, b)), angle, 0, 360, int(intensity), -1)
    if random.random() < 0.5:
        ksize = random.choice([3, 3, 5])
        canvas = cv2.GaussianBlur(canvas, (ksize, ksize), 0)
    return canvas


def draw_pen_fill(canvas, cx, cy, inner_r, fill_fraction):
    """Ballpoint / felt-tip pen mark — solid dark, less textured than pencil."""
    ink_color = random.randint(5, 50)   # very dark
    # Main solid ellipse
    a = int(inner_r * random.uniform(0.6, 1.0) * fill_fraction)
    b = int(inner_r * random.uniform(0.5, 0.9) * fill_fraction)
    angle = random.randint(0, 180)
    cv2.ellipse(canvas, (cx, cy), (max(1, a), max(1, b)),
                angle, 0, 360, ink_color, -1)
    # Ink bleed ring
    if random.random() < 0.4:
        bleed_r = int(inner_r * 0.15 * fill_fraction)
        cv2.circle(canvas, (cx, cy), inner_r + bleed_r, ink_color + 30, 1)
    return canvas


def add_scan_artifacts(img):
    # Brightness jitter ±20
    shift = random.uniform(-20, 20)
    img = np.clip(img.astype(np.float32) + shift, 0, 255).astype(np.uint8)
    # Slight rotation ±5°
    if random.random() < 0.45:
        angle = random.uniform(-5, 5)
        M = cv2.getRotationMatrix2D((IMG_SIZE // 2, IMG_SIZE // 2), angle, 1.0)
        img = cv2.warpAffine(img, M, (IMG_SIZE, IMG_SIZE),
                             borderMode=cv2.BORDER_REFLECT)
    # JPEG compression artefact
    if random.random() < 0.35:
        quality = random.randint(65, 95)
        _, enc = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        img = cv2.imdecode(enc, cv2.IMREAD_GRAYSCALE)
    # Gaussian noise
    noise = np.random.normal(0, random.uniform(0, 5), img.shape).astype(np.float32)
    img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return img


def simulate_smear(canvas, cx, cy, inner_r):
    smear_intensity = random.randint(155, 215)
    smear_r = int(inner_r * random.uniform(0.25, 0.75))
    angle = random.randint(0, 180)
    cv2.ellipse(canvas, (cx, cy), (smear_r, max(1, smear_r // 3)),
                angle, 0, 360, smear_intensity, -1)
    return cv2.GaussianBlur(canvas, (3, 3), 0)


# ── Image generator ───────────────────────────────────────────────────────────

def generate_one(filled: bool, scale: int = 4) -> np.ndarray:
    S        = IMG_SIZE * scale
    cx = cy  = S // 2
    outer_r  = int(S * 0.38)
    inner_r  = int(S * 0.28)
    ring_t   = random.randint(2, 4) * scale

    bg_hires = cv2.resize(paper_background(S * 2).astype(np.uint8), (S, S))
    canvas   = bg_hires.copy().astype(np.uint8)

    ring_color = random.randint(25, 80)
    draw_bubble_ring(canvas, cx, cy, outer_r, ring_t, ring_color)

    if filled:
        fill_fraction = random.uniform(0.35, 1.0)
        use_pen = random.random() < 0.20   # 20% pen marks, 80% pencil
        if use_pen:
            draw_pen_fill(canvas, cx, cy, inner_r, fill_fraction)
        else:
            draw_pencil_fill(canvas, cx, cy, inner_r, fill_fraction)
        # 22% smear / erasure attempt
        if random.random() < 0.22:
            canvas = simulate_smear(canvas, cx, cy, inner_r)
    else:
        # 15% empty bubbles have faint pencil dust / stray marks
        if random.random() < 0.15:
            noise_patch = np.random.randint(195, 245, (inner_r * 2, inner_r * 2),
                                            dtype=np.uint8)
            mask = np.zeros((S, S), dtype=np.uint8)
            cv2.circle(mask, (cx, cy), inner_r, 255, -1)
            y1, y2 = cy - inner_r, cy + inner_r
            x1, x2 = cx - inner_r, cx + inner_r
            y1_c, y2_c = max(0, y1), min(S, y2)
            x1_c, x2_c = max(0, x1), min(S, x2)
            patch  = noise_patch[y1_c - y1:y2_c - y1, x1_c - x1:x2_c - x1]
            roi    = canvas[y1_c:y2_c, x1_c:x2_c]
            roi_m  = mask[y1_c:y2_c, x1_c:x2_c]
            canvas[y1_c:y2_c, x1_c:x2_c] = np.where(
                roi_m > 0, np.minimum(roi, patch), roi
            )

    small = cv2.resize(canvas, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
    return add_scan_artifacts(small)


# ── Main ──────────────────────────────────────────────────────────────────────

def generate_dataset():
    print(f"Generating {NUM_FILLED} filled + {NUM_EMPTY} empty bubble images...")
    print(f"Output: {OUT_DIR}\n")

    for i in range(NUM_FILLED):
        img = generate_one(filled=True)
        cv2.imwrite(str(FILLED_DIR / f"filled_{i:05d}.png"), img)
        if (i + 1) % 2000 == 0:
            print(f"  Filled: {i+1}/{NUM_FILLED}")

    for i in range(NUM_EMPTY):
        img = generate_one(filled=False)
        cv2.imwrite(str(EMPTY_DIR / f"empty_{i:05d}.png"), img)
        if (i + 1) % 2000 == 0:
            print(f"  Empty:  {i+1}/{NUM_EMPTY}")

    print(f"\nDataset complete: {NUM_FILLED + NUM_EMPTY} images in '{OUT_DIR}'")
    print("Next: run 'python train_model.py'")


if __name__ == "__main__":
    generate_dataset()
