import os
import uuid
import json
import csv
import io
import traceback
import concurrent.futures
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
from werkzeug.utils import secure_filename

from flask_socketio import SocketIO, emit
from omr_engine import evaluate_omr
from ollama_client import extract_answer_key_from_image
from full_evaluator import FullOMREvaluator
from hardware_handler import OMRHardwareHandler
from session_manager import SessionManager
from answer_key_generator import AnswerKeyGenerator
from dashboard_analytics import DashboardAnalytics
from solver_logging_config import get_logger

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize AI Question Solver components
session_manager = SessionManager()
answer_key_generator = AnswerKeyGenerator()
dashboard_analytics = DashboardAnalytics()

# Initialize logger for API endpoints
api_logger = get_logger("api")


# ---------------------------------------------------------------------------
# Authentication and Authorization Middleware
# ---------------------------------------------------------------------------

def require_auth(f):
    """
    Decorator to require authentication for endpoints.
    
    For now, this is a placeholder that always allows access.
    In production, this should check for valid authentication tokens.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Implement actual authentication check
        # For now, we'll check for a simple API key in headers
        
        # Skip auth for development
        # In production, uncomment the following:
        # auth_header = request.headers.get('Authorization')
        # if not auth_header or not auth_header.startswith('Bearer '):
        #     return jsonify({
        #         "error": "Authentication required",
        #         "error_type": "auth_required"
        #     }), 401
        
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f):
    """
    Decorator to require admin privileges for endpoints.
    
    For now, this is a placeholder that always allows access.
    In production, this should check for admin role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Implement actual authorization check
        # For now, we'll check for a simple admin flag in headers
        
        # Skip auth for development
        # In production, uncomment the following:
        # auth_header = request.headers.get('Authorization')
        # if not auth_header:
        #     return jsonify({
        #         "error": "Authentication required",
        #         "error_type": "auth_required"
        #     }), 401
        #
        # # Check if user has admin role
        # # This would typically involve decoding a JWT token and checking roles
        # is_admin = request.headers.get('X-User-Role') == 'admin'
        # if not is_admin:
        #     return jsonify({
        #         "error": "Admin privileges required",
        #         "error_type": "insufficient_privileges"
        #     }), 403
        
        return f(*args, **kwargs)
    return decorated_function

def on_hardware_data(data):
    print(f"[App] Hardware Data Received, Emitting to frontend: {data}")
    with app.app_context():
        socketio.emit('new_omr_sheet', data)

hardware_handler = OMRHardwareHandler(callback=on_hardware_data)

# Error message templates for API responses
ERROR_MESSAGES = {
    "no_file": {
        "error": "No question paper file provided",
        "error_type": "missing_file",
        "suggestions": ["Please select a file to upload"]
    },
    "file_not_found": {
        "error": "The uploaded file could not be found",
        "error_type": "file_not_found",
        "suggestions": ["Try uploading the file again"]
    },
    "extraction_failed": {
        "error": "AI could not extract any answers from this file",
        "error_type": "extraction_failed",
        "suggestions": [
            "Ensure the image clearly shows question numbers and answers (e.g., Q1: A, Q2: C)",
            "Try uploading a higher resolution or clearer image",
            "Verify the answer key section is visible and not obscured",
            "If using a photo, ensure good lighting and focus"
        ]
    },
    "poor_quality": {
        "error": "Image quality is too low for reliable extraction",
        "error_type": "poor_quality",
        "suggestions": [
            "Use a scanner instead of a camera if possible",
            "Ensure good lighting when taking photos",
            "Hold the camera steady to avoid blur",
            "Try increasing image resolution"
        ]
    },
    "processing_error": {
        "error": "An error occurred while processing the file",
        "error_type": "processing_error",
        "suggestions": [
            "Verify the file is a valid image or PDF",
            "Try a different file format",
            "Check if the file is corrupted"
        ]
    }
}

# API Routes - Must be defined BEFORE catch-all route
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "EvalGenius AI Backend"}), 200


# ---------------------------------------------------------------------------
# Helper — parse the answer key CSV
# ---------------------------------------------------------------------------

def parse_answer_key_csv(csv_file):
    """
    Parse the answer key CSV.

    Accepted format (1-indexed question numbers):
        1,A
        2,B
        3,C
    or with a header row (case-insensitive), which is skipped automatically.

    Returns:
        dict  {question_index_0based: option_index_0based}

    Raises:
        ValueError if the CSV cannot be parsed or produces duplicate keys.
    """
    option_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}
    master_answer_key = {}
    seen_questions = set()

    df = pd.read_csv(csv_file, header=None, dtype=str)

    for _, row in df.iterrows():
        q_num = None
        letter = None

        for val in row.values:
            if val is None:
                continue
            val_str = str(val).strip().upper()

            # Skip header-like tokens
            if val_str in ('Q', 'QUESTION', 'ANS', 'ANSWER', 'NO', '#'):
                continue

            if q_num is None and val_str.isdigit():
                raw = int(val_str)
                if raw < 1:
                    continue  # invalid question number
                q_num = raw - 1  # convert to 0-based index

            if letter is None and val_str in option_map:
                letter = val_str

        if q_num is not None and letter is not None:
            if q_num in seen_questions:
                raise ValueError(
                    f"Duplicate question number {q_num + 1} found in the answer key CSV. "
                    f"Each question must appear exactly once."
                )
            seen_questions.add(q_num)
            master_answer_key[q_num] = option_map[letter]

    if not master_answer_key:
        raise ValueError(
            "Failed to parse Answer Key CSV. "
            "Ensure it has the format '1,A' (one question per row, 1-indexed)."
        )

    return master_answer_key


# ---------------------------------------------------------------------------
# Helper — compute real AI insights from question_details
# ---------------------------------------------------------------------------

