# Implementation Plan: EvalGenius AI OMR Evaluation System UI Redesign

## Overview

This implementation plan breaks down the EvalGenius AI OMR evaluation system UI redesign into actionable coding tasks. The system supports two distinct evaluation workflows: Manual Evaluation Mode (user provides answer key CSV) and AI Evaluation Mode (AI extracts answer keys from multi-set question papers). Each task builds incrementally on previous work, with property-based tests validating correctness properties from the design document.

## Technology Stack

- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3
- **State Management**: Global state object with session persistence
- **API Communication**: Fetch API with FormData
- **Testing**: Jest for unit tests, fast-check for property-based tests

## Tasks

### 1. Core Infrastructure Setup

- [x] 1.1 Set up project structure and base files
  - Create directory structure: `js/`, `js/components/`, `js/utils/`, `assets/`
  - Create base files: `index.html`, `app.js`, `style.css`, `js/state.js`, `js/api.js`, `js/constants.js`
  - Set up CSS custom properties for theming (colors, spacing, typography)
  - _Requirements: 12.7_

- [x] 1.2 Implement global state management system
  - Create `appState` object with all required properties (currentMode, uploadedFiles, answerKeys, progress, results, filters)
  - Implement state update functions with immutability
  - Add session storage persistence functions (`saveSessionState`, `restoreSessionState`, `clearSessionData`)
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [ ]* 1.3 Write property test for state management
  - **Property 2: File Upload State Preservation**
  - **Validates: Requirements 1.6**
  - Test that navigation preserves uploaded files in state

- [x] 1.4 Implement navigation and routing system
  - Create `showScreen(screenId)` function to switch between views
  - Implement `goToModeSelection()`, `goBack()` navigation functions
  - Add browser history management for back button support
  - _Requirements: 12.1, 12.2, 12.5, 12.6_

- [x] 1.5 Create base UI component system
  - Implement reusable button components (primary, outline, ghost, icon)
  - Create modal component with overlay and close functionality
  - Build toast notification system with success/error/info/warning types
  - Add loading spinner component
  - _Requirements: 11.1_

- [ ]* 1.6 Write property test for mode selection navigation
  - **Property 1: Mode Selection Navigation**
  - **Validates: Requirements 1.4, 1.5**
  - Test that selecting any mode navigates to correct workflow and persists mode in state

- [x] 1.7 Implement API integration layer
  - Create `API_BASE` constant and endpoint configuration
  - Implement `callAPI(endpoint, method, body)` wrapper function with error handling
  - Add request/response logging for debugging
  - _Requirements: 2.8, 3.6_

- [ ] 1.8 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

### 2. Mode Selection Screen

- [x] 2.1 Create mode selection UI
  - Build HTML structure for mode selection screen with two mode cards
  - Add icons, titles, descriptions, and feature lists for Manual and AI modes
  - Implement hover effects and tooltips
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2.2 Implement mode selection logic
  - Add click handlers for mode cards
  - Implement `selectMode(mode)` function to update state and navigate
  - Add mode validation and error handling
  - _Requirements: 1.4, 1.5_

- [ ] 2.3 Style mode selection screen
  - Create responsive grid layout for mode cards
  - Add CSS animations for hover and selection states
  - Ensure mobile-friendly layout (stack cards vertically on small screens)
  - _Requirements: 17.1, 17.2, 17.5_


### 3. Manual Evaluation Workflow

- [x] 3.1 Create manual workflow UI structure
  - Build HTML for manual evaluation screen with header, upload zones, options panel, and start button
  - Add back button to return to mode selection
  - Create two upload zones: OMR sheets (multiple files) and answer key CSV (single file)
  - _Requirements: 2.1, 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 3.2 Implement file upload functionality
  - Add file input handlers for OMR sheets and answer key
  - Implement drag-and-drop support for both upload zones
  - Create `handleFileUpload(files, fileType)` function with validation
  - Display uploaded file list with filenames and sizes
  - _Requirements: 2.2, 2.3, 2.4, 2.5_

- [ ]* 3.3 Write property test for file type validation
  - **Property 3: File Type Validation**
  - **Validates: Requirements 2.2, 3.3, 11.6, 11.7**
  - Test that valid file types are accepted and invalid types are rejected with error messages

- [ ]* 3.4 Write property test for file size validation
  - **Property 26: File Size Validation**
  - **Validates: Requirements 8.8, 8.9**
  - Test that files exceeding 20MB or batches exceeding 100MB are rejected

- [ ]* 3.5 Write property test for file metadata display
  - **Property 5: File Metadata Display**
  - **Validates: Requirements 2.4, 2.5, 3.4**
  - Test that filename and file size are displayed for all uploaded files

- [x] 3.6 Implement CSV answer key validation
  - Create `validateAnswerKeyCSV(csvContent)` function
  - Parse CSV and validate format (question_number, answer)
  - Check for valid question numbers (positive integers) and answers (A-E)
  - Detect and report duplicate questions and invalid answers
  - Display preview of first 10 entries and total question count
  - _Requirements: 2.3, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8_

- [ ]* 3.7 Write property test for CSV validation
  - **Property 4: CSV Answer Key Validation**
  - **Validates: Requirements 2.3, 11.8, 11.9, 15.1, 15.3, 15.4**
  - Test that valid CSVs are accepted and invalid CSVs are rejected with specific errors

