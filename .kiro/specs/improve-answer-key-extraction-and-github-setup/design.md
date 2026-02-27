# Design Document: Enhanced Answer Key Extraction and GitHub Setup

## Overview

This design document specifies the technical implementation for improving the reliability of AI-based answer key extraction in the OMR evaluation system and establishing a GitHub repository for the project. The system currently uses Ollama with the moondream vision model but lacks robust error handling, image preprocessing, and multi-pass extraction strategies. This enhancement will add image preprocessing, multiple extraction strategies with fallback mechanisms, comprehensive validation, detailed error reporting, and performance monitoring.

The design addresses two main areas:
1. **Enhanced Extraction System**: Improving the reliability and accuracy of AI-based answer key extraction through preprocessing, multi-pass strategies, validation, and monitoring
2. **GitHub Repository Setup**: Establishing a well-documented, properly structured public repository

### Key Design Goals

- Increase extraction success rate from question paper images through preprocessing and multi-pass strategies
- Provide clear, actionable error messages when extraction fails
- Enable monitoring and debugging of extraction performance
- Support alternative vision models for improved accuracy
- Establish a professional, well-documented GitHub repository
- Maintain backward compatibility with existing API contracts

## Architecture

### System Components

The enhanced system consists of the following components:

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (index.html)                    │
│  - File upload UI                                            │
│  - Error display with actionable guidance                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP POST /api/extract_key
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend API (app.py)                       │
│  - Request validation                                        │
│  - HTTP status code mapping (404, 422, 500)                 │
│  - Error message formatting                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ extract_answer_key_from_image()
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            Extraction Engine (ollama_client.py)              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 1. Image Preprocessing Module                         │  │
│  │    - Format detection (PDF/Image)                     │  │
│  │    - PDF to image conversion (200+ DPI)               │  │
│  │    - Contrast/brightness enhancement                  │  │
│  │    - Optimal resizing for vision model                │  │
│  └───────────────────────────────────────────────────────┘  │
│                       ▼                                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 2. Multi-Pass Extraction Module                       │  │
│  │    - Pass 1: Detailed JSON prompt                     │  │
│  │    - Pass 2: Simplified prompt                        │  │
│  │    - Pass 3: Alternative vision model (if configured) │  │
│  │    - Regex fallback for each pass                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                       ▼                                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 3. Validation Module                                  │  │
│  │    - Question number validation (positive integers)   │  │
│  │    - Answer validation (A-E only)                     │  │
│  │    - Duplicate removal                                │  │
│  │    - Minimum count warning (< 5 pairs)                │  │
│  └───────────────────────────────────────────────────────┘  │
│                       ▼                                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 4. Logging & Monitoring Module                        │  │
│  │    - Extraction attempt logging                       │  │
│  │    - Success/failure tracking                         │  │
│  │    - Processing time measurement                      │  │
│  │    - Strategy success tracking                        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Ollama Vision Model (moondream)                 │
│  - Local inference                                           │
│  - Alternative model support (configurable)                  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Upload Phase**: User uploads question paper image/PDF via frontend
2. **Preprocessing Phase**: Image is enhanced (contrast, brightness, resize) and PDFs converted to high-res images
3. **Extraction Phase**: Multi-pass extraction with different prompts and optional fallback model
4. **Validation Phase**: Results validated for correctness (numeric keys, valid answers, duplicates)
5. **Response Phase**: Validated results or detailed error messages returned to frontend
6. **Logging Phase**: All attempts, timings, and outcomes logged for monitoring

### Configuration Management

The system will support configuration through a new `ExtractionConfig` class:

```python
class ExtractionConfig:
    max_extraction_passes: int = 3
    extraction_timeout_seconds: int = 30
    primary_model: str = "moondream"
    fallback_model: Optional[str] = None
    min_dpi_for_pdf: int = 200
    target_image_width: int = 1024
    enable_preprocessing: bool = True
    log_path: str = "debug_ollama.log"
```

## Components and Interfaces

### 1. Image Preprocessing Module

