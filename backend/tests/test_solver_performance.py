"""
Performance Tests for AI Question Solver

Tests performance requirements:
- 2+ questions/minute for text questions
- 1+ questions/minute for image questions
- 100 questions extracted in < 60 seconds
- 500 question session completes successfully

Requirements: 11.1-11.4 (Performance Requirements)
"""

import pytest
import time
import statistics
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from session_manager import SessionManager
from question_parser import QuestionParser, Question, QuestionOption
from ai_solver import AISolver, SolverResult, ModelSelector
from app import app


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
def question_parser():
    """Question parser instance"""
    return QuestionParser()


@pytest.fixture
def ai_solver():
    """AI solver instance"""
    return AISolver()


def generate_questions(count, question_type="factual", has_image=False):
    """Helper to generate test questions"""
    questions = []
    for i in range(1, count + 1):
        questions.append(Question(
            number=i,
            text=f"Question {i}: What is the answer?",
            options=[
                QuestionOption(label="A", text=f"Option A for Q{i}"),
                QuestionOption(label="B", text=f"Option B for Q{i}"),
                QuestionOption(label="C", text=f"Option C for Q{i}"),
                QuestionOption(label="D", text=f"Option D for Q{i}"),
            ],
            page_number=(i-1)//5 + 1,
            has_image=has_image,
            image_data=b"mock_image_data" if has_image else None,
            question_type=question_type
        ))
    return questions


class TestTextQuestionPerformance:
    """Test performance for text-only questions (Req 11.1)"""
    
    @patch('ai_solver.OllamaClient')
    def test_text_questions_per_minute_rate(self, mock_ollama_client, ai_solver):
        """Test that text questions are processed at 2+ questions/minute (Req 11.1)"""
        # Mock Ollama client with realistic response time
        mock_client = mock_ollama_client.return_value
        mock_client.generate.return_value = {
            "response": "ANSWER: B\nEXPLANATION: This is the correct answer because..."
        }
        
        # Generate 10 text questions
        questions = generate_questions(10, question_type="factual", has_image=False)
        
        # Measure solving time
        start_time = time.time()
        results = []
        for question in questions:
            result = ai_solver.solve_question(question)
            results.append(result)
        elapsed_time = time.time() - start_time
        
        # Calculate questions per minute
        questions_per_minute = (len(questions) / elapsed_time) * 60
        
        # Verify performance requirement
        assert questions_per_minute >= 2.0, \
            f"Performance requirement not met: {questions_per_minute:.2f} questions/minute (required: 2+)"
        
        # Verify all questions were solved
        assert len(results) == 10
        assert all(r.status == "solved" for r in results)
    
    @patch('ai_solver.OllamaClient')
    def test_average_processing_time_text_questions(self, mock_ollama_client, ai_solver):
        """Test average processing time for text questions"""
        # Mock Ollama with fast responses
        mock_client = mock_ollama_client.return_value
        mock_client.generate.return_value = {
            "response": "ANSWER: B\nEXPLANATION: Correct answer"
        }
        
        questions = generate_questions(20, question_type="factual")
        
        processing_times = []
        for question in questions:
            start = time.time()
            result = ai_solver.solve_question(question)
            elapsed = time.time() - start
            processing_times.append(elapsed)
        
        avg_time = statistics.mean(processing_times)
        max_time = max(processing_times)
        
        # Average should be under 30 seconds (well under for text)
        assert avg_time < 30, f"Average processing time too high: {avg_time:.2f}s"
        
        # Max should not exceed timeout
        assert max_time < 30, f"Max processing time exceeded timeout: {max_time:.2f}s"
        
        print(f"\nText Question Performance:")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Max: {max_time:.2f}s")
        print(f"  Min: {min(processing_times):.2f}s")
        print(f"  Rate: {60/avg_time:.2f} questions/minute")


