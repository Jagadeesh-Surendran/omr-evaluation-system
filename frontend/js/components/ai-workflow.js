/**
 * AI Workflow Component
 * Renders the AI evaluation workflow (Phase 1 and Phase 2)
 */

/**
 * Render AI workflow phase 1 screen
 * @returns {string} HTML content
 */
function renderAIWorkflowPhase1() {
  const questionPaper = appState.uploadedFiles.questionPaper;
  const hasQuestionPaper = questionPaper !== null;
  
  return `
    <div class="workflow-container">
      <div class="workflow-header">
        <button class="btn-icon" onclick="navigateTo('${SCREENS.MODE_SELECTION}')">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h2>AI Evaluation - Phase 1: Extract Answer Keys</h2>
      </div>
      
      <div class="workflow-content">
        <div class="ai-upload-section">
          <div class="upload-zone ai-upload ${hasQuestionPaper ? 'has-files' : ''}" 
               id="question-paper-upload-zone"
               ondrop="handleQuestionPaperDrop(event)" 
               ondragover="handleDragOver(event)"
               ondragleave="handleDragLeave(event)">
            <input type="file" 
                   id="question-paper-file" 
                   accept="image/*,.pdf"
                   onchange="handleQuestionPaperUpload(event)"
                   style="display: none;">
            <label for="question-paper-file" class="upload-label">
              <i class="fas fa-brain"></i>
              <h4>Question Paper (Multi-Set)</h4>
              <p>Upload question paper with multiple sets</p>
              <span class="file-formats">Supports: PDF, JPG, PNG</span>
            </label>
            
            ${hasQuestionPaper ? `
              <div class="file-list">
                <div class="file-item">
                  <i class="fas fa-file-pdf"></i>
                  <div class="file-info">
                    <span class="file-name">${questionPaper.name}</span>
                    <span class="file-size">${formatFileSize(questionPaper.size)}</span>
                  </div>
                  <button class="btn-icon btn-remove" onclick="removeQuestionPaper()" title="Remove file">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              </div>
            ` : ''}
          </div>
        </div>
        
        <button id="extract-btn" 
                class="btn-primary btn-large" 
                ${!hasQuestionPaper ? 'disabled' : ''}
                onclick="extractAnswerKeys()">
          <i class="fas fa-wand-magic-sparkles"></i>
          Extract Answer Keys
        </button>
      </div>
    </div>
  `;
}

/**
 * Render AI workflow phase 2 screen (Task 5.1)
 * @returns {string} HTML content
 */
function renderAIWorkflowPhase2() {
  const omrSheets = appState.uploadedFiles.omrSheets;
  const hasOMRSheets = omrSheets.length > 0;
  
  // Get confirmed answer keys summary
  const aiKeys = appState.answerKeys.ai;
  const confirmedSets = Object.keys(aiKeys).filter(set => Object.keys(aiKeys[set]).length > 0);
  
  return `
    <div class="workflow-container">
      <div class="workflow-header">
        <button class="btn-icon" onclick="navigateTo('${SCREENS.AI_WORKFLOW_PHASE1}')">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h2>AI Evaluation - Phase 2: Upload OMR Sheets</h2>
      </div>
      
      <div class="workflow-content">
        <div class="answer-keys-summary">
          <h4><i class="fas fa-check-circle"></i> Answer Keys Confirmed</h4>
          <div class="sets-confirmed">
            ${confirmedSets.map(set => `
              <span class="set-badge" data-set="${set}">
                Set ${set}: ${Object.keys(aiKeys[set]).length} questions
              </span>
            `).join('')}
          </div>
        </div>
        
        <div class="upload-section">
          <div class="upload-zone ${hasOMRSheets ? 'has-files' : ''}" 
               id="omr-upload-zone-ai"
               ondrop="handleOMRDropAI(event)" 
               ondragover="handleDragOver(event)"
               ondragleave="handleDragLeave(event)">
            <input type="file" 
                   id="omr-files-ai" 
                   multiple 
                   accept="image/*,.pdf"
                   onchange="handleOMRUploadAI(event)"
                   style="display: none;">
            <label for="omr-files-ai" class="upload-label">
              <i class="fas fa-file-image"></i>
              <h4>OMR Answer Sheets</h4>
              <p>Upload sheets from all sets</p>
              <span class="file-formats">AI will automatically detect the set for each sheet</span>
            </label>
            
            ${hasOMRSheets ? `
              <div class="file-list" id="omr-file-list-ai">
                ${renderOMRFileList(omrSheets)}
              </div>
            ` : ''}
          </div>
        </div>
        
        <button id="start-eval-ai-btn" 
                class="btn-primary btn-large" 
                ${!hasOMRSheets ? 'disabled' : ''}
                onclick="startAIEvaluation()">
          <i class="fas fa-play-circle"></i>
          Start AI Evaluation
        </button>
      </div>
    </div>
  `;
}

