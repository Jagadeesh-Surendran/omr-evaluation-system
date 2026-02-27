# Implementation Plan: Enhanced Answer Key Extraction and GitHub Setup

## Overview

This implementation plan breaks down the enhancement of the answer key extraction system into discrete coding tasks. The implementation will add image preprocessing, multi-pass extraction with fallback strategies, comprehensive validation, enhanced error handling, detailed logging, and GitHub repository setup. Each task builds incrementally on previous work to ensure continuous integration and early validation.

## Tasks

- [ ] 1. Set up image preprocessing infrastructure
  - [x] 1.1 Implement image preprocessing function in ollama_client.py
    - Add `preprocess_image()` function with OpenCV operations (CLAHE, bilateral filter, resize)
    - Add temporary file management for preprocessed images
    - Add preprocessing logging
    - _Requirements: 2.1, 2.2, 2.3, 2.5_
  
  - [x] 1.2 Write property test for image preprocessing
    - **Property 6: Image Dimension Normalization**
    - **Validates: Requirements 2.3**
  
  - [x] 1.3 Write property test for original file preservation
    - **Property 8: Original File Preservation**
    - **Validates: Requirements 2.5**
  
  - [x] 1.4 Implement PDF to high-resolution image conversion
    - Add `convert_pdf_to_image()` function using PyMuPDF with configurable DPI
    - Ensure minimum 200 DPI conversion
    - Add temporary file cleanup
    - _Requirements: 2.4_
  
  - [ ] 1.5 Write property test for PDF conversion
    - **Property 7: PDF High-Resolution Conversion**
    - **Validates: Requirements 2.4**
  
  - [ ] 1.6 Write unit tests for preprocessing edge cases
    - Test with corrupted images, unsupported formats, very large images
    - Test temporary file cleanup on errors
    - _Requirements: 2.1, 2.5_

- [ ] 2. Implement extraction configuration system
  - [x] 2.1 Create ExtractionConfig dataclass in ollama_client.py
    - Define all configuration parameters (max_passes, timeout, models, DPI, etc.)
    - Implement default values
    - Add configuration validation
    - _Requirements: 5.1, 10.1, 10.2, 10.4_
  
  - [ ] 2.2 Write property test for configuration parameter respect
    - **Property 13: Configuration Parameter Respect**
    - **Validates: Requirements 5.1, 10.1, 10.2, 10.3_
  
  - [ ] 2.3 Write property test for default configuration
    - **Property 16: Default Configuration Values**
    - **Validates: Requirements 10.4**
  
  - [ ] 2.4 Write unit tests for configuration validation
    - Test invalid configuration values (negative timeouts, invalid model names)
    - Test configuration merging with defaults
    - _Requirements: 5.1, 10.1_

- [ ] 3. Implement validation module
  - [x] 3.1 Create validate_extraction_result() function in ollama_client.py
    - Validate question numbers are positive integers
    - Validate answers are A-E only
    - Remove duplicate question numbers (keep first)
    - Generate warnings for low count (< 5 pairs)
    - Return tuple of (cleaned_dict, warnings_list)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ] 3.2 Write property test for validated result structure
    - **Property 9: Validated Result Structure**
    - **Validates: Requirements 3.1, 3.2, 3.5**
  
  - [ ] 3.3 Write property test for duplicate deduplication
    - **Property 11: Duplicate Question Deduplication**
    - **Validates: Requirements 3.4**
  
  - [ ] 3.4 Write property test for low count warning
    - **Property 10: Low Count Warning**
    - **Validates: Requirements 3.3**
  
  - [ ] 3.5 Write unit tests for validation edge cases
    - Test empty results, single question, all invalid answers
    - Test mixed valid/invalid data
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement structured logging system
  - [x] 5.1 Create ExtractionLogger class in ollama_client.py
    - Implement log_attempt_start() method
    - Implement log_attempt_result() method
    - Implement log_preprocessing() method
    - Implement log_validation_warnings() method
    - Implement log_final_result() method
    - Use structured log format with timestamps
    - _Requirements: 1.5, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5, 10.5_
  
  - [ ] 5.2 Write property test for comprehensive logging
    - **Property 4: Comprehensive Extraction Logging**
    - **Validates: Requirements 1.5, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5**
  
  - [ ] 5.3 Write property test for preprocessing logging
    - **Property 5: Preprocessing Before Extraction**
    - **Validates: Requirements 2.1, 2.2**
  
  - [ ] 5.4 Write property test for skip logging
    - **Property 17: Skip Logging**
    - **Validates: Requirements 10.5**
  
  - [ ] 5.5 Write unit tests for logging behavior
    - Test log file creation and permissions
    - Test log rotation if implemented
    - Test logging with different log levels
    - _Requirements: 1.5, 6.1_

