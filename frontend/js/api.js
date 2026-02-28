/**
 * API Integration Module
 * Handles all backend API communications
 */

// API base URL - will be configured based on environment
const API_BASE = window.location.origin;

// API endpoint configuration
const API_ENDPOINTS = {
  EXTRACT_KEY: '/api/extract_key',
  EVALUATE_BATCH: '/api/evaluate_batch',
  EXPORT: '/api/export',
  LINK_DB: '/api/link_db'
};

// Enable/disable API logging
const API_LOGGING_ENABLED = true;

/**
 * Log API request details
 * @param {string} endpoint - API endpoint
 * @param {string} method - HTTP method
 * @param {*} body - Request body
 */
function logAPIRequest(endpoint, method, body) {
  if (!API_LOGGING_ENABLED) return;
  
  console.group(`🔵 API Request: ${method} ${endpoint}`);
  console.log('Timestamp:', new Date().toISOString());
  console.log('Endpoint:', endpoint);
  console.log('Method:', method);
  
  if (body instanceof FormData) {
    console.log('Body Type: FormData');
    console.log('FormData entries:');
    for (const [key, value] of body.entries()) {
      if (value instanceof File) {
        console.log(`  ${key}: File(${value.name}, ${value.size} bytes, ${value.type})`);
      } else {
        console.log(`  ${key}:`, value);
      }
    }
  } else if (body) {
    console.log('Body:', body);
  }
  
  console.groupEnd();
}

/**
 * Log API response details
 * @param {string} endpoint - API endpoint
 * @param {Response} response - Fetch response object
 * @param {*} data - Response data
 * @param {number} duration - Request duration in ms
 */
function logAPIResponse(endpoint, response, data, duration) {
  if (!API_LOGGING_ENABLED) return;
  
  const isSuccess = response.ok;
  const icon = isSuccess ? '✅' : '❌';
  
  console.group(`${icon} API Response: ${endpoint} (${duration}ms)`);
  console.log('Timestamp:', new Date().toISOString());
  console.log('Status:', response.status, response.statusText);
  console.log('Duration:', `${duration}ms`);
  console.log('Success:', isSuccess);
  
  if (data instanceof Blob) {
    console.log('Response Type: Blob');
    console.log('Blob size:', data.size, 'bytes');
    console.log('Blob type:', data.type);
  } else {
    console.log('Response Data:', data);
  }
  
  console.groupEnd();
}

/**
 * Log API error details
 * @param {string} endpoint - API endpoint
 * @param {Error} error - Error object
 * @param {number} duration - Request duration in ms
 */
function logAPIError(endpoint, error, duration) {
  if (!API_LOGGING_ENABLED) return;
  
  console.group(`❌ API Error: ${endpoint} (${duration}ms)`);
  console.log('Timestamp:', new Date().toISOString());
  console.log('Duration:', `${duration}ms`);
  console.error('Error:', error.message);
  console.error('Stack:', error.stack);
  console.groupEnd();
}

/**
 * Generic API call wrapper with error handling and logging
 * @param {string} endpoint - API endpoint path
 * @param {string} method - HTTP method (GET, POST, etc.)
 * @param {*} body - Request body (FormData, JSON object, etc.)
 * @param {Object} options - Additional fetch options
 * @returns {Promise<*>} Response data
 */
async function callAPI(endpoint, method = 'GET', body = null, options = {}) {
  const startTime = performance.now();
  const url = `${API_BASE}${endpoint}`;
  
  // Prepare fetch options
  const fetchOptions = {
    method,
    ...options
  };
  
  // Add body if provided
  if (body) {
    if (body instanceof FormData) {
      fetchOptions.body = body;
      // Don't set Content-Type for FormData - browser will set it with boundary
    } else if (typeof body === 'object') {
      fetchOptions.headers = {
        'Content-Type': 'application/json',
        ...fetchOptions.headers
      };
      fetchOptions.body = JSON.stringify(body);
    } else {
      fetchOptions.body = body;
    }
  }
  
  // Log request
  logAPIRequest(endpoint, method, body);
  
  try {
    const response = await fetch(url, fetchOptions);
    const duration = Math.round(performance.now() - startTime);
    
    // Handle different response types
    let data;
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else if (contentType && (contentType.includes('application/octet-stream') || 
                                contentType.includes('application/vnd.openxmlformats') ||
                                contentType.includes('text/csv'))) {
      data = await response.blob();
    } else {
      data = await response.text();
    }
    
    // Log response
    logAPIResponse(endpoint, response, data, duration);
    
    // Handle error responses
    if (!response.ok) {
      const errorMessage = typeof data === 'object' && data.error 
        ? data.error 
        : `API request failed with status ${response.status}`;
      
      const error = new Error(errorMessage);
      error.status = response.status;
      error.response = data;
      throw error;
    }
    
    return data;
    
  } catch (error) {
    const duration = Math.round(performance.now() - startTime);
    logAPIError(endpoint, error, duration);
    
    // Enhance error with user-friendly message
    if (error.message.includes('Failed to fetch')) {
      error.userMessage = 'Unable to connect to the server. Please check your internet connection and try again.';
    } else if (error.status === 413) {
      error.userMessage = 'The uploaded files are too large. Please reduce the file size or number of files.';
    } else if (error.status === 400) {
      error.userMessage = error.message || 'Invalid request. Please check your input and try again.';
    } else if (error.status === 500) {
      error.userMessage = 'Server error occurred. Please try again later or contact support.';
    } else {
      error.userMessage = error.message || 'An unexpected error occurred. Please try again.';
    }
    
    throw error;
  }
}

/**
 * Extract answer keys from question paper (AI mode)
 * @param {File} questionPaperFile - Question paper PDF or image
 * @returns {Promise<Object>} Extracted answer keys by set
 */
async function extractAnswerKeys(questionPaperFile) {
  const formData = new FormData();
  formData.append('qp_file', questionPaperFile);
  
  return await callAPI(API_ENDPOINTS.EXTRACT_KEY, 'POST', formData);
}

/**
 * Evaluate batch of OMR sheets
 * @param {File[]} omrFiles - Array of OMR sheet files
 * @param {Object} config - Evaluation configuration
 * @returns {Promise<Object>} Evaluation results
 */
async function evaluateBatch(omrFiles, config) {
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

/**
 * Export results to Excel or CSV format
 * @param {Array} results - Evaluation results
 * @param {string} format - Export format ('excel' or 'csv')
 * @returns {Promise<Blob>} File blob for download
 */
async function exportResults(results, format) {
  const body = {
    results: results,
    format: format,
    mode: appState.currentMode
  };
  
  return await callAPI(API_ENDPOINTS.EXPORT, 'POST', body);
}

/**
 * Link student database to results
 * @param {File} databaseFile - Student database CSV
 * @param {Array} results - Current results
 * @returns {Promise<Object>} Updated results with student names
 */
async function linkStudentDatabase(databaseFile, results) {
  const formData = new FormData();
  formData.append('db_file', databaseFile);
  formData.append('results', JSON.stringify(results));
  
  return await callAPI(API_ENDPOINTS.LINK_DB, 'POST', formData);
}