def generate_insights(students, avg_score, highest_score):
    """
    Generate factual, data-driven insights instead of hardcoded strings.
    """
    insights = []

    # 1. Overall class performance
    if avg_score < 40:
        insights.append(f"Class average is very low ({avg_score}%). Fundamental concept review is strongly recommended.")
    elif avg_score < 60:
        insights.append(f"Class average is below passing ({avg_score}%). Consider additional practice sessions.")
    elif avg_score < 80:
        insights.append(f"Class average is satisfactory ({avg_score}%). There is room for improvement.")
    else:
        insights.append(f"Outstanding class performance! Class average: {avg_score}%.")

    # 2. Per-question error analysis
    question_error_counts = {}
    question_blank_counts = {}
    question_multi_counts = {}
    total_students = len(students)

    for student in students:
        for qd in student.get("question_details", []):
            qn = qd.get("question_number")
            if qn is None:
                continue
            if not qd.get("is_correct", False):
                question_error_counts[qn] = question_error_counts.get(qn, 0) + 1
            if qd.get("marked_answer") == "BLANK":
                question_blank_counts[qn] = question_blank_counts.get(qn, 0) + 1
            if qd.get("marked_answer") == "MULTI":
                question_multi_counts[qn] = question_multi_counts.get(qn, 0) + 1

    if question_error_counts:
        # Highest error question
        hardest_q = max(question_error_counts, key=question_error_counts.get)
        hardest_errors = question_error_counts[hardest_q]
        error_pct = round((hardest_errors / total_students) * 100)
        insights.append(
            f"Question {hardest_q} had the highest error rate: "
            f"{hardest_errors}/{total_students} students ({error_pct}%) answered it incorrectly."
        )

        # Questions where >50% of students were wrong
        hard_questions = [
            q for q, cnt in question_error_counts.items()
            if cnt / total_students > 0.5 and q != hardest_q
        ]
        if hard_questions:
            qs = ", ".join(f"Q{q}" for q in sorted(hard_questions)[:3])
            insights.append(f"Other difficult questions: {qs}. These topics may need revisiting.")

    # 3. Blank / multi-bubble issues
    total_blanks = sum(question_blank_counts.values())
    total_multis = sum(question_multi_counts.values())
    if total_blanks > 0:
        insights.append(f"{total_blanks} blank answer(s) detected — some students may have skipped questions.")
    if total_multis > 0:
        insights.append(
            f"{total_multis} multi-marked answer(s) detected — those responses were marked as wrong. "
            f"Advise students to erase clearly before re-marking."
        )

    # 4. Pass/fail split
    if total_students > 1:
        passed = sum(1 for s in students if s.get("score", 0) >= 50)
        failed = total_students - passed
        insights.append(f"Pass/Fail split (≥50%): {passed} passed, {failed} failed.")

    # 5. Top performer
    insights.append(f"Top performer scored {highest_score}%.")

    return insights


# ---------------------------------------------------------------------------
# Route — Evaluate OMR Sheets
# ---------------------------------------------------------------------------

from full_evaluator import FullOMREvaluator
evaluator = FullOMREvaluator()

@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    try:
        if 'omr_files' not in request.files:
            return jsonify({"error": "No OMR files uploaded"}), 400

        omr_files = request.files.getlist('omr_files')

        try:
            num_options = int(request.form.get('num_options', 5))  # Default to 5
            if num_options not in (3, 4, 5):
                num_options = 5
        except (ValueError, TypeError):
            num_options = 5

        multiplex_keys = {}
        if 'answer_keys_multiplex' in request.form:
            try:
                raw_mux = json.loads(request.form['answer_keys_multiplex'])
                # Convert all keys in all dictionaries to integers, skip null/non-dict sets
                for set_label, key_dict in raw_mux.items():
                    if key_dict and isinstance(key_dict, dict):
                        try:
                            multiplex_keys[set_label] = {int(k): v for k, v in key_dict.items()}
                        except (ValueError, TypeError) as conv_err:
                            print(f"[App] Warning: skipping set {set_label} key conversion: {conv_err}")
                master_answer_key = multiplex_keys.get("A") or multiplex_keys.get("B") or multiplex_keys.get("UNKNOWN")
            except Exception as e:
                return jsonify({"error": f"Invalid Multiplex JSON: {e}"}), 400
        elif 'answer_key_json' in request.form:
            try:
                master_answer_key = json.loads(request.form['answer_key_json'])
                master_answer_key = {int(k): v for k, v in master_answer_key.items()}
            except Exception as e:
                return jsonify({"error": f"Invalid JSON answer key: {e}"}), 400
        elif 'answer_key_csv' in request.files:
            try:
                master_answer_key = parse_answer_key_csv(request.files['answer_key_csv'])
            except ValueError as ve:
                return jsonify({"error": str(ve)}), 400
        else:
            return jsonify({"error": "Answer Key CSV or JSON is required"}), 400

        # Save files temporarily for processing
        temp_dir = os.path.join(os.getcwd(), 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)

        MAX_FILE_MB   = 20
        MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024

        results = []
        total_score = 0
        highest = 0
        saved_temps = []

        try:
            for idx, file in enumerate(omr_files):
                # Guard: file size
                file.seek(0, 2)  # seek to end
                file_size = file.tell()
                file.seek(0)
                if file_size > MAX_FILE_BYTES:
                    return jsonify({"error": f"File '{file.filename}' exceeds {MAX_FILE_MB}MB limit."}), 400

                temp_path = os.path.join(temp_dir, secure_filename(file.filename) or f"sheet_{idx}.jpg")
                file.save(temp_path)
                saved_temps.append(temp_path)

                try:
                    # Determine which answer key to use if multiplexed
                    current_key = master_answer_key
                    
                    # Initial process to detect form_type
                    eval_res = evaluator.process_sheet(temp_path, current_key, num_options=num_options)
                    
                    # If multiplexed and form_type changed, re-grade!
                    form_type = eval_res.get("form_type", "UNKNOWN")
                    if multiplex_keys and form_type in multiplex_keys and multiplex_keys[form_type] != current_key:
                        print(f"  [App] Sheet {idx}: Detected {form_type}, switching key and re-grading.")
                        eval_res = evaluator.process_sheet(temp_path, multiplex_keys[form_type], num_options=num_options)
                    
                    score     = eval_res['raw_score']
                    q_details = eval_res.get('question_details', [])
                    cand_id   = eval_res.get('student_id', f"CAND-{1000 + idx}")
                    form_type = eval_res.get('form_type', 'UNKNOWN')
                except Exception as e:
                    print(f"Error evaluating '{file.filename}': {e}")
                    traceback.print_exc()
                    score, q_details, cand_id, form_type = 0, [], f"ERR-{1000+idx}", 'UNKNOWN'

                total_score += score
                if score > highest:
                    highest = score

                results.append({
                    "id":               cand_id,
                    "student_id":       cand_id,
                    "name":             f"Student ({cand_id})",
                    "score":            round(score, 2),
                    "raw_score":        round(score, 2),
                    "form_type":        form_type,
                    "question_details": q_details,
                    "filename":         file.filename
                })
        finally:
            # Always remove temp files — even if an exception occurred
            for p in saved_temps:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass

        avg_score = round(total_score / len(omr_files), 2) if omr_files else 0
        insights = generate_insights(results, avg_score, highest)

        return jsonify({
            "total_processed": len(omr_files),
            "average_score": avg_score,
            "highest_score": highest,
            "students": results,
            "insights": insights
        })

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Route — Evaluate Single Sheet (for per-file frontend progress)
# ---------------------------------------------------------------------------

