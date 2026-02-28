# Implementation Plan: AI Question Solver

## Overview

This implementation plan converts the AI Question Solver design into actionable coding tasks. The feature extends the existing OMR Evaluation System to automatically generate answer keys from question bank PDFs using AI models. Implementation follows a bottom-up approach: core modules first, then orchestration, then API/UI integration.

The system integrates with existing infrastructure (PyMuPDF, Ollama, Flask) and introduces 6 new modules: Question Parser, AI Solver, Model Selector, Validation Engine, Session Manager, and Answer Key Generator. Testing uses pytest for unit tests and hypothesis for property-based tests.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create directory structure for new modules and session storage
  - Add new dependencies to requirements.txt (hypothesis for property-based testing)
  - Create test fixtures directory structure
  - Set up logging configuration for solver modules
  - _Requirements: 10.6, 14.1_

- [x] 2. Implement Question Parser module
  - [x] 2.1 Create data models for questions and document classification
    - Implement QuestionOption, Question, and DocumentClassification dataclasses in backend/question_parser.py
    - Include all fields specified in design (number, text, options, page_number, has_image, image_data, question_type)
    - _Requirements: 2.1, 2.2, 2.7_

  - [x] 2.2 Implement document type classification
    - Write classify_document() method to analyze first 3 pages
    - Detect question patterns (numbers + options) vs answer key patterns (filled bubbles, answer lists)
    - Return DocumentClassification with confidence score
    - Handle low confidence cases (< 0.7)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 2.3 Write property test for document classification
    - **Property 1: Document Classification Correctness**
    - **Property 2: Classification Confidence Range**
    - **Property 3: Low Confidence Prompting**
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.5**

  - [x] 2.4 Implement question extraction from PDF
    - Write extract_questions() method to process all pages
    - Convert PDF pages to images using existing convert_pdf_to_image patterns
    - Extract question numbers, text, and options (A-E)
    - Detect and handle multi-page questions
    - Detect questions with images and store image_data
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 2.5 Implement question type detection
    - Write _detect_question_type() method using keyword analysis
    - Detect math (arithmetic, algebra, geometry, calculus keywords)
    - Detect logical (patterns, sequences, deduction keywords)
    - Detect factual (general knowledge patterns)
    - Detect visual (has_image flag)
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

  - [x] 2.6 Add error handling for parse failures
    - Implement try-catch around individual question parsing
    - Log parse errors and continue with remaining questions
    - Mark failed questions with "parse_failed" status
    - _Requirements: 2.6, 10.2_

  - [x] 2.7 Write property tests for question extraction
    - **Property 4: Complete Question Extraction**
    - **Property 5: Mathematical Notation Preservation**
    - **Property 6: Multi-Page Question Combination**
    - **Property 7: Image Detection and Inclusion**
    - **Property 8: Parse Error Recovery**
    - **Validates: Requirements 2.1-2.6**

  - [x] 2.8 Write unit tests for Question Parser
    - Test classify_document with sample PDFs (question bank vs answer key)
    - Test extract_questions with known question counts
    - Test multi-page question handling
    - Test image detection
    - Test error recovery
    - _Requirements: 2.1-2.6_

- [x] 3. Checkpoint - Verify Question Parser
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Model Selector module
  - [x] 4.1 Create ModelSelector class with model mapping
    - Implement ModelSelector in backend/ai_solver.py
    - Define model_map for question types (math→llama3.2, visual→moondream, etc.)
    - Set default_model as fallback
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 4.2 Implement model selection logic
    - Write select_model() method based on question.question_type
    - Return appropriate model name from model_map
    - Fall back to default_model if type not in map
    - _Requirements: 3.2, 3.3_

  - [x] 4.3 Implement model availability checking
    - Write is_model_available() method to check Ollama service
    - Query Ollama for available models
    - Implement fallback logic when model unavailable
    - Log warnings for fallback usage
    - _Requirements: 3.5, 3.6_

  - [x] 4.4 Write unit tests for Model Selector
    - Test select_model for each question type
    - Test fallback when model unavailable
    - Test vision capability validation
    - _Requirements: 3.2, 3.3, 3.5, 3.6_

