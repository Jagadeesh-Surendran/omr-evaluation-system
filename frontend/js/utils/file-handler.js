/**
 * File Handler Utilities
 * File upload and processing functions
 */

/**
 * Handle file upload
 * @param {FileList} files - Files to upload
 * @param {string} fileType - Type category
 * @returns {Promise<boolean>} Success status
 */
async function handleFileUpload(files, fileType) {
  const fileArray = Array.from(files);
  
  // Validate file count
  if (fileType === 'OMR' && !validateFileCount(fileArray)) {
    showToast(`Maximum ${FILE_LIMITS.MAX_FILES} files allowed`, TOAST_TYPES.ERROR);
    return false;
  }
  
  // Validate file types
  for (const file of fileArray) {
    if (!validateFileType(file, fileType)) {
      showToast(`Invalid file type: ${file.name}`, TOAST_TYPES.ERROR);
      return false;
    }
    
    if (!validateFileSize(file)) {
      showToast(`File too large: ${file.name} (max 20MB)`, TOAST_TYPES.ERROR);
      return false;
    }
  }
  
  // Validate batch size
  if (!validateBatchSize(fileArray)) {
    showToast('Total upload size exceeds 100MB', TOAST_TYPES.ERROR);
    return false;
  }
  
  return true;
}

/**
 * Read file as text
 * @param {File} file - File to read
 * @returns {Promise<string>} File content
 */
function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = (e) => reject(e);
    reader.readAsText(file);
  });
}

/**
 * Download file
 * @param {string} content - File content
 * @param {string} filename - File name
 * @param {string} mimeType - MIME type
 */
function downloadFile(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  downloadBlob(blob, filename);
}

/**
 * Download blob
 * @param {Blob} blob - Blob to download
 * @param {string} filename - File name
 */
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
