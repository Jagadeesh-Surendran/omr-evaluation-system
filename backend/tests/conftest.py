"""
conftest.py — Shared pytest fixtures for the OMR test suite.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import numpy as np
import cv2


# ── Bubble image fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def filled_bubble_img():
    """28×28 grayscale image of a clearly filled bubble (dark pencil mark)."""
    img = np.ones((28, 28), dtype=np.uint8) * 230
    cv2.circle(img, (14, 14), 10, 40, 2)   # outer ring
    cv2.circle(img, (14, 14), 8,  30, -1)  # solid fill
    cv2.ellipse(img, (14, 14), (7, 5), 45, 0, 360, 50, -1)
    return img


@pytest.fixture
def empty_bubble_img():
    """28×28 grayscale image of an unfilled bubble (ring only, no fill)."""
    img = np.ones((28, 28), dtype=np.uint8) * 230
    cv2.circle(img, (14, 14), 10, 40, 2)
    return img


@pytest.fixture
def filled_bubble_color():
    """28×28 BGR colour filled bubble."""
    img = np.ones((28, 28, 3), dtype=np.uint8) * 220
    cv2.circle(img, (14, 14), 9, (30, 30, 30), -1)
    return img


# ── Answer key fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def five_question_key():
    """5-question answer key, 0-indexed, option indices."""
    return {0: 0, 1: 1, 2: 2, 3: 3, 4: 0}  # A, B, C, D, A


@pytest.fixture
def ten_question_key():
    """10-question answer key, all 'A' (index 0)."""
    return {i: 0 for i in range(10)}


# ── Synthetic OMR sheet fixture ───────────────────────────────────────────────

@pytest.fixture
def synthetic_omr_image():
    """
    Draws a simple 5-question × 4-option OMR grid on a white canvas.
    The bubbles for option A (index 0) are filled for all questions.
    """
    H, W = 400, 600
    img = np.ones((H, W, 3), dtype=np.uint8) * 255

    bubble_r   = 15
    row_start  = 60
    row_step   = 60
    col_start  = 80
    col_step   = 70
    num_q      = 5
    num_opts   = 4
    filled_opt = 0  # fill option A for every question

    for q in range(num_q):
        cy = row_start + q * row_step
        for o in range(num_opts):
            cx = col_start + o * col_step
            # Outer ring (always draw)
            cv2.circle(img, (cx, cy), bubble_r, (40, 40, 40), 2)
            if o == filled_opt:
                # Solid fill for the chosen option
                cv2.circle(img, (cx, cy), bubble_r - 3, (30, 30, 30), -1)

    return img


# ── Answer key image fixture ──────────────────────────────────────────────────

@pytest.fixture
def sample_answer_key_image():
    """Create a synthetic answer key image for testing."""
    import tempfile
    
    # Create a white image with text
    img = np.ones((800, 600, 3), dtype=np.uint8) * 255
    
    # Add some text to simulate an answer key
    font = cv2.FONT_HERSHEY_SIMPLEX
    y_pos = 100
    for i in range(1, 6):
        answer = chr(65 + (i % 5))  # A, B, C, D, E
        text = f"Q{i}: {answer}"
        cv2.putText(img, text, (50, y_pos), font, 1, (0, 0, 0), 2)
        y_pos += 80
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        cv2.imwrite(f.name, img)
        yield f.name
    
    # Cleanup
    if os.path.exists(f.name):
        os.unlink(f.name)


# ── Flask app client fixture ──────────────────────────────────────────────────

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as test_client:
        yield test_client
