"""
ollama_client.py — AI Answer Key Extraction using Ollama
---------------------------------------------------------
Uses the locally-installed Ollama (moondream vision model) to extract
answer keys from question-paper images or PDFs.

Fix log:
  - Raises FileNotFoundError for missing files (fixes failing test).
  - Massively improved prompt with explicit format example.
  - Two-pass JSON extraction: formal JSON parse → regex line-scanner fallback.
  - Validates all extracted keys are numeric; skips bad entries.
"""

import os
import re
import time
import json
import subprocess
import traceback

import fitz   # PyMuPDF
import numpy as np
import cv2
import ollama
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class ExtractionConfig:
    """Configuration for answer key extraction.
    
    This dataclass holds all configuration parameters for the extraction system,
    including retry behavior, model selection, preprocessing options, and logging.
    """
    
    # Extraction behavior
    max_extraction_passes: int = 5  # Increased from 3 to 5 for better coverage
    extraction_timeout_seconds: int = 45  # Increased from 30 to 45 for large question sets
    
    # Model configuration
    primary_model: str = "moondream"
    fallback_model: Optional[str] = None  # e.g., "llava"
    
    # Image preprocessing
    min_dpi_for_pdf: int = 200
    target_image_width: int = 1024
    enable_preprocessing: bool = True
    
    # Logging
    log_path: str = "debug_ollama.log"
    
    # Extraction validation
    expected_question_count: Optional[int] = None  # For validation feedback
    
    def __post_init__(self):
        """Validate configuration parameters after initialization."""
        # Validate max_extraction_passes
        if self.max_extraction_passes < 1:
            raise ValueError(f"max_extraction_passes must be at least 1, got {self.max_extraction_passes}")
        
        # Validate extraction_timeout_seconds
        if self.extraction_timeout_seconds < 1:
            raise ValueError(f"extraction_timeout_seconds must be at least 1, got {self.extraction_timeout_seconds}")
        
        # Validate min_dpi_for_pdf
        if self.min_dpi_for_pdf < 72:
            raise ValueError(f"min_dpi_for_pdf must be at least 72, got {self.min_dpi_for_pdf}")
        
        # Validate target_image_width
        if self.target_image_width < 100:
            raise ValueError(f"target_image_width must be at least 100, got {self.target_image_width}")
        
        # Validate primary_model is not empty
        if not self.primary_model or not self.primary_model.strip():
            raise ValueError("primary_model cannot be empty")
        
        # Validate log_path is not empty
        if not self.log_path or not self.log_path.strip():
            raise ValueError("log_path cannot be empty")

# ---------------------------------------------------------------------------
# Prompt Strategies for Multi-Pass Extraction
# ---------------------------------------------------------------------------

# Pass 1: Detailed structured prompt with explicit format instructions
# Purpose: Provides comprehensive guidance to the AI model with clear rules
#          and examples. This is the primary extraction strategy that works
#          best when the model needs detailed context about the task.
PROMPT_PASS_1 = """You are an answer key extraction system. Analyze this question paper image and extract ALL the correct answers you can see.

Return a JSON object with this exact format:
{"1":"A","2":"C","3":"B","4":"D","5":"E",...}

IMPORTANT:
- Extract ALL questions visible in the image (could be 10, 50, 100+ questions)
- Keys must be question numbers (as strings)
- Values must be single letters: A, B, C, D, or E
- Include EVERY question with a clearly visible answer
- Do not stop at 5 or 10 questions - extract ALL of them
- If no answers are found, return {}
- Do not include any explanation or markdown formatting
"""

# Pass 2: Minimal prompt for quick extraction
# Purpose: Uses minimal instructions to avoid over-complicating the task.
#          Some models perform better with concise prompts. This strategy
#          is used as a fallback when the detailed prompt fails.
PROMPT_PASS_2 = """Extract ALL answers from this image as JSON: {"1":"A","2":"B",...,"100":"C"}. Extract every question you see. Nothing else."""

# Pass 3: Alternative phrasing with different instruction style
# Purpose: Rephrases the extraction request using different terminology.
#          This can help when the model misunderstands the previous prompts.
#          Uses "list" instead of "extract" and emphasizes JSON output format.
PROMPT_PASS_3 = """List the correct answer for EVERY question number in the image in JSON format like {"1":"A","2":"C",...}. Include all questions from 1 to the last question number. Only output the JSON object."""


