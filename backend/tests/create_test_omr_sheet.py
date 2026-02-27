"""
create_test_omr_sheet.py  (v3 — solid-foreground approach)
-----------------------------------------------------------
Each bubble appears as a SOLID DARK DISK on a plain white sheet.
After THRESH_BINARY_INV: filled bubbles → bright solid blobs (easy to detect).
No rings — just opaque disks. 40 disks total (10 rows × 4).

Student answers (7/10 correct, expected 70%):
  Q1=A(✓) Q2=B(✓) Q3=A(✗,key=C) Q4=D(✓)
  Q5=A(✓) Q6=C(✗,key=B) Q7=C(✓) Q8=D(✓)
  Q9=B(✗,key=A) Q10=B(✓)
"""

import cv2
import numpy as np
import os
import json
import csv
from pathlib import Path

OUT_DIR = Path(__file__).parent / "test_assets"
OUT_DIR.mkdir(exist_ok=True)

NUM_QUESTIONS  = 10
NUM_OPTIONS    = 4
OPTION_LABELS  = ['A', 'B', 'C', 'D']

# Image dimensions and bubble layout
IMG_W, IMG_H   = 400, 650
BUBBLE_R       = 16          # radius in pixels
H_SPACING      = 60          # centre-to-centre in X
V_SPACING      = 54          # centre-to-centre in Y
START_X        = 60          # x-centre of col A
START_Y        = 60          # y-centre of row 1

MASTER_KEY = {
    1: 'A', 2: 'B', 3: 'C', 4: 'D',
    5: 'A', 6: 'B', 7: 'C', 8: 'D',
    9: 'A', 10: 'B'
}
STUDENT_ANSWERS = {
    1: 'A', 2: 'B', 3: 'A', 4: 'D',
    5: 'A', 6: 'C', 7: 'C', 8: 'D',
    9: 'B', 10: 'B',
}


def generate_omr_sheet():
    """
    White background.
    Each bubble drawn as a SOLID DARK CIRCLE (filled disk).
    Filled (student) answers → very dark (30px gray).
    Empty bubbles → medium gray ring (border 160, white fill).
    
    After THRESH_BINARY_INV (which inverts):
      - Filled dark disks → bright white → large blob → detected as filled bubble
      - Medium-gray rings → invert to ~95px → below OTSU threshold → either
        detected as thin ring or not detected (white fill means no inner contour)
    """
    print("Generating OMR sheet (solid-disk approach)...")
    # White background
    sheet = np.full((IMG_H, IMG_W, 3), 255, dtype=np.uint8)

    # Thick black border — critical for document corner detection
    cv2.rectangle(sheet, (5, 5), (IMG_W - 6, IMG_H - 6), (0, 0, 0), 5)

    for q in range(1, NUM_QUESTIONS + 1):
        cy = START_Y + (q - 1) * V_SPACING
        student_ans = STUDENT_ANSWERS.get(q)

        for opt_idx, lbl in enumerate(OPTION_LABELS):
            cx = START_X + opt_idx * H_SPACING

            if student_ans and lbl == student_ans:
                # Filled bubble: solid very dark disk
                cv2.circle(sheet, (cx, cy), BUBBLE_R, (30, 30, 30), -1)
            else:
                # Empty bubble: white interior + gray ring
                cv2.circle(sheet, (cx, cy), BUBBLE_R, (255, 255, 255), -1)
                cv2.circle(sheet, (cx, cy), BUBBLE_R, (140, 140, 140), 2)

    return sheet


def save_all():
    sheet = generate_omr_sheet()
    img_path = OUT_DIR / "test_omr_sheet.png"
    cv2.imwrite(str(img_path), sheet)
    print(f"  Saved: {img_path}")

    csv_path = OUT_DIR / "answer_key.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        for q, ans in MASTER_KEY.items():
            writer.writerow([q, ans])
    print(f"  Saved: {csv_path}")

    correct = sum(
        1 for q in range(1, NUM_QUESTIONS + 1)
        if STUDENT_ANSWERS.get(q) == MASTER_KEY.get(q)
    )
    expected = {
        "total_questions": NUM_QUESTIONS,
        "correct": correct,
        "wrong": NUM_QUESTIONS - correct,
        "percentage": round(correct / NUM_QUESTIONS * 100, 1),
        "master_key": MASTER_KEY,
        "student_answers": STUDENT_ANSWERS,
        "per_question": {
            str(q): {
                "correct_answer": MASTER_KEY[q],
                "student_answer": STUDENT_ANSWERS[q],
                "is_correct": STUDENT_ANSWERS[q] == MASTER_KEY[q]
            }
            for q in range(1, NUM_QUESTIONS + 1)
        }
    }
    json_path = OUT_DIR / "expected_results.json"
    with open(json_path, 'w') as f:
        json.dump(expected, f, indent=2)
    print(f"  Saved: {json_path}")
    print(f"\nExpected: {correct}/{NUM_QUESTIONS} = {expected['percentage']}%")
    return img_path, csv_path, expected


if __name__ == "__main__":
    save_all()