- [ ]* 3.8 Write property test for duplicate question detection
  - **Property 29: Duplicate Question Detection**
  - **Validates: Requirements 15.5**
  - Test that CSVs with duplicate question numbers are rejected with error listing duplicates

- [ ]* 3.9 Write property test for invalid answer detection
  - **Property 30: Invalid Answer Detection**
  - **Validates: Requirements 15.6**
  - Test that CSVs with invalid answer options are rejected with error listing invalid entries

- [ ]* 3.10 Write property test for answer key preview
  - **Property 31: Answer Key Preview**
  - **Validates: Requirements 15.7, 15.8**
  - Test that valid answer keys display preview of first 10 entries and total count

- [ ]* 3.11 Write property test for small answer key warning
  - **Property 32: Small Answer Key Warning**
  - **Validates: Requirements 15.9**
  - Test that answer keys with fewer than 10 questions display warning


- [x] 3.12 Implement options panel
  - Add dropdown for number of options (3, 4, or 5)
  - Store selection in `appState.evaluationConfig.numOptions`
  - _Requirements: 2.6_

- [x] 3.13 Implement start evaluation button logic
  - Create `checkReadyToEvaluate()` function to enable/disable button
  - Button enabled only when OMR sheets and answer key are uploaded
  - Add click handler to call `startManualEvaluation()`
  - _Requirements: 2.7_

- [ ]* 3.14 Write property test for evaluation button state
  - **Property 6: Evaluation Button State**
  - **Validates: Requirements 2.7**
  - Test that button is enabled if and only if all required files are uploaded

- [x] 3.15 Integrate manual evaluation with API
  - Create `startManualEvaluation()` function
  - Build FormData with omr_files, answer_key_csv, and num_options
  - Call `/api/evaluate_batch` endpoint
  - Handle response and errors
  - _Requirements: 2.8_

- [ ]* 3.16 Write property test for API endpoint invocation
  - **Property 7: API Endpoint Invocation**
  - **Validates: Requirements 2.8, 3.6, 3.13**
  - Test that evaluation calls correct endpoint with correct parameters for each mode

- [ ] 3.17 Style manual workflow screen
  - Create responsive layout for upload zones (side-by-side on desktop, stacked on mobile)
  - Style file lists with icons, filenames, and sizes
  - Add visual feedback for drag-and-drop (hover states, drop zones)
  - Style options panel and start button
  - _Requirements: 17.1, 17.2, 17.5_

- [ ] 3.18 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

### 4. AI Evaluation Workflow - Phase 1

- [x] 4.1 Create AI workflow phase 1 UI
  - Build HTML for AI phase 1 screen with header and question paper upload zone
  - Add back button to return to mode selection
  - Create upload zone for question paper (PDF/JPG/PNG)
  - Add "Extract Answer Keys" button
  - _Requirements: 3.1, 3.2, 3.3, 13.7, 13.8, 13.9_

- [x] 4.2 Implement question paper upload
  - Add file input handler for question paper
  - Implement drag-and-drop support
  - Validate file type (PDF, JPG, PNG) and size (max 20MB)
  - Display uploaded filename and size
  - _Requirements: 3.3, 3.4_

- [x] 4.3 Implement answer key extraction
  - Create `extractAnswerKeys()` function
  - Build FormData with qp_file
  - Call `/api/extract_key` endpoint
  - Show loading indicator during extraction
  - Handle response with extracted keys
  - _Requirements: 3.5, 3.6, 3.7_


- [x] 4.4 Create answer key review modal
  - Build modal HTML with header, set tabs, answer key grid, and action buttons
  - Create tabs for each detected set (A, B, C, D)
  - Implement tab switching to display different sets
  - Add "Download as CSV" and "Confirm and Continue" buttons
  - _Requirements: 3.8, 4.1, 4.8, 4.9_

- [ ]* 4.5 Write property test for answer key extraction display
  - **Property 10: Answer Key Extraction Display**
  - **Validates: Requirements 3.8, 3.9, 3.10, 4.1, 4.2, 4.3**
  - Test that all extracted sets are displayed grouped by set label with editable answers

- [x] 4.6 Implement editable answer key grid
  - Create `renderAnswerKeyGrid(answerKey, setLabel)` function
  - Display questions in grid format with question numbers and answer dropdowns
  - Make each answer editable via dropdown (A, B, C, D, E options)
  - _Requirements: 3.9, 3.10, 4.2, 4.3_

- [x] 4.7 Implement answer key editing logic
  - Create `editAnswerKey(set, question, newAnswer)` function
  - Update `appState.answerKeys.ai` when answer is changed
  - Add visual indicator (highlight) for edited answers
  - Validate answer option (A-E only)
  - _Requirements: 4.4, 4.5, 4.6_

- [ ]* 4.8 Write property test for answer key editing
  - **Property 11: Answer Key Editing**
  - **Validates: Requirements 4.4, 4.5, 4.6**
  - Test that edits immediately update state, display visual indicator, and mark as edited

- [x] 4.9 Implement answer key completeness validation
  - Create `validateAnswerKeyCompleteness()` function
  - Check that all sets have complete answer keys (no missing questions)
  - Display error if any set is incomplete
  - Enable "Confirm and Continue" only when all sets are complete
  - _Requirements: 4.10_

- [ ]* 4.10 Write property test for answer key completeness
  - **Property 12: Answer Key Completeness Validation**
  - **Validates: Requirements 4.10**
  - Test that incomplete answer keys prevent progression with error, complete keys allow progression

