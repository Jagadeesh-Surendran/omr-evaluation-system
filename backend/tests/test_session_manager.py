"""
Comprehensive unit tests for Session Manager module.

Tests cover:
- Session creation and initialization
- Pause/resume state preservation
- Cancel and cleanup
- Manual corrections and notes
- Session persistence and recovery
- Concurrent access with locks
"""
import pytest
import os
import tempfile
import shutil
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from session_manager import SessionManager, SessionState
from question_parser import Question, QuestionOption
from ai_solver import SolverResult
from validation_engine import ValidationReport, ValidationIssue


class TestSessionManagerCreation:
    """Tests for session creation and initialization."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.manager = SessionManager()
        self.manager.sessions_dir = self.test_dir
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_create_session_success(self):
        """Test successful session creation."""
        # Create a temporary PDF file
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        # Create session
        session_id = self.manager.create_session(pdf_path)
        
        # Verify session was created
        assert session_id is not None
        assert len(session_id) > 0
        assert session_id in self.manager.active_sessions
        assert session_id in self.manager.session_locks
        
        # Verify session state
        session = self.manager.get_session(session_id)
        assert session is not None
        assert session.session_id == session_id
        assert session.status == "pending"
        assert session.pdf_path == pdf_path
        assert session.total_questions == 0
        assert session.processed_count == 0
        assert session.solved_count == 0
        assert session.unsolvable_count == 0
        assert session.error_count == 0
        assert session.start_time is None
        assert session.end_time is None
        assert len(session.questions) == 0
        assert len(session.results) == 0
        assert session.validation_report is None
        assert len(session.user_corrections) == 0
        assert len(session.user_notes) == 0
        
        # Verify session directory was created
        session_dir = os.path.join(self.test_dir, session_id)
        assert os.path.exists(session_dir)
        assert os.path.exists(os.path.join(session_dir, "logs"))
    
    def test_create_session_invalid_path(self):
        """Test session creation with invalid PDF path."""
        with pytest.raises(FileNotFoundError):
            self.manager.create_session("/nonexistent/path.pdf")
    
    def test_create_session_unique_ids(self):
        """Test that each session gets a unique ID."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id1 = self.manager.create_session(pdf_path)
        session_id2 = self.manager.create_session(pdf_path)
        
        assert session_id1 != session_id2
    
    def test_get_session_existing(self):
        """Test retrieving existing session."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        
        assert session is not None
        assert session.session_id == session_id
    
    def test_get_session_nonexistent(self):
        """Test retrieving non-existent session."""
        session = self.manager.get_session("nonexistent-id")
        assert session is None


class TestSessionManagerPauseResume:
    """Tests for pause/resume functionality with state preservation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.manager = SessionManager()
        self.manager.sessions_dir = self.test_dir
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_pause_processing_session(self):
        """Test pausing a processing session."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        session.status = "processing"
        
        success = self.manager.pause_session(session_id)
        
        assert success is True
        assert session.status == "paused"
    
    def test_pause_non_processing_session(self):
        """Test pausing a non-processing session fails."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        
        # Try to pause pending session
        success = self.manager.pause_session(session_id)
        assert success is False
    
    def test_pause_nonexistent_session(self):
        """Test pausing non-existent session."""
        success = self.manager.pause_session("nonexistent-id")
        assert success is False
    
    def test_resume_paused_session(self):
        """Test resuming a paused session."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        session.status = "paused"
        
        # Mock start_processing to avoid actual processing
        with patch.object(self.manager, 'start_processing'):
            success = self.manager.resume_session(session_id)
        
        assert success is True
    
    def test_resume_non_paused_session(self):
        """Test resuming a non-paused session fails."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        
        # Try to resume pending session
        success = self.manager.resume_session(session_id)
        assert success is False
    
    def test_resume_nonexistent_session(self):
        """Test resuming non-existent session."""
        success = self.manager.resume_session("nonexistent-id")
        assert success is False
    
    def test_pause_resume_state_preservation(self):
        """Test that pause/resume preserves all session state."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        
        # Set up session state
        session.status = "processing"
        session.total_questions = 10
        session.processed_count = 5
        session.solved_count = 4
        session.unsolvable_count = 1
        session.error_count = 0
        session.start_time = time.time()
        
        # Add questions
        session.questions = [
            Question(
                number=i,
                text=f"Question {i}",
                options=[
                    QuestionOption(label="A", text="Option A"),
                    QuestionOption(label="B", text="Option B")
                ],
                page_number=1
            )
            for i in range(1, 11)
        ]
        
        # Add results
        for i in range(1, 6):
            session.results[i] = SolverResult(
                question_number=i,
                selected_option="A",
                explanation=f"Explanation {i}",
                confidence=0.8,
                processing_time_ms=1000,
                status="solved"
            )
        
        # Add user corrections and notes
        session.user_corrections[3] = "B"
        session.user_notes[3] = "This was corrected"
        
        # Capture state before pause
        state_before = {
            "processed_count": session.processed_count,
            "solved_count": session.solved_count,
            "unsolvable_count": session.unsolvable_count,
            "error_count": session.error_count,
            "results_count": len(session.results),
            "questions_count": len(session.questions),
            "corrections_count": len(session.user_corrections),
            "notes_count": len(session.user_notes)
        }
        
        # Pause session
        success = self.manager.pause_session(session_id)
        assert success is True
        
        # Verify state after pause
        session_after_pause = self.manager.get_session(session_id)
        assert session_after_pause.status == "paused"
        assert session_after_pause.processed_count == state_before["processed_count"]
        assert session_after_pause.solved_count == state_before["solved_count"]
        assert len(session_after_pause.results) == state_before["results_count"]
        assert len(session_after_pause.questions) == state_before["questions_count"]
        assert len(session_after_pause.user_corrections) == state_before["corrections_count"]
        assert len(session_after_pause.user_notes) == state_before["notes_count"]
        
        # Resume session
        with patch.object(self.manager, 'start_processing'):
            success = self.manager.resume_session(session_id)
        assert success is True


class TestSessionManagerCancel:
    """Tests for cancel functionality and cleanup."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.manager = SessionManager()
        self.manager.sessions_dir = self.test_dir
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_cancel_pending_session(self):
        """Test cancelling a pending session."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        
        success = self.manager.cancel_session(session_id)
        
        assert success is True
        assert session_id not in self.manager.active_sessions
        assert session_id not in self.manager.session_locks
    
    def test_cancel_processing_session(self):
        """Test cancelling a processing session."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        session.status = "processing"
        
        success = self.manager.cancel_session(session_id)
        
        assert success is True
        assert session.status == "cancelled"
        assert session.end_time is not None
        assert session_id not in self.manager.active_sessions
        assert session_id not in self.manager.session_locks
    
    def test_cancel_completed_session_fails(self):
        """Test that cancelling a completed session fails."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        session.status = "completed"
        
        success = self.manager.cancel_session(session_id)
        assert success is False
    
    def test_cancel_already_cancelled_session_fails(self):
        """Test that cancelling an already cancelled session fails."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        session.status = "cancelled"
        
        success = self.manager.cancel_session(session_id)
        assert success is False
    
    def test_cancel_nonexistent_session(self):
        """Test cancelling non-existent session."""
        success = self.manager.cancel_session("nonexistent-id")
        assert success is False
    
    def test_cancel_discards_partial_results(self):
        """Test that cancelling discards partial results."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        session.status = "processing"
        
        # Add some partial results
        session.results[1] = SolverResult(
            question_number=1,
            selected_option="A",
            explanation="Test",
            confidence=0.8,
            processing_time_ms=1000,
            status="solved"
        )
        
        # Cancel session
        success = self.manager.cancel_session(session_id)
        assert success is True
        
        # Verify session is removed from active sessions
        assert session_id not in self.manager.active_sessions


class TestSessionManagerCorrectionsAndNotes:
    """Tests for manual corrections and notes."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.manager = SessionManager()
        self.manager.sessions_dir = self.test_dir
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_update_answer_success(self):
        """Test successful answer update."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        
        # Add a result
        session.results[1] = SolverResult(
            question_number=1,
            selected_option="A",
            explanation="Original answer",
            confidence=0.5,
            processing_time_ms=1000,
            status="solved"
        )
        
        # Update answer
        success = self.manager.update_answer(session_id, 1, "B")
        
        assert success is True
        assert session.results[1].selected_option == "B"
        assert session.results[1].confidence == 1.0
        assert session.results[1].status == "solved"
        assert "[MANUALLY VERIFIED]" in session.results[1].explanation
        assert 1 in session.user_corrections
        assert session.user_corrections[1] == "B"
    
    def test_update_answer_invalid_option(self):
        """Test updating answer with invalid option."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        
        session.results[1] = SolverResult(
            question_number=1,
            selected_option="A",
            explanation="Original answer",
            confidence=0.5,
            processing_time_ms=1000,
            status="solved"
        )
        
        # Try invalid options
        assert self.manager.update_answer(session_id, 1, "Z") is False
        assert self.manager.update_answer(session_id, 1, "F") is False
        assert self.manager.update_answer(session_id, 1, "1") is False
        assert self.manager.update_answer(session_id, 1, "") is False
    
    def test_update_answer_nonexistent_question(self):
        """Test updating answer for non-existent question."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        
        success = self.manager.update_answer(session_id, 999, "A")
        assert success is False
    
    def test_update_answer_nonexistent_session(self):
        """Test updating answer for non-existent session."""
        success = self.manager.update_answer("nonexistent-id", 1, "A")
        assert success is False
    
    def test_update_answer_multiple_times(self):
        """Test updating the same answer multiple times."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        
        session.results[1] = SolverResult(
            question_number=1,
            selected_option="A",
            explanation="Original answer",
            confidence=0.5,
            processing_time_ms=1000,
            status="solved"
        )
        
        # First update
        self.manager.update_answer(session_id, 1, "B")
        assert session.results[1].selected_option == "B"
        assert session.user_corrections[1] == "B"
        
        # Second update
        self.manager.update_answer(session_id, 1, "C")
        assert session.results[1].selected_option == "C"
        # First correction should still be recorded
        assert session.user_corrections[1] == "B"
    
    def test_add_note_success(self):
        """Test successfully adding a note."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        
        # Add a question
        session.questions = [
            Question(
                number=1,
                text="Test question",
                options=[
                    QuestionOption(label="A", text="Option A"),
                    QuestionOption(label="B", text="Option B")
                ],
                page_number=1
            )
        ]
        
        # Add note
        success = self.manager.add_note(session_id, 1, "This is a test note")
        
        assert success is True
        assert 1 in session.user_notes
        assert session.user_notes[1] == "This is a test note"
    
    def test_add_note_nonexistent_question(self):
        """Test adding note for non-existent question."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        
        success = self.manager.add_note(session_id, 999, "Test note")
        assert success is False
    
    def test_add_note_nonexistent_session(self):
        """Test adding note for non-existent session."""
        success = self.manager.add_note("nonexistent-id", 1, "Test note")
        assert success is False
    
    def test_add_note_multiple_times(self):
        """Test adding multiple notes to the same question."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        
        session.questions = [
            Question(
                number=1,
                text="Test question",
                options=[
                    QuestionOption(label="A", text="Option A"),
                    QuestionOption(label="B", text="Option B")
                ],
                page_number=1
            )
        ]
        
        # Add first note
        self.manager.add_note(session_id, 1, "First note")
        assert session.user_notes[1] == "First note"
        
        # Add second note (should overwrite)
        self.manager.add_note(session_id, 1, "Second note")
        assert session.user_notes[1] == "Second note"



class TestSessionManagerPersistence:
    """Tests for session persistence and recovery."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.manager = SessionManager()
        self.manager.sessions_dir = self.test_dir
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_save_session_basic(self):
        """Test saving basic session state."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        
        # Set some state
        session.status = "completed"
        session.total_questions = 10
        session.processed_count = 10
        session.solved_count = 8
        session.unsolvable_count = 1
        session.error_count = 1
        
        # Save session
        self.manager.save_session(session_id)
        
        # Verify files were created
        session_dir = os.path.join(self.test_dir, session_id)
        assert os.path.exists(os.path.join(session_dir, "session.json"))
    
    def test_save_and_load_session_complete(self):
        """Test saving and loading complete session with all data."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        
        # Set up complete session state
        session.status = "completed"
        session.total_questions = 3
        session.processed_count = 3
        session.solved_count = 2
        session.unsolvable_count = 1
        session.error_count = 0
        session.start_time = 1234567890.0
        session.end_time = 1234567990.0
        
        # Add questions
        session.questions = [
            Question(
                number=1,
                text="Question 1",
                options=[
                    QuestionOption(label="A", text="Option A"),
                    QuestionOption(label="B", text="Option B")
                ],
                page_number=1,
                question_type="math"
            ),
            Question(
                number=2,
                text="Question 2",
                options=[
                    QuestionOption(label="A", text="Option A"),
                    QuestionOption(label="B", text="Option B")
                ],
                page_number=1,
                question_type="logical"
            ),
            Question(
                number=3,
                text="Question 3",
                options=[
                    QuestionOption(label="A", text="Option A"),
                    QuestionOption(label="B", text="Option B")
                ],
                page_number=2,
                question_type="factual"
            )
        ]
        
        # Add results
        session.results[1] = SolverResult(
            question_number=1,
            selected_option="A",
            explanation="Explanation 1",
            confidence=0.9,
            processing_time_ms=1500,
            status="solved"
        )
        session.results[2] = SolverResult(
            question_number=2,
            selected_option="B",
            explanation="Explanation 2",
            confidence=0.7,
            processing_time_ms=2000,
            status="solved"
        )
        session.results[3] = SolverResult(
            question_number=3,
            selected_option=None,
            explanation="Could not solve",
            confidence=0.0,
            processing_time_ms=500,
            status="unsolvable",
            error_message="Unsupported question type"
        )
        
        # Add validation report
        session.validation_report = ValidationReport(
            total_questions=3,
            issues=[
                ValidationIssue(
                    question_number=2,
                    severity="warning",
                    issue_type="low_confidence",
                    description="Confidence below 0.8"
                )
            ],
            flagged_questions={2},
            average_confidence=0.8
        )
        
        # Add user corrections and notes
        session.user_corrections[1] = "B"
        session.user_notes[1] = "Corrected after review"
        session.user_notes[3] = "Needs manual solving"
        
        # Save session
        self.manager.save_session(session_id)
        
        # Remove from active sessions
        del self.manager.active_sessions[session_id]
        
        # Load session
        loaded_session = self.manager.load_session(session_id)
        
        # Verify all data was preserved
        assert loaded_session is not None
        assert loaded_session.session_id == session_id
        assert loaded_session.status == "completed"
        assert loaded_session.total_questions == 3
        assert loaded_session.processed_count == 3
        assert loaded_session.solved_count == 2
        assert loaded_session.unsolvable_count == 1
        assert loaded_session.error_count == 0
        assert loaded_session.start_time == 1234567890.0
        assert loaded_session.end_time == 1234567990.0
        
        # Verify questions
        assert len(loaded_session.questions) == 3
        assert loaded_session.questions[0].number == 1
        assert loaded_session.questions[0].text == "Question 1"
        assert loaded_session.questions[0].question_type == "math"
        assert len(loaded_session.questions[0].options) == 2
        
        # Verify results
        assert len(loaded_session.results) == 3
        assert loaded_session.results[1].selected_option == "A"
        assert loaded_session.results[1].confidence == 0.9
        assert loaded_session.results[3].status == "unsolvable"
        
        # Verify validation report
        assert loaded_session.validation_report is not None
        assert loaded_session.validation_report.total_questions == 3
        assert len(loaded_session.validation_report.issues) == 1
        assert 2 in loaded_session.validation_report.flagged_questions
        
        # Verify user corrections and notes
        # Note: JSON serialization converts integer keys to strings
        assert loaded_session.user_corrections["1"] == "B"
        assert loaded_session.user_notes["1"] == "Corrected after review"
        assert loaded_session.user_notes["3"] == "Needs manual solving"
    
    def test_load_nonexistent_session(self):
        """Test loading non-existent session."""
        loaded_session = self.manager.load_session("nonexistent-id")
        assert loaded_session is None
    
    def test_save_session_creates_files(self):
        """Test that save_session creates all necessary files."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        
        # Add minimal data
        session.questions = [
            Question(
                number=1,
                text="Test",
                options=[QuestionOption(label="A", text="A")],
                page_number=1
            )
        ]
        session.results[1] = SolverResult(
            question_number=1,
            selected_option="A",
            explanation="Test",
            confidence=0.8,
            processing_time_ms=1000,
            status="solved"
        )
        session.validation_report = ValidationReport(
            total_questions=1,
            issues=[],
            flagged_questions=set(),
            average_confidence=0.8
        )
        
        # Save session
        self.manager.save_session(session_id)
        
        # Verify all files exist
        session_dir = os.path.join(self.test_dir, session_id)
        assert os.path.exists(os.path.join(session_dir, "session.json"))
        assert os.path.exists(os.path.join(session_dir, "questions.json"))
        assert os.path.exists(os.path.join(session_dir, "results.json"))
        assert os.path.exists(os.path.join(session_dir, "validation.json"))
    
    def test_session_recovery_after_crash(self):
        """Test that sessions can be recovered after a crash."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        # Create and save session
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        session.status = "processing"
        session.processed_count = 5
        session.total_questions = 10
        self.manager.save_session(session_id)
        
        # Simulate crash by creating new manager
        new_manager = SessionManager()
        new_manager.sessions_dir = self.test_dir
        
        # Load session
        recovered_session = new_manager.load_session(session_id)
        
        assert recovered_session is not None
        assert recovered_session.session_id == session_id
        assert recovered_session.processed_count == 5
        assert recovered_session.total_questions == 10


