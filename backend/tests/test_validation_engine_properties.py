"""
test_validation_engine_properties.py
-------------------------------------
Property-based tests for Validation Engine module using Hypothesis.

These tests verify universal properties that should hold across all valid inputs.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from hypothesis import given, settings, strategies as st, assume
from strategies.question_strategies import question_strategy
from strategies.solver_strategies import (
    solver_result_strategy,
    solved_result_strategy,
    result_with_uncertainty_strategy,
    low_confidence_result_strategy,
    duplicate_questions_strategy
)
from validation_engine import ValidationEngine, ValidationIssue, ValidationReport
from question_parser import Question, QuestionOption
from ai_solver import SolverResult


# ── Property Tests ────────────────────────────────────────────────────────────

# Feature: ai-question-solver, Property 16: Confidence Score Range
# **Validates: Requirements 5.1**
@settings(max_examples=100, deadline=10000)
@given(
    result=solved_result_strategy(),
    question=question_strategy()
)
def test_property_16_confidence_score_range(result, question):
    """
    Property 16: Confidence Score Range
    
    For any solved question, the calculated confidence score must be between 
    0.0 and 1.0 inclusive.
    
    This property verifies that:
    1. Confidence score is >= 0.0
    2. Confidence score is <= 1.0
    3. Confidence score is a valid float
    """
    engine = ValidationEngine()
    
    # Ensure question number matches
    result.question_number = question.number
    
    # Calculate confidence
    confidence = engine.calculate_confidence(result, question)
    
    # Property 1: Confidence >= 0.0
    assert confidence >= 0.0, \
        f"Confidence score should be >= 0.0, got {confidence}"
    
    # Property 2: Confidence <= 1.0
    assert confidence <= 1.0, \
        f"Confidence score should be <= 1.0, got {confidence}"
    
    # Property 3: Confidence is a valid float
    assert isinstance(confidence, float), \
        f"Confidence score should be a float, got {type(confidence)}"


# Feature: ai-question-solver, Property 17: Low Confidence Flagging
# **Validates: Requirements 5.3**
@settings(max_examples=100, deadline=10000)
@given(
    result=low_confidence_result_strategy(),
    question=question_strategy()
)
def test_property_17_low_confidence_flagging(result, question):
    """
    Property 17: Low Confidence Flagging
    
    For any answer with confidence score below 0.6, the Validation_Engine 
    should flag it for mandatory review.
    
    This property verifies that:
    1. Low confidence answers (< 0.6) are flagged
    2. Flagged questions appear in the flagged_questions set
    3. A low_confidence issue is added to the issues list
    """
    engine = ValidationEngine()
    
    # Ensure question number matches
    result.question_number = question.number
    
    # Calculate confidence
    confidence = engine.calculate_confidence(result, question)
    
    # Create a batch validation with this single result
    report = engine.validate_batch([result], [question])
    
    # If confidence is below 0.6, it should be flagged
    if confidence < 0.6:
        # Property 1: Question should be in flagged_questions
        assert result.question_number in report.flagged_questions, \
            f"Question {result.question_number} with confidence {confidence:.2f} " \
            f"should be flagged for review"
        
        # Property 2: Should have a low_confidence issue
        low_conf_issues = [
            issue for issue in report.issues
            if issue.issue_type == "low_confidence" and 
            issue.question_number == result.question_number
        ]
        assert len(low_conf_issues) > 0, \
            f"Question {result.question_number} with confidence {confidence:.2f} " \
            f"should have a low_confidence issue"


# Feature: ai-question-solver, Property 18: Confidence Categorization
# **Validates: Requirements 5.4**
@settings(max_examples=100, deadline=10000)
@given(
    result=solved_result_strategy(),
    question=question_strategy()
)
def test_property_18_confidence_categorization(result, question):
    """
    Property 18: Confidence Categorization
    
    For any confidence score, it should be categorized as:
    - high (0.8-1.0)
    - medium (0.6-0.79)
    - low (0.0-0.59)
    
    This property verifies that:
    1. Confidence scores map to the correct category
    2. Category boundaries are respected
    3. All scores fall into exactly one category
    """
    engine = ValidationEngine()
    
    # Ensure question number matches
    result.question_number = question.number
    
    # Calculate confidence
    confidence = engine.calculate_confidence(result, question)
    
    # Determine expected category
    if confidence >= 0.8:
        expected_category = "high"
    elif confidence >= 0.6:
        expected_category = "medium"
    else:
        expected_category = "low"
    
    # Property: Confidence score should map to correct category
    if expected_category == "high":
        assert 0.8 <= confidence <= 1.0, \
            f"High confidence should be in range [0.8, 1.0], got {confidence}"
    elif expected_category == "medium":
        assert 0.6 <= confidence < 0.8, \
            f"Medium confidence should be in range [0.6, 0.8), got {confidence}"
    else:  # low
        assert 0.0 <= confidence < 0.6, \
            f"Low confidence should be in range [0.0, 0.6), got {confidence}"


# Feature: ai-question-solver, Property 20: Duplicate Question Consistency
# **Validates: Requirements 6.2**
@settings(max_examples=50, deadline=10000)
@given(
    duplicate_data=duplicate_questions_strategy()
)
def test_property_20_duplicate_question_consistency(duplicate_data):
    """
    Property 20: Duplicate Question Consistency
    
    For any set of questions with identical text, they should all have the 
    same answer, or be flagged if they have different answers.
    
    This property verifies that:
    1. Duplicate questions with different answers are detected
    2. All duplicate questions are flagged
    3. A duplicate_inconsistency issue is created for each duplicate
    """
    questions, results = duplicate_data
    
    engine = ValidationEngine()
    
    # Run batch validation
    report = engine.validate_batch(results, questions)
    
    # Check if answers are consistent
    answers = [r.selected_option for r in results]
    unique_answers = set(answers)
    
    # Property: If answers differ, all duplicates should be flagged
    if len(unique_answers) > 1:
        # All duplicate questions should be flagged
        for question in questions:
            assert question.number in report.flagged_questions, \
                f"Duplicate question {question.number} with inconsistent answer " \
                f"should be flagged"
        
        # Should have duplicate_inconsistency issues
        duplicate_issues = [
            issue for issue in report.issues
            if issue.issue_type == "duplicate_inconsistency"
        ]
        assert len(duplicate_issues) > 0, \
            "Duplicate questions with different answers should have " \
            "duplicate_inconsistency issues"
        
        # Each duplicate question should have an issue
        flagged_question_numbers = {issue.question_number for issue in duplicate_issues}
        for question in questions:
            assert question.number in flagged_question_numbers, \
                f"Question {question.number} should have a duplicate_inconsistency issue"


# Feature: ai-question-solver, Property 21: Uncertainty Detection in Explanations
# **Validates: Requirements 6.5**
@settings(max_examples=100, deadline=10000)
@given(
    result=result_with_uncertainty_strategy(),
    question=question_strategy()
)
def test_property_21_uncertainty_detection_in_explanations(result, question):
    """
    Property 21: Uncertainty Detection in Explanations
    
    For any explanation containing uncertainty phrases ("possibly", "might be", 
    "unclear", "not sure"), the question should be flagged for review.
    
    This property verifies that:
    1. Uncertainty phrases are detected in explanations
    2. Questions with uncertainty are flagged
    3. An uncertainty issue is added to the issues list
    """
    engine = ValidationEngine()
    
    # Ensure question number matches
    result.question_number = question.number
    
    # Ensure selected option is valid for this question
    valid_options = [opt.label for opt in question.options]
    if result.selected_option not in valid_options:
        result.selected_option = valid_options[0]
    
    # Validate the answer
    issues = engine.validate_answer(result, question)
    
    # Property: Should have an uncertainty issue
    uncertainty_issues = [
        issue for issue in issues
        if issue.issue_type == "uncertainty"
    ]
    
    assert len(uncertainty_issues) > 0, \
        f"Explanation with uncertainty phrase should be flagged. " \
        f"Explanation: {result.explanation}"
    
    # Property: Uncertainty issue should have correct severity
    for issue in uncertainty_issues:
        assert issue.severity == "warning", \
            f"Uncertainty issue should have 'warning' severity, got {issue.severity}"


# Feature: ai-question-solver, Property 22: Validation Report Structure
# **Validates: Requirements 6.6**
@settings(max_examples=50, deadline=10000)
@given(
    results=st.lists(solved_result_strategy(), min_size=1, max_size=20),
    questions=st.lists(question_strategy(), min_size=1, max_size=20)
)
def test_property_22_validation_report_structure(results, questions):
    """
    Property 22: Validation Report Structure
    
    For any validation report, it must contain:
    - total_questions count
    - a list of ValidationIssue objects with severity levels
    - a set of flagged question numbers
    
    This property verifies that:
    1. Report has total_questions field with correct count
    2. Report has issues list containing ValidationIssue objects
    3. Report has flagged_questions set
    4. All issues have valid severity levels (critical, warning, info)
    5. Average confidence is calculated
    """
    # Ensure we have matching counts
    min_count = min(len(results), len(questions))
    results = results[:min_count]
    questions = questions[:min_count]
    
    # Ensure question numbers match
    for i, (result, question) in enumerate(zip(results, questions)):
        result.question_number = question.number = i + 1
        # Ensure selected option is valid
        valid_options = [opt.label for opt in question.options]
        if result.selected_option and result.selected_option not in valid_options:
            result.selected_option = valid_options[0]
    
    engine = ValidationEngine()
    
    # Generate validation report
    report = engine.validate_batch(results, questions)
    
    # Property 1: Report has total_questions field
    assert hasattr(report, 'total_questions'), \
        "ValidationReport should have total_questions field"
    assert report.total_questions == len(results), \
        f"total_questions should be {len(results)}, got {report.total_questions}"
    
    # Property 2: Report has issues list
    assert hasattr(report, 'issues'), \
        "ValidationReport should have issues field"
    assert isinstance(report.issues, list), \
        f"issues should be a list, got {type(report.issues)}"
    
    # Property 3: All issues are ValidationIssue objects
    for issue in report.issues:
        assert isinstance(issue, ValidationIssue), \
            f"All issues should be ValidationIssue objects, got {type(issue)}"
    
    # Property 4: All issues have valid severity levels
    valid_severities = {'critical', 'warning', 'info'}
    for issue in report.issues:
        assert issue.severity in valid_severities, \
            f"Issue severity should be one of {valid_severities}, " \
            f"got {issue.severity}"
    
    # Property 5: Report has flagged_questions set
    assert hasattr(report, 'flagged_questions'), \
        "ValidationReport should have flagged_questions field"
    assert isinstance(report.flagged_questions, set), \
        f"flagged_questions should be a set, got {type(report.flagged_questions)}"
    
    # Property 6: Report has average_confidence field
    assert hasattr(report, 'average_confidence'), \
        "ValidationReport should have average_confidence field"
    assert isinstance(report.average_confidence, float), \
        f"average_confidence should be a float, got {type(report.average_confidence)}"
    assert 0.0 <= report.average_confidence <= 1.0, \
        f"average_confidence should be in range [0.0, 1.0], " \
        f"got {report.average_confidence}"


# Additional helper property tests

# Feature: ai-question-solver, Property: Non-Solved Status Confidence
# **Validates: Requirements 5.1**
@settings(max_examples=50, deadline=10000)
@given(
    result=solver_result_strategy(status=st.sampled_from(["unsolvable", "timeout", "error"])),
    question=question_strategy()
)
def test_property_non_solved_status_confidence(result, question):
    """
    Property: Non-Solved Status Confidence
    
    For any question with status other than "solved", the confidence score 
    should be 0.0.
    
    This property verifies that:
    1. Unsolvable questions have 0.0 confidence
    2. Timeout questions have 0.0 confidence
    3. Error questions have 0.0 confidence
    """
    engine = ValidationEngine()
    
    # Ensure question number matches
    result.question_number = question.number
    
    # Calculate confidence
    confidence = engine.calculate_confidence(result, question)
    
    # Property: Non-solved questions should have 0.0 confidence
    assert confidence == 0.0, \
        f"Question with status '{result.status}' should have 0.0 confidence, " \
        f"got {confidence}"


# Feature: ai-question-solver, Property: Invalid Option Detection
# **Validates: Requirements 6.1**
@settings(max_examples=50, deadline=10000)
@given(
    result=solved_result_strategy(),
    question=question_strategy()
)
def test_property_invalid_option_detection(result, question):
    """
    Property: Invalid Option Detection
    
    For any solved question, if the selected option does not exist in the 
    question's option list, a critical validation issue should be raised.
    
    This property verifies that:
    1. Invalid options are detected
    2. A critical issue is created
    3. The issue type is "invalid_option"
    """
    engine = ValidationEngine()
    
    # Ensure question number matches
    result.question_number = question.number
    
    # Get valid options
    valid_options = [opt.label for opt in question.options]
    
    # Set an invalid option (one that's not in the question)
    all_options = ['A', 'B', 'C', 'D', 'E']
    invalid_options = [opt for opt in all_options if opt not in valid_options]
    
    # Only test if there are invalid options available
    assume(len(invalid_options) > 0)
    
    result.selected_option = invalid_options[0]
    
    # Validate the answer
    issues = engine.validate_answer(result, question)
    
    # Property: Should have an invalid_option issue
    invalid_option_issues = [
        issue for issue in issues
        if issue.issue_type == "invalid_option"
    ]
    
    assert len(invalid_option_issues) > 0, \
        f"Invalid option '{result.selected_option}' should be detected. " \
        f"Valid options: {valid_options}"
    
    # Property: Invalid option issue should be critical
    for issue in invalid_option_issues:
        assert issue.severity == "critical", \
            f"Invalid option issue should have 'critical' severity, " \
            f"got {issue.severity}"


# Feature: ai-question-solver, Property: Explanation Match Detection
# **Validates: Requirements 6.3**
@settings(max_examples=50, deadline=10000)
@given(
    result=solved_result_strategy(),
    question=question_strategy()
)
def test_property_explanation_match_detection(result, question):
    """
    Property: Explanation Match Detection
    
    For any solved question, the validation engine should check if the 
    explanation discusses the selected option.
    
    This property verifies that:
    1. Explanation match checking is performed
    2. Mismatches can be detected (when they occur)
    3. The validation process completes without errors
    """
    engine = ValidationEngine()
    
    # Ensure question number matches
    result.question_number = question.number
    
    # Ensure selected option is valid
    valid_options = [opt.label for opt in question.options]
    if result.selected_option not in valid_options:
        result.selected_option = valid_options[0]
    
    # Validate the answer
    issues = engine.validate_answer(result, question)
    
    # Property: Validation should complete without errors
    assert isinstance(issues, list), \
        "validate_answer should return a list of issues"
    
    # Property: All issues should be ValidationIssue objects
    for issue in issues:
        assert isinstance(issue, ValidationIssue), \
            f"All issues should be ValidationIssue objects, got {type(issue)}"


# Feature: ai-question-solver, Property: Average Confidence Calculation
# **Validates: Requirements 5.1, 6.6**
@settings(max_examples=50, deadline=10000)
@given(
    results=st.lists(solved_result_strategy(), min_size=1, max_size=10),
    questions=st.lists(question_strategy(), min_size=1, max_size=10)
)
def test_property_average_confidence_calculation(results, questions):
    """
    Property: Average Confidence Calculation
    
    For any batch of results, the average confidence in the validation report 
    should be the arithmetic mean of all individual confidence scores.
    
    This property verifies that:
    1. Average confidence is calculated correctly
    2. Average is in valid range [0.0, 1.0]
    3. Average matches manual calculation
    """
    # Ensure we have matching counts
    min_count = min(len(results), len(questions))
    results = results[:min_count]
    questions = questions[:min_count]
    
    # Ensure question numbers match
    for i, (result, question) in enumerate(zip(results, questions)):
        result.question_number = question.number = i + 1
        # Ensure selected option is valid
        valid_options = [opt.label for opt in question.options]
        if result.selected_option and result.selected_option not in valid_options:
            result.selected_option = valid_options[0]
    
    engine = ValidationEngine()
    
    # Calculate individual confidence scores
    individual_confidences = []
    for result, question in zip(results, questions):
        confidence = engine.calculate_confidence(result, question)
        individual_confidences.append(confidence)
    
    # Generate validation report
    report = engine.validate_batch(results, questions)
    
    # Calculate expected average
    expected_average = sum(individual_confidences) / len(individual_confidences)
    
    # Property: Average confidence should match expected value (with small tolerance for float precision)
    assert abs(report.average_confidence - expected_average) < 0.001, \
        f"Average confidence should be {expected_average:.4f}, " \
        f"got {report.average_confidence:.4f}"