- [x] 4.11 Implement download answer key as CSV
  - Create `downloadAnswerKey(set)` function
  - Generate CSV content from answer key object
  - Trigger browser download with filename format: `answer_key_set_{set}.csv`
  - _Requirements: 4.8_

- [x] 4.12 Style AI phase 1 screen and review modal
  - Style question paper upload zone with appropriate icon
  - Create modal styling with tabs, grid layout for answers
  - Add hover and focus states for editable answers
  - Style action buttons
  - _Requirements: 17.1, 17.2_


### 5. AI Evaluation Workflow - Phase 2

- [x] 5.1 Create AI workflow phase 2 UI
  - Build HTML for AI phase 2 screen with header and OMR upload zone
  - Add back button to return to answer key review
  - Display summary of confirmed answer keys (sets and question counts)
  - Create upload zone for OMR sheets (multiple files)
  - Add "Start AI Evaluation" button
  - _Requirements: 3.11, 3.12_

- [x] 5.2 Implement OMR sheet upload for AI mode
  - Add file input handler for OMR sheets
  - Implement drag-and-drop support
  - Validate file types and sizes
  - Display uploaded file list
  - _Requirements: 3.12_

- [x] 5.3 Implement AI evaluation start
  - Create `startAIEvaluation()` function
  - Build FormData with omr_files, multiplex_key (JSON string), and num_options
  - Call `/api/evaluate_batch` endpoint
  - Handle response with form_type for each student
  - _Requirements: 3.13, 3.14, 3.15_

- [x] 5.4 Style AI phase 2 screen
  - Style answer keys summary section with set badges
  - Style OMR upload zone
  - Add responsive layout
  - _Requirements: 17.1, 17.2_

- [ ] 5.5 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

### 6. Progress Tracking Modal

- [x] 6.1 Create progress modal UI
  - Build modal HTML with header, circular progress indicator, metrics display, and cancel button
  - Add SVG circular progress bar with background and fill circles
  - Create metrics display for processed count, time elapsed, and time remaining
  - Add set detection container (hidden by default, shown in AI mode)
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6.2 Implement circular progress animation
  - Calculate SVG stroke-dashoffset based on percentage
  - Animate progress circle smoothly
  - Update percentage text in center
  - _Requirements: 5.2_

- [x] 6.3 Implement progress calculation logic
  - Create `calculateProgress(current, total, startTime)` function
  - Calculate percentage, elapsed time, remaining time, and processing speed
  - Return progress object with all metrics
  - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.8_

- [ ]* 6.4 Write property test for progress calculation
  - **Property 13: Progress Calculation**
  - **Validates: Requirements 5.2, 5.3, 5.4, 5.5, 5.8**
  - Test that progress calculations are correct for any current/total/startTime combination


- [x] 6.5 Implement progress update mechanism
  - Create `updateProgress(current, total, status, setDetection)` function
  - Update all progress UI elements (circle, percentage, counts, times)
  - Implement simulated progress for batch processing (update every 100ms)
  - _Requirements: 5.6_

- [ ]* 6.6 Write property test for progress updates
  - **Property 14: Progress Updates**
  - **Validates: Requirements 5.6**
  - Test that progress counter increments and display updates for each processed sheet

- [x] 6.7 Implement set detection visualization
  - Create `updateSetDetection(students)` function to calculate set distribution
  - Display detected form_type for each processed sheet
  - Show running count of sheets per set with color coding (A=blue, B=green, C=orange, D=purple, UNKNOWN=red)
  - Only display in AI mode
  - _Requirements: 5.7, 16.2, 16.3, 16.4_

- [ ]* 6.8 Write property test for set detection display
  - **Property 15: Set Detection Display**
  - **Validates: Requirements 5.7**
  - Test that AI mode displays detected form_type and maintains running count per set

- [x] 6.9 Implement evaluation with progress
  - Create `startEvaluationWithProgress(formData, totalSheets)` function
  - Show progress modal immediately
  - Start progress simulation interval
  - Call API endpoint
  - Update progress to 100% on completion
  - Hide modal after 1 second delay
  - Navigate to results view
  - _Requirements: 2.9, 5.1, 5.10_

- [ ]* 6.10 Write property test for progress modal display
  - **Property 8: Progress Modal Display**
  - **Validates: Requirements 2.9, 5.1**
  - Test that progress modal displays immediately on evaluation start and remains visible until completion

- [ ]* 6.11 Write property test for navigation on completion
  - **Property 9: Navigation on Completion**
  - **Validates: Requirements 2.10, 5.10, 6.1**
  - Test that system navigates to results view and hides progress modal on completion

- [x] 6.12 Implement cancel evaluation
  - Add cancel button handler
  - Abort ongoing API request
  - Hide progress modal
  - Return to previous screen
  - _Requirements: 5.9_

- [x] 6.13 Style progress modal
  - Create modal overlay with blur effect
  - Style circular progress with gradient colors
  - Style metrics display with icons
  - Add set detection badges with colors
  - Ensure responsive layout
  - _Requirements: 17.1, 17.4_


### 7. Results Display

- [x] 7.1 Create results view UI structure
  - Build HTML for results screen with header, statistics cards, insights panel, and results table
  - Add "New Evaluation" button and export buttons in header
  - Create grid layout for statistics cards
  - Add table controls (search box, filters)
  - _Requirements: 6.1, 6.2, 6.6, 6.9_

