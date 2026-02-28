"""
test_answer_key_generator.py
-----------------------------
Unit tests for answer_key_generator.py module.
Tests the AnswerKeyGenerator class including JSON generation, CSV export,
PDF report generation, metadata extraction, and approval workflow.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import json
import csv
import io

from answer_key_generator import AnswerKeyGenerator, AnswerKeyMetadata
from ai_solver import SolverResult
from question_parser import Question, QuestionOption


# ── Helpers ───────────────────────────────────────────────────────────────────

@dataclass
class MockSessionState:
    """Mock SessionState for testing."""
    session_id: str
    status: str
    pdf_path: str
    total_questions: int = 0
    processed_count: int = 0
    solved_count: int = 0
    unsolvable_count: int = 0
    error_count: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    questions: List[Question] = field(default_factory=list)
    results: Dict[int, SolverResult] = field(default_factory=dict)
    validation_report: Optional[object] = None
    user_corrections: Dict[int, str] = field(default_factory=dict)
    user_notes: Dict[int, str] = field(default_factory=dict)


def _make_question(number: int = 1) -> Question:
    """Create a test Question object."""
    return Question(
        number=number,
        text=f"Question {number} text?",
        options=[
            QuestionOption(label="A", text="Option A"),
            QuestionOption(label="B", text="Option B"),
            QuestionOption(label="C", text="Option C"),
            QuestionOption(label="D", text="Option D"),
        ],
        page_number=1,
        has_image=False,
        image_data=None,
        question_type="factual"
    )


def _make_solver_result(
    question_number: int,
    selected_option: str = "A",
    confidence: float = 0.85,
    status: str = "solved"
) -> SolverResult:
    """Create a test SolverResult object."""
    return SolverResult(
        question_number=question_number,
        selected_option=selected_option if status == "solved" else None,
        explanation="This is the explanation" if status == "solved" else None,
        confidence=confidence,
        processing_time_ms=1000.0,
        status=status,
        error_message=None if status == "solved" else "Error occurred"
    )


def _make_session(
    session_id: str = "test-session-123",
    num_questions: int = 5,
    num_unsolvable: int = 0
) -> MockSessionState:
    """Create a mock session with questions and results."""
    session = MockSessionState(
        session_id=session_id,
        status="completed",
        pdf_path="/path/to/test.pdf",
        total_questions=num_questions,
        processed_count=num_questions,
        solved_count=num_questions - num_unsolvable,
        unsolvable_count=num_unsolvable,
        error_count=0
    )
    
    # Add questions
    for i in range(1, num_questions + 1):
        session.questions.append(_make_question(i))
    
    # Add results
    for i in range(1, num_questions + 1):
        if i <= num_questions - num_unsolvable:
            # Solved questions
            option = chr(ord('A') + (i - 1) % 4)  # Cycle through A, B, C, D
            session.results[i] = _make_solver_result(i, selected_option=option)
        else:
            # Unsolvable questions
            session.results[i] = _make_solver_result(i, status="unsolvable")
    
    return session


# ── Tests for AnswerKeyMetadata ──────────────────────────────────────────────

class TestAnswerKeyMetadata:
    
    def test_metadata_creation(self):
        """Test creating AnswerKeyMetadata with all fields."""
        metadata = AnswerKeyMetadata(
            session_id="test-123",
            generation_time="2024-01-15T10:30:00",
            total_questions=100,
            solved_count=95,
            unsolvable_count=5,
            manual_corrections=2,
            average_confidence=0.82,
            approved=True,
            approved_by="admin_user",
            approved_at="2024-01-15T11:00:00"
        )
        
        assert metadata.session_id == "test-123"
        assert metadata.total_questions == 100
        assert metadata.solved_count == 95
        assert metadata.unsolvable_count == 5
        assert metadata.manual_corrections == 2
        assert metadata.average_confidence == 0.82
        assert metadata.approved is True
        assert metadata.approved_by == "admin_user"
        assert metadata.approved_at == "2024-01-15T11:00:00"
    
    def test_metadata_defaults(self):
        """Test AnswerKeyMetadata default values."""
        metadata = AnswerKeyMetadata(
            session_id="test-123",
            generation_time="2024-01-15T10:30:00",
            total_questions=100,
            solved_count=95,
            unsolvable_count=5,
            manual_corrections=0,
            average_confidence=0.82
        )
        
        assert metadata.approved is False
        assert metadata.approved_by is None
        assert metadata.approved_at is None


# ── Tests for generate_json ──────────────────────────────────────────────────

class TestGenerateJson:
    
    def test_generate_json_basic(self):
        """Test basic JSON generation with solved questions."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=3)
        
        result = generator.generate_json(session)
        
        assert "answer_key" in result
        assert "metadata" in result
        assert "unsolvable" in result
        assert "low_confidence" in result
        
        # Check answer key format (0-based indices)
        assert result["answer_key"][0] == 0  # Question 1, Answer A -> 0
        assert result["answer_key"][1] == 1  # Question 2, Answer B -> 1
        assert result["answer_key"][2] == 2  # Question 3, Answer C -> 2
    
    def test_generate_json_with_unsolvable(self):
        """Test JSON generation with unsolvable questions."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=5, num_unsolvable=2)
        
        result = generator.generate_json(session)
        
        # Should have 3 solved questions
        assert len(result["answer_key"]) == 3
        
        # Should have 2 unsolvable questions
        assert len(result["unsolvable"]) == 2
        assert 4 in result["unsolvable"]
        assert 5 in result["unsolvable"]
    
    def test_generate_json_with_user_corrections(self):
        """Test JSON generation with user corrections."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=3)
        
        # Add user correction for question 2
        session.user_corrections[2] = "D"
        
        result = generator.generate_json(session)
        
        # Question 2 should use corrected answer (D -> 3)
        assert result["answer_key"][1] == 3
        
        # Metadata should reflect manual correction
        assert result["metadata"]["manual_corrections"] == 1
    
    def test_generate_json_metadata(self):
        """Test JSON metadata is complete."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=5)
        
        result = generator.generate_json(session)
        metadata = result["metadata"]
        
        assert metadata["session_id"] == "test-session-123"
        assert metadata["total_questions"] == 5
        assert metadata["solved_count"] == 5
        assert metadata["unsolvable_count"] == 0
        assert metadata["manual_corrections"] == 0
        assert "average_confidence" in metadata
        assert metadata["approved"] is False
        assert metadata["approved_by"] is None
    
    def test_generate_json_low_confidence_tracking(self):
        """Test tracking of low confidence answers."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=3)
        
        # Set low confidence for question 2
        session.results[2] = _make_solver_result(2, selected_option="B", confidence=0.5)
        
        result = generator.generate_json(session)
        
        # Question 2 should be in low_confidence list
        assert 2 in result["low_confidence"]
        assert len(result["low_confidence"]) == 1
    
    def test_generate_json_invalid_answer_option(self):
        """Test handling of invalid answer options."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=2)
        
        # Set invalid answer option
        session.results[1] = _make_solver_result(1, selected_option="X", confidence=0.8)
        
        result = generator.generate_json(session)
        
        # Invalid answer should be treated as unsolvable
        assert 0 not in result["answer_key"]
        assert 1 in result["unsolvable"]


# ── Tests for generate_csv ───────────────────────────────────────────────────

class TestGenerateCsv:
    
    def test_generate_csv_basic(self):
        """Test basic CSV generation."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=3)
        
        csv_content = generator.generate_csv(session)
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        assert len(rows) == 3
        assert rows[0]['question_number'] == '1'
        assert rows[0]['correct_answer'] == 'A'
        assert rows[0]['modified'] == 'No'
        assert 'confidence' in rows[0]
        assert 'explanation' in rows[0]
    
    def test_generate_csv_with_corrections(self):
        """Test CSV generation with user corrections."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=3)
        
        # Add user correction
        session.user_corrections[2] = "D"
        
        csv_content = generator.generate_csv(session)
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Question 2 should show correction
        assert rows[1]['correct_answer'] == 'D'
        assert rows[1]['modified'] == 'Yes'
        assert rows[1]['confidence'] == '1.00'
    
    def test_generate_csv_with_unsolvable(self):
        """Test CSV generation with unsolvable questions."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=3, num_unsolvable=1)
        
        csv_content = generator.generate_csv(session)
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Last question should be unsolvable
        assert rows[2]['correct_answer'] == 'N/A'
        assert rows[2]['confidence'] == '0.00'
        # Explanation should contain either status or error message
        assert rows[2]['explanation'] in ['unsolvable', 'Error occurred']
    
    def test_generate_csv_header(self):
        """Test CSV has correct header."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=1)
        
        csv_content = generator.generate_csv(session)
        
        # Check header
        lines = csv_content.split('\n')
        header = lines[0]
        
        assert 'question_number' in header
        assert 'correct_answer' in header
        assert 'confidence' in header
        assert 'explanation' in header
        assert 'modified' in header
    
    def test_generate_csv_explanation_cleaning(self):
        """Test that explanations are cleaned for CSV format."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=1)
        
        # Set explanation with newlines
        session.results[1].explanation = "Line 1\nLine 2\rLine 3"
        
        csv_content = generator.generate_csv(session)
        
        # Newlines should be replaced with spaces
        assert '\n' not in csv_content.split('\n')[1]  # Skip header


