/**
 * CSV Parser Utilities
 * CSV parsing and validation functions
 */

/**
 * Parse and validate answer key CSV
 * @param {string} csvContent - CSV file content
 * @returns {Object} Validation result with answer key or errors
 */
function parseAnswerKeyCSV(csvContent) {
  const lines = csvContent.split('\n').filter(line => line.trim());
  const answerKey = {};
  const errors = [];
  const duplicates = new Set();
  
  lines.forEach((line, index) => {
    // Skip header if present
    if (index === 0 && line.toLowerCase().includes('question')) {
      return;
    }
    
    const [question, answer] = line.split(',').map(s => s.trim());
    
    // Validate question number
    if (!question || isNaN(question) || parseInt(question) <= 0) {
      errors.push(`Invalid question number at line ${index + 1}`);
      return;
    }
    
    // Validate answer option
    if (!answer || !/^[A-E]$/i.test(answer)) {
      errors.push(`Invalid answer option at line ${index + 1}: "${answer}"`);
      return;
    }
    
    // Check for duplicates
    if (answerKey[question]) {
      duplicates.add(question);
      errors.push(`Duplicate question ${question}`);
    }
    
    answerKey[question] = answer.toUpperCase();
  });
  
  return {
    valid: errors.length === 0,
    answerKey,
    errors,
    questionCount: Object.keys(answerKey).length
  };
}

/**
 * Generate CSV from answer key
 * @param {Object} answerKey - Answer key object
 * @returns {string} CSV content
 */
function generateAnswerKeyCSV(answerKey) {
  let csv = 'Question,Answer\n';
  
  const questions = Object.keys(answerKey).sort((a, b) => parseInt(a) - parseInt(b));
  questions.forEach(q => {
    csv += `${q},${answerKey[q]}\n`;
  });
  
  return csv;
}

/**
 * Validate CSV format
 * @param {File} file - CSV file
 * @returns {Promise<Object>} Validation result
 */
async function validateAnswerKeyCSV(file) {
  try {
    const content = await readFileAsText(file);
    return parseAnswerKeyCSV(content);
  } catch (error) {
    return {
      valid: false,
      answerKey: {},
      errors: ['Failed to read CSV file'],
      questionCount: 0
    };
  }
}
