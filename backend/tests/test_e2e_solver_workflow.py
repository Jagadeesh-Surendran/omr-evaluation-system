"""
End-to-End Workflow Tests for AI Question Solver

Tests the complete workflow: upload → classify → extract → solve → validate → review → approve → export
Tests with various PDF formats, question bank sizes, and question types.

Requirements: All requirements (comprehensive workflow validation)
"""

import pytest
import json
import time
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from app import app
from session_manager import SessionManager, SessionState
from question_parser import QuestionParser, Question, QuestionOption, DocumentClassification
from ai_solver import AISolver, SolverResult, ModelSelector
from validation_engine import ValidationEngine, ValidationReport
from answer_key_generator import AnswerKeyGenerator


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
def mock_pdf_small():
    """Mock small PDF with 10 questions"""
    return BytesIO(b'%PDF-1.4 mock small question bank')


@pytest.fixture
def mock_pdf_medium():
    """Mock medium PDF with 100 questions"""
    return BytesIO(b'%PDF-1.4 mock medium question bank')


@pytest.fixture
def mock_pdf_large():
    """Mock large PDF with 500 questions"""
    return BytesIO(b'%PDF-1.4 mock large question bank')


@pytest.fixture
def sample_questions_small():
    """Sample questions for small test (10 questions)"""
    questions = []
    for i in range(1, 11):
        questions.append(Question(
            number=i,
            text=f"What is {i} + {i}?",
            options=[
                QuestionOption(label="A", text=f"{i*2-1}"),
                QuestionOption(label="B", text=f"{i*2}"),
                QuestionOption(label="C", text=f"{i*2+1}"),
                QuestionOption(label="D", text=f"{i*2+2}"),
            ],
            page_number=i,
            question_type="math"
        ))
    return questions


@pytest.fixture
def sample_questions_mixed():
    """Sample questions with mixed types"""
    return [
        Question(
            number=1,
            text="What is 2 + 2?",
            options=[
                QuestionOption(label="A", text="3"),
                QuestionOption(label="B", text="4"),
                QuestionOption(label="C", text="5"),
            ],
            page_number=1,
            question_type="math"
        ),
        Question(
            number=2,
            text="What comes next: 2, 4, 6, ?",
            options=[
                QuestionOption(label="A", text="7"),
                QuestionOption(label="B", text="8"),
                QuestionOption(label="C", text="9"),
            ],
            page_number=1,
            question_type="logical"
        ),
        Question(
            number=3,
            text="What is the capital of France?",
            options=[
                QuestionOption(label="A", text="London"),
                QuestionOption(label="B", text="Paris"),
                QuestionOption(label="C", text="Berlin"),
            ],
            page_number=2,
            question_type="factual"
        ),
        Question(
            number=4,
            text="Identify the shape in the image",
            options=[
                QuestionOption(label="A", text="Circle"),
                QuestionOption(label="B", text="Square"),
                QuestionOption(label="C", text="Triangle"),
            ],
            page_number=2,
            has_image=True,
            image_data=b"mock_image_data",
            question_type="visual"
        ),
    ]


