/**
 * Results View Component
 * Renders the evaluation results screen
 */

/**
 * Render results view screen
 * @returns {string} HTML content
 */
function renderResultsView() {
  const results = appState.results;
  const isAIMode = appState.currentMode === EVALUATION_MODES.AI;
  
  return `
    <div class="results-container">
      <div class="results-header">
        <button class="btn-ghost" onclick="newEvaluation()">
          <i class="fas fa-arrow-left"></i> New Evaluation
        </button>
        <h2>Evaluation Results</h2>
        <div class="export-buttons">
          <button class="btn-outline" onclick="exportCSV(appState.results.students)">
            <i class="fas fa-download"></i> Export CSV
          </button>
          <button class="btn-primary" onclick="exportExcel(appState.results.students)">
            <i class="fas fa-file-excel"></i> Export Excel
          </button>
        </div>
      </div>
      
      <!-- Statistics Cards -->
      <div class="stats-grid">
        ${renderStatisticsCards(results)}
      </div>
      
      <!-- Set Distribution (AI mode only) -->
      ${isAIMode ? renderSetDistribution(results) : ''}
      
      <!-- AI Insights -->
      ${renderInsightsPanel(results)}
      
      <!-- Results Table -->
      <div class="results-table-container">
        <div class="table-controls">
          <div class="search-box">
            <i class="fas fa-search"></i>
            <input type="text" id="search-input" placeholder="Search by name or ID..." 
                   oninput="handleSearchInput(event)" value="${appState.filters.searchTerm}">
          </div>
          ${isAIMode ? renderSetFilter() : ''}
        </div>
        
        <div class="table-wrapper">
          <table class="results-table">
            <thead>
              <tr>
                <th onclick="sortResults('index')"># ${getSortIcon('index')}</th>
                <th onclick="sortResults('student_id')">Student ID ${getSortIcon('student_id')}</th>
                <th onclick="sortResults('name')">Name ${getSortIcon('name')}</th>
                <th onclick="sortResults('score')">Score ${getSortIcon('score')}</th>
                <th onclick="sortResults('grade')">Grade ${getSortIcon('grade')}</th>
                ${isAIMode ? `<th onclick="sortResults('form_type')">Set ${getSortIcon('form_type')}</th>` : ''}
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="results-table-body">
              ${renderResultsTableRows(getFilteredStudents())}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

/**
 * Render statistics cards
 * @param {Object} results - Results object
 * @returns {string} HTML content
 */
function renderStatisticsCards(results) {
  const stats = results.statistics || {};
  const totalStudents = results.students.length;
  const averageScore = totalStudents > 0 
    ? (results.students.reduce((sum, s) => sum + (s.score || 0), 0) / totalStudents).toFixed(1)
    : 0;
  const highestScore = totalStudents > 0
    ? Math.max(...results.students.map(s => s.score || 0))
    : 0;
  const processingTime = stats.processingTime || stats.processing_time || 0;
  
  return `
    <div class="stat-card">
      <div class="stat-icon" style="background: var(--color-primary-light);">
        <i class="fas fa-users" style="color: var(--color-primary);"></i>
      </div>
      <div class="stat-content">
        <div class="stat-label">Total Students</div>
        <div class="stat-value">${totalStudents}</div>
      </div>
    </div>
    
    <div class="stat-card">
      <div class="stat-icon" style="background: var(--color-success-light);">
        <i class="fas fa-chart-line" style="color: var(--color-success);"></i>
      </div>
      <div class="stat-content">
        <div class="stat-label">Average Score</div>
        <div class="stat-value">${averageScore}%</div>
      </div>
    </div>
    
    <div class="stat-card">
      <div class="stat-icon" style="background: var(--color-warning-light);">
        <i class="fas fa-trophy" style="color: var(--color-warning);"></i>
      </div>
      <div class="stat-content">
        <div class="stat-label">Highest Score</div>
        <div class="stat-value">${highestScore}%</div>
      </div>
    </div>
    
    <div class="stat-card">
      <div class="stat-icon" style="background: var(--color-info-light);">
        <i class="fas fa-clock" style="color: var(--color-info);"></i>
      </div>
      <div class="stat-content">
        <div class="stat-label">Processing Time</div>
        <div class="stat-value">${processingTime.toFixed(1)}s</div>
      </div>
    </div>
  `;
}

/**
 * Render set distribution chart (AI mode only)
 * @param {Object} results - Results object
 * @returns {string} HTML content
 */
function renderSetDistribution(results) {
  const students = results.students || [];
  const setDistribution = {};
  const setScores = {};
  
  // Calculate distribution and average scores per set
  students.forEach(student => {
    const set = student.form_type || 'UNKNOWN';
    setDistribution[set] = (setDistribution[set] || 0) + 1;
    
    if (!setScores[set]) {
      setScores[set] = [];
    }
    setScores[set].push(student.score || 0);
  });
  
  const maxCount = Math.max(...Object.values(setDistribution), 1);
  const totalStudents = students.length;
  
  return `
    <div class="set-distribution-panel">
      <h3><i class="fas fa-chart-bar"></i> Set Distribution</h3>
      <div class="distribution-chart">
        ${Object.entries(setDistribution).sort().map(([set, count]) => {
          const percentage = ((count / totalStudents) * 100).toFixed(1);
          const barHeight = (count / maxCount) * 100;
          const avgScore = setScores[set].length > 0
            ? (setScores[set].reduce((a, b) => a + b, 0) / setScores[set].length).toFixed(1)
            : 0;
          const color = SET_COLORS[set] || SET_COLORS.UNKNOWN;
          
          return `
            <div class="distribution-bar-container">
              <div class="distribution-bar" data-set="${set}">
                <div class="bar-fill" style="height: ${barHeight}%; background: ${color};"></div>
              </div>
              <div class="bar-info">
                <span class="bar-label">Set ${set}</span>
                <span class="bar-value">${count} (${percentage}%)</span>
                <span class="bar-avg">Avg: ${avgScore}%</span>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;
}

/**
 * Render AI insights panel
 * @param {Object} results - Results object
 * @returns {string} HTML content
 */
function renderInsightsPanel(results) {
  const insights = results.insights || [];
  const generatedInsights = generateInsights(results);
  const allInsights = [...insights, ...generatedInsights];
  
  if (allInsights.length === 0) {
    return '';
  }
  
  return `
    <div class="insights-panel">
      <h3><i class="fas fa-lightbulb"></i> Insights</h3>
      <div class="insights-grid">
        ${allInsights.map(insight => `
          <div class="insight-item">
            <i class="fas fa-check-circle"></i>
            <p>${insight}</p>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

/**
 * Generate client-side insights
 * @param {Object} results - Results object
 * @returns {Array<string>} Array of insight strings
 */
function generateInsights(results) {
  const insights = [];
  const students = results.students || [];
  
  if (students.length === 0) return insights;
  
  const averageScore = students.reduce((sum, s) => sum + (s.score || 0), 0) / students.length;
  const passCount = students.filter(s => (s.score || 0) >= 50).length;
  const passRate = (passCount / students.length) * 100;
  
  // Average score insight
  if (averageScore >= 75) {
    insights.push(`Excellent performance! Average score is ${averageScore.toFixed(1)}%`);
  } else if (averageScore >= 60) {
    insights.push(`Good performance with average score of ${averageScore.toFixed(1)}%`);
  } else if (averageScore < 50) {
    insights.push(`Average score is ${averageScore.toFixed(1)}%. Consider reviewing the material.`);
  }
  
  // Pass rate insight
  if (passRate === 100) {
    insights.push('All students passed! 🎉');
  } else if (passRate >= 90) {
    insights.push(`${passRate.toFixed(0)}% pass rate - excellent results!`);
  } else if (passRate < 50) {
    insights.push(`Only ${passRate.toFixed(0)}% passed. Review may be needed.`);
  }
  
  // Unknown set warning (AI mode)
  if (appState.currentMode === EVALUATION_MODES.AI) {
    const unknownCount = students.filter(s => s.form_type === 'UNKNOWN').length;
    if (unknownCount > 0) {
      const unknownPercent = (unknownCount / students.length) * 100;
      if (unknownPercent > 10) {
        insights.push(`⚠️ ${unknownCount} sheets (${unknownPercent.toFixed(0)}%) have unknown set detection`);
      }
    }
  }
  
  return insights;
}

/**
 * Render set filter dropdown (AI mode only)
 * @returns {string} HTML content
 */
function renderSetFilter() {
  const students = appState.results.students || [];
  const sets = new Set(students.map(s => s.form_type || 'UNKNOWN'));
  const sortedSets = Array.from(sets).sort();
  
  return `
    <div class="filter-group">
      <label for="set-filter">Filter by Set:</label>
      <select id="set-filter" onchange="handleSetFilter(event)">
        <option value="all" ${appState.filters.set === 'all' ? 'selected' : ''}>All Sets</option>
        ${sortedSets.map(set => `
          <option value="${set}" ${appState.filters.set === set ? 'selected' : ''}>
            Set ${set}
          </option>
        `).join('')}
      </select>
    </div>
  `;
}

/**
 * Render results table rows
 * @param {Array} students - Filtered student results
 * @returns {string} HTML content
 */
function renderResultsTableRows(students) {
  if (students.length === 0) {
    return `
      <tr>
        <td colspan="8" style="text-align: center; padding: var(--spacing-xl);">
          <i class="fas fa-inbox" style="font-size: 48px; color: var(--color-text-light); margin-bottom: var(--spacing-md);"></i>
          <p style="color: var(--color-text-light);">No results found</p>
        </td>
      </tr>
    `;
  }
  
  const isAIMode = appState.currentMode === EVALUATION_MODES.AI;
  
  return students.map((student, index) => {
    const grade = calculateGrade(student.score || 0);
    const status = (student.score || 0) >= 50 ? 'pass' : 'fail';
    const isUnknownSet = student.form_type === 'UNKNOWN';
    const rowClass = isUnknownSet ? 'warning-row' : '';
    
    return `
      <tr class="${rowClass}">
        <td>${index + 1}</td>
        <td>${student.student_id || student.id || '-'}</td>
        <td>${student.name || 'Student ' + (index + 1)}</td>
        <td><span class="score-badge">${student.score || 0}%</span></td>
        <td><span class="grade-badge grade-${grade}">${grade}</span></td>
        ${isAIMode ? `
          <td>
            <span class="set-badge ${isUnknownSet ? 'set-unknown' : ''}" 
                  style="background: ${SET_COLORS[student.form_type] || SET_COLORS.UNKNOWN}20; 
                         color: ${SET_COLORS[student.form_type] || SET_COLORS.UNKNOWN}; 
                         border: 1px solid ${SET_COLORS[student.form_type] || SET_COLORS.UNKNOWN};">
              ${isUnknownSet ? '<i class="fas fa-exclamation-triangle"></i> ' : ''}Set ${student.form_type || 'UNKNOWN'}
            </span>
          </td>
        ` : ''}
        <td><span class="status-badge status-${status}">${status.toUpperCase()}</span></td>
        <td>
          <button class="btn-icon" onclick="viewStudentDetails(${index})" title="View Details">
            <i class="fas fa-eye"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * Get filtered students based on current filters
 * @returns {Array} Filtered student array
 */
function getFilteredStudents() {
  let students = [...appState.results.students];
  const filters = appState.filters;
  
  // Apply search filter
  if (filters.searchTerm) {
    const term = filters.searchTerm.toLowerCase();
    students = students.filter(s => {
      const name = (s.name || '').toLowerCase();
      const id = (s.student_id || s.id || '').toString().toLowerCase();
      return name.includes(term) || id.includes(term);
    });
  }
  
  // Apply set filter (AI mode only)
  if (appState.currentMode === EVALUATION_MODES.AI && filters.set !== 'all') {
    students = students.filter(s => (s.form_type || 'UNKNOWN') === filters.set);
  }
  
  // Apply sorting
  if (filters.sortBy) {
    students.sort((a, b) => {
      let aVal, bVal;
      
      switch (filters.sortBy) {
        case 'index':
          return filters.sortOrder === 'asc' ? 0 : 0; // Keep original order
        case 'student_id':
          aVal = a.student_id || a.id || '';
          bVal = b.student_id || b.id || '';
          break;
        case 'name':
          aVal = a.name || '';
          bVal = b.name || '';
          break;
        case 'score':
          aVal = a.score || 0;
          bVal = b.score || 0;
          break;
        case 'grade':
          aVal = calculateGrade(a.score || 0);
          bVal = calculateGrade(b.score || 0);
          break;
        case 'form_type':
          aVal = a.form_type || 'UNKNOWN';
          bVal = b.form_type || 'UNKNOWN';
          break;
        default:
          return 0;
      }
      
      if (typeof aVal === 'number') {
        return filters.sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
      } else {
        const comparison = aVal.toString().localeCompare(bVal.toString());
        return filters.sortOrder === 'asc' ? comparison : -comparison;
      }
    });
  }
  
  return students;
}

/**
 * Get sort icon for column
 * @param {string} column - Column name
 * @returns {string} HTML for sort icon
 */
function getSortIcon(column) {
  if (appState.filters.sortBy !== column) {
    return '<i class="fas fa-sort" style="opacity: 0.3;"></i>';
  }
  
  return appState.filters.sortOrder === 'asc'
    ? '<i class="fas fa-sort-up"></i>'
    : '<i class="fas fa-sort-down"></i>';
}

/**
 * Handle search input
 * @param {Event} event - Input event
 */
function handleSearchInput(event) {
  updateFilters({ searchTerm: event.target.value });
  refreshResultsTable();
}

/**
 * Handle set filter change
 * @param {Event} event - Change event
 */
function handleSetFilter(event) {
  updateFilters({ set: event.target.value });
  refreshResultsTable();
}

/**
 * Sort results by column
 * @param {string} column - Column name
 */
function sortResults(column) {
  const currentSort = appState.filters.sortBy;
  const currentOrder = appState.filters.sortOrder;
  
  // Toggle sort order if same column, otherwise default to ascending
  const newOrder = currentSort === column && currentOrder === 'asc' ? 'desc' : 'asc';
  
  updateFilters({ sortBy: column, sortOrder: newOrder });
  refreshResultsTable();
}

/**
 * Refresh results table without full page re-render
 */
function refreshResultsTable() {
  const tbody = document.getElementById('results-table-body');
  if (tbody) {
    tbody.innerHTML = renderResultsTableRows(getFilteredStudents());
  }
  
  // Update sort icons in headers
  const headers = document.querySelectorAll('.results-table th[onclick]');
  headers.forEach(header => {
    const column = header.getAttribute('onclick').match(/sortResults\('(.+?)'\)/)[1];
    const iconHTML = getSortIcon(column);
    const text = header.textContent.replace(/<i.*<\/i>/, '').trim();
    header.innerHTML = `${text} ${iconHTML}`;
  });
}

/**
 * View student details
 * @param {number} index - Student index in filtered results
 */
function viewStudentDetails(index) {
  const students = getFilteredStudents();
  const student = students[index];
  
  if (!student) {
    showToast('Student not found', TOAST_TYPES.ERROR);
    return;
  }
  
  const grade = calculateGrade(student.score || 0);
  const isAIMode = appState.currentMode === EVALUATION_MODES.AI;
  
  const content = `
    <div class="student-details">
      <div class="detail-row">
        <span class="detail-label">Student ID:</span>
        <span class="detail-value">${student.student_id || student.id || '-'}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Name:</span>
        <span class="detail-value">${student.name || 'Student ' + (index + 1)}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Score:</span>
        <span class="detail-value"><span class="score-badge">${student.score || 0}%</span></span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Grade:</span>
        <span class="detail-value"><span class="grade-badge grade-${grade}">${grade}</span></span>
      </div>
      ${isAIMode ? `
        <div class="detail-row">
          <span class="detail-label">Set:</span>
          <span class="detail-value">
            <span class="set-badge" style="background: ${SET_COLORS[student.form_type] || SET_COLORS.UNKNOWN}20; 
                                           color: ${SET_COLORS[student.form_type] || SET_COLORS.UNKNOWN};">
              Set ${student.form_type || 'UNKNOWN'}
            </span>
          </span>
        </div>
      ` : ''}
      <div class="detail-row">
        <span class="detail-label">Filename:</span>
        <span class="detail-value">${student.filename || '-'}</span>
      </div>
      ${student.correct_count !== undefined ? `
        <div class="detail-row">
          <span class="detail-label">Correct Answers:</span>
          <span class="detail-value" style="color: var(--color-success);">${student.correct_count || 0}</span>
        </div>
      ` : ''}
      ${student.incorrect_count !== undefined ? `
        <div class="detail-row">
          <span class="detail-label">Incorrect Answers:</span>
          <span class="detail-value" style="color: var(--color-error);">${student.incorrect_count || 0}</span>
        </div>
      ` : ''}
      ${student.unanswered_count !== undefined ? `
        <div class="detail-row">
          <span class="detail-label">Unanswered:</span>
          <span class="detail-value" style="color: var(--color-warning);">${student.unanswered_count || 0}</span>
        </div>
      ` : ''}
    </div>
  `;
  
  const modal = createModal({
    title: 'Student Details',
    subtitle: `${student.name || 'Student ' + (index + 1)}`,
    content: content,
    actions: [
      {
        text: 'Close',
        type: 'primary',
        onClick: () => closeModal(modal)
      }
    ]
  });
  
  showModal(modal);
}
