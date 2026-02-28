"""
Tests for solver logging configuration and functionality.

Validates Requirements 14.1, 14.4:
- 14.1: Log all AI_Solver responses including question, answer, confidence, and processing time
- 14.4: Log original and corrected answers for model improvement analysis
"""
import pytest
import os
import json
import tempfile
import shutil
import logging
from datetime import datetime, timedelta
from solver_logging_config import (
    SolverLogger,
    setup_solver_logging,
    get_logger,
    cleanup_old_logs,
    StructuredFormatter
)


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    temp_dir = tempfile.mkdtemp()
    
    # Create backend structure in temp directory
    backend_dir = os.path.join(temp_dir, "backend")
    os.makedirs(backend_dir, exist_ok=True)
    
    # Save original directory
    original_dir = os.getcwd()
    
    # Change to temp directory
    os.chdir(temp_dir)
    
    yield temp_dir
    
    # Restore original directory
    os.chdir(original_dir)
    
    # Cleanup - close all log handlers first
    logging.shutdown()
    
    # Wait a bit for file handles to be released
    import time
    time.sleep(0.1)
    
    # Cleanup temp directory
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Could not remove temp dir: {e}")


@pytest.fixture
def solver_logger(temp_log_dir):
    """Create a SolverLogger instance for testing."""
    session_id = "test-session-123"
    logger = SolverLogger(session_id)
    return logger


def test_solver_logger_initialization(temp_log_dir):
    """Test SolverLogger initialization creates necessary directories."""
    session_id = "test-session-init"
    logger = SolverLogger(session_id)
    
    # Verify main logs directory exists
    assert os.path.exists("backend/logs")
    
    # Verify session logs directory exists
    session_log_dir = f"backend/solver_sessions/{session_id}/logs"
    assert os.path.exists(session_log_dir)
    
    # Verify log files are created
    assert os.path.exists(os.path.join(session_log_dir, "solver_responses.jsonl"))
    assert os.path.exists(os.path.join(session_log_dir, "user_corrections.jsonl"))
    assert os.path.exists(os.path.join(session_log_dir, "approvals.jsonl"))


def test_log_solver_response_success(solver_logger):
    """Test logging successful AI solver response (Requirement 14.1)."""
    # Log a successful solver response
    solver_logger.log_solver_response(
        question_number=1,
        question_text="What is 2 + 2?",
        selected_answer="B",
        explanation="2 + 2 equals 4",
        confidence=0.95,
        processing_time_ms=1500.5,
        model_used="llama3.2:latest",
        status="solved"
    )
    
    # Read the solver responses log
    log_file = "backend/solver_sessions/test-session-123/logs/solver_responses.jsonl"
    assert os.path.exists(log_file)
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 1
        
        log_entry = json.loads(lines[0])
        assert log_entry["level"] == "INFO"
        assert log_entry["session_id"] == "test-session-123"
        assert log_entry["question_number"] == 1
        assert log_entry["event_type"] == "solver_response"
        
        data = log_entry["data"]
        assert data["question_number"] == 1
        assert data["question_text"] == "What is 2 + 2?"
        assert data["selected_answer"] == "B"
        assert data["explanation"] == "2 + 2 equals 4"
        assert data["confidence"] == 0.95
        assert data["processing_time_ms"] == 1500.5
        assert data["model_used"] == "llama3.2:latest"
        assert data["status"] == "solved"
        assert data["error_message"] is None


def test_log_solver_response_with_error(solver_logger):
    """Test logging AI solver response with error (Requirement 14.1)."""
    # Log a solver response with error
    solver_logger.log_solver_response(
        question_number=5,
        question_text="Complex question",
        selected_answer=None,
        explanation="",
        confidence=0.0,
        processing_time_ms=500.0,
        model_used="llama3.2:latest",
        status="error",
        error_message="Connection timeout"
    )
    
    # Read the solver responses log
    log_file = "backend/solver_sessions/test-session-123/logs/solver_responses.jsonl"
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
        log_entry = json.loads(lines[-1])  # Get last entry
        
        data = log_entry["data"]
        assert data["status"] == "error"
        assert data["error_message"] == "Connection timeout"
        assert data["selected_answer"] is None
        assert data["confidence"] == 0.0


def test_log_solver_response_truncates_long_text(solver_logger):
    """Test that long question text and explanations are truncated."""
    long_question = "A" * 300
    long_explanation = "B" * 600
    
    solver_logger.log_solver_response(
        question_number=10,
        question_text=long_question,
        selected_answer="C",
        explanation=long_explanation,
        confidence=0.85,
        processing_time_ms=2000.0,
        model_used="llama3.2:latest",
        status="solved"
    )
    
    # Read the log
    log_file = "backend/solver_sessions/test-session-123/logs/solver_responses.jsonl"
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
        log_entry = json.loads(lines[-1])
        
        data = log_entry["data"]
        # Question should be truncated to 200 chars + "..."
        assert len(data["question_text"]) == 203
        assert data["question_text"].endswith("...")
        
        # Explanation should be truncated to 500 chars + "..."
        assert len(data["explanation"]) == 503
        assert data["explanation"].endswith("...")


