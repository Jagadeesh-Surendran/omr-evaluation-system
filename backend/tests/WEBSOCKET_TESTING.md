# WebSocket Testing Guide

This document explains how to test the WebSocket integration for real-time progress updates in the AI Question Solver.

## Overview

Task 13.2 implements real-time progress display using WebSocket (Socket.IO) for live updates during question solving sessions. The implementation includes:

1. **Backend**: Session manager emits progress updates via Flask-SocketIO
2. **Frontend**: WebSocket client connects and displays real-time progress
3. **Fallback**: Automatic fallback to polling if WebSocket connection fails

## Testing Approach

### 1. Manual Testing (Recommended)

The easiest way to test the WebSocket functionality is through manual testing:

**Steps:**
1. Start the Flask backend server:
   ```bash
   cd backend
   python app.py
   ```

2. Open the frontend in a browser:
   ```
   http://localhost:5000
   ```

3. Navigate to the AI Question Solver tab

4. Upload a PDF with questions

5. Observe the progress display:
   - Current question number updates in real-time
   - Total questions displayed
   - Elapsed time updates every second
   - Estimated remaining time calculated
   - Questions per minute metric
   - Average confidence percentage
   - Progress bar fills as questions are processed

6. Test pause/resume:
   - Click "Pause" - WebSocket should disconnect
   - Click "Resume" - WebSocket should reconnect and continue updates

7. Test cancel:
   - Click "Cancel" - WebSocket should disconnect and reset

**Expected Behavior:**
- Progress updates appear immediately without delay
- All metrics update smoothly in real-time
- No polling requests in browser network tab (only WebSocket frames)
- If WebSocket fails, system automatically falls back to polling

### 2. Automated Testing

Run the WebSocket test suite:

```bash
cd backend
python -m pytest tests/test_api_solver_endpoints.py::TestWebSocketProgress -v
```

**Note:** These tests require the Flask app to be fully importable. If YOLO weights are missing, tests will be skipped.

### 3. Manual Script Testing

Use the provided manual test script:

```bash
cd backend
python tests/test_websocket_manual.py
```

This script:
- Connects to the WebSocket server
- Tests error handling (missing session_id, invalid session_id)
- Can be extended to test with real session IDs

## WebSocket Message Format

### Subscribe Request
```json
{
  "session_id": "uuid-string"
}
```

### Progress Update Response
```json
{
  "session_id": "uuid-string",
  "status": "processing",
  "current_question": 45,
  "total_questions": 100,
  "processed_count": 45,
  "solved_count": 42,
  "unsolvable_count": 2,
  "error_count": 1,
  "elapsed_time_seconds": 1350,
  "estimated_remaining_seconds": 1650,
  "average_confidence": 0.78,
  "questions_per_minute": 2.0
}
```

### Error Response
```json
{
  "error": "Session not found"
}
```

## Verification Checklist

- [ ] WebSocket connection established on session start
- [ ] Progress updates received in real-time
- [ ] All metrics display correctly:
  - [ ] Current question number
  - [ ] Total questions
  - [ ] Elapsed time (MM:SS format)
  - [ ] Estimated remaining time (MM:SS format)
  - [ ] Questions per minute (decimal)
  - [ ] Average confidence (percentage)
  - [ ] Progress bar percentage
- [ ] Pause disconnects WebSocket
- [ ] Resume reconnects WebSocket
- [ ] Cancel disconnects WebSocket
- [ ] Completion disconnects WebSocket
- [ ] Error handling works (missing/invalid session_id)
- [ ] Fallback to polling works if WebSocket fails

## Browser Developer Tools

To verify WebSocket is working:

1. Open browser DevTools (F12)
2. Go to Network tab
3. Filter by "WS" (WebSocket)
4. You should see:
   - WebSocket connection to `ws://localhost:5000/socket.io/`
   - Frames showing progress_update messages
   - No polling requests (unless fallback is triggered)

## Troubleshooting

### WebSocket not connecting
- Check Flask-SocketIO is installed: `pip install flask-socketio`
- Check Socket.IO client library is loaded in HTML
- Check CORS settings in app.py
- Check browser console for errors

### Progress not updating
- Check session is actually processing (backend logs)
- Check WebSocket connection in browser DevTools
- Check session_manager._emit_progress is being called
- Verify socketio.emit is working (check backend logs)

### Fallback to polling
- This is expected behavior if WebSocket fails
- Check browser console for WebSocket errors
- Verify polling requests in Network tab
- System should still work, just with slight delay

## Requirements Validated

This implementation validates:
- **Requirement 9.1**: Real-time progress updates via WebSocket
- **Requirement 9.2**: Display current question, total, elapsed time, estimated remaining, questions/min, avg confidence
- **Property 30**: Progress updates emitted at regular intervals
- **Property 31**: Progress messages include all required fields

## Next Steps

After verifying WebSocket functionality:
1. Proceed to Task 13.3: Create session control panel
2. Implement remaining review interface tasks
3. Add more comprehensive integration tests
