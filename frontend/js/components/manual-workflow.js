/**
 * Manual Workflow Component
 * Renders the manual evaluation workflow
 */

/**
 * Render manual workflow screen
 * @returns {string} HTML content
 */
function renderManualWorkflow() {
  const omrFiles = appState.uploadedFiles.omrSheets;
  const answerKeyFile = appState.uploadedFiles.answerKey;
  const numOptions = appState.evaluationConfig.numOptions;
  
  // Set up drag-and-drop after render
  setTimeout(() => {
    setupDragAndDrop();
  }, 0);
  
  return `
    <div class="workflow-container">
      <div class="workflow-header">
        <button class="btn-icon back-btn" onclick="goToModeSelection()" title="Back to Mode Selection">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h2>Manual Evaluation</h2>
      </div>
      
      <div class="upload-section">
        <!-- OMR Sheets Upload Zone -->
        <div class="upload-zone" id="omr-upload-zone" data-upload-type="omr">
          <input 
            type="file" 
            id="omr-files" 
            multiple 
            accept="${FILE_EXTENSIONS.OMR}"
            style="display: none;"
            onchange="handleOMRUpload(this.files)"
          >
          <label for="omr-files" class="upload-label">
            <i class="fas fa-file-image upload-icon"></i>
            <h4>OMR Answer Sheets</h4>
            <p class="upload-hint">Click or drag files here</p>
            <span class="upload-formats">Supports: JPG, PNG, PDF</span>
          </label>
          <div id="omr-file-list" class="file-list">
            ${renderOMRFileList(omrFiles)}
          </div>
        </div>
        
        <!-- Answer Key CSV Upload Zone -->
        <div class="upload-zone" id="answer-key-upload-zone" data-upload-type="answer-key">
          <input 
            type="file" 
            id="answer-key-file" 
            accept="${FILE_EXTENSIONS.ANSWER_KEY}"
            style="display: none;"
            onchange="handleAnswerKeyUpload(this.files[0])"
          >
          <label for="answer-key-file" class="upload-label">
            <i class="fas fa-file-csv upload-icon"></i>
            <h4>Answer Key CSV</h4>
            <p class="upload-hint">Click or drag file here</p>
            <span class="upload-formats">Format: question_number,answer</span>
          </label>
          <div id="answer-key-preview" class="file-preview">
            ${renderAnswerKeyPreview(answerKeyFile)}
          </div>
        </div>
      </div>
      
      <div class="options-panel">
        <div class="option-group">
          <label for="num-options">Number of Options</label>
          <select id="num-options" onchange="handleNumOptionsChange(this.value)">
            <option value="3" ${numOptions === 3 ? 'selected' : ''}>3 Options (A, B, C)</option>
            <option value="4" ${numOptions === 4 ? 'selected' : ''}>4 Options (A, B, C, D)</option>
            <option value="5" ${numOptions === 5 ? 'selected' : ''}>5 Options (A, B, C, D, E)</option>
          </select>
        </div>
      </div>
      
      <button 
        id="start-eval-btn" 
        class="btn-primary btn-large" 
        onclick="startManualEvaluation()"
        ${isReadyToEvaluate() ? '' : 'disabled'}
      >
        <i class="fas fa-play-circle"></i>
        Start Evaluation
      </button>
    </div>
  `;
}

/**
 * Render OMR file list
 * @param {File[]} files - Array of uploaded OMR files
 * @returns {string} HTML content
 */
function renderOMRFileList(files) {
  if (!files || files.length === 0) {
    return '';
  }
  
  return `
    <div class="file-list-header">
      <span>${files.length} file${files.length !== 1 ? 's' : ''} uploaded</span>
      <button class="btn-text" onclick="clearOMRFiles()">
        <i class="fas fa-times"></i> Clear all
      </button>
    </div>
    <div class="file-items">
      ${files.map((file, index) => `
        <div class="file-item">
          <i class="fas fa-${getFileIcon(file.type)}"></i>
          <div class="file-info">
            <span class="file-name">${file.name}</span>
            <span class="file-size">${formatFileSize(file.size)}</span>
          </div>
          <button class="btn-icon-small" onclick="removeOMRFile(${index})" title="Remove file">
            <i class="fas fa-times"></i>
          </button>
        </div>
      `).join('')}
    </div>
  `;
}

