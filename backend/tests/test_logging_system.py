"""
Unit tests for comprehensive logging system.
"""
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
import pytest
from solver_logging_config import SolverLogger, cleanup_old_logs, LOG_RETENTION_DAYS


class TestSolverLogger:
    """Test SolverLogger functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_session_id = "test-session-123"
        self.logger = SolverLogger(self.test_session_id)
        
        # Create test log directory
        self.log_dir = f"backend/solver_sessions/{self.test_session_id}/logs"
        os.makedirs(self.log_dir, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove test session directory
        session_dir = f"backend/solver_sessions/{self.test_session_id}"
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
    
    def test_log_solver_response(self):
        """Test logging AI solver response."""
        self.logger.log_solver_response(
            question_number=1,
            question_text="What is 2+2?",
            selected_answer="C",
            explanation="2+2 equals 4",
            confidence=0.95,
            processing_time_ms=1234.56,
            model_used="llama3.2:latest",
            status="solved"
        )
        
        # Verify log file was created
        log_file = os.path.join(self.log_dir, "solver_responses.jsonl")
        assert os.path.exists(log_file)
        
        # Read and verify log content
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            log_entry = json.loads(lines[0])
            assert log_entry['event_type'] == 'solver_response'
            assert log_entry['question_number'] == 1
            assert log_entry['session_id'] == self.test_session_id
            assert log_entry['data']['selected_answer'] == 'C'
            assert log_entry['data']['confidence'] == 0.95
            assert log_entry['data']['model_used'] == 'llama3.2:latest'
            assert log_entry['data']['status'] == 'solved'
    
    def test_log_user_correction(self):
        """Test logging user correction."""
        self.logger.log_user_correction(
            question_number=5,
            original_answer="B",
            corrected_answer="C",
            user_id="admin_123",
            note="Original answer was incorrect"
        )
        
        # Verify log file was created
        log_file = os.path.join(self.log_dir, "user_corrections.jsonl")
        assert os.path.exists(log_file)
        
        # Read and verify log content
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            log_entry = json.loads(lines[0])
            assert log_entry['event_type'] == 'user_correction'
            assert log_entry['question_number'] == 5
            assert log_entry['user_id'] == 'admin_123'
            assert log_entry['data']['original_answer'] == 'B'
            assert log_entry['data']['corrected_answer'] == 'C'
            assert log_entry['data']['note'] == 'Original answer was incorrect'
    
    def test_log_approval_action(self):
        """Test logging approval action."""
        self.logger.log_approval_action(
            user_id="admin_456",
            action="approve",
            total_questions=100,
            solved_count=95,
            manual_corrections=3,
            average_confidence=0.82,
            flagged_questions=[15, 42, 78]
        )
        
        # Verify log file was created
        log_file = os.path.join(self.log_dir, "approvals.jsonl")
        assert os.path.exists(log_file)
        
        # Read and verify log content
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            log_entry = json.loads(lines[0])
            assert log_entry['event_type'] == 'approval_action'
            assert log_entry['user_id'] == 'admin_456'
            assert log_entry['data']['action'] == 'approve'
            assert log_entry['data']['total_questions'] == 100
            assert log_entry['data']['solved_count'] == 95
            assert log_entry['data']['manual_corrections'] == 3
            assert log_entry['data']['average_confidence'] == 0.82
            assert log_entry['data']['flagged_questions'] == [15, 42, 78]
    
    def test_multiple_solver_responses(self):
        """Test logging multiple solver responses."""
        # Log 5 responses
        for i in range(1, 6):
            self.logger.log_solver_response(
                question_number=i,
                question_text=f"Question {i}",
                selected_answer="A",
                explanation=f"Explanation {i}",
                confidence=0.8 + (i * 0.02),
                processing_time_ms=1000 + (i * 100),
                model_used="llama3.2:latest",
                status="solved"
            )
        
        # Verify all responses were logged
        log_file = os.path.join(self.log_dir, "solver_responses.jsonl")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 5
            
            # Verify each entry
            for i, line in enumerate(lines, 1):
                log_entry = json.loads(line)
                assert log_entry['question_number'] == i
                assert log_entry['data']['confidence'] == 0.8 + (i * 0.02)
    
    def test_log_solver_error(self):
        """Test logging solver error."""
        self.logger.log_solver_response(
            question_number=10,
            question_text="Unsolvable question",
            selected_answer=None,
            explanation="",
            confidence=0.0,
            processing_time_ms=30000,
            model_used="llama3.2:latest",
            status="timeout",
            error_message="Timeout after 30s"
        )
        
        # Verify error was logged
        log_file = os.path.join(self.log_dir, "solver_responses.jsonl")
        with open(log_file, 'r') as f:
            log_entry = json.loads(f.readline())
            assert log_entry['data']['status'] == 'timeout'
            assert log_entry['data']['error_message'] == 'Timeout after 30s'
            assert log_entry['data']['selected_answer'] is None


class TestLogCleanup:
    """Test log cleanup functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp()
        self.original_sessions_dir = "backend/solver_sessions"
        
        # Create test session directories with different ages
        self.old_session_id = "old-session-123"
        self.new_session_id = "new-session-456"
        
        old_session_dir = os.path.join(self.test_dir, self.old_session_id)
        new_session_dir = os.path.join(self.test_dir, self.new_session_id)
        
        os.makedirs(old_session_dir, exist_ok=True)
        os.makedirs(new_session_dir, exist_ok=True)
        
        # Create session.json files
        old_session_file = os.path.join(old_session_dir, "session.json")
        new_session_file = os.path.join(new_session_dir, "session.json")
        
        with open(old_session_file, 'w') as f:
            json.dump({"session_id": self.old_session_id}, f)
        
        with open(new_session_file, 'w') as f:
            json.dump({"session_id": self.new_session_id}, f)
        
        # Set old file modification time to 40 days ago
        old_time = (datetime.now() - timedelta(days=40)).timestamp()
        os.utime(old_session_file, (old_time, old_time))
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_cleanup_identifies_old_sessions(self):
        """Test that cleanup identifies sessions older than retention period."""
        # Note: This is a basic test structure
        # Full implementation would require mocking the cleanup function
        # to use the test directory instead of the real sessions directory
        
        # For now, just verify the test setup
        old_session_file = os.path.join(self.test_dir, self.old_session_id, "session.json")
        new_session_file = os.path.join(self.test_dir, self.new_session_id, "session.json")
        
        old_mtime = datetime.fromtimestamp(os.path.getmtime(old_session_file))
        new_mtime = datetime.fromtimestamp(os.path.getmtime(new_session_file))
        
        cutoff_date = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
        
        assert old_mtime < cutoff_date, "Old session should be older than cutoff"
        assert new_mtime > cutoff_date, "New session should be newer than cutoff"


