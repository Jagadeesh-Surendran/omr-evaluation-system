/**
 * Helper Utilities
 * General utility functions
 */

/**
 * Calculate grade from score
 * @param {number} score - Score percentage
 * @returns {string} Grade letter
 */
function calculateGrade(score) {
  if (score >= GRADE_THRESHOLDS.A) return 'A';
  if (score >= GRADE_THRESHOLDS.B) return 'B';
  if (score >= GRADE_THRESHOLDS.C) return 'C';
  if (score >= GRADE_THRESHOLDS.D) return 'D';
  if (score >= GRADE_THRESHOLDS.E) return 'E';
  return 'F';
}

/**
 * Format timestamp
 * @param {Date} date - Date object
 * @returns {string} Formatted timestamp
 */
function formatTimestamp(date = new Date()) {
  return date.toISOString().replace(/[:.]/g, '-').slice(0, -5);
}

/**
 * Generate unique ID
 * @returns {string} Unique identifier
 */
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * Debounce function
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Deep clone object
 * @param {Object} obj - Object to clone
 * @returns {Object} Cloned object
 */
function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Check if object is empty
 * @param {Object} obj - Object to check
 * @returns {boolean} True if empty
 */
function isEmpty(obj) {
  return Object.keys(obj).length === 0;
}

/**
 * Format file size for display
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Get file extension from filename
 * @param {string} filename - File name
 * @returns {string} File extension
 */
function getFileExtension(filename) {
  return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2).toLowerCase();
}

/**
 * Get file icon class based on file type
 * @param {string} filename - File name
 * @returns {string} Font Awesome icon class
 */
function getFileIcon(filename) {
  const ext = getFileExtension(filename);
  const iconMap = {
    'pdf': 'fas fa-file-pdf',
    'jpg': 'fas fa-file-image',
    'jpeg': 'fas fa-file-image',
    'png': 'fas fa-file-image',
    'csv': 'fas fa-file-csv'
  };
  return iconMap[ext] || 'fas fa-file';
}
