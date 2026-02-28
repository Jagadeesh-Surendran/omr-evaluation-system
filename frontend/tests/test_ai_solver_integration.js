/**
 * Frontend Integration Tests for AI Question Solver
 * 
 * These tests validate the complete frontend workflow including:
 * - File upload and session creation
 * - WebSocket connection and progress updates
 * - Pause/resume/cancel controls
 * - Answer correction and note addition
 * - Filtering and sorting
 * - Approval workflow
 * - Export functionality
 * 
 * Requirements: Backend server running on http://localhost:5000
 */

const BACKEND_BASE = 'http://localhost:5000';
const TEST_TIMEOUT = 30000; // 30 seconds

// Test utilities
class TestRunner {
    constructor() {
        this.tests = [];
        this.results = [];
    }

    test(name, fn) {
        this.tests.push({ name, fn });
    }

    async run() {
        console.log(`Running ${this.tests.length} tests...`);
        
        for (const test of this.tests) {
            try {
                console.log(`\n▶ ${test.name}`);
                await test.fn();
                this.results.push({ name: test.name, status: 'PASS' });
                console.log(`✓ ${test.name} PASSED`);
            } catch (error) {
                this.results.push({ name: test.name, status: 'FAIL', error: error.message });
                console.error(`✗ ${test.name} FAILED:`, error.message);
            }
        }

        this.printSummary();
    }

    printSummary() {
        const passed = this.results.filter(r => r.status === 'PASS').length;
        const failed = this.results.filter(r => r.status === 'FAIL').length;
        
        console.log('\n' + '='.repeat(50));
        console.log(`Test Results: ${passed} passed, ${failed} failed`);
        console.log('='.repeat(50));
        
        if (failed > 0) {
            console.log('\nFailed Tests:');
            this.results.filter(r => r.status === 'FAIL').forEach(r => {
                console.log(`  ✗ ${r.name}: ${r.error}`);
            });
        }
    }
}

// Assertion helpers
function assert(condition, message) {
    if (!condition) {
        throw new Error(message || 'Assertion failed');
    }
}

function assertEquals(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(message || `Expected ${expected}, got ${actual}`);
    }
}

function assertNotNull(value, message) {
    if (value === null || value === undefined) {
        throw new Error(message || 'Value is null or undefined');
    }
}

// Test fixtures
async function createTestPDF() {
    // Create a simple test PDF blob
    const pdfContent = '%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n190\n%%EOF';
    return new Blob([pdfContent], { type: 'application/pdf' });
}

async function uploadTestPDF() {
    const formData = new FormData();
    const pdfBlob = await createTestPDF();
    formData.append('pdf_file', pdfBlob, 'test_questions.pdf');

    const response = await fetch(`${BACKEND_BASE}/api/solve/upload`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
    }

    const data = await response.json();
    return data.session_id;
}

async function waitForSessionStatus(sessionId, targetStatus, timeout = TEST_TIMEOUT) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
        const response = await fetch(`${BACKEND_BASE}/api/solve/session/${sessionId}`);
        const data = await response.json();
        
        if (data.status === targetStatus) {
            return data;
        }
        
        if (data.status === 'error') {
            throw new Error('Session entered error state');
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error(`Timeout waiting for status ${targetStatus}`);
}

// Test Suite
const runner = new TestRunner();

// Test 1: File upload and session creation
runner.test('File upload creates session', async () => {
    const sessionId = await uploadTestPDF();
    assertNotNull(sessionId, 'Session ID should not be null');
    assert(sessionId.length > 0, 'Session ID should not be empty');
});

// Test 2: Session status retrieval
runner.test('Session status can be retrieved', async () => {
    const sessionId = await uploadTestPDF();
    
    const response = await fetch(`${BACKEND_BASE}/api/solve/session/${sessionId}`);
    assert(response.ok, 'Session status request should succeed');
    
    const data = await response.json();
    assertNotNull(data.session_id, 'Session data should have session_id');
    assertNotNull(data.status, 'Session data should have status');
});

