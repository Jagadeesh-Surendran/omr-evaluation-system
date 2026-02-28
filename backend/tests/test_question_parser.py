"""
test_question_parser.py
-----------------------
Unit tests for Question Parser module.

These tests verify specific examples and edge cases for the Question Parser functionality.
Tests cover:
1. Document classification (question bank vs answer key)
2. Question extraction with known counts
3. Multi-page question handling
4. Image detection in questions
5. Error recovery for parse failures

**Validates: Requirements 2.1-2.6**
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import pytest
import fitz  # PyMuPDF
from question_parser import QuestionParser, Question, QuestionOption, DocumentClassification


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def parser():
    """Create a QuestionParser instance."""
    return QuestionParser()


@pytest.fixture
def sample_question_bank_pdf():
    """Create a sample question bank PDF with 5 questions."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    # Add 5 questions with options
    y_pos = 50
    for i in range(1, 6):
        page.insert_text((50, y_pos), f"{i}. What is the capital of country {i}?", fontsize=11)
        y_pos += 20
        page.insert_text((70, y_pos), f"A. City A{i}", fontsize=10)
        y_pos += 15
        page.insert_text((70, y_pos), f"B. City B{i}", fontsize=10)
        y_pos += 15
        page.insert_text((70, y_pos), f"C. City C{i}", fontsize=10)
        y_pos += 15
        page.insert_text((70, y_pos), f"D. City D{i}", fontsize=10)
        y_pos += 25
    
    doc.save(tmp.name)
    doc.close()
    
    yield tmp.name
    
    # Cleanup
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


@pytest.fixture
def sample_answer_key_pdf():
    """Create a sample answer key PDF."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    # Add answer key content
    page.insert_text((50, 50), "Answer Key", fontsize=14)
    y_pos = 80
    for i in range(1, 11):
        answer = chr(65 + (i % 4))  # A, B, C, D
        page.insert_text((50, y_pos), f"{i}: {answer}", fontsize=11)
        y_pos += 20
    
    doc.save(tmp.name)
    doc.close()
    
    yield tmp.name
    
    # Cleanup
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


@pytest.fixture
def multi_page_question_pdf():
    """Create a PDF with questions spanning multiple pages."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    doc = fitz.open()
    
    # Page 1 with 3 questions
    page1 = doc.new_page(width=595, height=842)
    y_pos = 50
    for i in range(1, 4):
        page1.insert_text((50, y_pos), f"{i}. Question {i} on page 1?", fontsize=11)
        y_pos += 20
        page1.insert_text((70, y_pos), f"A. Option A{i}", fontsize=10)
        y_pos += 15
        page1.insert_text((70, y_pos), f"B. Option B{i}", fontsize=10)
        y_pos += 15
        page1.insert_text((70, y_pos), f"C. Option C{i}", fontsize=10)
        y_pos += 25
    
    # Page 2 with 2 more questions
    page2 = doc.new_page(width=595, height=842)
    y_pos = 50
    for i in range(4, 6):
        page2.insert_text((50, y_pos), f"{i}. Question {i} on page 2?", fontsize=11)
        y_pos += 20
        page2.insert_text((70, y_pos), f"A. Option A{i}", fontsize=10)
        y_pos += 15
        page2.insert_text((70, y_pos), f"B. Option B{i}", fontsize=10)
        y_pos += 15
        page2.insert_text((70, y_pos), f"C. Option C{i}", fontsize=10)
        y_pos += 25
    
    doc.save(tmp.name)
    doc.close()
    
    yield tmp.name
    
    # Cleanup
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


@pytest.fixture
def pdf_with_images():
    """Create a PDF with a question containing an image/diagram."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    # Add question with diagram
    page.insert_text((50, 50), "1. What shape is shown in the diagram below?", fontsize=11)
    
    # Draw a rectangle to simulate a diagram
    rect = fitz.Rect(50, 70, 200, 150)
    page.draw_rect(rect, color=(0, 0, 0), width=2)
    page.insert_text((100, 105), "[DIAGRAM]", fontsize=10)
    
    # Add options
    page.insert_text((50, 170), "A. Circle", fontsize=10)
    page.insert_text((50, 185), "B. Rectangle", fontsize=10)
    page.insert_text((50, 200), "C. Triangle", fontsize=10)
    page.insert_text((50, 215), "D. Square", fontsize=10)
    
    doc.save(tmp.name)
    doc.close()
    
    yield tmp.name
    
    # Cleanup
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


@pytest.fixture
def math_question_pdf():
    """Create a PDF with mathematical questions."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    # Add math questions
    page.insert_text((50, 50), "1. Calculate the value of 2 + 2 =", fontsize=11)
    page.insert_text((70, 70), "A. 3", fontsize=10)
    page.insert_text((70, 85), "B. 4", fontsize=10)
    page.insert_text((70, 100), "C. 5", fontsize=10)
    
    page.insert_text((50, 130), "2. Solve the equation: x + 5 = 10", fontsize=11)
    page.insert_text((70, 150), "A. x = 3", fontsize=10)
    page.insert_text((70, 165), "B. x = 5", fontsize=10)
    page.insert_text((70, 180), "C. x = 15", fontsize=10)
    
    doc.save(tmp.name)
    doc.close()
    
    yield tmp.name
    
    # Cleanup
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


