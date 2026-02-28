/**
 * Constants Module
 * Application-wide constants and configuration
 */

// API endpoints
const API_ENDPOINTS = {
  EXTRACT_KEY: '/api/extract_key',
  EVALUATE_BATCH: '/api/evaluate_batch',
  EXPORT: '/api/export',
  LINK_DB: '/api/link_db'
};

// File upload limits
const FILE_LIMITS = {
  MAX_FILE_SIZE: 20 * 1024 * 1024,      // 20MB per file
  MAX_BATCH_SIZE: 100 * 1024 * 1024,    // 100MB total
  MAX_FILES: 200                         // Maximum number of files
};

// Accepted file types
const ACCEPTED_FILE_TYPES = {
  OMR: ['image/jpeg', 'image/png', 'application/pdf'],
  ANSWER_KEY: ['text/csv', 'application/vnd.ms-excel'],
  QUESTION_PAPER: ['image/jpeg', 'image/png', 'application/pdf']
};

// File extensions for display
const FILE_EXTENSIONS = {
  OMR: '.jpg, .png, .pdf',
  ANSWER_KEY: '.csv',
  QUESTION_PAPER: '.pdf, .jpg, .png'
};

// Evaluation modes
const EVALUATION_MODES = {
  MANUAL: 'manual',
  AI: 'ai'
};

// Screen identifiers
const SCREENS = {
  MODE_SELECTION: 'mode-selection',
  MANUAL_WORKFLOW: 'manual-workflow',
  AI_WORKFLOW_PHASE1: 'ai-workflow-phase1',
  AI_WORKFLOW_PHASE2: 'ai-workflow-phase2',
  RESULTS: 'results'
};

// Error types
const ERROR_TYPES = {
  FILE_UPLOAD: 'file_upload',
  FILE_VALIDATION: 'file_validation',
  API_ERROR: 'api_error',
  EXTRACTION_ERROR: 'extraction_error',
  EVALUATION_ERROR: 'evaluation_error',
  EXPORT_ERROR: 'export_error'
};

// Toast notification types
const TOAST_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info'
};

// Set colors for visualization
const SET_COLORS = {
  'A': '#3b82f6',  // blue
  'B': '#10b981',  // green
  'C': '#f59e0b',  // orange
  'D': '#8b5cf6',  // purple
  'UNKNOWN': '#ef4444'  // red
};

// Grade thresholds
const GRADE_THRESHOLDS = {
  A: 90,
  B: 80,
  C: 70,
  D: 60,
  E: 50,
  F: 0
};

// Progress update interval (milliseconds)
const PROGRESS_UPDATE_INTERVAL = 100;

// Answer options
const ANSWER_OPTIONS = ['A', 'B', 'C', 'D', 'E'];

// Number of options choices
const NUM_OPTIONS_CHOICES = [3, 4, 5];
