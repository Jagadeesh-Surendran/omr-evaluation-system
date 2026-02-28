# Requirements Document

## Introduction

This document specifies the requirements for redesigning the EvalGenius AI OMR evaluation system to support two distinct evaluation workflows: Manual Evaluation Mode and AI Evaluation Mode. The redesign addresses critical UI/UX issues, adds missing features for multi-set question paper handling, and provides a clear separation between the two evaluation approaches while maintaining compatibility with the existing backend API infrastructure.

## Glossary

- **OMR_System**: The EvalGenius AI optical mark recognition evaluation system
- **Manual_Eval_Mode**: Evaluation workflow where users provide their own answer key CSV
- **AI_Eval_Mode**: Evaluation workflow where AI extracts answer keys from question papers
- **Question_Paper**: PDF or image file containing exam questions with multiple sets (A, B, C, D, etc.)
- **Answer_Key**: Mapping of question numbers to correct answer options (A, B, C, D, E)
- **OMR_Sheet**: Scanned bubble sheet containing student responses
- **Set_Label**: Identifier for different versions of the same exam (Set A, Set B, Set C, Set D)
- **Multiplex_Key**: Collection of answer keys for multiple exam sets
- **Form_Type**: Detected set identifier from an OMR sheet (A, B, C, D, or UNKNOWN)
- **Student_Database**: CSV file containing student names and roll numbers
- **Evaluation_Session**: Complete workflow from file upload through result generation
- **Progress_Modal**: UI component showing real-time evaluation progress
- **Results_View**: UI component displaying evaluation outcomes and statistics

## Requirements

### Requirement 1: Mode Selection Interface

**User Story:** As a teacher, I want to clearly choose between Manual and AI evaluation modes, so that I can select the workflow that matches my needs.

#### Acceptance Criteria

1. WHEN the user accesses the main dashboard, THE OMR_System SHALL display a mode selection interface with two distinct options
2. THE Mode_Selection_Interface SHALL present "Manual Evaluation" and "AI Evaluation" as clearly labeled choices
3. WHEN the user hovers over a mode option, THE OMR_System SHALL display a tooltip explaining the mode's purpose
4. WHEN the user selects a mode, THE OMR_System SHALL navigate to the corresponding workflow interface
5. THE OMR_System SHALL persist the selected mode for the current Evaluation_Session
6. THE OMR_System SHALL provide a way to return to mode selection without losing uploaded files

### Requirement 2: Manual Evaluation Workflow

**User Story:** As a teacher with a pre-prepared answer key, I want to upload my OMR sheets and answer key CSV, so that I can quickly evaluate student responses.

#### Acceptance Criteria

1. WHEN Manual_Eval_Mode is selected, THE OMR_System SHALL display upload zones for OMR sheets and answer key CSV
2. THE OMR_Upload_Zone SHALL accept multiple files in JPG, PNG, and PDF formats
3. THE Answer_Key_Upload_Zone SHALL accept CSV files in the format "question_number,answer_option"
4. WHEN files are uploaded, THE OMR_System SHALL display a list of uploaded OMR sheets with filenames and file sizes
5. WHEN the answer key is uploaded, THE OMR_System SHALL display the filename and validate the CSV format
6. THE OMR_System SHALL provide a dropdown to select number of options (3, 4, or 5)
7. WHEN all required files are uploaded, THE OMR_System SHALL enable the "Start Evaluation" button
8. WHEN the user clicks "Start Evaluation", THE OMR_System SHALL call the /api/evaluate_batch endpoint
9. WHILE evaluation is in progress, THE OMR_System SHALL display the Progress_Modal with real-time updates
10. WHEN evaluation completes, THE OMR_System SHALL navigate to the Results_View

### Requirement 3: AI Evaluation Workflow

**User Story:** As a teacher with multi-set question papers, I want AI to extract all answer keys automatically, so that I can evaluate sheets from different sets without manual key entry.

#### Acceptance Criteria