- [ ] 6. Implement multi-pass extraction logic
  - [x] 6.1 Define multiple prompt strategies in ollama_client.py
    - Create PROMPT_PASS_1 (detailed JSON prompt)
    - Create PROMPT_PASS_2 (simplified prompt)
    - Create PROMPT_PASS_3 (alternative phrasing)
    - Document each prompt's purpose
    - _Requirements: 1.1, 1.2_
  
  - [x] 6.2 Refactor extract_answer_key_from_image() for multi-pass extraction
    - Add config parameter with default None
    - Integrate preprocessing at start
    - Implement loop through extraction passes
    - Add timing measurement for each pass
    - Implement early exit on success
    - Add pass-specific logging using ExtractionLogger
    - Try JSON parsing first, fallback to regex for each pass
    - Return best result or empty dict
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [ ] 6.3 Write property test for multi-pass attempts
    - **Property 1: Multi-Pass Extraction Attempts**
    - **Validates: Requirements 1.1, 1.2**
  
  - [ ] 6.4 Write property test for non-empty success results
    - **Property 2: Non-Empty Success Results**
    - **Validates: Requirements 1.3**
  
  - [ ] 6.5 Write property test for error messages on failure
    - **Property 3: Error Messages on Complete Failure**
    - **Validates: Requirements 1.4**
  
  - [ ] 6.6 Write unit tests for each prompt strategy
    - Mock Ollama responses for each prompt
    - Test JSON parsing and regex fallback
    - Test early exit behavior
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 7. Implement alternative vision model support
  - [x] 7.1 Add fallback model support to ExtractionConfig
    - Add fallback_model optional parameter
    - Update extraction logic to use fallback model on primary failure
    - Add model-specific logging
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ] 7.2 Write property test for fallback model usage
    - **Property 14: Fallback Model Usage**
    - **Validates: Requirements 5.2, 5.4**
  
  - [ ] 7.3 Write property test for multi-model support
    - **Property 15: Multi-Model Support**
    - **Validates: Requirements 5.5**
  
  - [ ] 7.4 Write unit tests for model switching
    - Mock multiple models (moondream, llava)
    - Test fallback behavior when primary fails
    - Test logging of model usage
    - _Requirements: 5.2, 5.3, 5.4_

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Enhance backend API error handling
  - [x] 9.1 Define error message templates in app.py
    - Create ERROR_MESSAGES dictionary with all error types
    - Include error, error_type, and suggestions for each
    - Cover: no_file, file_not_found, extraction_failed, poor_quality, processing_error
    - _Requirements: 4.1, 4.2, 4.5_
  
  - [x] 9.2 Update /api/extract_key endpoint with enhanced error handling
    - Add try-except blocks for different error types
    - Map error types to HTTP status codes (404, 422, 500)
    - Return structured error responses with suggestions
    - Add processing time to success responses
    - Add warnings to success responses
    - _Requirements: 4.1, 4.2, 4.4, 4.5_
  
  - [ ] 9.3 Write property test for error status code mapping
    - **Property 12: Error Type to Status Code Mapping**
    - **Validates: Requirements 4.4, 4.5**
  
  - [ ] 9.4 Write unit tests for each error scenario
    - Test no file provided (400)
    - Test file not found (404)
    - Test extraction failure with zero results (422)
    - Test server errors (500)
    - Verify error response structure
    - _Requirements: 4.1, 4.2, 4.4, 4.5_

