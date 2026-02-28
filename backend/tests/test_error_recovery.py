"""
Error Recovery Tests for AI Question Solver

Tests recovery from various failure scenarios:
- Ollama service interruption
- Page conversion failures
- AI solver timeouts
- Session recovery after crash

Requirements: 10.1-10.7 (Error Handling and Recovery)
"""

import pytest
import json
import time
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from app import app
from session_manager import SessionManager, SessionState
from question_parser import QuestionParser, Question, QuestionOption
from ai_solver import AISolver, SolverResult
from ollama_client import OllamaClient


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def session_manager():
    """Session manager instance"""
    return SessionManager()


@pytest.fixture
def sample_questions():
    """Sample questions for testing"""
    return [
        Question(
            number=i,
            text=f"Question {i}",
            options=[QuestionOption(label=l, text=f"Option {l}") for l in "ABCD"],
            page_number=1,
            question_type="factual"
        )
        for i in range(1, 6)
    ]


class TestOllamaServiceRecovery:
    """Test recovery from Ollama service interruptions"""
    
    @patch('ollama_client.requests')
    def test_service_unavailable_on_upload(self, mock_requests, client):
        """Test that upload fails gracefully when Ollama is unavailable (Req 10.1)"""
        # Mock Ollama service unavailable
        mock_requests.get.side_effect = ConnectionError("Service unavailable")
        
        response = client.post(
            '/api/solve/upload',
            data={'file': (BytesIO(b'%PDF-1.4 mock'), 'test.pdf')},
            content_type='multipart/form-data'
        )
        
        # Should return error and prevent session initiation
        assert response.status_code in [503, 500]
        data = json.loads(response.data)
        assert 'error' in data
        assert 'ollama' in data['error'].lower() or 'service' in data['error'].lower()
    
    @patch('session_manager.AISolver')
    def test_service_interruption_during_solving(
        self, mock_solver, client, session_manager, sample_questions
    ):
        """Test recovery when Ollama fails during solving (Req 10.3, 10.4)"""
        # Create session
        session_id = session_manager.create_session('/tmp/test.pdf')
        session = session_manager.get_session(session_id)
        session.questions = sample_questions
        session.total_questions = len(sample_questions)
        
        # Mock solver with intermittent failures
        call_count = [0]
        def solve_with_failures(question):
            call_count[0] += 1
            if call_count[0] in [2, 3]:  # Fail on questions 2 and 3
                raise ConnectionError("Ollama service interrupted")
            return SolverResult(
                question.number, "B", "Answer", 0.9, 500, "solved"
            )
        
        mock_solver_instance = mock_solver.return_value
        mock_solver_instance.solve_question.side_effect = solve_with_failures
        
        # Start processing
        session_manager.start_processing(session_id)
        
        # Wait for completion
        time.sleep(5)
        
        # Verify retry logic was applied
        session = session_manager.get_session(session_id)
        
        # Questions 2 and 3 should have "solver_error" status after retries
        assert session.results[2].status == "solver_error"
        assert session.results[3].status == "solver_error"
        
        # Other questions should be solved
        assert session.results[1].status == "solved"
        assert session.results[4].status == "solved"
        assert session.results[5].status == "solved"
        
        # Processing should continue despite errors
        assert session.status == "completed"
        assert session.error_count == 2
    
    @patch('ai_solver.OllamaClient')
    def test_exponential_backoff_on_retry(self, mock_ollama_client):
        """Test exponential backoff retry logic (Req 10.3, 10.4)"""
        solver = AISolver()
        
        # Mock Ollama client with failures
        mock_client = mock_ollama_client.return_value
        attempt_times = []
        
        def failing_generate(*args, **kwargs):
            attempt_times.append(time.time())
            raise ConnectionError("Service unavailable")
        
        mock_client.generate.side_effect = failing_generate
        
        question = Question(
            number=1,
            text="Test question",
            options=[QuestionOption(label="A", text="Option A")],
            page_number=1,
            question_type="factual"
        )
        
        # Attempt to solve (should retry 2 times)
        result = solver.solve_question(question)
        
        # Verify result marked as error
        assert result.status == "solver_error"
        assert "error" in result.error_message.lower()
        
        # Verify exponential backoff (3 attempts total: initial + 2 retries)
        assert len(attempt_times) == 3
        
        # Check backoff delays (approximately 2^0, 2^1, 2^2 seconds)
        if len(attempt_times) >= 2:
            delay1 = attempt_times[1] - attempt_times[0]
            assert delay1 >= 1.8  # ~2 seconds with tolerance
        
        if len(attempt_times) >= 3:
            delay2 = attempt_times[2] - attempt_times[1]
            assert delay2 >= 3.8  # ~4 seconds with tolerance


