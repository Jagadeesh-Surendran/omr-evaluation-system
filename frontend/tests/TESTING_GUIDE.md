# Frontend Integration Testing Guide

## Overview

This directory contains comprehensive integration tests for the AI Question Solver frontend. The tests validate the complete user workflow from file upload through answer key approval and export.

## Test Coverage

### 1. File Upload and Session Creation (Test 1-2)
- ✅ PDF file upload creates a valid session
- ✅ Session status can be retrieved via API
- ✅ Session data contains required fields

### 2. WebSocket Connection and Progress Updates (Test 3)
- ✅ WebSocket connection establishes successfully
- ✅ Progress updates are received in real-time
- ✅ Session-specific updates are filtered correctly

### 3. Pause/Resume/Cancel Controls (Test 4-6)
- ✅ Active session can be paused
- ✅ Paused session can be resumed
- ✅ Session can be cancelled at any time
- ✅ State is preserved during pause/resume

### 4. Answer Correction and Note Addition (Test 7-8)
- ✅ Individual answers can be corrected
- ✅ Corrections are marked as manually verified
- ✅ Notes can be added to questions
- ✅ Notes persist with session data

### 5. Filtering and Sorting (Test 14-15)
- ✅ Questions can be filtered by confidence level
- ✅ Questions can be filtered by status (flagged, unsolvable, corrected)
- ✅ Questions can be sorted by number, confidence, or type
- ✅ Filter and sort operations preserve data integrity

### 6. Approval Workflow (Test 13)
- ✅ Completed sessions can be approved
- ✅ Approval requires all flagged questions to be reviewed
- ✅ Approval metadata is recorded (user, timestamp)
- ✅ Approved answer keys become immutable

### 7. Export Functionality (Test 9-12)
- ✅ Answer keys can be exported as JSON
- ✅ Answer keys can be exported as CSV
- ✅ Answer keys can be exported as PDF
- ✅ Exports include all required metadata
- ✅ Answer keys can be used directly for OMR evaluation

## Running the Tests

### Prerequisites

1. **Backend Server**: The backend must be running on `http://localhost:5000`
   ```bash
   cd backend
   python app.py
   ```

2. **Ollama Service**: Ollama must be running for AI solver functionality
   ```bash
   ollama serve
   ```

3. **Modern Browser**: Chrome, Firefox, Edge, or Safari with JavaScript enabled

### Method 1: Browser-Based Testing (Recommended)

1. Start the backend server (see prerequisites)

2. Open the test runner in your browser:
   ```bash
   # From the project root
   open frontend/tests/test_runner.html
   # Or navigate to: file:///path/to/frontend/tests/test_runner.html
   ```

3. Click "▶ Run All Tests" button

4. Watch the tests execute in real-time with visual feedback

5. Review results:
   - Green checkmarks (✓) indicate passed tests
   - Red X marks (✗) indicate failed tests
   - Error messages are displayed below failed tests
   - Console output shows detailed execution logs

### Method 2: Command Line Testing (Node.js)

If you prefer automated testing:

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run tests:
   ```bash
   npm test
   ```

3. View results in terminal output

### Method 3: Automated Browser Testing (Playwright)

For CI/CD integration:

1. Install Playwright:
   ```bash
   npm install -D @playwright/test
   ```

2. Create test configuration (see `playwright.config.js`)

3. Run tests:
   ```bash
   npx playwright test
   ```

## Test Structure

### Test Files

- **`test_ai_solver_integration.js`**: Core test suite with 15 integration tests
- **`test_runner.html`**: Visual test runner with real-time feedback
- **`README.md`**: Quick reference guide
- **`TESTING_GUIDE.md`**: This comprehensive guide

### Test Organization

Each test follows this structure:

```javascript
runner.test('Test name', async () => {
    // 1. Setup: Create test data
    const sessionId = await uploadTestPDF();
    
    // 2. Execute: Perform action
    const response = await fetch(`${BACKEND_BASE}/api/endpoint`);
    
    // 3. Assert: Verify results
    assert(response.ok, 'Request should succeed');
    
    // 4. Cleanup: (automatic via session lifecycle)
});
```

## Troubleshooting

### Backend Connection Failed

**Error**: `Backend is not available`

**Solution**:
1. Verify backend is running: `curl http://localhost:5000/api/health`
2. Check for port conflicts
3. Review backend logs for errors

### WebSocket Connection Failed

**Error**: `WebSocket connection failed`

**Solution**:
1. Ensure backend supports WebSocket connections
2. Check firewall settings
3. Verify Socket.IO is properly configured

### Test Timeouts

**Error**: `Timeout waiting for status`

**Solution**:
1. Increase `TEST_TIMEOUT` constant in test file
2. Check Ollama service is running and responsive
3. Verify system resources are sufficient

### PDF Upload Failed

**Error**: `Upload failed: 400`

**Solution**:
1. Check PDF file format is valid
2. Verify backend accepts PDF uploads
3. Review backend validation rules

## Writing New Tests

To add new integration tests:

1. Open `test_ai_solver_integration.js`

2. Add a new test using the runner:

```javascript
runner.test('Your test name', async () => {
    // Test implementation
    const sessionId = await uploadTestPDF();
    
    // Your test logic here
    const response = await fetch(`${BACKEND_BASE}/api/your-endpoint`);
    assert(response.ok, 'Your assertion message');
});
```

3. Use assertion helpers:
   - `assert(condition, message)` - General assertion
   - `assertEquals(actual, expected, message)` - Equality check
   - `assertNotNull(value, message)` - Null check

4. Follow async/await patterns for API calls

5. Clean up resources (sessions auto-cleanup on backend)

## Best Practices

### 1. Test Isolation
- Each test should be independent
- Don't rely on state from previous tests
- Create fresh test data for each test

### 2. Async Handling
- Always use `async/await` for API calls
- Handle promise rejections properly
- Use timeouts to prevent hanging tests

### 3. Error Messages
- Provide clear, descriptive error messages
- Include expected vs actual values
- Add context about what was being tested

### 4. Test Data
- Use realistic test data
- Cover edge cases (empty, null, invalid)
- Test boundary conditions

### 5. Performance
- Keep tests fast (< 30 seconds each)
- Use appropriate timeouts
- Parallelize when possible

## Continuous Integration

### GitHub Actions Example

```yaml
name: Frontend Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
      
      - name: Start backend
        run: |
          cd backend
          python app.py &
          sleep 5
      
      - name: Run tests
        run: |
          npm install
          npm test
```

## Test Results Interpretation

### Success Criteria

All tests should pass (15/15) for a successful test run:
- ✅ All green checkmarks
- ✅ No error messages
- ✅ Summary shows "All Tests Passed"

### Partial Failure

If some tests fail:
1. Review error messages for each failed test
2. Check if backend/Ollama services are running
3. Verify test data is valid
4. Check for timing issues (increase timeouts if needed)

### Complete Failure

If all tests fail:
1. Verify backend is accessible at `http://localhost:5000`
2. Check CORS settings allow frontend requests
3. Review backend logs for errors
4. Ensure all dependencies are installed

## Support

For issues or questions:
1. Check this guide first
2. Review backend logs
3. Check browser console for errors
4. Verify all prerequisites are met
5. Create an issue with:
   - Test output/screenshots
   - Backend logs
   - Browser console errors
   - System information

## Future Enhancements

Planned improvements:
- [ ] Visual regression testing
- [ ] Performance benchmarking
- [ ] Accessibility testing
- [ ] Mobile responsiveness tests
- [ ] Cross-browser compatibility tests
- [ ] Load testing for concurrent users