1. WHEN AI_Eval_Mode is selected, THE OMR_System SHALL display a two-phase workflow interface
2. THE Phase_One_Interface SHALL display an upload zone for question paper files
3. THE Question_Paper_Upload_Zone SHALL accept PDF and image files
4. WHEN a question paper is uploaded, THE OMR_System SHALL display the filename and file size
5. THE OMR_System SHALL provide an "Extract Answer Keys" button
6. WHEN the user clicks "Extract Answer Keys", THE OMR_System SHALL call the /api/extract_key endpoint
7. WHILE extraction is in progress, THE OMR_System SHALL display a loading indicator with status message
8. WHEN extraction completes, THE OMR_System SHALL display all extracted answer keys grouped by Set_Label
9. THE OMR_System SHALL detect and display answer keys for Set A, Set B, Set C, and Set D if present
10. FOR ALL extracted answer keys, THE OMR_System SHALL provide an edit interface for manual corrections
11. WHEN the user confirms the extracted keys, THE OMR_System SHALL proceed to Phase Two
12. THE Phase_Two_Interface SHALL display an upload zone for OMR sheets
13. WHEN OMR sheets are uploaded and evaluation starts, THE OMR_System SHALL send the Multiplex_Key to /api/evaluate_batch
14. THE OMR_System SHALL automatically detect the Form_Type for each OMR_Sheet
15. THE OMR_System SHALL evaluate each sheet using the corresponding set's answer key

### Requirement 4: Answer Key Review and Edit Interface

**User Story:** As a teacher, I want to review and edit AI-extracted answer keys before evaluation, so that I can correct any extraction errors.

#### Acceptance Criteria

1. WHEN answer keys are extracted, THE OMR_System SHALL display a review interface showing all sets
2. THE Review_Interface SHALL display answer keys in a grid format with question numbers and answers
3. FOR ALL answer entries, THE OMR_System SHALL provide inline editing capability
4. WHEN the user clicks an answer, THE OMR_System SHALL display a dropdown with options A, B, C, D, E
5. WHEN the user changes an answer, THE OMR_System SHALL update the Multiplex_Key immediately
6. THE OMR_System SHALL highlight edited answers with a visual indicator
7. THE Review_Interface SHALL display the total number of questions per set
8. THE OMR_System SHALL provide a "Download as CSV" button for each set's answer key
9. THE OMR_System SHALL provide a "Confirm and Continue" button to proceed to OMR upload
10. WHEN the user clicks "Confirm and Continue", THE OMR_System SHALL validate that all sets have complete answer keys

### Requirement 5: Real-Time Progress Tracking

**User Story:** As a teacher, I want to see real-time progress during evaluation, so that I know how long the process will take.

#### Acceptance Criteria

1. WHEN evaluation starts, THE OMR_System SHALL display the Progress_Modal
2. THE Progress_Modal SHALL display a circular progress indicator showing percentage complete
3. THE Progress_Modal SHALL display "Processed X / Y sheets" counter
4. THE Progress_Modal SHALL display elapsed time in seconds
5. THE Progress_Modal SHALL calculate and display estimated remaining time
6. WHILE processing each sheet, THE OMR_System SHALL update the progress counter
7. IF AI_Eval_Mode is active, THE Progress_Modal SHALL display the detected Form_Type for each processed sheet
8. THE Progress_Modal SHALL display processing speed in sheets per minute
9. THE OMR_System SHALL provide a "Cancel" button to abort evaluation
10. WHEN evaluation completes, THE Progress_Modal SHALL display "Evaluation Complete" for 1 second before closing

### Requirement 6: Multi-Set Results Display

**User Story:** As a teacher, I want to see which set each student's sheet belonged to, so that I can verify correct answer key usage.

#### Acceptance Criteria

1. WHEN evaluation completes, THE OMR_System SHALL display the Results_View
2. THE Results_Table SHALL include a "Set" column showing the Form_Type for each student
3. THE Results_Table SHALL display student ID, name, score, grade, set, and status
4. THE OMR_System SHALL provide filtering by Form_Type
5. THE OMR_System SHALL provide sorting by any column
6. THE OMR_System SHALL display statistics cards showing total students, average score, highest score, and processing time
7. IF multiple sets were used, THE OMR_System SHALL display a breakdown of students per set
8. THE OMR_System SHALL generate insights based on per-set performance
9. THE Results_View SHALL provide a search box to filter students by name or ID
10. THE OMR_System SHALL highlight students with Form_Type "UNKNOWN" in a warning color

### Requirement 7: Enhanced Export Functionality

**User Story:** As a teacher, I want to export results with set information included, so that I can maintain complete records.

#### Acceptance Criteria

