# AI Question Solver API Documentation

## Overview

The AI Question Solver API extends the OMR Evaluation System to automatically generate answer keys from question bank PDFs using AI models. This API provides endpoints for uploading PDFs, managing solver sessions, reviewing and correcting AI-generated answers, and exporting answer keys in multiple formats.

**Base URL**: `/api/solve`

**Authentication**: All endpoints require authentication via session token or API key.

**Authorization**: Answer key approval requires administrator privileges.

## Table of Contents

- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Upload PDF](#upload-pdf)
  - [Get Session Status](#get-session-status)
  - [Pause Session](#pause-session)
  - [Resume Session](#resume-session)
  - [Cancel Session](#cancel-session)
  - [Update Answer](#update-answer)
  - [Add Note](#add-note)
  - [Approve Answer Key](#approve-answer-key)
  - [Export Answer Key](#export-answer-key)
  - [Use for OMR Evaluation](#use-for-omr-evaluation)
  - [WebSocket Progress Updates](#websocket-progress-updates)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limits](#rate-limits)

---

## Authentication

All API endpoints require authentication. Include the authentication token in the request header:

```http
Authorization: Bearer <your-token>
```

**Authentication Errors**:
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Insufficient privileges for the requested operation

---

## Endpoints

### Upload PDF

Upload a question bank PDF and start a solver session.

**Endpoint**: `POST /api/solve/upload`

**Authentication**: Required

**Request**:

```http
POST /api/solve/upload HTTP/1.1
Content-Type: multipart/form-data
Authorization: Bearer <token>

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="questions.pdf"
Content-Type: application/pdf

<PDF binary data>
------WebKitFormBoundary--
```

**Request Parameters**:
- `file` (required): PDF file containing question bank

**Response** (200 OK):

```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "classification": {
    "doc_type": "question_bank",
    "confidence": 0.95,
    "reasoning": "Document contains numbered questions with multiple choice options but no answer indicators"
  },
  "total_questions": 100,
  "status": "processing",
  "message": "Question extraction started. Use WebSocket to monitor progress."
}
```

**Response** (Low Confidence Classification):

```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "classification": {
    "doc_type": "unknown",
    "confidence": 0.65,
    "reasoning": "Document structure is ambiguous"
  },
  "requires_manual_classification": true,
  "message": "Please confirm document type: question_bank or answer_key"
}
```

**Error Responses**:

```json
{
  "error": true,
  "error_type": "service_unavailable",
  "message": "Ollama service is not available",
  "details": {
    "suggestions": [
      "Ensure Ollama is running: ollama serve",
      "Check service status: curl http://localhost:11434/api/tags"
    ]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

```json
{
  "error": true,
  "error_type": "document_error",
  "message": "Invalid PDF file",
  "details": {
    "reason": "File is password-protected or corrupted"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

```json
{
  "error": true,
  "error_type": "capacity_error",
  "message": "Maximum concurrent sessions reached",
  "details": {
    "current_sessions": 2,
    "max_sessions": 2,
    "queue_position": 3,
    "estimated_wait_minutes": 15
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Get Session Status

Retrieve the current status and results of a solver session.

**Endpoint**: `GET /api/solve/session/<session_id>`

**Authentication**: Required

**Request**:

```http
GET /api/solve/session/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Authorization: Bearer <token>
```

**Response** (200 OK):

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "pdf_path": "/uploads/questions.pdf",
  "total_questions": 100,
  "processed_count": 45,
  "solved_count": 42,
  "unsolvable_count": 2,
  "error_count": 1,
  "start_time": "2024-01-15T10:00:00Z",
  "elapsed_seconds": 1350,
  "estimated_remaining_seconds": 1650,
  "average_confidence": 0.78,
  "questions_per_minute": 2.0,
  "questions": [
    {
      "number": 1,
      "text": "What is 2 + 2?",
      "options": [
        {"label": "A", "text": "3"},
        {"label": "B", "text": "4"},
        {"label": "C", "text": "5"},
        {"label": "D", "text": "6"}
      ],
      "page_number": 1,
      "has_image": false,
      "question_type": "math"
    }
  ],
  "results": {
    "1": {
      "question_number": 1,
      "selected_option": "B",
      "explanation": "2 + 2 equals 4, which is option B.",
      "confidence": 0.95,
      "processing_time_ms": 1250,
      "status": "solved"
    }
  },
  "validation_report": {
    "total_questions": 45,
    "issues": [
      {
        "question_number": 15,
        "severity": "warning",
        "issue_type": "low_confidence",
        "description": "Confidence score 0.55 is below threshold 0.6"
      }
    ],
    "flagged_questions": [15, 23],
    "average_confidence": 0.78
  },
  "user_corrections": {
    "15": "C"
  },
  "user_notes": {
    "15": "Original answer was B, but explanation was incorrect"
  }
}
```

**Error Responses**:

```json
{
  "error": true,
  "error_type": "not_found",
  "message": "Session not found",
  "details": {
    "session_id": "invalid-id"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Pause Session

Pause an active solver session.

**Endpoint**: `POST /api/solve/session/<session_id>/pause`

**Authentication**: Required

**Request**:

```http
POST /api/solve/session/550e8400-e29b-41d4-a716-446655440000/pause HTTP/1.1
Authorization: Bearer <token>
```

**Response** (200 OK):

```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "paused",
  "processed_count": 45,
  "message": "Session paused successfully. All progress has been saved."
}
```

**Error Responses**:

```json
{
  "error": true,
  "error_type": "invalid_operation",
  "message": "Cannot pause session in current state",
  "details": {
    "current_status": "completed",
    "allowed_statuses": ["processing"]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Resume Session

Resume a paused solver session.

**Endpoint**: `POST /api/solve/session/<session_id>/resume`

**Authentication**: Required

**Request**:

```http
POST /api/solve/session/550e8400-e29b-41d4-a716-446655440000/resume HTTP/1.1
Authorization: Bearer <token>
```

**Response** (200 OK):

```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "processed_count": 45,
  "remaining_questions": 55,
  "message": "Session resumed. Processing will continue from question 46."
}
```

---

### Cancel Session

Cancel a solver session and discard partial results.

**Endpoint**: `POST /api/solve/session/<session_id>/cancel`

**Authentication**: Required

**Request**:

```http
POST /api/solve/session/550e8400-e29b-41d4-a716-446655440000/cancel HTTP/1.1
Authorization: Bearer <token>
```

**Response** (200 OK):

```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "message": "Session cancelled. Partial results have been discarded."
}
```

---

### Update Answer

Update the answer for a specific question (manual correction).

**Endpoint**: `PUT /api/solve/session/<session_id>/answer/<question_number>`

**Authentication**: Required

**Request**:

```http
PUT /api/solve/session/550e8400-e29b-41d4-a716-446655440000/answer/15 HTTP/1.1
Content-Type: application/json
Authorization: Bearer <token>

{
  "new_answer": "C",
  "reason": "Original explanation was incorrect"
}
```

**Request Body**:
- `new_answer` (required): New answer option (A, B, C, D, or E)
- `reason` (optional): Reason for correction

**Response** (200 OK):

```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "question_number": 15,
  "original_answer": "B",
  "new_answer": "C",
  "confidence": 1.0,
  "manually_verified": true,
  "message": "Answer updated successfully"
}
```

**Error Responses**:

```json
{
  "error": true,
  "error_type": "validation_error",
  "message": "Invalid answer option",
  "details": {
    "provided": "F",
    "valid_options": ["A", "B", "C", "D", "E"]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Add Note

Add a note or comment to a specific question.

**Endpoint**: `POST /api/solve/session/<session_id>/note/<question_number>`

**Authentication**: Required

**Request**:

```http
POST /api/solve/session/550e8400-e29b-41d4-a716-446655440000/note/15 HTTP/1.1
Content-Type: application/json
Authorization: Bearer <token>

{
  "note": "This question has ambiguous wording. Consider revising."
}
```

**Response** (200 OK):

```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "question_number": 15,
  "note": "This question has ambiguous wording. Consider revising.",
  "message": "Note added successfully"
}
```

---

### Approve Answer Key

Approve and finalize the answer key (admin only).

**Endpoint**: `POST /api/solve/session/<session_id>/approve`

**Authentication**: Required

**Authorization**: Administrator role required

**Request**:

```http
POST /api/solve/session/550e8400-e29b-41d4-a716-446655440000/approve HTTP/1.1
Content-Type: application/json
Authorization: Bearer <token>

{
  "approved_by": "admin_user",
  "comments": "All flagged questions reviewed and verified"
}
```

**Response** (200 OK):

```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "approved": true,
  "approved_by": "admin_user",
  "approved_at": "2024-01-15T11:00:00Z",
  "immutable": true,
  "message": "Answer key approved and marked as immutable"
}
```

**Error Responses**:

```json
{
  "error": true,
  "error_type": "authorization_error",
  "message": "Insufficient privileges to approve answer keys",
  "details": {
    "required_role": "administrator",
    "user_role": "user"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

```json
{
  "error": true,
  "error_type": "validation_error",
  "message": "Cannot approve answer key with unreviewed flagged questions",
  "details": {
    "flagged_questions": [15, 23, 42],
    "reviewed_questions": [15],
    "unreviewed_questions": [23, 42]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Export Answer Key

Export the answer key in various formats.

**Endpoint**: `GET /api/solve/session/<session_id>/export?format=<format>`

**Authentication**: Required

**Query Parameters**:
- `format` (required): Export format - `json`, `csv`, or `pdf`

**Request (JSON)**:

```http
GET /api/solve/session/550e8400-e29b-41d4-a716-446655440000/export?format=json HTTP/1.1
Authorization: Bearer <token>
```

**Response (JSON)** (200 OK):

```json
{
  "answer_key": {
    "0": 1,
    "1": 0,
    "2": 3
  },
  "metadata": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "generation_time": "2024-01-15T11:00:00Z",
    "total_questions": 100,
    "solved_count": 95,
    "unsolvable_count": 3,
    "manual_corrections": 2,
    "average_confidence": 0.82,
    "approved": true,
    "approved_by": "admin_user",
    "approved_at": "2024-01-15T11:00:00Z"
  },
  "unsolvable": [23, 67, 89],
  "low_confidence": [15, 42, 78]
}
```

**Request (CSV)**:

```http
GET /api/solve/session/550e8400-e29b-41d4-a716-446655440000/export?format=csv HTTP/1.1
Authorization: Bearer <token>
```

**Response (CSV)** (200 OK):

```csv
question_number,correct_answer,confidence,explanation,modified
1,B,0.95,"2 + 2 equals 4, which is option B.",false
2,A,0.88,"The capital of France is Paris.",false
15,C,1.00,"Corrected by user - original was B.",true
```

**Request (PDF)**:

```http
GET /api/solve/session/550e8400-e29b-41d4-a716-446655440000/export?format=pdf HTTP/1.1
Authorization: Bearer <token>
```

**Response (PDF)** (200 OK):

```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="answer_key_550e8400.pdf"

<PDF binary data>
```

---

### Use for OMR Evaluation

Use the generated answer key directly for OMR evaluation.

**Endpoint**: `POST /api/solve/session/<session_id>/use-for-evaluation`

**Authentication**: Required

**Request**:

```http
POST /api/solve/session/550e8400-e29b-41d4-a716-446655440000/use-for-evaluation HTTP/1.1
Content-Type: application/json
Authorization: Bearer <token>

{
  "student_responses_pdf": "/uploads/student_responses.pdf"
}
```

**Response** (200 OK):

```json
{
  "success": true,
  "evaluation_id": "eval-12345",
  "answer_key_session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "OMR evaluation started using generated answer key",
  "evaluation_url": "/api/evaluate/eval-12345"
}
```

---

### WebSocket Progress Updates

Real-time progress updates during question solving.

**Endpoint**: `WebSocket /api/solve/progress`

**Authentication**: Required (via query parameter or initial message)

**Connection**:

```javascript
const ws = new WebSocket('ws://localhost:5000/api/solve/progress?token=<your-token>');

ws.onopen = () => {
  // Subscribe to session updates
  ws.send(JSON.stringify({
    action: 'subscribe',
    session_id: '550e8400-e29b-41d4-a716-446655440000'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress update:', data);
};
```

**Progress Message Format**:

```json
{
  "type": "progress",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "current_question": 45,
  "total_questions": 100,
  "processed_count": 45,
  "solved_count": 42,
  "unsolvable_count": 2,
  "error_count": 1,
  "elapsed_time_seconds": 1350,
  "estimated_remaining_seconds": 1650,
  "average_confidence": 0.78,
  "questions_per_minute": 2.0,
  "timestamp": "2024-01-15T10:22:30Z"
}
```

**Completion Message Format**:

```json
{
  "type": "completion",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "total_questions": 100,
  "solved_count": 95,
  "unsolvable_count": 3,
  "error_count": 2,
  "total_time_seconds": 3000,
  "average_confidence": 0.82,
  "flagged_questions": [15, 23, 42],
  "timestamp": "2024-01-15T10:50:00Z"
}
```

**Error Message Format**:

```json
{
  "type": "error",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "error_type": "processing_error",
  "message": "Critical error during processing",
  "details": {
    "error": "Out of memory",
    "partial_results_saved": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Data Models

### Question

```typescript
interface Question {
  number: number;
  text: string;
  options: QuestionOption[];
  page_number: number;
  has_image: boolean;
  image_data?: string;  // Base64 encoded
  question_type?: 'math' | 'logical' | 'factual' | 'visual';
}
```

### QuestionOption

```typescript
interface QuestionOption {
  label: string;  // A, B, C, D, E
  text: string;
  has_image: boolean;
  image_data?: string;  // Base64 encoded
}
```

### SolverResult

```typescript
interface SolverResult {
  question_number: number;
  selected_option?: string;  // A, B, C, D, E
  explanation: string;
  confidence: number;  // 0.0 to 1.0
  processing_time_ms: number;
  status: 'solved' | 'unsolvable' | 'timeout' | 'error';
  error_message?: string;
}
```

### ValidationIssue

```typescript
interface ValidationIssue {
  question_number: number;
  severity: 'critical' | 'warning' | 'info';
  issue_type: string;
  description: string;
}
```

### ValidationReport

```typescript
interface ValidationReport {
  total_questions: number;
  issues: ValidationIssue[];
  flagged_questions: number[];
  average_confidence: number;
}
```

---

## Error Handling

All error responses follow a consistent format:

```json
{
  "error": true,
  "error_type": "service_unavailable|document_error|processing_error|validation_error|auth_error|authorization_error|not_found|invalid_operation|capacity_error",
  "message": "Human-readable error description",
  "details": {
    "additional": "context-specific information"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Types

| Error Type | HTTP Status | Description |
|------------|-------------|-------------|
| `service_unavailable` | 503 | Ollama service is not available |
| `document_error` | 400 | PDF file is invalid, corrupted, or encrypted |
| `processing_error` | 500 | Error during question extraction or solving |
| `validation_error` | 400 | Invalid input parameters or data |
| `auth_error` | 401 | Missing or invalid authentication token |
| `authorization_error` | 403 | Insufficient privileges for operation |
| `not_found` | 404 | Session or resource not found |
| `invalid_operation` | 400 | Operation not allowed in current state |
| `capacity_error` | 429 | Maximum concurrent sessions reached |

---

## Rate Limits

- **Concurrent Sessions**: Maximum 2 active solver sessions per user
- **Upload Rate**: Maximum 10 PDF uploads per hour per user
- **API Requests**: Maximum 1000 requests per hour per user
- **WebSocket Connections**: Maximum 5 concurrent connections per user

When rate limits are exceeded:

```json
{
  "error": true,
  "error_type": "rate_limit_exceeded",
  "message": "Rate limit exceeded",
  "details": {
    "limit": 10,
    "window": "1 hour",
    "retry_after_seconds": 3600
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Example Workflows

### Complete Workflow Example

```javascript
// 1. Upload PDF
const formData = new FormData();
formData.append('file', pdfFile);

const uploadResponse = await fetch('/api/solve/upload', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});

const { session_id } = await uploadResponse.json();

// 2. Connect to WebSocket for progress
const ws = new WebSocket(`ws://localhost:5000/api/solve/progress?token=${token}`);
ws.send(JSON.stringify({ action: 'subscribe', session_id }));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'completion') {
    console.log('Processing complete!');
    loadSessionResults();
  }
};

// 3. Get session status
const statusResponse = await fetch(`/api/solve/session/${session_id}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});

const session = await statusResponse.json();

// 4. Review and correct answers
for (const flaggedQuestion of session.validation_report.flagged_questions) {
  // Display question to user for review
  // If user corrects answer:
  await fetch(`/api/solve/session/${session_id}/answer/${flaggedQuestion}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ new_answer: 'C', reason: 'Explanation was incorrect' })
  });
}

// 5. Approve answer key (admin only)
await fetch(`/api/solve/session/${session_id}/approve`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    approved_by: 'admin_user',
    comments: 'All flagged questions reviewed'
  })
});

// 6. Export answer key
const exportResponse = await fetch(`/api/solve/session/${session_id}/export?format=json`, {
  headers: { 'Authorization': `Bearer ${token}` }
});

const answerKey = await exportResponse.json();
console.log('Answer key:', answerKey);
```

---

## Support

For API support and questions:
- Documentation: `/docs/api/ai-question-solver-api.md`
- Troubleshooting: `/docs/troubleshooting.md`
- GitHub Issues: [repository-url]/issues