/**
 * Render OMR file list
 * @param {Array} files - Array of File objects
 * @returns {string} HTML for file list
 */
function renderOMRFileList(files) {
  return files.map((file, index) => `
    <div class="file-item">
      <i class="fas ${file.type === 'application/pdf' ? 'fa-file-pdf' : 'fa-file-image'}"></i>
      <div class="file-info">
        <span class="file-name">${file.name}</span>
        <span class="file-size">${formatFileSize(file.size)}</span>
      </div>
      <button class="btn-icon btn-remove" onclick="removeOMRFileAI(${index})" title="Remove file">
        <i class="fas fa-times"></i>
      </button>
    </div>
  `).join('');
}

/**
 * Handle question paper file upload
 * @param {Event} event - File input change event
 */
function handleQuestionPaperUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  // Validate file type
  if (!ACCEPTED_FILE_TYPES.QUESTION_PAPER.includes(file.type)) {
    showToast('Invalid file type. Please upload PDF, JPG, or PNG files.', TOAST_TYPES.ERROR);
    return;
  }
  
  // Validate file size
  if (file.size > FILE_LIMITS.MAX_FILE_SIZE) {
    showToast(`File size exceeds ${FILE_LIMITS.MAX_FILE_SIZE / (1024 * 1024)}MB limit.`, TOAST_TYPES.ERROR);
    return;
  }
  
  // Store file in state
  updateUploadedFiles('questionPaper', file);
  
  // Re-render the screen
  renderCurrentScreen();
  
  showToast('Question paper uploaded successfully', TOAST_TYPES.SUCCESS);
}

/**
 * Handle drag and drop for question paper
 * @param {DragEvent} event - Drop event
 */
function handleQuestionPaperDrop(event) {
  event.preventDefault();
  event.stopPropagation();
  
  const uploadZone = document.getElementById('question-paper-upload-zone');
  uploadZone.classList.remove('drag-over');
  
  const files = event.dataTransfer.files;
  if (files.length > 0) {
    const file = files[0];
    
    // Validate file type
    if (!ACCEPTED_FILE_TYPES.QUESTION_PAPER.includes(file.type)) {
      showToast('Invalid file type. Please upload PDF, JPG, or PNG files.', TOAST_TYPES.ERROR);
      return;
    }
    
    // Validate file size
    if (file.size > FILE_LIMITS.MAX_FILE_SIZE) {
      showToast(`File size exceeds ${FILE_LIMITS.MAX_FILE_SIZE / (1024 * 1024)}MB limit.`, TOAST_TYPES.ERROR);
      return;
    }
    
    // Store file in state
    updateUploadedFiles('questionPaper', file);
    
    // Re-render the screen
    renderCurrentScreen();
    
    showToast('Question paper uploaded successfully', TOAST_TYPES.SUCCESS);
  }
}

/**
 * Handle drag over event
 * @param {DragEvent} event - Drag over event
 */
function handleDragOver(event) {
  event.preventDefault();
  event.stopPropagation();
  event.currentTarget.classList.add('drag-over');
}

/**
 * Handle drag leave event
 * @param {DragEvent} event - Drag leave event
 */
function handleDragLeave(event) {
  event.preventDefault();
  event.stopPropagation();
  event.currentTarget.classList.remove('drag-over');
}

/**
 * Remove uploaded question paper
 */
function removeQuestionPaper() {
  updateUploadedFiles('questionPaper', null);
  renderCurrentScreen();
  showToast('Question paper removed', TOAST_TYPES.INFO);
}

/**
 * Format file size for display
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

/**
 * Extract answer keys from question paper (Task 4.3)
 */