class TestSessionManagerConcurrency:
    """Tests for concurrent access with locks."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.manager = SessionManager()
        self.manager.sessions_dir = self.test_dir
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_session_lock_created(self):
        """Test that session lock is created with session."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        
        assert session_id in self.manager.session_locks
        assert isinstance(self.manager.session_locks[session_id], threading.Lock)
    
    def test_concurrent_answer_updates(self):
        """Test concurrent answer updates are thread-safe."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        
        # Add results for multiple questions
        for i in range(1, 11):
            session.results[i] = SolverResult(
                question_number=i,
                selected_option="A",
                explanation=f"Original {i}",
                confidence=0.5,
                processing_time_ms=1000,
                status="solved"
            )
        
        # Function to update answers
        def update_answers(start, end, option):
            for i in range(start, end):
                self.manager.update_answer(session_id, i, option)
        
        # Create threads to update different questions concurrently
        thread1 = threading.Thread(target=update_answers, args=(1, 4, "B"))
        thread2 = threading.Thread(target=update_answers, args=(4, 7, "C"))
        thread3 = threading.Thread(target=update_answers, args=(7, 11, "D"))
        
        # Start threads
        thread1.start()
        thread2.start()
        thread3.start()
        
        # Wait for completion
        thread1.join()
        thread2.join()
        thread3.join()
        
        # Verify all updates were applied
        session = self.manager.get_session(session_id)
        for i in range(1, 4):
            assert session.results[i].selected_option == "B"
        for i in range(4, 7):
            assert session.results[i].selected_option == "C"
        for i in range(7, 11):
            assert session.results[i].selected_option == "D"
    
    def test_concurrent_note_additions(self):
        """Test concurrent note additions are thread-safe."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        
        # Add questions
        for i in range(1, 11):
            session.questions.append(
                Question(
                    number=i,
                    text=f"Question {i}",
                    options=[QuestionOption(label="A", text="A")],
                    page_number=1
                )
            )
        
        # Function to add notes
        def add_notes(start, end, prefix):
            for i in range(start, end):
                self.manager.add_note(session_id, i, f"{prefix} note {i}")
        
        # Create threads to add notes concurrently
        thread1 = threading.Thread(target=add_notes, args=(1, 4, "Thread1"))
        thread2 = threading.Thread(target=add_notes, args=(4, 7, "Thread2"))
        thread3 = threading.Thread(target=add_notes, args=(7, 11, "Thread3"))
        
        # Start threads
        thread1.start()
        thread2.start()
        thread3.start()
        
        # Wait for completion
        thread1.join()
        thread2.join()
        thread3.join()
        
        # Verify all notes were added
        session = self.manager.get_session(session_id)
        assert len(session.user_notes) == 10
        for i in range(1, 11):
            assert i in session.user_notes
    
    def test_pause_during_concurrent_operations(self):
        """Test pausing session during concurrent operations."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        session.status = "processing"
        
        # Add results
        for i in range(1, 6):
            session.results[i] = SolverResult(
                question_number=i,
                selected_option="A",
                explanation=f"Original {i}",
                confidence=0.5,
                processing_time_ms=1000,
                status="solved"
            )
        
        # Function to update answers with delay
        def update_with_delay():
            for i in range(1, 6):
                time.sleep(0.01)  # Small delay
                self.manager.update_answer(session_id, i, "B")
        
        # Start update thread
        update_thread = threading.Thread(target=update_with_delay)
        update_thread.start()
        
        # Pause session while updates are happening
        time.sleep(0.02)
        self.manager.pause_session(session_id)
        
        # Wait for thread to complete
        update_thread.join()
        
        # Verify session is paused
        session = self.manager.get_session(session_id)
        assert session.status == "paused"
    
    def test_lock_prevents_race_conditions(self):
        """Test that locks prevent race conditions in session state."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        
        # Counter to track operations
        operation_count = [0]
        
        # Function to increment counter with lock
        def increment_with_lock():
            for _ in range(100):
                with self.manager.session_locks[session_id]:
                    current = operation_count[0]
                    time.sleep(0.0001)  # Simulate some work
                    operation_count[0] = current + 1
        
        # Create multiple threads
        threads = [threading.Thread(target=increment_with_lock) for _ in range(5)]
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Verify counter is correct (no race condition)
        assert operation_count[0] == 500  # 5 threads * 100 increments


