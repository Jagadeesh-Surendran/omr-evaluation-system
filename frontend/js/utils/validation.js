/**
 * Validation Utilities
 * File and data validation functions
 */

/**
 * Validate file type
 * @param {File} file - File to validate
 * @param {string} fileType - Type category (OMR, ANSWER_KEY, QUESTION_PAPER)
 * @returns {boolean} True if valid
 */
function validateFileType(file, fileType) {
  const acceptedTypes = ACCEPTED_FILE_TYPES[fileType];
  return acceptedTypes.includes(file.type);
}

/**
 * Validate file size
 * @param {File} file - File to validate
 * @returns {boolean} True if valid
 */
function validateFileSize(file) {
  return file.size <= FILE_LIMITS.MAX_FILE_SIZE;
}

/**
 * Validate batch size
 * @param {File[]} files - Array of files
 * @returns {boolean} True if valid
 */
function validateBatchSize(files) {
  const totalSize = files.reduce((sum, file) => sum + file.size, 0);
  return totalSize <= FILE_LIMITS.MAX_BATCH_SIZE;
}

/**
 * Validate file count
 * @param {File[]} files - Array of files
 * @returns {boolean} True if valid
 */
function validateFileCount(files) {
  return files.length <= FILE_LIMITS.MAX_FILES;
}

/**
 * Format file size for display
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted size string
 */
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