1. THE Results_View SHALL provide export buttons for CSV and Excel formats
2. WHEN the user clicks "Export CSV", THE OMR_System SHALL generate a CSV file
3. THE CSV_Export SHALL include columns: Student ID, Name, Score, Grade, Set, Status, Filename
4. WHEN the user clicks "Export Excel", THE OMR_System SHALL call /api/export with format=excel
5. THE Excel_Export SHALL include the same columns as CSV plus question-level details
6. THE OMR_System SHALL include the evaluation timestamp in the export filename
7. THE OMR_System SHALL trigger a browser download with the appropriate filename
8. THE Export_Filename SHALL follow the format "evalgenius_results_YYYYMMDD_HHMMSS.csv"
9. IF AI_Eval_Mode was used, THE Export SHALL include a summary sheet showing answer keys for all sets
10. THE OMR_System SHALL display a success toast notification after export completes

### Requirement 8: PDF Upload Support for OMR Sheets

**User Story:** As a teacher, I want to upload PDF files containing multiple OMR sheets, so that I don't have to convert them to images first.

#### Acceptance Criteria

1. THE OMR_Upload_Zone SHALL accept PDF files in addition to image files
2. WHEN a PDF is uploaded, THE OMR_System SHALL display it in the file list with a PDF icon
3. THE OMR_System SHALL send PDF files to the backend without client-side conversion
4. THE Backend SHALL handle PDF files by extracting pages as images
5. THE OMR_System SHALL count each page in a PDF as a separate sheet for progress tracking
6. THE Progress_Modal SHALL display "Processing page X of PDF" when handling PDF files
7. THE OMR_System SHALL support mixed uploads of PDFs and images in the same batch
8. THE OMR_System SHALL validate PDF file size does not exceed 20MB
9. IF a PDF exceeds the size limit, THE OMR_System SHALL display an error message
10. THE Results_View SHALL display the PDF filename with page number for each student

### Requirement 9: Student Database Integration

**User Story:** As a teacher, I want to link student names from my database to evaluation results, so that results show actual names instead of just IDs.

#### Acceptance Criteria

1. THE Results_View SHALL provide an "Import Student Database" button
2. WHEN the user clicks the button, THE OMR_System SHALL display a file upload dialog
3. THE Upload_Dialog SHALL accept CSV files with columns for roll number and name
4. WHEN a database CSV is uploaded, THE OMR_System SHALL call /api/link_db
5. THE OMR_System SHALL match students by sequential position in the results list
6. WHEN linking completes, THE OMR_System SHALL update the Results_Table with student names
7. THE OMR_System SHALL display a success message showing how many names were linked
8. THE OMR_System SHALL preserve unmatched results with placeholder names
9. THE OMR_System SHALL allow re-importing the database to correct mistakes
10. THE Updated_Results SHALL be included in subsequent exports

### Requirement 10: Session State Management

**User Story:** As a teacher, I want my uploaded files and extracted keys to persist during my session, so that I can navigate between screens without losing data.

#### Acceptance Criteria

1. THE OMR_System SHALL store uploaded OMR files in browser memory during the Evaluation_Session
2. THE OMR_System SHALL store the uploaded answer key in browser memory
3. IF AI_Eval_Mode is active, THE OMR_System SHALL store the Multiplex_Key in browser memory
4. THE OMR_System SHALL store the selected mode in browser memory
5. WHEN the user navigates back from Results_View, THE OMR_System SHALL restore the previous screen state
6. THE OMR_System SHALL clear session data when the user clicks "New Evaluation"
7. THE OMR_System SHALL warn the user before clearing session data if results exist
8. THE OMR_System SHALL provide a "Back" button on each workflow screen
9. WHEN the user clicks "Back", THE OMR_System SHALL return to the previous step without losing data
10. THE OMR_System SHALL clear all session data when the browser tab is closed

### Requirement 11: Error Handling and Validation

**User Story:** As a teacher, I want clear error messages when something goes wrong, so that I can fix issues and complete my evaluation.

#### Acceptance Criteria

1. WHEN a file upload fails, THE OMR_System SHALL display an error toast with the failure reason
2. WHEN answer key extraction fails, THE OMR_System SHALL display suggestions for improving image quality
3. WHEN evaluation fails for a specific sheet, THE OMR_System SHALL mark that student with an error status
4. THE Results_Table SHALL display error details when the user clicks on an error status
5. WHEN the backend returns an error, THE OMR_System SHALL parse the error_type and display appropriate messages
6. THE OMR_System SHALL validate file types before upload
7. IF an invalid file type is selected, THE OMR_System SHALL display an error and reject the file
8. THE OMR_System SHALL validate CSV format for answer keys
9. IF the CSV format is invalid, THE OMR_System SHALL display the expected format
10. THE OMR_System SHALL provide a "Retry" button for failed operations

