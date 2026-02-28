/**
 * State Management Module
 * Manages global application state for the OMR evaluation system
 */

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

/**
 * Reset session data to initial state
 */
function resetSessionData() {
  appState.uploadedFiles = {
    omrSheets: [],
    answerKey: null,
    questionPaper: null
  };
  appState.answerKeys = {
    manual: null,
    ai: { A: {}, B: {}, C: {}, D: {} },
    edited: new Set()
  };
  appState.results = {
    students: [],
    statistics: {},
    insights: [],
    setDistribution: {},
    setAverages: {}
  };
}

/**
 * Save state to session storage
 */
function saveSessionState() {
  const stateToSave = {
    currentMode: appState.currentMode,
    currentScreen: appState.currentScreen,
    evaluationConfig: appState.evaluationConfig,
    hasFiles: {
      omrSheets: appState.uploadedFiles.omrSheets.length > 0,
      answerKey: appState.uploadedFiles.answerKey !== null,
      questionPaper: appState.uploadedFiles.questionPaper !== null
    }
  };
  
  sessionStorage.setItem('evalgenius_state', JSON.stringify(stateToSave));
}

/**
 * Restore state from session storage
 */
function restoreSessionState() {
  const saved = sessionStorage.getItem('evalgenius_state');
  if (saved) {
    const state = JSON.parse(saved);
    appState.currentMode = state.currentMode;
    appState.currentScreen = state.currentScreen;
    appState.evaluationConfig = state.evaluationConfig;
  }
}

/**
 * Clear session data
 */
function clearSessionData() {
  sessionStorage.removeItem('evalgenius_state');
  resetSessionData();
}

/**
 * State update functions with immutability
 * These functions return new state objects instead of mutating existing state
 */

/**
 * Update current mode
 * @param {string} mode - 'manual' | 'ai' | null
 */
function updateMode(mode) {
  appState.currentMode = mode;
  appState.currentScreen = mode === 'manual' ? 'manual-workflow' : 
                          mode === 'ai' ? 'ai-workflow-phase1' : 
                          'mode-selection';
  saveSessionState();
}

/**
 * Update current screen
 * @param {string} screen - Screen identifier
 */
function updateScreen(screen) {
  appState.previousScreen = appState.currentScreen;
  appState.currentScreen = screen;
  saveSessionState();
}

/**
 * Update uploaded files
 * @param {string} fileType - 'omrSheets' | 'answerKey' | 'questionPaper'
 * @param {File|File[]|null} files - File(s) to store
 */
function updateUploadedFiles(fileType, files) {
  if (fileType === 'omrSheets') {
    appState.uploadedFiles.omrSheets = Array.isArray(files) ? [...files] : [];
  } else if (fileType === 'answerKey') {
    appState.uploadedFiles.answerKey = files;
  } else if (fileType === 'questionPaper') {
    appState.uploadedFiles.questionPaper = files;
  }
  saveSessionState();
}

/**
 * Update answer key for manual mode
 * @param {Object} answerKey - Answer key object {1: 'A', 2: 'B', ...}
 */
function updateManualAnswerKey(answerKey) {
  appState.answerKeys.manual = { ...answerKey };
}

/**
 * Update answer key for AI mode
 * @param {string} set - 'A' | 'B' | 'C' | 'D'
 * @param {Object} answerKey - Answer key object for the set
 */
function updateAIAnswerKey(set, answerKey) {
  appState.answerKeys.ai[set] = { ...answerKey };
}

/**
 * Update a single answer in AI mode answer key
 * @param {string} set - 'A' | 'B' | 'C' | 'D'
 * @param {string} question - Question number
 * @param {string} answer - Answer option (A-E)
 */
function updateAIAnswer(set, question, answer) {
  appState.answerKeys.ai[set] = {
    ...appState.answerKeys.ai[set],
    [question]: answer
  };
  appState.answerKeys.edited.add(`${set}-${question}`);
}

/**
 * Update evaluation configuration
 * @param {Object} config - Configuration object
 */
function updateEvaluationConfig(config) {
  appState.evaluationConfig = {
    ...appState.evaluationConfig,
    ...config
  };
  saveSessionState();
}

/**
 * Update progress state
 * @param {Object} progressData - Progress data object
 */
function updateProgress(progressData) {
  appState.progress = {
    ...appState.progress,
    ...progressData
  };
}

/**
 * Update set detection counts (AI mode)
 * @param {Object} setDetection - Set detection counts {A: 5, B: 3, ...}
 */
function updateSetDetection(setDetection) {
  appState.progress.setDetection = { ...setDetection };
}

/**
 * Update results
 * @param {Object} results - Results object with students, statistics, insights
 */
function updateResults(results) {
  appState.results = {
    students: results.students ? [...results.students] : [],
    statistics: results.statistics ? { ...results.statistics } : {},
    insights: results.insights ? [...results.insights] : [],
    setDistribution: results.setDistribution ? { ...results.setDistribution } : {},
    setAverages: results.setAverages ? { ...results.setAverages } : {}
  };
}

/**
 * Update filters
 * @param {Object} filters - Filter object
 */
function updateFilters(filters) {
  appState.filters = {
    ...appState.filters,
    ...filters
  };
}

/**
 * Reset app state to initial values
 */
function resetAppState() {
  appState.currentMode = null;
  appState.currentScreen = 'mode-selection';
  appState.previousScreen = null;
  resetSessionData();
  appState.evaluationConfig = {
    numOptions: 5,
    evaluationMode: 'standard'
  };
  appState.progress = {
    isActive: false,
    current: 0,
    total: 0,
    startTime: null,
    status: '',
    setDetection: {}
  };
  appState.filters = {
    searchTerm: '',
    set: 'all',
    status: 'all',
    sortBy: null,
    sortOrder: 'asc'
  };
}