- [x] 7.2 Implement statistics cards
  - Create `renderStatisticsCards(results)` function
  - Display total students, average score, highest score, and processing time
  - Calculate statistics from results data
  - Add icons and styling for each card
  - _Requirements: 6.6_

- [ ]* 7.3 Write property test for statistics display
  - **Property 18: Statistics Display**
  - **Validates: Requirements 6.6**
  - Test that statistics are calculated and displayed correctly for any results

- [x] 7.4 Implement set distribution chart (AI mode only)
  - Create `renderSetDistribution(results)` function
  - Calculate count and percentage per set
  - Display as bar chart with labels and values
  - Show average score per set
  - Only display in AI mode
  - _Requirements: 6.7, 16.5, 16.6, 16.7_

- [ ]* 7.5 Write property test for set distribution display
  - **Property 19: Set Distribution Display**
  - **Validates: Requirements 6.7**
  - Test that AI mode results display breakdown of students per set with counts and percentages

- [x] 7.6 Implement AI insights panel
  - Display insights array from API response
  - Format insights with icons and styling
  - Generate client-side insights (e.g., set performance comparison)
  - _Requirements: 6.8_

- [x] 7.7 Create results table
  - Build table with columns: #, Student ID, Name, Score, Grade, Set (AI mode), Status, Actions
  - Create `renderResultsTableRows(students)` function
  - Display all student results with appropriate formatting
  - Add grade badges with color coding (A=green, B=blue, C=yellow, D=orange, F=red)
  - Add status badges (pass/fail)
  - _Requirements: 6.2, 6.3_

- [x] 7.8 Implement unknown set highlighting
  - Apply warning styling (yellow/orange background) to rows with form_type "UNKNOWN"
  - Add warning icon to UNKNOWN set badges
  - _Requirements: 6.10_

- [ ]* 7.9 Write property test for unknown set highlighting
  - **Property 20: Unknown Set Highlighting**
  - **Validates: Requirements 6.10**
  - Test that students with form_type "UNKNOWN" have warning styling applied


- [x] 7.10 Implement search functionality
  - Add search input handler
  - Create `filterResults(students, filters)` function
  - Filter by student name or ID (case-insensitive)
  - Update table display with filtered results
  - _Requirements: 6.9_

- [x] 7.11 Implement set filter (AI mode only)
  - Create set filter dropdown with options: All, Set A, Set B, Set C, Set D, UNKNOWN
  - Filter results by selected set
  - Update table display
  - _Requirements: 6.4_

- [x] 7.12 Implement table sorting
  - Add click handlers to table headers
  - Sort by any column (ascending/descending)
  - Update sort indicators (arrows) in headers
  - Maintain sort state in `appState.filters`
  - _Requirements: 6.5_

- [ ]* 7.13 Write property test for results filtering
  - **Property 16: Results Filtering**
  - **Validates: Requirements 6.4, 6.9**
  - Test that filtering displays only students matching all active filters

- [ ]* 7.14 Write property test for results sorting
  - **Property 17: Results Sorting**
  - **Validates: Requirements 6.5**
  - Test that sorting reorders rows correctly by any column in any direction

- [x] 7.15 Implement student details view
  - Create `viewStudentDetails(index)` function
  - Display modal with detailed student information (answers, correct/incorrect breakdown)
  - Show question-by-question comparison with answer key
  - _Requirements: 11.4_

- [x] 7.16 Style results view
  - Create responsive grid layout for statistics cards
  - Style set distribution chart with bars and labels
  - Style results table with alternating row colors, hover effects
  - Add responsive table (horizontal scroll on small screens)
  - Style badges, buttons, and filters
  - _Requirements: 17.1, 17.2, 17.3_

- [ ] 7.17 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

### 8. Export Functionality

- [x] 8.1 Implement CSV export
  - Create `exportCSV(students)` function
  - Build CSV headers: #, Student ID, Name, Score, Grade, Set (AI mode), Status, Filename
  - Generate CSV rows from student data
  - Add summary section for AI mode (set distribution and averages)
  - Trigger browser download with filename format: `evalgenius_results_YYYYMMDD_HHMMSS.csv`
  - _Requirements: 7.2, 7.3, 7.9_

- [ ]* 8.2 Write property test for CSV export structure
  - **Property 21: CSV Export Structure**
  - **Validates: Requirements 7.2, 7.3**
  - Test that CSV includes all required columns with correct values for each student


- [x] 8.3 Implement Excel export
  - Create `exportExcel(students)` function
  - Call `/api/export` endpoint with results and format='excel'
  - Handle binary response (blob)
  - Trigger browser download with filename format: `evalgenius_results_YYYYMMDD_HHMMSS.xlsx`
  - _Requirements: 7.4, 7.5_

- [ ]* 8.4 Write property test for export filename format
  - **Property 22: Export Filename Format**
  - **Validates: Requirements 7.6, 7.8**
  - Test that export filenames follow correct format with timestamp

- [x] 8.5 Implement export success notification
  - Show toast notification on successful export
  - Display error toast if export fails
  - _Requirements: 7.10_

- [ ]* 8.6 Write property test for export success notification
  - **Property 23: Export Success Notification**
  - **Validates: Requirements 7.10**
  - Test that success toast displays after successful export