async function extractAnswerKeys() {
  const questionPaper = appState.uploadedFiles.questionPaper;
  
  if (!questionPaper) {
    showToast('Please upload a question paper first', TOAST_TYPES.ERROR);
    return;
  }
  
  // Show loading state
  const extractBtn = document.getElementById('extract-btn');
  const originalHTML = extractBtn.innerHTML;
  extractBtn.disabled = true;
  extractBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Extracting...';
  
  try {
    // Call API to extract answer keys
    const response = await extractAnswerKeysAPI(questionPaper);
    
    // Store extracted keys in state
    if (response.answer_key) {
      // Update AI answer keys for each set
      Object.keys(response.answer_key).forEach(set => {
        updateAIAnswerKey(set, response.answer_key[set]);
      });
      
      // Show review modal
      showAnswerKeyReviewModal(response.answer_key, response.sets_detected || Object.keys(response.answer_key));
      
      showToast(`Successfully extracted answer keys for ${response.sets_detected?.length || Object.keys(response.answer_key).length} sets`, TOAST_TYPES.SUCCESS);
    } else {
      throw new Error('No answer keys found in response');
    }
    
  } catch (error) {
    console.error('Answer key extraction failed:', error);
    showToast(error.userMessage || 'Failed to extract answer keys. Please check the image quality and try again.', TOAST_TYPES.ERROR);
  } finally {
    // Restore button state
    extractBtn.disabled = false;
    extractBtn.innerHTML = originalHTML;
  }
}

/**
 * API call to extract answer keys
 * @param {File} questionPaperFile - Question paper file
 * @returns {Promise<Object>} Extracted answer keys
 */
async function extractAnswerKeysAPI(questionPaperFile) {
  const formData = new FormData();
  formData.append('qp_file', questionPaperFile);
  
  return await callAPI(API_ENDPOINTS.EXTRACT_KEY, 'POST', formData);
}

/**
 * Show answer key review modal (Task 4.4)
 * @param {Object} extractedKeys - Extracted answer keys by set
 * @param {Array} setsDetected - Array of detected set labels
 */