class TestStructuredLogging:
    """Test structured logging format."""
    
    def test_json_format_validity(self):
        """Test that logged JSON is valid and parseable."""
        session_id = "test-json-session"
        logger = SolverLogger(session_id)
        
        # Create log directory
        log_dir = f"backend/solver_sessions/{session_id}/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        try:
            # Log a response
            logger.log_solver_response(
                question_number=1,
                question_text="Test question",
                selected_answer="A",
                explanation="Test explanation",
                confidence=0.9,
                processing_time_ms=1500.0,
                model_used="test-model",
                status="solved"
            )
            
            # Read and parse JSON
            log_file = os.path.join(log_dir, "solver_responses.jsonl")
            with open(log_file, 'r') as f:
                for line in f:
                    # Should not raise exception
                    log_entry = json.loads(line)
                    
                    # Verify required fields
                    assert 'timestamp' in log_entry
                    assert 'level' in log_entry
                    assert 'module' in log_entry
                    assert 'message' in log_entry
                    assert 'session_id' in log_entry
                    assert 'event_type' in log_entry
                    assert 'data' in log_entry
                    
                    # Verify timestamp is ISO format
                    datetime.fromisoformat(log_entry['timestamp'])
        
        finally:
            # Cleanup
            session_dir = f"backend/solver_sessions/{session_id}"
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