- [x] 8.7 Implement file download utilities
  - Create `downloadFile(content, filename, mimeType)` function for text files
  - Create `downloadBlob(blob, filename)` function for binary files
  - Handle browser compatibility (create temporary anchor element, click, remove)
  - _Requirements: 7.7_

### 9. PDF Upload Support

- [ ] 9.1 Implement PDF file handling
  - Update file type validation to accept PDF files
  - Display PDF icon for PDF files in file lists
  - Send PDF files to backend without client-side conversion
  - _Requirements: 8.1, 8.2, 8.3_

- [ ]* 9.2 Write property test for PDF file handling
  - **Property 24: PDF File Handling**
  - **Validates: Requirements 8.1, 8.2, 8.3**
  - Test that PDF files are accepted, displayed with PDF icon, and sent to backend

- [ ] 9.3 Implement mixed file type support
  - Allow uploading both PDF and image files in same batch
  - Display appropriate icons for each file type
  - _Requirements: 8.7_

- [ ]* 9.4 Write property test for mixed file type support
  - **Property 25: Mixed File Type Support**
  - **Validates: Requirements 8.7**
  - Test that batches with both PDF and image files are accepted and processed

- [ ] 9.5 Update progress tracking for PDFs
  - Display "Processing page X of PDF" message when handling PDFs
  - Count each PDF page as separate sheet for progress calculation
  - _Requirements: 8.6_

- [ ] 9.6 Update results display for PDFs
  - Display PDF filename with page number for each student (e.g., "exam.pdf - Page 1")
  - _Requirements: 8.10_


### 10. Student Database Integration

- [ ] 10.1 Add student database import button
  - Add "Import Student Database" button to results view
  - Create file upload dialog for CSV files
  - _Requirements: 9.1, 9.2_

- [ ] 10.2 Implement student database linking
  - Create `linkStudentDatabase(csvFile)` function
  - Parse CSV with roll number and name columns
  - Call `/api/link_db` endpoint
  - Match students by sequential position
  - Update results table with student names
  - _Requirements: 9.3, 9.4, 9.5, 9.6_

- [ ] 10.3 Handle database linking results
  - Display success message with count of linked names
  - Preserve unmatched results with placeholder names
  - Allow re-importing to correct mistakes
  - Update exports to include linked names
  - _Requirements: 9.7, 9.8, 9.9, 9.10_

### 11. Error Handling and Validation

- [ ] 11.1 Implement comprehensive error handling
  - Create `handleError(error, type)` function with error type enum
  - Define error types: FILE_UPLOAD, FILE_VALIDATION, API_ERROR, EXTRACTION_ERROR, EVALUATION_ERROR, EXPORT_ERROR
  - Generate user-friendly error messages with suggestions for each type
  - _Requirements: 11.1, 11.2, 11.3, 11.5_

- [ ] 11.2 Create error modal component
  - Build modal to display error message and suggestions
  - Show contextual help based on error type
  - Add "Retry" button for recoverable errors
  - _Requirements: 11.10_

- [ ]* 11.3 Write property test for error toast display
  - **Property 27: Error Toast Display**
  - **Validates: Requirements 11.1, 11.2, 11.5**
  - Test that error conditions display error toast with failure reason and suggestions

- [ ] 11.4 Implement CSV header handling
  - Detect and skip header row if present (check for "question" keyword)
  - Parse CSV with or without header
  - _Requirements: 15.2_

- [ ]* 11.5 Write property test for CSV header handling
  - **Property 28: CSV Header Handling**
  - **Validates: Requirements 15.2**
  - Test that CSVs with or without headers are parsed correctly

- [ ] 11.6 Add validation feedback
  - Display inline validation errors for file uploads
  - Show validation status icons (checkmark for valid, X for invalid)
  - Highlight invalid fields with red borders
  - _Requirements: 11.6, 11.7, 11.8, 11.9_

- [ ] 11.7 Implement retry logic
  - Add retry functionality for failed API calls
  - Implement exponential backoff for transient failures
  - Display retry count and status
  - _Requirements: 11.10_


### 12. Navigation and Layout

- [ ] 12.1 Create navigation header
  - Build header with logo, mode indicator, and action buttons
  - Add "Home" button to return to mode selection
  - Display current mode name in header
  - Add "Help" button
  - _Requirements: 12.5, 12.7, 12.9, 20.1_

- [ ] 12.2 Implement progress indicator
  - Create step indicator showing: Mode Selection → Upload → Processing → Results
  - Highlight current step
  - Disable future steps until prerequisites met
  - _Requirements: 12.1, 12.2, 12.3, 12.4_

- [ ] 12.3 Implement breadcrumb navigation
  - Display breadcrumb showing current location
  - Make breadcrumb items clickable to navigate back
  - _Requirements: 12.6_

- [ ] 12.4 Add keyboard shortcuts
  - Implement Enter key to submit forms
  - Implement Esc key to close modals
  - Add keyboard navigation for tabs and dropdowns
  - _Requirements: 12.10, 18.2_

- [ ] 12.5 Implement session warnings
  - Warn user before clearing session data if results exist
  - Confirm before navigating away with unsaved data
  - _Requirements: 10.7_

- [ ] 12.6 Style navigation components
  - Create consistent header styling across all screens
  - Style progress indicator with colors and icons
  - Add breadcrumb styling with separators
  - Ensure responsive header (collapse to hamburger menu on mobile)
  - _Requirements: 17.6_

### 13. Upload Zone Enhancements