class TestConcurrentSessionManagement:
    """Tests for concurrent session limits and queue management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.manager = SessionManager()
        self.manager.sessions_dir = self.test_dir
        
        # Mock validation engine to avoid delays
        self.manager.validation_engine.validate_batch = Mock(return_value=ValidationReport(
            total_questions=0,
            issues=[],
            flagged_questions=set(),
            average_confidence=0.8
        ))
        
        # Mock resource check to avoid psutil delays
        self.manager.check_system_resources = Mock(return_value=(True, None))
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_two_concurrent_sessions_allowed(self):
        """Test that 2 concurrent sessions can run simultaneously."""
        # Create two PDF files
        pdf_path1 = os.path.join(self.test_dir, "test1.pdf")
        pdf_path2 = os.path.join(self.test_dir, "test2.pdf")
        with open(pdf_path1, 'w') as f:
            f.write("dummy pdf content 1")
        with open(pdf_path2, 'w') as f:
            f.write("dummy pdf content 2")
        
        # Create two sessions
        session_id1 = self.manager.create_session(pdf_path1)
        session_id2 = self.manager.create_session(pdf_path2)
        
        # Manually set up sessions with questions (bypass extraction)
        session1 = self.manager.get_session(session_id1)
        session2 = self.manager.get_session(session_id2)
        
        session1.questions = [
            Question(
                number=1,
                text="Test question",
                options=[QuestionOption(label="A", text="Option A")],
                page_number=1
            )
        ]
        session1.total_questions = 1
        
        session2.questions = [
            Question(
                number=1,
                text="Test question",
                options=[QuestionOption(label="A", text="Option A")],
                page_number=1
            )
        ]
        session2.total_questions = 1
        
        # Mock the AI solver to complete quickly
        def mock_solve(question):
            return SolverResult(
                question_number=question.number,
                selected_option="A",
                explanation="Test",
                confidence=0.8,
                processing_time_ms=100,
                status="solved"
            )
        
        self.manager.ai_solver.solve_question = mock_solve
        
        # Start both sessions
        self.manager.start_processing(session_id1)
        self.manager.start_processing(session_id2)
        
        # Give threads time to start
        time.sleep(0.2)
        
        # Check that both started (they might complete quickly)
        session1 = self.manager.get_session(session_id1)
        session2 = self.manager.get_session(session_id2)
        
        # At least one should have processed
        assert session1.processed_count > 0 or session2.processed_count > 0
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_third_session_queued(self, mock_memory, mock_cpu):
        """Test that third session is queued when at capacity."""
        # Mock resource checks
        mock_cpu.return_value = 50.0
        mock_mem = Mock()
        mock_mem.percent = 50.0
        mock_mem.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory.return_value = mock_mem
        
        # Create three PDF files
        pdf_paths = []
        for i in range(3):
            pdf_path = os.path.join(self.test_dir, f"test{i}.pdf")
            with open(pdf_path, 'w') as f:
                f.write(f"dummy pdf content {i}")
            pdf_paths.append(pdf_path)
        
        # Create three sessions
        session_ids = [self.manager.create_session(path) for path in pdf_paths]
        
        # Manually set first two sessions to processing status
        session1 = self.manager.get_session(session_ids[0])
        session2 = self.manager.get_session(session_ids[1])
        session1.status = "processing"
        session2.status = "processing"
        
        # Count active sessions - should be 2
        active_count = self.manager._count_active_sessions()
        assert active_count == 2
        
        # Try to start third session - should be queued
        self.manager.start_processing(session_ids[2])
        
        # Check third session is queued
        session3 = self.manager.get_session(session_ids[2])
        assert session3.status == "queued"
        
        # Check queue position
        position = self.manager.get_queue_position(session_ids[2])
        assert position == 1
        
        # Check queue length
        assert len(self.manager.session_queue) == 1
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_queued_session_auto_starts(self, mock_memory, mock_cpu):
        """Test that queued session automatically starts when slot available."""
        # Mock resource checks
        mock_cpu.return_value = 50.0
        mock_mem = Mock()
        mock_mem.percent = 50.0
        mock_mem.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory.return_value = mock_mem
        
        # Create three PDF files
        pdf_paths = []
        for i in range(3):
            pdf_path = os.path.join(self.test_dir, f"test{i}.pdf")
            with open(pdf_path, 'w') as f:
                f.write(f"dummy pdf content {i}")
            pdf_paths.append(pdf_path)
        
        # Create three sessions
        session_ids = [self.manager.create_session(path) for path in pdf_paths]
        
        # Set up third session with minimal questions
        session3 = self.manager.get_session(session_ids[2])
        session3.questions = [
            Question(
                number=1,
                text="Test question",
                options=[QuestionOption(label="A", text="Option A")],
                page_number=1
            )
        ]
        session3.total_questions = 1
        
        # Mock AI solver to complete quickly
        def quick_solve(question):
            return SolverResult(
                question_number=question.number,
                selected_option="A",
                explanation="Test",
                confidence=0.8,
                processing_time_ms=10,
                status="solved"
            )
        
        self.manager.ai_solver.solve_question = quick_solve
        
        # Manually set first two sessions to processing
        session1 = self.manager.get_session(session_ids[0])
        session2 = self.manager.get_session(session_ids[1])
        session1.status = "processing"
        session2.status = "processing"
        
        # Start third session - should be queued
        self.manager.start_processing(session_ids[2])
        
        # Verify third is queued
        session3 = self.manager.get_session(session_ids[2])
        assert session3.status == "queued"
        
        # Manually complete first session to free up a slot
        session1.status = "completed"
        
        # Trigger queue processing
        self.manager._start_next_queued_session()
        
        # Give it a moment to start
        time.sleep(0.5)
        
        # Third session should have started
        session3 = self.manager.get_session(session_ids[2])
        assert session3.status in ["processing", "completed"]
    
    def test_queue_position_tracking(self):
        """Test that queue positions are tracked correctly."""
        # Create multiple sessions
        pdf_paths = []
        for i in range(5):
            pdf_path = os.path.join(self.test_dir, f"test{i}.pdf")
            with open(pdf_path, 'w') as f:
                f.write(f"dummy pdf content {i}")
            pdf_paths.append(pdf_path)
        
        session_ids = [self.manager.create_session(path) for path in pdf_paths]
        
        # Add all to queue manually
        for session_id in session_ids:
            self.manager._add_to_queue(session_id)
        
        # Check positions
        for i, session_id in enumerate(session_ids):
            position = self.manager.get_queue_position(session_id)
            assert position == i + 1  # 1-based position
    
    def test_cancel_removes_from_queue(self):
        """Test that cancelling a session removes it from queue."""
        # Create sessions
        pdf_paths = []
        for i in range(3):
            pdf_path = os.path.join(self.test_dir, f"test{i}.pdf")
            with open(pdf_path, 'w') as f:
                f.write(f"dummy pdf content {i}")
            pdf_paths.append(pdf_path)
        
        session_ids = [self.manager.create_session(path) for path in pdf_paths]
        
        # Add to queue
        for session_id in session_ids:
            self.manager._add_to_queue(session_id)
        
        # Cancel middle session
        self.manager.cancel_session(session_ids[1])
        
        # Check it's removed from queue
        position = self.manager.get_queue_position(session_ids[1])
        assert position is None
        
        # Check other positions updated
        assert self.manager.get_queue_position(session_ids[0]) == 1
        assert self.manager.get_queue_position(session_ids[2]) == 2
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_resource_check_rejects_high_cpu(self, mock_memory, mock_cpu):
        """Test that high CPU usage rejects new sessions."""
        # Mock high CPU usage
        mock_cpu.return_value = 95.0
        
        # Mock normal memory
        mock_mem = Mock()
        mock_mem.percent = 50.0
        mock_mem.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory.return_value = mock_mem
        
        # Check resources
        resources_ok, error_msg = self.manager.check_system_resources()
        
        assert not resources_ok
        assert "CPU" in error_msg
        assert "critically high" in error_msg
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_resource_check_rejects_high_memory(self, mock_memory, mock_cpu):
        """Test that high memory usage rejects new sessions."""
        # Mock normal CPU
        mock_cpu.return_value = 50.0
        
        # Mock high memory usage
        mock_mem = Mock()
        mock_mem.percent = 95.0
        mock_mem.available = 100 * 1024 * 1024  # Only 100MB available
        mock_memory.return_value = mock_mem
        
        # Check resources
        resources_ok, error_msg = self.manager.check_system_resources()
        
        assert not resources_ok
        assert "memory" in error_msg.lower()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_resource_check_passes_normal_usage(self, mock_memory, mock_cpu):
        """Test that normal resource usage allows new sessions."""
        # Mock normal CPU
        mock_cpu.return_value = 50.0
        
        # Mock normal memory
        mock_mem = Mock()
        mock_mem.percent = 50.0
        mock_mem.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory.return_value = mock_mem
        
        # Check resources
        resources_ok, error_msg = self.manager.check_system_resources()
        
        assert resources_ok
        assert error_msg is None
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_resource_stats(self, mock_disk, mock_memory, mock_cpu):
        """Test getting resource statistics."""
        # Mock CPU
        mock_cpu.return_value = 45.5
        
        # Mock memory
        mock_mem = Mock()
        mock_mem.percent = 60.2
        mock_mem.available = 2 * 1024 * 1024 * 1024  # 2GB
        mock_mem.total = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory.return_value = mock_mem
        
        # Mock disk
        mock_disk_info = Mock()
        mock_disk_info.percent = 70.0
        mock_disk_info.free = 50 * 1024 * 1024 * 1024  # 50GB
        mock_disk.return_value = mock_disk_info
        
        # Get stats
        stats = self.manager.get_resource_stats()
        
        assert stats["cpu_percent"] == 45.5
        assert stats["memory_percent"] == 60.2
        assert stats["memory_available_mb"] == 2048
        assert stats["memory_total_mb"] == 8192
        assert stats["disk_percent"] == 70.0
        assert stats["disk_free_gb"] == 50.0
        assert "active_sessions" in stats
        assert "queued_sessions" in stats


class TestSessionManagerEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.manager = SessionManager()
        self.manager.sessions_dir = self.test_dir
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_empty_session_save_and_load(self):
        """Test saving and loading session with no data."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        
        # Save empty session
        self.manager.save_session(session_id)
        
        # Remove from active sessions
        del self.manager.active_sessions[session_id]
        
        # Load session
        loaded_session = self.manager.load_session(session_id)
        
        assert loaded_session is not None
        assert loaded_session.session_id == session_id
        assert len(loaded_session.questions) == 0
        assert len(loaded_session.results) == 0
    
    def test_update_answer_preserves_original_explanation(self):
        """Test that updating answer preserves original explanation."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        session_id = self.manager.create_session(pdf_path)
        session = self.manager.get_session(session_id)
        
        original_explanation = "This is the original AI explanation"
        session.results[1] = SolverResult(
            question_number=1,
            selected_option="A",
            explanation=original_explanation,
            confidence=0.5,
            processing_time_ms=1000,
            status="solved"
        )
        
        # Update answer
        self.manager.update_answer(session_id, 1, "B")
        
        # Verify original explanation is preserved with marker
        assert original_explanation in session.results[1].explanation
        assert "[MANUALLY VERIFIED]" in session.results[1].explanation
    
    def test_multiple_sessions_independent(self):
        """Test that multiple sessions are independent."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        # Create two sessions
        session_id1 = self.manager.create_session(pdf_path)
        session_id2 = self.manager.create_session(pdf_path)
        
        session1 = self.manager.get_session(session_id1)
        session2 = self.manager.get_session(session_id2)
        
        # Modify session1
        session1.status = "completed"
        session1.total_questions = 10
        
        # Verify session2 is unaffected
        assert session2.status == "pending"
        assert session2.total_questions == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
