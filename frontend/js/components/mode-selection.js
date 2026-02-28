/**
 * Mode Selection Component
 * Renders the mode selection screen with two mode cards
 * Implements Requirements 1.1, 1.2, 1.3
 */

/**
 * Render mode selection screen
 * @returns {string} HTML content
 */
function renderModeSelectionScreen() {
  return `
    <div class="mode-selection-container">
      <h1>Choose Evaluation Mode</h1>
      <p class="subtitle">Select the evaluation workflow that matches your needs</p>
      
      <div class="mode-cards">
        <div class="mode-card" 
             onclick="selectMode('${EVALUATION_MODES.MANUAL}')"
             data-mode="manual"
             title="For users with pre-prepared answer keys">
          <i class="fas fa-file-upload"></i>
          <h3>Manual Evaluation</h3>
          <p>Upload your own answer key CSV</p>
          <ul>
            <li>Quick setup</li>
            <li>Single answer key</li>
            <li>Best for uniform exams</li>
          </ul>
        </div>
        
        <div class="mode-card" 
             onclick="selectMode('${EVALUATION_MODES.AI}')"
             data-mode="ai"
             title="For users with multi-set question papers">
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

/**
 * Select evaluation mode
 * Implements Requirements 1.4, 1.5
 * @param {string} mode - Mode identifier ('manual' or 'ai')
 */
function selectMode(mode) {
  try {
    // Validate mode parameter
    if (!mode || typeof mode !== 'string') {
      console.error('Invalid mode parameter:', mode);
      showToast('Invalid mode selected', TOAST_TYPES.ERROR);
      return;
    }
    
    // Validate mode value
    if (!Object.values(EVALUATION_MODES).includes(mode)) {
      console.error('Unknown mode value:', mode);
      showToast('Invalid mode selected. Please choose Manual or AI evaluation.', TOAST_TYPES.ERROR);
      return;
    }
    
    // Check if already in this mode
    if (appState.currentMode === mode) {
      console.log('Already in mode:', mode);
      // Still navigate to the workflow screen in case user is on mode selection
      const screen = mode === EVALUATION_MODES.MANUAL 
        ? SCREENS.MANUAL_WORKFLOW 
        : SCREENS.AI_WORKFLOW_PHASE1;
      navigateTo(screen);
      return;
    }
    
    // Update state with selected mode
    appState.currentMode = mode;
    
    // Reset session data for new evaluation
    resetSessionData();
    
    // Determine target screen based on mode
    const targetScreen = mode === EVALUATION_MODES.MANUAL 
      ? SCREENS.MANUAL_WORKFLOW 
      : SCREENS.AI_WORKFLOW_PHASE1;
    
    // Validate target screen exists
    if (!Object.values(SCREENS).includes(targetScreen)) {
      console.error('Invalid target screen:', targetScreen);
      showToast('Navigation error. Please try again.', TOAST_TYPES.ERROR);
      return;
    }
    
    // Navigate to workflow (this will persist state via saveSessionState)
    navigateTo(targetScreen);
    
    // Log analytics event
    logModeSelection(mode);
    
    // Show success notification
    const modeName = mode === EVALUATION_MODES.MANUAL ? 'Manual' : 'AI';
    showToast(`${modeName} evaluation mode selected`, TOAST_TYPES.SUCCESS);
    
  } catch (error) {
    console.error('Error in selectMode:', error);
    showToast('An error occurred while selecting mode. Please try again.', TOAST_TYPES.ERROR);
  }
}

/**
 * Log mode selection for analytics
 * @param {string} mode - Selected mode
 */
function logModeSelection(mode) {
  const timestamp = new Date().toISOString();
  console.log(`[Analytics] Mode selected: ${mode} at ${timestamp}`);
  
  // Store in session for analytics
  const analyticsData = {
    event: 'mode_selected',
    mode: mode,
    timestamp: timestamp
  };
  
  // Save to session storage for potential analytics integration
  try {
    const existingAnalytics = sessionStorage.getItem('evalgenius_analytics');
    const analytics = existingAnalytics ? JSON.parse(existingAnalytics) : [];
    analytics.push(analyticsData);
    sessionStorage.setItem('evalgenius_analytics', JSON.stringify(analytics));
  } catch (error) {
    console.warn('Failed to log analytics:', error);
  }
}
