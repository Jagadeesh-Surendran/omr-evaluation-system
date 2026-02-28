# Task 3.15: Manual Evaluation API Integration

## Overview
This document describes the implementation of task 3.15, which integrates the manual evaluation workflow with the backend API endpoint `/api/evaluate_batch`.

## Implementation Details

### Function: `startManualEvaluation()`
**Location:** `frontend/js/components/manual-workflow.js`

### Key Features

1. **Validation**
   - Checks if all required files are uploaded using `isReadyToEvaluate()`
   - Shows error toast if validation fails

2. **FormData Construction**
   - Creates FormData object with three required parameters:
     - `omr_files`: Array of uploaded OMR sheet files
     - `answer_key_csv`: Single answer key CSV file
     - `num_options`: Number of answer options (3, 4, or 5)

3. **API Integration**
   - Calls `/api/evaluate_batch` endpoint using the `callAPI()` wrapper
   - Uses POST method with FormData body
   - Handles both success and error responses

4. **Progress Tracking**
   - Initializes progress state before API call
   - Tracks evaluation start time
   - Updates progress state on completion

5. **Results Handling**
   - Stores API response in global state using `updateResults()`
   - Maps backend response fields to frontend state structure:
     - `students`: Array of student results
     - `statistics`: Aggregated statistics (total, average, highest, lowest, processing time)
     - `insights`: AI-generated insights array

6. **Navigation**
   - Navigates to results view on success using `showScreen(SCREENS.RESULTS)`
   - Shows success toast notification

7. **Error Handling**
   - Catches and logs errors
   - Displays user-friendly error messages via toast notifications
   - Re-enables the start button on error
   - Resets progress state

8. **UI Feedback**
   - Disables start button during evaluation to prevent double submission
   - Shows loading spinner while processing
   - Re-enables button on error

## API Request Format

```javascript
POST /api/evaluate_batch
Content-Type: multipart/form-data

FormData:
  - omr_files: File[] (multiple OMR sheet files)
  - answer_key_csv: File (single CSV file)
  - num_options: string (e.g., "5")
```

## Expected API Response Format

```javascript
{
  "students": [
    {
      "student_id": "001",
      "name": "Student 1",
      "score": 85,
      "grade": "A",
      "status": "success",
      "filename": "sheet_001.jpg"
    },
    // ... more students
  ],
  "total_processed": 50,
  "average_score": 78.5,
  "highest_score": 95,
  "lowest_score": 45,
  "processing_time": 2.5,
  "insights": [
    "Average score is above 75%",
    "3 students scored below 50%"
  ]
}
```

## State Updates

### Before API Call
```javascript
appState.progress = {
  isActive: true,
  current: 0,
  total: <number of OMR files>,
  startTime: Date.now(),
  status: 'Starting evaluation...'
}
```

### After Successful API Call
```javascript
appState.results = {
  students: [...],
  statistics: {
    totalProcessed: <number>,
    averageScore: <number>,
    highestScore: <number>,
    lowestScore: <number>,
    processingTime: <number>
  },
  insights: [...],
  setDistribution: {},
  setAverages: {}
}

appState.progress = {
  isActive: false,
  current: <total files>,
  total: <total files>,
  status: 'Evaluation complete!'
}
```

## Requirements Satisfied

✓ **Requirement 2.8**: "WHEN the user clicks 'Start Evaluation', THE OMR_System SHALL call the /api/evaluate_batch endpoint"

The implementation:
- Calls the correct endpoint (`/api/evaluate_batch`)
- Sends all required parameters (omr_files, answer_key_csv, num_options)
- Handles the response correctly
- Provides error handling
- Updates state and navigates to results view

## Testing

A verification test has been created at `frontend/tests/verify_manual_evaluation.html` that checks:
- Function exists and is async
- Required dependencies are available
- State structure is correct
- API endpoint is defined
- Mock data validation works

To run the test:
1. Open `frontend/tests/verify_manual_evaluation.html` in a browser
2. Click "Run Integration Test"
3. Verify all tests pass

## Integration Points

### Dependencies
- `callAPI()` from `js/api.js` - API wrapper function
- `updateProgress()` from `js/state.js` - Progress state management
- `updateResults()` from `js/state.js` - Results state management
- `showToast()` from `js/utils/ui-components.js` - Toast notifications
- `showScreen()` from `app.js` - Screen navigation
- `isReadyToEvaluate()` from `js/components/manual-workflow.js` - Validation

### State Dependencies
- `appState.uploadedFiles.omrSheets` - Array of OMR files
- `appState.uploadedFiles.answerKey` - Answer key file
- `appState.evaluationConfig.numOptions` - Number of options setting

### Constants Used
- `API_ENDPOINTS.EVALUATE_BATCH` - API endpoint path
- `SCREENS.RESULTS` - Results screen identifier
- `TOAST_TYPES.SUCCESS` - Success toast type
- `TOAST_TYPES.ERROR` - Error toast type

## Error Scenarios Handled

1. **Missing Files**: Shows error if files not uploaded
2. **API Connection Error**: Shows "Unable to connect to server" message
3. **File Too Large (413)**: Shows "Files are too large" message
4. **Invalid Request (400)**: Shows "Invalid request" message
5. **Server Error (500)**: Shows "Server error occurred" message
6. **Generic Errors**: Shows error message from API or generic fallback

## Next Steps

This implementation completes task 3.15. The next tasks in the workflow are:
- Task 3.16: Write property test for API endpoint invocation
- Task 3.17: Style manual workflow screen
- Task 3.18: Checkpoint - Ensure all tests pass

## Notes

- The function is marked as `async` to handle the asynchronous API call
- Error messages use the `userMessage` property from the API wrapper for user-friendly text
- The start button is disabled during evaluation to prevent duplicate submissions
- Progress tracking is initialized but the actual progress modal display will be implemented in later tasks (Task 6.x)
- Results view rendering will be implemented in later tasks (Task 7.x)