# ── Tests for generate_pdf_report ────────────────────────────────────────────

class TestGeneratePdfReport:
    
    def test_generate_pdf_report_creates_file(self, tmp_path):
        """Test PDF report generation creates a file."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=3)
        
        output_path = tmp_path / "report.txt"
        result_path = generator.generate_pdf_report(session, str(output_path))
        
        assert os.path.exists(result_path)
        assert result_path == str(output_path)
    
    def test_generate_pdf_report_content(self, tmp_path):
        """Test PDF report contains expected content."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=3)
        
        output_path = tmp_path / "report.txt"
        generator.generate_pdf_report(session, str(output_path))
        
        # Read content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "ANSWER KEY REPORT" in content
        assert session.session_id in content
        assert "Question 1:" in content
        assert "Question 2:" in content
        assert "Question 3:" in content
    
    def test_generate_pdf_report_with_corrections(self, tmp_path):
        """Test PDF report shows manual corrections."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=2)
        
        # Add correction and note
        session.user_corrections[1] = "C"
        session.user_notes[1] = "This was corrected by reviewer"
        
        output_path = tmp_path / "report.txt"
        generator.generate_pdf_report(session, str(output_path))
        
        # Read content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "MANUALLY CORRECTED" in content
        assert "This was corrected by reviewer" in content
    
    def test_generate_pdf_report_with_low_confidence(self, tmp_path):
        """Test PDF report flags low confidence answers."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=2)
        
        # Set low confidence
        session.results[1] = _make_solver_result(1, confidence=0.5)
        
        output_path = tmp_path / "report.txt"
        generator.generate_pdf_report(session, str(output_path))
        
        # Read content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "LOW CONFIDENCE" in content