// Test 3: WebSocket connection
runner.test('WebSocket connection establishes', async () => {
    return new Promise(async (resolve, reject) => {
        const sessionId = await uploadTestPDF();
        
        const ws = new WebSocket(`ws://localhost:5000/api/solve/progress`);
        
        ws.onopen = () => {
            ws.send(JSON.stringify({
                type: 'subscribe_progress',
                session_id: sessionId
            }));
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.session_id === sessionId) {
                ws.close();
                resolve();
            }
        };
        
        ws.onerror = (error) => {
            reject(new Error('WebSocket connection failed'));
        };
        
        setTimeout(() => {
            ws.close();
            reject(new Error('WebSocket connection timeout'));
        }, 5000);
    });
});

// Test 4: Pause session
runner.test('Session can be paused', async () => {
    const sessionId = await uploadTestPDF();
    
    // Wait for processing to start
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const response = await fetch(`${BACKEND_BASE}/api/solve/session/${sessionId}/pause`, {
        method: 'POST'
    });
    
    assert(response.ok, 'Pause request should succeed');
    
    const data = await response.json();
    assert(data.success === true, 'Pause should be successful');
});

// Test 5: Resume session
runner.test('Paused session can be resumed', async () => {
    const sessionId = await uploadTestPDF();
    
    // Pause the session
    await fetch(`${BACKEND_BASE}/api/solve/session/${sessionId}/pause`, {
        method: 'POST'
    });
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Resume the session
    const response = await fetch(`${BACKEND_BASE}/api/solve/session/${sessionId}/resume`, {
        method: 'POST'
    });
    
    assert(response.ok, 'Resume request should succeed');
    
    const data = await response.json();
    assert(data.success === true, 'Resume should be successful');
});

// Test 6: Cancel session
runner.test('Session can be cancelled', async () => {
    const sessionId = await uploadTestPDF();
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const response = await fetch(`${BACKEND_BASE}/api/solve/session/${sessionId}/cancel`, {
        method: 'POST'
    });
    
    assert(response.ok, 'Cancel request should succeed');
    
    const data = await response.json();
    assert(data.success === true, 'Cancel should be successful');
});

// Test 7: Answer correction
runner.test('Answer can be corrected', async () => {
    const sessionId = await uploadTestPDF();
    
    // Wait for at least one question to be processed
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    const questionNumber = 1;
    const newAnswer = 'B';
    
    const response = await fetch(
        `${BACKEND_BASE}/api/solve/session/${sessionId}/answer/${questionNumber}`,
        {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answer: newAnswer })
        }
    );
    
    assert(response.ok, 'Answer correction should succeed');
    
    const data = await response.json();
    assert(data.success === true, 'Answer correction should be successful');
});

// Test 8: Note addition
runner.test('Note can be added to question', async () => {
    const sessionId = await uploadTestPDF();
    
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    const questionNumber = 1;
    const note = 'Test note for question 1';
    
    const response = await fetch(
        `${BACKEND_BASE}/api/solve/session/${sessionId}/note/${questionNumber}`,
        {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ note: note })
        }
    );
    
    assert(response.ok, 'Note addition should succeed');
    
    const data = await response.json();
    assert(data.success === true, 'Note addition should be successful');
});

// Test 9: Export JSON
runner.test('Answer key can be exported as JSON', async () => {
    const sessionId = await uploadTestPDF();
    
    // Wait for session to complete
    await waitForSessionStatus(sessionId, 'completed');
    
    const response = await fetch(
        `${BACKEND_BASE}/api/solve/session/${sessionId}/export?format=json`
    );
    
    assert(response.ok, 'JSON export should succeed');
    
    const data = await response.json();
    assertNotNull(data.answer_key, 'Export should contain answer_key');
    assertNotNull(data.metadata, 'Export should contain metadata');
});

