"""
full_evaluator.py — Delegates to OMRPipeline (unified model coordinator)
-------------------------------------------------------------------------
This module is the backward-compatible entry point used by app.py.
All model coordination logic (YOLOv8 + BubbleCNN-V2 + CV heuristic) is
now centralised in pipeline.py / OMRPipeline.
"""

import os
import pandas as pd
from pathlib import Path
import sys

backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from pipeline import OMRPipeline


class FullOMREvaluator:
    """
    Backward-compatible wrapper around OMRPipeline.
    app.py uses this class — all logic is in OMRPipeline.

    Pipeline flow:
        FullOMREvaluator.process_sheet()
            → OMRPipeline._detect_regions()      [YOLOv8, adaptive conf]
            → OMRPipeline._extract_student_id()  [grid bubble → numeric ID]
            → OMRPipeline._grade_answers()
                → omr_engine.evaluate_omr()
                    → predict_bubble_dl()        [70% CNN + 30% CV ensemble]
    """

    def __init__(self):
        self._pipeline = OMRPipeline()

    def process_sheet(self, image_path, answer_key, num_options=None) -> dict:
        """
        Process a single OMR sheet image.

        Args:
            image_path  : path to the image file
            answer_key  : {q_idx_0based: option_idx_0based}
            num_options : bubbles per question (3/4/5); None = auto-discover
            conf        : ignored (pipeline uses adaptive confidence)

        Returns dict with keys: student_id, form_type, raw_score,
                                question_details, filename, regions_detected
        """
        return self._pipeline.process_sheet(str(image_path), answer_key,
                                            num_options=num_options)

    def generate_excel_report(self, all_results: list, output_path) -> str:
        """Write a summary Excel report. Delegates to OMRPipeline."""
        return self._pipeline.generate_excel_report(all_results, output_path)
