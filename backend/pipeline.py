"""
pipeline.py — Unified OMR Pipeline
------------------------------------
Single entry-point that owns and coordinates all three model components:

  1. YOLOv8        — detects labelled regions on the OMR sheet
                     (answer_region, sheet_id_region, personal_data, sign)
  2. BubbleCNN-V2  — deep-learning bubble classifier (trained model)
  3. CV Heuristic  — classical pixel-density fallback

Usage (from full_evaluator or app):
    from pipeline import OMRPipeline
    pipeline = OMRPipeline()                      # load all models once
    result   = pipeline.process_sheet(img_path, answer_key)

The pipeline is designed so that:
  - Accuracy is maximised via ensemble bubble scoring (70% CNN + 30% CV)
  - YOLO confidence adapts: tries 0.30 first, falls to 0.10 if no regions found
  - Full-image fallback when YOLO detects no answer region
"""

import os
import cv2
import numpy as np
from pathlib import Path
import sys

backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from dl_model import predict_bubble_dl, predict_document_corners
from omr_engine import evaluate_omr, extract_grid_data, four_point_transform, detect_form_type

# ── Model paths ───────────────────────────────────────────────────────────────
PROJECT_ROOT  = backend_dir.parent
YOLO_WEIGHTS  = PROJECT_ROOT / "yolov8_runs" / "omr_yolov8n" / "weights" / "best.pt"

# YOLO confidence search order — tries high confidence first, falls back if needed
YOLO_CONF_LEVELS = [0.30, 0.15, 0.10]

CLASS_NAMES = ["answer_region", "personal_data", "sheet_id_region", "sign"]