/**
 * Render answer key preview
 * @param {File} file - Uploaded answer key file
 * @returns {string} HTML content
 */
function renderAnswerKeyPreview(file) {
  if (!file) {
    return '';
  }
  
  const answerKey = appState.answerKeys.manual;
  
  return `
    <div class="file-item answer-key-file">
      <i class="fas fa-file-csv"></i>
      <div class="file-info">
        <span class="file-name">${file.name}</span>
        <span class="file-size">${formatFileSize(file.size)}</span>
      </div>
      <button class="btn-icon-small" onclick="clearAnswerKey()" title="Remove file">
        <i class="fas fa-times"></i>
      </button>
    </div>
    ${answerKey ? `
      <div class="answer-key-summary">
        <div class="summary-header">
          <i class="fas fa-check-circle"></i>
          <span>Answer key validated</span>
        </div>
        <div class="summary-details">
          <span class="detail-item">
            <strong>${Object.keys(answerKey).length}</strong> questions
          </span>
        </div>
      </div>
    ` : ''}
  `;
}

/**
 * Get file icon based on MIME type
 * @param {string} mimeType - File MIME type
 * @returns {string} Font Awesome icon name
 */
function getFileIcon(mimeType) {
  if (mimeType === 'application/pdf') {
    return 'file-pdf';
  } else if (mimeType.startsWith('image/')) {
    return 'file-image';
  } else if (mimeType.includes('csv')) {
    return 'file-csv';
  }
  return 'file';
}

/**
 * Format file size for display
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
function formatFileSize(bytes) {
  if (bytes < 1024) {
    return bytes + ' B';
  } else if (bytes < 1024 * 1024) {
    return (bytes / 1024).toFixed(1) + ' KB';
  } else {
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }
}

/**
 * Check if ready to start evaluation
 * @returns {boolean} True if all required files are uploaded
 */
function isReadyToEvaluate() {
  return appState.uploadedFiles.omrSheets.length > 0 && 
         appState.uploadedFiles.answerKey !== null &&
         appState.answerKeys.manual !== null;
}

/**
 * Handle OMR file upload
 * @param {FileList} files - Uploaded files
 */
async function handleOMRUpload(files) {
  if (!files || files.length === 0) {
    return;
  }
  
  // Validate file count
  if (files.length > FILE_LIMITS.MAX_FILES) {
    showToast(`Maximum ${FILE_LIMITS.MAX_FILES} files allowed`, TOAST_TYPES.ERROR);
    return;
  }
  
  // Validate each file
  const validFiles = [];
  let totalSize = 0;
  
  for (const file of files) {
    // Check file type
    if (!ACCEPTED_FILE_TYPES.OMR.includes(file.type)) {
      showToast(`Invalid file type: ${file.name}. Accepted formats: JPG, PNG, PDF`, TOAST_TYPES.ERROR);
      continue;
    }
    
    // Check file size
    if (file.size > FILE_LIMITS.MAX_FILE_SIZE) {
      showToast(`File too large: ${file.name} (max ${formatFileSize(FILE_LIMITS.MAX_FILE_SIZE)})`, TOAST_TYPES.ERROR);
      continue;
    }
    
    totalSize += file.size;
    validFiles.push(file);
  }
  
  // Check total batch size
  if (totalSize > FILE_LIMITS.MAX_BATCH_SIZE) {
    showToast(`Total upload size exceeds ${formatFileSize(FILE_LIMITS.MAX_BATCH_SIZE)}`, TOAST_TYPES.ERROR);
    return;
  }
  
  // Add to existing files or replace
  const existingFiles = appState.uploadedFiles.omrSheets;
  const allFiles = [...existingFiles, ...validFiles];
  
  // Check combined file count
  if (allFiles.length > FILE_LIMITS.MAX_FILES) {
    showToast(`Total files would exceed ${FILE_LIMITS.MAX_FILES} limit`, TOAST_TYPES.ERROR);
    return;
  }
  
  // Update state
  updateUploadedFiles('omrSheets', allFiles);
  
  // Show success message
  showToast(`${validFiles.length} file${validFiles.length !== 1 ? 's' : ''} uploaded successfully`, TOAST_TYPES.SUCCESS);
  
  // Re-render the screen
  showScreen(SCREENS.MANUAL_WORKFLOW);
}