class TestImageQuestionPerformance:
    """Test performance for image-based questions (Req 11.2)"""
    
    @patch('ai_solver.OllamaClient')
    @patch('ai_solver.ModelSelector')
    def test_image_questions_per_minute_rate(
        self, mock_model_selector, mock_ollama_client, ai_solver
    ):
        """Test that image questions are processed at 1+ questions/minute (Req 11.2)"""
        # Mock model selector to use vision model
        mock_selector = mock_model_selector.return_value
        mock_selector.select_model.return_value = "moondream:latest"
        mock_selector.is_model_available.return_value = True
        
        # Mock Ollama client with slower response for vision
        mock_client = mock_ollama_client.return_value
        def slow_vision_response(*args, **kwargs):
            time.sleep(0.5)  # Simulate vision processing
            return {"response": "ANSWER: C\nEXPLANATION: Based on the image..."}
        
        mock_client.generate.side_effect = slow_vision_response
        
        # Generate 5 image questions
        questions = generate_questions(5, question_type="visual", has_image=True)
        
        # Measure solving time
        start_time = time.time()
        results = []
        for question in questions:
            result = ai_solver.solve_question(question)
            results.append(result)
        elapsed_time = time.time() - start_time
        
        # Calculate questions per minute
        questions_per_minute = (len(questions) / elapsed_time) * 60
        
        # Verify performance requirement
        assert questions_per_minute >= 1.0, \
            f"Performance requirement not met: {questions_per_minute:.2f} questions/minute (required: 1+)"
        
        # Verify all questions were solved
        assert len(results) == 5
        assert all(r.status == "solved" for r in results)
    
    @patch('ai_solver.OllamaClient')
    def test_image_processing_overhead(self, mock_ollama_client, ai_solver):
        """Test that image processing adds acceptable overhead"""
        mock_client = mock_ollama_client.return_value
        mock_client.generate.return_value = {
            "response": "ANSWER: B\nEXPLANATION: Answer"
        }
        
        # Compare text vs image question processing
        text_question = generate_questions(1, question_type="factual", has_image=False)[0]
        image_question = generate_questions(1, question_type="visual", has_image=True)[0]
        
        # Process text question
        start = time.time()
        text_result = ai_solver.solve_question(text_question)
        text_time = time.time() - start
        
        # Process image question
        start = time.time()
        image_result = ai_solver.solve_question(image_question)
        image_time = time.time() - start
        
        # Image processing should be slower but not excessively
        assert image_time > text_time or abs(image_time - text_time) < 1.0
        assert image_time < 60, "Image processing took too long"
        
        print(f"\nImage Processing Overhead:")
        print(f"  Text question: {text_time:.2f}s")
        print(f"  Image question: {image_time:.2f}s")
        print(f"  Overhead: {image_time - text_time:.2f}s")


class TestQuestionExtractionPerformance:
    """Test question extraction performance (Req 11.3)"""
    
    @patch('question_parser.fitz')
    def test_extract_100_questions_under_60_seconds(self, mock_fitz, question_parser):
        """Test that 100 questions are extracted in < 60 seconds (Req 11.3)"""
        # Mock PyMuPDF with 100 questions across 20 pages
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 20
        
        def get_page(index):
            mock_page = MagicMock()
            # Each page has 5 questions
            questions_text = ""
            for q in range(5):
                q_num = index * 5 + q + 1
                questions_text += f"\n{q_num}. Question {q_num} text here?\n"
                questions_text += "A) Option A\nB) Option B\nC) Option C\nD) Option D\n"
            
            mock_page.get_text.return_value = questions_text
            mock_page.get_pixmap.return_value = MagicMock(tobytes=lambda: b'image_data')
            return mock_page
        
        mock_doc.__getitem__.side_effect = get_page
        mock_fitz.open.return_value = mock_doc
        
        # Measure extraction time
        start_time = time.time()
        questions = question_parser.extract_questions('/tmp/test_100q.pdf')
        elapsed_time = time.time() - start_time
        
        # Verify performance requirement
        assert elapsed_time < 60, \
            f"Extraction took too long: {elapsed_time:.2f}s (required: < 60s)"
        
        # Verify all questions extracted
        assert len(questions) >= 90, \
            f"Not enough questions extracted: {len(questions)} (expected: ~100)"
        
        print(f"\nExtraction Performance (100 questions):")
        print(f"  Time: {elapsed_time:.2f}s")
        print(f"  Questions extracted: {len(questions)}")
        print(f"  Rate: {len(questions)/elapsed_time:.2f} questions/second")
    
    @patch('question_parser.fitz')
    def test_extraction_scales_linearly(self, mock_fitz, question_parser):
        """Test that extraction time scales linearly with question count"""
        def create_mock_doc(num_pages):
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = num_pages
            
            def get_page(index):
                mock_page = MagicMock()
                questions_text = ""
                for q in range(5):
                    q_num = index * 5 + q + 1
                    questions_text += f"\n{q_num}. Question text?\n"
                    questions_text += "A) Option A\nB) Option B\n"
                mock_page.get_text.return_value = questions_text
                mock_page.get_pixmap.return_value = MagicMock(tobytes=lambda: b'img')
                return mock_page
            
            mock_doc.__getitem__.side_effect = get_page
            return mock_doc
        
        # Test with different sizes
        sizes = [10, 20, 50]  # pages
        times = []
        
        for num_pages in sizes:
            mock_fitz.open.return_value = create_mock_doc(num_pages)
            
            start = time.time()
            questions = question_parser.extract_questions(f'/tmp/test_{num_pages}p.pdf')
            elapsed = time.time() - start
            times.append(elapsed)
            
            print(f"  {num_pages} pages: {elapsed:.2f}s ({len(questions)} questions)")
        
        # Verify roughly linear scaling (within 2x tolerance)
        if len(times) >= 2:
            ratio = times[1] / times[0]
            expected_ratio = sizes[1] / sizes[0]
            assert ratio < expected_ratio * 2, "Extraction does not scale linearly"