function showAnswerKeyReviewModal(extractedKeys, setsDetected) {
  const modalHTML = `
    <div class="modal active" id="answer-key-review-modal">
      <div class="modal-overlay" onclick="closeAnswerKeyReviewModal()"></div>
      <div class="modal-content large">
        <div class="modal-header">
          <h3>Review Extracted Answer Keys</h3>
          <p>Review and edit answer keys before evaluation</p>
          <button class="btn-icon modal-close" onclick="closeAnswerKeyReviewModal()">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <div class="set-tabs" id="set-tabs">
            ${setsDetected.map((set, index) => `
              <button class="set-tab ${index === 0 ? 'active' : ''}" 
                      data-set="${set}"
                      onclick="switchAnswerKeySet('${set}')">
                Set ${set}
                <span class="question-count">${Object.keys(extractedKeys[set] || {}).length} questions</span>
              </button>
            `).join('')}
          </div>
          
          <div class="answer-key-grid-container">
            <div class="answer-key-grid" id="answer-key-grid">
              ${renderAnswerKeyGrid(extractedKeys[setsDetected[0]], setsDetected[0])}
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button class="btn-outline" onclick="downloadAnswerKeyCSV()">
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
  
  // Add modal to DOM
  const existingModal = document.getElementById('answer-key-review-modal');
  if (existingModal) {
    existingModal.remove();
  }
  
  document.body.insertAdjacentHTML('beforeend', modalHTML);
  
  // Store current set for download
  window.currentAnswerKeySet = setsDetected[0];
}

/**
 * Close answer key review modal
 */
function closeAnswerKeyReviewModal() {
  const modal = document.getElementById('answer-key-review-modal');
  if (modal) {
    modal.remove();
  }
}

/**
 * Switch between answer key sets in the modal
 * @param {string} set - Set label (A, B, C, D)
 */
function switchAnswerKeySet(set) {
  // Update active tab
  const tabs = document.querySelectorAll('.set-tab');
  tabs.forEach(tab => {
    if (tab.dataset.set === set) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });
  
  // Update grid content
  const grid = document.getElementById('answer-key-grid');
  const answerKey = appState.answerKeys.ai[set];
  grid.innerHTML = renderAnswerKeyGrid(answerKey, set);
  
  // Store current set for download
  window.currentAnswerKeySet = set;
}

/**
 * Render answer key grid (Task 4.6)
 * @param {Object} answerKey - Answer key object {1: 'A', 2: 'B', ...}
 * @param {string} setLabel - Set label (A, B, C, D)
 * @returns {string} HTML for answer key grid
 */
function renderAnswerKeyGrid(answerKey, setLabel) {
  if (!answerKey || Object.keys(answerKey).length === 0) {
    return '<p class="empty-state">No answer key data available for this set</p>';
  }
  
  const questions = Object.keys(answerKey).sort((a, b) => parseInt(a) - parseInt(b));
  
  return questions.map(q => {
    const isEdited = appState.answerKeys.edited.has(`${setLabel}-${q}`);
    
    return `
      <div class="answer-item ${isEdited ? 'edited' : ''}" data-question="${q}">
        <span class="question-num">Q${q}</span>
        <select class="answer-select" 
                data-question="${q}" 
                data-set="${setLabel}"
                onchange="handleAnswerEdit('${setLabel}', '${q}', this.value)">
          ${ANSWER_OPTIONS.map(opt => `
            <option value="${opt}" ${answerKey[q] === opt ? 'selected' : ''}>
              ${opt}
            </option>
          `).join('')}
        </select>
        ${isEdited ? '<i class="fas fa-edit edit-indicator" title="Edited"></i>' : ''}
      </div>
    `;
  }).join('');
}

/**
 * Handle answer key edit (Task 4.7)
 * @param {string} set - Set label (A, B, C, D)
 * @param {string} question - Question number
 * @param {string} newAnswer - New answer option
 */
function handleAnswerEdit(set, question, newAnswer) {
  // Validate answer option
  if (!ANSWER_OPTIONS.includes(newAnswer)) {
    showToast('Invalid answer option', TOAST_TYPES.ERROR);
    return;
  }
  
  // Update state
  updateAIAnswer(set, question, newAnswer);
  
  // Re-render the grid to show edit indicator
  const grid = document.getElementById('answer-key-grid');
  const answerKey = appState.answerKeys.ai[set];
  grid.innerHTML = renderAnswerKeyGrid(answerKey, set);
  
  // Show feedback
  showToast(`Updated Q${question} for Set ${set}`, TOAST_TYPES.SUCCESS);
}

/**
 * Validate answer key completeness (Task 4.9)
 * @returns {Object} Validation result {valid: boolean, errors: Array}
 */
function validateAnswerKeyCompleteness() {
  const errors = [];
  const aiKeys = appState.answerKeys.ai;
  
  // Check each set
  Object.keys(aiKeys).forEach(set => {
    const answerKey = aiKeys[set];
    const questionCount = Object.keys(answerKey).length;
    
    if (questionCount === 0) {
      errors.push(`Set ${set} has no answer key`);
    } else {
      // Check for missing questions (gaps in sequence)
      const questions = Object.keys(answerKey).map(q => parseInt(q)).sort((a, b) => a - b);
      const maxQuestion = Math.max(...questions);
      
      for (let i = 1; i <= maxQuestion; i++) {
        if (!answerKey[i.toString()]) {
          errors.push(`Set ${set} is missing answer for question ${i}`);
        }
      }
    }
  });
  
  return {
    valid: errors.length === 0,
    errors: errors
  };
}

/**
 * Confirm and continue to phase 2 (Task 4.9)
 */
function confirmAndContinue() {
  // Validate completeness
  const validation = validateAnswerKeyCompleteness();
  
  if (!validation.valid) {
    showToast('Please complete all answer keys before continuing', TOAST_TYPES.ERROR);
    
    // Show detailed errors
    const errorList = validation.errors.join('\n');
    alert(`Answer key validation errors:\n\n${errorList}`);
    return;
  }
  
  // Close modal
  closeAnswerKeyReviewModal();
  
  // Navigate to phase 2
  navigateTo(SCREENS.AI_WORKFLOW_PHASE2);
  
  showToast('Answer keys confirmed. Ready to upload OMR sheets.', TOAST_TYPES.SUCCESS);
}

/**
 * Download answer key as CSV (Task 4.11)
 */
function downloadAnswerKeyCSV() {
  const currentSet = window.currentAnswerKeySet || 'A';
  const answerKey = appState.answerKeys.ai[currentSet];
  
  if (!answerKey || Object.keys(answerKey).length === 0) {
    showToast('No answer key data to download', TOAST_TYPES.ERROR);
    return;
  }
  
  // Generate CSV content
  let csvContent = 'question_number,answer\n';
  
  const questions = Object.keys(answerKey).sort((a, b) => parseInt(a) - parseInt(b));
  questions.forEach(q => {
    csvContent += `${q},${answerKey[q]}\n`;
  });
  
  // Create blob and download
  const blob = new Blob([csvContent], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `answer_key_set_${currentSet}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  
  showToast(`Downloaded answer key for Set ${currentSet}`, TOAST_TYPES.SUCCESS);
}