# ---------------------------------------------------------------------------
# Legacy Configuration (for backward compatibility)
# ---------------------------------------------------------------------------

MODEL_NAME = "moondream"   # local Ollama vision model

# Path to the locally bundled Ollama executable (if the system one isn't in PATH)
_OLLAMA_EXE = None   # auto-detected below; override here if needed

LOG_PATH = os.path.join(os.path.dirname(__file__), "debug_ollama.log")


def log_debug(msg: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} - {msg}\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Structured Logging for Extraction Process
# ---------------------------------------------------------------------------

class ExtractionLogger:
    """Structured logging for extraction attempts with timestamps and tags."""

    def log_attempt_start(self, image_path: str, pass_number: int, model: str) -> None:
        """
        Log the start of an extraction attempt.

        Args:
            image_path: Path to the image being processed
            pass_number: The extraction pass number (1, 2, 3, etc.)
            model: The vision model being used (e.g., 'moondream')
        """
        filename = os.path.basename(image_path)
        log_debug(f"[EXTRACTION_START] Pass {pass_number}, Model: {model}, File: {filename}")

    def log_attempt_result(
        self,
        pass_number: int,
        success: bool,
        count: int,
        duration_ms: float,
        strategy: str
    ) -> None:
        """
        Log the result of an extraction attempt.

        Args:
            pass_number: The extraction pass number
            success: Whether the extraction succeeded
            count: Number of question-answer pairs extracted
            duration_ms: Processing time in milliseconds
            strategy: The prompt strategy used (e.g., 'detailed_json', 'simplified')
        """
        status = "SUCCESS" if success else "FAILED"
        log_debug(
            f"[PASS_{pass_number}] Result: {status}, Count: {count}, "
            f"Duration: {duration_ms:.0f}ms, Strategy: {strategy}"
        )

    def log_preprocessing(self, operation: str, duration_ms: float) -> None:
        """
        Log preprocessing operations.

        Args:
            operation: Description of the preprocessing operation
                      (e.g., 'PDF conversion', 'Image enhancement')
            duration_ms: Processing time in milliseconds
        """
        log_debug(f"[PREPROCESSING] {operation}: {duration_ms:.0f}ms")

    def log_validation_warnings(self, warnings: list[str]) -> None:
        """
        Log validation warnings.

        Args:
            warnings: List of validation warning messages
        """
        if warnings:
            for warning in warnings:
                log_debug(f"[VALIDATION] Warning: {warning}")

    def log_final_result(self, total_duration_ms: float, final_count: int) -> None:
        """
        Log the final extraction outcome.

        Args:
            total_duration_ms: Total processing time in milliseconds
            final_count: Final number of question-answer pairs extracted
        """
        log_debug(
            f"[EXTRACTION_COMPLETE] Total: {total_duration_ms:.0f}ms, "
            f"Final count: {final_count}"
        )



# ---------------------------------------------------------------------------
# Ollama availability helpers
# ---------------------------------------------------------------------------

def _ensure_ollama_running() -> None:
    """Start the local Ollama server if it is not already running."""
    try:
        ollama.list()          # quick connectivity test
        return
    except Exception:
        pass

    log_debug("Ollama server not responding — attempting to start it.")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        time.sleep(3)          # give it a moment to come up
    except FileNotFoundError:
        log_debug("Could not start Ollama — 'ollama' binary not found in PATH.")


# ---------------------------------------------------------------------------
# Image Preprocessing
# ---------------------------------------------------------------------------