- [x] 5. Implement AI Solver module
  - [x] 5.1 Create data models for solver configuration and results
    - Implement SolverConfig dataclass with timeout, retries, backoff settings
    - Implement SolverResult dataclass with question_number, selected_option, explanation, confidence, status, error_message
    - _Requirements: 4.1, 4.2, 4.4, 4.5_

  - [x] 5.2 Implement prompt engineering for AI solver
    - Write _build_prompt() method to construct structured prompts
    - Include question text, all options, and response format instructions
    - Handle image-based questions with vision model prompts
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 5.3 Implement AI response parsing
    - Write _parse_ai_response() method to extract answer and explanation
    - Parse "ANSWER: [A/B/C/D/E]" and "EXPLANATION: [text]" format
    - Handle malformed responses gracefully
    - _Requirements: 4.2, 4.4_

  - [x] 5.4 Implement core solve_question method
    - Write solve_question() method with timeout enforcement (30s)
    - Integrate ModelSelector for model selection
    - Call Ollama using existing ollama_client patterns
    - Parse response and create SolverResult
    - Track processing time
    - _Requirements: 4.1, 4.2, 4.3, 4.6_

  - [x] 5.5 Implement retry logic with exponential backoff
    - Add retry loop (max 2 retries) around Ollama calls
    - Implement exponential backoff (2^attempt seconds)
    - Retry on connection errors, timeouts, invalid responses
    - Mark as "solver_error" after all retries fail
    - _Requirements: 10.3, 10.4_

  - [x] 5.6 Handle unsolvable questions and timeouts
    - Detect when AI indicates uncertainty or cannot solve
    - Mark status as "unsolvable" with reason
    - Handle timeout exceptions and mark status as "timeout"
    - Continue processing next question after errors
    - _Requirements: 4.5, 4.6, 4.7_

  - [x] 5.7 Write property tests for AI Solver
    - **Property 12: Valid Answer Option Selection**
    - **Property 13: Explanation Generation**
    - **Property 14: Unsolvable Question Handling**
    - **Property 15: Timeout Enforcement and Handling**
    - **Property 36: Retry Logic with Exponential Backoff**
    - **Validates: Requirements 4.2, 4.4, 4.5, 4.6, 4.7, 10.3, 10.4**

  - [x] 5.8 Write unit tests for AI Solver
    - Test solve_question with mocked Ollama responses
    - Test timeout handling
    - Test retry logic
    - Test unsolvable question detection
    - Test prompt building for different question types
    - _Requirements: 4.1-4.7, 10.3, 10.4_

- [x] 6. Checkpoint - Verify AI Solver
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement Validation Engine module
  - [x] 7.1 Create data models for validation
    - Implement ValidationIssue dataclass with question_number, severity, issue_type, description
    - Implement ValidationReport dataclass with total_questions, issues, flagged_questions, average_confidence
    - _Requirements: 6.6_

  - [x] 7.2 Implement confidence score calculation
    - Write calculate_confidence() method analyzing multiple factors
    - Factor in explanation quality (length, specificity)
    - Detect uncertainty indicators ("possibly", "might be", "unclear")
    - Consider processing time (very fast/slow = lower confidence)
    - Return score between 0.0 and 1.0
    - _Requirements: 5.1, 5.2_

  - [x] 7.3 Implement single answer validation
    - Write validate_answer() method for individual answers
    - Check selected option exists in question's option list
    - Verify explanation doesn't contradict selected answer
    - Detect uncertainty phrases in explanation
    - Return list of ValidationIssue objects
    - _Requirements: 6.1, 6.3, 6.5_

  - [x] 7.4 Implement batch validation with cross-question checks
    - Write validate_batch() method for all answers
    - Detect duplicate questions with different answers
    - Calculate average confidence across all questions
    - Flag low confidence answers (< 0.6) for mandatory review
    - Categorize confidence levels (high/medium/low)
    - Generate comprehensive ValidationReport
    - _Requirements: 5.3, 5.4, 6.2, 6.6_

  - [x] 7.5 Write property tests for Validation Engine
    - **Property 16: Confidence Score Range**
    - **Property 17: Low Confidence Flagging**
    - **Property 18: Confidence Categorization**
    - **Property 20: Duplicate Question Consistency**
    - **Property 21: Uncertainty Detection in Explanations**
    - **Property 22: Validation Report Structure**
    - **Validates: Requirements 5.1, 5.3, 5.4, 6.2, 6.5, 6.6**

  - [x] 7.6 Write unit tests for Validation Engine
    - Test confidence calculation with various inputs
    - Test uncertainty detection with sample phrases
    - Test duplicate question detection
    - Test validation report generation
    - _Requirements: 5.1-5.4, 6.1-6.6_

