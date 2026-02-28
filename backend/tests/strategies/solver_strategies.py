"""
Hypothesis strategies for generating SolverResult and related objects for property-based testing.
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite


@composite
def solver_result_strategy(draw, question_number=None, status=None):
    """
    Strategy for generating SolverResult objects.
    
    Args:
        question_number: Optional fixed question number (otherwise random)
        status: Optional fixed status (otherwise random from valid statuses)
    """
    from ai_solver import SolverResult
    
    # Generate or use provided question number
    qnum = question_number if question_number is not None else draw(
        st.integers(min_value=1, max_value=500)
    )
    
    # Generate or use provided status
    valid_statuses = ["solved", "unsolvable", "timeout", "error"]
    result_status = status if status is not None else draw(st.sampled_from(valid_statuses))
    
    # Generate selected option (only for solved status)
    if result_status == "solved":
        selected_option = draw(st.sampled_from(['A', 'B', 'C', 'D', 'E']))
    else:
        selected_option = None
    
    # Generate explanation
    if result_status == "solved":
        # For solved questions, generate a more detailed explanation
        explanation = draw(st.text(
            min_size=20,
            max_size=300,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
                blacklist_characters='\n\r\t'
            )
        ))
    else:
        # For non-solved questions, generate a shorter explanation/reason
        explanation = draw(st.text(
            min_size=10,
            max_size=100,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
                blacklist_characters='\n\r\t'
            )
        ))
    
    # Generate processing time (in milliseconds)
    # Normal range: 1000ms to 25000ms (1s to 25s)
    processing_time_ms = draw(st.floats(min_value=100.0, max_value=30000.0))
    
    # Generate confidence (will be calculated by validation engine, but include for completeness)
    confidence = draw(st.floats(min_value=0.0, max_value=1.0))
    
    # Generate error message (only for error status)
    if result_status == "error":
        error_message = draw(st.text(
            min_size=10,
            max_size=100,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
                blacklist_characters='\n\r\t'
            )
        ))
    else:
        error_message = None
    
    return SolverResult(
        question_number=qnum,
        selected_option=selected_option,
        explanation=explanation,
        confidence=confidence,
        processing_time_ms=processing_time_ms,
        status=result_status,
        error_message=error_message
    )


@composite
def solved_result_strategy(draw, question_number=None):
    """Strategy for generating SolverResult objects with status='solved'."""
    return draw(solver_result_strategy(question_number=question_number, status="solved"))


@composite
def result_with_uncertainty_strategy(draw, question_number=None):
    """
    Strategy for generating SolverResult objects with uncertainty phrases in explanation.
    """
    from ai_solver import SolverResult
    
    qnum = question_number if question_number is not None else draw(
        st.integers(min_value=1, max_value=500)
    )
    
    # Uncertainty phrases to inject
    uncertainty_phrases = [
        "possibly", "might be", "unclear", "not sure", "maybe",
        "could be", "perhaps", "uncertain", "probably", "likely"
    ]
    
    selected_phrase = draw(st.sampled_from(uncertainty_phrases))
    selected_option = draw(st.sampled_from(['A', 'B', 'C', 'D', 'E']))
    
    # Generate explanation with uncertainty phrase
    base_text = draw(st.text(
        min_size=20,
        max_size=200,
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
            blacklist_characters='\n\r\t'
        )
    ))
    
    explanation = f"{base_text} {selected_phrase} the answer is {selected_option}"
    
    processing_time_ms = draw(st.floats(min_value=1000.0, max_value=25000.0))
    confidence = draw(st.floats(min_value=0.0, max_value=1.0))
    
    return SolverResult(
        question_number=qnum,
        selected_option=selected_option,
        explanation=explanation,
        confidence=confidence,
        processing_time_ms=processing_time_ms,
        status="solved",
        error_message=None
    )


@composite
def low_confidence_result_strategy(draw, question_number=None):
    """
    Strategy for generating SolverResult objects that should result in low confidence.
    This includes short explanations, uncertainty phrases, or extreme processing times.
    """
    from ai_solver import SolverResult
    
    qnum = question_number if question_number is not None else draw(
        st.integers(min_value=1, max_value=500)
    )
    
    selected_option = draw(st.sampled_from(['A', 'B', 'C', 'D', 'E']))
    
    # Choose a low-confidence characteristic
    characteristic = draw(st.sampled_from(['short_explanation', 'uncertainty', 'fast_processing', 'slow_processing']))
    
    if characteristic == 'short_explanation':
        # Very short explanation (< 20 chars)
        explanation = draw(st.text(min_size=5, max_size=19, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            blacklist_characters='\n\r\t'
        )))
        processing_time_ms = draw(st.floats(min_value=2000.0, max_value=20000.0))
    
    elif characteristic == 'uncertainty':
        # Explanation with uncertainty phrase
        uncertainty_phrases = ["possibly", "might be", "unclear", "not sure"]
        phrase = draw(st.sampled_from(uncertainty_phrases))
        base_text = draw(st.text(min_size=20, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
            blacklist_characters='\n\r\t'
        )))
        explanation = f"{base_text} {phrase}"
        processing_time_ms = draw(st.floats(min_value=2000.0, max_value=20000.0))
    
    elif characteristic == 'fast_processing':
        # Very fast processing (< 1s)
        explanation = draw(st.text(min_size=20, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
            blacklist_characters='\n\r\t'
        )))
        processing_time_ms = draw(st.floats(min_value=100.0, max_value=999.0))
    
    else:  # slow_processing
        # Very slow processing (> 25s)
        explanation = draw(st.text(min_size=20, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
            blacklist_characters='\n\r\t'
        )))
        processing_time_ms = draw(st.floats(min_value=25001.0, max_value=29999.0))
    
    confidence = draw(st.floats(min_value=0.0, max_value=1.0))
    
    return SolverResult(
        question_number=qnum,
        selected_option=selected_option,
        explanation=explanation,
        confidence=confidence,
        processing_time_ms=processing_time_ms,
        status="solved",
        error_message=None
    )


@composite
def duplicate_questions_strategy(draw):
    """
    Strategy for generating duplicate questions (same text) with potentially different answers.
    Returns a tuple of (questions, results) where some questions have identical text.
    """
    from question_parser import Question, QuestionOption
    
    # Draw the number of duplicates
    num_duplicates = draw(st.integers(min_value=2, max_value=4))
    
    # Generate a base question text that will be duplicated
    base_text = draw(st.text(
        min_size=20,
        max_size=200,
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
            blacklist_characters='\n\r\t'
        )
    ))
    
    # Generate options for the questions
    num_options = draw(st.integers(min_value=3, max_value=5))
    labels = ['A', 'B', 'C', 'D', 'E'][:num_options]
    
    options = []
    for label in labels:
        option_text = draw(st.text(
            min_size=5,
            max_size=100,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
                blacklist_characters='\n\r\t'
            )
        ))
        options.append(QuestionOption(label=label, text=option_text))
    
    # Create duplicate questions with same text
    questions = []
    results = []
    
    for i in range(num_duplicates):
        question_number = i + 1
        
        question = Question(
            number=question_number,
            text=base_text,  # Same text for all duplicates
            options=options.copy(),
            page_number=i + 1,
            has_image=False,
            image_data=None,
            question_type="factual"
        )
        questions.append(question)
        
        # Generate result (potentially different answers)
        result = draw(solved_result_strategy(question_number=question_number))
        # Ensure the selected option is valid for this question
        result.selected_option = draw(st.sampled_from(labels))
        results.append(result)
    
    return questions, results
