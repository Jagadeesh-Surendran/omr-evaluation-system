/**
 * Export Component
 * Handles result export functionality
 */

/**
 * Export results to CSV
 * @param {Array} students - Student results
 */
function exportCSV(students) {
  try {
    const isAIMode = appState.currentMode === EVALUATION_MODES.AI;
    
    // Build CSV headers
    const headers = ['#', 'Student ID', 'Name', 'Score', 'Grade'];
    if (isAIMode) {
      headers.push('Set');
    }
    headers.push('Status', 'Filename');
    
    // Build CSV rows
    const rows = students.map((student, index) => {
      const row = [
        index + 1,
        student.student_id || student.id || '',
        student.name || '',
        student.score || 0,
        calculateGrade(student.score || 0)
      ];
      
      if (isAIMode) {
        row.push(student.form_type || 'UNKNOWN');
      }
      
      row.push(
        (student.score || 0) >= 50 ? 'PASS' : 'FAIL',
        student.filename || ''
      );
      
      return row;
    });
    
    // Generate CSV content
    let csv = headers.join(',') + '\n';
    rows.forEach(row => {
      csv += row.map(cell => `"${cell}"`).join(',') + '\n';
    });
    
    // Add summary section for AI mode
    if (isAIMode) {
      csv += '\n\n';
      csv += 'Set Distribution Summary\n';
      csv += 'Set,Count,Average Score\n';
      
      const setStats = calculateSetStatistics(students);
      Object.entries(setStats).sort().forEach(([set, stats]) => {
        csv += `"${set}",${stats.count},${stats.average.toFixed(1)}\n`;
      });
    }
    
    // Download file
    const timestamp = formatTimestamp();
    const filename = `evalgenius_results_${timestamp}.csv`;
    downloadFile(csv, filename, 'text/csv');
    
    showToast('CSV exported successfully', TOAST_TYPES.SUCCESS);
  } catch (error) {
    console.error('CSV export error:', error);
    showToast(`CSV export failed: ${error.message}`, TOAST_TYPES.ERROR);
  }
}

/**
 * Export results to Excel
 * @param {Array} students - Student results
 */
async function exportExcel(students) {
  try {
    // Show loading state
    showToast('Generating Excel file...', TOAST_TYPES.INFO);
    
    // Call API to generate Excel file
    const blob = await exportResults(students, 'excel');
    
    // Generate filename with timestamp
    const timestamp = formatTimestamp();
    const filename = `evalgenius_results_${timestamp}.xlsx`;
    
    // Download the file
    downloadBlob(blob, filename);
    
    showToast('Excel exported successfully', TOAST_TYPES.SUCCESS);
  } catch (error) {
    console.error('Excel export error:', error);
    showToast(`Excel export failed: ${error.userMessage || error.message}`, TOAST_TYPES.ERROR);
  }
}

/**
 * Calculate statistics per set (AI mode)
 * @param {Array} students - Student results
 * @returns {Object} Set statistics
 */
function calculateSetStatistics(students) {
  const setStats = {};
  
  students.forEach(student => {
    const set = student.form_type || 'UNKNOWN';
    
    if (!setStats[set]) {
      setStats[set] = {
        count: 0,
        totalScore: 0,
        average: 0
      };
    }
    
    setStats[set].count++;
    setStats[set].totalScore += (student.score || 0);
  });
  
  // Calculate averages
  Object.keys(setStats).forEach(set => {
    setStats[set].average = setStats[set].totalScore / setStats[set].count;
  });
  
  return setStats;
}

/**
 * Download answer key as CSV (for AI mode review)
 * @param {string} set - Set label (A, B, C, D)
 */
function downloadAnswerKeyCSV(set) {
  try {
    const answerKey = appState.answerKeys.ai[set];
    
    if (!answerKey || Object.keys(answerKey).length === 0) {
      showToast(`No answer key found for Set ${set}`, TOAST_TYPES.WARNING);
      return;
    }
    
    // Build CSV content
    let csv = 'Question,Answer\n';
    
    // Sort questions numerically
    const questions = Object.keys(answerKey).sort((a, b) => parseInt(a) - parseInt(b));
    
    questions.forEach(question => {
      csv += `${question},${answerKey[question]}\n`;
    });
    
    // Download file
    const filename = `answer_key_set_${set}.csv`;
    downloadFile(csv, filename, 'text/csv');
    
    showToast(`Answer key for Set ${set} downloaded`, TOAST_TYPES.SUCCESS);
  } catch (error) {
    console.error('Answer key download error:', error);
    showToast(`Download failed: ${error.message}`, TOAST_TYPES.ERROR);
  }
}
