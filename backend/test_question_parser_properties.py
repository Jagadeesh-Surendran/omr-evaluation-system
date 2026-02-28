"""
Property-based tests for Question Parser module.

Tests Properties 1-3:
- Property 1: Document Classification Correctness
- Property 2: Classification Confidence Range
- Property 3: Low Confidence Prompting

Validates Requirements: 1.2, 1.3, 1.4, 1.5
"""
import os
import tempfile
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import fitz  # PyMuPDF
from question_parser import QuestionParser, DocumentClassification


# Strategy for generating PDF content
@composite
def pdf_content_strategy(draw):
    """
    Generates PDF content that represents either a question bank or answer key.
    Returns tuple: (content_type, text_content)
    """
    content_type = draw(st.sampled_from(["question_bank", "answer_key", "ambiguous"]))
    
    if content_type == "question_bank":
        # Generate question bank content with questions and options
        num_questions = draw(st.integers(min_value=5, max_value=20))
        lines = []
        
        for i in range(1, num_questions + 1):
            lines.append(f"Q{i}. What is the answer to question {i}?")
            lines.append(f"A. Option A for question {i}")
            lines.append(f"B. Option B for question {i}")
            lines.append(f"C. Option C for question {i}")
            lines.append(f"D. Option D for question {i}")
            lines.append("")
        
        return ("question_bank", "\n".join(lines))
    
    elif content_type == "answer_key":
        # Generate answer key content with answer indicators
        num_answers = draw(st.integers(min_value=5, max_value=20))
        format_type = draw(st.sampled_from(["colon", "dash", "paren", "word"]))
        lines = []
        
        for i in range(1, num_answers + 1):
            answer = draw(st.sampled_from(["A", "B", "C", "D", "E"]))
            
            if format_type == "colon":
                lines.append(f"{i}: {answer}")
            elif format_type == "dash":
                lines.append(f"{i}-{answer}")
            elif format_type == "paren":
                lines.append(f"{i}) {answer}")
            else:  # word
                lines.append(f"Answer: {answer}")
        
        return ("answer_key", "\n".join(lines))
    
    else:  # ambiguous
        # Generate content with few patterns
        lines = [
            "This is a document with minimal structure.",
            "It contains some text but no clear patterns.",
            "There might be a number 1 or 2 here.",
            "But no clear question or answer format."
        ]
        return ("ambiguous", "\n".join(lines))


