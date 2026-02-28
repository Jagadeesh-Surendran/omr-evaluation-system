/**
 * Progress Modal Component
 * Renders the progress modal for evaluation tracking
 */

/**
 * Render progress modal
 * @returns {string} HTML content
 */
function renderProgressModal() {
  return `
    <div class="modal" id="progress-modal">
      <div class="modal-content progress-modal">
        <div class="progress-header">
          <h3>Processing OMR Sheets</h3>
          <p id="progress-status">Initializing...</p>
        </div>
        
        <div class="progress-content">
          <p>Progress modal will be implemented in subsequent tasks.</p>
        </div>
      </div>
    </div>
  `;
}

/**
 * Show progress modal
 */
function showProgressModal() {
  const modalHTML = `
    <div class="modal active" id="progress-modal">
      <div class="modal-overlay"></div>
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
  
  // Add modal to DOM
  const existingModal = document.getElementById('progress-modal');
  if (existingModal) {
    existingModal.remove();
  }
  
  document.body.insertAdjacentHTML('beforeend', modalHTML);
}

/**
 * Hide progress modal
 */
function hideProgressModal() {
  const modal = document.getElementById('progress-modal');
  if (modal) {
    modal.classList.remove('active');
    setTimeout(() => modal.remove(), 300);
  }
}

/**
 * Update progress UI
 */
function updateProgressUI() {
  const progress = appState.progress;
  const percentage = progress.total > 0 ? Math.round((progress.current / progress.total) * 100) : 0;
  
  // Update circular progress
  const circle = document.getElementById('progress-circle');
  if (circle) {
    const circumference = 2 * Math.PI * 45;
    const offset = circumference - (percentage / 100) * circumference;
    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = offset;
  }
  
  // Update text
  const percentageEl = document.getElementById('progress-percentage');
  if (percentageEl) {
    percentageEl.textContent = `${percentage}%`;
  }
  
  const countEl = document.getElementById('processed-count');
  if (countEl) {
    countEl.textContent = `${progress.current} / ${progress.total}`;
  }
  
  const statusEl = document.getElementById('progress-status');
  if (statusEl) {
    statusEl.textContent = progress.status;
  }
  
  // Update time
  if (progress.startTime) {
    const elapsed = Math.floor((Date.now() - progress.startTime) / 1000);
    const elapsedEl = document.getElementById('time-elapsed');
    if (elapsedEl) {
      elapsedEl.textContent = `${elapsed}s`;
    }
    
    if (progress.current > 0) {
      const avgTime = elapsed / progress.current;
      const remaining = Math.ceil((progress.total - progress.current) * avgTime);
      const remainingEl = document.getElementById('time-remaining');
      if (remainingEl) {
        remainingEl.textContent = `${remaining}s`;
      }
    }
  }
  
  // Update set detection (AI mode only)
  if (appState.currentMode === 'ai' && Object.keys(progress.setDetection).length > 0) {
    const container = document.getElementById('set-detection-container');
    if (container) {
      container.style.display = 'block';
      
      const countsHTML = Object.entries(progress.setDetection).map(([set, count]) => `
        <div class="set-count" data-set="${set}">
          <span class="set-label">Set ${set}</span>
          <span class="set-value">${count}</span>
        </div>
      `).join('');
      
      const countsEl = document.getElementById('set-counts');
      if (countsEl) {
        countsEl.innerHTML = countsHTML;
      }
    }
  }
}

/**
 * Cancel evaluation
 */
function cancelEvaluation() {
  if (confirm('Are you sure you want to cancel the evaluation?')) {
    // Reset progress
    updateProgress({
      isActive: false,
      current: 0,
      total: 0,
      startTime: null,
      status: '',
      setDetection: {}
    });
    
    hideProgressModal();
    showToast('Evaluation cancelled', TOAST_TYPES.INFO);
  }
}