- [x] 8. Implement Session Manager module
  - [x] 8.1 Create data models for session state
    - Implement SessionState dataclass with all fields (session_id, status, pdf_path, counts, timestamps, questions, results, validation_report, user_corrections, user_notes)
    - Define session status enum values (pending, processing, paused, completed, cancelled, error)
    - _Requirements: 9.3, 9.4_

  - [x] 8.2 Implement session creation and initialization
    - Write create_session() method to generate unique session_id
    - Initialize session directory structure in backend/solver_sessions/{session_id}/
    - Create session locks for concurrent access control
    - _Requirements: 15.4_

  - [x] 8.3 Implement background processing orchestration
    - Write start_processing() method to run solver workflow in background thread
    - Coordinate Question Parser, AI Solver, and Validation Engine
    - Process questions sequentially with progress tracking
    - Handle pause/resume/cancel signals during processing
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 8.4 Implement pause and resume functionality
    - Write pause_session() method to set pause flag and wait for current question to complete
    - Write resume_session() method to continue from last processed question
    - Ensure all state is preserved during pause (processed_count, results, validation_report)
    - _Requirements: 9.3, 9.4_

  - [x] 8.5 Implement cancel functionality
    - Write cancel_session() method to stop processing immediately
    - Discard partial results (do not save to disk)
    - Clean up session resources and temporary files
    - _Requirements: 9.5_

  - [x] 8.6 Implement manual answer correction
    - Write update_answer() method to modify specific question answer
    - Mark corrected answers as "manually verified" with confidence 1.0
    - Track original AI answer and corrected answer in user_corrections dict
    - _Requirements: 8.4, 14.4_

  - [x] 8.7 Implement note management
    - Write add_note() method to attach user comments to questions
    - Store notes in user_notes dict with question_number as key
    - Persist notes with session state
    - _Requirements: 8.8_

  - [x] 8.8 Implement session persistence
    - Write save_session() method to serialize SessionState to JSON
    - Save questions, results, and validation_report to separate JSON files
    - Implement automatic checkpoint saves every 10 questions
    - Write load_session() method to restore session from disk
    - _Requirements: 9.4, 10.7_

  - [x] 8.9 Implement WebSocket progress updates
    - Write _emit_progress() method to send progress messages via WebSocket
    - Include current_question, total_questions, elapsed_time, estimated_remaining
    - Calculate questions_per_minute and average_confidence
    - Emit updates every 5 seconds during processing
    - Emit completion event when all questions processed
    - _Requirements: 9.1, 9.2, 9.6_

  - [x] 8.10 Write unit tests for Session Manager
    - Test session creation and initialization
    - Test pause/resume state preservation
    - Test cancel and cleanup
    - Test manual corrections and notes
    - Test session persistence and recovery
    - Test concurrent access with locks
    - _Requirements: 9.3, 9.4, 9.5, 15.4_