/**
 * Handle OMR sheet upload for AI mode (Task 5.2)
 * @param {Event} event - File input change event
 */
function handleOMRUploadAI(event) {
  const files = Array.from(event.target.files);
  if (files.length === 0) return;
  
  // Validate files
  const validFiles = [];
  let hasErrors = false;
  
  files.forEach(file => {
    // Validate file type
    if (!ACCEPTED_FILE_TYPES.OMR.includes(file.type)) {
      showToast(`Invalid file type: ${file.name}. Please upload JPG, PNG, or PDF files.`, TOAST_TYPES.ERROR);
      hasErrors = true;
      return;
    }
    
    // Validate file size
    if (file.size > FILE_LIMITS.MAX_FILE_SIZE) {
      showToast(`File too large: ${file.name}. Maximum size is ${FILE_LIMITS.MAX_FILE_SIZE / (1024 * 1024)}MB.`, TOAST_TYPES.ERROR);
      hasErrors = true;
      return;
    }
    
    validFiles.push(file);
  });
  
  if (validFiles.length === 0) return;
  
  // Check total batch size
  const existingFiles = appState.uploadedFiles.omrSheets;
  const allFiles = [...existingFiles, ...validFiles];
  const totalSize = allFiles.reduce((sum, file) => sum + file.size, 0);
  
  if (totalSize > FILE_LIMITS.MAX_BATCH_SIZE) {
    showToast(`Total batch size exceeds ${FILE_LIMITS.MAX_BATCH_SIZE / (1024 * 1024)}MB limit.`, TOAST_TYPES.ERROR);
    return;
  }
  
  if (allFiles.length > FILE_LIMITS.MAX_FILES) {
    showToast(`Maximum ${FILE_LIMITS.MAX_FILES} files allowed per batch.`, TOAST_TYPES.ERROR);
    return;
  }
  
  // Store files in state
  updateUploadedFiles('omrSheets', allFiles);
  
  // Re-render the screen
  renderCurrentScreen();
  
  showToast(`${validFiles.length} OMR sheet(s) uploaded successfully`, TOAST_TYPES.SUCCESS);
}

/**
 * Handle drag and drop for OMR sheets in AI mode
 * @param {DragEvent} event - Drop event
 */
function handleOMRDropAI(event) {
  event.preventDefault();
  event.stopPropagation();
  
  const uploadZone = document.getElementById('omr-upload-zone-ai');
  uploadZone.classList.remove('drag-over');
  
  const files = Array.from(event.dataTransfer.files);
  if (files.length === 0) return;
  
  // Validate files
  const validFiles = [];
  let hasErrors = false;
  
  files.forEach(file => {
    // Validate file type
    if (!ACCEPTED_FILE_TYPES.OMR.includes(file.type)) {
      showToast(`Invalid file type: ${file.name}. Please upload JPG, PNG, or PDF files.`, TOAST_TYPES.ERROR);
      hasErrors = true;
      return;
    }
    
    // Validate file size
    if (file.size > FILE_LIMITS.MAX_FILE_SIZE) {
      showToast(`File too large: ${file.name}. Maximum size is ${FILE_LIMITS.MAX_FILE_SIZE / (1024 * 1024)}MB.`, TOAST_TYPES.ERROR);
      hasErrors = true;
      return;
    }
    
    validFiles.push(file);
  });
  
  if (validFiles.length === 0) return;
  
  // Check total batch size
  const existingFiles = appState.uploadedFiles.omrSheets;
  const allFiles = [...existingFiles, ...validFiles];
  const totalSize = allFiles.reduce((sum, file) => sum + file.size, 0);
  
  if (totalSize > FILE_LIMITS.MAX_BATCH_SIZE) {
    showToast(`Total batch size exceeds ${FILE_LIMITS.MAX_BATCH_SIZE / (1024 * 1024)}MB limit.`, TOAST_TYPES.ERROR);
    return;
  }
  
  if (allFiles.length > FILE_LIMITS.MAX_FILES) {
    showToast(`Maximum ${FILE_LIMITS.MAX_FILES} files allowed per batch.`, TOAST_TYPES.ERROR);
    return;
  }
  
  // Store files in state
  updateUploadedFiles('omrSheets', allFiles);
  
  // Re-render the screen
  renderCurrentScreen();
  
  showToast(`${validFiles.length} OMR sheet(s) uploaded successfully`, TOAST_TYPES.SUCCESS);
}

