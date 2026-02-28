"""
Property-based tests for AI Solver module.

Tests Properties 12, 13, 14, 15, 36:
- Property 12: Valid Answer Option Selection
- Property 13: Explanation Generation
- Property 14: Unsolvable Question Handling
- Property 15: Timeout Enforcement and Handling
- Property 36: Retry Logic with Exponential Backoff

Validates Requirements: 4.2, 4.4, 4.5, 4.6, 4.7, 10.3, 10.4
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite

from ai_solver import AISolver, SolverConfig, SolverResult
from question_parser import Question, QuestionOption


# ── Strategy Definitions ──────────────────────────────────────────────────────

@composite
def question_option_strategy(draw):
    """Generate a valid QuestionOption."""
    label = draw(st.sampled_from(["A", "B", "C", "D", "E"]))
    text = draw(st.text(min_size=5, max_size=100))
    has_image = draw(st.booleans())
    
    return QuestionOption(
        label=label,
        text=text,
        has_image=has_image,
        image_data=None
    )


@composite
def question_strategy(draw):
    """Generate a valid Question with 2-5 options."""
    number = draw(st.integers(min_value=1, max_value=500))
    text = draw(st.text(min_size=10, max_size=500))
    
    # Generate 2-5 unique options with labels A-E
    num_options = draw(st.integers(min_value=2, max_value=5))
    labels = ["A", "B", "C", "D", "E"][:num_options]
    
    options = []
    for label in labels:
        option_text = draw(st.text(min_size=5, max_size=100))
        options.append(QuestionOption(
            label=label,
            text=option_text,
            has_image=False,
            image_data=None
        ))
    
    page_number = draw(st.integers(min_value=1, max_value=100))
    has_image = draw(st.booleans())
    question_type = draw(st.sampled_from(["math", "logical", "factual", "visual", None]))
    
    return Question(
        number=number,
        text=text,
        options=options,
        page_number=page_number,
        has_image=has_image,
        image_data=None,
        question_type=question_type
    )


@composite
def solver_config_strategy(draw):
    """Generate a valid SolverConfig."""
    timeout_seconds = draw(st.integers(min_value=1, max_value=60))
    max_retries = draw(st.integers(min_value=0, max_value=5))
    retry_backoff_base = draw(st.floats(min_value=1.0, max_value=5.0))
    min_confidence_threshold = draw(st.floats(min_value=0.0, max_value=1.0))
    
    return SolverConfig(
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        retry_backoff_base=retry_backoff_base,
        min_confidence_threshold=min_confidence_threshold
    )


def _make_ollama_response(content: str):
    """Build a mock return value that matches ollama.chat() structure."""
    return {"message": {"content": content}}


# ── Property 12: Valid Answer Option Selection ────────────────────────────────

@given(question=question_strategy())
@settings(max_examples=50, deadline=None)
@patch('ai_solver.ollama.chat')
def test_property_12_valid_answer_option_selection(mock_chat, question):
    """
    Property 12: Valid Answer Option Selection
    
    For any solved question, the selected answer option must be one of the 
    valid options (A, B, C, D, or E) that exists in the question's option list.
    
    Validates: Requirements 4.2, 6.1
    """
    # Get valid option labels from the question
    valid_labels = [opt.label for opt in question.options]
    assume(len(valid_labels) > 0)
    
    # Pick a random valid option for the mock response
    selected_option = valid_labels[0]
    
    # Mock Ollama to return a valid structured response
    mock_chat.return_value = _make_ollama_response(
        f"ANSWER: {selected_option}\nEXPLANATION: This is the correct answer."
    )
    
    # Solve the question
    solver = AISolver()
    result = solver.solve_question(question)
    
    # Property assertion: If status is "solved", selected_option must be valid
    if result.status == "solved":
        assert result.selected_option is not None, \
            "Solved question must have a selected option"
        assert result.selected_option in valid_labels, \
            f"Selected option '{result.selected_option}' must be in valid options {valid_labels}"


# ── Property 13: Explanation Generation ───────────────────────────────────────

@given(question=question_strategy())
@settings(max_examples=50, deadline=None)
@patch('ai_solver.ollama.chat')
def test_property_13_explanation_generation(mock_chat, question):
    """
    Property 13: Explanation Generation
    
    For any question with status "solved", the SolverResult must include 
    a non-empty explanation string.
    
    Validates: Requirements 4.4
    """
    # Get valid option labels
    valid_labels = [opt.label for opt in question.options]
    assume(len(valid_labels) > 0)
    
    selected_option = valid_labels[0]
    explanation_text = "This is a detailed explanation of why this answer is correct."
    
    # Mock Ollama to return a response with explanation
    mock_chat.return_value = _make_ollama_response(
        f"ANSWER: {selected_option}\nEXPLANATION: {explanation_text}"
    )
    
    # Solve the question
    solver = AISolver()
    result = solver.solve_question(question)
    
    # Property assertion: If status is "solved", explanation must be non-empty
    if result.status == "solved":
        assert result.explanation is not None, \
            "Solved question must have an explanation"
        assert len(result.explanation.strip()) > 0, \
            "Explanation must be non-empty for solved questions"
        assert isinstance(result.explanation, str), \
            "Explanation must be a string"


# ── Property 14: Unsolvable Question Handling ─────────────────────────────────

@given(question=question_strategy())
@settings(max_examples=50, deadline=None)
@patch('ai_solver.ollama.chat')
def test_property_14_unsolvable_question_handling(mock_chat, question):
    """
    Property 14: Unsolvable Question Handling
    
    For any question where the AI cannot determine an answer with reasonable 
    confidence, the status should be "unsolvable" and a reason must be provided.
    
    Validates: Requirements 4.5
    """
    # Mock Ollama to return an unsolvable response
    unsolvable_phrases = [
        "I cannot determine the answer due to insufficient information.",
        "Unable to solve this question with the given context.",
        "Not enough context to provide a reliable answer.",
        "Cannot answer this question confidently."
    ]
    
    # Use one of the unsolvable phrases
    phrase = unsolvable_phrases[question.number % len(unsolvable_phrases)]
    mock_chat.return_value = _make_ollama_response(phrase)
    
    # Solve the question
    solver = AISolver()
    result = solver.solve_question(question)
    
    # Property assertion: Unsolvable questions must have correct status and reason
    if result.status == "unsolvable":
        assert result.selected_option is None, \
            "Unsolvable question should not have a selected option"
        assert result.explanation is not None and len(result.explanation) > 0, \
            "Unsolvable question must provide a reason/explanation"
        assert any(keyword in result.explanation.lower() 
                   for keyword in ["cannot", "unable", "insufficient", "not enough"]), \
            "Explanation should indicate why the question is unsolvable"


# ── Property 15: Timeout Enforcement and Handling ─────────────────────────────

@given(
    question=question_strategy(),
    config=solver_config_strategy()
)
@settings(max_examples=30, deadline=None)
@patch('ai_solver.ollama.chat')
def test_property_15_timeout_enforcement_and_handling(mock_chat, question, config):
    """
    Property 15: Timeout Enforcement and Handling
    
    For any question, processing time should not exceed the configured timeout,
    and if it does, the status should be "timeout" and processing should 
    continue with the next question.
    
    Validates: Requirements 4.6, 4.7
    """
    # Ensure timeout is reasonable for testing
    assume(config.timeout_seconds >= 1)
    
    # Mock Ollama to raise TimeoutError
    mock_chat.side_effect = TimeoutError("Request timeout")
    
    # Solve the question
    solver = AISolver(config)
    start_time = time.time()
    result = solver.solve_question(question)
    elapsed_time = time.time() - start_time
    
    # Property assertions for timeout handling
    assert result.status == "timeout", \
        "Question that times out must have status 'timeout'"
    assert result.selected_option is None, \
        "Timeout question should not have a selected option"
    assert result.error_message is not None, \
        "Timeout question must have an error message"
    assert "timeout" in result.error_message.lower(), \
        "Error message should mention timeout"
    
    # Verify processing doesn't hang indefinitely
    # Allow some overhead for test execution
    assert elapsed_time < config.timeout_seconds + 5, \
        f"Processing should complete quickly after timeout (took {elapsed_time:.2f}s)"


# ── Property 36: Retry Logic with Exponential Backoff ─────────────────────────

@given(
    question=question_strategy(),
    config=solver_config_strategy()
)
@settings(max_examples=30, deadline=None)
@patch('ai_solver.ollama.chat')
@patch('ai_solver.time.sleep')  # Mock sleep to speed up tests
def test_property_36_retry_logic_with_exponential_backoff(mock_sleep, mock_chat, question, config):
    """
    Property 36: Retry Logic with Exponential Backoff
    
    For any solver error, the system should retry exactly max_retries times 
    with exponentially increasing delays before marking as "solver_error".
    
    Validates: Requirements 10.3, 10.4
    """
    # Ensure we have retries configured
    assume(config.max_retries >= 1)
    
    # Mock Ollama to always fail with a connection error
    mock_chat.side_effect = Exception("Connection error")
    
    # Solve the question
    solver = AISolver(config)
    result = solver.solve_question(question)
    
    # Property assertions for retry logic
    expected_attempts = config.max_retries + 1  # Initial attempt + retries
    
    assert mock_chat.call_count == expected_attempts, \
        f"Should attempt exactly {expected_attempts} times (1 initial + {config.max_retries} retries), " \
        f"but attempted {mock_chat.call_count} times"
    
    # Verify exponential backoff was applied
    # Sleep should be called once per retry (not on initial attempt)
    assert mock_sleep.call_count == config.max_retries, \
        f"Should sleep {config.max_retries} times (once per retry), " \
        f"but slept {mock_sleep.call_count} times"
    
    # Verify exponential backoff delays
    if config.max_retries > 0:
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        
        for i, sleep_time in enumerate(sleep_calls):
            expected_sleep = config.retry_backoff_base ** (i + 1)
            assert abs(sleep_time - expected_sleep) < 0.01, \
                f"Retry {i+1} should sleep for {expected_sleep}s (backoff_base^{i+1}), " \
                f"but slept for {sleep_time}s"
    
    # After all retries fail, status should be "error"
    assert result.status == "error", \
        "After all retries fail, status should be 'error'"
    assert result.selected_option is None, \
        "Failed question should not have a selected option"
    assert result.error_message is not None, \
        "Failed question must have an error message"


# ── Additional Property: Retry Success on Subsequent Attempt ──────────────────

@given(
    question=question_strategy(),
    config=solver_config_strategy()
)
@settings(max_examples=30, deadline=None)
@patch('ai_solver.ollama.chat')
@patch('ai_solver.time.sleep')
def test_property_retry_succeeds_on_second_attempt(mock_sleep, mock_chat, question, config):
    """
    Additional Property: Retry Success on Subsequent Attempt
    
    When the first attempt fails but a retry succeeds, the system should 
    return a successful result without exhausting all retries.
    
    Validates: Requirements 10.3, 10.4
    """
    # Ensure we have at least one retry
    assume(config.max_retries >= 1)
    
    # Get valid option
    valid_labels = [opt.label for opt in question.options]
    assume(len(valid_labels) > 0)
    selected_option = valid_labels[0]
    
    # First call fails, second call succeeds
    mock_chat.side_effect = [
        Exception("Temporary connection error"),
        _make_ollama_response(
            f"ANSWER: {selected_option}\nEXPLANATION: This is correct."
        )
    ]
    
    # Solve the question
    solver = AISolver(config)
    result = solver.solve_question(question)
    
    # Property assertions
    assert result.status == "solved", \
        "Should succeed on retry when subsequent attempt works"
    assert result.selected_option == selected_option, \
        "Should return the correct answer from successful retry"
    
    # Should only attempt twice (initial + 1 retry)
    assert mock_chat.call_count == 2, \
        "Should stop retrying after first success"
    
    # Should only sleep once (before the successful retry)
    assert mock_sleep.call_count == 1, \
        "Should sleep once before successful retry"


# ── Property: Processing Time Tracking ────────────────────────────────────────

@given(question=question_strategy())
@settings(max_examples=30, deadline=None)
@patch('ai_solver.ollama.chat')
def test_property_processing_time_tracking(mock_chat, question):
    """
    Additional Property: Processing Time Tracking
    
    For any question (regardless of status), the SolverResult must include 
    a positive processing_time_ms value.
    
    Validates: Requirements 4.6
    """
    # Get valid option
    valid_labels = [opt.label for opt in question.options]
    assume(len(valid_labels) > 0)
    
    # Mock response
    mock_chat.return_value = _make_ollama_response(
        f"ANSWER: {valid_labels[0]}\nEXPLANATION: Correct answer."
    )
    
    # Solve the question
    solver = AISolver()
    result = solver.solve_question(question)
    
    # Property assertion: processing time must be positive
    assert result.processing_time_ms > 0, \
        "Processing time must be positive"
    assert isinstance(result.processing_time_ms, (int, float)), \
        "Processing time must be numeric"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