**Location**: `backend/ollama_client.py`

**New Functions**:

```python
def preprocess_image(image_path: str) -> str:
    """
    Enhance image quality for better extraction.
    
    Args:
        image_path: Path to original image
        
    Returns:
        Path to preprocessed image (temporary file)
        
    Processing steps:
    - Load image with OpenCV
    - Convert to grayscale
    - Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    - Denoise with bilateral filter
    - Resize to optimal dimensions (1024px width, maintain aspect ratio)
    - Save to temporary file
    """
    
def convert_pdf_to_image(pdf_path: str, dpi: int = 200) -> str:
    """
    Convert PDF first page to high-resolution image.
    
    Args:
        pdf_path: Path to PDF file
        dpi: Resolution for conversion (default 200)
        
    Returns:
        Path to converted image (temporary file)
        
    Uses PyMuPDF (fitz) for conversion with specified DPI.
    """
```

**Integration Point**: Called at the start of `extract_answer_key_from_image()` before any AI extraction attempts.

### 2. Multi-Pass Extraction Module

**Location**: `backend/ollama_client.py`

**Enhanced Function**:

```python
def extract_answer_key_from_image(
    image_path: str,
    config: Optional[ExtractionConfig] = None
) -> dict:
    """
    Extract answer keys using multi-pass strategy.
    
    Extraction Strategy:
    1. Preprocess image
    2. Pass 1: Detailed JSON prompt with primary model
       - Try JSON parsing
       - Fallback to regex if JSON fails
    3. Pass 2: Simplified prompt with primary model
       - Try JSON parsing
       - Fallback to regex if JSON fails
    4. Pass 3: Alternative model (if configured)
       - Try JSON parsing
       - Fallback to regex if JSON fails
    5. Return best result or empty dict
    
    Each pass logs:
    - Timestamp
    - Model used
    - Prompt strategy
    - Raw output (first 500 chars)
    - Parsing success/failure
    - Number of extracted pairs
    - Processing time
    
    Returns:
        {question_number (int): answer_letter (str)}
        Empty dict {} if all passes fail
        
    Raises:
        FileNotFoundError: if image_path does not exist
    """
```

**New Prompt Strategies**:

```python
# Pass 1: Detailed structured prompt
PROMPT_PASS_1 = """You are an answer key extraction system. Analyze this question paper image and extract ONLY the correct answers.

Return a JSON object with this exact format:
{"1":"A","2":"C","3":"B","4":"D","5":"E"}

Rules:
- Keys must be question numbers (as strings)
- Values must be single letters: A, B, C, D, or E
- Include only questions with clearly visible answers
- If no answers are found, return {}
- Do not include any explanation or markdown formatting
"""

# Pass 2: Minimal prompt
PROMPT_PASS_2 = """Extract answers as JSON: {"1":"A","2":"B"}. Nothing else."""

# Pass 3: Alternative phrasing
PROMPT_PASS_3 = """List the correct answer for each question number in JSON format like {"1":"A","2":"C"}. Only output the JSON object."""
```

### 3. Validation Module

**Location**: `backend/ollama_client.py`

**New Function**:

```python
def validate_extraction_result(result: dict) -> tuple[dict, list[str]]:
    """
    Validate and clean extraction results.
    
    Args:
        result: Raw extraction dict
        
    Returns:
        Tuple of (cleaned_dict, warnings_list)
        
    Validation checks:
    - All keys are positive integers
    - All values are single letters A-E
    - No duplicate question numbers (keep first)
    - Warn if < 5 question-answer pairs
    
    Example:
        result = {"1": "A", "2": "C", "1": "B", "3": "X"}
        cleaned, warnings = validate_extraction_result(result)
        # cleaned = {"1": "A", "2": "C"}
        # warnings = ["Duplicate question 1 removed", 
        #             "Invalid answer 'X' for question 3 removed",
        #             "Only 2 answers extracted (< 5)"]
    """
```

### 4. Logging & Monitoring Module

**Location**: `backend/ollama_client.py`

