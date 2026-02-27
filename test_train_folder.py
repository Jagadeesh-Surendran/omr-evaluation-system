"""
test_train_folder.py
--------------------
Real-world OMR evaluation using the 10 images from the project's /train folder.

The train folder contains a Roboflow COCO dataset:
  - 11 images (1700x2200px) of real OMR evaluation sheets
  - _annotations.coco.json with exact bounding box annotations

Category map from annotations:
  cat_id 1  = bubble marked "1" (rating 1)
  cat_id 2  = bubble marked "2" (rating 2)
  cat_id 3  = bubble marked "3" (rating 3)
  cat_id 4  = bubble marked "4" (rating 4)
  cat_id 5  = bubble marked "5" (rating 5)
  cat_id 6  = "absent" (student absent marker)
  cat_id 28 = "skills" (the skill label column — not a bubble)
  cat_id 24 = "header", 23 = "footer", 25 = "name", etc.

Each row of bubbles (1–5) represents a SKILL rating.
The CNN model is used to verify/confirm which bubble in each row is filled.

This script:
  1. Loads all 10 images + annotations
  2. Crops each annotated bubble using the exact COCO bounding box
  3. Passes each crop to predict_bubble_dl() (our CNN/CV model)
  4. Compares CNN confidence vs. the annotated ground-truth category
  5. Reports per-image accuracy and overall CNN performance on real data
"""

import sys, os, json, cv2, numpy as np
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from dl_model import predict_bubble_dl

TRAIN_DIR   = Path(__file__).parent / "train"
ANNO_FILE   = TRAIN_DIR / "_annotations.coco.json"
RESULTS_DIR = TRAIN_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ── Load annotations ──────────────────────────────────────────────────────────
with open(ANNO_FILE) as f:
    coco = json.load(f)

# Category lookup
cat_map = {c["id"]: c["name"] for c in coco["categories"]}
# Bubble categories = those named "1" through "5" or "absent"
BUBBLE_CATS      = {1, 2, 3, 4, 5}    # filled skill-rating bubbles
ABSENT_CAT       = 6
RATING_CATS      = BUBBLE_CATS | {ABSENT_CAT}

# Image lookup
img_map = {i["id"]: i for i in coco["images"]}

# Group annotations by image
from collections import defaultdict
anno_by_image = defaultdict(list)
for a in coco["annotations"]:
    anno_by_image[a["image_id"]].append(a)

print("=" * 65)
print("  REAL-WORLD OMR EVALUATION — Train Folder")
print("  Using CNN model on COCO-annotated real exam sheets")
print("=" * 65)

all_tp = all_fp = all_fn = 0
image_results = []

for img_id, img_info in sorted(img_map.items()):
    fname  = img_info["file_name"]
    fpath  = TRAIN_DIR / fname

    if not fpath.exists():
        print(f"\nMISSING: {fname}")
        continue

    img = cv2.imread(str(fpath))
    if img is None:
        print(f"\nERROR reading: {fname}")
        continue

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    annots = anno_by_image[img_id]

    # Filter to bubble rating annotations only
    rating_annots = [a for a in annots if a["category_id"] in RATING_CATS]

    # Build a visual output image
    vis = img.copy()

    correct = wrong = 0
    skill_reads = []

    for a in rating_annots:
        cat_id = a["category_id"]
        true_label = cat_map[cat_id]   # "1","2","3","4","5","absent"

        # Parse bbox [x, y, w, h]
        bx, by, bw, bh = [int(float(v)) for v in a["bbox"]]

        # Crop with small padding
        pad = 3
        x1 = max(0, bx - pad)
        y1 = max(0, by - pad)
        x2 = min(gray.shape[1], bx + int(bw) + pad)
        y2 = min(gray.shape[0], by + int(bh) + pad)
        crop = gray[y1:y2, x1:x2]

        if crop.size == 0:
            continue

        # Run CNN on the crop
        prob = predict_bubble_dl(crop)

        # Ground truth: rating bubbles (1-5) ARE filled; we expect prob >= 0.5
        # absent bubble: also marked, expect prob >= 0.5
        gt_filled = True   # all annotated rating bubbles are filled by definition

        cnn_filled = prob >= 0.5
        is_correct = (cnn_filled == gt_filled)

        if is_correct:
            correct += 1
            color = (0, 200, 0)   # green
        else:
            wrong += 1
            color = (0, 0, 220)   # red

        # Draw on vis
        cv2.rectangle(vis, (bx, by), (bx+int(bw), by+int(bh)), color, 2)
        label_txt = f"{true_label}|{prob:.2f}"
        cv2.putText(vis, label_txt, (bx, by - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

        skill_reads.append({
            "gt": true_label,
            "cnn_prob": round(prob, 3),
            "cnn_says_filled": cnn_filled,
            "correct": is_correct
        })

    total = correct + wrong
    acc = round(correct / total * 100, 1) if total > 0 else 0.0

    all_tp += correct
    all_fp += wrong   # wrong here = FP (said not-filled when filled)

    # Save annotated output image
    out_path = RESULTS_DIR / f"result_{fname}"
    cv2.imwrite(str(out_path), vis)

    # Print per-image summary
    print(f"\n  Image: {fname}")
    print(f"  Size : {img.shape[1]}x{img.shape[0]}px")
    print(f"  Annotated bubbles : {total}")
    print(f"  CNN correct (filled detected) : {correct}/{total} = {acc}%")
    print(f"  Per-bubble reads:")
    for r in skill_reads:
        status = "OK" if r["correct"] else "MISS"
        print(f"    [{status}] Rating={r['gt']}  CNN_prob={r['cnn_prob']:.3f}  "
              f"{'FILLED' if r['cnn_says_filled'] else 'empty'}")

    print(f"  Output saved: results/result_{fname}")
    image_results.append((fname, total, correct, wrong, acc))

# ── Summary ────────────────────────────────────────────────────────────────────
total_bubbles = sum(t for _, t, _, _, _ in image_results)
total_correct = sum(c for _, _, c, _, _ in image_results)
overall_acc   = round(total_correct / total_bubbles * 100, 1) if total_bubbles > 0 else 0

print(f"\n{'='*65}")
print("  OVERALL RESULTS SUMMARY")
print(f"{'='*65}")
print(f"  {'Image':<50} {'Bubbles':>8} {'Correct':>8} {'Acc%':>6}")
print(f"  {'-'*65}")
for fname, t, c, w, acc in image_results:
    short = fname[:48]
    print(f"  {short:<50} {t:>8} {c:>8} {acc:>5}%")
print(f"  {'─'*65}")
print(f"  {'TOTAL':<50} {total_bubbles:>8} {total_correct:>8} {overall_acc:>5}%")
print(f"\n  CNN Model Accuracy on REAL annotated OMR bubbles: {overall_acc}%")
print(f"  Annotated visual outputs saved to: train/results/")
print("=" * 65)