- [ ] 13.1 Add upload zone labels and icons
  - Display clear labels for each upload zone (OMR Answer Sheets, Answer Key CSV, Question Paper)
  - Add appropriate icons (documents, spreadsheet, brain)
  - Show accepted formats below each zone
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9_

- [ ] 13.2 Implement drag-and-drop visual feedback
  - Add hover state when dragging files over upload zone
  - Change border color and background on drag over
  - Show "Drop files here" message
  - _Requirements: 13.3_

- [ ] 13.3 Add example file format information
  - Display example CSV format below answer key upload zone
  - Add "Download Sample CSV" link
  - Show tooltip with format details on hover
  - _Requirements: 13.10, 15.10_


### 14. Batch Processing Performance

- [ ] 14.1 Implement batch size validation
  - Validate maximum 200 sheets per batch
  - Validate maximum 100MB total upload size
  - Display error if limits exceeded
  - _Requirements: 14.3, 14.4, 14.5_

- [ ] 14.2 Add batch processing indicators
  - Display estimated processing time based on batch size
  - Show processing speed (sheets per minute) in progress modal
  - _Requirements: 14.6, 14.8_

- [ ] 14.3 Optimize UI responsiveness
  - Use requestAnimationFrame for progress updates
  - Debounce search and filter operations
  - Implement virtual scrolling for large result tables (future enhancement)
  - _Requirements: 14.7_

- [ ] 14.4 Add performance logging
  - Log batch size, processing time, and speed metrics
  - Send performance data to analytics (if configured)
  - _Requirements: 14.10_

### 15. Help and Documentation

- [ ] 15.1 Create help modal
  - Build modal with tabs for different help topics
  - Add step-by-step guides for Manual and AI modes
  - Include troubleshooting tips for common issues
  - _Requirements: 20.1, 20.2, 20.3, 20.5_

- [ ] 15.2 Add example files for download
  - Provide sample answer key CSV
  - Provide sample student database CSV
  - Add download links in help modal
  - _Requirements: 20.4_

- [ ] 15.3 Implement contextual help tooltips
  - Add tooltips to upload zones explaining file requirements
  - Add tooltips to buttons explaining their function
  - Add tooltips to options explaining their effect
  - _Requirements: 1.3, 20.6_

- [ ] 15.4 Create quick start guide
  - Display quick start guide on first use (check localStorage flag)
  - Highlight key features and workflow steps
  - Add "Don't show again" checkbox
  - _Requirements: 20.7, 20.8_

- [ ] 15.5 Add "What's New" section
  - Display feature updates and improvements
  - Show version number
  - _Requirements: 20.9_

- [ ] 15.6 Add links to external documentation
  - Link to video tutorials (if available)
  - Link to full documentation site
  - _Requirements: 20.10_


### 16. Responsive Design

- [ ] 16.1 Implement responsive breakpoints
  - Define CSS media queries for breakpoints: 768px (tablet), 1024px (desktop), 1440px (large desktop)
  - Test layouts at each breakpoint
  - _Requirements: 17.1, 17.10_

- [ ] 16.2 Optimize mobile layouts
  - Stack upload zones vertically on screens < 1024px
  - Make results table horizontally scrollable on small screens
  - Collapse navigation to hamburger menu on screens < 768px
  - Scale progress modal for different screen sizes
  - _Requirements: 17.2, 17.3, 17.4, 17.5, 17.6_

- [ ] 16.3 Ensure touch-friendly controls
  - Use minimum 44x44px button sizes
  - Add adequate spacing between interactive elements
  - Test touch interactions on tablet/mobile devices
  - _Requirements: 17.7_

- [ ] 16.4 Maintain readability
  - Use minimum 14px font size
  - Ensure adequate line height and spacing
  - Test readability on small screens
  - _Requirements: 17.9_

- [ ] 16.5 Test on multiple browsers
  - Test on Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
  - Verify functionality and styling consistency
  - Fix browser-specific issues
  - _Requirements: 17.8_

### 17. Accessibility Compliance

- [ ] 17.1 Add semantic HTML structure
  - Use semantic elements: nav, main, section, article, header, footer
  - Ensure proper heading hierarchy (h1, h2, h3)
  - _Requirements: 18.9_

- [ ] 17.2 Implement keyboard navigation
  - Ensure all interactive elements are keyboard accessible (Tab, Enter, Esc)
  - Add visible focus indicators to all focusable elements
  - Test full keyboard navigation flow
  - _Requirements: 18.2, 18.5_

- [ ] 17.3 Add ARIA labels and attributes
  - Add ARIA labels to all form controls and buttons
  - Use ARIA live regions for dynamic updates (progress, toasts)
  - Add ARIA roles where semantic HTML is insufficient
  - _Requirements: 18.3, 18.6_

- [ ] 17.4 Add alt text to images and icons
  - Provide descriptive alt text for all images
  - Use aria-label for icon-only buttons
  - _Requirements: 18.1_


- [ ] 17.5 Ensure color contrast compliance
  - Verify color contrast ratio of at least 4.5:1 for all text
  - Test with color contrast analyzer tools
  - Adjust colors if needed to meet WCAG AA standards
  - _Requirements: 18.4_

- [ ] 17.6 Implement skip navigation
  - Add "Skip to main content" link at top of page
  - Ensure skip link is keyboard accessible and visible on focus
  - _Requirements: 18.8_