**Enhanced Logging**:

```python
class ExtractionLogger:
    """Structured logging for extraction attempts."""
    
    def log_attempt_start(self, image_path: str, pass_number: int, model: str):
        """Log start of extraction attempt."""
        
    def log_attempt_result(
        self, 
        pass_number: int, 
        success: bool, 
        count: int, 
        duration_ms: float,
        strategy: str
    ):
        """Log result of extraction attempt."""
        
    def log_preprocessing(self, operation: str, duration_ms: float):
        """Log preprocessing operations."""
        
    def log_validation_warnings(self, warnings: list[str]):
        """Log validation warnings."""
        
    def log_final_result(self, total_duration_ms: float, final_count: int):
        """Log final extraction outcome."""
```

**Log Format**:
```
2024-01-15 10:30:45 - [EXTRACTION_START] File: question_paper.jpg
2024-01-15 10:30:45 - [PREPROCESSING] PDF conversion: 245ms
2024-01-15 10:30:45 - [PREPROCESSING] Image enhancement: 123ms
2024-01-15 10:30:46 - [PASS_1] Model: moondream, Strategy: detailed_json
2024-01-15 10:30:48 - [PASS_1] Raw output: {"1":"A","2":"C"...
2024-01-15 10:30:48 - [PASS_1] Result: SUCCESS, Count: 25, Duration: 2134ms
2024-01-15 10:30:48 - [VALIDATION] Warning: Duplicate question 5 removed
2024-01-15 10:30:48 - [EXTRACTION_COMPLETE] Total: 2502ms, Final count: 24
```

### 5. Backend API Error Handling

**Location**: `backend/app.py`

**Enhanced `/api/extract_key` Endpoint**:

```python
@app.route('/api/extract_key', methods=['POST'])
def extract_key():
    """
    Extract answer key from question paper with enhanced error handling.
    
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
            "Try uploading a higher resolution image",
            "Verify the answer key format is visible"
        ]
    }
    """
```

**Error Message Templates**:

```python
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
```

### 6. Frontend Error Display

**Location**: `frontend/index.html`

**Enhanced Error Display**:

```javascript
function displayExtractionError(errorData) {
    const errorContainer = document.getElementById('extractionError');
    
    // Clear previous errors
    errorContainer.innerHTML = '';
    errorContainer.classList.remove('hidden');
    
    // Create error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <div class="error-header">
            <i class="fa-solid fa-triangle-exclamation"></i>
            <span>${errorData.error}</span>
        </div>
        ${errorData.suggestions ? `
            <div class="error-suggestions">
                <strong>Suggestions:</strong>
                <ul>
                    ${errorData.suggestions.map(s => `<li>${s}</li>`).join('')}
                </ul>
            </div>
        ` : ''}
    `;
    
    errorContainer.appendChild(errorDiv);
}
```

**CSS Styling**:

```css
.error-message {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 12px;
    padding: 16px;
    margin-top: 12px;
}

.error-header {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #ef4444;
    font-weight: 600;
    margin-bottom: 12px;
}

.error-suggestions {
    color: var(--text-muted);
    font-size: 0.85rem;
}

.error-suggestions ul {
    margin: 8px 0 0 20px;
    padding: 0;
}

.error-suggestions li {
    margin: 4px 0;
}
```

## Data Models

### ExtractionConfig

```python
@dataclass
class ExtractionConfig:
    """Configuration for answer key extraction."""
    
    # Extraction behavior
    max_extraction_passes: int = 3
    extraction_timeout_seconds: int = 30
    
    # Model configuration
    primary_model: str = "moondream"
    fallback_model: Optional[str] = None  # e.g., "llava"
    
    # Image preprocessing
    min_dpi_for_pdf: int = 200
    target_image_width: int = 1024
    enable_preprocessing: bool = True
    contrast_enhancement: bool = True
    
    # Validation
    min_answer_count_warning: int = 5
    
    # Logging
    log_path: str = "debug_ollama.log"
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
```

### ExtractionResult

```python
@dataclass
class ExtractionResult:
    """Result of an extraction attempt."""
    
    success: bool
    answer_key: dict[int, str]  # {question_num: answer_letter}
    count: int
    warnings: list[str]
    processing_time_ms: float
    passes_attempted: int
    successful_pass: Optional[int]
    model_used: str