def convert_pdf_to_image(pdf_path: str, dpi: int = 200) -> str:
    """
    Convert PDF first page to high-resolution image.
    
    Args:
        pdf_path: Path to PDF file
        dpi: Resolution for conversion (default 200, minimum 200)
        
    Returns:
        Path to converted image (temporary file)
        
    Raises:
        ValueError: if pdf_path is not a PDF file or conversion fails
        FileNotFoundError: if pdf_path does not exist
        
    Uses PyMuPDF (fitz) for conversion with specified DPI.
    """
    start_time = time.time()
    
    if not os.path.exists(pdf_path):
        log_debug(f"[PDF_CONVERSION] File not found: {pdf_path}")
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.lower().endswith(".pdf"):
        log_debug(f"[PDF_CONVERSION] Not a PDF file: {pdf_path}")
        raise ValueError(f"File is not a PDF: {pdf_path}")
    
    # Ensure minimum DPI of 200
    if dpi < 200:
        log_debug(f"[PDF_CONVERSION] DPI {dpi} is below minimum, using 200 DPI")
        dpi = 200
    
    log_debug(f"[PDF_CONVERSION] Starting PDF conversion: {pdf_path} at {dpi} DPI")
    
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)  # Convert first page only
        pix = page.get_pixmap(dpi=dpi)
        
        # Create temporary file path
        temp_image_path = pdf_path + "_converted.jpg"
        pix.save(temp_image_path)
        doc.close()
        
        duration_ms = (time.time() - start_time) * 1000
        log_debug(f"[PDF_CONVERSION] Conversion successful: {duration_ms:.0f}ms")
        log_debug(f"[PDF_CONVERSION] Output: {temp_image_path} ({pix.width}x{pix.height})")
        
        return temp_image_path
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_debug(f"[PDF_CONVERSION] Failed after {duration_ms:.0f}ms: {e}")
        raise ValueError(f"PDF conversion failed: {e}")


