# AI Question Solver - Comprehensive Logging System

## Overview

The AI Question Solver includes a comprehensive logging system that tracks all critical events, AI responses, user actions, and system operations. This document describes the logging architecture, log files, and how to use the logging system.

## Log Files and Locations

### System-Wide Logs

Located in `backend/logs/`:

- **solver_main.log** - Main application log with all system events
  - Rotates when reaching 100MB
  - Keeps 5 backup files
  - Contains INFO, WARNING, and ERROR level messages

### Session-Specific Logs

Located in `backend/solver_sessions/{session_id}/logs/`:

- **solver_responses.jsonl** - Structured JSON log of all AI solver responses
  - One JSON object per line (JSONL format)
  - Contains: question, answer, confidence, processing time, model used
  - Used for model performance analysis

- **user_corrections.jsonl** - Structured JSON log of all user corrections
  - One JSON object per line (JSONL format)
  - Contains: question number, original answer, corrected answer, user ID, timestamp
  - Used for model improvement analysis

- **approvals.jsonl** - Structured JSON log of approval actions
  - One JSON object per line (JSONL format)
  - Contains: user ID, action, statistics, timestamp
  - Used for audit trail

- **extraction.log** - Question extraction process logs
  - PDF processing details
  - Question parsing events
  - Extraction errors

- **validation.log** - Validation engine logs
  - Confidence score calculations
  - Validation issues detected
  - Flagged questions

- **errors.log** - All ERROR level messages for the session
  - Critical errors
  - Exception stack traces
  - Used for debugging

## Log Formats

### Standard Log Format

```
2024-01-15 10:30:45,123 - module_name - LEVEL - Message
```

### Structured JSON Format (JSONL)

Solver responses:
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "module": "solver",
  "message": "[SOLVER_RESPONSE] Q15: solved - Answer: C, Confidence: 0.85, Time: 2345ms, Model: llama3.2:latest",
  "session_id": "uuid-string",
  "question_number": 15,
  "event_type": "solver_response",
  "data": {
    "question_number": 15,
    "question_text": "What is the capital of France?",
    "selected_answer": "C",
    "explanation": "Paris is the capital and largest city of France...",
    "confidence": 0.850,
    "processing_time_ms": 2345.67,
    "model_used": "llama3.2:latest",
    "status": "solved",
    "error_message": null
  }
}
```

User corrections:
```json
{
  "timestamp": "2024-01-15T10:35:12.456789",
  "level": "INFO",
  "module": "solver",
  "message": "[USER_CORRECTION] Q15: B → C by user admin_123",
  "session_id": "uuid-string",
  "question_number": 15,
  "user_id": "admin_123",
  "event_type": "user_correction",
  "data": {
    "question_number": 15,
    "original_answer": "B",
    "corrected_answer": "C",
    "user_id": "admin_123",
    "note": null,
    "timestamp": "2024-01-15T10:35:12.456789"
  }
}
```

Approval actions:
```json
{
  "timestamp": "2024-01-15T11:00:00.123456",
  "level": "INFO",
  "module": "solver",
  "message": "[APPROVAL_ACTION] approve by user admin_123 - 95/100 solved, 2 corrections, avg confidence: 0.82",
  "session_id": "uuid-string",
  "user_id": "admin_123",
  "event_type": "approval_action",
  "data": {
    "user_id": "admin_123",
    "action": "approve",
    "total_questions": 100,
    "solved_count": 95,
    "manual_corrections": 2,
    "average_confidence": 0.820,
    "flagged_questions": [15, 42, 78],
    "timestamp": "2024-01-15T11:00:00.123456"
  }
}
```

## Using the Logging System

### In Code

```python
from solver_logging_config import SolverLogger

# Create logger for a session
logger = SolverLogger(session_id="uuid-string")

# Log AI solver response
logger.log_solver_response(
    question_number=15,
    question_text="What is the capital of France?",
    selected_answer="C",
    explanation="Paris is the capital...",
    confidence=0.85,
    processing_time_ms=2345.67,
    model_used="llama3.2:latest",
    status="solved"
)

# Log user correction
logger.log_user_correction(
    question_number=15,
    original_answer="B",
    corrected_answer="C",
    user_id="admin_123",
    note="Original answer was incorrect"
)

# Log approval action
logger.log_approval_action(
    user_id="admin_123",
    action="approve",
    total_questions=100,
    solved_count=95,
    manual_corrections=2,
    average_confidence=0.82,
    flagged_questions=[15, 42, 78]
)

# Standard logging methods
logger.info("Processing started")
logger.warning("Low confidence detected")
logger.error("Failed to process question")
```

### Module-Specific Loggers

```python
from solver_logging_config import get_logger