```

### ExtractionAttempt (for logging)

```python
@dataclass
class ExtractionAttempt:
    """Record of a single extraction attempt."""
    
    timestamp: str
    pass_number: int
    model: str
    strategy: str
    success: bool
    count: int
    duration_ms: float
    raw_output_preview: str  # First 500 chars
```

## Data Models

### GitHub Repository Structure

```
omr-evaluation-system/
├── .gitignore
├── README.md
├── LICENSE (optional)
├── requirements.txt (root level, points to backend/requirements.txt)
├── backend/
│   ├── app.py
│   ├── ollama_client.py
│   ├── omr_engine.py
│   ├── full_evaluator.py
│   ├── dl_model.py
│   ├── hardware_handler.py
│   ├── pipeline.py
│   ├── requirements.txt
│   ├── tests/
│   │   └── (test files)
│   └── (other backend files)
├── frontend/
│   ├── index.html
│   └── style.css
├── docs/
│   ├── SETUP.md
│   ├── API.md
│   └── TROUBLESHOOTING.md
└── .kiro/
    └── specs/
        └── (specification files)
```

### .gitignore Content

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project Specific
backend/temp_uploads/
backend/debug_ollama.log
backend/*.pth
backend/bubble_dataset/
backend/synthetic_omr_data/
debug_vis/
runs/
yolov8_results/
yolov8_runs/
*.zip
*.pt

# Model weights
*.pth
*.onnx
*.weights

# Data
train/
yolov8_omr/

# Temporary files
*.tmp
*.log
temp_*
```

### README.md Structure

```markdown
# OMR Evaluation System - EvalGenius AI

Next-generation Optical Mark Recognition system with AI-powered answer key extraction.

## Features

- 🤖 AI-powered answer key extraction from question papers
- 📊 Automated OMR sheet evaluation with bubble detection
- 📈 Real-time grading and analytics
- 🔄 Multi-set exam support (Set A, Set B)
- 📱 Modern web interface
- 🔌 Hardware integration support

## Prerequisites

- Python 3.8+
- Ollama (for AI answer key extraction)
- OpenCV dependencies

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Jagadeesh-Surendran/omr-evaluation-system.git
cd omr-evaluation-system
```

### 2. Set Up Python Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 3. Install Ollama