/**
 * Remove OMR file from AI mode upload
 * @param {number} index - File index to remove
 */
function removeOMRFileAI(index) {
  const files = [...appState.uploadedFiles.omrSheets];
  files.splice(index, 1);
  updateUploadedFiles('omrSheets', files);
  renderCurrentScreen();
  showToast('File removed', TOAST_TYPES.INFO);
}

/**
 * Start AI evaluation (Task 5.3)
 */
async function startAIEvaluation() {
  const omrFiles = appState.uploadedFiles.omrSheets;
  
  if (omrFiles.length === 0) {
    showToast('Please upload OMR sheets first', TOAST_TYPES.ERROR);
    return;
  }
  
  // Validate answer keys
  const validation = validateAnswerKeyCompleteness();
  if (!validation.valid) {
    showToast('Answer keys are incomplete. Please review and complete them.', TOAST_TYPES.ERROR);
    return;
  }
  
  // Prepare multiplex key
  const multiplexKey = appState.answerKeys.ai;
  
  // Prepare evaluation config
  const config = {
    mode: 'ai',
    numOptions: appState.evaluationConfig.numOptions,
    multiplexKey: multiplexKey
  };
  
  // Show progress modal
  showProgressModal();
  
  // Initialize progress
  updateProgress({
    isActive: true,
    current: 0,
    total: omrFiles.length,
    startTime: Date.now(),
    status: 'Starting AI evaluation...',
    setDetection: {}
  });
  
  // Start simulated progress updates
  const progressInterval = setInterval(() => {
    if (appState.progress.current < appState.progress.total - 1) {
      updateProgress({
        current: appState.progress.current + 1,
        status: `Processing sheet ${appState.progress.current + 1}...`
      });
      updateProgressUI();
    }
  }, PROGRESS_UPDATE_INTERVAL);
  
  try {
    // Call evaluation API
    const results = await evaluateBatchAPI(omrFiles, config);
    
    // Stop progress simulation
    clearInterval(progressInterval);
    
    // Complete progress
    updateProgress({
      current: omrFiles.length,
      status: 'Evaluation complete!'
    });
    updateProgressUI();
    
    // Calculate set detection
    const setDetection = {};
    results.students.forEach(student => {
      const set = student.form_type || 'UNKNOWN';
      setDetection[set] = (setDetection[set] || 0) + 1;
    });
    updateSetDetection(setDetection);
    
    // Store results
    updateResults(results);
    
    // Wait a moment then navigate to results
    setTimeout(() => {
      hideProgressModal();
      navigateTo(SCREENS.RESULTS);
    }, 1000);
    
  } catch (error) {
    clearInterval(progressInterval);
    hideProgressModal();
    console.error('AI evaluation failed:', error);
    showToast(error.userMessage || 'Evaluation failed. Please try again.', TOAST_TYPES.ERROR);
  }
}

/**
 * API call to evaluate batch
 * @param {Array} omrFiles - Array of OMR file objects
 * @param {Object} config - Evaluation configuration
 * @returns {Promise<Object>} Evaluation results
 */
async function evaluateBatchAPI(omrFiles, config) {
  const formData = new FormData();
  
  // Add OMR files
  omrFiles.forEach(file => {
    formData.append('omr_files', file);
  });
  
  // Add configuration
  formData.append('num_options', config.numOptions);
  
  // Add answer key based on mode
  if (config.mode === 'manual') {
    formData.append('answer_key_csv', config.answerKeyFile);
  } else if (config.mode === 'ai') {
    formData.append('multiplex_key', JSON.stringify(config.multiplexKey));
  }
  
  return await callAPI(API_ENDPOINTS.EVALUATE_BATCH, 'POST', formData);
}