- [ ] 17.7 Test with screen readers
  - Test with NVDA (Windows) and JAWS screen readers
  - Verify all content is announced correctly
  - Test navigation flow with screen reader
  - Fix any issues found
  - _Requirements: 18.10_

- [ ] 17.8 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

### 18. Data Privacy and Security

- [ ] 18.1 Implement client-side file processing
  - Process and validate files client-side before sending to backend
  - Don't store sensitive data in localStorage (use sessionStorage only)
  - _Requirements: 19.1, 19.4_

- [ ] 18.2 Ensure secure API communication
  - Use HTTPS for all API calls
  - Validate API responses before processing
  - _Requirements: 19.2_

- [ ] 18.3 Implement data cleanup
  - Clear all session data when user logs out or closes tab
  - Provide "Clear All Data" button in settings
  - _Requirements: 19.5, 19.9_

- [ ] 18.4 Add privacy notice
  - Display privacy notice on first use
  - Explain data handling and storage practices
  - _Requirements: 19.6_

- [ ] 18.5 Implement client-side student database linking
  - Link student names client-side only (don't send names to backend during evaluation)
  - _Requirements: 19.7, 19.8_

- [ ] 18.6 Add audit logging
  - Log all file uploads and evaluations (without sensitive data)
  - Store logs for debugging and analytics
  - _Requirements: 19.10_

### 19. Testing and Quality Assurance

- [ ] 19.1 Set up testing framework
  - Install Jest for unit tests
  - Install fast-check for property-based tests
  - Configure test runner and coverage reporting
  - Create test directory structure: `tests/unit/`, `tests/property/`, `tests/integration/`


- [ ]* 19.2 Write unit tests for mode selection
  - Test mode selection UI rendering
  - Test mode selection event handlers
  - Test state updates on mode selection
  - Test navigation to workflow screens

- [ ]* 19.3 Write unit tests for manual workflow
  - Test file upload handlers
  - Test CSV validation logic
  - Test answer key preview display
  - Test evaluation button enable/disable logic
  - Test API integration

- [ ]* 19.4 Write unit tests for AI workflow
  - Test question paper upload
  - Test answer key extraction
  - Test answer key review modal
  - Test answer key editing
  - Test phase 2 OMR upload
  - Test AI evaluation API integration

- [ ]* 19.5 Write unit tests for progress modal
  - Test progress modal display
  - Test progress calculation
  - Test progress updates
  - Test set detection display
  - Test cancel functionality

- [ ]* 19.6 Write unit tests for results view
  - Test statistics calculation
  - Test set distribution chart
  - Test results table rendering
  - Test search functionality
  - Test filtering and sorting
  - Test student details modal

- [ ]* 19.7 Write unit tests for export functionality
  - Test CSV export generation
  - Test Excel export API call
  - Test filename generation
  - Test download trigger

- [ ]* 19.8 Write integration tests for manual evaluation flow
  - Test complete manual evaluation workflow from mode selection to results
  - Test error handling at each step
  - Test navigation between screens

- [ ]* 19.9 Write integration tests for AI evaluation flow
  - Test complete AI evaluation workflow from mode selection to results
  - Test answer key extraction and editing
  - Test set detection and results display

- [ ] 19.10 Run all tests and fix failures
  - Execute all unit tests
  - Execute all property-based tests (minimum 100 runs each)
  - Execute all integration tests
  - Fix any failing tests
  - Achieve minimum 80% code coverage

- [ ] 19.11 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


### 20. Polish and Final Touches

- [ ] 20.1 Optimize performance
  - Minify JavaScript and CSS files
  - Optimize images and icons
  - Implement lazy loading for non-critical resources
  - Test page load time and optimize

- [ ] 20.2 Add loading states
  - Add skeleton loaders for data loading
  - Add spinner for API calls
  - Add disabled states for buttons during processing
  - Ensure smooth transitions between states

- [ ] 20.3 Implement animations and transitions
  - Add smooth transitions for screen changes
  - Add fade-in animations for modals
  - Add progress bar animations
  - Keep animations subtle and performant

- [ ] 20.4 Add visual polish
  - Refine color scheme and ensure consistency
  - Add shadows and depth to cards and modals
  - Ensure consistent spacing and alignment
  - Add hover and focus states to all interactive elements

- [ ] 20.5 Implement dark mode (optional enhancement)
  - Create dark mode color scheme
  - Add toggle switch in settings
  - Store preference in localStorage
  - Test all screens in dark mode

- [ ] 20.6 Add analytics tracking
  - Track mode selection
  - Track evaluation starts and completions
  - Track export actions
  - Track errors and failures

- [ ] 20.7 Create user onboarding
  - Add welcome screen for first-time users
  - Add interactive tutorial highlighting key features
  - Add tooltips for first-time actions

- [ ] 20.8 Implement feedback mechanism
  - Add "Send Feedback" button
  - Create feedback form modal
  - Send feedback to backend or email

- [ ] 20.9 Add version information
  - Display version number in footer or settings
  - Add changelog or release notes link

- [ ] 20.10 Final testing and bug fixes
  - Perform end-to-end testing of all workflows
  - Test edge cases and error scenarios
  - Fix any remaining bugs
  - Verify all requirements are met

- [ ] 20.11 Prepare deployment
  - Create production build
  - Set up deployment configuration
  - Test on production environment
  - Verify API endpoints and HTTPS
  - Update documentation

- [ ] 20.12 Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


## Implementation Notes

### Task Execution Guidelines

1. **Incremental Development**: Each task builds on previous tasks. Complete tasks in order within each section.

2. **Testing Strategy**: 
   - Tasks marked with `*` are optional and can be skipped for faster MVP delivery
   - Property-based tests validate universal correctness properties
   - Unit tests validate specific examples and edge cases
   - Run tests frequently during development

3. **Property Test Configuration**:
   - Use fast-check library with minimum 100 iterations per property
   - Tag each property test with format: `// Feature: ui-redesign-manual-ai-eval-modes, Property {number}: {property_text}`
   - Reference the design document property number and requirements

4. **Code Organization**:
   - Keep components modular and reusable
   - Use consistent naming conventions
   - Document complex logic with comments
   - Follow JavaScript ES6+ best practices

5. **State Management**:
   - Always update state immutably
   - Validate state transitions
   - Clear sensitive data appropriately
   - Use session storage for persistence

6. **API Integration**:
   - Handle all error cases gracefully
   - Provide user-friendly error messages
   - Implement retry logic for transient failures
   - Log API calls for debugging

7. **Accessibility**:
   - Test with keyboard navigation throughout development
   - Use semantic HTML from the start
   - Add ARIA labels as you build components
   - Test with screen readers before final release

8. **Responsive Design**:
   - Use mobile-first approach
   - Test on multiple screen sizes regularly
   - Ensure touch-friendly controls
   - Verify cross-browser compatibility

### Checkpoints

Checkpoints are included at strategic points to ensure quality and allow for user feedback:
- After core infrastructure (Task 1.8)
- After manual workflow (Task 3.18)
- After AI workflow phase 2 (Task 5.5)
- After results display (Task 7.17)
- After accessibility implementation (Task 17.8)
- After testing (Task 19.11)
- After final polish (Task 20.12)

At each checkpoint, ensure all tests pass and ask the user if any questions or concerns arise before proceeding.

### Requirements Coverage

All 20 requirements from the requirements document are covered by implementation tasks:
- Requirement 1: Tasks 2.1-2.3
- Requirement 2: Tasks 3.1-3.17
- Requirement 3: Tasks 4.1-5.4
- Requirement 4: Tasks 4.4-4.12
- Requirement 5: Tasks 6.1-6.13
- Requirement 6: Tasks 7.1-7.16
- Requirement 7: Tasks 8.1-8.7
- Requirement 8: Tasks 9.1-9.6
- Requirement 9: Tasks 10.1-10.3
- Requirement 10: Tasks 1.2, 12.5
- Requirement 11: Tasks 11.1-11.7
- Requirement 12: Tasks 12.1-12.6
- Requirement 13: Tasks 13.1-13.3
- Requirement 14: Tasks 14.1-14.4
- Requirement 15: Tasks 3.6-3.11, 11.4-11.5
- Requirement 16: Tasks 6.7, 7.4-7.5
- Requirement 17: Tasks 16.1-16.5
- Requirement 18: Tasks 17.1-17.8
- Requirement 19: Tasks 18.1-18.6
- Requirement 20: Tasks 15.1-15.6

### Property Tests Coverage

All 32 correctness properties from the design document are covered by property-based test tasks:
- Properties 1-2: Tasks 1.3, 1.6
- Properties 3-5: Tasks 3.3-3.5
- Property 6: Task 3.14
- Property 7: Task 3.16
- Properties 8-9: Tasks 6.10-6.11
- Properties 10-12: Tasks 4.5, 4.8, 4.10
- Properties 13-15: Tasks 6.4, 6.6, 6.8
- Properties 16-17: Tasks 7.13-7.14
- Properties 18-20: Tasks 7.3, 7.5, 7.9
- Properties 21-23: Tasks 8.2, 8.4, 8.6
- Properties 24-26: Tasks 9.2, 9.4, 3.4
- Property 27: Task 11.3
- Properties 28-32: Tasks 11.5, 3.7-3.11

## Estimated Timeline

- **Phase 1: Core Infrastructure** (Tasks 1-2): 3-4 days
- **Phase 2: Manual Workflow** (Task 3): 4-5 days
- **Phase 3: AI Workflow** (Tasks 4-5): 5-6 days
- **Phase 4: Progress & Results** (Tasks 6-7): 5-6 days
- **Phase 5: Export & Enhancements** (Tasks 8-10): 3-4 days
- **Phase 6: Error Handling & Navigation** (Tasks 11-13): 3-4 days
- **Phase 7: Performance & Help** (Tasks 14-15): 2-3 days
- **Phase 8: Responsive & Accessibility** (Tasks 16-17): 4-5 days
- **Phase 9: Security & Testing** (Tasks 18-19): 5-6 days
- **Phase 10: Polish & Deployment** (Task 20): 3-4 days

**Total Estimated Time**: 37-47 days (7-9 weeks)

Note: Timeline assumes one developer working full-time. Adjust based on team size and availability.

## Success Criteria

The implementation will be considered complete when:
1. All non-optional tasks are completed
2. All property-based tests pass (minimum 100 runs each)
3. All unit tests pass with minimum 80% code coverage
4. Both manual and AI evaluation workflows function end-to-end
5. All 20 requirements are validated
6. Accessibility testing passes with NVDA/JAWS
7. Cross-browser testing passes on Chrome, Firefox, Safari, Edge
8. User acceptance testing is successful
9. Documentation is complete
10. Production deployment is successful