Download and install Ollama from [ollama.ai](https://ollama.ai)

Pull the required vision model:
```bash
ollama pull moondream
```

### 4. Run the Application

```bash
# Start the backend server
cd backend
python app.py

# The server will start on http://localhost:5000
# Open http://localhost:5000 in your browser
```

## Usage

### Automatic Evaluation Mode

1. Upload question paper images (Set A and/or Set B) for AI extraction
2. Upload OMR sheets (student answer sheets)
3. Click "Process Sheets" to evaluate
4. View results, analytics, and export reports

### Manual Evaluation Mode

1. Process sheets in automatic mode first
2. Click "Manual" on any result to review bubble detections
3. Correct any misreadings
4. Save changes to recalculate scores

## Project Structure

- `backend/` - Flask API server and processing logic
- `frontend/` - HTML/CSS/JavaScript web interface
- `backend/tests/` - Unit tests
- `docs/` - Additional documentation

## Configuration

Edit `backend/ollama_client.py` to configure:
- Vision model selection
- Extraction timeout
- Image preprocessing options
- Logging level

## Troubleshooting

### Ollama Connection Issues

Ensure Ollama is running:
```bash
ollama serve
```

### Extraction Failures

- Use high-resolution images (200+ DPI for PDFs)
- Ensure good lighting and contrast
- Verify answer key format is clearly visible

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more help.

## License

[Specify license here]

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Author

Jagadeesh Surendran
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified several areas where properties can be consolidated:

**Consolidation 1**: Logging properties (1.5, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5, 10.5) all test that specific information is logged. These can be combined into comprehensive logging properties that verify all required information is present.

**Consolidation 2**: Configuration properties (5.1, 10.1, 10.2, 10.3, 10.4) all test configuration support. These can be combined into properties that verify configuration is respected across all configurable parameters.

**Consolidation 3**: Validation properties (3.1, 3.2, 3.5) all test that extraction results meet validation criteria. These can be combined into a single comprehensive validation property.

**Consolidation 4**: Fallback model properties (5.2, 5.4) test the same behavior - using fallback model when primary fails. These are redundant and can be combined.

**Consolidation 5**: Documentation properties (7.4, 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.2) are all examples testing specific file content. These don't need separate properties as they're one-time setup verification.

### Property 1: Multi-Pass Extraction Attempts

*For any* question paper image provided to the extraction system, the system should attempt extraction using at least the configured number of different strategies (default 3), with each pass using a different prompt or model.

**Validates: Requirements 1.1, 1.2**

### Property 2: Non-Empty Success Results

*For any* extraction attempt that returns success status, the result must contain at least one valid question-answer pair where the question is a positive integer and the answer is a letter from {A, B, C, D, E}.

**Validates: Requirements 1.3**

### Property 3: Error Messages on Complete Failure

*For any* extraction attempt where all passes fail to produce valid results, the system should return a descriptive error message (not an empty response) that indicates the failure reason.

**Validates: Requirements 1.4**

### Property 4: Comprehensive Extraction Logging

*For any* extraction attempt, the debug log file should contain entries with: timestamp, pass number, model used, strategy name, success/failure status, count of extracted pairs, and processing duration.

**Validates: Requirements 1.5, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5**

### Property 5: Preprocessing Before Extraction

*For any* question paper image, preprocessing operations (contrast enhancement, resizing) should be applied before any AI extraction attempts, as evidenced by preprocessing log entries appearing before extraction log entries.

**Validates: Requirements 2.1, 2.2**

### Property 6: Image Dimension Normalization

*For any* input image, after preprocessing, the image dimensions should match the configured target dimensions (default 1024px width with maintained aspect ratio).

**Validates: Requirements 2.3**

### Property 7: PDF High-Resolution Conversion

*For any* PDF file input, the converted image should have a resolution of at least the configured minimum DPI (default 200 DPI).

**Validates: Requirements 2.4**

### Property 8: Original File Preservation

*For any* input file, after extraction completes (success or failure), the original file should remain unmodified and any temporary files should be cleaned up.

**Validates: Requirements 2.5**

### Property 9: Validated Result Structure

*For any* extraction result that passes validation, all question numbers must be positive integers, all answer values must be single letters from {A, B, C, D, E}, and the count field must equal the number of entries in the answer_key dictionary.

**Validates: Requirements 3.1, 3.2, 3.5**

### Property 10: Low Count Warning

*For any* extraction result containing fewer than the configured minimum (default 5) question-answer pairs, the log file should contain a warning message about the low count.

**Validates: Requirements 3.3**

### Property 11: Duplicate Question Deduplication

*For any* raw extraction result containing duplicate question numbers, the validated result should contain only the first occurrence of each question number.

**Validates: Requirements 3.4**

### Property 12: Error Type to Status Code Mapping

*For any* API request to /api/extract_key, the HTTP status code should correctly map to the error type: 404 for file not found, 422 for extraction failures (zero results), and 500 for server errors.

**Validates: Requirements 4.4, 4.5**

### Property 13: Configuration Parameter Respect

*For any* extraction attempt with provided configuration, the system should respect all configured limits including max_extraction_passes, extraction_timeout_seconds, and model selections.

**Validates: Requirements 5.1, 10.1, 10.2, 10.3**

### Property 14: Fallback Model Usage

*For any* extraction attempt where the primary model fails and a fallback model is configured, the system should automatically attempt extraction with the fallback model.

**Validates: Requirements 5.2, 5.4**

### Property 15: Multi-Model Support

*For any* configured vision model from the supported set (moondream, llava, etc.), the extraction system should be able to use that model for extraction attempts.

**Validates: Requirements 5.5**

### Property 16: Default Configuration Values

*For any* extraction attempt without explicit configuration, the system should use sensible default values (3 passes, 30 second timeout, moondream model, preprocessing enabled).

**Validates: Requirements 10.4**

### Property 17: Skip Logging

*For any* extraction attempt where passes are skipped due to timeout or retry limits, the log should contain entries explaining why the passes were skipped.

**Validates: Requirements 10.5**

## Error Handling

### Error Categories

The system handles four main categories of errors:

1. **File Errors (HTTP 404)**
   - Missing file
   - File not found after upload
   - Invalid file path

2. **Extraction Errors (HTTP 422)**
   - No answers extracted (all passes failed)
   - Poor image quality
   - Unrecognizable format

3. **Validation Errors (HTTP 400)**
   - No file provided in request
   - Invalid file format
   - Corrupted file

4. **Server Errors (HTTP 500)**
   - Ollama connection failure
   - Unexpected processing errors
   - System resource issues

### Error Response Format

All error responses follow a consistent structure:

```json
{
    "error": "Human-readable error message",
    "error_type": "error_category_identifier",
    "suggestions": [
        "Actionable suggestion 1",
        "Actionable suggestion 2"
    ],
    "details": {
        "passes_attempted": 3,
        "processing_time_ms": 2500
    }
}
```

### Error Recovery Strategies

1. **Automatic Retry**: Multi-pass extraction with different strategies
2. **Preprocessing Enhancement**: Apply image enhancement before retry
3. **Model Fallback**: Try alternative vision model if configured
4. **Graceful Degradation**: Return partial results with warnings if some questions extracted

### Frontend Error Handling

The frontend implements:
- Clear error message display with icons
- Actionable suggestions for users
- Error state management (hide/show)
- Retry mechanism for transient failures

### Logging for Debugging

All errors are logged with:
- Full stack trace
- Request context (file name, size, format)
- Extraction attempt details
- Timestamp and duration

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests** focus on:
- Specific error scenarios (file not found, empty results)
- Edge cases (single question, malformed JSON)
- Integration points (API endpoints, file handling)
- Configuration validation
- Mock-based testing of Ollama interactions

**Property-Based Tests** focus on:
- Universal properties across all inputs
- Validation logic correctness
- Logging completeness
- Configuration parameter respect
- Multi-pass behavior

### Property-Based Testing Configuration

We will use **Hypothesis** for Python property-based testing with the following configuration:

```python
from hypothesis import given, settings, strategies as st

# Configure for thorough testing
@settings(max_examples=100, deadline=None)
@given(
    image_path=st.text(min_size=1),
    config=st.builds(ExtractionConfig)
)
def test_property_X(image_path, config):
    # Property test implementation
    pass
```

Each property test must:
- Run minimum 100 iterations
- Reference its design document property in a comment
- Use appropriate Hypothesis strategies for input generation
- Tag format: `# Feature: improve-answer-key-extraction-and-github-setup, Property X: [property text]`

### Test Organization

```
backend/tests/
├── test_extraction_properties.py      # Property-based tests
├── test_extraction_unit.py            # Unit tests for extraction
├── test_preprocessing.py              # Image preprocessing tests
├── test_validation.py                 # Validation logic tests
├── test_api_errors.py                 # API error handling tests
├── test_logging.py                    # Logging behavior tests
└── fixtures/
    ├── sample_question_papers/        # Test images
    └── mock_responses/                # Mock Ollama responses
```

### Unit Test Examples

```python
def test_file_not_found_returns_404():
    """Test that missing files return 404 status."""
    response = client.post('/api/extract_key', data={})
    assert response.status_code == 400  # No file provided
    
    response = client.post('/api/extract_key', 
                          data={'qp_file': 'nonexistent.jpg'})
    assert response.status_code == 404

def test_empty_extraction_returns_422():
    """Test that zero results return 422 with suggestions."""
    # Mock Ollama to return empty results
    with mock.patch('ollama_client.ollama.chat') as mock_chat:
        mock_chat.return_value.message.content = "{}"
        response = client.post('/api/extract_key', 
                              data={'qp_file': test_image})
        assert response.status_code == 422
        assert 'suggestions' in response.json

def test_preprocessing_enhances_contrast():
    """Test that preprocessing applies CLAHE."""
    original = cv2.imread('test_image.jpg')
    processed_path = preprocess_image('test_image.jpg')
    processed = cv2.imread(processed_path)
    
    # Processed image should have different histogram
    assert not np.array_equal(original, processed)
    os.remove(processed_path)
```

### Property Test Examples

```python
# Feature: improve-answer-key-extraction-and-github-setup, Property 9: Validated Result Structure
@settings(max_examples=100)
@given(raw_result=st.dictionaries(
    keys=st.integers(min_value=-10, max_value=100),
    values=st.text(min_size=0, max_size=5)
))
def test_validated_results_have_correct_structure(raw_result):
    """For any raw extraction result, validated results must have 
    positive integer keys and A-E values."""
    validated, warnings = validate_extraction_result(raw_result)
    
    for question_num, answer in validated.items():
        assert isinstance(question_num, int)
        assert question_num > 0
        assert answer in {'A', 'B', 'C', 'D', 'E'}
    
    assert len(validated) == len(set(validated.keys()))  # No duplicates

# Feature: improve-answer-key-extraction-and-github-setup, Property 11: Duplicate Question Deduplication
@settings(max_examples=100)
@given(questions=st.lists(st.integers(min_value=1, max_value=50), min_size=1))
def test_duplicate_questions_keep_first_occurrence(questions):
    """For any list with duplicate questions, only first occurrence is kept."""
    # Create raw result with duplicates
    raw_result = {str(q): 'A' for q in questions}
    validated, warnings = validate_extraction_result(raw_result)
    
    # Check that first occurrence is preserved
    seen = set()
    for q in questions:
        if q not in seen:
            assert q in validated
            seen.add(q)
        else:
            # Duplicate should not override first
            pass
```

### Integration Testing

Integration tests verify:
- End-to-end extraction flow from API to response
- File upload and cleanup
- Ollama communication
- Log file writing
- Error propagation through layers

### Performance Testing

Performance tests verify:
- Extraction completes within timeout (default 30s)
- Preprocessing completes within 2s
- Memory usage stays reasonable (< 500MB per request)
- Concurrent requests handled correctly

### GitHub Repository Testing

For GitHub setup, manual verification checklist:
- [ ] Repository created at correct URL
- [ ] Repository is public
- [ ] All source files committed
- [ ] README.md contains all required sections
- [ ] .gitignore excludes all specified patterns
- [ ] requirements.txt is present and complete
- [ ] Repository structure matches specification

## Implementation Approach

### Phase 1: Image Preprocessing Enhancement

**Files to Modify**: `backend/ollama_client.py`

**Steps**:
1. Add `preprocess_image()` function with OpenCV operations
2. Add `convert_pdf_to_image()` enhancement for higher DPI
3. Integrate preprocessing into `extract_answer_key_from_image()` at the start
4. Add preprocessing logging
5. Ensure temporary file cleanup

**Testing**: Unit tests for preprocessing functions, verify image enhancement

### Phase 2: Multi-Pass Extraction Logic

**Files to Modify**: `backend/ollama_client.py`

**Steps**:
1. Define multiple prompt strategies (PROMPT_PASS_1, PROMPT_PASS_2, PROMPT_PASS_3)
2. Refactor extraction to loop through passes
3. Add timing measurement for each pass
4. Implement early exit on success
5. Add pass-specific logging

**Testing**: Property tests for multi-pass behavior, unit tests for each prompt strategy

### Phase 3: Validation Module

**Files to Modify**: `backend/ollama_client.py`

**Steps**:
1. Create `validate_extraction_result()` function
2. Implement question number validation (positive integers)
3. Implement answer validation (A-E only)
4. Implement duplicate removal (keep first)
5. Implement low count warning
6. Return validated dict and warnings list

**Testing**: Property tests for validation logic, unit tests for edge cases

### Phase 4: Enhanced Logging

**Files to Modify**: `backend/ollama_client.py`

**Steps**:
1. Create `ExtractionLogger` class
2. Add structured logging methods
3. Integrate logging throughout extraction flow
4. Add timing measurements
5. Add statistics tracking

**Testing**: Unit tests verify log entries are written correctly

### Phase 5: Configuration Support

**Files to Modify**: `backend/ollama_client.py`

**Steps**:
1. Create `ExtractionConfig` dataclass
2. Add config parameter to `extract_answer_key_from_image()`
3. Implement default config values
4. Use config values throughout extraction
5. Add config validation

**Testing**: Property tests verify config is respected, unit tests for defaults

### Phase 6: Alternative Model Support

**Files to Modify**: `backend/ollama_client.py`

**Steps**:
1. Add fallback model support to config
2. Implement model switching logic
3. Add model-specific logging
4. Test with multiple models (moondream, llava)

**Testing**: Unit tests with mocked models, integration tests with real models

### Phase 7: Backend API Error Handling

**Files to Modify**: `backend/app.py`

**Steps**:
1. Define error message templates
2. Update `/api/extract_key` endpoint with enhanced error handling
3. Map error types to HTTP status codes (404, 422, 500)
4. Add detailed error responses with suggestions
5. Add processing time to responses

**Testing**: Unit tests for each error scenario, verify status codes

### Phase 8: Frontend Error Display

**Files to Modify**: `frontend/index.html`, `frontend/style.css`

**Steps**:
1. Add error container to upload section
2. Implement `displayExtractionError()` function
3. Add CSS styling for error messages
4. Integrate with API error responses
5. Add error dismissal functionality

**Testing**: Manual testing of error display, verify styling

### Phase 9: GitHub Repository Setup

**Files to Create**: `.gitignore`, `README.md`, `docs/SETUP.md`, `docs/API.md`, `docs/TROUBLESHOOTING.md`

**Steps**:
1. Create comprehensive .gitignore file
2. Write detailed README.md with all sections
3. Create additional documentation files
4. Initialize git repository
5. Create GitHub repository
6. Push all files
7. Verify repository structure and documentation

**Testing**: Manual verification checklist

### Phase 10: Documentation and Testing

**Files to Create**: Test files in `backend/tests/`

**Steps**:
1. Write unit tests for all new functions
2. Write property-based tests for all properties
3. Write integration tests for end-to-end flow
4. Update documentation with examples
5. Add troubleshooting guide
6. Run full test suite and verify coverage

**Testing**: Achieve >80% code coverage for new code

### Migration Strategy

To ensure smooth transition:

1. **Backward Compatibility**: Existing API contracts remain unchanged
2. **Feature Flags**: New features can be enabled/disabled via config
3. **Gradual Rollout**: Deploy preprocessing first, then multi-pass, then validation
4. **Monitoring**: Track extraction success rates before and after changes
5. **Rollback Plan**: Keep previous version available for quick rollback if needed

### Deployment Checklist

- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Ollama models available (moondream, optionally llava)
- [ ] Log file permissions configured
- [ ] Temp directory cleanup verified
- [ ] Error messages reviewed for clarity
- [ ] GitHub repository created and documented
- [ ] Performance benchmarks met
- [ ] Backward compatibility verified

## Conclusion

This design provides a comprehensive enhancement to the answer key extraction system with robust error handling, multi-pass strategies, validation, and monitoring. The GitHub repository setup ensures the project is well-documented and accessible. The implementation approach is phased to allow incremental development and testing, with clear success criteria for each phase.

The dual testing strategy (unit tests + property-based tests) ensures both specific scenarios and universal properties are validated, providing high confidence in the system's correctness and reliability.
