# Design Document: EvalGenius AI OMR Evaluation System UI Redesign

## Overview

This design document specifies the architecture, components, data models, and implementation strategy for redesigning the EvalGenius AI OMR evaluation system to support two distinct evaluation workflows: Manual Evaluation Mode and AI Evaluation Mode. The redesign addresses critical UI/UX issues, adds multi-set question paper handling, and provides clear separation between evaluation approaches while maintaining compatibility with the existing backend API infrastructure.

### Design Goals

1. **Clear Mode Separation**: Provide distinct, intuitive workflows for Manual and AI evaluation modes
2. **Multi-Set Support**: Enable evaluation of question papers with multiple sets (A, B, C, D) with automatic set detection
3. **Real-Time Feedback**: Display progress, status, and results with live updates during evaluation
4. **Enhanced UX**: Improve file upload experience, answer key review, and results visualization
5. **Maintainability**: Create modular, well-structured code that's easy to extend and maintain
6. **Accessibility**: Ensure WCAG compliance with keyboard navigation and screen reader support

### Technology Stack

- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3
- **State Management**: Global state object with session persistence
- **API Communication**: Fetch API with FormData for file uploads
- **UI Components**: Modular component-based architecture (without framework)
- **Styling**: CSS custom properties, flexbox/grid layouts, responsive design

## Architecture

### System Architecture Overview


```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Mode         │  │ Manual Eval  │  │ AI Eval      │          │
│  │ Selection    │  │ Workflow     │  │ Workflow     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Progress     │  │ Results      │  │ Export       │          │
│  │ Modal        │  │ View         │  │ Manager      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    State Management Layer                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Global State Object                                      │   │
│  │ - currentMode, uploadedFiles, answerKeys, results       │   │
│  │ - sessionData, progressData, evaluationMetrics          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                      API Integration Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ /api/        │  │ /api/        │  │ /api/        │          │
│  │ extract_key  │  │ evaluate     │  │ export       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                      Backend Services                            │
│  (Existing Flask API - No Changes Required)                     │
└─────────────────────────────────────────────────────────────────┘
```

### Component Hierarchy


```
App
├── NavigationBar
│   ├── Logo
│   ├── ModeIndicator
│   └── ActionButtons
│
├── ModeSelectionScreen
│   ├── ModeCard (Manual)
│   └── ModeCard (AI)
│
├── ManualEvalWorkflow
│   ├── FileUploadZone (OMR Sheets)
│   ├── FileUploadZone (Answer Key CSV)
│   ├── OptionsPanel
│   │   ├── NumOptionsSelector
│   │   └── EvaluationModeSelector
│   └── StartEvaluationButton
│
├── AIEvalWorkflow
│   ├── Phase1: Answer Key Extraction
│   │   ├── FileUploadZone (Question Paper)
│   │   ├── ExtractButton
│   │   └── AnswerKeyReviewModal
│   │       ├── SetTabs (A, B, C, D)
│   │       ├── AnswerKeyGrid (editable)
│   │       └── ConfirmButton
│   └── Phase2: OMR Evaluation
│       ├── FileUploadZone (OMR Sheets)
│       └── StartEvaluationButton
│
├── ProgressModal
│   ├── CircularProgress
│   ├── StatusMessage
│   ├── MetricsDisplay
│   │   ├── ProcessedCount
│   │   ├── TimeElapsed
│   │   └── TimeRemaining
│   ├── SetDetectionIndicator (AI mode only)
│   └── CancelButton
│
├── ResultsView
│   ├── StatisticsCards
│   │   ├── TotalStudents
│   │   ├── AverageScore
│   │   ├── HighestScore
│   │   └── ProcessingTime
│   ├── SetDistributionChart (AI mode only)
│   ├── AIInsightsPanel
│   ├── ResultsTable
│   │   ├── SearchBox
│   │   ├── FilterControls
│   │   └── DataGrid
│   └── ExportButtons
│
└── ToastNotificationSystem
```

### State Management Approach

The application uses a centralized global state object stored in browser memory during the evaluation session. State is managed through pure functions that return new state objects, ensuring predictable state transitions.

**State Structure:**
```javascript
const appState = {
  currentMode: null,              // 'manual' | 'ai' | null
  currentScreen: 'mode-selection', // Current UI screen
  uploadedFiles: {
    omrSheets: [],                // Array of File objects
    answerKey: null,              // File object (manual mode)
    questionPaper: null           // File object (AI mode)
  },
  answerKeys: {
    manual: null,                 // Single answer key object
    ai: {                         // Multiplex answer key
      setA: {},
      setB: {},
      setC: {},
      setD: {}
    }
  },
  evaluationConfig: {
    numOptions: 5,
    evaluationMode: 'standard'
  },
  progress: {
    isActive: false,
    current: 0,
    total: 0,
    startTime: null,
    status: ''
  },
  results: {
    students: [],
    statistics: {},
    insights: [],
    setDistribution: {}
  }
};
```

### API Integration Patterns



**1. Answer Key Extraction (AI Mode)**
```javascript
POST /api/extract_key
Content-Type: multipart/form-data

Request:
- qp_file: File (question paper PDF/image)

Response:
{
  "answer_key": {
    "A": { "1": "A", "2": "B", ... },
    "B": { "1": "C", "2": "D", ... },
    "C": { "1": "B", "2": "A", ... },
    "D": { "1": "D", "2": "C", ... }
  },
  "count": 40,
  "sets_detected": ["A", "B", "C", "D"]
}
```

**2. Batch Evaluation**
```javascript
POST /api/evaluate_batch
Content-Type: multipart/form-data

Request (Manual Mode):
- omr_files: File[] (multiple OMR sheets)
- answer_key_csv: File (single answer key)
- num_options: number (3, 4, or 5)

Request (AI Mode):
- omr_files: File[] (multiple OMR sheets)
- multiplex_key: JSON string (answer keys for all sets)
- num_options: number (3, 4, or 5)

Response:
{
  "students": [
    {
      "student_id": "001",
      "name": "Student 1",
      "score": 85,
      "grade": "A",
      "form_type": "A",  // AI mode only
      "status": "success",
      "filename": "sheet_001.jpg"
    },
    ...
  ],
  "total_processed": 50,
  "average_score": 78.5,
  "highest_score": 95,
  "processing_time": 2.5,
  "insights": ["Average score is above 75%", ...]
}
```

**3. Export Results**
```javascript
POST /api/export
Content-Type: application/json

Request:
{
  "results": [...],
  "format": "excel" | "csv"
}

Response:
Binary file download (Excel/CSV)
```

### File Upload and Processing Flow

**Manual Mode Flow:**
```
1. User selects Manual Mode
2. User uploads OMR sheets (multiple files)
3. User uploads answer key CSV
4. User configures options (num_options)
5. User clicks "Start Evaluation"
6. System validates files
7. System creates FormData with files
8. System calls /api/evaluate_batch
9. System displays progress modal
10. System receives results
11. System displays results view
```

**AI Mode Flow:**
```
Phase 1: Answer Key Extraction
1. User selects AI Mode
2. User uploads question paper
3. User clicks "Extract Answer Keys"
4. System calls /api/extract_key
5. System displays extracted keys in review modal
6. User reviews and edits keys if needed
7. User clicks "Confirm and Continue"

Phase 2: OMR Evaluation
8. User uploads OMR sheets
9. User clicks "Start Evaluation"
10. System creates FormData with multiplex_key
11. System calls /api/evaluate_batch
12. System displays progress with set detection
13. System receives results with form_type
14. System displays results with set breakdown
```