- [ ] 10. Enhance frontend error display
  - [x] 10.1 Add error container to frontend/index.html
    - Add error display div in upload section
    - Ensure proper placement and initial hidden state
    - _Requirements: 4.3_
  
  - [x] 10.2 Implement displayExtractionError() function in index.html
    - Parse error response from API
    - Create error message HTML with icon
    - Display suggestions list if present
    - Show/hide error container appropriately
    - _Requirements: 4.3_
  
  - [x] 10.3 Add error styling to frontend/style.css
    - Style error-message container
    - Style error-header with icon
    - Style error-suggestions list
    - Ensure responsive design
    - _Requirements: 4.3_
  
  - [x] 10.4 Integrate error display with API calls
    - Update fetch error handling to call displayExtractionError()
    - Handle different HTTP status codes
    - Clear errors on new upload
    - _Requirements: 4.3_
  
  - [ ] 10.5 Write manual test checklist for frontend errors
    - Test display of each error type
    - Test error dismissal
    - Test error styling on different screen sizes
    - _Requirements: 4.3_

- [-] 11. Create GitHub repository documentation
  - [x] 11.1 Create comprehensive .gitignore file
    - Exclude Python cache and build files
    - Exclude virtual environments
    - Exclude IDE files
    - Exclude project-specific files (temp_uploads, debug logs, model weights)
    - Exclude data directories
    - _Requirements: 7.5_
  
  - [x] 11.2 Create detailed README.md
    - Add project title and description
    - Add features list
    - Add prerequisites section
    - Add installation instructions (clone, venv, pip install)
    - Add Ollama setup instructions
    - Add usage instructions (run server, access frontend)
    - Add project structure overview
    - Add configuration section
    - Add troubleshooting section
    - Add license and author information
    - _Requirements: 7.4, 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [x] 11.3 Create docs/SETUP.md with detailed setup guide
    - Detailed environment setup
    - Dependency installation troubleshooting
    - Ollama configuration details
    - _Requirements: 8.2_
  
  - [x] 11.4 Create docs/API.md with API documentation
    - Document /api/extract_key endpoint
    - Document request/response formats
    - Document error codes and messages
    - _Requirements: 8.2_
  
  - [x] 11.5 Create docs/TROUBLESHOOTING.md
    - Common issues and solutions
    - Ollama connection problems
    - Extraction failure guidance
    - Performance optimization tips
    - _Requirements: 8.2_

- [ ] 12. Set up GitHub repository
  - [-] 12.1 Initialize git repository and create GitHub repo
    - Run git init if not already initialized
    - Create .gitignore before first commit
    - Create initial commit with all source files
    - Create GitHub repository under "Jagadeesh-Surendran"
    - Set repository to public
    - Push all files to GitHub
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [~] 12.2 Verify repository structure and documentation
    - Verify all source files are present
    - Verify README.md displays correctly
    - Verify .gitignore excludes correct files
    - Verify requirements.txt is complete
    - Verify documentation files are accessible
    - _Requirements: 7.3, 7.4, 7.5, 8.1, 9.1, 9.2_
  
  - [~] 12.3 Add repository metadata
    - Add repository description
    - Add topics/tags (omr, ai, opencv, flask, ollama)
    - Add license if applicable
    - _Requirements: 7.2, 9.5_

- [ ] 13. Final integration and testing
  - [~] 13.1 Run full test suite
    - Run all unit tests
    - Run all property-based tests
    - Verify test coverage > 80% for new code
    - _Requirements: All_
  
  - [~] 13.2 Perform end-to-end integration testing
    - Test complete extraction flow with real images
    - Test with various image qualities and formats
    - Test error scenarios (missing file, poor quality, no answers)
    - Test with PDF files
    - Verify logging output
    - Verify frontend error display
    - _Requirements: All_
  
  - [~] 13.3 Performance validation
    - Verify extraction completes within timeout (30s default)
    - Verify preprocessing completes within 2s
    - Test concurrent requests
    - _Requirements: 6.2, 10.2_
  
  - [~] 13.4 Documentation review
    - Verify README instructions work for fresh setup
    - Verify all documentation is accurate and complete
    - Test setup instructions on clean environment
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [~] 14. Final checkpoint - Deployment readiness
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation uses Python as specified in the design document
- All code changes maintain backward compatibility with existing API contracts
- GitHub repository setup tasks (11-12) can be performed independently after core functionality is complete