@app.route('/api/evaluate_single', methods=['POST'])
def evaluate_single():
    """Process ONE OMR sheet. Frontend calls this per-file to show live progress."""
    try:
        if 'omr_file' not in request.files:
            return jsonify({"error": "No OMR file uploaded"}), 400

        file = request.files['omr_file']

        multiplex_keys = {}
        if 'answer_keys_multiplex' in request.form:
            try:
                raw_mux = json.loads(request.form['answer_keys_multiplex'])
                for set_label, key_dict in raw_mux.items():
                    if key_dict and isinstance(key_dict, dict):
                        try:
                            multiplex_keys[set_label] = {int(k): v for k, v in key_dict.items()}
                        except (ValueError, TypeError) as conv_err:
                            print(f"[App] Warning: skipping set {set_label} key conversion: {conv_err}")
                master_answer_key = multiplex_keys.get("A") or multiplex_keys.get("B") or multiplex_keys.get("UNKNOWN")
            except Exception as e:
                return jsonify({"error": f"Invalid Multiplex JSON: {e}"}), 400
        elif 'answer_key_json' in request.form:
            try:
                master_answer_key = json.loads(request.form['answer_key_json'])
                master_answer_key = {int(k): v for k, v in master_answer_key.items()}
            except Exception as e:
                return jsonify({"error": f"Invalid JSON answer key: {e}"}), 400
        elif 'answer_key_csv' in request.files:
            try:
                master_answer_key = parse_answer_key_csv(request.files['answer_key_csv'])
            except ValueError as ve:
                return jsonify({"error": str(ve)}), 400
        else:
            return jsonify({"error": "Answer Key CSV or JSON is required"}), 400

        try:
            num_options = int(request.form.get('num_options', 5))  # Default to 5
            if num_options not in (3, 4, 5): num_options = 5
        except (ValueError, TypeError):
            num_options = 5
        try:
            index = int(request.form.get('index', 0))
        except (ValueError, TypeError):
            index = 0

        file.seek(0, 2); file_size = file.tell(); file.seek(0)
        if file_size > 20 * 1024 * 1024:
            return jsonify({"error": f"File '{file.filename}' exceeds 20MB."}), 400

        temp_dir  = os.path.join(os.getcwd(), 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, secure_filename(file.filename) or f"sheet_{index}.jpg")

        try:
            file.save(temp_path)
            
            # Initial grade with default key
            eval_res  = evaluator.process_sheet(temp_path, master_answer_key, num_options=num_options)
            
            # Re-grade if set is different and we have a key for it
            form_type = eval_res.get('form_type', 'UNKNOWN')
            if multiplex_keys and form_type in multiplex_keys and multiplex_keys[form_type] != master_answer_key:
                eval_res = evaluator.process_sheet(temp_path, multiplex_keys[form_type], num_options=num_options)
                form_type = eval_res.get('form_type', 'UNKNOWN')

            score     = round(eval_res['raw_score'], 2)
            q_details = eval_res.get('question_details', [])
            cand_id   = eval_res.get('student_id', f"CAND-{1000 + index}")
        except Exception as e:
            print(f"evaluate_single error: {e}"); traceback.print_exc()
            score, q_details, cand_id, form_type = 0.0, [], f"ERR-{1000+index}", 'UNKNOWN'
        finally:
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except Exception: pass

        return jsonify({
            "id": cand_id, "student_id": cand_id,
            "name": f"Student ({cand_id})",
            "score": score, "raw_score": score,
            "form_type": form_type,
            "question_details": q_details,
            "filename": file.filename,
            "index": index
        })
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Route — Extract Answer Key from Question Paper (AI)
# ---------------------------------------------------------------------------

