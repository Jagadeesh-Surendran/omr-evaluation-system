"""
omr_engine.py — Core OMR Processing Engine
-------------------------------------------
Functions:
  - four_point_transform      : perspective warp
  - _dynamic_row_threshold    : adaptive row spacing
  - detect_bubbles_raw        : find bubble contours
  - evaluate_omr              : grade a sheet against an answer key
  - extract_grid_data         : read numeric bubble grid (Student ID)
  - detect_form_type          : detect exam set A / B from top of sheet
"""

import cv2
import numpy as np
import imutils
from imutils import contours
from dl_model import predict_bubble_dl, predict_document_corners


# ── Perspective Transform ────────────────────────────────────────────────────

def four_point_transform(image, pts):
    """Warp and deskew a region defined by 4 corner points."""
    rect = _order_points(pts)
    (tl, tr, br, bl) = rect

    widthA  = np.linalg.norm(br - bl)
    widthB  = np.linalg.norm(tr - tl)
    maxW    = max(int(widthA), int(widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxH    = max(int(heightA), int(heightB))

    dst = np.array([[0, 0], [maxW - 1, 0],
                    [maxW - 1, maxH - 1], [0, maxH - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (maxW, maxH))


def _order_points(pts):
    pts = pts.reshape(4, 2).astype("float32")
    rect = np.zeros((4, 2), dtype="float32")
    s    = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


# ── Row Threshold ─────────────────────────────────────────────────────────────

def _dynamic_row_threshold(questionCnts):
    """
    Compute an adaptive vertical tolerance for grouping contours into rows.
    Returns a fixed default (10) for < 2 contours.
    """
    if len(questionCnts) < 2:
        return 10
    heights = [cv2.boundingRect(c)[3] for c in questionCnts]
    avg_h   = sum(heights) / len(heights)
    return avg_h * 0.7


# ── Bubble Detection ──────────────────────────────────────────────────────────

def detect_bubbles_raw(image):
    """
    Find bubble-shaped contours in an image.
    Returns a list of contours (may be empty).
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh_adapt = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    _, thresh_otsu = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
    )

    all_cnts = []
    for th in [thresh_adapt, thresh_otsu]:
        c = cv2.findContours(th.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        all_cnts.extend(imutils.grab_contours(c))

    questionCnts = []
    img_area = gray.shape[0] * gray.shape[1]
    min_area, max_area = img_area * 0.00005, img_area * 0.02

    seen_boxes = []
    for c in all_cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        ar   = w / float(max(h, 1))
        if min_area <= area <= max_area and 0.5 <= ar <= 2.0:
            is_dup = False
            for (sx, sy, sw, sh) in seen_boxes:
                if abs(x - sx) < w / 2 and abs(y - sy) < h / 2:
                    is_dup = True
                    break
            if not is_dup:
                questionCnts.append(c)
                seen_boxes.append((x, y, w, h))
    return questionCnts


# ── OMR Grading ───────────────────────────────────────────────────────────────

def evaluate_omr(image, answer_key, num_options=None):
    """
    Grade a single OMR sheet image against an answer key.

    Args:
        image       : BGR ndarray of the sheet (or a warped region)
        answer_key  : {q_idx_0based: option_idx_0based}  (or letter string)
        num_options : if provided, keep only the first N bubbles per row
                      (3 = A/B/C, 4 = A/B/C/D, 5 = A/B/C/D/E)
                      Default: auto-discovered from sheet.

    Returns:
        (question_details: list[dict], score_pct: float)
    """
    # 1. Align / Perspective Correction
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
    try:
        docCnt = predict_document_corners(image if len(image.shape) == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR))
        warped = four_point_transform(gray, docCnt)
    except Exception as e:
        print(f"[omr_engine] Corner detection failed ({e}). Using full image.")
        warped = gray

    # 2. Detect Bubbles
    questionCnts = detect_bubbles_raw(warped)
    if len(questionCnts) == 0:
        raise ValueError("No bubbles detected.")

    # 3. Sort and Group into rows
    questionCnts = contours.sort_contours(questionCnts, method="top-to-bottom")[0]
    row_threshold = _dynamic_row_threshold(questionCnts)

    rows = []
    current_row = [questionCnts[0]]
    for c in questionCnts[1:]:
        (_, y1, _, _) = cv2.boundingRect(current_row[-1])
        (_, y2, _, _) = cv2.boundingRect(c)
        if abs(y1 - y2) < row_threshold:
            current_row.append(c)
        else:
            rows.append(current_row)
            current_row = [c]
    rows.append(current_row)

    # 4. Grade
    correct         = 0
    total_questions = len(answer_key)
    question_details = []
    options_map      = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E'}

    for q_idx, row in enumerate(rows):
        if q_idx >= total_questions:
            break

        row = contours.sort_contours(row, method="left-to-right")[0]

        # Trim to num_options if specified
        if num_options is not None and len(row) > num_options:
            row = row[:num_options]

        bubbled    = None
        confidences = []

        for b_idx, c in enumerate(row):
            (x, y, w, h) = cv2.boundingRect(c)
            roi = warped[y:y + h, x:x + w]
            if roi.size == 0:
                confidences.append(0.0)
                continue
            prob = predict_bubble_dl(roi)
            confidences.append(float(prob))

        # Selection logic with MULTI-mark detection
        FILL_THRESHOLD = 0.30
        above_thresh   = [(i, p) for i, p in enumerate(confidences) if p >= FILL_THRESHOLD]

        marked_letter = None
        mark_status   = "BLANK"

        if len(above_thresh) == 0:
            mark_status = "BLANK"
        elif len(above_thresh) >= 2:
            above_sorted = sorted(above_thresh, key=lambda x: x[1], reverse=True)
            if above_sorted[0][1] - above_sorted[1][1] <= 0.15:
                mark_status = "MULTI"
            else:
                bubbled       = above_sorted[0][0]
                marked_letter = options_map.get(bubbled)
                mark_status   = marked_letter
        else:
            bubbled       = above_thresh[0][0]
            marked_letter = options_map.get(bubbled)
            mark_status   = marked_letter

        actual_answer        = answer_key[q_idx]
        correct_answer_letter = (
            options_map.get(actual_answer)
            if isinstance(actual_answer, int)
            else str(actual_answer).strip().upper()
        )

        is_correct = (
            mark_status not in ("BLANK", "MULTI")
            and mark_status == correct_answer_letter
        )
        if is_correct:
            correct += 1

        question_details.append({
            "question_number" : q_idx + 1,
            "marked_answer"   : mark_status,
            "correct_answer"  : correct_answer_letter,
            "selected_option" : mark_status,
            "actual_answer"   : correct_answer_letter,
            "is_correct"      : is_correct,
            "confidence"      : max(confidences) if confidences else 0.0
        })

    score_pct = (correct / total_questions) * 100 if total_questions > 0 else 0.0
    return question_details, score_pct


# ── Student ID Grid Reader ─────────────────────────────────────────────────────

def extract_grid_data(image, rows_n=10, cols_n=10):
    """
    Read a numeric bubble ID grid (e.g. student roll number).

    Layout assumption:
        - Rows = digit value 0..9  (top = 0, bottom = 9)
        - Columns = digit position (leftmost = first digit)

    Returns a string like "2301" or "" if no bubbles detected.
    """
    if image is None or image.size == 0:
        return ""

    all_cnts = detect_bubbles_raw(image)
    if not all_cnts:
        return ""

    # Get bounding boxes for every detected bubble
    boxes = []           # list of (x_center, y_center, x, y, w, h)
    for c in all_cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        boxes.append((x + w // 2, y + h // 2, x, y, w, h))

    if not boxes:
        return ""

    # ── 1. Cluster into columns by x_center ──────────────────────────────────
    boxes.sort(key=lambda b: b[0])   # sort by x
    # Estimate typical bubble width
    avg_w = sum(b[4] for b in boxes) / len(boxes)
    col_tol = avg_w * 0.7            # two bubbles in same column if x within this

    columns = []   # list of lists of boxes
    for box in boxes:
        placed = False
        for col in columns:
            if abs(box[0] - col[0][0]) < col_tol:
                col.append(box)
                placed = True
                break
        if not placed:
            columns.append([box])

    # ── 2. Within each column find the filled bubble → determine digit ────────
    # Cluster columns by y into rows_n rows to learn y_center of each digit
    all_y = sorted(set(round(b[1]) for b in boxes))
    row_centers = _cluster_y_centers(all_y, n_clusters=rows_n)  # len ≤ rows_n

    id_digits = []
    for col in sorted(columns, key=lambda c: c[0][0]):   # left-to-right
        best_prob = 0.0
        best_digit = None

        for box in col:
            cx, cy, x, y, w, h = box
            roi = image[y:y + h, x:x + w]
            if roi.size == 0:
                continue
            prob = predict_bubble_dl(roi)
            if prob > best_prob:
                best_prob  = prob
                # Map y_center to digit index
                dists = [abs(cy - rc) for rc in row_centers]
                best_digit = dists.index(min(dists)) % 10

        if best_prob > 0.35 and best_digit is not None:
            id_digits.append(str(best_digit))

    return "".join(id_digits) if id_digits else ""


def _cluster_y_centers(y_values, n_clusters=10):
    """Simple single-pass clustering of y values into up to n_clusters groups."""
    if not y_values:
        return []
    clusters = [[y_values[0]]]
    gap = (max(y_values) - min(y_values)) / max(n_clusters, 1) * 0.8
    for y in y_values[1:]:
        if abs(y - clusters[-1][-1]) < max(gap, 5):
            clusters[-1].append(y)
        else:
            clusters.append([y])
    return [sum(c) / len(c) for c in clusters[:n_clusters]]


# ── Exam Set A/B Detector ──────────────────────────────────────────────────────

def detect_form_type(image):
    """
    Detect exam set / form type (A or B) from the OMR sheet.

    Strategy:
      1. Scan the top 20% of the image for a 2-bubble row (FORM A / FORM B).
      2. The more darkly filled bubble determines the form type.
      3. Falls back to "UNKNOWN" if no clear result.

    Returns: "A", "B", or "UNKNOWN"
    """
    if image is None or image.size == 0:
        return "UNKNOWN"

    h, w = image.shape[:2]
    # Look in top 20% of the sheet
    top_region = image[:int(h * 0.22), :]

    cnts = detect_bubbles_raw(top_region)
    if not cnts:
        return "UNKNOWN"

    # Sort left-to-right
    cnts_sorted, _ = contours.sort_contours(cnts, method="left-to-right")

    # Score each bubble
    bubble_scores = []
    for c in cnts_sorted:
        (x, y, bw, bh) = cv2.boundingRect(c)
        roi = top_region[y:y + bh, x:x + bw]
        if roi.size == 0:
            continue
        prob = predict_bubble_dl(roi)
        bubble_scores.append((prob, x))

    if len(bubble_scores) < 2:
        # Only 1 bubble found — use x-position to distinguish A (left) vs B (right)
        if bubble_scores and bubble_scores[0][0] > 0.40:
            bx = bubble_scores[0][1]
            return "A" if bx < w * 0.5 else "B"
        return "UNKNOWN"

    # The first two left-to-right bubbles → A, B
    b1_prob, b1_x = bubble_scores[0]
    b2_prob, b2_x = bubble_scores[1]

    THRESH = 0.30
    if b1_prob >= THRESH and b2_prob < THRESH:
        return "A"
    elif b2_prob >= THRESH and b1_prob < THRESH:
        return "B"
    elif b1_prob >= THRESH and b2_prob >= THRESH:
        # Both marked — pick the more confidently filled one
        return "A" if b1_prob >= b2_prob else "B"
    return "UNKNOWN"
