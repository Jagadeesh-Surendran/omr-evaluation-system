# Frontend Integration Tests

This directory contains integration tests for the AI Question Solver frontend.

## Test Files

- `test_ai_solver_integration.js` - Integration tests for AI Solver workflow
- `test_runner.html` - HTML test runner for browser-based testing

## Running Tests

### Option 1: Browser-based Testing
1. Start the backend server: `python backend/app.py`
2. Open `test_runner.html` in a web browser
3. Tests will run automatically and display results

### Option 2: Automated Testing (Playwright/Puppeteer)
```bash
npm install
npm test
```

## Test Coverage

The integration tests cover:
- File upload and session creation flow
- WebSocket connection and progress updates
- Pause/resume/cancel controls
- Answer correction and note addition
- Filtering and sorting
- Approval workflow
- Export functionality

## Requirements

- Backend server running on http://localhost:5000
- Modern web browser with JavaScript enabled
- WebSocket support