// Test 10: Export CSV
runner.test('Answer key can be exported as CSV', async () => {
    const sessionId = await uploadTestPDF();
    
    await waitForSessionStatus(sessionId, 'completed');
    
    const response = await fetch(
        `${BACKEND_BASE}/api/solve/session/${sessionId}/export?format=csv`
    );
    
    assert(response.ok, 'CSV export should succeed');
    assert(response.headers.get('content-type').includes('text/csv'), 'Response should be CSV');
    
    const csvContent = await response.text();
    assert(csvContent.length > 0, 'CSV content should not be empty');
    assert(csvContent.includes('question_number'), 'CSV should have header row');
});

// Test 11: Export PDF
runner.test('Answer key can be exported as PDF', async () => {
    const sessionId = await uploadTestPDF();
    
    await waitForSessionStatus(sessionId, 'completed');
    
    const response = await fetch(
        `${BACKEND_BASE}/api/solve/session/${sessionId}/export?format=pdf`
    );
    
    assert(response.ok, 'PDF export should succeed');
    
    const pdfContent = await response.text();
    assert(pdfContent.length > 0, 'PDF content should not be empty');
});

// Test 12: Use for evaluation
runner.test('Answer key can be used for OMR evaluation', async () => {
    const sessionId = await uploadTestPDF();
    
    await waitForSessionStatus(sessionId, 'completed');
    
    const response = await fetch(
        `${BACKEND_BASE}/api/solve/session/${sessionId}/use-for-evaluation`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        }
    );
    
    assert(response.ok, 'Use for evaluation should succeed');
    
    const data = await response.json();
    assert(data.success === true, 'Use for evaluation should be successful');
    assertNotNull(data.answer_key, 'Response should contain answer_key');
});

// Test 13: Approval workflow
runner.test('Answer key can be approved', async () => {
    const sessionId = await uploadTestPDF();
    
    await waitForSessionStatus(sessionId, 'completed');
    
    const response = await fetch(
        `${BACKEND_BASE}/api/solve/session/${sessionId}/approve`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: 'test_admin' })
        }
    );
    
    assert(response.ok, 'Approval should succeed');
    
    const data = await response.json();
    assert(data.success === true, 'Approval should be successful');
    assertNotNull(data.approved_by, 'Response should contain approved_by');
    assertNotNull(data.approved_at, 'Response should contain approved_at');
});

// Test 14: Filtering questions
runner.test('Questions can be filtered by criteria', async () => {
    // This is a UI test that would need to be run in browser context
    // For now, we'll test the data structure
    const sessionId = await uploadTestPDF();
    await waitForSessionStatus(sessionId, 'completed');
    
    const response = await fetch(`${BACKEND_BASE}/api/solve/session/${sessionId}`);
    const data = await response.json();
    
    assertNotNull(data.questions, 'Session should have questions');
    assertNotNull(data.results, 'Session should have results');
    assertNotNull(data.validation_report, 'Session should have validation_report');
});

// Test 15: Sorting questions
runner.test('Questions can be sorted by different criteria', async () => {
    // This is a UI test that would need to be run in browser context
    // For now, we'll verify the data is sortable
    const sessionId = await uploadTestPDF();
    await waitForSessionStatus(sessionId, 'completed');
    
    const response = await fetch(`${BACKEND_BASE}/api/solve/session/${sessionId}`);
    const data = await response.json();
    
    if (data.questions && data.questions.length > 0) {
        const question = data.questions[0];
        assertNotNull(question.number, 'Question should have number for sorting');
        assertNotNull(question.question_type, 'Question should have type for sorting');
    }
    
    if (data.results) {
        const resultKeys = Object.keys(data.results);
        if (resultKeys.length > 0) {
            const result = data.results[resultKeys[0]];
            assertNotNull(result.confidence, 'Result should have confidence for sorting');
        }
    }
});

// Export for use in test runner
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { runner, TestRunner };
}

// Auto-run if in browser
if (typeof window !== 'undefined') {
    window.runTests = () => runner.run();
}