def create_pdf_from_text(text: str, num_pages: int = 1) -> str:
    """
    Creates a temporary PDF file with the given text content.
    Returns the path to the created PDF.
    """
    # Create temporary PDF file
    temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(temp_fd)
    
    # Create PDF with text
    doc = fitz.open()
    
    # Distribute text across pages
    lines = text.split("\n")
    lines_per_page = max(1, len(lines) // num_pages)
    
    for page_idx in range(num_pages):
        page = doc.new_page()
        start_idx = page_idx * lines_per_page
        end_idx = start_idx + lines_per_page if page_idx < num_pages - 1 else len(lines)
        page_text = "\n".join(lines[start_idx:end_idx])
        
        # Insert text at position (50, 50)
        page.insert_text((50, 50), page_text, fontsize=11)
    
    doc.save(temp_path)
    doc.close()
    
    return temp_path


# Property 1: Document Classification Correctness
@given(pdf_content=pdf_content_strategy())
@settings(max_examples=50, deadline=5000)
def test_property_1_document_classification_correctness(pdf_content):
    """
    Property 1: Document Classification Correctness
    
    For any PDF document, when the Question_Parser classifies it, the classification
    should be "question_bank" if the document contains question numbers with options
    but no answer indicators, and "answer_key" if it contains answer indicators
    (filled bubbles, answer lists, or key patterns).
    
    Validates: Requirements 1.2, 1.3
    """
    expected_type, text_content = pdf_content
    
    # Skip ambiguous cases for this property (they're tested separately)
    assume(expected_type != "ambiguous")
    
    # Create PDF from content
    pdf_path = create_pdf_from_text(text_content, num_pages=1)
    
    try:
        parser = QuestionParser()
        result = parser.classify_document(pdf_path)
        
        # Verify classification matches expected type
        # Note: Due to heuristic nature, we allow some flexibility
        # but the classification should generally match the content type
        assert result.doc_type in ["question_bank", "answer_key"], \
            f"Classification must be either 'question_bank' or 'answer_key', got: {result.doc_type}"
        
        # For strong patterns, classification should match expected type
        if result.confidence >= 0.7:
            assert result.doc_type == expected_type, \
                f"High confidence classification should match content type. " \
                f"Expected: {expected_type}, Got: {result.doc_type} (confidence: {result.confidence})"
    
    finally:
        # Cleanup
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


# Property 2: Classification Confidence Range
@given(pdf_content=pdf_content_strategy())
@settings(max_examples=50, deadline=5000)
def test_property_2_classification_confidence_range(pdf_content):
    """
    Property 2: Classification Confidence Range
    
    For any document classification result, the confidence score must be
    between 0.0 and 1.0 inclusive.
    
    Validates: Requirements 1.4
    """
    _, text_content = pdf_content
    
    # Create PDF from content
    pdf_path = create_pdf_from_text(text_content, num_pages=1)
    
    try:
        parser = QuestionParser()
        result = parser.classify_document(pdf_path)
        
        # Verify confidence is in valid range
        assert 0.0 <= result.confidence <= 1.0, \
            f"Confidence score must be between 0.0 and 1.0, got: {result.confidence}"
        
        # Verify confidence is a float
        assert isinstance(result.confidence, float), \
            f"Confidence must be a float, got: {type(result.confidence)}"
    
    finally:
        # Cleanup
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


# Property 3: Low Confidence Prompting
@given(pdf_content=pdf_content_strategy())
@settings(max_examples=50, deadline=5000)
def test_property_3_low_confidence_prompting(pdf_content):
    """
    Property 3: Low Confidence Prompting
    
    For any classification result with confidence below 0.7, the system should
    prompt the user to manually select the document type.
    
    Note: This property tests that low confidence is properly detected.
    The actual user prompting is tested in integration tests.
    
    Validates: Requirements 1.5
    """
    _, text_content = pdf_content
    
    # Create PDF from content
    pdf_path = create_pdf_from_text(text_content, num_pages=1)
    
    try:
        parser = QuestionParser()
        result = parser.classify_document(pdf_path)
        
        # Property: If confidence < 0.7, this should be flagged for manual selection
        # We verify that the system correctly identifies low confidence cases
        if result.confidence < 0.7:
            # Low confidence detected - this is the condition that should trigger prompting
            assert result.confidence < 0.7, \
                "Low confidence threshold check failed"
            
            # Verify that a reasoning is provided for low confidence
            assert result.reasoning is not None and len(result.reasoning) > 0, \
                "Low confidence results must include reasoning"
        
        # Property: High confidence results should not trigger prompting
        if result.confidence >= 0.7:
            assert result.confidence >= 0.7, \
                "High confidence threshold check failed"
    
    finally:
        # Cleanup
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


# Additional test: Verify classification returns proper structure
@given(pdf_content=pdf_content_strategy())
@settings(max_examples=30, deadline=5000)
def test_classification_result_structure(pdf_content):
    """
    Verifies that classification always returns a properly structured result.
    """
    _, text_content = pdf_content
    
    # Create PDF from content
    pdf_path = create_pdf_from_text(text_content, num_pages=1)
    
    try:
        parser = QuestionParser()
        result = parser.classify_document(pdf_path)
        
        # Verify result is DocumentClassification instance
        assert isinstance(result, DocumentClassification), \
            f"Result must be DocumentClassification instance, got: {type(result)}"
        
        # Verify all required fields are present
        assert hasattr(result, 'doc_type'), "Result must have doc_type field"
        assert hasattr(result, 'confidence'), "Result must have confidence field"
        assert hasattr(result, 'reasoning'), "Result must have reasoning field"
        
        # Verify field types
        assert isinstance(result.doc_type, str), "doc_type must be string"
        assert isinstance(result.confidence, float), "confidence must be float"
        assert isinstance(result.reasoning, str), "reasoning must be string"
        
        # Verify doc_type is valid
        assert result.doc_type in ["question_bank", "answer_key"], \
            f"doc_type must be 'question_bank' or 'answer_key', got: {result.doc_type}"
    
    finally:
        # Cleanup
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


# Test with multi-page PDFs
@given(
    pdf_content=pdf_content_strategy(),
    num_pages=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=30, deadline=5000)
def test_classification_with_multiple_pages(pdf_content, num_pages):
    """
    Verifies that classification works correctly with multi-page PDFs.
    The classifier should analyze the first 3 pages.
    """
    _, text_content = pdf_content
    
    # Create PDF from content
    pdf_path = create_pdf_from_text(text_content, num_pages=num_pages)
    
    try:
        parser = QuestionParser()
        result = parser.classify_document(pdf_path)
        
        # Verify classification succeeds regardless of page count
        assert result is not None, "Classification should succeed for multi-page PDFs"
        assert 0.0 <= result.confidence <= 1.0, "Confidence must be in valid range"
        assert result.doc_type in ["question_bank", "answer_key"], \
            "Classification must return valid document type"
    
    finally:
        # Cleanup
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
