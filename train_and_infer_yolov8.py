"""
train_and_infer_yolov8.py
--------------------------
1. Fixes the data.yaml paths to absolute
2. Trains YOLOv8n on the 150-image OMR region detection dataset
3. Runs inference on all 11 images in the /train folder
4. Draws annotated bounding boxes (answer_region, personal_data, sheet_id, sign)
5. Prints a detailed per-image detection report
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

import cv2, yaml, shutil
from pathlib import Path
from ultralytics import YOLO

ROOT     = Path(__file__).parent
YOLO_DIR = ROOT / "yolov8_omr"
TRAIN_IMGS = ROOT / "train"
OUT_DIR    = ROOT / "yolov8_results"
OUT_DIR.mkdir(exist_ok=True)

# ── Step 1: Fix data.yaml with absolute paths ─────────────────────────────────
print("Step 1: Writing absolute-path data.yaml...")
data_yaml = {
    "train": str(YOLO_DIR / "train" / "images"),
    "val":   str(YOLO_DIR / "valid" / "images"),
    "nc":    4,
    "names": ["answer_region", "personal_data", "sheet_id_region", "sign"]
}
yaml_path = YOLO_DIR / "data_abs.yaml"
with open(yaml_path, "w") as f:
    yaml.dump(data_yaml, f)
print(f"  Saved: {yaml_path}")

# ── Step 2: Train YOLOv8n ─────────────────────────────────────────────────────
print("\nStep 2: Training YOLOv8n on 150 real OMR images...")
model = YOLO("yolov8n.pt")   # auto-downloads nano pre-trained weights
results_train = model.train(
    data    = str(yaml_path),
    epochs  = 30,
    imgsz   = 640,
    batch   = 8,
    name    = "omr_yolov8n",
    project = str(ROOT / "yolov8_runs"),
    device  = "cpu",          # use CPU (no GPU needed for nano)
    verbose = False,
    patience= 10,
    save    = True,
)
print("  Training complete!")

# ── Step 3: Load the best trained weights ────────────────────────────────────
best_pt = ROOT / "yolov8_runs" / "omr_yolov8n" / "weights" / "best.pt"
print(f"\nStep 3: Loading best model: {best_pt}")
model_best = YOLO(str(best_pt))

# ── Step 4: Run inference on all real OMR images from /train folder ──────────
class_names = ["answer_region", "personal_data", "sheet_id_region", "sign"]
class_colors = {
    "answer_region":   (0, 200, 50),    # green
    "personal_data":   (200, 100, 0),   # orange
    "sheet_id_region": (50, 50, 220),   # blue
    "sign":            (200, 0, 180),   # purple
}

imgs = sorted([p for p in TRAIN_IMGS.glob("*.jpg")])
print(f"\nStep 4: Running inference on {len(imgs)} real OMR images...\n")
print("=" * 65)

for img_path in imgs:
    img = cv2.imread(str(img_path))
    if img is None:
        continue

    # Run inference
    preds = model_best.predict(str(img_path), conf=0.25, verbose=False)[0]

    boxes  = preds.boxes
    n_det  = len(boxes)

    print(f"  Image : {img_path.name}")
    print(f"  Size  : {img.shape[1]}x{img.shape[0]}px")
    print(f"  Detections: {n_det}")

    det_by_class = {c: [] for c in class_names}
    for box in boxes:
        cls_id   = int(box.cls[0])
        conf_val = float(box.conf[0])
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
        cls_name = class_names[cls_id] if cls_id < len(class_names) else f"cls{cls_id}"
        det_by_class[cls_name].append((x1, y1, x2, y2, conf_val))

        # Draw on image
        color = class_colors.get(cls_name, (200, 200, 200))
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
        label = f"{cls_name} {conf_val:.2f}"
        cv2.putText(img, label, (x1, max(y1 - 8, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    # Per-class breakdown
    for cls_name, dets in det_by_class.items():
        if dets:
            confs = [d[4] for d in dets]
            avg_conf = sum(confs) / len(confs)
            print(f"    [{cls_name}] x{len(dets)}  avg_conf={avg_conf:.3f}")
            for d in dets:
                print(f"      bbox=({d[0]},{d[1]},{d[2]},{d[3]})  conf={d[4]:.3f}")

    print()

    # Save annotated image
    out_name = OUT_DIR / f"yolo_{img_path.stem}.jpg"
    cv2.imwrite(str(out_name), img)

# ── Step 5: Validation metrics ───────────────────────────────────────────────
print("\nStep 5: Validation metrics on 19 validation images:")
val_results = model_best.val(data=str(yaml_path), verbose=False)
mp  = val_results.box.mp   if hasattr(val_results.box, 'mp')  else None
mr  = val_results.box.mr   if hasattr(val_results.box, 'mr')  else None
map50 = val_results.box.map50 if hasattr(val_results.box, 'map50') else None

print(f"  mAP@0.50     : {map50:.4f}" if map50 is not None else "  mAP@0.50 : N/A")
print(f"  Precision    : {mp:.4f}"    if mp  is not None else "  Precision: N/A")
print(f"  Recall       : {mr:.4f}"    if mr  is not None else "  Recall   : N/A")

print(f"\n  Annotated result images saved to: yolov8_results/")
print("=" * 65)
print("YOLOv8 OMR real-world detection COMPLETE!")
