// EvalGenius AI - Main Application JavaScript
// Backend API base URL
const API_BASE = 'http://localhost:5000/api';

// Global state
let currentUser = null;
let currentResults = [];
let currentAnswerKey = null;

// ============================================================================
// NAVIGATION & UI MANAGEMENT
// ============================================================================

function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
        section.classList.add('hidden');
    });
    
    // Show target section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.remove('hidden');
        targetSection.classList.add('active');
    }
}

function showMessage(message, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => messageDiv.remove(), 300);
    }, 3000);
}

// ============================================================================
// AUTHENTICATION (Simplified - Guest Mode)
// ============================================================================

function guestLogin() {
    currentUser = {
        id: 'guest',
        name: 'Guest User',
        email: 'guest@evalgenius.ai'
    };
    
    showMessage('Logged in as Guest', 'success');
    showSection('main-section');
}

// ============================================================================
// FILE UPLOAD HANDLERS
// ============================================================================

function handleOMRUpload(event) {
    const files = event.target.files;
    if (!files || files.length === 0) {
        showMessage('Please select OMR sheet files', 'error');
        return;
    }
    
    const fileList = document.getElementById('omr-file-list');
    fileList.innerHTML = '';
    
    Array.from(files).forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <i class="fas fa-file-image"></i>
            <span>${file.name}</span>
            <span class="file-size">${(file.size / 1024).toFixed(1)} KB</span>
        `;
        fileList.appendChild(fileItem);
    });
    
    showMessage(`${files.length} file(s) selected`, 'success');
}

function handleAnswerKeyUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const fileName = document.getElementById('answer-key-filename');
    if (fileName) {
        fileName.textContent = file.name;
    }
    
    showMessage('Answer key uploaded', 'success');
}

// ============================================================================
// OMR EVALUATION
// ============================================================================

async function evaluateOMR() {
    const omrFiles = document.getElementById('omr-files').files;
    const answerKeyFile = document.getElementById('answer-key-file').files[0];
    
    if (!omrFiles || omrFiles.length === 0) {
        showMessage('Please upload OMR sheet files', 'error');
        return;
    }
    
    if (!answerKeyFile) {
        showMessage('Please upload answer key file', 'error');
        return;
    }
    
    // Show progress
    const progressSection = document.getElementById('progress-section');
    const resultsSection = document.getElementById('results-section');
    
    if (progressSection) {
        progressSection.classList.remove('hidden');
    }
    
    try {
        const formData = new FormData();
        
        // Add OMR files
        Array.from(omrFiles).forEach(file => {
            formData.append('omr_files', file);
        });
        
        // Add answer key
        formData.append('answer_key_csv', answerKeyFile);
        
        // Add number of options (default 5)
        formData.append('num_options', '5');
        
        // Update progress
        updateProgress(0, omrFiles.length, 'Starting evaluation...');
        
        // Call API
        const response = await fetch(`${API_BASE}/evaluate`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Evaluation failed');
        }
        
        const results = await response.json();
        
        // Update progress
        updateProgress(omrFiles.length, omrFiles.length, 'Evaluation complete!');
        
        // Store results
        currentResults = results.students || [];
        
        // Show results
        setTimeout(() => {
            if (progressSection) {
                progressSection.classList.add('hidden');
            }
            displayResults(results);
            if (resultsSection) {
                resultsSection.classList.remove('hidden');
            }
        }, 1000);
        
        showMessage('Evaluation completed successfully!', 'success');
        
    } catch (error) {
        console.error('Evaluation error:', error);
        showMessage(`Evaluation failed: ${error.message}`, 'error');
        
        if (progressSection) {
            progressSection.classList.add('hidden');
        }
    }
}

function updateProgress(current, total, message) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const progressMessage = document.getElementById('progress-message');
    
    const percentage = Math.round((current / total) * 100);
    
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
    }
    
    if (progressText) {
        progressText.textContent = `${current} / ${total} sheets processed`;
    }
    
    if (progressMessage) {
        progressMessage.textContent = message;
    }
}

// ============================================================================
// RESULTS DISPLAY
// ============================================================================

function displayResults(results) {
    // Update statistics
    document.getElementById('total-students').textContent = results.total_processed || 0;
    document.getElementById('average-score').textContent = `${results.average_score || 0}%`;
    document.getElementById('highest-score').textContent = `${results.highest_score || 0}%`;
    
    // Display insights
    const insightsContainer = document.getElementById('insights-container');
    if (insightsContainer && results.insights) {
        insightsContainer.innerHTML = results.insights.map(insight => `
            <div class="insight-item">
                <i class="fas fa-lightbulb"></i>
                <p>${insight}</p>
            </div>
        `).join('');
    }
    
    // Display student results
    const resultsTable = document.getElementById('results-table-body');
    if (resultsTable && results.students) {
        resultsTable.innerHTML = results.students.map((student, index) => `
            <tr>
                <td>${index + 1}</td>
                <td>${student.student_id || student.id}</td>
                <td>${student.name || 'Student ' + (index + 1)}</td>
                <td><span class="score-badge">${student.score}%</span></td>
                <td>
                    <button class="btn-small" onclick="viewDetails(${index})">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `).join('');
    }
}

function viewDetails(studentIndex) {
    const student = currentResults[studentIndex];
    if (!student) return;
    
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Student Details: ${student.name || student.student_id}</h3>
                <button class="close-btn" onclick="this.closest('.modal').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="student-info">
                    <p><strong>ID:</strong> ${student.student_id || student.id}</p>
                    <p><strong>Score:</strong> ${student.score}%</p>
                    <p><strong>Form Type:</strong> ${student.form_type || 'N/A'}</p>
                </div>
                <h4>Question-wise Analysis</h4>
                <div class="questions-grid">
                    ${(student.question_details || []).map(q => `
                        <div class="question-card ${q.is_correct ? 'correct' : 'incorrect'}">
                            <div class="question-number">Q${q.question_number}</div>
                            <div class="question-answer">
                                <span>Marked: ${q.marked_answer}</span>
                                <span>Correct: ${q.correct_answer}</span>
                            </div>
                            <i class="fas fa-${q.is_correct ? 'check-circle' : 'times-circle'}"></i>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    setTimeout(() => modal.classList.add('active'), 10);
}