@app.route('/api/extract_key', methods=['POST'])
def extract_key():
    """
    Extract answer key from a question paper image using Ollama with enhanced error handling.
    
    HTTP Status Codes:
    - 200: Success with extracted answers
    - 400: Bad request (no file provided)
    - 404: File not found
    - 422: Extraction failed (no answers found)
    - 500: Server error
    
    Response Format (Success):
    {
        "success": true,
        "answer_key": {"1": "A", "2": "C", ...},
        "count": 25,
        "warnings": ["Only 3 answers extracted (< 5)"],
        "processing_time_ms": 2502
    }
    
    Response Format (Error):
    {
        "error": "Detailed error message",
        "error_type": "extraction_failed",
        "suggestions": [
            "Ensure the image clearly shows question numbers",
            "Try uploading a higher resolution image"
        ]
    }
    """
    import time
    start_time = time.time()
    
    try:
        # Check if file was provided
        if 'qp_file' not in request.files:
            return jsonify(ERROR_MESSAGES["no_file"]), 400

        file = request.files['qp_file']
        
        # Validate file has a filename
        if not file.filename:
            return jsonify(ERROR_MESSAGES["no_file"]), 400
        
        temp_dir = os.path.join(os.getcwd(), 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"qp_{uuid.uuid4().hex}_{secure_filename(file.filename)}")
        
        try:
            # Save the uploaded file
            file.save(temp_path)
            
            # Verify file was saved successfully
            if not os.path.exists(temp_path):
                return jsonify(ERROR_MESSAGES["file_not_found"]), 404
            
            try:
                # Get optional expected question count from form data
                expected_count = request.form.get('expected_count')
                expected_count = int(expected_count) if expected_count and expected_count.isdigit() else None
                
                # Create config with expected count if provided
                from ollama_client import ExtractionConfig
                config = ExtractionConfig(expected_question_count=expected_count) if expected_count else None
                
                # Extract answer key with metadata
                extracted_key, warnings, processing_time_ms = extract_answer_key_from_image(temp_path, config=config)
            except FileNotFoundError as fnf:
                # File not found error (404)
                return jsonify(ERROR_MESSAGES["file_not_found"]), 404
            except Exception as extraction_error:
                # Log the error for debugging
                print(f"Extraction error: {extraction_error}")
                print(traceback.format_exc())
                
                # Check if it's an Ollama connection error
                if "ollama" in str(extraction_error).lower() or "connection" in str(extraction_error).lower():
                    return jsonify({
                        "error": "Could not connect to Ollama AI service",
                        "error_type": "service_unavailable",
                        "suggestions": [
                            "Ensure Ollama is installed and running",
                            "Try running 'ollama serve' in a terminal",
                            "Check if the moondream model is available"
                        ]
                    }), 500
                
                # Generic processing error
                return jsonify(ERROR_MESSAGES["processing_error"]), 500

            # Check if extraction returned any results
            if not extracted_key:
                # Extraction failed - no answers found (422)
                return jsonify(ERROR_MESSAGES["extraction_failed"]), 422

            # Success response with metadata
            return jsonify({
                "success": True,
                "answer_key": extracted_key,
                "count": len(extracted_key),
                "warnings": warnings if warnings else [],
                "processing_time_ms": round(processing_time_ms, 2)
            }), 200
            
        finally:
            # Always cleanup temporary file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as cleanup_error:
                    print(f"Warning: Could not remove temp file {temp_path}: {cleanup_error}")
                
    except Exception as e:
        # Unexpected server error (500)
        print(f"Unexpected error in extract_key endpoint: {e}")
        print(traceback.format_exc())
        return jsonify({
            "error": "An unexpected error occurred while processing the file",
            "error_type": "server_error",
            "suggestions": [
                "Try uploading the file again",
                "Verify the file is not corrupted",
                "Contact support if the problem persists"
            ]
        }), 500


# ---------------------------------------------------------------------------
# Route — Link Student Database (sequential CSV name mapping)
# ---------------------------------------------------------------------------

@app.route('/api/link_db', methods=['POST'])
def link_db():
    """
    Maps student names from a CSV to the result list by row position.

    CSV format (with or without header):
        Roll Number, Name
        1, Alice Sharma
        2, Bob Patel

    This is the correct approach when we don't yet have roll-number OCR.
    Sequential mapping is valid when sheets are uploaded in the same order
    as the student list.
    """
    try:
        if 'db_file' not in request.files:
            return jsonify({"error": "No database CSV file provided."}), 400

        db_file = request.files['db_file']
        current_results_raw = request.form.get('current_results', '[]')

        try:
            current_results = json.loads(current_results_raw)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid results data sent from frontend."}), 400

        if not current_results:
            return jsonify({"error": "No results to link. Process OMR sheets first."}), 400

        # Parse the student DB CSV
        df = pd.read_csv(db_file, header=None, dtype=str)
        student_names = []

        for _, row in df.iterrows():
            # Look for the longest non-numeric, non-empty cell in the row (= the name)
            name_candidate = None
            for val in row.values:
                if val is None:
                    continue
                val_str = str(val).strip()
                if val_str == '' or val_str.upper() in ('NAME', 'STUDENT', 'ROLL', 'NO', '#'):
                    continue
                if not val_str.replace('.', '', 1).isdigit():
                    # Not purely numeric — treat as a name
                    if name_candidate is None or len(val_str) > len(name_candidate):
                        name_candidate = val_str

            if name_candidate:
                student_names.append(name_candidate)

        if not student_names:
            return jsonify({"error": "No student names could be parsed from the database CSV."}), 400

        # Sequential mapping: match by position
        updated_results = []
        for i, result in enumerate(current_results):
            result_copy = result.copy()
            if i < len(student_names):
                result_copy['name'] = student_names[i]
            updated_results.append(result_copy)

        linked = min(len(student_names), len(current_results))
        return jsonify({
            "students": updated_results,
            "message": f"Successfully linked {linked} student name(s) by row position."
        })

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Route — Export Results as CSV
# ---------------------------------------------------------------------------

@app.route('/api/export', methods=['POST'])
def export_results():
    """Converts a JSON payload of student results into a downloadable file."""
    try:
        data = request.json
        format_type = request.args.get('format', 'csv').lower()
        
        if not data or 'results' not in data:
            return jsonify({"error": "No results provided for export."}), 400

        if format_type == 'excel':
            # Use FullOMREvaluator's Excel logic
            temp_xls = os.path.join(os.getcwd(), 'omr_results.xlsx')
            evaluator.generate_excel_report(data['results'], temp_xls)
            
            with open(temp_xls, 'rb') as f:
                output = f.read()
            
            os.remove(temp_xls)
            return output, 200, {
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'Content-Disposition': 'attachment; filename=omr_results.xlsx'
            }
        else:
            # Traditional CSV
            si = io.StringIO()
            cw = csv.writer(si)
            cw.writerow(['Candidate ID', 'Name', 'Score (%)', 'Filename'])

            for student in data['results']:
                cw.writerow([
                    student.get('id', 'N/A'),
                    student.get('name', 'N/A'),
                    student.get('score', 0),
                    student.get('filename', 'N/A')
                ])

            output = si.getvalue()
            return output, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename=omr_results.csv'
            }

    except Exception as e:
        print(f"Export Error: {e}")
        return jsonify({"error": "Failed to generate export file."}), 500


# ---------------------------------------------------------------------------
# Machine Control Endpoints
# ---------------------------------------------------------------------------

@app.route('/api/machine/connect', methods=['POST'])
def machine_connect():
    data = request.json or {}
    port = data.get('port', 'COM3')
    baud = data.get('baudrate', 9600)
    success, msg = hardware_handler.connect(port, baud)
    if success:
        return jsonify({"status": "connected", "message": msg}), 200
    else:
        return jsonify({"status": "error", "message": msg}), 400