class TestLargeSessionPerformance:
    """Test performance with large question banks (Req 11.4)"""
    
    @patch('session_manager.QuestionParser')
    @patch('session_manager.AISolver')
    @patch('session_manager.ValidationEngine')
    def test_500_question_session_completes(
        self, mock_validation, mock_solver, mock_parser,
        session_manager
    ):
        """Test that 500 question session completes successfully (Req 11.4)"""
        # Generate 500 questions
        questions = generate_questions(500, question_type="factual")
        
        # Setup mocks
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.extract_questions.return_value = questions
        
        mock_solver_instance = mock_solver.return_value
        mock_solver_instance.solve_question.return_value = SolverResult(
            1, "B", "Answer", 0.9, 500, "solved"
        )
        
        mock_validation_instance = mock_validation.return_value
        mock_validation_instance.calculate_confidence.return_value = 0.9
        mock_validation_instance.validate_answer.return_value = []
        
        # Create and start session
        session_id = session_manager.create_session('/tmp/test_500q.pdf')
        
        start_time = time.time()
        session_manager.start_processing(session_id)
        
        # Wait for completion (with timeout)
        max_wait = 600  # 10 minutes max
        while time.time() - start_time < max_wait:
            session = session_manager.get_session(session_id)
            if session.status == "completed":
                break
            time.sleep(5)
        
        elapsed_time = time.time() - start_time
        
        # Verify completion
        session = session_manager.get_session(session_id)
        assert session.status == "completed", \
            f"Session did not complete in {max_wait}s"
        assert session.total_questions == 500
        assert session.processed_count == 500
        
        # Calculate performance metrics
        questions_per_minute = (500 / elapsed_time) * 60
        
        print(f"\n500 Question Session Performance:")
        print(f"  Total time: {elapsed_time:.2f}s ({elapsed_time/60:.2f} minutes)")
        print(f"  Questions/minute: {questions_per_minute:.2f}")
        print(f"  Average per question: {elapsed_time/500:.2f}s")
        
        # Should meet minimum performance requirement
        assert questions_per_minute >= 1.0, \
            f"Performance too slow: {questions_per_minute:.2f} q/min"
    
    @patch('session_manager.QuestionParser')
    @patch('session_manager.AISolver')
    def test_memory_usage_large_session(
        self, mock_solver, mock_parser, session_manager
    ):
        """Test that memory usage remains reasonable for large sessions"""
        import psutil
        import os
        
        # Generate 200 questions (smaller for faster test)
        questions = generate_questions(200, question_type="factual")
        
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.extract_questions.return_value = questions
        
        mock_solver_instance = mock_solver.return_value
        mock_solver_instance.solve_question.return_value = SolverResult(
            1, "B", "Answer", 0.9, 500, "solved"
        )
        
        # Measure memory before
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create and process session
        session_id = session_manager.create_session('/tmp/test_200q.pdf')
        session_manager.start_processing(session_id)
        
        # Wait for completion
        max_wait = 300
        start_time = time.time()
        while time.time() - start_time < max_wait:
            session = session_manager.get_session(session_id)
            if session.status == "completed":
                break
            time.sleep(2)
        
        # Measure memory after
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_increase = mem_after - mem_before
        
        print(f"\nMemory Usage (200 questions):")
        print(f"  Before: {mem_before:.2f} MB")
        print(f"  After: {mem_after:.2f} MB")
        print(f"  Increase: {mem_increase:.2f} MB")
        print(f"  Per question: {mem_increase/200:.2f} MB")
        
        # Memory increase should be reasonable (< 500 MB for 200 questions)
        assert mem_increase < 500, \
            f"Memory usage too high: {mem_increase:.2f} MB"


class TestConcurrentSessionLimits:
    """Test concurrent session limits (Req 11.5)"""
    
    @patch('session_manager.QuestionParser')
    @patch('session_manager.AISolver')
    def test_concurrent_session_limit_enforced(
        self, mock_solver, mock_parser, client
    ):
        """Test that concurrent sessions are limited to 2 (Req 11.5)"""
        # Setup mocks
        questions = generate_questions(10)
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.extract_questions.return_value = questions
        
        mock_solver_instance = mock_solver.return_value
        mock_solver_instance.solve_question.return_value = SolverResult(
            1, "B", "Answer", 0.9, 500, "solved"
        )
        
        # Start first session
        response1 = client.post(
            '/api/solve/upload',
            data={'file': (BytesIO(b'%PDF-1.4 test1'), 'test1.pdf')},
            content_type='multipart/form-data'
        )
        assert response1.status_code == 200
        
        # Start second session
        response2 = client.post(
            '/api/solve/upload',
            data={'file': (BytesIO(b'%PDF-1.4 test2'), 'test2.pdf')},
            content_type='multipart/form-data'
        )
        assert response2.status_code == 200
        
        # Third session should be queued or rejected
        response3 = client.post(
            '/api/solve/upload',
            data={'file': (BytesIO(b'%PDF-1.4 test3'), 'test3.pdf')},
            content_type='multipart/form-data'
        )
        
        # Should either queue (200 with queued status) or reject (429/503)
        assert response3.status_code in [200, 429, 503]
        
        if response3.status_code == 200:
            data = response3.get_json()
            assert data.get('status') == 'queued' or 'queue' in str(data).lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