## Components and Interfaces

### 1. ModeSelectionScreen

**Purpose**: Allow users to choose between Manual and AI evaluation modes

**Structure**:
```javascript
function renderModeSelectionScreen() {
  return `
    <div class="mode-selection-container">
      <h1>Choose Evaluation Mode</h1>
      <div class="mode-cards">
        <div class="mode-card" data-mode="manual">
          <i class="fas fa-file-upload"></i>
          <h3>Manual Evaluation</h3>
          <p>Upload your own answer key CSV</p>
          <ul>
            <li>Quick setup</li>
            <li>Single answer key</li>
            <li>Best for uniform exams</li>
          </ul>
        </div>
        <div class="mode-card" data-mode="ai">
          <i class="fas fa-brain"></i>
          <h3>AI Evaluation</h3>
          <p>AI extracts answer keys from question paper</p>
          <ul>
            <li>Multi-set support</li>
            <li>Automatic extraction</li>
            <li>Best for varied exams</li>
          </ul>
        </div>
      </div>
    </div>
  `;
}
```

**Event Handlers**:
- `onModeSelect(mode)`: Sets currentMode in state and navigates to workflow

**State Updates**:
- Sets `appState.currentMode` to 'manual' or 'ai'
- Sets `appState.currentScreen` to corresponding workflow screen



### 2. ManualEvalWorkflow

**Purpose**: Handle file uploads and configuration for manual evaluation

**Structure**:
```javascript
function renderManualEvalWorkflow() {
  return `
    <div class="workflow-container">
      <div class="workflow-header">
        <button class="back-btn" onclick="goToModeSelection()">
          <i class="fas fa-arrow-left"></i> Back
        </button>
        <h2>Manual Evaluation</h2>
      </div>
      
      <div class="upload-section">
        <div class="upload-zone" id="omr-upload-zone">
          <input type="file" id="omr-files" multiple accept="image/*,.pdf">
          <label for="omr-files">
            <i class="fas fa-file-image"></i>
            <h4>OMR Answer Sheets</h4>
            <p>Click or drag files here</p>
            <span>Supports: JPG, PNG, PDF</span>
          </label>
          <div id="omr-file-list"></div>
        </div>
        
        <div class="upload-zone" id="answer-key-upload-zone">
          <input type="file" id="answer-key-file" accept=".csv">
          <label for="answer-key-file">
            <i class="fas fa-file-csv"></i>
            <h4>Answer Key CSV</h4>
            <p>Click or drag file here</p>
            <span>Format: question_number,answer</span>
          </label>
          <div id="answer-key-preview"></div>
        </div>
      </div>
      
      <div class="options-panel">
        <div class="option-group">
          <label>Number of Options</label>
          <select id="num-options">
            <option value="3">3 Options (A, B, C)</option>
            <option value="4">4 Options (A, B, C, D)</option>
            <option value="5" selected>5 Options (A, B, C, D, E)</option>
          </select>
        </div>
      </div>
      
      <button id="start-eval-btn" class="btn-primary btn-large" disabled>
        <i class="fas fa-play-circle"></i>
        Start Evaluation
      </button>
    </div>
  `;
}
```

**Key Functions**:
- `handleOMRUpload(files)`: Validates and stores OMR files
- `handleAnswerKeyUpload(file)`: Validates CSV format and displays preview
- `validateAnswerKeyCSV(file)`: Parses CSV and checks format
- `startManualEvaluation()`: Initiates evaluation with uploaded files

**Validation Logic**:
```javascript
function validateAnswerKeyCSV(csvContent) {
  const lines = csvContent.split('\n').filter(line => line.trim());
  const answerKey = {};
  const errors = [];
  
  lines.forEach((line, index) => {
    // Skip header if present
    if (index === 0 && line.toLowerCase().includes('question')) return;
    
    const [question, answer] = line.split(',').map(s => s.trim());
    
    // Validate question number
    if (!question || isNaN(question) || parseInt(question) <= 0) {
      errors.push(`Invalid question number at line ${index + 1}`);
    }
    
    // Validate answer option
    if (!answer || !/^[A-E]$/i.test(answer)) {
      errors.push(`Invalid answer option at line ${index + 1}`);
    }
    
    // Check for duplicates
    if (answerKey[question]) {
      errors.push(`Duplicate question ${question}`);
    }
    
    answerKey[question] = answer.toUpperCase();
  });
  
  return { valid: errors.length === 0, answerKey, errors };
}
```

### 3. AIEvalWorkflow

**Purpose**: Handle two-phase AI evaluation workflow

**Phase 1 Structure**:
```javascript
function renderAIEvalPhase1() {
  return `
    <div class="workflow-container">
      <div class="workflow-header">
        <button class="back-btn" onclick="goToModeSelection()">
          <i class="fas fa-arrow-left"></i> Back
        </button>
        <h2>AI Evaluation - Phase 1: Extract Answer Keys</h2>
      </div>
      
      <div class="ai-upload-section">
        <div class="upload-zone ai-upload">
          <input type="file" id="question-paper-file" accept="image/*,.pdf">
          <label for="question-paper-file">
            <i class="fas fa-brain"></i>
            <h4>Question Paper (Multi-Set)</h4>
            <p>Upload question paper with multiple sets</p>
            <span>Supports: PDF, JPG, PNG</span>
          </label>
        </div>
      </div>
      
      <button id="extract-btn" class="btn-primary btn-large" disabled>
        <i class="fas fa-wand-magic-sparkles"></i>
        Extract Answer Keys
      </button>
    </div>
  `;
}
```

**Answer Key Review Modal**:
```javascript
function renderAnswerKeyReviewModal(extractedKeys) {
  return `
    <div class="modal active" id="answer-key-review-modal">
      <div class="modal-content large">
        <div class="modal-header">
          <h3>Review Extracted Answer Keys</h3>
          <p>Review and edit answer keys before evaluation</p>
        </div>
        
        <div class="set-tabs">
          ${Object.keys(extractedKeys).map(set => `
            <button class="set-tab" data-set="${set}">
              Set ${set}
            </button>
          `).join('')}
        </div>
        
        <div class="answer-key-grid" id="answer-key-grid">
          <!-- Dynamically populated based on selected set -->
        </div>
        
        <div class="modal-actions">
          <button class="btn-outline" onclick="downloadAnswerKey()">
            <i class="fas fa-download"></i>
            Download as CSV
          </button>
          <button class="btn-primary" onclick="confirmAndContinue()">
            <i class="fas fa-check"></i>
            Confirm and Continue
          </button>
        </div>
      </div>
    </div>
  `;
}
```

**Answer Key Grid (Editable)**:
```javascript
function renderAnswerKeyGrid(answerKey, setLabel) {
  const questions = Object.keys(answerKey).sort((a, b) => parseInt(a) - parseInt(b));
  
  return questions.map(q => `
    <div class="answer-item" data-question="${q}">
      <span class="question-num">Q${q}</span>
      <select class="answer-select" data-question="${q}" data-set="${setLabel}">
        ${['A', 'B', 'C', 'D', 'E'].map(opt => `
          <option value="${opt}" ${answerKey[q] === opt ? 'selected' : ''}>
            ${opt}
          </option>
        `).join('')}
      </select>
    </div>
  `).join('');
}
```

