# Integration Tests for AI Question Solver API Endpoints

## Overview

This document describes the comprehensive integration tests implemented for the AI Question Solver API endpoints in `test_api_solver_endpoints.py`.

## Test Coverage

The integration tests cover all requirements specified in task 11.11:

### 1. Complete Workflow Tests (`TestCompleteWorkflow`)
- **test_complete_workflow_success**: Tests the entire workflow from upload through export
  - Upload PDF → Check status (processing) → Pause → Resume → Wait for completion → Approve → Export
  - Validates each step returns correct status codes and data structures
  
- **test_workflow_with_manual_corrections**: Tests workflow with manual answer corrections
  - Simulates low-confidence answers requiring manual review
  - Tests updating multiple answers
  - Verifies corrections are tracked

### 2. Authentication Tests (`TestAuthenticationAuthorization`)
Tests that all endpoints require authentication:
- Upload endpoint
- Session status endpoint
- Pause/resume/cancel endpoints
- Update answer endpoint
- Approve endpoint (requires admin)
- Export endpoint

**Note**: Current implementation has authentication disabled for development. Tests document expected behavior when authentication is enabled.

### 3. Authorization Tests
- **test_approve_requires_auth_and_admin**: Verifies only admin users can approve answer keys
- **test_approve_with_non_admin_user**: Tests that non-admin users are rejected

### 4. Error Response Tests (`TestErrorResponses`)
Comprehensive error handling validation:
- **Upload errors**: Missing file, non-PDF file, Ollama unavailable
- **Session errors**: Invalid session ID, session not found
- **State errors**: Pause already paused, resume not paused, cancel completed
- **Validation errors**: Invalid question number, invalid answer option
- **Approval errors**: Incomplete session, unflagged questions not reviewed
- **Export errors**: Invalid format, non-completed session

### 5. WebSocket Tests (`TestWebSocketProgress`)
- **test_websocket_subscribe_progress**: Verifies WebSocket endpoint exists
- **test_progress_update_format**: Validates progress message structure includes:
  - current_question, total_questions
  - processed_count, solved_count, unsolvable_count
  - elapsed_time, estimated_remaining

### 6. Concurrent Session Tests (`TestConcurrentSessions`)
- **test_concurrent_session_limit**: Validates 2 concurrent session limit
  - Creates 2 sessions successfully
  - Third session is queued or rejected (503)
  
- **test_session_queue_notification**: Tests queue position notifications
  - Queued sessions receive queue_position in status

### 7. Edge Case Tests (`TestEdgeCases`)
- **test_export_large_answer_key**: Tests exporting 500-question answer key
- **test_rapid_answer_updates**: Tests rapid successive updates to same question
- **test_session_with_all_unsolvable_questions**: Tests session where all questions fail
- **test_cancel_already_completed_session**: Tests canceling completed session

## Test Requirements

### Environment Setup

These tests require a properly initialized Flask application. The app initialization requires:

1. **YOLO Weights**: The FullOMREvaluator requires YOLO model weights at:
   ```
   backend/tests/yolov8_runs/omr_yolov8n/weights/best.pt
   ```

2. **Dependencies**: All Python dependencies from `requirements.txt`

3. **Ollama Service** (for some tests): Local Ollama service running

### Running the Tests

**With Full Environment**:
```bash
cd backend
python -m pytest tests/test_api_solver_endpoints.py -v
```

**Current Behavior**:
- Tests are automatically skipped if Flask app cannot be initialized
- Skip reason is displayed: "Flask app not available: [error message]"
- This is expected in environments without YOLO weights

**To Enable Tests**:
1. Train or download YOLO weights to the expected path
2. Ensure all dependencies are installed
3. Run tests as shown above

## Test Structure

### Fixtures

- **client**: Flask test client fixture
  - Configures app in TESTING mode
  - Provides test client for making requests

- **mock_session**: Mock SessionState object
  - Pre-configured with test data
  - Used across multiple tests

### Mocking Strategy

Tests use extensive mocking to isolate API endpoint logic:
- `session_manager` methods (get_session, pause_session, etc.)
- `answer_key_generator` methods (generate_json, generate_csv, etc.)
- `OllamaClient` for service availability checks
- `QuestionParser` for PDF processing

This allows testing API logic without requiring:
- Real PDF files
- Actual AI model calls
- Real session processing

## Requirements Validation

These tests validate the following requirements:

- **Requirement 9.1-9.6**: Progress tracking, pause/resume/cancel functionality
- **Requirement 11.5**: Concurrent session limiting (max 2)
- **Requirement 11.6**: Session queueing with position notification
- **Requirement 15.1**: Authentication enforcement on all endpoints
- **Requirement 15.2**: Authorization for approval endpoint (admin only)

## Test Metrics

- **Total Tests**: 46 integration tests
- **Test Classes**: 7 test classes organizing related tests
- **Coverage Areas**:
  - Complete workflow: 2 tests
  - Authentication/Authorization: 9 tests
  - Error responses: 12 tests
  - WebSocket: 2 tests
  - Concurrent sessions: 2 tests
  - Edge cases: 4 tests
  - Basic endpoint tests: 15 tests

## Future Enhancements

1. **Real WebSocket Testing**: Implement full WebSocket client tests using Flask-SocketIO test client
2. **Performance Tests**: Add tests for response time and throughput
3. **Load Tests**: Test system behavior under high concurrent load
4. **Integration with Real Ollama**: Tests with actual AI model calls (slower, more comprehensive)
5. **End-to-End Tests**: Tests with real PDF files and complete processing

## Notes

- Tests are designed to be fast and reliable through extensive mocking
- Tests document expected behavior even when features are not fully implemented (e.g., authentication)
- Tests can run in CI/CD pipelines once environment is properly configured
- Skip mechanism ensures tests don't fail in incomplete environments