/**
 * Handle answer key file upload
 * @param {File} file - Uploaded answer key file
 */
async function handleAnswerKeyUpload(file) {
  if (!file) {
    return;
  }
  
  // Validate file type
  if (!ACCEPTED_FILE_TYPES.ANSWER_KEY.includes(file.type) && !file.name.endsWith('.csv')) {
    showToast('Invalid file type. Please upload a CSV file', TOAST_TYPES.ERROR);
    return;
  }
  
  // Validate file size
  if (file.size > FILE_LIMITS.MAX_FILE_SIZE) {
    showToast(`File too large (max ${formatFileSize(FILE_LIMITS.MAX_FILE_SIZE)})`, TOAST_TYPES.ERROR);
    return;
  }
  
  // Read and validate CSV content
  try {
    const csvContent = await readFileAsText(file);
    const validation = validateAnswerKeyCSV(csvContent);
    
    if (!validation.valid) {
      showToast(`Invalid CSV format: ${validation.errors[0]}`, TOAST_TYPES.ERROR);
      return;
    }
    
    // Store file and parsed answer key
    updateUploadedFiles('answerKey', file);
    updateManualAnswerKey(validation.answerKey);
    
    showToast(`Answer key uploaded: ${Object.keys(validation.answerKey).length} questions`, TOAST_TYPES.SUCCESS);
    
    // Re-render the screen
    showScreen(SCREENS.MANUAL_WORKFLOW);
    
  } catch (error) {
    showToast(`Failed to read file: ${error.message}`, TOAST_TYPES.ERROR);
  }
}

/**
 * Read file as text
 * @param {File} file - File to read
 * @returns {Promise<string>} File content as text
 */
function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = (e) => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}

/**
 * Validate answer key CSV content
 * @param {string} csvContent - CSV file content
 * @returns {Object} Validation result with valid flag, answerKey object, and errors array
 */
function validateAnswerKeyCSV(csvContent) {
  const lines = csvContent.split('\n').filter(line => line.trim());
  const answerKey = {};
  const errors = [];
  
  if (lines.length === 0) {
    return { valid: false, answerKey: {}, errors: ['CSV file is empty'] };
  }
  
  lines.forEach((line, index) => {
    // Skip header if present (check for common header keywords)
    if (index === 0 && /question|q|number|answer|key/i.test(line)) {
      return;
    }
    
    // Parse line
    const parts = line.split(',').map(s => s.trim());
    
    if (parts.length < 2) {
      errors.push(`Invalid format at line ${index + 1}: expected "question,answer"`);
      return;
    }
    
    const [question, answer] = parts;
    
    // Validate question number
    if (!question || isNaN(question) || parseInt(question) <= 0) {
      errors.push(`Invalid question number at line ${index + 1}: "${question}"`);
      return;
    }
    
    // Validate answer option
    if (!answer || !/^[A-E]$/i.test(answer)) {
      errors.push(`Invalid answer option at line ${index + 1}: "${answer}" (must be A-E)`);
      return;
    }
    
    // Check for duplicates
    if (answerKey[question]) {
      errors.push(`Duplicate question ${question} at line ${index + 1}`);
      return;
    }
    
    answerKey[question] = answer.toUpperCase();
  });
  
  // Check if we have any valid answers
  if (Object.keys(answerKey).length === 0 && errors.length === 0) {
    errors.push('No valid answer key entries found');
  }
  
  return {
    valid: errors.length === 0,
    answerKey,
    errors
  };
}

/**
 * Handle number of options change
 * @param {string} value - Selected number of options
 */
function handleNumOptionsChange(value) {
  updateEvaluationConfig({ numOptions: parseInt(value) });
}

/**
 * Clear all OMR files
 */
function clearOMRFiles() {
  updateUploadedFiles('omrSheets', []);
  showScreen(SCREENS.MANUAL_WORKFLOW);
}

/**
 * Remove a specific OMR file
 * @param {number} index - File index to remove
 */
function removeOMRFile(index) {
  const files = [...appState.uploadedFiles.omrSheets];
  files.splice(index, 1);
  updateUploadedFiles('omrSheets', files);
  showScreen(SCREENS.MANUAL_WORKFLOW);
}

/**
 * Clear answer key file
 */
function clearAnswerKey() {
  updateUploadedFiles('answerKey', null);
  updateManualAnswerKey(null);
  showScreen(SCREENS.MANUAL_WORKFLOW);
}