@app.route('/api/machine/disconnect', methods=['POST'])
def machine_disconnect():
    hardware_handler.disconnect()
    return jsonify({"status": "disconnected"}), 200

@app.route('/api/machine/simulate', methods=['POST'])
def machine_simulate():
    data = request.json or {}
    enable = data.get('enable', True)
    if enable:
        hardware_handler.start_simulation()
    else:
        hardware_handler.disconnect()
    return jsonify({"status": "simulation_started" if enable else "stopped"}), 200

# ---------------------------------------------------------------------------
# Route — Batch Evaluate (parallel, one call for all sheets)
# ---------------------------------------------------------------------------

@app.route('/api/evaluate_batch', methods=['POST'])
def evaluate_batch():
    """
    Process ALL uploaded OMR sheets in parallel using ThreadPoolExecutor.
    Returns results for every sheet in a single response — much faster than
    sequential per-sheet calls when many sheets are uploaded at once.
    """
    try:
        if 'omr_files' not in request.files:
            return jsonify({"error": "No OMR files uploaded"}), 400

        omr_files = request.files.getlist('omr_files')

        try:
            num_options = int(request.form.get('num_options', 5))
            if num_options not in (3, 4, 5):
                num_options = 5
        except (ValueError, TypeError):
            num_options = 5

        multiplex_keys = {}
        if 'answer_keys_multiplex' in request.form:
            try:
                raw_mux = json.loads(request.form['answer_keys_multiplex'])
                for set_label, key_dict in raw_mux.items():
                    if key_dict and isinstance(key_dict, dict):
                        try:
                            multiplex_keys[set_label] = {int(k): v for k, v in key_dict.items()}
                        except (ValueError, TypeError):
                            pass
                master_answer_key = (
                    multiplex_keys.get("A")
                    or multiplex_keys.get("B")
                    or multiplex_keys.get("UNKNOWN")
                )
            except Exception as e:
                return jsonify({"error": f"Invalid Multiplex JSON: {e}"}), 400
        elif 'answer_key_json' in request.form:
            try:
                master_answer_key = json.loads(request.form['answer_key_json'])
                master_answer_key = {int(k): v for k, v in master_answer_key.items()}
            except Exception as e:
                return jsonify({"error": f"Invalid JSON answer key: {e}"}), 400
        elif 'answer_key_csv' in request.files:
            try:
                master_answer_key = parse_answer_key_csv(request.files['answer_key_csv'])
            except ValueError as ve:
                return jsonify({"error": str(ve)}), 400
        else:
            return jsonify({"error": "Answer Key CSV or JSON is required"}), 400

        # Save all temp files up-front
        temp_dir = os.path.join(os.getcwd(), 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)

        MAX_FILE_BYTES = 20 * 1024 * 1024
        temp_paths     = []
        file_names     = []

        for idx, file in enumerate(omr_files):
            file.seek(0, 2); size = file.tell(); file.seek(0)
            if size > MAX_FILE_BYTES:
                return jsonify({"error": f"File '{file.filename}' exceeds 20 MB."}), 400
            fname = secure_filename(file.filename) or f"sheet_{idx}.jpg"
            tp = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{fname}")
            file.save(tp)
            temp_paths.append(tp)
            file_names.append(file.filename)

        # ── Process all sheets in parallel ────────────────────────────────
        def _process_one(args):
            idx, temp_path, filename = args
            try:
                current_key = master_answer_key
                res = evaluator.process_sheet(temp_path, current_key, num_options=num_options)
                form_type = res.get("form_type", "UNKNOWN")
                if multiplex_keys and form_type in multiplex_keys and multiplex_keys[form_type] != current_key:
                    res = evaluator.process_sheet(temp_path, multiplex_keys[form_type], num_options=num_options)
                    form_type = res.get("form_type", "UNKNOWN")
                score    = res['raw_score']
                q_detail = res.get('question_details', [])
                cand_id  = res.get('student_id', f"CAND-{1000 + idx}")
            except Exception as e:
                print(f"[Batch] Error on '{filename}': {e}")
                traceback.print_exc()
                score, q_detail, cand_id, form_type = 0, [], f"ERR-{1000+idx}", "UNKNOWN"
            return {
                "id":               cand_id,
                "student_id":       cand_id,
                "name":             f"Student ({cand_id})",
                "score":            round(score, 2),
                "raw_score":        round(score, 2),
                "form_type":        form_type,
                "question_details": q_detail,
                "filename":         filename,
                "index":            idx,
            }

        # Use up to 4 threads — more doesn't help since the model is CPU-bound
        max_workers = min(4, len(temp_paths))
        results = [None] * len(temp_paths)
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {
                    pool.submit(_process_one, (i, tp, fn)): i
                    for i, (tp, fn) in enumerate(zip(temp_paths, file_names))
                }
                for future in concurrent.futures.as_completed(futures):
                    i = futures[future]
                    try:
                        results[i] = future.result()
                    except Exception as exc:
                        results[i] = {
                            "id": f"ERR-{1000+i}", "student_id": f"ERR-{1000+i}",
                            "name": f"Error ({file_names[i]})",
                            "score": 0, "raw_score": 0,
                            "form_type": "UNKNOWN", "question_details": [],
                            "filename": file_names[i], "index": i,
                        }
        finally:
            for tp in temp_paths:
                try:
                    if os.path.exists(tp): os.remove(tp)
                except Exception:
                    pass

        # Filter out any None slots (shouldn't happen)
        results = [r for r in results if r is not None]

        total_score  = sum(r['score'] for r in results)
        highest      = max((r['score'] for r in results), default=0)
        avg_score    = round(total_score / len(results), 2) if results else 0
        insights     = generate_insights(results, avg_score, highest)

        return jsonify({
            "total_processed": len(results),
            "average_score":   avg_score,
            "highest_score":   highest,
            "students":        results,
            "insights":        insights,
        })

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# AI Question Solver Endpoints
# ---------------------------------------------------------------------------