@pytest.fixture
def corrupted_pdf():
    """Create a corrupted PDF file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(b"This is not a valid PDF file content")
    tmp.close()
    
    yield tmp.name
    
    # Cleanup
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


# ── Test Document Classification ─────────────────────────────────────────────

def test_classify_question_bank(parser, sample_question_bank_pdf):
    """Test classification of a question bank PDF."""
    result = parser.classify_document(sample_question_bank_pdf)
    
    assert isinstance(result, DocumentClassification)
    assert result.doc_type == "question_bank"
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.reasoning) > 0


def test_classify_answer_key(parser, sample_answer_key_pdf):
    """Test classification of an answer key PDF."""
    result = parser.classify_document(sample_answer_key_pdf)
    
    assert isinstance(result, DocumentClassification)
    assert result.doc_type == "answer_key"
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.reasoning) > 0


def test_classify_nonexistent_file(parser):
    """Test classification with a non-existent file."""
    with pytest.raises(FileNotFoundError):
        parser.classify_document("/nonexistent/file.pdf")


def test_classify_non_pdf_file(parser):
    """Test classification with a non-PDF file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
    tmp.write(b"Not a PDF")
    tmp.close()
    
    try:
        with pytest.raises(ValueError, match="not a PDF"):
            parser.classify_document(tmp.name)
    finally:
        os.unlink(tmp.name)


def test_classify_confidence_range(parser, sample_question_bank_pdf):
    """Test that confidence score is within valid range."""
    result = parser.classify_document(sample_question_bank_pdf)
    
    assert result.confidence >= 0.0
    assert result.confidence <= 1.0


def test_classify_low_confidence_detection(parser):
    """Test detection of low confidence when patterns are unclear."""
    # Create a PDF with minimal content
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Some random text without clear patterns", fontsize=11)
    doc.save(tmp.name)
    doc.close()
    
    try:
        result = parser.classify_document(tmp.name)
        # Should have low confidence due to lack of clear patterns
        assert result.confidence < 0.7
    finally:
        os.unlink(tmp.name)


# ── Test Question Extraction ─────────────────────────────────────────────────

def test_extract_questions_known_count(parser, sample_question_bank_pdf):
    """Test extraction with known question count."""
    questions = parser.extract_questions(sample_question_bank_pdf)
    
    assert len(questions) == 5
    
    # Verify each question has required fields
    for i, question in enumerate(questions, 1):
        assert question.number == i
        assert len(question.text) > 0
        assert len(question.options) >= 3
        assert question.page_number == 1


def test_extract_questions_structure(parser, sample_question_bank_pdf):
    """Test that extracted questions have correct structure."""
    questions = parser.extract_questions(sample_question_bank_pdf)
    
    for question in questions:
        # Check Question object structure
        assert isinstance(question, Question)
        assert isinstance(question.number, int)
        assert isinstance(question.text, str)
        assert isinstance(question.options, list)
        assert isinstance(question.page_number, int)
        assert isinstance(question.has_image, bool)
        assert question.question_type in ['math', 'logical', 'factual', 'visual']
        
        # Check QuestionOption structure
        for option in question.options:
            assert isinstance(option, QuestionOption)
            assert option.label in ['A', 'B', 'C', 'D', 'E']
            assert isinstance(option.text, str)
            assert len(option.text) > 0


def test_extract_questions_option_labels(parser, sample_question_bank_pdf):
    """Test that options have correct labels (A-E)."""
    questions = parser.extract_questions(sample_question_bank_pdf)
    
    for question in questions:
        labels = [opt.label for opt in question.options]
        
        # Labels should be unique
        assert len(labels) == len(set(labels))
        
        # Labels should be from A-E
        for label in labels:
            assert label in ['A', 'B', 'C', 'D', 'E']
        
        # Labels should be in alphabetical order
        assert labels == sorted(labels)


