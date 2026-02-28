"""
Hypothesis strategies for generating Question and related objects for property-based testing.
"""
import tempfile
import os
from hypothesis import strategies as st
from hypothesis.strategies import composite
import fitz  # PyMuPDF


@composite
def question_option_strategy(draw):
    """Strategy for generating QuestionOption objects."""
    from question_parser import QuestionOption
    
    label = draw(st.sampled_from(['A', 'B', 'C', 'D', 'E']))
    text = draw(st.text(min_size=5, max_size=200, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
        blacklist_characters='\n\r\t'
    )))
    has_image = draw(st.booleans())
    image_data = draw(st.binary(min_size=10, max_size=100)) if has_image else None
    
    return QuestionOption(
        label=label,
        text=text,
        has_image=has_image,
        image_data=image_data
    )


@composite
def question_strategy(draw):
    """Strategy for generating Question objects."""
    from question_parser import Question
    
    number = draw(st.integers(min_value=1, max_value=500))
    text = draw(st.text(min_size=10, max_size=500, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
        blacklist_characters='\n\r\t'
    )))
    
    # Generate 3-5 options
    num_options = draw(st.integers(min_value=3, max_value=5))
    options = [draw(question_option_strategy()) for _ in range(num_options)]
    
    # Ensure unique labels
    labels = ['A', 'B', 'C', 'D', 'E'][:num_options]
    for i, option in enumerate(options):
        option.label = labels[i]
    
    page_number = draw(st.integers(min_value=1, max_value=100))
    has_image = draw(st.booleans())
    image_data = draw(st.binary(min_size=10, max_size=100)) if has_image else None
    question_type = draw(st.sampled_from(['math', 'logical', 'factual', 'visual']))
    
    return Question(
        number=number,
        text=text,
        options=options,
        page_number=page_number,
        has_image=has_image,
        image_data=image_data,
        question_type=question_type
    )


@composite
def pdf_with_questions_strategy(draw, min_questions=1, max_questions=10):
    """
    Strategy for generating a PDF file with a known number of questions.
    Returns a tuple of (pdf_path, expected_question_count, questions_data).
    """
    num_questions = draw(st.integers(min_value=min_questions, max_value=max_questions))
    
    # Create a temporary PDF file
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    # Create PDF with questions
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 size
    
    y_position = 50
    questions_data = []
    
    for i in range(1, num_questions + 1):
        # Generate question text
        question_text = draw(st.text(min_size=20, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
            blacklist_characters='\n\r\t'
        )))
        
        # Generate options
        num_options = draw(st.integers(min_value=3, max_value=5))
        options = []
        for j in range(num_options):
            option_label = chr(65 + j)  # A, B, C, D, E
            option_text = draw(st.text(min_size=5, max_size=50, alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
                blacklist_characters='\n\r\t'
            )))
            options.append((option_label, option_text))
        
        # Write question to PDF
        page.insert_text((50, y_position), f"{i}. {question_text}", fontsize=11)
        y_position += 20
        
        for option_label, option_text in options:
            page.insert_text((70, y_position), f"{option_label}. {option_text}", fontsize=10)
            y_position += 15
        
        y_position += 10  # Space between questions
        
        questions_data.append({
            'number': i,
            'text': question_text,
            'options': options
        })
        
        # Create new page if needed
        if y_position > 750 and i < num_questions:
            page = doc.new_page(width=595, height=842)
            y_position = 50
    
    doc.save(tmp.name)
    doc.close()
    
    return tmp.name, num_questions, questions_data


@composite
def pdf_with_math_notation_strategy(draw):
    """
    Strategy for generating a PDF with mathematical notation.
    Returns (pdf_path, expected_symbols).
    """
    # Mathematical symbols to test
    math_symbols = ['∫', '∑', '√', '∞', '≤', '≥', '≠', '±', '×', '÷', 'π', 'θ', 'α', 'β']
    
    # Select some symbols to include
    num_symbols = draw(st.integers(min_value=2, max_value=5))
    selected_symbols = draw(st.lists(
        st.sampled_from(math_symbols),
        min_size=num_symbols,
        max_size=num_symbols,
        unique=True
    ))
    
    # Create a temporary PDF file
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    # Create PDF with mathematical notation
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    # Create question with math symbols
    question_text = f"1. Calculate the value: {' '.join(selected_symbols)}"
    page.insert_text((50, 50), question_text, fontsize=11)
    
    # Add options
    page.insert_text((70, 70), "A. Option with symbols", fontsize=10)
    page.insert_text((70, 85), "B. Another option", fontsize=10)
    page.insert_text((70, 100), "C. Third option", fontsize=10)
    
    doc.save(tmp.name)
    doc.close()
    
    return tmp.name, selected_symbols


def multi_page_question_pdf_strategy():
    """
    Strategy for generating a PDF with a question spanning multiple pages.
    Returns (pdf_path, question_number, total_pages_spanned).
    """
    # Create a temporary PDF file
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    # Create PDF with multi-page question
    doc = fitz.open()
    
    # First page with question start
    page1 = doc.new_page(width=595, height=842)
    page1.insert_text((50, 50), "1. This is a long question that spans multiple pages.", fontsize=11)
    page1.insert_text((50, 70), "Part 1 of the question is on this page.", fontsize=11)
    
    # Second page with question continuation
    page2 = doc.new_page(width=595, height=842)
    page2.insert_text((50, 50), "Part 2 of the question continues here.", fontsize=11)
    page2.insert_text((50, 70), "A. First option", fontsize=10)
    page2.insert_text((50, 85), "B. Second option", fontsize=10)
    page2.insert_text((50, 100), "C. Third option", fontsize=10)
    
    doc.save(tmp.name)
    doc.close()
    
    return st.just((tmp.name, 1, 2))


def pdf_with_images_strategy():
    """
    Strategy for generating a PDF with images in questions.
    Returns (pdf_path, has_images).
    """
    # Create a temporary PDF file
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    
    # Create PDF
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    # Add question text
    page.insert_text((50, 50), "1. What is shown in the diagram below?", fontsize=11)
    
    # Add a simple rectangle to simulate an image/diagram
    rect = fitz.Rect(50, 70, 200, 150)
    page.draw_rect(rect, color=(0, 0, 0), width=2)
    page.insert_text((60, 90), "[DIAGRAM]", fontsize=10)
    
    # Add options
    page.insert_text((50, 170), "A. Option A", fontsize=10)
    page.insert_text((50, 185), "B. Option B", fontsize=10)
    page.insert_text((50, 200), "C. Option C", fontsize=10)
    
    doc.save(tmp.name)
    doc.close()
    
    return st.just((tmp.name, True))


def corrupted_pdf_strategy():
    """
    Strategy for generating a corrupted or invalid PDF.
    Returns pdf_path.
    """
    # Create a temporary file with invalid PDF content
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(b"This is not a valid PDF file")
    tmp.close()
    
    return st.just(tmp.name)