class TestEndToEndWorkflow:
    """Test complete workflow from upload to export"""
    
    @patch('session_manager.QuestionParser')
    @patch('session_manager.AISolver')
    @patch('session_manager.ValidationEngine')
    def test_complete_workflow_small_pdf(
        self, mock_validation, mock_solver, mock_parser,
        client, sample_questions_small
    ):
        """Test complete workflow with small PDF (10 questions)"""
        # Setup mocks
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.classify_document.return_value = DocumentClassification(
            doc_type="question_bank",
            confidence=0.95,
            reasoning="Contains numbered questions with options"
        )
        mock_parser_instance.extract_questions.return_value = sample_questions_small
        
        mock_solver_instance = mock_solver.return_value
        mock_solver_instance.solve_question.side_effect = [
            SolverResult(
                question_number=i,
                selected_option="B",
                explanation=f"The answer is {i*2}",
                confidence=0.9,
                processing_time_ms=500,
                status="solved"
            )
            for i in range(1, 11)
        ]
        
        mock_validation_instance = mock_validation.return_value
        mock_validation_instance.calculate_confidence.return_value = 0.9
        mock_validation_instance.validate_answer.return_value = []
        mock_validation_instance.validate_batch.return_value = ValidationReport(
            total_questions=10,
            issues=[],
            flagged_questions=set(),
            average_confidence=0.9
        )
        
        # Step 1: Upload PDF
        response = client.post(
            '/api/solve/upload',
            data={'file': (BytesIO(b'%PDF-1.4 mock'), 'test.pdf')},
            content_type='multipart/form-data'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        session_id = data['session_id']
        assert data['status'] == 'pending'
        
        # Step 2: Check classification
        time.sleep(0.5)  # Allow background processing
        response = client.get(f'/api/solve/session/{session_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['document_classification']['doc_type'] == 'question_bank'
        assert data['document_classification']['confidence'] >= 0.7
        
        # Step 3: Wait for extraction and solving
        max_wait = 30
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = client.get(f'/api/solve/session/{session_id}')
            data = json.loads(response.data)
            if data['status'] == 'completed':
                break
            time.sleep(1)
        
        assert data['status'] == 'completed'
        assert data['total_questions'] == 10
        assert data['solved_count'] == 10
        
        # Step 4: Review answers
        assert 'results' in data
        assert len(data['results']) == 10
        for result in data['results'].values():
            assert result['status'] == 'solved'
            assert result['selected_option'] in ['A', 'B', 'C', 'D', 'E']
            assert result['confidence'] > 0
        
        # Step 5: Make manual correction
        response = client.put(
            f'/api/solve/session/{session_id}/answer/5',
            json={'answer': 'C'}
        )
        assert response.status_code == 200
        
        # Verify correction
        response = client.get(f'/api/solve/session/{session_id}')
        data = json.loads(response.data)
        assert data['results']['5']['selected_option'] == 'C'
        assert data['results']['5']['confidence'] == 1.0
        
        # Step 6: Approve answer key
        response = client.post(
            f'/api/solve/session/{session_id}/approve',
            json={'user_id': 'test_admin'}
        )
        assert response.status_code == 200
        
        # Step 7: Export in multiple formats
        # JSON export
        response = client.get(f'/api/solve/session/{session_id}/export?format=json')
        assert response.status_code == 200
        json_data = json.loads(response.data)
        assert 'answer_key' in json_data
        assert 'metadata' in json_data
        assert json_data['metadata']['approved'] is True
        
        # CSV export
        response = client.get(f'/api/solve/session/{session_id}/export?format=csv')
        assert response.status_code == 200
        assert response.content_type == 'text/csv'
        
        # PDF export
        response = client.get(f'/api/solve/session/{session_id}/export?format=pdf')
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
    
    @patch('session_manager.QuestionParser')
    @patch('session_manager.AISolver')
    def test_workflow_with_mixed_question_types(
        self, mock_solver, mock_parser,
        client, sample_questions_mixed
    ):
        """Test workflow with different question types (math, logical, factual, visual)"""
        # Setup mocks
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.classify_document.return_value = DocumentClassification(
            doc_type="question_bank",
            confidence=0.92,
            reasoning="Mixed question types detected"
        )
        mock_parser_instance.extract_questions.return_value = sample_questions_mixed
        
        # Mock solver with different responses for different types
        mock_solver_instance = mock_solver.return_value
        mock_solver_instance.solve_question.side_effect = [
            SolverResult(1, "B", "2+2=4", 0.95, 400, "solved"),
            SolverResult(2, "B", "Pattern increases by 2", 0.88, 600, "solved"),
            SolverResult(3, "B", "Paris is the capital", 0.92, 500, "solved"),
            SolverResult(4, "C", "The shape is a triangle", 0.75, 1200, "solved"),
        ]
        
        # Upload and process
        response = client.post(
            '/api/solve/upload',
            data={'file': (BytesIO(b'%PDF-1.4 mock'), 'mixed.pdf')},
            content_type='multipart/form-data'
        )
        assert response.status_code == 200
        session_id = json.loads(response.data)['session_id']
        
        # Wait for completion
        max_wait = 20
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = client.get(f'/api/solve/session/{session_id}')
            data = json.loads(response.data)
            if data['status'] == 'completed':
                break
            time.sleep(1)
        
        # Verify all question types were processed
        assert data['total_questions'] == 4
        assert data['solved_count'] == 4
        
        # Verify question type distribution
        question_types = set()
        for q in data['questions']:
            question_types.add(q['question_type'])
        
        assert 'math' in question_types
        assert 'logical' in question_types
        assert 'factual' in question_types
        assert 'visual' in question_types
    
    @patch('session_manager.QuestionParser')
    @patch('session_manager.AISolver')
    def test_workflow_with_pause_and_resume(
        self, mock_solver, mock_parser,
        client, sample_questions_small
    ):
        """Test pause and resume functionality during workflow"""
        # Setup mocks with slow processing
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.classify_document.return_value = DocumentClassification(
            doc_type="question_bank", confidence=0.95, reasoning="Test"
        )
        mock_parser_instance.extract_questions.return_value = sample_questions_small
        
        def slow_solve(question):
            time.sleep(0.5)  # Simulate slow processing
            return SolverResult(
                question.number, "B", "Answer", 0.9, 500, "solved"
            )
        
        mock_solver_instance = mock_solver.return_value
        mock_solver_instance.solve_question.side_effect = slow_solve
        
        # Upload
        response = client.post(
            '/api/solve/upload',
            data={'file': (BytesIO(b'%PDF-1.4 mock'), 'test.pdf')},
            content_type='multipart/form-data'
        )
        session_id = json.loads(response.data)['session_id']
        
        # Wait for some processing
        time.sleep(2)
        
        # Pause
        response = client.post(f'/api/solve/session/{session_id}/pause')
        assert response.status_code == 200
        
        # Check status
        response = client.get(f'/api/solve/session/{session_id}')
        data = json.loads(response.data)
        assert data['status'] == 'paused'
        paused_count = data['processed_count']
        assert paused_count > 0
        assert paused_count < 10
        
        # Resume
        response = client.post(f'/api/solve/session/{session_id}/resume')
        assert response.status_code == 200
        
        # Wait for completion
        max_wait = 30
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = client.get(f'/api/solve/session/{session_id}')
            data = json.loads(response.data)
            if data['status'] == 'completed':
                break
            time.sleep(1)
        
        # Verify all questions processed
        assert data['status'] == 'completed'
        assert data['processed_count'] == 10
    
    @patch('session_manager.QuestionParser')
    @patch('session_manager.AISolver')
    def test_workflow_with_validation_flags(
        self, mock_solver, mock_parser,
        client, sample_questions_small
    ):
        """Test workflow with low confidence answers requiring review"""
        # Setup mocks
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.classify_document.return_value = DocumentClassification(
            doc_type="question_bank", confidence=0.95, reasoning="Test"
        )
        mock_parser_instance.extract_questions.return_value = sample_questions_small
        
        # Mock solver with some low confidence answers
        def solve_with_varying_confidence(question):
            if question.number in [3, 7]:
                return SolverResult(
                    question.number, "B", "Not sure, possibly B", 0.45, 500, "solved"
                )
            return SolverResult(
                question.number, "B", "Confident answer", 0.92, 500, "solved"
            )
        
        mock_solver_instance = mock_solver.return_value
        mock_solver_instance.solve_question.side_effect = solve_with_varying_confidence
        
        # Upload and process
        response = client.post(
            '/api/solve/upload',
            data={'file': (BytesIO(b'%PDF-1.4 mock'), 'test.pdf')},
            content_type='multipart/form-data'
        )
        session_id = json.loads(response.data)['session_id']
        
        # Wait for completion
        max_wait = 30
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = client.get(f'/api/solve/session/{session_id}')
            data = json.loads(response.data)
            if data['status'] == 'completed':
                break
            time.sleep(1)
        
        # Verify flagged questions
        assert 'validation_report' in data
        assert len(data['validation_report']['flagged_questions']) >= 2
        assert 3 in data['validation_report']['flagged_questions']
        assert 7 in data['validation_report']['flagged_questions']
        
        # Verify approval is blocked until review
        response = client.post(
            f'/api/solve/session/{session_id}/approve',
            json={'user_id': 'test_admin'}
        )
        # Should fail or require force flag
        assert response.status_code in [400, 403]


class TestPDFFormatVariations:
    """Test with various PDF formats"""
    
    @patch('question_parser.fitz')
    def test_scanned_pdf_format(self, mock_fitz, client):
        """Test with scanned PDF (image-based)"""
        # Mock PyMuPDF for scanned PDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_pixmap.return_value = MagicMock(tobytes=lambda: b'image_data')
        mock_doc.__len__.return_value = 3
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc
        
        response = client.post(
            '/api/solve/upload',
            data={'file': (BytesIO(b'%PDF-1.4 scanned'), 'scanned.pdf')},
            content_type='multipart/form-data'
        )
        
        # Should handle scanned PDFs
        assert response.status_code in [200, 202]
    
    @patch('question_parser.fitz')
    def test_digital_pdf_format(self, mock_fitz, client):
        """Test with digital PDF (text-based)"""
        # Mock PyMuPDF for digital PDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "1. Question text\nA) Option A\nB) Option B"
        mock_doc.__len__.return_value = 3
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc
        
        response = client.post(
            '/api/solve/upload',
            data={'file': (BytesIO(b'%PDF-1.4 digital'), 'digital.pdf')},
            content_type='multipart/form-data'
        )
        
        # Should handle digital PDFs
        assert response.status_code in [200, 202]


class TestQuestionBankSizes:
    """Test with different question bank sizes"""
    
    @patch('session_manager.QuestionParser')
    @patch('session_manager.AISolver')
    def test_medium_question_bank_100_questions(
        self, mock_solver, mock_parser, client
    ):
        """Test with 100 question bank"""
        # Generate 100 questions
        questions = [
            Question(
                number=i,
                text=f"Question {i}",
                options=[QuestionOption(label=l, text=f"Option {l}") for l in "ABCD"],
                page_number=(i-1)//5 + 1,
                question_type="factual"
            )
            for i in range(1, 101)
        ]
        
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.classify_document.return_value = DocumentClassification(
            doc_type="question_bank", confidence=0.95, reasoning="Test"
        )
        mock_parser_instance.extract_questions.return_value = questions
        
        mock_solver_instance = mock_solver.return_value
        mock_solver_instance.solve_question.return_value = SolverResult(
            1, "B", "Answer", 0.9, 500, "solved"
        )
        
        response = client.post(
            '/api/solve/upload',
            data={'file': (BytesIO(b'%PDF-1.4 100q'), 'medium.pdf')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        session_id = json.loads(response.data)['session_id']
        
        # Verify session created for 100 questions
        response = client.get(f'/api/solve/session/{session_id}')
        data = json.loads(response.data)
        assert data['total_questions'] == 100
    
    @patch('session_manager.QuestionParser')
    @patch('session_manager.AISolver')
    def test_large_question_bank_500_questions(
        self, mock_solver, mock_parser, client
    ):
        """Test with 500 question bank (performance requirement)"""
        # Generate 500 questions
        questions = [
            Question(
                number=i,
                text=f"Question {i}",
                options=[QuestionOption(label=l, text=f"Option {l}") for l in "ABCD"],
                page_number=(i-1)//5 + 1,
                question_type="factual"
            )
            for i in range(1, 501)
        ]
        
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.classify_document.return_value = DocumentClassification(
            doc_type="question_bank", confidence=0.95, reasoning="Test"
        )
        mock_parser_instance.extract_questions.return_value = questions
        
        mock_solver_instance = mock_solver.return_value
        mock_solver_instance.solve_question.return_value = SolverResult(
            1, "B", "Answer", 0.9, 500, "solved"
        )
        
        response = client.post(
            '/api/solve/upload',
            data={'file': (BytesIO(b'%PDF-1.4 500q'), 'large.pdf')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        session_id = json.loads(response.data)['session_id']
        
        # Verify session created for 500 questions
        response = client.get(f'/api/solve/session/{session_id}')
        data = json.loads(response.data)
        assert data['total_questions'] == 500


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