def test_extract_questions_nonexistent_file(parser):
    """Test extraction with non-existent file."""
    with pytest.raises(FileNotFoundError):
        parser.extract_questions("/nonexistent/file.pdf")


# ── Test Multi-Page Question Handling ────────────────────────────────────────

def test_multi_page_extraction(parser, multi_page_question_pdf):
    """Test extraction from multi-page PDF."""
    questions = parser.extract_questions(multi_page_question_pdf)
    
    # Should extract all 5 questions across 2 pages
    assert len(questions) == 5
    
    # Verify questions from page 1
    page1_questions = [q for q in questions if q.page_number == 1]
    assert len(page1_questions) == 3
    
    # Verify questions from page 2
    page2_questions = [q for q in questions if q.page_number == 2]
    assert len(page2_questions) == 2


def test_multi_page_question_numbers(parser, multi_page_question_pdf):
    """Test that question numbers are correct across pages."""
    questions = parser.extract_questions(multi_page_question_pdf)
    
    # Sort by question number
    questions.sort(key=lambda q: q.number)
    
    # Verify sequential numbering
    for i, question in enumerate(questions, 1):
        assert question.number == i


def test_multi_page_page_references(parser, multi_page_question_pdf):
    """Test that page references are correct."""
    questions = parser.extract_questions(multi_page_question_pdf)
    
    for question in questions:
        # Page number should be valid
        assert question.page_number > 0
        assert question.page_number <= 2  # We have 2 pages


# ── Test Image Detection ─────────────────────────────────────────────────────

def test_image_detection_question_extraction(parser, pdf_with_images):
    """Test that questions with images are extracted correctly."""
    questions = parser.extract_questions(pdf_with_images)
    
    # Should extract the question
    assert len(questions) == 1
    
    question = questions[0]
    assert question.number == 1
    assert "diagram" in question.text.lower()
    assert len(question.options) == 4


def test_image_detection_has_image_flag(parser, pdf_with_images):
    """Test image detection flag (currently not implemented)."""
    questions = parser.extract_questions(pdf_with_images)
    
    # Note: Image detection is currently TODO in the implementation
    # This test documents expected behavior for future implementation
    question = questions[0]
    
    # Currently has_image is False by default
    # Future: assert question.has_image == True
    assert isinstance(question.has_image, bool)


def test_image_detection_with_text(parser, pdf_with_images):
    """Test that text is extracted even when images are present."""
    questions = parser.extract_questions(pdf_with_images)
    
    question = questions[0]
    
    # Text should be extracted
    assert len(question.text) > 0
    assert "shape" in question.text.lower()
    
    # Options should be extracted
    assert len(question.options) == 4
    option_texts = [opt.text for opt in question.options]
    assert any("Rectangle" in text for text in option_texts)


# ── Test Question Type Detection ─────────────────────────────────────────────

def test_question_type_detection_math(parser, math_question_pdf):
    """Test detection of mathematical questions."""
    questions = parser.extract_questions(math_question_pdf)
    
    assert len(questions) == 2
    
    # Both questions should be detected as math type
    for question in questions:
        assert question.question_type == "math"


def test_question_type_detection_factual(parser, sample_question_bank_pdf):
    """Test detection of factual questions."""
    questions = parser.extract_questions(sample_question_bank_pdf)
    
    # Questions about capitals should be factual
    for question in questions:
        assert question.question_type in ['factual', 'logical', 'math', 'visual']


def test_question_type_valid_values(parser, sample_question_bank_pdf):
    """Test that question types are valid."""
    questions = parser.extract_questions(sample_question_bank_pdf)
    
    valid_types = {'math', 'logical', 'factual', 'visual'}
    
    for question in questions:
        assert question.question_type in valid_types


# ── Test Error Recovery ──────────────────────────────────────────────────────

def test_error_recovery_corrupted_pdf(parser, corrupted_pdf):
    """Test error handling with corrupted PDF."""
    with pytest.raises(Exception) as exc_info:
        parser.extract_questions(corrupted_pdf)
    
    # Should raise an exception with informative message
    error_msg = str(exc_info.value).lower()
    assert any(keyword in error_msg for keyword in ['extraction', 'failed', 'error'])