# Get logger for specific module
logger = get_logger("question_parser")
logger.info("Extracting questions from PDF")
```

## Log Rotation and Retention

### Automatic Rotation

- Main log file (`solver_main.log`) rotates automatically when it reaches 100MB
- Keeps 5 backup files (solver_main.log.1, solver_main.log.2, etc.)
- Oldest backup is deleted when creating a new one

### Retention Policy

- **Default retention period**: 30 days
- Session logs older than 30 days are automatically deleted
- Main logs are rotated but not automatically deleted (manual cleanup required)

### Manual Cleanup

Run the cleanup script manually:

```bash
# Clean up logs older than 30 days (default)
python backend/log_cleanup.py

# Clean up logs older than 60 days
python backend/log_cleanup.py --retention-days 60

# Dry run (show what would be deleted)
python backend/log_cleanup.py --dry-run
```

### Scheduled Cleanup (Recommended)

Set up a cron job to run cleanup daily:

```bash
# Edit crontab
crontab -e

# Add this line to run cleanup daily at 2 AM
0 2 * * * cd /path/to/project && python backend/log_cleanup.py >> /var/log/solver_cleanup.log 2>&1
```

On Windows, use Task Scheduler:
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 2:00 AM
4. Set action: Start a program
5. Program: `python`
6. Arguments: `backend/log_cleanup.py`
7. Start in: `C:\path\to\project`

## Analyzing Logs

### Viewing Structured Logs

Since solver responses, corrections, and approvals are in JSONL format, you can use `jq` for analysis:

```bash
# Count total solver responses
cat backend/solver_sessions/*/logs/solver_responses.jsonl | wc -l

# Get average confidence score
cat backend/solver_sessions/*/logs/solver_responses.jsonl | \
  jq -r '.data.confidence' | \
  awk '{sum+=$1; count++} END {print sum/count}'

# Find all questions with confidence < 0.6
cat backend/solver_sessions/*/logs/solver_responses.jsonl | \
  jq 'select(.data.confidence < 0.6) | .data.question_number'

# Count corrections by user
cat backend/solver_sessions/*/logs/user_corrections.jsonl | \
  jq -r '.data.user_id' | \
  sort | uniq -c

# Get all timeout errors
cat backend/solver_sessions/*/logs/solver_responses.jsonl | \
  jq 'select(.data.status == "timeout")'
```

### Python Analysis

```python
import json

# Read solver responses
responses = []
with open('backend/solver_sessions/{session_id}/logs/solver_responses.jsonl', 'r') as f:
    for line in f:
        responses.append(json.loads(line))

# Calculate statistics
total = len(responses)
solved = sum(1 for r in responses if r['data']['status'] == 'solved')
avg_confidence = sum(r['data']['confidence'] for r in responses) / total
avg_time = sum(r['data']['processing_time_ms'] for r in responses) / total

print(f"Total: {total}, Solved: {solved}, Avg Confidence: {avg_confidence:.2f}, Avg Time: {avg_time:.0f}ms")
```

## Log Levels

- **DEBUG**: Detailed diagnostic information (disabled in production)
- **INFO**: General informational messages about system operation
- **WARNING**: Warning messages for potentially problematic situations
- **ERROR**: Error messages for failures that don't stop the system
- **CRITICAL**: Critical errors that may cause system failure

## Configuration

Log settings can be configured in `solver_logging_config.py`:

```python
# Log retention settings
LOG_RETENTION_DAYS = 30  # Days to keep logs
MAX_LOG_SIZE_MB = 100    # Max size before rotation
BACKUP_COUNT = 5         # Number of backup files to keep
```

## Troubleshooting

### Logs not being created

1. Check that the logs directory exists: `backend/logs/`
2. Check file permissions
3. Check disk space

### Session logs not appearing

1. Verify session ID is correct
2. Check that session directory exists: `backend/solver_sessions/{session_id}/logs/`
3. Verify logger is initialized with session ID

### Log rotation not working

1. Check that `MAX_LOG_SIZE_MB` is set correctly
2. Verify write permissions on log directory
3. Check that `RotatingFileHandler` is being used

## Best Practices

1. **Always use structured logging for machine-parseable events** (solver responses, corrections, approvals)
2. **Include context in log messages** (session ID, question number, user ID)
3. **Use appropriate log levels** (don't log everything as ERROR)
4. **Monitor log file sizes** and adjust rotation settings if needed
5. **Set up automated cleanup** to prevent disk space issues
6. **Review error logs regularly** to identify systemic issues
7. **Use log analysis tools** (jq, grep, Python) for insights

## Security Considerations

- Log files may contain sensitive information (question content, user IDs)
- Restrict access to log directories (chmod 700)
- Consider encrypting logs at rest for sensitive deployments
- Sanitize logs before sharing for debugging
- Follow data retention policies for your organization