**Phase 2 Structure**:
```javascript
function renderAIEvalPhase2() {
  return `
    <div class="workflow-container">
      <div class="workflow-header">
        <button class="back-btn" onclick="goToPhase1()">
          <i class="fas fa-arrow-left"></i> Back to Answer Keys
        </button>
        <h2>AI Evaluation - Phase 2: Upload OMR Sheets</h2>
      </div>
      
      <div class="answer-keys-summary">
        <h4>Answer Keys Confirmed</h4>
        <div class="sets-confirmed">
          ${Object.keys(appState.answerKeys.ai).map(set => `
            <span class="set-badge">${set}: ${Object.keys(appState.answerKeys.ai[set]).length} questions</span>
          `).join('')}
        </div>
      </div>
      
      <div class="upload-section">
        <div class="upload-zone">
          <input type="file" id="omr-files-ai" multiple accept="image/*,.pdf">
          <label for="omr-files-ai">
            <i class="fas fa-file-image"></i>
            <h4>OMR Answer Sheets</h4>
            <p>Upload sheets from all sets</p>
            <span>AI will automatically detect the set for each sheet</span>
          </label>
          <div id="omr-file-list-ai"></div>
        </div>
      </div>
      
      <button id="start-eval-ai-btn" class="btn-primary btn-large" disabled>
        <i class="fas fa-play-circle"></i>
        Start AI Evaluation
      </button>
    </div>
  `;
}
```



### 4. ProgressModal

**Purpose**: Display real-time progress during evaluation

**Structure**:
```javascript
function renderProgressModal() {
  return `
    <div class="modal" id="progress-modal">
      <div class="modal-content progress-modal">
        <div class="progress-header">
          <h3>Processing OMR Sheets</h3>
          <p id="progress-status">Initializing...</p>
        </div>
        
        <div class="circular-progress">
          <svg viewBox="0 0 100 100">
            <circle class="progress-bg" cx="50" cy="50" r="45"></circle>
            <circle class="progress-fill" cx="50" cy="50" r="45" id="progress-circle"></circle>
          </svg>
          <div class="progress-text">
            <span id="progress-percentage">0%</span>
          </div>
        </div>
        
        <div class="progress-details">
          <div class="detail-item">
            <span>Processed</span>
            <strong id="processed-count">0 / 0</strong>
          </div>
          <div class="detail-item">
            <span>Time Elapsed</span>
            <strong id="time-elapsed">0s</strong>
          </div>
          <div class="detail-item">
            <span>Estimated Time</span>
            <strong id="time-remaining">--</strong>
          </div>
        </div>
        
        <div id="set-detection-container" class="set-detection" style="display: none;">
          <h4>Set Detection</h4>
          <div id="set-counts"></div>
        </div>
        
        <button class="btn-ghost btn-full" onclick="cancelEvaluation()">
          <i class="fas fa-times"></i>
          Cancel
        </button>
      </div>
    </div>
  `;
}
```

**Progress Update Logic**:
```javascript
function updateProgress(current, total, status, setDetection = null) {
  const percentage = Math.round((current / total) * 100);
  
  // Update circular progress
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (percentage / 100) * circumference;
  document.getElementById('progress-circle').style.strokeDashoffset = offset;
  
  // Update text
  document.getElementById('progress-percentage').textContent = `${percentage}%`;
  document.getElementById('processed-count').textContent = `${current} / ${total}`;
  document.getElementById('progress-status').textContent = status;
  
  // Update time
  const elapsed = Math.floor((Date.now() - appState.progress.startTime) / 1000);
  document.getElementById('time-elapsed').textContent = `${elapsed}s`;
  
  if (current > 0) {
    const avgTime = elapsed / current;
    const remaining = Math.ceil((total - current) * avgTime);
    document.getElementById('time-remaining').textContent = `${remaining}s`;
  }
  
  // Update set detection (AI mode only)
  if (setDetection && appState.currentMode === 'ai') {
    const container = document.getElementById('set-detection-container');
    container.style.display = 'block';
    
    const countsHTML = Object.entries(setDetection).map(([set, count]) => `
      <div class="set-count" data-set="${set}">
        <span class="set-label">Set ${set}</span>
        <span class="set-value">${count}</span>
      </div>
    `).join('');
    
    document.getElementById('set-counts').innerHTML = countsHTML;
  }
}
```

**Simulated Progress for Batch Processing**:
```javascript
async function startEvaluationWithProgress(formData, totalSheets) {
  showProgressModal();
  appState.progress = {
    isActive: true,
    current: 0,
    total: totalSheets,
    startTime: Date.now(),
    status: 'Starting evaluation...'
  };
  
  // Simulate progress updates (since backend processes in batch)
  const progressInterval = setInterval(() => {
    if (appState.progress.current < appState.progress.total - 1) {
      appState.progress.current++;
      updateProgress(
        appState.progress.current,
        appState.progress.total,
        `Processing sheet ${appState.progress.current}...`
      );
    }
  }, 100); // Update every 100ms
  
  try {
    const response = await fetch(`${API_BASE}/evaluate_batch`, {
      method: 'POST',
      body: formData
    });
    
    clearInterval(progressInterval);
    
    if (!response.ok) {
      throw new Error('Evaluation failed');
    }
    
    const results = await response.json();
    
    // Complete progress
    updateProgress(totalSheets, totalSheets, 'Evaluation complete!');
    
    setTimeout(() => {
      hideProgressModal();
      displayResults(results);
    }, 1000);
    
  } catch (error) {
    clearInterval(progressInterval);
    hideProgressModal();
    showToast(`Evaluation failed: ${error.message}`, 'error');
  }
}
```

### 5. ResultsView

**Purpose**: Display evaluation results with statistics, insights, and data table

**Structure**:
```javascript
function renderResultsView(results) {
  return `
    <div class="results-container">
      <div class="results-header">
        <button class="back-btn" onclick="newEvaluation()">
          <i class="fas fa-arrow-left"></i> New Evaluation
        </button>
        <h2>Evaluation Results</h2>
        <div class="export-buttons">
          <button class="btn-outline" onclick="exportResults('csv')">
            <i class="fas fa-download"></i> Export CSV
          </button>
          <button class="btn-primary" onclick="exportResults('excel')">
            <i class="fas fa-file-excel"></i> Export Excel
          </button>
        </div>
      </div>
      
      <!-- Statistics Cards -->
      <div class="stats-grid">
        ${renderStatisticsCards(results)}
      </div>
      
      <!-- Set Distribution (AI mode only) -->
      ${appState.currentMode === 'ai' ? renderSetDistribution(results) : ''}
      
      <!-- AI Insights -->
      <div class="insights-panel">
        <h3><i class="fas fa-lightbulb"></i> AI Insights</h3>
        <div class="insights-grid">
          ${results.insights.map(insight => `
            <div class="insight-item">
              <i class="fas fa-check-circle"></i>
              <p>${insight}</p>
            </div>
          `).join('')}
        </div>
      </div>
      
      <!-- Results Table -->
      <div class="results-table-container">
        <div class="table-controls">
          <div class="search-box">
            <i class="fas fa-search"></i>
            <input type="text" id="search-input" placeholder="Search students...">
          </div>
          ${appState.currentMode === 'ai' ? renderSetFilter() : ''}
        </div>
        
        <table class="results-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Student ID</th>
              <th>Name</th>
              <th>Score</th>
              <th>Grade</th>
              ${appState.currentMode === 'ai' ? '<th>Set</th>' : ''}
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="results-table-body">
            ${renderResultsTableRows(results.students)}
          </tbody>
        </table>
      </div>
    </div>
  `;
}
```