@app.route('/api/solve/upload', methods=['POST'])
@require_auth
def solve_upload():
    """
    Upload PDF and start solver session.
    
    Request:
        - qp_file: PDF file containing questions
        
    Response:
        {
            "session_id": "uuid",
            "status": "pending",
            "message": "Session created successfully"
        }
    """
    try:
        api_logger.info("[API] Received PDF upload request")
        
        # Check if file was provided
        if 'qp_file' not in request.files:
            api_logger.warning("[API] Upload request missing file")
            return jsonify({
                "error": "No question paper file provided",
                "error_type": "missing_file"
            }), 400
        
        file = request.files['qp_file']
        
        # Validate file has a filename
        if not file.filename:
            api_logger.warning("[API] Upload request has empty filename")
            return jsonify({
                "error": "No question paper file provided",
                "error_type": "missing_file"
            }), 400
        
        api_logger.info(f"[API] Processing upload: {file.filename}")
        
        # Check Ollama service availability
        try:
            from ollama_client import OllamaClient
            ollama_client = OllamaClient()
            # Simple check - try to list models
            # If this fails, Ollama is not available
            api_logger.debug("[API] Checking Ollama service availability")
        except Exception as e:
            api_logger.error(f"[API] Ollama service unavailable: {e}")
            return jsonify({
                "error": "Ollama AI service is not available",
                "error_type": "service_unavailable",
                "suggestions": [
                    "Ensure Ollama is installed and running",
                    "Try running 'ollama serve' in a terminal"
                ]
            }), 503
        
        # Save uploaded file temporarily
        temp_dir = os.path.join(os.getcwd(), 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"qp_{uuid.uuid4().hex}_{secure_filename(file.filename)}")
        
        try:
            file.save(temp_path)
            api_logger.info(f"[API] Saved uploaded file to: {temp_path}")
            
            # Create new session
            session_id = session_manager.create_session(temp_path)
            api_logger.info(f"[API] Created session: {session_id}")
            
            # Start processing in background
            session_manager.start_processing(session_id)
            api_logger.info(f"[API] Started processing for session: {session_id}")
            
            return jsonify({
                "session_id": session_id,
                "status": "processing",
                "message": "Session created and processing started"
            }), 200
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    api_logger.debug(f"[API] Cleaned up temp file: {temp_path}")
                except Exception:
                    pass
            raise
            
    except Exception as e:
        api_logger.error(f"[API] Error in solve_upload: {e}")
        api_logger.error(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "error_type": "processing_error"
        }), 500


@app.route('/api/solve/session/<session_id>', methods=['GET'])
@require_auth
def solve_session_status(session_id):
    """
    Get session status and results.
    
    Response:
        {
            "session_id": "uuid",
            "status": "processing|completed|paused|cancelled|error",
            "total_questions": 100,
            "processed_count": 45,
            "solved_count": 42,
            "unsolvable_count": 2,
            "error_count": 1,
            "average_confidence": 0.82,
            "questions": [...],
            "results": {...},
            "validation_report": {...}
        }
    """
    try:
        api_logger.info(f"[API] Session status request for: {session_id}")
        
        # Get session
        session = session_manager.get_session(session_id)
        
        if not session:
            api_logger.warning(f"[API] Session not found: {session_id}")
            return jsonify({
                "error": f"Session {session_id} not found",
                "error_type": "not_found"
            }), 404
        
        api_logger.debug(f"[API] Session {session_id} status: {session.status}, processed: {session.processed_count}/{session.total_questions}")
        
        # Calculate average confidence
        average_confidence = 0.0
        if session.results:
            confidence_scores = [
                r.confidence for r in session.results.values()
                if r.status == "solved"
            ]
            if confidence_scores:
                average_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # Build response
        response = {
            "session_id": session.session_id,
            "status": session.status,
            "total_questions": session.total_questions,
            "processed_count": session.processed_count,
            "solved_count": session.solved_count,
            "unsolvable_count": session.unsolvable_count,
            "error_count": session.error_count,
            "average_confidence": round(average_confidence, 2),
            "start_time": session.start_time,
            "end_time": session.end_time
        }
        
        # Include questions if available
        if session.questions:
            response["questions"] = [
                {
                    "number": q.number,
                    "text": q.text,
                    "options": [
                        {"label": opt.label, "text": opt.text}
                        for opt in q.options
                    ],
                    "page_number": q.page_number,
                    "question_type": q.question_type
                }
                for q in session.questions
            ]
        
        # Include results if available
        if session.results:
            response["results"] = {
                str(qnum): {
                    "question_number": result.question_number,
                    "selected_option": result.selected_option,
                    "explanation": result.explanation,
                    "confidence": result.confidence,
                    "status": result.status,
                    "error_message": result.error_message
                }
                for qnum, result in session.results.items()
            }
        
        # Include validation report if available
        if session.validation_report:
            response["validation_report"] = {
                "total_questions": session.validation_report.total_questions,
                "issues": [
                    {
                        "question_number": issue.question_number,
                        "severity": issue.severity,
                        "issue_type": issue.issue_type,
                        "description": issue.description
                    }
                    for issue in session.validation_report.issues
                ],
                "flagged_questions": list(session.validation_report.flagged_questions),
                "average_confidence": session.validation_report.average_confidence
            }
        
        # Include user corrections and notes
        response["user_corrections"] = session.user_corrections
        response["user_notes"] = session.user_notes
        
        api_logger.info(f"[API] Returning session status for: {session_id}")
        return jsonify(response), 200
        
    except Exception as e:
        api_logger.error(f"[API] Error in solve_session_status: {e}")
        api_logger.error(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "error_type": "processing_error"
        }), 500


@app.route('/api/solve/session/<session_id>/pause', methods=['POST'])
@require_auth
def solve_session_pause(session_id):
    """
    Pause active session.
    
    Response:
        {
            "success": true,
            "message": "Session paused successfully"
        }
    """
    try:
        success = session_manager.pause_session(session_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Session paused successfully"
            }), 200
        else:
            return jsonify({
                "error": "Failed to pause session",
                "error_type": "operation_failed"
            }), 400
            
    except Exception as e:
        print(f"Error in solve_session_pause: {e}")
        print(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "error_type": "processing_error"
        }), 500