### Requirement 12: Navigation and Layout Improvements

**User Story:** As a teacher, I want intuitive navigation between sections, so that I can easily move through the evaluation workflow.

#### Acceptance Criteria

1. THE OMR_System SHALL display a progress indicator showing current workflow step
2. THE Progress_Indicator SHALL show steps: Mode Selection → Upload → Processing → Results
3. THE OMR_System SHALL highlight the current step in the progress indicator
4. THE OMR_System SHALL disable future steps in the progress indicator until prerequisites are met
5. THE OMR_System SHALL provide a "Home" button to return to mode selection
6. THE OMR_System SHALL provide breadcrumb navigation showing the current location
7. THE OMR_System SHALL maintain consistent header and navigation across all screens
8. THE OMR_System SHALL use distinct visual styles for Manual_Eval_Mode and AI_Eval_Mode
9. THE OMR_System SHALL display the selected mode name in the header
10. THE OMR_System SHALL provide keyboard shortcuts for common actions (Enter to submit, Esc to cancel)

### Requirement 13: Upload Zone Clarity

**User Story:** As a teacher, I want upload zones to clearly indicate what files are required, so that I don't upload the wrong files.

#### Acceptance Criteria

1. THE OMR_Upload_Zone SHALL display the label "OMR Answer Sheets"
2. THE OMR_Upload_Zone SHALL display accepted formats: "JPG, PNG, PDF"
3. THE OMR_Upload_Zone SHALL display an icon representing multiple documents
4. THE Answer_Key_Upload_Zone SHALL display the label "Answer Key CSV"
5. THE Answer_Key_Upload_Zone SHALL display accepted format: "CSV"
6. THE Answer_Key_Upload_Zone SHALL display an icon representing a spreadsheet
7. THE Question_Paper_Upload_Zone SHALL display the label "Question Paper (Multi-Set)"
8. THE Question_Paper_Upload_Zone SHALL display accepted formats: "PDF, JPG, PNG"
9. THE Question_Paper_Upload_Zone SHALL display an icon representing a document with sets
10. THE OMR_System SHALL display example file format information below each upload zone

### Requirement 14: Batch Processing Performance

**User Story:** As a teacher, I want to evaluate large batches of sheets quickly, so that I can process entire classes efficiently.

#### Acceptance Criteria

1. WHEN the user uploads more than 10 sheets, THE OMR_System SHALL use /api/evaluate_batch instead of /api/evaluate_single
2. THE OMR_System SHALL process sheets in parallel using the backend's ThreadPoolExecutor
3. THE OMR_System SHALL support uploading up to 200 sheets in a single batch
4. THE OMR_System SHALL validate that total upload size does not exceed 100MB
5. IF the batch size limit is exceeded, THE OMR_System SHALL display an error message
6. THE OMR_System SHALL display estimated processing time based on batch size
7. THE OMR_System SHALL maintain responsive UI during batch processing
8. THE Progress_Modal SHALL update at least once per second during batch processing
9. THE OMR_System SHALL complete evaluation of 50 sheets in under 2 minutes
10. THE OMR_System SHALL log performance metrics for batch operations

### Requirement 15: Answer Key Format Validation

**User Story:** As a teacher, I want the system to validate my answer key format, so that I can fix errors before evaluation starts.

#### Acceptance Criteria

1. WHEN an answer key CSV is uploaded, THE OMR_System SHALL parse and validate the format
2. THE OMR_System SHALL accept CSV with or without header row
3. THE OMR_System SHALL validate that question numbers are positive integers
4. THE OMR_System SHALL validate that answers are valid options (A, B, C, D, or E)
5. IF duplicate question numbers are found, THE OMR_System SHALL display an error listing the duplicates
6. IF invalid answer options are found, THE OMR_System SHALL display an error listing the invalid entries
7. THE OMR_System SHALL display a preview of the first 10 answer key entries after successful upload
8. THE OMR_System SHALL display the total number of questions in the answer key
9. THE OMR_System SHALL warn if the answer key has fewer than 10 questions
10. THE OMR_System SHALL provide a "Download Sample CSV" link showing the correct format

### Requirement 16: Multi-Set Detection Visualization

**User Story:** As a teacher, I want to see visual confirmation of set detection, so that I can verify the system is using the correct answer keys.

#### Acceptance Criteria