- [x] 9. Checkpoint - Verify Session Manager
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement Answer Key Generator module
  - [x] 10.1 Create data models for answer key metadata
    - Implement AnswerKeyMetadata dataclass with all fields (session_id, generation_time, counts, average_confidence, approval info)
    - _Requirements: 7.3_

  - [x] 10.2 Implement JSON answer key generation
    - Write generate_json() method to create OMR-compatible format
    - Convert question numbers to 0-based indices
    - Convert answer options (A-E) to 0-based indices (0-4)
    - Include metadata, unsolvable list, and low_confidence list
    - _Requirements: 7.1, 7.2, 7.3, 7.5_

  - [x] 10.3 Implement CSV export generation
    - Write generate_csv() method with required columns
    - Include question_number, correct_answer, confidence, explanation, modified columns
    - Mark manually corrected answers with "modified" indicator
    - _Requirements: 7.4, 12.2, 12.4_

  - [x] 10.4 Implement PDF report generation
    - Write generate_pdf_report() method to create visual report
    - Show all questions with correct answers highlighted
    - Include confidence scores and flags (low confidence, unsolvable, manually corrected)
    - Use existing PDF processing patterns for layout
    - _Requirements: 12.3_

  - [x] 10.5 Implement answer key approval
    - Write approve_answer_key() method to mark as approved and immutable
    - Record approval metadata (approved_by, approved_at timestamp)
    - Prevent modifications to approved answer keys
    - _Requirements: 8.9, 15.2, 15.5_

  - [x] 10.6 Implement answer key retrieval
    - Write get_metadata() method to extract metadata from session
    - Store generated answer keys with timestamps
    - Allow retrieval of previous sessions by session_id
    - _Requirements: 12.6_

  - [x] 10.7 Write property tests for Answer Key Generator
    - **Property 23: OMR Format Compatibility**
    - **Property 24: Answer Key Metadata Completeness**
    - **Property 25: CSV Export Format**
    - **Property 26: Unsolvable Question Handling in Answer Key**
    - **Property 41: Multi-Format Export Compatibility**
    - **Property 42: Manual Correction Indicators**
    - **Property 53: Answer Key Immutability After Approval**
    - **Validates: Requirements 7.1-7.5, 12.1-12.4, 12.6, 15.5**

  - [x] 10.8 Write unit tests for Answer Key Generator
    - Test JSON format generation with various inputs
    - Test CSV export with all columns
    - Test PDF report generation
    - Test approval workflow and immutability
    - Test manual correction indicators in exports
    - _Requirements: 7.1-7.5, 12.1-12.6, 15.5_

- [x] 11. Implement Flask API endpoints
  - [x] 11.1 Create upload endpoint for PDF submission
    - Implement POST /api/solve/upload endpoint
    - Validate uploaded file is PDF format
    - Check Ollama service availability before accepting upload
    - Create new session and return session_id
    - Trigger document classification and question extraction
    - _Requirements: 1.1, 10.1_

  - [x] 11.2 Create session status endpoint
    - Implement GET /api/solve/session/<id> endpoint
    - Return complete session state including questions, results, validation_report
    - Include progress statistics and confidence scores
    - _Requirements: 9.2, 14.2_

  - [x] 11.3 Create session control endpoints
    - Implement POST /api/solve/session/<id>/pause endpoint
    - Implement POST /api/solve/session/<id>/resume endpoint
    - Implement POST /api/solve/session/<id>/cancel endpoint
    - Return success/error status for each operation
    - _Requirements: 9.3, 9.4, 9.5_

  - [x] 11.4 Create answer update endpoint
    - Implement PUT /api/solve/session/<id>/answer/<qnum> endpoint
    - Accept new answer option in request body
    - Validate answer option is valid (A-E)
    - Update session state and mark as manually verified
    - _Requirements: 8.3, 8.4_

  - [x] 11.5 Create answer key approval endpoint
    - Implement POST /api/solve/session/<id>/approve endpoint
    - Check user has administrator privileges
    - Verify all flagged questions have been reviewed
    - Mark answer key as approved and immutable
    - Log approval action with user_id and timestamp
    - _Requirements: 8.9, 15.2, 15.3, 15.5_

  - [x] 11.6 Create export endpoints
    - Implement GET /api/solve/session/<id>/export?format=json endpoint
    - Implement GET /api/solve/session/<id>/export?format=csv endpoint
    - Implement GET /api/solve/session/<id>/export?format=pdf endpoint
    - Return appropriate content-type headers for each format
    - _Requirements: 12.1, 12.2, 12.3_

  - [x] 11.7 Create direct OMR integration endpoint
    - Implement POST /api/solve/session/<id>/use-for-evaluation endpoint
    - Allow using generated answer key directly for OMR evaluation
    - Integrate with existing evaluate() endpoint workflow
    - _Requirements: 12.5_

  - [x] 11.8 Implement WebSocket endpoint for progress updates
    - Implement WebSocket /api/solve/progress endpoint
    - Handle client connections and subscriptions to session updates
    - Emit progress messages from Session Manager
    - Handle reconnection and message buffering
    - _Requirements: 9.1, 9.2, 9.6_

  - [x] 11.9 Add authentication and authorization middleware
    - Implement authentication check for all solver endpoints
    - Implement authorization check for approval endpoint (admin only)
    - Return 401 for unauthenticated requests
    - Return 403 for unauthorized approval attempts
    - _Requirements: 15.1, 15.2_

  - [x] 11.10 Implement error handling and logging
    - Add try-catch blocks around all endpoint handlers
    - Return consistent error response format (error, error_type, message, details, timestamp)
    - Log all errors with context (session_id, user_id, operation)
    - Implement service availability checks
    - _Requirements: 10.1, 10.6, 15.3_

  - [x] 11.11 Write integration tests for API endpoints
    - Test complete workflow: upload → status → pause → resume → approve → export
    - Test authentication on all endpoints
    - Test authorization for approval endpoint
    - Test error responses for invalid inputs
    - Test WebSocket connection and progress updates
    - Test concurrent session limits
    - _Requirements: 9.1-9.6, 11.5, 11.6, 15.1, 15.2_