@app.route('/api/solve/session/<session_id>/resume', methods=['POST'])
@require_auth
def solve_session_resume(session_id):
    """
    Resume paused session.
    
    Response:
        {
            "success": true,
            "message": "Session resumed successfully"
        }
    """
    try:
        success = session_manager.resume_session(session_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Session resumed successfully"
            }), 200
        else:
            return jsonify({
                "error": "Failed to resume session",
                "error_type": "operation_failed"
            }), 400
            
    except Exception as e:
        print(f"Error in solve_session_resume: {e}")
        print(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "error_type": "processing_error"
        }), 500


@app.route('/api/solve/session/<session_id>/cancel', methods=['POST'])
@require_auth
def solve_session_cancel(session_id):
    """
    Cancel session and discard results.
    
    Response:
        {
            "success": true,
            "message": "Session cancelled successfully"
        }
    """
    try:
        success = session_manager.cancel_session(session_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Session cancelled successfully"
            }), 200
        else:
            return jsonify({
                "error": "Failed to cancel session",
                "error_type": "operation_failed"
            }), 400
            
    except Exception as e:
        print(f"Error in solve_session_cancel: {e}")
        print(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "error_type": "processing_error"
        }), 500


@app.route('/api/solve/session/<session_id>/answer/<int:question_num>', methods=['PUT'])
@require_auth
def solve_update_answer(session_id, question_num):
    """
    Update specific answer (manual correction).
    
    Request:
        {
            "answer": "A|B|C|D|E"
        }
        
    Response:
        {
            "success": true,
            "message": "Answer updated successfully"
        }
    """
    try:
        data = request.json
        
        if not data or 'answer' not in data:
            return jsonify({
                "error": "Answer option is required",
                "error_type": "missing_parameter"
            }), 400
        
        new_answer = data['answer'].upper()
        
        # Validate answer option
        if new_answer not in ['A', 'B', 'C', 'D', 'E']:
            return jsonify({
                "error": f"Invalid answer option: {new_answer}. Must be A, B, C, D, or E",
                "error_type": "invalid_parameter"
            }), 400
        
        success = session_manager.update_answer(session_id, question_num, new_answer)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Answer for question {question_num} updated to {new_answer}"
            }), 200
        else:
            return jsonify({
                "error": "Failed to update answer",
                "error_type": "operation_failed"
            }), 400
            
    except Exception as e:
        print(f"Error in solve_update_answer: {e}")
        print(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "error_type": "processing_error"
        }), 500


@app.route('/api/solve/session/<session_id>/note/<int:question_num>', methods=['PUT'])
@require_auth
def solve_add_note(session_id, question_num):
    """
    Add or update note for specific question.
    
    Request:
        {
            "note": "User note text"
        }
        
    Response:
        {
            "success": true,
            "message": "Note saved successfully"
        }
    """
    try:
        data = request.json
        
        if not data or 'note' not in data:
            return jsonify({
                "error": "Note text is required",
                "error_type": "missing_parameter"
            }), 400
        
        note = data['note']
        
        success = session_manager.add_note(session_id, question_num, note)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Note for question {question_num} saved successfully"
            }), 200
        else:
            return jsonify({
                "error": "Failed to save note",
                "error_type": "operation_failed"
            }), 400
            
    except Exception as e:
        print(f"Error in solve_add_note: {e}")
        print(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "error_type": "processing_error"
        }), 500


@app.route('/api/solve/session/<session_id>/approve', methods=['POST'])
@require_auth
@require_admin
def solve_approve_answer_key(session_id):
    """
    Approve and finalize answer key.
    
    Request:
        {
            "user_id": "admin_user"
        }
        
    Response:
        {
            "success": true,
            "message": "Answer key approved successfully"
        }
    """
    try:
        data = request.json or {}
        user_id = data.get('user_id', 'unknown')
        
        # TODO: Add authentication and authorization checks
        # For now, we'll accept any user_id
        
        # Get session to verify it exists and is completed
        session = session_manager.get_session(session_id)
        
        if not session:
            return jsonify({
                "error": f"Session {session_id} not found",
                "error_type": "not_found"
            }), 404
        
        # Check if session is completed
        if session.status != "completed":
            return jsonify({
                "error": f"Cannot approve session with status '{session.status}'. Session must be completed.",
                "error_type": "invalid_status"
            }), 400
        
        # Check if all flagged questions have been reviewed
        if session.validation_report:
            flagged_questions = session.validation_report.flagged_questions
            # Check if any flagged questions don't have user corrections or notes
            unreviewed = [
                q for q in flagged_questions
                if q not in session.user_corrections and q not in session.user_notes
            ]
            
            if unreviewed:
                return jsonify({
                    "error": f"Cannot approve: {len(unreviewed)} flagged questions have not been reviewed",
                    "error_type": "validation_required",
                    "unreviewed_questions": unreviewed
                }), 400
        
        # Approve the answer key
        success = answer_key_generator.approve_answer_key(session_id, user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Answer key approved successfully",
                "approved_by": user_id
            }), 200
        else:
            return jsonify({
                "error": "Failed to approve answer key (may already be approved)",
                "error_type": "operation_failed"
            }), 400
            
    except Exception as e:
        print(f"Error in solve_approve_answer_key: {e}")
        print(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "error_type": "processing_error"
        }), 500


@app.route('/api/solve/session/<session_id>/export', methods=['GET'])
@require_auth
def solve_export_answer_key(session_id):
    """
    Export answer key in specified format.
    
    Query Parameters:
        format: json|csv|pdf (default: json)
        
    Response:
        - JSON: application/json
        - CSV: text/csv
        - PDF: application/pdf (currently text/plain)
    """
    try:
        format_type = request.args.get('format', 'json').lower()
        
        # Get session
        session = session_manager.get_session(session_id)
        
        if not session:
            return jsonify({
                "error": f"Session {session_id} not found",
                "error_type": "not_found"
            }), 404
        
        # Check if session has results
        if not session.results:
            return jsonify({
                "error": "Session has no results to export",
                "error_type": "no_results"
            }), 400
        
        if format_type == 'json':
            # Generate JSON answer key
            answer_key_data = answer_key_generator.generate_json(session)
            return jsonify(answer_key_data), 200
            
        elif format_type == 'csv':
            # Generate CSV export
            csv_content = answer_key_generator.generate_csv(session)
            return csv_content, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=answer_key_{session_id}.csv'
            }
            
        elif format_type == 'pdf':
            # Generate PDF report
            session_dir = os.path.join(session_manager.sessions_dir, session_id)
            pdf_path = os.path.join(session_dir, 'answer_key_report.pdf')
            
            answer_key_generator.generate_pdf_report(session, pdf_path)
            
            # Read and return PDF content
            with open(pdf_path, 'r', encoding='utf-8') as f:
                pdf_content = f.read()
            
            return pdf_content, 200, {
                'Content-Type': 'text/plain',  # TODO: Change to application/pdf when real PDF generation is implemented
                'Content-Disposition': f'attachment; filename=answer_key_{session_id}.pdf'
            }
            
        else:
            return jsonify({
                "error": f"Invalid format: {format_type}. Must be json, csv, or pdf",
                "error_type": "invalid_parameter"
            }), 400
            
    except Exception as e:
        print(f"Error in solve_export_answer_key: {e}")
        print(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "error_type": "processing_error"
        }), 500