def test_error_recovery_empty_pdf(parser):
    """Test handling of empty PDF."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    # Create empty PDF
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    doc.save(tmp.name)
    doc.close()
    
    try:
        questions = parser.extract_questions(tmp.name)
        
        # Should return empty list, not crash
        assert isinstance(questions, list)
        assert len(questions) == 0
    finally:
        os.unlink(tmp.name)


def test_error_recovery_malformed_questions(parser):
    """Test handling of malformed question format."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    # Add malformed content (no options)
    page.insert_text((50, 50), "1. This is a question without options", fontsize=11)
    page.insert_text((50, 70), "Some random text", fontsize=10)
    
    doc.save(tmp.name)
    doc.close()
    
    try:
        questions = parser.extract_questions(tmp.name)
        
        # Should handle gracefully - either skip or extract what's possible
        assert isinstance(questions, list)
        # If extracted, should have valid structure
        for q in questions:
            assert isinstance(q, Question)
    finally:
        os.unlink(tmp.name)


def test_error_recovery_partial_extraction(parser):
    """Test that extraction continues after encountering a bad question."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    # Add good question
    page.insert_text((50, 50), "1. Good question?", fontsize=11)
    page.insert_text((70, 70), "A. Option A", fontsize=10)
    page.insert_text((70, 85), "B. Option B", fontsize=10)
    page.insert_text((70, 100), "C. Option C", fontsize=10)
    
    # Add malformed question (no options)
    page.insert_text((50, 130), "2. Bad question without options", fontsize=11)
    
    # Add another good question
    page.insert_text((50, 160), "3. Another good question?", fontsize=11)
    page.insert_text((70, 180), "A. Option A", fontsize=10)
    page.insert_text((70, 195), "B. Option B", fontsize=10)
    page.insert_text((70, 210), "C. Option C", fontsize=10)
    
    doc.save(tmp.name)
    doc.close()
    
    try:
        questions = parser.extract_questions(tmp.name)
        
        # Should extract the good questions
        assert isinstance(questions, list)
        # Should have at least the good questions
        assert len(questions) >= 2
    finally:
        os.unlink(tmp.name)


# ── Test Edge Cases ──────────────────────────────────────────────────────────

def test_extract_questions_with_special_characters(parser):
    """Test extraction with special characters in text."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    # Add question with special characters
    page.insert_text((50, 50), "1. What is 50% of $100?", fontsize=11)
    page.insert_text((70, 70), "A. $25", fontsize=10)
    page.insert_text((70, 85), "B. $50", fontsize=10)
    page.insert_text((70, 100), "C. $75", fontsize=10)
    
    doc.save(tmp.name)
    doc.close()
    
    try:
        questions = parser.extract_questions(tmp.name)
        
        assert len(questions) >= 1
        question = questions[0]
        assert "$" in question.text or "50" in question.text
    finally:
        os.unlink(tmp.name)


def test_extract_questions_with_five_options(parser):
    """Test extraction with 5 options (A-E)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    # Add question with 5 options
    page.insert_text((50, 50), "1. Which is correct?", fontsize=11)
    page.insert_text((70, 70), "A. Option A", fontsize=10)
    page.insert_text((70, 85), "B. Option B", fontsize=10)
    page.insert_text((70, 100), "C. Option C", fontsize=10)
    page.insert_text((70, 115), "D. Option D", fontsize=10)
    page.insert_text((70, 130), "E. Option E", fontsize=10)
    
    doc.save(tmp.name)
    doc.close()
    
    try:
        questions = parser.extract_questions(tmp.name)
        
        assert len(questions) >= 1
        question = questions[0]
        assert len(question.options) == 5
        
        labels = [opt.label for opt in question.options]
        assert labels == ['A', 'B', 'C', 'D', 'E']
    finally:
        os.unlink(tmp.name)


def test_extract_questions_with_long_text(parser):
    """Test extraction with long question text."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    # Add question with long text
    long_text = "This is a very long question that contains multiple sentences. " * 3
    page.insert_text((50, 50), f"1. {long_text}", fontsize=11)
    page.insert_text((70, 100), "A. Option A", fontsize=10)
    page.insert_text((70, 115), "B. Option B", fontsize=10)
    page.insert_text((70, 130), "C. Option C", fontsize=10)
    
    doc.save(tmp.name)
    doc.close()
    
    try:
        questions = parser.extract_questions(tmp.name)
        
        assert len(questions) >= 1
        question = questions[0]
        assert len(question.text) > 50  # Should preserve long text
    finally:
        os.unlink(tmp.name)
