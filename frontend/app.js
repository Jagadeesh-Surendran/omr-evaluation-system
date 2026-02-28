/**
 * Main Application Entry Point
 * Initializes the application and handles routing
 */

// Initialize application on DOM load
document.addEventListener('DOMContentLoaded', () => {
  console.log('EvalGenius AI - OMR Evaluation System');
  
  // Restore session state if available
  restoreSessionState();
  
  // Initialize the application
  initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
  // Show the current screen based on state
  showScreen(appState.currentScreen);
  
  // Set up event listeners
  setupGlobalEventListeners();
}

/**
 * Show a specific screen
 * @param {string} screenId - Screen identifier from SCREENS constant
 */
function showScreen(screenId) {
  const container = document.getElementById('app-container');
  
  if (!container) {
    console.error('App container not found');
    return;
  }
  
  // Validate screen ID
  const validScreens = Object.values(SCREENS);
  if (!validScreens.includes(screenId)) {
    console.warn(`Invalid screen ID: ${screenId}, defaulting to mode selection`);
    screenId = SCREENS.MODE_SELECTION;
  }
  
  // Update state
  appState.previousScreen = appState.currentScreen;
  appState.currentScreen = screenId;
  
  // Render the appropriate screen
  switch (screenId) {
    case SCREENS.MODE_SELECTION:
      container.innerHTML = renderModeSelectionScreen();
      break;
    case SCREENS.MANUAL_WORKFLOW:
      container.innerHTML = renderManualWorkflow();
      break;
    case SCREENS.AI_WORKFLOW_PHASE1:
      container.innerHTML = renderAIWorkflowPhase1();
      break;
    case SCREENS.AI_WORKFLOW_PHASE2:
      container.innerHTML = renderAIWorkflowPhase2();
      break;
    case SCREENS.RESULTS:
      container.innerHTML = renderResultsView();
      break;
    default:
      container.innerHTML = renderModeSelectionScreen();
  }
  
  // Update browser history
  updateBrowserHistory(screenId);
  
  // Save state after screen change
  saveSessionState();
}

/**
 * Set up global event listeners
 */
function setupGlobalEventListeners() {
  // Help button
  const helpBtn = document.getElementById('help-btn');
  if (helpBtn) {
    helpBtn.addEventListener('click', showHelpModal);
  }
  
  // Handle browser back button
  window.addEventListener('popstate', (event) => {
    if (event.state && event.state.screen) {
      // Navigate without adding to history again
      const container = document.getElementById('app-container');
      appState.previousScreen = appState.currentScreen;
      appState.currentScreen = event.state.screen;
      
      // Render the screen
      switch (event.state.screen) {
        case SCREENS.MODE_SELECTION:
          container.innerHTML = renderModeSelectionScreen();
          break;
        case SCREENS.MANUAL_WORKFLOW:
          container.innerHTML = renderManualWorkflow();
          break;
        case SCREENS.AI_WORKFLOW_PHASE1:
          container.innerHTML = renderAIWorkflowPhase1();
          break;
        case SCREENS.AI_WORKFLOW_PHASE2:
          container.innerHTML = renderAIWorkflowPhase2();
          break;
        case SCREENS.RESULTS:
          container.innerHTML = renderResultsView();
          break;
        default:
          container.innerHTML = renderModeSelectionScreen();
      }
      
      saveSessionState();
    } else {
      // No state, go to mode selection
      showScreen(SCREENS.MODE_SELECTION);
    }
  });
}

/**
 * Update browser history for back button support
 * @param {string} screenId - Screen identifier
 */
function updateBrowserHistory(screenId) {
  const url = `#${screenId}`;
  const state = { screen: screenId };
  
  // Only push state if it's different from current
  if (!history.state || history.state.screen !== screenId) {
    history.pushState(state, '', url);
  }
}

/**
 * Navigate to a specific screen
 * @param {string} screenId - Screen identifier
 */
function navigateTo(screenId) {
  // Validate screen ID
  const validScreens = Object.values(SCREENS);
  if (!validScreens.includes(screenId)) {
    console.warn(`Invalid screen ID: ${screenId}`);
    return;
  }
  
  // Show the screen (this will update history)
  showScreen(screenId);
}

/**
 * Re-render the current screen (useful after state updates)
 */
function renderCurrentScreen() {
  showScreen(appState.currentScreen);
}

/**
 * Go back to previous screen
 */
function goBack() {
  if (appState.previousScreen) {
    showScreen(appState.previousScreen);
  } else {
    // Default to mode selection if no previous screen
    showScreen(SCREENS.MODE_SELECTION);
  }
}

/**
 * Navigate to mode selection screen
 */
function goToModeSelection() {
  // Warn if there's unsaved data
  if (shouldWarnBeforeNavigation()) {
    if (!confirm('Are you sure you want to go back? Any unsaved progress will be lost.')) {
      return;
    }
  }
  
  // Reset session data
  resetSessionData();
  
  // Navigate to mode selection
  showScreen(SCREENS.MODE_SELECTION);
}

/**
 * Check if we should warn before navigation
 * @returns {boolean} True if there's data that would be lost
 */
function shouldWarnBeforeNavigation() {
  // Warn if files are uploaded
  if (appState.uploadedFiles.omrSheets.length > 0 ||
      appState.uploadedFiles.answerKey !== null ||
      appState.uploadedFiles.questionPaper !== null) {
    return true;
  }
  
  // Warn if results exist
  if (appState.results.students.length > 0) {
    return true;
  }
  
  // Warn if evaluation is in progress
  if (appState.progress.isActive) {
    return true;
  }
  
  return false;
}

/**
 * Show help modal
 */
function showHelpModal() {
  showToast('Help documentation coming soon', TOAST_TYPES.INFO);
}

/**
 * Navigate to manual workflow
 */
function goToManualWorkflow() {
  appState.currentMode = EVALUATION_MODES.MANUAL;
  showScreen(SCREENS.MANUAL_WORKFLOW);
}

/**
 * Navigate to AI workflow phase 1
 */
function goToAIWorkflow() {
  appState.currentMode = EVALUATION_MODES.AI;
  showScreen(SCREENS.AI_WORKFLOW_PHASE1);
}

/**
 * Navigate to AI workflow phase 2
 */
function goToAIWorkflowPhase2() {
  if (appState.currentMode !== EVALUATION_MODES.AI) {
    console.error('Cannot navigate to AI phase 2 without being in AI mode');
    return;
  }
  
  // Validate that answer keys are confirmed
  if (!hasConfirmedAnswerKeys()) {
    showToast('Please confirm answer keys before proceeding', TOAST_TYPES.WARNING);
    return;
  }
  
  showScreen(SCREENS.AI_WORKFLOW_PHASE2);
}

/**
 * Navigate back to AI workflow phase 1
 */
function goToAIWorkflowPhase1() {
  if (appState.currentMode !== EVALUATION_MODES.AI) {
    console.error('Cannot navigate to AI phase 1 without being in AI mode');
    return;
  }
  
  showScreen(SCREENS.AI_WORKFLOW_PHASE1);
}

/**
 * Navigate to results screen
 */
function goToResults() {
  showScreen(SCREENS.RESULTS);
}

/**
 * Start a new evaluation (reset and go to mode selection)
 */
function newEvaluation() {
  // Warn if there are results
  if (appState.results.students.length > 0) {
    if (!confirm('Are you sure you want to start a new evaluation? Current results will be lost.')) {
      return;
    }
  }
  
  // Reset all data
  resetAppState();
  clearSessionData();
  
  // Navigate to mode selection
  showScreen(SCREENS.MODE_SELECTION);
}

/**
 * Check if answer keys are confirmed for AI mode
 * @returns {boolean} True if at least one set has answer keys
 */
function hasConfirmedAnswerKeys() {
  const aiKeys = appState.answerKeys.ai;
  
  // Check if at least one set has keys
  return Object.values(aiKeys).some(setKeys => 
    Object.keys(setKeys).length > 0
  );
}

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - Toast type (success, error, warning, info)
 */
function showToast(message, type = TOAST_TYPES.INFO) {
  const container = document.getElementById('toast-container');
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <i class="fas fa-${getToastIcon(type)}"></i>
    <span>${message}</span>
  `;
  
  container.appendChild(toast);
  
  // Animate in
  setTimeout(() => toast.classList.add('show'), 10);
  
  // Remove after 3 seconds
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

/**
 * Get icon for toast type
 * @param {string} type - Toast type
 * @returns {string} Font Awesome icon name
 */
function getToastIcon(type) {
  switch (type) {
    case TOAST_TYPES.SUCCESS: return 'check-circle';
    case TOAST_TYPES.ERROR: return 'exclamation-circle';
    case TOAST_TYPES.WARNING: return 'exclamation-triangle';
    case TOAST_TYPES.INFO: return 'info-circle';
    default: return 'info-circle';
  }
}

/**
 * Placeholder render functions (will be implemented in component files)
 */
function renderModeSelectionScreen() {
  return '<div class="loading">Loading mode selection...</div>';
}

function renderManualWorkflow() {
  return '<div class="loading">Loading manual workflow...</div>';
}

function renderAIWorkflowPhase1() {
  return '<div class="loading">Loading AI workflow...</div>';
}

function renderAIWorkflowPhase2() {
  return '<div class="loading">Loading AI workflow phase 2...</div>';
}

function renderResultsView() {
  return '<div class="loading">Loading results...</div>';
}