class TestPageConversionRecovery:
    """Test recovery from PDF page conversion failures"""
    
    @patch('question_parser.fitz')
    def test_page_conversion_failure_recovery(self, mock_fitz, session_manager):
        """Test that page conversion failures are handled gracefully (Req 10.5)"""
        parser = QuestionParser()
        
        # Mock PyMuPDF with page conversion failure
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 5
        
        def get_page(index):
            if index == 2:  # Page 3 fails
                raise RuntimeError("Page conversion failed")
            mock_page = MagicMock()
            mock_page.get_pixmap.return_value = MagicMock(tobytes=lambda: b'image_data')
            mock_page.get_text.return_value = f"Question {index+1}\nA) Option A\nB) Option B"
            return mock_page
        
        mock_doc.__getitem__.side_effect = get_page
        mock_fitz.open.return_value = mock_doc
        
        # Extract questions
        questions = parser.extract_questions('/tmp/test.pdf')
        
        # Should skip page 3 but continue with others
        # Questions from pages 1, 2, 4, 5 should be extracted
        assert len(questions) >= 3  # At least some questions extracted
        
        # Verify no questions from page 3
        page_numbers = [q.page_number for q in questions]
        assert 3 not in page_numbers or len([p for p in page_numbers if p == 3]) == 0
    
    @patch('question_parser.fitz')
    def test_partial_extraction_with_errors(self, mock_fitz):
        """Test that extraction continues after individual question parse failures (Req 2.6, 10.2)"""
        parser = QuestionParser()
        
        # Mock document with some malformed questions
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3
        
        def get_page(index):
            mock_page = MagicMock()
            if index == 1:  # Page 2 has malformed content
                mock_page.get_text.return_value = "Malformed content without proper structure"
            else:
                mock_page.get_text.return_value = f"Question {index+1}\nA) Option A\nB) Option B"
            mock_page.get_pixmap.return_value = MagicMock(tobytes=lambda: b'image_data')
            return mock_page
        
        mock_doc.__getitem__.side_effect = get_page
        mock_fitz.open.return_value = mock_doc
        
        # Extract questions
        questions = parser.extract_questions('/tmp/test.pdf')
        
        # Should extract questions from pages 1 and 3, skip malformed page 2
        assert len(questions) >= 1
        
        # Verify questions from valid pages
        valid_pages = [q.page_number for q in questions]
        assert 1 in valid_pages or 3 in valid_pages


class TestTimeoutRecovery:
    """Test recovery from AI solver timeouts"""
    
    @patch('ai_solver.OllamaClient')
    def test_timeout_handling(self, mock_ollama_client):
        """Test that timeouts are enforced and handled (Req 4.6, 4.7)"""
        solver = AISolver()
        
        # Mock Ollama client with slow response
        mock_client = mock_ollama_client.return_value
        def slow_generate(*args, **kwargs):
            time.sleep(35)  # Exceed 30 second timeout
            return {"response": "ANSWER: B\nEXPLANATION: Too slow"}
        
        mock_client.generate.side_effect = slow_generate
        
        question = Question(
            number=1,
            text="Test question",
            options=[QuestionOption(label="A", text="Option A")],
            page_number=1,
            question_type="factual"
        )
        
        start_time = time.time()
        result = solver.solve_question(question)
        elapsed = time.time() - start_time
        
        # Should timeout and mark as timeout status
        assert result.status == "timeout"
        assert elapsed < 35  # Should not wait full 35 seconds
        assert elapsed >= 30  # Should wait at least timeout duration
    
    @patch('session_manager.AISolver')
    def test_continue_after_timeout(
        self, mock_solver, session_manager, sample_questions
    ):
        """Test that processing continues after timeout (Req 4.7)"""
        # Create session
        session_id = session_manager.create_session('/tmp/test.pdf')
        session = session_manager.get_session(session_id)
        session.questions = sample_questions
        session.total_questions = len(sample_questions)
        
        # Mock solver with timeout on question 3
        def solve_with_timeout(question):
            if question.number == 3:
                return SolverResult(
                    question.number, None, "", 0.0, 30000, "timeout"
                )
            return SolverResult(
                question.number, "B", "Answer", 0.9, 500, "solved"
            )
        
        mock_solver_instance = mock_solver.return_value
        mock_solver_instance.solve_question.side_effect = solve_with_timeout
        
        # Start processing
        session_manager.start_processing(session_id)
        time.sleep(5)
        
        # Verify processing continued after timeout
        session = session_manager.get_session(session_id)
        assert session.results[3].status == "timeout"
        assert session.results[4].status == "solved"
        assert session.results[5].status == "solved"
        assert session.status == "completed"


