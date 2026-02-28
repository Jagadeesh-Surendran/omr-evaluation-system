"""
Basic tests for Session Manager module.
"""
import pytest
import os
import tempfile
import shutil
from session_manager import SessionManager, SessionState


class TestSessionManagerBasic:
    """Basic tests for SessionManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directory for test sessions
        self.test_dir = tempfile.mkdtemp()
        self.manager = SessionManager()
        # Override sessions directory for testing
        self.manager.sessions_dir = self.test_dir
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_create_session(self):
        """Test session creation."""
        # Create a temporary PDF file
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        # Create session
        session_id = self.manager.create_session(pdf_path)
        
        # Verify session was created
        assert session_id is not None
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
    
    def test_create_session_invalid_path(self):
        """Test session creation with invalid PDF path."""
        with pytest.raises(FileNotFoundError):
            self.manager.create_session("/nonexistent/path.pdf")
    
    def test_get_session(self):
        """Test retrieving session."""
        # Create a temporary PDF file
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        # Create session
        session_id = self.manager.create_session(pdf_path)
        
        # Get session
        session = self.manager.get_session(session_id)
        assert session is not None
        assert session.session_id == session_id
        
        # Get non-existent session
        session = self.manager.get_session("nonexistent")
        assert session is None
    
    def test_update_answer(self):
        """Test manual answer correction."""
        # Create a temporary PDF file
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        # Create session
        session_id = self.manager.create_session(pdf_path)
        
        # Add a dummy result
        from ai_solver import SolverResult
        session = self.manager.get_session(session_id)
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
        
        # Verify update
        session = self.manager.get_session(session_id)
        assert session.results[1].selected_option == "B"
        assert session.results[1].confidence == 1.0
        assert 1 in session.user_corrections
        assert session.user_corrections[1] == "B"
    
    def test_update_answer_invalid_option(self):
        """Test updating answer with invalid option."""
        # Create a temporary PDF file
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        # Create session
        session_id = self.manager.create_session(pdf_path)
        
        # Add a dummy result
        from ai_solver import SolverResult
        session = self.manager.get_session(session_id)
        session.results[1] = SolverResult(
            question_number=1,
            selected_option="A",
            explanation="Original answer",
            confidence=0.5,
            processing_time_ms=1000,
            status="solved"
        )
        
        # Try to update with invalid option
        success = self.manager.update_answer(session_id, 1, "Z")
        assert success is False
    
    def test_add_note(self):
        """Test adding user note."""
        # Create a temporary PDF file
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        # Create session
        session_id = self.manager.create_session(pdf_path)
        
        # Add a dummy question
        from question_parser import Question, QuestionOption
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
        
        # Add note
        success = self.manager.add_note(session_id, 1, "This is a test note")
        assert success is True
        
        # Verify note
        session = self.manager.get_session(session_id)
        assert 1 in session.user_notes
        assert session.user_notes[1] == "This is a test note"
    
    def test_cancel_session(self):
        """Test cancelling session."""
        # Create a temporary PDF file
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        # Create session
        session_id = self.manager.create_session(pdf_path)
        
        # Cancel session
        success = self.manager.cancel_session(session_id)
        assert success is True
        
        # Verify session was removed
        assert session_id not in self.manager.active_sessions
        assert session_id not in self.manager.session_locks
    
    def test_save_and_load_session(self):
        """Test session persistence."""
        # Create a temporary PDF file
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        # Create session
        session_id = self.manager.create_session(pdf_path)
        
        # Add some data
        session = self.manager.get_session(session_id)
        session.status = "completed"
        session.total_questions = 10
        session.processed_count = 10
        session.solved_count = 8
        session.unsolvable_count = 1
        session.error_count = 1
        
        # Save session
        self.manager.save_session(session_id)
        
        # Remove from active sessions
        del self.manager.active_sessions[session_id]
        
        # Load session
        loaded_session = self.manager.load_session(session_id)
        
        # Verify loaded data
        assert loaded_session is not None
        assert loaded_session.session_id == session_id
        assert loaded_session.status == "completed"
        assert loaded_session.total_questions == 10
        assert loaded_session.processed_count == 10
        assert loaded_session.solved_count == 8
        assert loaded_session.unsolvable_count == 1
        assert loaded_session.error_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