def test_log_user_correction(solver_logger):
    """Test logging user correction (Requirement 14.4)."""
    # Log a user correction
    solver_logger.log_user_correction(
        question_number=3,
        original_answer="B",
        corrected_answer="C",
        user_id="user-456",
        note="Original answer was incorrect based on context"
    )
    
    # Read the user corrections log
    log_file = "backend/solver_sessions/test-session-123/logs/user_corrections.jsonl"
    assert os.path.exists(log_file)
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 1
        
        log_entry = json.loads(lines[0])
        assert log_entry["level"] == "INFO"
        assert log_entry["session_id"] == "test-session-123"
        assert log_entry["question_number"] == 3
        assert log_entry["user_id"] == "user-456"
        assert log_entry["event_type"] == "user_correction"
        
        data = log_entry["data"]
        assert data["question_number"] == 3
        assert data["original_answer"] == "B"
        assert data["corrected_answer"] == "C"
        assert data["user_id"] == "user-456"
        assert data["note"] == "Original answer was incorrect based on context"
        assert "timestamp" in data


def test_log_user_correction_without_note(solver_logger):
    """Test logging user correction without note (Requirement 14.4)."""
    solver_logger.log_user_correction(
        question_number=7,
        original_answer="A",
        corrected_answer="D",
        user_id="user-789"
    )
    
    # Read the log
    log_file = "backend/solver_sessions/test-session-123/logs/user_corrections.jsonl"
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
        log_entry = json.loads(lines[-1])
        
        data = log_entry["data"]
        assert data["note"] is None


def test_log_user_correction_with_none_original(solver_logger):
    """Test logging correction when original answer was None (unsolvable)."""
    solver_logger.log_user_correction(
        question_number=12,
        original_answer=None,
        corrected_answer="B",
        user_id="user-999",
        note="AI couldn't solve, but answer is B"
    )
    
    # Read the log
    log_file = "backend/solver_sessions/test-session-123/logs/user_corrections.jsonl"
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
        log_entry = json.loads(lines[-1])
        
        data = log_entry["data"]
        assert data["original_answer"] is None
        assert data["corrected_answer"] == "B"


def test_log_approval_action(solver_logger):
    """Test logging approval action with metadata."""
    # Log an approval action
    solver_logger.log_approval_action(
        user_id="admin-123",
        action="approve",
        total_questions=100,
        solved_count=95,
        manual_corrections=5,
        average_confidence=0.87,
        flagged_questions=[15, 42, 67, 89, 91]
    )
    
    # Read the approvals log
    log_file = "backend/solver_sessions/test-session-123/logs/approvals.jsonl"
    assert os.path.exists(log_file)
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 1
        
        log_entry = json.loads(lines[0])
        assert log_entry["level"] == "INFO"
        assert log_entry["session_id"] == "test-session-123"
        assert log_entry["user_id"] == "admin-123"
        assert log_entry["event_type"] == "approval_action"
        
        data = log_entry["data"]
        assert data["user_id"] == "admin-123"
        assert data["action"] == "approve"
        assert data["total_questions"] == 100
        assert data["solved_count"] == 95
        assert data["manual_corrections"] == 5
        assert data["average_confidence"] == 0.87
        assert data["flagged_questions"] == [15, 42, 67, 89, 91]
        assert "timestamp" in data


def test_multiple_solver_responses_logged(solver_logger):
    """Test that multiple solver responses are logged sequentially."""
    # Log multiple responses
    for i in range(1, 6):
        solver_logger.log_solver_response(
            question_number=i,
            question_text=f"Question {i}",
            selected_answer="A",
            explanation=f"Explanation {i}",
            confidence=0.8 + (i * 0.02),
            processing_time_ms=1000.0 + (i * 100),
            model_used="llama3.2:latest",
            status="solved"
        )
    
    # Read the log
    log_file = "backend/solver_sessions/test-session-123/logs/solver_responses.jsonl"
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 5
        
        # Verify each entry
        for i, line in enumerate(lines, start=1):
            log_entry = json.loads(line)
            data = log_entry["data"]
            assert data["question_number"] == i
            assert data["question_text"] == f"Question {i}"


def test_structured_formatter():
    """Test StructuredFormatter produces valid JSON."""
    formatter = StructuredFormatter()
    
    # Create a log record
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    # Add extra fields
    record.session_id = "session-123"
    record.question_number = 5
    record.event_type = "solver_response"
    record.data = {"key": "value"}
    
    # Format the record
    formatted = formatter.format(record)
    
    # Verify it's valid JSON
    parsed = json.loads(formatted)
    assert parsed["level"] == "INFO"
    assert parsed["module"] == "test"
    assert parsed["message"] == "Test message"
    assert parsed["session_id"] == "session-123"
    assert parsed["question_number"] == 5
    assert parsed["event_type"] == "solver_response"
    assert parsed["data"] == {"key": "value"}
    assert "timestamp" in parsed