# ── Tests for get_metadata ───────────────────────────────────────────────────

class TestGetMetadata:
    
    def test_get_metadata_basic(self):
        """Test basic metadata extraction."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=5)
        
        metadata = generator.get_metadata(session)
        
        assert metadata.session_id == "test-session-123"
        assert metadata.total_questions == 5
        assert metadata.solved_count == 5
        assert metadata.unsolvable_count == 0
        assert metadata.manual_corrections == 0
        assert metadata.approved is False
    
    def test_get_metadata_average_confidence(self):
        """Test average confidence calculation."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=3)
        
        # Set specific confidences
        session.results[1] = _make_solver_result(1, confidence=0.8)
        session.results[2] = _make_solver_result(2, confidence=0.9)
        session.results[3] = _make_solver_result(3, confidence=0.7)
        
        metadata = generator.get_metadata(session)
        
        # Average should be (0.8 + 0.9 + 0.7) / 3 = 0.8
        assert abs(metadata.average_confidence - 0.8) < 0.01
    
    def test_get_metadata_with_corrections(self):
        """Test metadata includes correction count."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=5)
        
        # Add corrections
        session.user_corrections[1] = "B"
        session.user_corrections[3] = "D"
        
        metadata = generator.get_metadata(session)
        
        assert metadata.manual_corrections == 2
    
    def test_get_metadata_with_approval(self):
        """Test metadata includes approval info."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=3)
        
        # Approve the session
        generator.approve_answer_key(session.session_id, "admin_user")
        
        metadata = generator.get_metadata(session)
        
        assert metadata.approved is True
        assert metadata.approved_by == "admin_user"
        assert metadata.approved_at is not None
    
    def test_get_metadata_empty_results(self):
        """Test metadata with no solved questions."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=2, num_unsolvable=2)
        
        metadata = generator.get_metadata(session)
        
        # Average confidence should be 0 when no solved questions
        assert metadata.average_confidence == 0.0


# ── Tests for approve_answer_key ─────────────────────────────────────────────

class TestApproveAnswerKey:
    
    def test_approve_answer_key_success(self):
        """Test successful answer key approval."""
        generator = AnswerKeyGenerator()
        
        result = generator.approve_answer_key("session-123", "admin_user")
        
        assert result is True
        assert "session-123" in generator.approved_sessions
        
        approval = generator.approved_sessions["session-123"]
        assert approval.approved is True
        assert approval.approved_by == "admin_user"
        assert approval.approved_at is not None
    
    def test_approve_answer_key_already_approved(self):
        """Test approving an already approved answer key."""
        generator = AnswerKeyGenerator()
        
        # First approval
        generator.approve_answer_key("session-123", "admin_user")
        
        # Second approval should fail
        result = generator.approve_answer_key("session-123", "another_user")
        
        assert result is False
        
        # Original approval should remain
        approval = generator.approved_sessions["session-123"]
        assert approval.approved_by == "admin_user"
    
    def test_approve_answer_key_records_timestamp(self):
        """Test that approval records a timestamp."""
        generator = AnswerKeyGenerator()
        
        before = datetime.now().isoformat()
        generator.approve_answer_key("session-123", "admin_user")
        after = datetime.now().isoformat()
        
        approval = generator.approved_sessions["session-123"]
        
        # Timestamp should be between before and after
        assert approval.approved_at >= before
        assert approval.approved_at <= after


# ── Integration Tests ─────────────────────────────────────────────────────────

class TestAnswerKeyGeneratorIntegration:
    
    def test_complete_workflow(self, tmp_path):
        """Test complete workflow: generate JSON, CSV, PDF, and approve."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=5)
        
        # Add some corrections
        session.user_corrections[2] = "D"
        session.user_corrections[4] = "A"
        
        # Generate JSON
        json_result = generator.generate_json(session)
        assert len(json_result["answer_key"]) == 5
        assert json_result["metadata"]["manual_corrections"] == 2
        
        # Generate CSV
        csv_content = generator.generate_csv(session)
        assert len(csv_content.split('\n')) > 5  # Header + 5 rows
        
        # Generate PDF
        pdf_path = tmp_path / "report.txt"
        generator.generate_pdf_report(session, str(pdf_path))
        assert os.path.exists(pdf_path)
        
        # Approve
        result = generator.approve_answer_key(session.session_id, "admin_user")
        assert result is True
        
        # Get metadata after approval
        metadata = generator.get_metadata(session)
        assert metadata.approved is True
        assert metadata.approved_by == "admin_user"
    
    def test_json_csv_consistency(self):
        """Test that JSON and CSV exports are consistent."""
        generator = AnswerKeyGenerator()
        session = _make_session(num_questions=3)
        
        # Generate both formats
        json_result = generator.generate_json(session)
        csv_content = generator.generate_csv(session)
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        csv_rows = list(reader)
        
        # Check consistency
        for row in csv_rows:
            q_num = int(row['question_number'])
            q_idx = q_num - 1
            
            if row['correct_answer'] != 'N/A':
                # Convert answer to index
                answer_idx = ord(row['correct_answer']) - ord('A')
                assert json_result["answer_key"][q_idx] == answer_idx


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