/**
 * Start manual evaluation
 * Integrates with the backend API to evaluate OMR sheets using the uploaded answer key
 */
async function startManualEvaluation() {
  // Validate that all required files are present
  if (!isReadyToEvaluate()) {
    showToast('Please upload OMR sheets and answer key before starting evaluation', TOAST_TYPES.ERROR);
    return;
  }
  
  const omrFiles = appState.uploadedFiles.omrSheets;
  const answerKeyFile = appState.uploadedFiles.answerKey;
  const numOptions = appState.evaluationConfig.numOptions;
  
  // Disable the start button to prevent double submission
  const startBtn = document.getElementById('start-eval-btn');
  if (startBtn) {
    startBtn.disabled = true;
    startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
  }
  
  try {
    // Build FormData with all required parameters
    const formData = new FormData();
    
    // Add OMR files
    omrFiles.forEach(file => {
      formData.append('omr_files', file);
    });
    
    // Add answer key CSV
    formData.append('answer_key_csv', answerKeyFile);
    
    // Add number of options
    formData.append('num_options', numOptions.toString());
    
    // Initialize progress tracking
    updateProgress({
      isActive: true,
      current: 0,
      total: omrFiles.length,
      startTime: Date.now(),
      status: 'Starting evaluation...'
    });
    
    // Call the API endpoint
    const results = await callAPI(API_ENDPOINTS.EVALUATE_BATCH, 'POST', formData);
    
    // Store results in state
    updateResults({
      students: results.students || [],
      statistics: {
        totalProcessed: results.total_processed || results.students?.length || 0,
        averageScore: results.average_score || 0,
        highestScore: results.highest_score || 0,
        lowestScore: results.lowest_score || 0,
        processingTime: results.processing_time || 0
      },
      insights: results.insights || [],
      setDistribution: {},
      setAverages: {}
    });
    
    // Mark progress as complete
    updateProgress({
      isActive: false,
      current: omrFiles.length,
      total: omrFiles.length,
      status: 'Evaluation complete!'
    });
    
    // Show success message
    showToast(`Evaluation complete! Processed ${results.total_processed || results.students?.length || 0} sheets`, TOAST_TYPES.SUCCESS);
    
    // Navigate to results view
    showScreen(SCREENS.RESULTS);
    
  } catch (error) {
    // Handle errors
    console.error('Evaluation failed:', error);
    
    // Mark progress as inactive
    updateProgress({
      isActive: false
    });
    
    // Show error message with user-friendly text
    const errorMessage = error.userMessage || error.message || 'Evaluation failed. Please try again.';
    showToast(errorMessage, TOAST_TYPES.ERROR);
    
    // Re-enable the start button
    if (startBtn) {
      startBtn.disabled = false;
      startBtn.innerHTML = '<i class="fas fa-play-circle"></i> Start Evaluation';
    }
  }
}

/**
 * Set up drag-and-drop functionality for upload zones
 */
function setupDragAndDrop() {
  const omrZone = document.getElementById('omr-upload-zone');
  const answerKeyZone = document.getElementById('answer-key-upload-zone');
  
  if (omrZone) {
    setupDropZone(omrZone, 'omr');
  }
  
  if (answerKeyZone) {
    setupDropZone(answerKeyZone, 'answer-key');
  }
}

/**
 * Set up a single drop zone
 * @param {HTMLElement} zone - Upload zone element
 * @param {string} type - Upload type ('omr' or 'answer-key')
 */
function setupDropZone(zone, type) {
  // Prevent default drag behaviors
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    zone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });
  
  // Highlight drop zone when item is dragged over it
  ['dragenter', 'dragover'].forEach(eventName => {
    zone.addEventListener(eventName, () => {
      zone.classList.add('drag-over');
    }, false);
  });
  
  ['dragleave', 'drop'].forEach(eventName => {
    zone.addEventListener(eventName, () => {
      zone.classList.remove('drag-over');
    }, false);
  });
  
  // Handle dropped files
  zone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (type === 'omr') {
      handleOMRUpload(files);
    } else if (type === 'answer-key') {
      handleAnswerKeyUpload(files[0]);
    }
  }, false);
}

/**
 * Prevent default drag behaviors
 * @param {Event} e - Event object
 */
function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}