def test_setup_solver_logging():
    """Test setup_solver_logging function."""
    logger = setup_solver_logging("test-session-setup")
    
    assert isinstance(logger, SolverLogger)
    assert logger.session_id == "test-session-setup"


def test_get_logger():
    """Test get_logger function."""
    logger = get_logger("test_module")
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"


def test_cleanup_old_logs(temp_log_dir):
    """Test cleanup of old log files."""
    # Create log directory structure
    log_dir = "backend/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    sessions_dir = "backend/solver_sessions"
    os.makedirs(sessions_dir, exist_ok=True)
    
    # Create old log file (35 days old)
    old_log_file = os.path.join(log_dir, "old_solver.log")
    with open(old_log_file, 'w') as f:
        f.write("old log content")
    
    # Set modification time to 35 days ago
    old_time = (datetime.now() - timedelta(days=35)).timestamp()
    os.utime(old_log_file, (old_time, old_time))
    
    # Create recent log file (5 days old)
    recent_log_file = os.path.join(log_dir, "recent_solver.log")
    with open(recent_log_file, 'w') as f:
        f.write("recent log content")
    
    recent_time = (datetime.now() - timedelta(days=5)).timestamp()
    os.utime(recent_log_file, (recent_time, recent_time))
    
    # Create old session directory (35 days old)
    old_session_dir = os.path.join(sessions_dir, "old-session")
    os.makedirs(old_session_dir, exist_ok=True)
    old_session_file = os.path.join(old_session_dir, "session.json")
    with open(old_session_file, 'w') as f:
        json.dump({"session_id": "old-session"}, f)
    
    os.utime(old_session_file, (old_time, old_time))
    
    # Create recent session directory (5 days old)
    recent_session_dir = os.path.join(sessions_dir, "recent-session")
    os.makedirs(recent_session_dir, exist_ok=True)
    recent_session_file = os.path.join(recent_session_dir, "session.json")
    with open(recent_session_file, 'w') as f:
        json.dump({"session_id": "recent-session"}, f)
    
    os.utime(recent_session_file, (recent_time, recent_time))
    
    # Run cleanup with 30 day retention
    cleanup_old_logs(retention_days=30)
    
    # Verify old files are removed
    assert not os.path.exists(old_log_file)
    assert not os.path.exists(old_session_dir)
    
    # Verify recent files are kept
    assert os.path.exists(recent_log_file)
    assert os.path.exists(recent_session_dir)


def test_log_rotation_configuration(solver_logger):
    """Test that log rotation is properly configured."""
    # Check that handlers have rotation configured
    for handler in solver_logger.logger.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            # Verify rotation settings
            assert handler.maxBytes == 100 * 1024 * 1024  # 100 MB
            assert handler.backupCount == 5


def test_session_logger_isolation(temp_log_dir):
    """Test that different session loggers write to separate files."""
    # Create two session loggers
    logger1 = SolverLogger("session-1")
    logger2 = SolverLogger("session-2")
    
    # Log to each
    logger1.log_solver_response(
        question_number=1,
        question_text="Question 1",
        selected_answer="A",
        explanation="Explanation 1",
        confidence=0.9,
        processing_time_ms=1000.0,
        model_used="llama3.2:latest",
        status="solved"
    )
    
    logger2.log_solver_response(
        question_number=2,
        question_text="Question 2",
        selected_answer="B",
        explanation="Explanation 2",
        confidence=0.8,
        processing_time_ms=1500.0,
        model_used="llama3.2:latest",
        status="solved"
    )
    
    # Verify separate log files
    log_file1 = "backend/solver_sessions/session-1/logs/solver_responses.jsonl"
    log_file2 = "backend/solver_sessions/session-2/logs/solver_responses.jsonl"
    
    assert os.path.exists(log_file1)
    assert os.path.exists(log_file2)
    
    # Verify content is separate
    with open(log_file1, 'r') as f:
        lines1 = f.readlines()
        assert len(lines1) == 1
        entry1 = json.loads(lines1[0])
        assert entry1["data"]["question_number"] == 1
    
    with open(log_file2, 'r') as f:
        lines2 = f.readlines()
        assert len(lines2) == 1
        entry2 = json.loads(lines2[0])
        assert entry2["data"]["question_number"] == 2


def test_error_log_level_filtering(solver_logger):
    """Test that errors.log only contains ERROR level messages."""
    # Log messages at different levels
    solver_logger.info("Info message")
    solver_logger.warning("Warning message")
    solver_logger.error("Error message")
    
    # Check errors.log
    errors_log = "backend/solver_sessions/test-session-123/logs/errors.log"
    
    with open(errors_log, 'r') as f:
        content = f.read()
        # Should only contain error message
        assert "Error message" in content
        assert "Info message" not in content
        assert "Warning message" not in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