// ============================================================================
// EXPORT FUNCTIONALITY
// ============================================================================

function exportResults(format) {
    if (!currentResults || currentResults.length === 0) {
        showMessage('No results to export', 'error');
        return;
    }
    
    if (format === 'csv') {
        exportCSV();
    } else if (format === 'excel') {
        exportExcel();
    } else if (format === 'pdf') {
        showMessage('PDF export coming soon', 'info');
    }
}

function exportCSV() {
    const headers = ['Student ID', 'Name', 'Score', 'Form Type'];
    const rows = currentResults.map(student => [
        student.student_id || student.id,
        student.name || '',
        student.score,
        student.form_type || ''
    ]);
    
    let csv = headers.join(',') + '\n';
    rows.forEach(row => {
        csv += row.join(',') + '\n';
    });
    
    downloadFile(csv, 'results.csv', 'text/csv');
    showMessage('CSV exported successfully', 'success');
}

function exportExcel() {
    showMessage('Excel export requires additional library', 'info');
}

function downloadFile(content, filename, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
}

// ============================================================================
// AI ANSWER KEY EXTRACTION
// ============================================================================

async function extractAnswerKey() {
    const fileInput = document.getElementById('question-paper-file');
    const file = fileInput?.files[0];
    
    if (!file) {
        showMessage('Please upload a question paper image', 'error');
        return;
    }
    
    const extractBtn = document.getElementById('extract-btn');
    if (extractBtn) {
        extractBtn.disabled = true;
        extractBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Extracting...';
    }
    
    try {
        const formData = new FormData();
        formData.append('qp_file', file);
        
        const response = await fetch(`${API_BASE}/extract_key`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Extraction failed');
        }
        
        // Display extracted answer key
        displayExtractedKey(result.answer_key);
        showMessage(`Extracted ${result.count} answers successfully!`, 'success');
        
    } catch (error) {
        console.error('Extraction error:', error);
        showMessage(`Extraction failed: ${error.message}`, 'error');
    } finally {
        if (extractBtn) {
            extractBtn.disabled = false;
            extractBtn.innerHTML = '<i class="fas fa-magic"></i> Extract Answer Key';
        }
    }
}

function displayExtractedKey(answerKey) {
    const container = document.getElementById('extracted-key-container');
    if (!container) return;
    
    container.innerHTML = `
        <h4>Extracted Answer Key</h4>
        <div class="answer-key-grid">
            ${Object.entries(answerKey).map(([q, ans]) => `
                <div class="answer-item">
                    <span class="question-num">Q${q}</span>
                    <span class="answer-value">${ans}</span>
                </div>
            `).join('')}
        </div>
        <button class="btn btn-primary" onclick="downloadAnswerKey()">
            <i class="fas fa-download"></i> Download as CSV
        </button>
    `;
    
    container.classList.remove('hidden');
    currentAnswerKey = answerKey;
}

function downloadAnswerKey() {
    if (!currentAnswerKey) return;
    
    let csv = 'Question,Answer\n';
    Object.entries(currentAnswerKey).forEach(([q, ans]) => {
        csv += `${q},${ans}\n`;
    });
    
    downloadFile(csv, 'answer_key.csv', 'text/csv');
    showMessage('Answer key downloaded', 'success');
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('EvalGenius AI - Application loaded');
    
    // Set up event listeners
    setupEventListeners();
    
    // Show welcome section
    showSection('welcome-section');
});

function setupEventListeners() {
    // Guest login button
    const guestBtn = document.getElementById('guest-btn');
    if (guestBtn) {
        guestBtn.addEventListener('click', guestLogin);
    }
    
    // Get started button
    const getStartedBtn = document.querySelector('.btn-get-started');
    if (getStartedBtn) {
        getStartedBtn.addEventListener('click', () => showSection('auth-section'));
    }
    
    // File upload listeners
    const omrFilesInput = document.getElementById('omr-files');
    if (omrFilesInput) {
        omrFilesInput.addEventListener('change', handleOMRUpload);
    }
    
    const answerKeyInput = document.getElementById('answer-key-file');
    if (answerKeyInput) {
        answerKeyInput.addEventListener('change', handleAnswerKeyUpload);
    }
    
    // Evaluate button
    const evaluateBtn = document.getElementById('evaluate-btn');
    if (evaluateBtn) {
        evaluateBtn.addEventListener('click', evaluateOMR);
    }
    
    // Extract button
    const extractBtn = document.getElementById('extract-btn');
    if (extractBtn) {
        extractBtn.addEventListener('click', extractAnswerKey);
    }
}

// Make functions globally available
window.showSection = showSection;
window.guestLogin = guestLogin;
window.evaluateOMR = evaluateOMR;
window.viewDetails = viewDetails;
window.exportResults = exportResults;
window.extractAnswerKey = extractAnswerKey;
window.downloadAnswerKey = downloadAnswerKey;