- [x] 12. Checkpoint - Verify API endpoints
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement Frontend Review Interface
  - [x] 13.1 Create session upload and initialization UI
    - Build file upload component for PDF selection
    - Display document classification result with confidence
    - Show manual type selection when confidence < 0.7
    - Display question extraction progress
    - _Requirements: 1.5, 2.7_

  - [x] 13.2 Create real-time progress display
    - Build WebSocket client for progress updates
    - Display current question, total questions, elapsed time, estimated remaining
    - Show questions per minute and average confidence
    - Display progress bar with percentage complete
    - _Requirements: 9.1, 9.2_

  - [x] 13.3 Create session control panel
    - Add Pause, Resume, and Cancel buttons
    - Enable/disable buttons based on session status
    - Show confirmation dialog for cancel action
    - _Requirements: 9.3, 9.4, 9.5_

  - [x] 13.4 Create question review list view
    - Display all questions with AI-generated answers
    - Show confidence scores with color coding (green=high, yellow=medium, red=low)
    - Highlight flagged questions with visual indicators
    - Show question type icons (math, logical, factual, visual)
    - Display "manually verified" badge for corrected answers
    - _Requirements: 8.1, 8.2, 5.4_

  - [x] 13.5 Create question detail view
    - Display full question text with formatting preserved
    - Show all answer options (A-E)
    - Display question images if present
    - Show AI-selected answer with explanation
    - Show confidence score and validation issues
    - _Requirements: 8.6_

  - [x] 13.6 Create answer correction interface
    - Add radio buttons or dropdown for selecting different answer
    - Save button to submit correction
    - Display original AI answer and corrected answer side-by-side
    - Add text area for user notes
    - _Requirements: 8.3, 8.4, 8.8_

  - [x] 13.7 Create filtering and sorting controls
    - Add filter options: All, Low Confidence, Flagged, Unsolvable, Manually Corrected
    - Add sort options: Question Number, Confidence Score, Question Type
    - Update question list based on selected filters
    - _Requirements: 8.5_

  - [x] 13.8 Create progress statistics panel
    - Display total questions, solved count, unsolvable count, error count
    - Show reviewed count and remaining count
    - Display average confidence score
    - Show question type distribution chart
    - _Requirements: 8.7, 13.6, 14.2_

  - [x] 13.9 Create answer key approval interface
    - Add "Approve Answer Key" button (enabled only when all flagged questions reviewed)
    - Show approval confirmation dialog with summary statistics
    - Display approval status and metadata (approved_by, approved_at)
    - Disable editing after approval
    - _Requirements: 8.9, 15.2_

  - [x] 13.10 Create export interface
    - Add export buttons for JSON, CSV, and PDF formats
    - Show download progress for PDF generation
    - Add "Use for OMR Evaluation" button for direct integration
    - Display export history with timestamps
    - _Requirements: 12.1, 12.2, 12.3, 12.5, 12.6_

  - [x] 13.11 Create error display and recovery UI
    - Display error log panel with severity levels
    - Show per-question error details
    - Add retry button for failed questions
    - Display service availability status
    - _Requirements: 10.6_

  - [x] 13.12 Write integration tests for Frontend
    - Test file upload and session creation flow
    - Test WebSocket connection and progress updates
    - Test pause/resume/cancel controls
    - Test answer correction and note addition
    - Test filtering and sorting
    - Test approval workflow
    - Test export functionality
    - _Requirements: 8.1-8.9, 9.1-9.6, 12.1-12.6_