1. WHILE processing in AI_Eval_Mode, THE Progress_Modal SHALL display the detected Form_Type for each sheet
2. THE Progress_Modal SHALL use color coding for different sets (A=blue, B=green, C=orange, D=purple)
3. THE Progress_Modal SHALL display a running count of sheets per set
4. THE Progress_Modal SHALL display a warning icon for sheets with Form_Type "UNKNOWN"
5. WHEN evaluation completes, THE Results_View SHALL display a set distribution chart
6. THE Set_Distribution_Chart SHALL show the number of students per set as a bar chart
7. THE Results_View SHALL display average scores per set
8. THE OMR_System SHALL highlight sets with significantly different average scores
9. THE Results_View SHALL provide a filter to show only sheets with Form_Type "UNKNOWN"
10. THE OMR_System SHALL generate an insight if more than 10% of sheets have Form_Type "UNKNOWN"

### Requirement 17: Responsive Design

**User Story:** As a teacher, I want the interface to work on different screen sizes, so that I can use it on my laptop or tablet.

#### Acceptance Criteria

1. THE OMR_System SHALL display correctly on screens with minimum width 768px
2. THE OMR_System SHALL use responsive grid layouts that adapt to screen size
3. THE Results_Table SHALL be horizontally scrollable on smaller screens
4. THE Progress_Modal SHALL scale appropriately for different screen sizes
5. THE Upload_Zones SHALL stack vertically on screens smaller than 1024px
6. THE Navigation_Header SHALL collapse to a hamburger menu on screens smaller than 768px
7. THE OMR_System SHALL use touch-friendly button sizes (minimum 44x44px)
8. THE OMR_System SHALL test and verify functionality on Chrome, Firefox, Safari, and Edge
9. THE OMR_System SHALL maintain readability with font sizes no smaller than 14px
10. THE OMR_System SHALL use CSS media queries for responsive breakpoints

### Requirement 18: Accessibility Compliance

**User Story:** As a teacher with visual impairments, I want the interface to be accessible, so that I can use screen readers and keyboard navigation.

#### Acceptance Criteria

1. THE OMR_System SHALL provide alt text for all images and icons
2. THE OMR_System SHALL support full keyboard navigation with Tab and Enter keys
3. THE OMR_System SHALL provide ARIA labels for all interactive elements
4. THE OMR_System SHALL maintain color contrast ratio of at least 4.5:1 for text
5. THE OMR_System SHALL provide focus indicators for all focusable elements
6. THE OMR_System SHALL announce status changes to screen readers using ARIA live regions
7. THE Progress_Modal SHALL announce progress updates to screen readers
8. THE OMR_System SHALL provide skip navigation links
9. THE OMR_System SHALL use semantic HTML elements (nav, main, section, article)
10. THE OMR_System SHALL test with NVDA and JAWS screen readers

### Requirement 19: Data Privacy and Security

**User Story:** As a teacher, I want student data to be handled securely, so that I can comply with privacy regulations.

#### Acceptance Criteria

1. THE OMR_System SHALL process all files client-side before sending to the backend
2. THE OMR_System SHALL use HTTPS for all API communications
3. THE Backend SHALL delete temporary files immediately after processing
4. THE OMR_System SHALL not store student data in browser local storage
5. THE OMR_System SHALL clear all session data when the user logs out
6. THE OMR_System SHALL display a privacy notice on first use
7. THE OMR_System SHALL not send student names to the backend during evaluation
8. THE Student_Database linking SHALL occur client-side only
9. THE OMR_System SHALL provide a "Clear All Data" button in settings
10. THE OMR_System SHALL log all file uploads and evaluations for audit purposes

### Requirement 20: Help and Documentation

**User Story:** As a new teacher, I want access to help documentation, so that I can learn how to use the system effectively.

#### Acceptance Criteria

1. THE OMR_System SHALL provide a "Help" button in the navigation header
2. WHEN the user clicks "Help", THE OMR_System SHALL display a help modal
3. THE Help_Modal SHALL include step-by-step guides for both evaluation modes
4. THE Help_Modal SHALL include example files for download
5. THE Help_Modal SHALL include troubleshooting tips for common issues
6. THE OMR_System SHALL provide contextual help tooltips on each screen
7. THE OMR_System SHALL display a "Quick Start" guide on first use
8. THE Quick_Start_Guide SHALL highlight key features and workflow steps
9. THE OMR_System SHALL provide a "What's New" section for feature updates
10. THE OMR_System SHALL include links to video tutorials and documentation