@app.route('/api/solve/session/<session_id>/use-for-evaluation', methods=['POST'])
@require_auth
def solve_use_for_evaluation(session_id):
    """
    Use generated answer key directly for OMR evaluation.
    
    Response:
        {
            "success": true,
            "answer_key": {...},
            "message": "Answer key ready for OMR evaluation"
        }
    """
    try:
        # Get session
        session = session_manager.get_session(session_id)
        
        if not session:
            return jsonify({
                "error": f"Session {session_id} not found",
                "error_type": "not_found"
            }), 404
        
        # Check if session has results
        if not session.results:
            return jsonify({
                "error": "Session has no results",
                "error_type": "no_results"
            }), 400
        
        # Generate JSON answer key
        answer_key_data = answer_key_generator.generate_json(session)
        
        # Extract just the answer_key portion (compatible with OMR evaluation)
        answer_key = answer_key_data["answer_key"]
        
        return jsonify({
            "success": True,
            "answer_key": answer_key,
            "metadata": answer_key_data["metadata"],
            "message": "Answer key ready for OMR evaluation"
        }), 200
        
    except Exception as e:
        print(f"Error in solve_use_for_evaluation: {e}")
        print(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "error_type": "processing_error"
        }), 500


# ---------------------------------------------------------------------------
# Dashboard and Analytics Endpoints
# ---------------------------------------------------------------------------

@app.route('/api/solve/dashboard', methods=['GET'])
@require_auth
def solve_dashboard():
    """
    Get performance monitoring dashboard with solver statistics across all sessions.
    
    Response:
        {
            "overview": {
                "total_sessions": int,
                "total_questions": int,
                "total_solved": int,
                "total_unsolvable": int,
                "total_errors": int,
                "total_corrections": int,
                "overall_accuracy": float,
                "correction_rate": float
            },
            "accuracy_trends": [
                {
                    "date": "YYYY-MM-DD",
                    "avg_confidence": float,
                    "question_count": int
                }
            ],
            "failure_patterns": [
                {
                    "pattern": str,
                    "count": int
                }
            ],
            "model_performance_by_type": {
                "math": {
                    "total": int,
                    "solved": int,
                    "avg_confidence": float,
                    "avg_processing_time_ms": float
                },
                "logical": {...},
                "factual": {...}
            },
            "generated_at": "ISO timestamp"
        }
    """
    try:
        api_logger.info("[API] Dashboard data requested")
        
        # Get dashboard data from analytics module
        dashboard_data = dashboard_analytics.get_dashboard_data()
        
        api_logger.info(
            f"[API] Dashboard data generated: "
            f"{dashboard_data['overview']['total_sessions']} sessions, "
            f"{dashboard_data['overview']['total_questions']} questions"
        )
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        api_logger.error(f"[API] Error generating dashboard: {e}")
        print(f"Error in solve_dashboard: {e}")
        print(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "error_type": "processing_error",
            "message": "Failed to generate dashboard data"
        }), 500


# ---------------------------------------------------------------------------
# WebSocket Endpoints
# ---------------------------------------------------------------------------

# WebSocket endpoint for progress updates
@socketio.on('subscribe_progress')
def handle_subscribe_progress(data):
    """
    Subscribe to progress updates for a session.
    
    Data:
        {
            "session_id": "uuid"
        }
    """
    session_id = data.get('session_id')
    
    if not session_id:
        emit('error', {'error': 'session_id is required'})
        return
    
    # Get session
    session = session_manager.get_session(session_id)
    
    if not session:
        emit('error', {'error': f'Session {session_id} not found'})
        return
    
    # Send current progress
    # Calculate progress metrics
    elapsed_time = 0
    estimated_remaining = 0
    questions_per_minute = 0.0
    
    if session.start_time:
        elapsed_time = time.time() - session.start_time
        
        if session.processed_count > 0 and elapsed_time > 0:
            questions_per_minute = (session.processed_count / elapsed_time) * 60
            
            remaining_questions = session.total_questions - session.processed_count
            if questions_per_minute > 0:
                estimated_remaining = (remaining_questions / questions_per_minute) * 60
    
    # Calculate average confidence
    average_confidence = 0.0
    if session.results:
        confidence_scores = [
            r.confidence for r in session.results.values()
            if r.status == "solved"
        ]
        if confidence_scores:
            average_confidence = sum(confidence_scores) / len(confidence_scores)
    
    progress_message = {
        "session_id": session_id,
        "status": session.status,
        "current_question": session.processed_count,
        "total_questions": session.total_questions,
        "processed_count": session.processed_count,
        "solved_count": session.solved_count,
        "unsolvable_count": session.unsolvable_count,
        "error_count": session.error_count,
        "elapsed_time_seconds": int(elapsed_time),
        "estimated_remaining_seconds": int(estimated_remaining),
        "average_confidence": round(average_confidence, 2),
        "questions_per_minute": round(questions_per_minute, 2)
    }
    
    emit('progress_update', progress_message)


# ---------------------------------------------------------------------------
# Frontend Static File Serving - MUST BE LAST (catch-all route)
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Serve the main frontend HTML file"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    """Serve frontend static files (CSS, JS, images, etc.)"""
    return send_from_directory('../frontend', path)


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, host='0.0.0.0', allow_unsafe_werkzeug=True)