class OMRPipeline:
    """
    Unified pipeline that connects YOLOv8, BubbleCNN-V2, and CV Heuristic.

    Architecture:
        ┌─────────────────────────────────────────────────────┐
        │  Image                                              │
        │    ↓                                                │
        │  YOLOv8  ──► answer_region crop                     │
        │    │         (adaptive confidence: 0.30→0.15→0.10) │
        │    ↓                                                │
        │  omr_engine.evaluate_omr()                          │
        │    └─► per-bubble: predict_bubble_dl()              │
        │           └─► 0.70×BubbleCNNV2 + 0.30×CV heuristic │
        │    ↓                                                │
        │  Grade → question_details, score                    │
        └─────────────────────────────────────────────────────┘
    """

    def __init__(self):
        print("[OMRPipeline] Initialising models...")
        self._load_yolo()
        # CNN is lazy-loaded on first predict_bubble_dl() call
        print("[OMRPipeline] Ready.")

    # ── Model loading ─────────────────────────────────────────────────────────

    def _load_yolo(self):
        if not YOLO_WEIGHTS.exists():
            raise FileNotFoundError(
                f"YOLO weights not found at {YOLO_WEIGHTS}\n"
                "Train YOLO first or place weights at the expected path."
            )
        from ultralytics import YOLO
        self.yolo = YOLO(str(YOLO_WEIGHTS))
        print(f"[OMRPipeline] YOLOv8 loaded from {YOLO_WEIGHTS.name}")

    # ── Region detection ──────────────────────────────────────────────────────

    def _detect_regions(self, image: np.ndarray) -> dict:
        """
        Run YOLO with adaptive confidence.
        Tries each level in YOLO_CONF_LEVELS until at least 1 region is found.
        Returns dict {class_name: [(x1, y1, x2, y2), ...]}
        """
        regions = {name: [] for name in CLASS_NAMES}

        for conf in YOLO_CONF_LEVELS:
            results = self.yolo.predict(image, conf=conf, verbose=False)[0]
            regions = {name: [] for name in CLASS_NAMES}
            for box in results.boxes:
                cls_id = int(box.cls[0])
                if cls_id >= len(CLASS_NAMES):
                    continue
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
                regions[CLASS_NAMES[cls_id]].append((x1, y1, x2, y2))

            total = sum(len(v) for v in regions.values())
            if total > 0:
                print(f"  [YOLO] conf={conf:.2f} → detected: "
                      f"{ {k: len(v) for k, v in regions.items() if v} }")
                break
            else:
                print(f"  [YOLO] conf={conf:.2f} → no regions, retrying...")

        return regions

    # ── Student ID extraction ─────────────────────────────────────────────────

    def _extract_student_id(self, image: np.ndarray, regions: dict) -> str:
        if regions.get("sheet_id_region"):
            x1, y1, x2, y2 = regions["sheet_id_region"][0]
            roi = image[y1:y2, x1:x2]
            return extract_grid_data(roi) or "UNKNOWN"
        return "UNKNOWN"

    # ── Answer grading ────────────────────────────────────────────────────────

    def _grade_answers(self, image: np.ndarray, regions: dict,
                        answer_key: dict, num_options: int = None) -> tuple:
        """
        Grade using:
          1. answer_region crop (YOLO-detected) — preferred
          2. Full-image perspective-warp fallback

        Returns (question_details, score_pct)
        """
        if regions.get("answer_region"):
            x1, y1, x2, y2 = regions["answer_region"][0]
            roi = image[y1:y2, x1:x2]
            try:
                return evaluate_omr(roi, answer_key, num_options=num_options)
            except Exception as e:
                print(f"  [Pipeline] answer_region grading failed ({e}), falling back.")

        # Fallback: warp full image
        try:
            return evaluate_omr(image, answer_key, num_options=num_options)
        except Exception as e:
            print(f"  [Pipeline] Full-image grading failed: {e}")
            return [], 0.0

    # ── Public API ────────────────────────────────────────────────────────────

    def process_sheet(self, image_path: str, answer_key: dict,
                      num_options: int = None) -> dict:
        """
        Full pipeline:
          1. Load image
          2. Detect regions (YOLO, adaptive confidence)
          3. Detect exam set A/B (form_type)
          4. Extract student ID from sheet_id_region
          5. Grade answers using ensemble bubble scoring
          6. Return structured result dict

        Args:
            image_path  : absolute path to the OMR sheet image
            answer_key  : {question_index_0based: option_index_0based}
            num_options : number of options per question (3/4/5); None = auto

        Returns:
            {
              "student_id"       : str,
              "form_type"        : "A" | "B" | "UNKNOWN",
              "raw_score"        : float (0–100),
              "question_details" : list[dict],
              "filename"         : str,
              "regions_detected" : dict
            }
        """
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        print(f"\n[Pipeline] Processing: {Path(image_path).name}")

        # Step 1 — Detect all regions via YOLOv8
        regions = self._detect_regions(image)

        # Step 2 — Detect exam form type (A/B) from top of sheet
        form_type = detect_form_type(image)
        print(f"  Form type  : {form_type}")

        # Step 3 — Extract Student ID (from numeric grid bubble area)
        student_id = self._extract_student_id(image, regions)
        print(f"  Student ID : {student_id}")

        # Step 4 — Grade answer bubbles (CNN + CV ensemble)
        details, score = self._grade_answers(image, regions, answer_key,
                                             num_options=num_options)
        print(f"  Score      : {score:.1f}%  ({len(details)} questions graded)")

        return {
            "student_id"       : student_id,
            "form_type"        : form_type,
            "raw_score"        : score,
            "question_details" : details,
            "filename"         : Path(image_path).name,
            "regions_detected" : {k: len(v) for k, v in regions.items()},
        }

    def generate_excel_report(self, all_results: list, output_path) -> str:
        """Write a summary Excel report from a list of process_sheet (or export) results."""
        import pandas as pd
        rows = []
        for res in all_results:
            # Accept both key variants (id / student_id, score / raw_score)
            cand_id = res.get("student_id") or res.get("id", "")
            score   = res.get("raw_score")  if res.get("raw_score") is not None \
                      else res.get("score", 0)
            row = {
                "Filename"   : res.get("filename", ""),
                "Student ID" : cand_id,
                "Name"       : res.get("name", ""),
                "Score (%)"  : f"{score:.2f}%",
            }
            for qd in res.get("question_details", []):
                q = qd["question_number"]
                row[f"Q{q}_Marked"]  = qd.get("marked_answer", "?")
                row[f"Q{q}_Correct"] = qd.get("correct_answer", "?")
                row[f"Q{q}_OK"]      = "✓" if qd.get("is_correct") else "✗"
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_excel(str(output_path), index=False)
        print(f"[Pipeline] Excel report → {output_path}")
        return str(output_path)