def preprocess_image(image_path: str, target_width: int = 1024) -> str:
    """
    Enhance image quality for better extraction using OpenCV operations.
    
    Args:
        image_path: Path to original image
        target_width: Target width for resizing (default 1024px)
        
    Returns:
        Path to preprocessed image (temporary file)
        
    Processing steps:
    - Load image with OpenCV
    - Convert to grayscale
    - Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    - Denoise with bilateral filter
    - Resize to optimal dimensions (maintain aspect ratio)
    - Save to temporary file
    """
    start_time = time.time()
    log_debug(f"[PREPROCESSING] Starting preprocessing for: {image_path}")
    
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            log_debug(f"[PREPROCESSING] Failed to load image: {image_path}")
            raise ValueError(f"Could not load image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Apply bilateral filter for denoising while preserving edges
        denoised = cv2.bilateralFilter(enhanced, d=9, sigmaColor=75, sigmaSpace=75)
        
        # Resize to optimal dimensions (maintain aspect ratio)
        height, width = denoised.shape
        if width > target_width:
            aspect_ratio = height / width
            new_width = target_width
            new_height = int(target_width * aspect_ratio)
            resized = cv2.resize(denoised, (new_width, new_height), interpolation=cv2.INTER_AREA)
        else:
            resized = denoised
        
        # Save to temporary file
        base_name = os.path.basename(image_path)
        name_without_ext = os.path.splitext(base_name)[0]
        temp_path = os.path.join(
            os.path.dirname(image_path),
            f"{name_without_ext}_preprocessed.jpg"
        )
        
        cv2.imwrite(temp_path, resized)
        
        duration_ms = (time.time() - start_time) * 1000
        log_debug(f"[PREPROCESSING] Image enhancement completed: {duration_ms:.0f}ms")
        log_debug(f"[PREPROCESSING] Original size: {width}x{height}, New size: {resized.shape[1]}x{resized.shape[0]}")
        
        return temp_path
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_debug(f"[PREPROCESSING] Failed after {duration_ms:.0f}ms: {e}")
        raise


# ---------------------------------------------------------------------------
# JSON extraction helpers
# ---------------------------------------------------------------------------

_LETTER_RE = re.compile(r"\b([ABCDE])\b")


def _try_parse_json(text: str) -> dict | None:
    """
    Attempt to extract a JSON object from arbitrary model output.
    Handles markdown code fences.  Returns None on failure.
    """
    clean = text.strip()

    # Strip markdown fences
    if "```" in clean:
        parts = clean.split("```")
        for part in parts:
            trimmed = part.strip()
            if trimmed.lower().startswith("json"):
                trimmed = trimmed[4:].strip()
            if "{" in trimmed and "}" in trimmed:
                clean = trimmed
                break

    # Pull out the first {...} block
    start = clean.find("{")
    end   = clean.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(clean[start : end + 1])
        except json.JSONDecodeError:
            pass
    return None


def _regex_fallback(text: str) -> dict:
    """
    Scan raw text for patterns like:
        Q1: A       1. A       1) A       1  A       Question 1: A
    Returns {1: "A", ...} for any discovered pairs.
    """
    results = {}
    # Pattern: optional label, then a number, then optional punctuation, then a letter A-E
    pattern = re.compile(
        r"(?:q(?:uestion)?\s*)?(\d+)\s*[:.)]\s*([ABCDE])\b",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        q = int(m.group(1))
        a = m.group(2).upper()
        if q not in results:         # keep first occurrence
            results[q] = a
    return results


def _normalise_json_dict(raw: dict) -> dict:
    """Convert raw parsed dict to {int_q: str_letter} form, skipping bad entries."""
    out = {}
    for k, v in raw.items():
        try:
            q_num = int(str(k).strip())
        except (ValueError, TypeError):
            log_debug(f"Skipping non-numeric key: {k!r}")
            continue
        ans = str(v).strip().upper()
        # Accept only single letters A-E
        if re.match(r"^[ABCDE]$", ans):
            out[q_num] = ans
        else:
            # Try to pull the first letter from the value string
            m = _LETTER_RE.search(ans)
            if m:
                out[q_num] = m.group(1)
            else:
                log_debug(f"Skipping unrecognised answer value: {v!r} for Q{q_num}")
    return out


def validate_extraction_result(result: dict, expected_count: int = None) -> tuple[dict, list[str]]:
    """
    Validate and clean extraction results.

    Args:
        result: Raw extraction dict (keys can be any type, values can be any type)
        expected_count: Optional expected number of questions (for validation feedback)

    Returns:
        Tuple of (cleaned_dict, warnings_list)
        - cleaned_dict: {int: str} with valid question numbers and answers only
        - warnings_list: List of warning messages about validation issues

    Validation checks:
    - All keys must be positive integers (or convertible to positive integers)
    - All values must be single letters A-E
    - Duplicate question numbers are removed (keeping first occurrence)
    - Warning generated if < 5 question-answer pairs
    - Warning generated if extracted count is significantly less than expected

    Example:
        result = {"1": "A", "2": "C", "1": "B", "3": "X", "-1": "D"}
        cleaned, warnings = validate_extraction_result(result)
        # cleaned = {1: "A", 2: "C"}
        # warnings = ["Duplicate question 1 removed",
        #             "Invalid answer 'X' for question 3 removed",
        #             "Invalid question number '-1' removed",
        #             "Only 2 answers extracted (< 5)"]
    """
    cleaned = {}
    warnings = []
    seen_questions = set()

    # Process each entry in the result
    for key, value in result.items():
        # Validate question number (must be positive integer)
        try:
            question_num = int(str(key).strip())
        except (ValueError, TypeError):
            warnings.append(f"Invalid question number '{key}' removed (not a valid integer)")
            continue

        if question_num <= 0:
            warnings.append(f"Invalid question number '{question_num}' removed (must be positive)")
            continue

        # Check for duplicates (keep first occurrence)
        if question_num in seen_questions:
            warnings.append(f"Duplicate question {question_num} removed (keeping first occurrence)")
            continue

        # Validate answer (must be single letter A-E)
        answer_str = str(value).strip().upper()

        # Check if it's a valid single letter A-E
        if not re.match(r"^[ABCDE]$", answer_str):
            warnings.append(f"Invalid answer '{value}' for question {question_num} removed (must be A, B, C, D, or E)")
            continue

        # Valid entry - add to cleaned dict
        cleaned[question_num] = answer_str
        seen_questions.add(question_num)

    # Check for low count warning
    if len(cleaned) < 5:
        warnings.append(f"Only {len(cleaned)} answers extracted (< 5)")
    
    # Check against expected count if provided
    if expected_count and len(cleaned) < expected_count:
        percentage = (len(cleaned) / expected_count) * 100
        warnings.append(
            f"Extracted {len(cleaned)} of {expected_count} expected questions ({percentage:.1f}%). "
            f"Consider re-uploading with better image quality or try a different image format."
        )

    return cleaned, warnings



# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_answer_key_from_image(
    image_path: str,
    config: Optional[ExtractionConfig] = None
) -> tuple[dict, list[str], float]:
    """
    Extract answer keys using multi-pass strategy with configurable behavior.

    This function implements a robust multi-pass extraction strategy:
    1. Preprocess image (if enabled in config)
    2. Loop through extraction passes with different prompt strategies
    3. For each pass:
       - Try JSON parsing first
       - Fallback to regex if JSON fails
       - Log attempt details and timing
       - Return immediately on success
    4. Validate and clean results
    5. Return best result or empty dict if all passes fail

    Args:
        image_path: Absolute path to image (.jpg/.png) or PDF.
        config: Optional ExtractionConfig for customizing behavior.
                If None, uses default configuration.

    Returns:
        Tuple of (answer_key_dict, warnings_list, processing_time_ms):
        - answer_key_dict: {question_number (int): answer_letter (str)}  e.g.  {1: "A", 2: "C"}
          Returns {} if nothing could be extracted.
        - warnings_list: List of validation warnings (e.g., ["Only 3 answers extracted (< 5)"])
        - processing_time_ms: Total processing time in milliseconds

    Raises:
        FileNotFoundError: if image_path does not exist.
    """
    # Use default config if none provided
    if config is None:
        config = ExtractionConfig()
    
    # Initialize logger and timing
    logger = ExtractionLogger()
    extraction_start_time = time.time()
    
    # Validate file exists
    if not os.path.exists(image_path):
        log_debug(f"File not found: {image_path}")
        raise FileNotFoundError(f"Image file not found: {image_path}")

    log_debug(f"[EXTRACTION_START] File: {os.path.basename(image_path)}")

    # Ensure Ollama daemon is up
    _ensure_ollama_running()

    # Track temporary files for cleanup
    temp_image_path = None
    temp_preprocessed_path = None
    
    # Define prompt strategies for each pass
    prompt_strategies = [
        ("detailed_json", PROMPT_PASS_1),
        ("simplified", PROMPT_PASS_2),
        ("alternative_phrasing", PROMPT_PASS_3),
    ]
    
    try:
        # ----- PDF Conversion (if needed) ---------------------------------
        if image_path.lower().endswith(".pdf"):
            log_debug("Detected PDF. Converting to image...")
            pdf_start = time.time()
            try:
                temp_image_path = convert_pdf_to_image(image_path, dpi=config.min_dpi_for_pdf)
                image_to_process = temp_image_path
                pdf_duration = (time.time() - pdf_start) * 1000
                logger.log_preprocessing("PDF conversion", pdf_duration)
            except Exception as pdf_err:
                log_debug(f"PDF conversion failed: {pdf_err}")
                total_duration = (time.time() - extraction_start_time) * 1000
                return {}, [f"PDF conversion failed: {str(pdf_err)}"], total_duration
        else:
            image_to_process = image_path

        # ----- Image Preprocessing (if enabled) ---------------------------
        if config.enable_preprocessing:
            preprocess_start = time.time()
            try:
                temp_preprocessed_path = preprocess_image(
                    image_to_process, 
                    target_width=config.target_image_width
                )
                image_to_process = temp_preprocessed_path
                preprocess_duration = (time.time() - preprocess_start) * 1000
                logger.log_preprocessing("Image enhancement", preprocess_duration)
            except Exception as preprocess_err:
                log_debug(f"[PREPROCESSING] Warning: Preprocessing failed, using original image: {preprocess_err}")
                # Continue with original image if preprocessing fails
        
        # ----- Multi-Pass Extraction Loop ---------------------------------
        best_result = {}
        
        for pass_number in range(1, config.max_extraction_passes + 1):
            # Determine which model and strategy to use for this pass
            # Use fallback model on the last pass if configured, otherwise use primary model
            is_last_pass = (pass_number == config.max_extraction_passes)
            use_fallback = is_last_pass and config.fallback_model is not None
            
            if use_fallback:
                # Last pass with fallback model configured
                model_to_use = config.fallback_model
                strategy_name = "fallback_model"
                prompt = PROMPT_PASS_1  # Use detailed prompt with fallback model
                log_debug(f"[PASS_{pass_number}] Using fallback model: {model_to_use}")
            elif pass_number <= len(prompt_strategies):
                # Use primary model with one of the prompt strategies
                strategy_name, prompt = prompt_strategies[pass_number - 1]
                model_to_use = config.primary_model
            else:
                # No more strategies available and no fallback model
                log_debug(f"[PASS_{pass_number}] Skipped: No more strategies available")
                continue
            
            # Log attempt start
            logger.log_attempt_start(image_path, pass_number, model_to_use)
            pass_start_time = time.time()
            
            try:
                # Send request to Ollama
                response = ollama.chat(
                    model=model_to_use,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                            "images": [image_to_process],
                        }
                    ],
                )

                # Extract content string
                try:
                    raw_text = response.message.content
                except AttributeError:
                    raw_text = response["message"]["content"]

                log_debug(f"[PASS_{pass_number}] Raw output: {raw_text[:500]}")

                # Try JSON parsing first
                parsed = _try_parse_json(raw_text)
                if parsed and isinstance(parsed, dict):
                    normalized = _normalise_json_dict(parsed)
                    if normalized:
                        # Validate and clean the result
                        validated, warnings = validate_extraction_result(
                            normalized, 
                            expected_count=config.expected_question_count
                        )
                        if validated:
                            pass_duration = (time.time() - pass_start_time) * 1000
                            logger.log_attempt_result(
                                pass_number, 
                                True, 
                                len(validated), 
                                pass_duration, 
                                strategy_name
                            )
                            logger.log_validation_warnings(warnings)
                            
                            # Calculate total duration and log final result
                            total_duration = (time.time() - extraction_start_time) * 1000
                            logger.log_final_result(total_duration, len(validated))
                            
                            # Early exit on success
                            return validated, warnings, total_duration

                # Fallback to regex if JSON parsing failed
                regex_result = _regex_fallback(raw_text)
                if regex_result:
                    # Validate and clean the regex result
                    validated, warnings = validate_extraction_result(
                        regex_result,
                        expected_count=config.expected_question_count
                    )
                    if validated:
                        pass_duration = (time.time() - pass_start_time) * 1000
                        logger.log_attempt_result(
                            pass_number, 
                            True, 
                            len(validated), 
                            pass_duration, 
                            f"{strategy_name}_regex"
                        )
                        logger.log_validation_warnings(warnings)
                        
                        # Calculate total duration and log final result
                        total_duration = (time.time() - extraction_start_time) * 1000
                        logger.log_final_result(total_duration, len(validated))
                        
                        # Early exit on success
                        return validated, warnings, total_duration

                # Pass failed
                pass_duration = (time.time() - pass_start_time) * 1000
                logger.log_attempt_result(
                    pass_number, 
                    False, 
                    0, 
                    pass_duration, 
                    strategy_name
                )

            except Exception as pass_exc:
                pass_duration = (time.time() - pass_start_time) * 1000
                log_debug(f"[PASS_{pass_number}] Error: {pass_exc}")
                logger.log_attempt_result(
                    pass_number, 
                    False, 
                    0, 
                    pass_duration, 
                    strategy_name
                )
        
        # All passes failed
        total_duration = (time.time() - extraction_start_time) * 1000
        logger.log_final_result(total_duration, 0)
        log_debug("All extraction passes failed — returning {}")
        return {}, ["All extraction passes failed - no answers could be extracted"], total_duration

    except Exception as exc:
        log_debug(f"Error extracting key: {exc}")
        log_debug(traceback.format_exc())
        total_duration = (time.time() - extraction_start_time) * 1000
        return {}, [f"Extraction error: {str(exc)}"], total_duration

    finally:
        # Cleanup temporary files
        if temp_image_path and os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
                log_debug(f"[CLEANUP] Removed temporary PDF conversion: {temp_image_path}")
            except Exception as e:
                log_debug(f"[CLEANUP] Failed to remove {temp_image_path}: {e}")
        
        if temp_preprocessed_path and os.path.exists(temp_preprocessed_path):
            try:
                os.remove(temp_preprocessed_path)
                log_debug(f"[CLEANUP] Removed temporary preprocessed image: {temp_preprocessed_path}")
            except Exception as e:
                log_debug(f"[CLEANUP] Failed to remove {temp_preprocessed_path}: {e}")


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    test_img = sys.argv[1] if len(sys.argv) > 1 else "question_paper_sample.jpg"
    if os.path.exists(test_img):
        print(f"Extracting answer key from: {test_img}")
        key, warnings, processing_time = extract_answer_key_from_image(test_img)
        print(f"Extracted Key ({len(key)} answers): {key}")
        print(f"Warnings: {warnings}")
        print(f"Processing time: {processing_time:.2f}ms")
    else:
        print(f"File not found: {test_img}")