- [ ] 14. Implement concurrent session management
  - [x] 14.1 Add session queue management
    - Implement queue for sessions when at capacity (max 2 concurrent)
    - Track queue position for each waiting session
    - Notify users of queue position via WebSocket
    - Automatically start queued sessions when slots available
    - _Requirements: 11.5, 11.6_

  - [x] 14.2 Add resource monitoring
    - Monitor CPU and memory usage during processing
    - Implement resource limits per session
    - Reject new sessions if resources critically low
    - _Requirements: 10.7, 11.5_

  - [-] 14.3 Write tests for concurrent session handling
    - Test 2 concurrent sessions processing simultaneously
    - Test queueing when at capacity
    - Test queue position notifications
    - Test automatic session start from queue
    - _Requirements: 11.5, 11.6_

- [x] 15. Implement monitoring and analytics
  - [x] 15.1 Create comprehensive logging system
    - Log all AI solver responses with question, answer, confidence, processing_time, model_used
    - Log all user corrections with original and corrected answers
    - Log all approval actions with user_id and timestamp
    - Implement log rotation and retention policies
    - _Requirements: 14.1, 14.4, 15.3_

  - [x] 15.2 Create session statistics calculation
    - Calculate average confidence per session
    - Calculate percentage of questions requiring manual correction
    - Track question type distribution
    - Calculate processing time statistics
    - _Requirements: 14.2, 14.3, 13.6_

  - [x] 15.3 Create performance monitoring dashboard
    - Display solver statistics across all sessions
    - Show accuracy trends over time
    - Identify common failure patterns
    - Display model performance by question type
    - _Requirements: 14.5_

  - [x] 15.4 Write tests for monitoring and analytics
    - Test logging of all required events
    - Test statistics calculation accuracy
    - Test dashboard data aggregation
    - _Requirements: 14.1-14.5_

- [x] 16. Integration and end-to-end testing
  - [x] 16.1 Write end-to-end workflow tests
    - Test complete workflow: upload → classify → extract → solve → validate → review → approve → export
    - Test with various PDF formats (scanned, digital, mixed)
    - Test with different question bank sizes (10, 100, 500 questions)
    - Test with different question types (math, logical, factual, visual)
    - _Requirements: All requirements_

  - [x] 16.2 Write error recovery tests
    - Test recovery from Ollama service interruption
    - Test recovery from page conversion failures
    - Test recovery from AI solver timeouts
    - Test session recovery after crash
    - _Requirements: 10.1-10.7_

  - [x] 16.3 Write performance tests
    - Verify 2+ questions/minute for text questions
    - Verify 1+ questions/minute for image questions
    - Verify 100 questions extracted in < 60 seconds
    - Verify 500 question session completes successfully
    - _Requirements: 11.1-11.4_

  - [x] 16.4 Write security tests
    - Test authentication enforcement on all endpoints
    - Test authorization for approval endpoint
    - Test session locking prevents concurrent edits
    - Test answer key immutability after approval
    - _Requirements: 15.1-15.5_

- [-] 17. Documentation and deployment preparation
  - [x] 17.1 Create API documentation
    - Document all endpoints with request/response formats
    - Include authentication requirements
    - Provide example requests and responses
    - Document WebSocket message formats
    - _Requirements: All API requirements_

  - [x] 17.2 Create user guide
    - Document PDF upload and session creation
    - Explain confidence scores and validation flags
    - Provide guidance on reviewing and correcting answers
    - Document export formats and OMR integration
    - _Requirements: User-facing requirements_

  - [ ] 17.3 Create deployment guide
    - Document Ollama service setup and model installation
    - Document required dependencies and versions
    - Provide configuration examples
    - Document resource requirements and scaling considerations
    - _Requirements: 3.1, 11.5_

  - [ ] 17.4 Create troubleshooting guide
    - Document common errors and solutions
    - Provide debugging steps for service issues
    - Document log file locations and formats
    - Include performance tuning recommendations
    - _Requirements: 10.1-10.7_

- [ ] 18. Final checkpoint - Complete system verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- The implementation follows a bottom-up approach: core modules first, then orchestration, then API/UI
- All code should integrate with existing infrastructure (PyMuPDF, Ollama, Flask)
- Session state is persisted to enable pause/resume and crash recovery
- WebSocket provides real-time progress updates during long-running operations
- Manual review interface enables human oversight before answer key approval
- Multiple export formats ensure compatibility with existing OMR workflow