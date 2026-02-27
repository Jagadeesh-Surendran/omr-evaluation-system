"""
dl_model.py — BubbleCNN-V2 + Ensemble Scoring

Bubble detection uses TWO strategies combined (ensemble):
  1. BubbleCNN-V2 (PyTorch) — deeper 3-block CNN with Squeeze-Excitation attention.
     Loaded from bubble_model.pth if it exists.
  2. CV Heuristic — pixel-density in circular mask. Always available.

Ensemble: final_prob = 0.70 × CNN_prob + 0.30 × CV_prob
This uses the CV heuristic as a calibration signal rather than a dead fallback,
which consistently improves accuracy on borderline bubbles.

Document corner detection uses contour-based CV (no model needed).

To train/re-train the CNN:
  1. python generate_bubble_dataset.py   (generates 30,000 realistic images)
  2. python train_model.py               (trains and saves bubble_model.pth)
"""

import cv2
import numpy as np
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'bubble_model.pth')

# ── CNN loading ───────────────────────────────────────────────────────────────
_model = None

def _load_cnn():
    global _model
    if _model is not None:
        return True
    if not os.path.exists(MODEL_PATH):
        return False
    try:
        import torch
        import torch.nn as nn

        class _SEBlock(nn.Module):
            """Squeeze-Excitation channel attention — focuses on the filled region."""
            def __init__(self, channels, reduction=8):
                super().__init__()
                self.se = nn.Sequential(
                    nn.AdaptiveAvgPool2d(1),
                    nn.Flatten(),
                    nn.Linear(channels, max(1, channels // reduction)),
                    nn.ReLU(inplace=True),
                    nn.Linear(max(1, channels // reduction), channels),
                    nn.Sigmoid(),
                )
            def forward(self, x):
                w = self.se(x).view(x.size(0), x.size(1), 1, 1)
                return x * w

        class BubbleCNNV2(nn.Module):
            """
            3-block CNN with Squeeze-Excitation attention.
            Input:  (B, 1, 28, 28)
            Output: (B, 1) — probability of being FILLED
            """
            def __init__(self):
                super().__init__()
                self.features = nn.Sequential(
                    # Block 1: 1→32
                    nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(True),
                    nn.Conv2d(32, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(True),
                    nn.MaxPool2d(2, 2),               # → (32, 14, 14)
                    nn.Dropout2d(0.15),

                    # Block 2: 32→64
                    nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(True),
                    nn.Conv2d(64, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(True),
                    nn.MaxPool2d(2, 2),               # → (64, 7, 7)
                    nn.Dropout2d(0.15),

                    # Block 3: 64→128 + SE attention
                    nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(True),
                    _SEBlock(128),
                    nn.Dropout2d(0.1),
                )
                self.classifier = nn.Sequential(
                    nn.AdaptiveAvgPool2d(1),    # Global average pool → (128, 1, 1)
                    nn.Flatten(),               # → 128
                    nn.Linear(128, 64), nn.ReLU(True), nn.Dropout(0.3),
                    nn.Linear(64, 1), nn.Sigmoid()
                )

            def forward(self, x):
                return self.classifier(self.features(x))

        # Also support loading old BubbleCNN weights (2-block architecture)
        class BubbleCNNLegacy(nn.Module):
            def __init__(self):
                super().__init__()
                self.features = nn.Sequential(
                    nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(True),
                    nn.Conv2d(32, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(True),
                    nn.MaxPool2d(2, 2), nn.Dropout2d(0.2),
                    nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(True),
                    nn.Conv2d(64, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(True),
                    nn.MaxPool2d(2, 2), nn.Dropout2d(0.2),
                )
                self.classifier = nn.Sequential(
                    nn.Flatten(),
                    nn.Linear(64 * 7 * 7, 128), nn.ReLU(True), nn.Dropout(0.4),
                    nn.Linear(128, 1), nn.Sigmoid()
                )
            def forward(self, x):
                return self.classifier(self.features(x))

        state = torch.load(MODEL_PATH, map_location=torch.device('cpu'), weights_only=True)

        # Try V2 first, fall back to legacy if key mismatch
        net = BubbleCNNV2()
        try:
            net.load_state_dict(state)
        except RuntimeError:
            net = BubbleCNNLegacy()
            net.load_state_dict(state)
            print("[dl_model] Loaded legacy BubbleCNN weights — retrain with train_model.py for V2.")

        net.eval()
        _model = net
        print(f"[dl_model] BubbleCNN loaded from {MODEL_PATH}")
        return True
    except Exception as e:
        print(f"[dl_model] Could not load CNN: {e}. Using CV heuristic only.")
        return False


# ── CV Heuristic ──────────────────────────────────────────────────────────────

def _cv_heuristic(bubble_img: np.ndarray) -> float:
    """
    Pixel density inside the inner circular region of the bubble.
    Returns 0.0–1.0 probability of being filled.
    """
    resized = cv2.resize(bubble_img, (28, 28)).astype(np.float32)
    if len(resized.shape) == 3:
        resized = cv2.cvtColor(resized.astype(np.uint8),
                               cv2.COLOR_BGR2GRAY).astype(np.float32)

    mask = np.zeros((28, 28), dtype=np.uint8)
    cv2.circle(mask, (14, 14), 8, 255, -1)
    inner_pixels = np.count_nonzero(mask)
    if inner_pixels == 0:
        return 0.0

    mean_val = float(np.mean(resized))
    if mean_val > 128:
        mark_map = (resized < 100).astype(np.uint8)
    else:
        mark_map = (resized > 30).astype(np.uint8)

    density = int(np.sum(mark_map[mask == 255])) / inner_pixels

    LOW, HIGH = 0.03, 0.20
    if density >= HIGH:
        return 1.0
    elif density <= LOW:
        return 0.0
    return (density - LOW) / (HIGH - LOW)


# ── Public API: predict_bubble_dl ─────────────────────────────────────────────

def predict_bubble_dl(bubble_img: np.ndarray) -> float:
    """
    Returns probability (0.0–1.0) that the bubble is FILLED.

    Ensemble strategy:
      - If BubbleCNN-V2 is loaded: final = 0.70 × CNN + 0.30 × CV
      - If CNN not available:      final = CV heuristic only

    The 70/30 blend keeps the CV heuristic as a calibration signal,
    which improves accuracy on borderline (lightly filled) bubbles.
    """
    cv_prob = _cv_heuristic(bubble_img)

    if _load_cnn():
        try:
            import torch
            resized = cv2.resize(bubble_img, (28, 28))
            if len(resized.shape) == 3:
                resized = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            img_f = resized.astype(np.float32) / 255.0
            tensor = torch.tensor(img_f).unsqueeze(0).unsqueeze(0)  # (1,1,28,28)
            with torch.no_grad():
                cnn_prob = _model(tensor).item()

            # Ensemble: weighted blend of CNN and CV
            return float(0.70 * cnn_prob + 0.30 * cv_prob)
        except Exception as e:
            print(f"[dl_model] CNN inference error: {e}. Using CV only.")

    return cv_prob


# ── Public API: predict_document_corners ─────────────────────────────────────

def predict_document_corners(image: np.ndarray) -> np.ndarray:
    """
    Finds the 4 corners of the OMR sheet using contour-based CV.
    Returns (4, 2) float32 array of (x, y) coordinates.
    Raises ValueError if no document boundary found.
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    edged = cv2.Canny(blurred, 50, 150)
    combined = cv2.bitwise_or(thresh, edged)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    combined = cv2.dilate(combined, kernel, iterations=1)

    cnts, _ = cv2.findContours(combined, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    doc_cnt = None
    for c in cnts:
        area = cv2.contourArea(c)
        if area < 1000 or area > 0.98 * w * h:
            continue
        peri   = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            doc_cnt = approx.reshape(4, 2).astype(np.float32)
            break

    if doc_cnt is None and cnts:
        hull  = cv2.convexHull(cnts[0])
        peri  = cv2.arcLength(hull, True)
        approx = cv2.approxPolyDP(hull, 0.02 * peri, True)
        pts   = approx.reshape(-1, 2).astype(np.float32)
        if len(pts) >= 4:
            s    = pts.sum(axis=1)
            diff = np.diff(pts, axis=1)
            doc_cnt = np.array([
                pts[np.argmin(s)], pts[np.argmin(diff)],
                pts[np.argmax(s)], pts[np.argmax(diff)],
            ], dtype=np.float32)

    if doc_cnt is None:
        raise ValueError("Could not detect document boundary.")

    return doc_cnt