class TestSessionRecovery:
    """Test session recovery after crashes"""
    
    def test_session_persistence_and_recovery(self, session_manager, sample_questions):
        """Test that sessions can be recovered after crash (Req 10.7)"""
        # Create and start session
        session_id = session_manager.create_session('/tmp/test.pdf')
        session = session_manager.get_session(session_id)
        session.questions = sample_questions
        session.total_questions = len(sample_questions)
        session.status = "processing"
        
        # Process some questions
        for i in range(1, 4):
            session.results[i] = SolverResult(
                i, "B", "Answer", 0.9, 500, "solved"
            )
            session.processed_count = i
        
        # Save session state
        session_manager.save_session(session_id)
        
        # Simulate crash - clear in-memory state
        session_manager.active_sessions.clear()
        
        # Recover session
        recovered_session = session_manager.load_session(session_id)
        
        # Verify recovered state
        assert recovered_session is not None
        assert recovered_session.session_id == session_id
        assert recovered_session.total_questions == 5
        assert recovered_session.processed_count == 3
        assert len(recovered_session.results) == 3
        assert recovered_session.results[1].status == "solved"
        assert recovered_session.results[2].status == "solved"
        assert recovered_session.results[3].status == "solved"
    
    def test_resume_from_checkpoint(self, session_manager, sample_questions):
        """Test resuming from checkpoint after interruption (Req 9.4, 10.7)"""
        # Create session with partial results
        session_id = session_manager.create_session('/tmp/test.pdf')
        session = session_manager.get_session(session_id)
        session.questions = sample_questions
        session.total_questions = len(sample_questions)
        session.status = "paused"
        session.processed_count = 3
        
        # Add partial results
        for i in range(1, 4):
            session.results[i] = SolverResult(
                i, "B", "Answer", 0.9, 500, "solved"
            )
        
        # Save checkpoint
        session_manager.save_session(session_id)
        
        # Resume processing
        with patch('session_manager.AISolver') as mock_solver:
            mock_solver_instance = mock_solver.return_value
            mock_solver_instance.solve_question.return_value = SolverResult(
                4, "B", "Answer", 0.9, 500, "solved"
            )
            
            session_manager.resume_session(session_id)
            time.sleep(3)
            
            # Verify resumed from checkpoint
            session = session_manager.get_session(session_id)
            assert session.processed_count >= 4
            assert 4 in session.results
    
    def test_error_log_persistence(self, session_manager, sample_questions):
        """Test that error logs are maintained and accessible (Req 10.6)"""
        # Create session
        session_id = session_manager.create_session('/tmp/test.pdf')
        session = session_manager.get_session(session_id)
        session.questions = sample_questions
        session.total_questions = len(sample_questions)
        
        # Add some errors
        session.results[2] = SolverResult(
            2, None, "", 0.0, 500, "solver_error",
            error_message="Connection failed"
        )
        session.results[4] = SolverResult(
            4, None, "", 0.0, 30000, "timeout",
            error_message="Processing timeout"
        )
        session.error_count = 2
        
        # Save session
        session_manager.save_session(session_id)
        
        # Verify error log exists
        session_dir = Path(f'backend/solver_sessions/{session_id}')
        assert session_dir.exists()
        
        # Load and verify errors are preserved
        recovered = session_manager.load_session(session_id)
        assert recovered.error_count == 2
        assert recovered.results[2].status == "solver_error"
        assert recovered.results[4].status == "timeout"
        assert "Connection failed" in recovered.results[2].error_message
        assert "timeout" in recovered.results[4].error_message.lower()


class TestCriticalErrorHandling:
    """Test handling of critical system errors"""
    
    @patch('session_manager.SessionManager.save_session')
    def test_save_partial_results_on_critical_error(
        self, mock_save, session_manager, sample_questions
    ):
        """Test that partial results are saved on critical errors (Req 10.7)"""
        # Create session
        session_id = session_manager.create_session('/tmp/test.pdf')
        session = session_manager.get_session(session_id)
        session.questions = sample_questions
        session.total_questions = len(sample_questions)
        
        # Process some questions
        for i in range(1, 3):
            session.results[i] = SolverResult(
                i, "B", "Answer", 0.9, 500, "solved"
            )
            session.processed_count = i
        
        # Simulate critical error during processing
        with patch('session_manager.AISolver') as mock_solver:
            mock_solver_instance = mock_solver.return_value
            mock_solver_instance.solve_question.side_effect = MemoryError("Out of memory")
            
            try:
                session_manager.start_processing(session_id)
                time.sleep(2)
            except MemoryError:
                pass
            
            # Verify save was called to preserve partial results
            assert mock_save.called
    
    def test_graceful_degradation_on_disk_full(self, session_manager):
        """Test graceful handling when disk is full"""
        session_id = session_manager.create_session('/tmp/test.pdf')
        
        # Mock disk full error
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            try:
                session_manager.save_session(session_id)
            except OSError as e:
                # Should handle gracefully
                assert "space" in str(e).lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