**Set Distribution Chart (AI Mode)**:
```javascript
function renderSetDistribution(results) {
  const setDistribution = {};
  results.students.forEach(student => {
    const set = student.form_type || 'UNKNOWN';
    setDistribution[set] = (setDistribution[set] || 0) + 1;
  });
  
  const maxCount = Math.max(...Object.values(setDistribution));
  
  return `
    <div class="set-distribution-panel">
      <h3><i class="fas fa-chart-bar"></i> Set Distribution</h3>
      <div class="distribution-chart">
        ${Object.entries(setDistribution).map(([set, count]) => {
          const percentage = (count / results.students.length) * 100;
          const barHeight = (count / maxCount) * 100;
          
          return `
            <div class="distribution-bar" data-set="${set}">
              <div class="bar-fill" style="height: ${barHeight}%"></div>
              <span class="bar-label">Set ${set}</span>
              <span class="bar-value">${count} (${percentage.toFixed(1)}%)</span>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;
}
```

**Results Table with Filtering**:
```javascript
function renderResultsTableRows(students) {
  return students.map((student, index) => {
    const grade = calculateGrade(student.score);
    const status = student.status || (student.score >= 50 ? 'pass' : 'fail');
    const isUnknownSet = student.form_type === 'UNKNOWN';
    
    return `
      <tr class="${isUnknownSet ? 'warning-row' : ''}">
        <td>${index + 1}</td>
        <td>${student.student_id || student.id}</td>
        <td>${student.name || 'Student ' + (index + 1)}</td>
        <td><span class="score-badge">${student.score}%</span></td>
        <td><span class="grade-badge grade-${grade}">${grade}</span></td>
        ${appState.currentMode === 'ai' ? `
          <td>
            <span class="set-badge ${isUnknownSet ? 'unknown' : ''}" data-set="${student.form_type}">
              ${student.form_type || 'UNKNOWN'}
            </span>
          </td>
        ` : ''}
        <td><span class="status-badge ${status}">${status.toUpperCase()}</span></td>
        <td>
          <button class="btn-icon" onclick="viewStudentDetails(${index})">
            <i class="fas fa-eye"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');
}
```



## Data Models

### Answer Key Formats

**Single Answer Key (Manual Mode)**:
```javascript
{
  "1": "A",
  "2": "B",
  "3": "C",
  "4": "D",
  "5": "E",
  // ... up to total questions
}
```

**Multiplex Answer Key (AI Mode)**:
```javascript
{
  "A": {
    "1": "A",
    "2": "B",
    "3": "C",
    // ... questions for Set A
  },
  "B": {
    "1": "C",
    "2": "D",
    "3": "A",
    // ... questions for Set B
  },
  "C": {
    "1": "B",
    "2": "A",
    "3": "D",
    // ... questions for Set C
  },
  "D": {
    "1": "D",
    "2": "C",
    "3": "B",
    // ... questions for Set D
  }
}
```

### Student Result Structure

```javascript
{
  "student_id": "001",
  "name": "John Doe",
  "score": 85,
  "grade": "A",
  "form_type": "A",        // AI mode only
  "status": "success",     // success | error | warning
  "filename": "sheet_001.jpg",
  "answers": {             // Optional detailed answers
    "1": "A",
    "2": "B",
    // ...
  },
  "correct_count": 17,
  "incorrect_count": 3,
  "unanswered_count": 0
}
```

### Evaluation Results Structure

```javascript
{
  "students": [
    // Array of student result objects
  ],
  "total_processed": 50,
  "average_score": 78.5,
  "highest_score": 95,
  "lowest_score": 45,
  "processing_time": 2.5,
  "insights": [
    "Average score is above 75%",
    "3 students scored below 50%",
    "Set A had the highest average (82%)"
  ],
  "set_distribution": {    // AI mode only
    "A": 12,
    "B": 15,
    "C": 13,
    "D": 10
  },
  "set_averages": {        // AI mode only
    "A": 82,
    "B": 78,
    "C": 75,
    "D": 79
  }
}
```

### Session State Structure

```javascript
{
  "sessionId": "uuid-v4",
  "timestamp": "2024-01-15T10:30:00Z",
  "mode": "ai",
  "files": {
    "omrCount": 50,
    "questionPaper": "exam_2024.pdf"
  },
  "answerKeys": {
    "sets": ["A", "B", "C", "D"],
    "questionsPerSet": 20
  },
  "results": {
    "totalStudents": 50,
    "averageScore": 78.5
  }
}
```

## Key Functions and Algorithms

### 1. Mode Selection and Routing

```javascript
function selectMode(mode) {
  // Validate mode
  if (!['manual', 'ai'].includes(mode)) {
    showToast('Invalid mode selected', 'error');
    return;
  }
  
  // Update state
  appState.currentMode = mode;
  appState.currentScreen = mode === 'manual' ? 'manual-workflow' : 'ai-workflow-phase1';
  
  // Clear previous session data
  resetSessionData();
  
  // Navigate to workflow
  showScreen(appState.currentScreen);
  
  // Log analytics
  logEvent('mode_selected', { mode });
}

function resetSessionData() {
  appState.uploadedFiles = {
    omrSheets: [],
    answerKey: null,
    questionPaper: null
  };
  appState.answerKeys = {
    manual: null,
    ai: { setA: {}, setB: {}, setC: {}, setD: {} }
  };
  appState.results = {
    students: [],
    statistics: {},
    insights: [],
    setDistribution: {}
  };
}
```

### 2. File Upload and Validation

```javascript
async function handleFileUpload(files, fileType) {
  // Validate file count
  if (fileType === 'omr' && files.length > 200) {
    showToast('Maximum 200 files allowed', 'error');
    return false;
  }
  
  // Validate file types
  const validTypes = {
    'omr': ['image/jpeg', 'image/png', 'application/pdf'],
    'answerKey': ['text/csv'],
    'questionPaper': ['image/jpeg', 'image/png', 'application/pdf']
  };
  
  for (const file of files) {
    if (!validTypes[fileType].includes(file.type)) {
      showToast(`Invalid file type: ${file.name}`, 'error');
      return false;
    }
    
    // Validate file size (20MB per file)
    if (file.size > 20 * 1024 * 1024) {
      showToast(`File too large: ${file.name} (max 20MB)`, 'error');
      return false;
    }
  }
  
  // Calculate total size
  const totalSize = Array.from(files).reduce((sum, file) => sum + file.size, 0);
  if (totalSize > 100 * 1024 * 1024) {
    showToast('Total upload size exceeds 100MB', 'error');
    return false;
  }
  
  // Store files in state
  if (fileType === 'omr') {
    appState.uploadedFiles.omrSheets = Array.from(files);
  } else if (fileType === 'answerKey') {
    appState.uploadedFiles.answerKey = files[0];
    await validateAndPreviewAnswerKey(files[0]);
  } else if (fileType === 'questionPaper') {
    appState.uploadedFiles.questionPaper = files[0];
  }
  
  // Update UI
  updateFileList(fileType);
  checkReadyToEvaluate();
  
  return true;
}
```

### 3. Answer Key Extraction and Review

```javascript
async function extractAnswerKeys() {
  const file = appState.uploadedFiles.questionPaper;
  
  if (!file) {
    showToast('Please upload a question paper', 'error');
    return;
  }
  
  // Show loading state
  setButtonLoading('extract-btn', true);
  
  try {
    const formData = new FormData();
    formData.append('qp_file', file);
    
    const response = await fetch(`${API_BASE}/extract_key`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Extraction failed');
    }
    
    const result = await response.json();
    
    // Store extracted keys
    appState.answerKeys.ai = result.answer_key;
    
    // Show review modal
    showAnswerKeyReviewModal(result.answer_key);
    
    showToast(`Extracted ${result.count} answers from ${result.sets_detected.length} sets`, 'success');
    
  } catch (error) {
    showToast(`Extraction failed: ${error.message}`, 'error');
  } finally {
    setButtonLoading('extract-btn', false);
  }
}

function editAnswerKey(set, question, newAnswer) {
  // Validate answer
  if (!/^[A-E]$/i.test(newAnswer)) {
    showToast('Invalid answer option', 'error');
    return;
  }
  
  // Update state
  appState.answerKeys.ai[set][question] = newAnswer.toUpperCase();
  
  // Mark as edited
  const element = document.querySelector(`[data-set="${set}"][data-question="${question}"]`);
  if (element) {
    element.classList.add('edited');
  }
  
  // Log change
  logEvent('answer_key_edited', { set, question, newAnswer });
}
```

### 4. Progress Tracking Calculations

```javascript
function calculateProgress(current, total, startTime) {
  const percentage = Math.round((current / total) * 100);
  const elapsed = Math.floor((Date.now() - startTime) / 1000);
  
  let remaining = 0;
  let speed = 0;
  
  if (current > 0) {
    const avgTimePerSheet = elapsed / current;
    remaining = Math.ceil((total - current) * avgTimePerSheet);
    speed = Math.round((current / elapsed) * 60); // sheets per minute
  }
  
  return {
    percentage,
    current,
    total,
    elapsed,
    remaining,
    speed,
    status: current === total ? 'Complete' : `Processing sheet ${current} of ${total}`
  };
}

function updateSetDetection(students) {
  const setDistribution = {};
  
  students.forEach(student => {
    const set = student.form_type || 'UNKNOWN';
    setDistribution[set] = (setDistribution[set] || 0) + 1;
  });
  
  return setDistribution;
}
```

### 5. Set Detection Visualization

```javascript
function visualizeSetDetection(setDistribution) {
  const colors = {
    'A': '#3b82f6',  // blue
    'B': '#10b981',  // green
    'C': '#f59e0b',  // orange
    'D': '#8b5cf6',  // purple
    'UNKNOWN': '#ef4444'  // red
  };
  
  const total = Object.values(setDistribution).reduce((sum, count) => sum + count, 0);
  
  return Object.entries(setDistribution).map(([set, count]) => {
    const percentage = ((count / total) * 100).toFixed(1);
    
    return {
      set,
      count,
      percentage,
      color: colors[set] || colors['UNKNOWN'],
      isUnknown: set === 'UNKNOWN'
    };
  });
}
```

### 6. Results Filtering and Sorting

```javascript
function filterResults(students, filters) {
  let filtered = [...students];
  
  // Filter by search term
  if (filters.searchTerm) {
    const term = filters.searchTerm.toLowerCase();
    filtered = filtered.filter(student => 
      student.name?.toLowerCase().includes(term) ||
      student.student_id?.toLowerCase().includes(term)
    );
  }
  
  // Filter by set (AI mode only)
  if (filters.set && filters.set !== 'all') {
    filtered = filtered.filter(student => student.form_type === filters.set);
  }
  
  // Filter by status
  if (filters.status && filters.status !== 'all') {
    filtered = filtered.filter(student => {
      if (filters.status === 'pass') return student.score >= 50;
      if (filters.status === 'fail') return student.score < 50;
      if (filters.status === 'unknown') return student.form_type === 'UNKNOWN';
      return true;
    });
  }
  
  // Sort results
  if (filters.sortBy) {
    filtered.sort((a, b) => {
      const aVal = a[filters.sortBy];
      const bVal = b[filters.sortBy];
      
      if (typeof aVal === 'number') {
        return filters.sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
      } else {
        return filters.sortOrder === 'asc' 
          ? String(aVal).localeCompare(String(bVal))
          : String(bVal).localeCompare(String(aVal));
      }
    });
  }
  
  return filtered;
}
```

### 7. Export Generation

```javascript
async function exportResults(format) {
  const students = appState.results.students;
  
  if (!students || students.length === 0) {
    showToast('No results to export', 'error');
    return;
  }
  
  if (format === 'csv') {
    exportCSV(students);
  } else if (format === 'excel') {
    await exportExcel(students);
  }
}

function exportCSV(students) {
  // Build CSV headers
  const headers = ['#', 'Student ID', 'Name', 'Score', 'Grade'];
  if (appState.currentMode === 'ai') {
    headers.push('Set');
  }
  headers.push('Status', 'Filename');
  
  // Build CSV rows
  const rows = students.map((student, index) => {
    const row = [
      index + 1,
      student.student_id || student.id,
      student.name || '',
      student.score,
      calculateGrade(student.score)
    ];
    
    if (appState.currentMode === 'ai') {
      row.push(student.form_type || 'UNKNOWN');
    }
    
    row.push(
      student.score >= 50 ? 'PASS' : 'FAIL',
      student.filename || ''
    );
    
    return row;
  });
  
  // Generate CSV content
  let csv = headers.join(',') + '\n';
  rows.forEach(row => {
    csv += row.map(cell => `"${cell}"`).join(',') + '\n';
  });
  
  // Add summary section for AI mode
  if (appState.currentMode === 'ai') {
    csv += '\n\nSet Distribution\n';
    csv += 'Set,Count,Average Score\n';
    
    const setStats = calculateSetStatistics(students);
    Object.entries(setStats).forEach(([set, stats]) => {
      csv += `${set},${stats.count},${stats.average}\n`;
    });
  }
  
  // Download file
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  const filename = `evalgenius_results_${timestamp}.csv`;
  downloadFile(csv, filename, 'text/csv');
  
  showToast('CSV exported successfully', 'success');
}

async function exportExcel(students) {
  try {
    const response = await fetch(`${API_BASE}/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        results: students,
        format: 'excel',
        mode: appState.currentMode
      })
    });
    
    if (!response.ok) {
      throw new Error('Export failed');
    }
    
    const blob = await response.blob();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `evalgenius_results_${timestamp}.xlsx`;
    
    downloadBlob(blob, filename);
    showToast('Excel exported successfully', 'success');
    
  } catch (error) {
    showToast(`Export failed: ${error.message}`, 'error');
  }
}
```



## State Management

### Global State Variables

```javascript
// Global state object
const appState = {
  // Mode and navigation
  currentMode: null,              // 'manual' | 'ai' | null
  currentScreen: 'mode-selection', // Current UI screen identifier
  previousScreen: null,           // For back navigation
  
  // File uploads
  uploadedFiles: {
    omrSheets: [],                // Array of File objects
    answerKey: null,              // File object (manual mode)
    questionPaper: null           // File object (AI mode)
  },
  
  // Answer keys
  answerKeys: {
    manual: null,                 // Single answer key object {1: 'A', 2: 'B', ...}
    ai: {                         // Multiplex answer key
      A: {},
      B: {},
      C: {},
      D: {}
    },
    edited: new Set()             // Track edited answer keys
  },
  
  // Evaluation configuration
  evaluationConfig: {
    numOptions: 5,
    evaluationMode: 'standard'
  },
  
  // Progress tracking
  progress: {
    isActive: false,
    current: 0,
    total: 0,
    startTime: null,
    status: '',
    setDetection: {}              // AI mode: count per set
  },
  
  // Results
  results: {
    students: [],
    statistics: {
      totalProcessed: 0,
      averageScore: 0,
      highestScore: 0,
      lowestScore: 0,
      processingTime: 0
    },
    insights: [],
    setDistribution: {},          // AI mode: students per set
    setAverages: {}               // AI mode: average score per set
  },
  
  // UI state
  filters: {
    searchTerm: '',
    set: 'all',
    status: 'all',
    sortBy: null,
    sortOrder: 'asc'
  }
};
```

### Session Persistence

```javascript
// Save state to session storage
function saveSessionState() {
  const stateToSave = {
    currentMode: appState.currentMode,
    currentScreen: appState.currentScreen,
    evaluationConfig: appState.evaluationConfig,
    // Note: Files cannot be serialized, so they're not persisted
    hasFiles: {
      omrSheets: appState.uploadedFiles.omrSheets.length > 0,
      answerKey: appState.uploadedFiles.answerKey !== null,
      questionPaper: appState.uploadedFiles.questionPaper !== null
    }
  };
  
  sessionStorage.setItem('evalgenius_state', JSON.stringify(stateToSave));
}

// Restore state from session storage
function restoreSessionState() {
  const saved = sessionStorage.getItem('evalgenius_state');
  if (saved) {
    const state = JSON.parse(saved);
    appState.currentMode = state.currentMode;
    appState.currentScreen = state.currentScreen;
    appState.evaluationConfig = state.evaluationConfig;
    
    // Show warning if files were present but can't be restored
    if (state.hasFiles.omrSheets || state.hasFiles.answerKey || state.hasFiles.questionPaper) {
      showToast('Previous session detected. Please re-upload your files.', 'info');
    }
  }
}

// Clear session data
function clearSessionData() {
  sessionStorage.removeItem('evalgenius_state');
  resetAppState();
}
```

### State Transitions

```
Mode Selection → Manual Workflow → Evaluation → Results
                                      ↓
                                   Progress Modal

Mode Selection → AI Workflow Phase 1 → Answer Key Review → AI Workflow Phase 2 → Evaluation → Results
                                                                                      ↓
                                                                                  Progress Modal
```

## Error Handling

### Error Types and Handling Strategy

```javascript
const ErrorTypes = {
  FILE_UPLOAD: 'file_upload',
  FILE_VALIDATION: 'file_validation',
  API_ERROR: 'api_error',
  EXTRACTION_ERROR: 'extraction_error',
  EVALUATION_ERROR: 'evaluation_error',
  EXPORT_ERROR: 'export_error'
};

function handleError(error, type) {
  console.error(`[${type}]`, error);
  
  let message = 'An error occurred';
  let suggestions = [];
  
  switch (type) {
    case ErrorTypes.FILE_UPLOAD:
      message = `File upload failed: ${error.message}`;
      suggestions = [
        'Check your internet connection',
        'Ensure file size is under 20MB',
        'Try uploading fewer files at once'
      ];
      break;
      
    case ErrorTypes.FILE_VALIDATION:
      message = `Invalid file: ${error.message}`;
      suggestions = [
        'Ensure file format is correct (JPG, PNG, PDF for images; CSV for answer keys)',
        'Check that CSV follows the format: question_number,answer',
        'Verify file is not corrupted'
      ];
      break;
      
    case ErrorTypes.EXTRACTION_ERROR:
      message = `Answer key extraction failed: ${error.message}`;
      suggestions = [
        'Ensure question paper image is clear and well-lit',
        'Try uploading a higher resolution image',
        'Verify the question paper contains answer keys',
        'Check that set labels (A, B, C, D) are visible'
      ];
      break;
      
    case ErrorTypes.EVALUATION_ERROR:
      message = `Evaluation failed: ${error.message}`;
      suggestions = [
        'Verify OMR sheets are clear and properly scanned',
        'Check that answer key is correct',
        'Ensure all required files are uploaded',
        'Try evaluating with fewer sheets'
      ];
      break;
      
    case ErrorTypes.EXPORT_ERROR:
      message = `Export failed: ${error.message}`;
      suggestions = [
        'Check that results are available',
        'Try a different export format',
        'Ensure browser allows downloads'
      ];
      break;
  }
  
  showErrorModal(message, suggestions);
  logError(type, error);
}

function showErrorModal(message, suggestions) {
  const modal = document.createElement('div');
  modal.className = 'modal active error-modal';
  modal.innerHTML = `
    <div class="modal-content">
      <div class="error-header">
        <i class="fas fa-exclamation-circle"></i>
        <h3>Error</h3>
      </div>
      <p class="error-message">${message}</p>
      ${suggestions.length > 0 ? `
        <div class="error-suggestions">
          <h4>Suggestions:</h4>
          <ul>
            ${suggestions.map(s => `<li>${s}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
      <div class="modal-actions">
        <button class="btn-primary" onclick="closeErrorModal()">
          OK
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}
```

## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and integration points
- Specific UI interactions (button clicks, form submissions)
- Edge cases (empty files, invalid formats, boundary conditions)
- Error conditions (network failures, invalid responses)
- Integration between components

**Property-Based Tests**: Verify universal properties across all inputs
- File validation logic with randomized file types and sizes
- CSV parsing with generated valid and invalid CSVs
- State transitions with random navigation paths
- Filter and sort operations with random data sets
- Progress calculations with random completion states

### Property-Based Testing Configuration

- **Library**: fast-check (JavaScript property-based testing library)
- **Iterations**: Minimum 100 runs per property test
- **Test Tagging**: Each property test references its design document property
- **Tag Format**: `// Feature: ui-redesign-manual-ai-eval-modes, Property {number}: {property_text}`

### Test Organization

```
tests/
├── unit/
│   ├── mode-selection.test.js
│   ├── manual-workflow.test.js
│   ├── ai-workflow.test.js
│   ├── progress-modal.test.js
│   ├── results-view.test.js
│   └── export.test.js
├── property/
│   ├── file-validation.property.test.js
│   ├── csv-parsing.property.test.js
│   ├── state-management.property.test.js
│   ├── filtering-sorting.property.test.js
│   └── progress-calculation.property.test.js
└── integration/
    ├── manual-eval-flow.test.js
    └── ai-eval-flow.test.js
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Mode Selection Navigation

*For any* mode selection ('manual' or 'ai'), when the user selects that mode, the system should navigate to the corresponding workflow screen and persist the mode in state.

**Validates: Requirements 1.4, 1.5**

### Property 2: File Upload State Preservation

*For any* navigation away from and back to a workflow screen within the same session, all uploaded files should remain in state unchanged.

**Validates: Requirements 1.6**

### Property 3: File Type Validation

*For any* file with a valid type (JPG, PNG, PDF for OMR sheets; CSV for answer keys; PDF/JPG/PNG for question papers), the system should accept the file, and for any file with an invalid type, the system should reject it with an error message.

**Validates: Requirements 2.2, 3.3, 11.6, 11.7**

### Property 4: CSV Answer Key Validation

*For any* CSV file, if it follows the format "question_number,answer" with valid question numbers (positive integers) and valid answers (A-E), it should be accepted; otherwise, it should be rejected with specific error messages listing the issues.

**Validates: Requirements 2.3, 11.8, 11.9, 15.1, 15.3, 15.4**

### Property 5: File Metadata Display

*For any* uploaded file, the system should display the filename and file size in the appropriate file list.

**Validates: Requirements 2.4, 2.5, 3.4**

### Property 6: Evaluation Button State

*For any* workflow state, the "Start Evaluation" button should be enabled if and only if all required files are uploaded (OMR sheets + answer key for manual mode; OMR sheets + confirmed answer keys for AI mode).

**Validates: Requirements 2.7**

### Property 7: API Endpoint Invocation

*For any* evaluation start action, the system should call the /api/evaluate_batch endpoint with the correct parameters for the current mode (answer_key_csv for manual, multiplex_key for AI).

**Validates: Requirements 2.8, 3.6, 3.13**

### Property 8: Progress Modal Display

*For any* evaluation start, the progress modal should be displayed immediately and remain visible until evaluation completes or is cancelled.

**Validates: Requirements 2.9, 5.1**

### Property 9: Navigation on Completion

*For any* completed evaluation, the system should navigate to the results view and hide the progress modal.

**Validates: Requirements 2.10, 5.10, 6.1**

### Property 10: Answer Key Extraction Display

*For any* successful answer key extraction, all extracted sets should be displayed in the review modal grouped by set label, with each answer editable.

**Validates: Requirements 3.8, 3.9, 3.10, 4.1, 4.2, 4.3**

### Property 11: Answer Key Editing

*For any* answer key edit action, the system should immediately update the multiplex key in state, display a visual indicator on the edited answer, and mark the answer as edited.

**Validates: Requirements 4.4, 4.5, 4.6**

### Property 12: Answer Key Completeness Validation

*For any* "Confirm and Continue" action in AI mode, if any set has incomplete answer keys (missing questions), the system should display an error and prevent progression; otherwise, it should proceed to phase two.

**Validates: Requirements 4.10**

### Property 13: Progress Calculation

*For any* progress state with current processed count and total count, the system should calculate and display: percentage complete, processed count (X / Y format), elapsed time, and estimated remaining time (if current > 0).

**Validates: Requirements 5.2, 5.3, 5.4, 5.5, 5.8**

### Property 14: Progress Updates

*For any* sheet processed during evaluation, the progress counter should increment and the progress display should update.

**Validates: Requirements 5.6**

### Property 15: Set Detection Display

*For any* AI mode evaluation, the progress modal should display the detected form type for each processed sheet and maintain a running count of sheets per set.

**Validates: Requirements 5.7**

### Property 16: Results Filtering

*For any* search term or filter criteria (set, status), the results table should display only students matching all active filters.

**Validates: Requirements 6.4, 6.9**

### Property 17: Results Sorting

*For any* column sort action, the results table should reorder all rows based on that column's values in the specified direction (ascending or descending).

**Validates: Requirements 6.5**

### Property 18: Statistics Display

*For any* evaluation results, the system should calculate and display total students, average score, highest score, and processing time.

**Validates: Requirements 6.6**

### Property 19: Set Distribution Display

*For any* AI mode results with multiple sets, the system should display a breakdown showing the count and percentage of students per set.

**Validates: Requirements 6.7**

### Property 20: Unknown Set Highlighting

*For any* student with form_type "UNKNOWN", the system should apply warning styling to that row in the results table.

**Validates: Requirements 6.10**

### Property 21: CSV Export Structure

*For any* CSV export action, the generated CSV should include all required columns (Student ID, Name, Score, Grade, Set (if AI mode), Status, Filename) with correct values for each student.

**Validates: Requirements 7.2, 7.3**

### Property 22: Export Filename Format

*For any* export action, the generated filename should follow the format "evalgenius_results_YYYYMMDD_HHMMSS.{extension}" where the timestamp reflects the export time.

**Validates: Requirements 7.6, 7.8**

### Property 23: Export Success Notification

*For any* successful export, the system should display a success toast notification.

**Validates: Requirements 7.10**

### Property 24: PDF File Handling

*For any* PDF file upload, the system should accept it, display it with a PDF icon, and send it to the backend without client-side conversion.

**Validates: Requirements 8.1, 8.2, 8.3**

### Property 25: Mixed File Type Support

*For any* batch upload containing both PDF and image files, all files should be accepted and processed together.

**Validates: Requirements 8.7**

### Property 26: File Size Validation

*For any* file exceeding 20MB or any batch exceeding 100MB total, the system should reject the upload and display an error message.

**Validates: Requirements 8.8, 8.9**

### Property 27: Error Toast Display

*For any* error condition (upload failure, extraction failure, evaluation failure), the system should display an error toast with the failure reason and relevant suggestions.

**Validates: Requirements 11.1, 11.2, 11.5**

### Property 28: CSV Header Handling

*For any* CSV file with or without a header row, the system should correctly parse the answer key data.

**Validates: Requirements 15.2**

### Property 29: Duplicate Question Detection

*For any* CSV with duplicate question numbers, the system should reject it and display an error listing all duplicate questions.

**Validates: Requirements 15.5**

### Property 30: Invalid Answer Detection

*For any* CSV with invalid answer options (not A-E), the system should reject it and display an error listing all invalid entries.

**Validates: Requirements 15.6**

### Property 31: Answer Key Preview

*For any* valid answer key upload, the system should display a preview of the first 10 entries and the total question count.

**Validates: Requirements 15.7, 15.8**

### Property 32: Small Answer Key Warning

*For any* answer key with fewer than 10 questions, the system should display a warning message.

**Validates: Requirements 15.9**

### Property Reflection

After reviewing all properties, the following consolidations were identified:

- **Properties 3 and 26** both deal with file validation but cover different aspects (type vs size), so both are retained
- **Properties 4, 29, and 30** all relate to CSV validation but test different validation rules, so all are retained
- **Property 7** covers API calls for both modes, which is appropriate as a single comprehensive property
- **Properties 13 and 14** cover different aspects of progress (calculation vs updates), so both are retained
- **Properties 16 and 17** cover different operations (filtering vs sorting), so both are retained

All properties provide unique validation value and should be implemented as separate property-based tests.



## Implementation Guidance

### Development Phases

**Phase 1: Core Infrastructure (Week 1)**
- Set up project structure and state management
- Implement navigation system and routing
- Create base UI components (buttons, modals, cards)
- Implement toast notification system

**Phase 2: Mode Selection and Manual Workflow (Week 2)**
- Implement mode selection screen
- Build manual evaluation workflow
- Implement file upload with drag-and-drop
- Add CSV validation and preview
- Integrate with /api/evaluate_batch endpoint

**Phase 3: AI Workflow (Week 3)**
- Build AI workflow phase 1 (question paper upload)
- Implement answer key extraction integration
- Create answer key review modal with editing
- Build AI workflow phase 2 (OMR upload)
- Integrate multiplex key with evaluation endpoint

**Phase 4: Progress and Results (Week 4)**
- Implement progress modal with real-time updates
- Build results view with statistics cards
- Add set distribution visualization (AI mode)
- Implement filtering and sorting
- Add search functionality

**Phase 5: Export and Polish (Week 5)**
- Implement CSV export
- Integrate Excel export with backend
- Add error handling and validation
- Implement accessibility features
- Perform cross-browser testing

**Phase 6: Testing and Documentation (Week 6)**
- Write unit tests for all components
- Implement property-based tests
- Perform integration testing
- Write user documentation
- Conduct user acceptance testing

### Code Organization

```
frontend/
├── index.html              # Main HTML file
├── app.js                  # Main application logic
├── style.css               # Styles
├── js/
│   ├── state.js           # State management
│   ├── api.js             # API integration
│   ├── components/
│   │   ├── mode-selection.js
│   │   ├── manual-workflow.js
│   │   ├── ai-workflow.js
│   │   ├── progress-modal.js
│   │   ├── results-view.js
│   │   └── export.js
│   ├── utils/
│   │   ├── validation.js
│   │   ├── file-handler.js
│   │   ├── csv-parser.js
│   │   └── helpers.js
│   └── constants.js
└── assets/
    ├── icons/
    └── images/
```

### Key Implementation Considerations

**1. File Upload Performance**
- Use FileReader API for client-side file validation
- Implement chunked uploads for large files (future enhancement)
- Show upload progress for large batches
- Validate files before sending to backend

**2. State Management**
- Use immutable state updates
- Implement state history for undo functionality (future enhancement)
- Clear sensitive data on session end
- Validate state transitions

**3. Progress Simulation**
- Backend processes in batch, so simulate progress on frontend
- Use realistic timing based on file count
- Update progress at consistent intervals (100ms)
- Handle edge cases (very fast/slow processing)

**4. Responsive Design**
- Mobile-first approach with progressive enhancement
- Breakpoints: 768px (tablet), 1024px (desktop), 1440px (large desktop)
- Touch-friendly controls (minimum 44x44px)
- Collapsible navigation on small screens

**5. Accessibility**
- Semantic HTML5 elements
- ARIA labels and roles
- Keyboard navigation (Tab, Enter, Escape)
- Screen reader announcements for dynamic content
- Focus management in modals
- Color contrast compliance (WCAG AA)

**6. Browser Compatibility**
- Target: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- Polyfills for older browsers (if needed)
- Feature detection for modern APIs
- Graceful degradation

### Performance Optimization

**1. Lazy Loading**
- Load components only when needed
- Defer non-critical JavaScript
- Use intersection observer for images

**2. Debouncing and Throttling**
- Debounce search input (300ms)
- Throttle scroll events (100ms)
- Throttle progress updates (100ms)

**3. Virtual Scrolling**
- Implement for large result sets (>100 students)
- Render only visible rows
- Recycle DOM elements

**4. Caching**
- Cache API responses in memory
- Store computed values (statistics, filtered results)
- Invalidate cache on data changes

### Security Considerations

**1. Input Validation**
- Validate all file types and sizes client-side
- Sanitize CSV input before parsing
- Validate answer key format strictly
- Prevent XSS in dynamic content

**2. Data Privacy**
- Process files client-side when possible
- Don't store sensitive data in localStorage
- Clear session data on logout
- Use HTTPS for all API calls

**3. Error Handling**
- Don't expose internal errors to users
- Log errors for debugging
- Provide user-friendly error messages
- Implement retry logic for transient failures

### Accessibility Checklist

- [ ] All images have alt text
- [ ] All interactive elements are keyboard accessible
- [ ] Focus indicators are visible
- [ ] Color contrast meets WCAG AA standards
- [ ] ARIA labels on all form controls
- [ ] ARIA live regions for dynamic updates
- [ ] Semantic HTML structure
- [ ] Skip navigation links
- [ ] Screen reader tested (NVDA/JAWS)
- [ ] Keyboard navigation tested

### Browser Testing Matrix

| Browser | Version | Desktop | Mobile | Status |
|---------|---------|---------|--------|--------|
| Chrome  | 90+     | ✓       | ✓      | Primary |
| Firefox | 88+     | ✓       | ✓      | Primary |
| Safari  | 14+     | ✓       | ✓      | Primary |
| Edge    | 90+     | ✓       | -      | Primary |

### Deployment Checklist

- [ ] Minify JavaScript and CSS
- [ ] Optimize images
- [ ] Enable gzip compression
- [ ] Set cache headers
- [ ] Test on production environment
- [ ] Verify API endpoints
- [ ] Check HTTPS configuration
- [ ] Test error handling
- [ ] Verify analytics integration
- [ ] Update documentation

## Diagrams

### Manual Evaluation Flow

```
┌─────────────────┐
│ Mode Selection  │
└────────┬────────┘
         │ Select Manual
         ↓
┌─────────────────┐
│ Upload OMR      │
│ Sheets          │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Upload Answer   │
│ Key CSV         │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Configure       │
│ Options         │
└────────┬────────┘
         │ Start Evaluation
         ↓
┌─────────────────┐
│ Progress Modal  │
│ (Real-time)     │
└────────┬────────┘
         │ Complete
         ↓
┌─────────────────┐
│ Results View    │
│ - Statistics    │
│ - Table         │
│ - Export        │
└─────────────────┘
```

### AI Evaluation Flow

```
┌─────────────────┐
│ Mode Selection  │
└────────┬────────┘
         │ Select AI
         ↓
┌─────────────────┐
│ Phase 1:        │
│ Upload Question │
│ Paper           │
└────────┬────────┘
         │ Extract
         ↓
┌─────────────────┐
│ AI Processing   │
│ (Backend)       │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Review Modal    │
│ - Set A, B, C, D│
│ - Edit Answers  │
│ - Confirm       │
└────────┬────────┘
         │ Confirm
         ↓
┌─────────────────┐
│ Phase 2:        │
│ Upload OMR      │
│ Sheets          │
└────────┬────────┘
         │ Start Evaluation
         ↓
┌─────────────────┐
│ Progress Modal  │
│ - Set Detection │
│ - Real-time     │
└────────┬────────┘
         │ Complete
         ↓
┌─────────────────┐
│ Results View    │
│ - Statistics    │
│ - Set Breakdown │
│ - Table w/ Sets │
│ - Export        │
└─────────────────┘
```

### State Transition Diagram

```
                    ┌──────────────┐
                    │ Mode         │
                    │ Selection    │
                    └──┬────────┬──┘
                       │        │
            ┌──────────┘        └──────────┐
            │                               │
            ↓                               ↓
    ┌───────────────┐              ┌───────────────┐
    │ Manual        │              │ AI Phase 1    │
    │ Workflow      │              │ (Extract)     │
    └───────┬───────┘              └───────┬───────┘
            │                               │
            │                               ↓
            │                      ┌───────────────┐
            │                      │ Answer Key    │
            │                      │ Review        │
            │                      └───────┬───────┘
            │                               │
            │                               ↓
            │                      ┌───────────────┐
            │                      │ AI Phase 2    │
            │                      │ (Upload OMR)  │
            │                      └───────┬───────┘
            │                               │
            └───────────┬───────────────────┘
                        │
                        ↓
                ┌───────────────┐
                │ Evaluation    │
                │ (Progress)    │
                └───────┬───────┘
                        │
                        ↓
                ┌───────────────┐
                │ Results       │
                │ View          │
                └───────────────┘
```

## Conclusion

This design document provides a comprehensive blueprint for implementing the EvalGenius AI OMR evaluation system UI redesign. The architecture supports both Manual and AI evaluation modes with clear separation of concerns, robust error handling, and comprehensive testing strategies.

Key design decisions:
- **Vanilla JavaScript**: Maintains simplicity and avoids framework overhead
- **Component-based architecture**: Enables modularity and reusability
- **Centralized state management**: Ensures predictable state transitions
- **Property-based testing**: Provides comprehensive validation coverage
- **Accessibility-first**: Ensures usability for all users
- **Progressive enhancement**: Works on all modern browsers

The implementation should follow the phased approach outlined, with continuous testing and user feedback integration throughout the development process.

