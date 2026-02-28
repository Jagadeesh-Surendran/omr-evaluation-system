"""
test_validation_engine.py
--------------------------
Unit tests for Validation Engine module.

These tests verify specific examples and edge cases for the validation engine,
complementing the property-based tests.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from validation_engine import ValidationEngine, ValidationIssue, ValidationReport
from question_parser import Question, QuestionOption
from ai_solver import SolverResult


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def validation_engine():
    """Create a ValidationEngine instance."""
    return ValidationEngine()


@pytest.fixture
def sample_question():
    """Create a sample question with options."""
    return Question(
        number=1,
        text="What is 2 + 2?",
        options=[
            QuestionOption(label="A", text="3"),
            QuestionOption(label="B", text="4"),
            QuestionOption(label="C", text="5"),
            QuestionOption(label="D", text="6")
        ],
        page_number=1,
        has_image=False,
        question_type="math"
    )


@pytest.fixture
def sample_solved_result():
    """Create a sample solved result."""
    return SolverResult(
        question_number=1,
        selected_option="B",
        explanation="The answer is B because 2 + 2 equals 4, which is a basic arithmetic fact.",
        confidence=0.0,  # Will be calculated by validation engine
        processing_time_ms=5000.0,
        status="solved"
    )


# ── Confidence Calculation Tests ──────────────────────────────────────────────

def test_confidence_calculation_with_detailed_explanation(validation_engine, sample_question):
    """Test confidence calculation with a long, detailed explanation."""
    result = SolverResult(
        question_number=1,
        selected_option="B",
        explanation="The answer is B because 2 + 2 equals 4. This is a fundamental "
                   "arithmetic operation that combines two quantities of 2 to produce "
                   "a sum of 4. This can be verified through counting or basic addition.",
        confidence=0.0,
        processing_time_ms=5000.0,
        status="solved"
    )
    
    confidence = validation_engine.calculate_confidence(result, sample_question)
    
    # Detailed explanation should increase confidence
    # Base: 0.7, +0.1 for length > 100 chars = 0.8
    assert confidence >= 0.7, "Detailed explanation should have high confidence"
    assert confidence <= 1.0, "Confidence should not exceed 1.0"


def test_confidence_calculation_with_short_explanation(validation_engine, sample_question):
    """Test confidence calculation with a very short explanation."""
    result = SolverResult(
        question_number=1,
        selected_option="B",
        explanation="It's 4.",
        confidence=0.0,
        processing_time_ms=5000.0,
        status="solved"
    )
    
    confidence = validation_engine.calculate_confidence(result, sample_question)
    
    # Short explanation should decrease confidence
    # Base: 0.7, -0.2 for length < 20 chars = 0.5
    assert confidence < 0.7, "Short explanation should have lower confidence"
    assert confidence >= 0.0, "Confidence should not be negative"


def test_confidence_calculation_with_very_fast_processing(validation_engine, sample_question):
    """Test confidence calculation with very fast processing time."""
    result = SolverResult(
        question_number=1,
        selected_option="B",
        explanation="The answer is B because 2 + 2 equals 4.",
        confidence=0.0,
        processing_time_ms=500.0,  # 0.5 seconds - very fast
        status="solved"
    )
    
    confidence = validation_engine.calculate_confidence(result, sample_question)
    
    # Very fast processing should decrease confidence
    # Base: 0.7, -0.15 for time < 1s = 0.55
    assert confidence < 0.7, "Very fast processing should lower confidence"


def test_confidence_calculation_with_slow_processing(validation_engine, sample_question):
    """Test confidence calculation with slow processing time."""
    result = SolverResult(
        question_number=1,
        selected_option="B",
        explanation="The answer is B because 2 + 2 equals 4.",
        confidence=0.0,
        processing_time_ms=26000.0,  # 26 seconds - slow
        status="solved"
    )
    
    confidence = validation_engine.calculate_confidence(result, sample_question)
    
    # Slow processing should decrease confidence
    # Base: 0.7, -0.1 for time > 25s = 0.6
    assert confidence < 0.7, "Slow processing should lower confidence"


def test_confidence_calculation_with_uncertainty_phrases(validation_engine, sample_question):
    """Test confidence calculation with uncertainty phrases in explanation."""
    result = SolverResult(
        question_number=1,
        selected_option="B",
        explanation="The answer might be B, possibly 4, but I'm not sure.",
        confidence=0.0,
        processing_time_ms=5000.0,
        status="solved"
    )
    
    confidence = validation_engine.calculate_confidence(result, sample_question)
    
    # Uncertainty phrases should significantly decrease confidence
    # Base: 0.7, -0.3 for uncertainty = 0.4
    assert confidence < 0.6, "Uncertainty phrases should significantly lower confidence"


def test_confidence_calculation_with_unsolved_status(validation_engine, sample_question):
    """Test confidence calculation for unsolved questions."""
    result = SolverResult(
        question_number=1,
        selected_option=None,
        explanation="Cannot determine the answer.",
        confidence=0.0,
        processing_time_ms=5000.0,
        status="unsolvable"
    )
    
    confidence = validation_engine.calculate_confidence(result, sample_question)
    
    # Unsolved questions should have 0.0 confidence
    assert confidence == 0.0, "Unsolved questions should have 0.0 confidence"


def test_confidence_calculation_with_timeout_status(validation_engine, sample_question):
    """Test confidence calculation for timeout questions."""
    result = SolverResult(
        question_number=1,
        selected_option=None,
        explanation="Processing timed out.",
        confidence=0.0,
        processing_time_ms=30000.0,
        status="timeout"
    )
    
    confidence = validation_engine.calculate_confidence(result, sample_question)
    
    # Timeout questions should have 0.0 confidence
    assert confidence == 0.0, "Timeout questions should have 0.0 confidence"


def test_confidence_calculation_optimal_conditions(validation_engine, sample_question):
    """Test confidence calculation under optimal conditions."""
    result = SolverResult(
        question_number=1,
        selected_option="B",
        explanation="The answer is B because 2 + 2 equals 4. This is a fundamental "
                   "arithmetic operation that combines two quantities of 2 to produce "
                   "a sum of 4. This can be verified through counting or basic addition.",
        confidence=0.0,
        processing_time_ms=5000.0,  # Normal processing time
        status="solved"
    )
    
    confidence = validation_engine.calculate_confidence(result, sample_question)
    
    # Optimal conditions: detailed explanation, no uncertainty, normal processing time
    # Base: 0.7, +0.1 for length > 100 = 0.8
    assert confidence >= 0.7, "Optimal conditions should have high confidence"
    assert confidence <= 1.0, "Confidence should not exceed 1.0"


# ── Uncertainty Detection Tests ───────────────────────────────────────────────

def test_uncertainty_detection_with_possibly(validation_engine):
    """Test uncertainty detection with 'possibly' phrase."""
    explanation = "The answer is possibly B."
    assert validation_engine._detect_uncertainty(explanation) is True


def test_uncertainty_detection_with_might_be(validation_engine):
    """Test uncertainty detection with 'might be' phrase."""
    explanation = "The answer might be C."
    assert validation_engine._detect_uncertainty(explanation) is True


def test_uncertainty_detection_with_unclear(validation_engine):
    """Test uncertainty detection with 'unclear' phrase."""
    explanation = "The question is unclear, but I think it's A."
    assert validation_engine._detect_uncertainty(explanation) is True


def test_uncertainty_detection_with_not_sure(validation_engine):
    """Test uncertainty detection with 'not sure' phrase."""
    explanation = "I'm not sure, but D seems correct."
    assert validation_engine._detect_uncertainty(explanation) is True


def test_uncertainty_detection_with_maybe(validation_engine):
    """Test uncertainty detection with 'maybe' phrase."""
    explanation = "Maybe the answer is A."
    assert validation_engine._detect_uncertainty(explanation) is True


def test_uncertainty_detection_with_probably(validation_engine):
    """Test uncertainty detection with 'probably' phrase."""
    explanation = "The answer is probably B."
    assert validation_engine._detect_uncertainty(explanation) is True


def test_uncertainty_detection_with_multiple_phrases(validation_engine):
    """Test uncertainty detection with multiple uncertainty phrases."""
    explanation = "I'm not sure, but it might be B, possibly C."
    assert validation_engine._detect_uncertainty(explanation) is True


def test_uncertainty_detection_with_confident_explanation(validation_engine):
    """Test uncertainty detection with a confident explanation."""
    explanation = "The answer is B because 2 + 2 equals 4."
    assert validation_engine._detect_uncertainty(explanation) is False


def test_uncertainty_detection_case_insensitive(validation_engine):
    """Test uncertainty detection is case-insensitive."""
    explanation = "The answer is POSSIBLY B."
    assert validation_engine._detect_uncertainty(explanation) is True


# ── Duplicate Question Detection Tests ────────────────────────────────────────

def test_duplicate_question_detection_with_different_answers(validation_engine):
    """Test detection of duplicate questions with different answers."""
    questions = [
        Question(
            number=1,
            text="What is 2 + 2?",
            options=[
                QuestionOption(label="A", text="3"),
                QuestionOption(label="B", text="4"),
                QuestionOption(label="C", text="5")
            ],
            page_number=1,
            has_image=False,
            question_type="math"
        ),
        Question(
            number=2,
            text="What is 2 + 2?",  # Duplicate text
            options=[
                QuestionOption(label="A", text="3"),
                QuestionOption(label="B", text="4"),
                QuestionOption(label="C", text="5")
            ],
            page_number=2,
            has_image=False,
            question_type="math"
        )
    ]
    
    results = [
        SolverResult(
            question_number=1,
            selected_option="B",
            explanation="2 + 2 = 4",
            confidence=0.0,
            processing_time_ms=5000.0,
            status="solved"
        ),
        SolverResult(
            question_number=2,
            selected_option="C",  # Different answer!
            explanation="2 + 2 = 5",
            confidence=0.0,
            processing_time_ms=5000.0,
            status="solved"
        )
    ]
    
    report = validation_engine.validate_batch(results, questions)
    
    # Both questions should be flagged
    assert 1 in report.flagged_questions, "Question 1 should be flagged"
    assert 2 in report.flagged_questions, "Question 2 should be flagged"
    
    # Should have duplicate_inconsistency issues
    duplicate_issues = [
        issue for issue in report.issues
        if issue.issue_type == "duplicate_inconsistency"
    ]
    assert len(duplicate_issues) > 0, "Should have duplicate_inconsistency issues"


def test_duplicate_question_detection_with_same_answers(validation_engine):
    """Test duplicate questions with same answers are not flagged."""
    questions = [
        Question(
            number=1,
            text="What is 2 + 2?",
            options=[
                QuestionOption(label="A", text="3"),
                QuestionOption(label="B", text="4"),
                QuestionOption(label="C", text="5")
            ],
            page_number=1,
            has_image=False,
            question_type="math"
        ),
        Question(
            number=2,
            text="What is 2 + 2?",  # Duplicate text
            options=[
                QuestionOption(label="A", text="3"),
                QuestionOption(label="B", text="4"),
                QuestionOption(label="C", text="5")
            ],
            page_number=2,
            has_image=False,
            question_type="math"
        )
    ]
    
    results = [
        SolverResult(
            question_number=1,
            selected_option="B",
            explanation="2 + 2 = 4",
            confidence=0.0,
            processing_time_ms=5000.0,
            status="solved"
        ),
        SolverResult(
            question_number=2,
            selected_option="B",  # Same answer
            explanation="2 + 2 = 4",
            confidence=0.0,
            processing_time_ms=5000.0,
            status="solved"
        )
    ]
    
    report = validation_engine.validate_batch(results, questions)
    
    # Should not have duplicate_inconsistency issues
    duplicate_issues = [
        issue for issue in report.issues
        if issue.issue_type == "duplicate_inconsistency"
    ]
    assert len(duplicate_issues) == 0, "Consistent duplicates should not be flagged"


def test_duplicate_question_detection_case_insensitive(validation_engine):
    """Test duplicate detection is case-insensitive."""
    questions = [
        Question(
            number=1,
            text="What is 2 + 2?",
            options=[
                QuestionOption(label="A", text="3"),
                QuestionOption(label="B", text="4")
            ],
            page_number=1,
            has_image=False,
            question_type="math"
        ),
        Question(
            number=2,
            text="WHAT IS 2 + 2?",  # Different case
            options=[
                QuestionOption(label="A", text="3"),
                QuestionOption(label="B", text="4")
            ],
            page_number=2,
            has_image=False,
            question_type="math"
        )
    ]
    
    results = [
        SolverResult(
            question_number=1,
            selected_option="B",
            explanation="2 + 2 = 4",
            confidence=0.0,
            processing_time_ms=5000.0,
            status="solved"
        ),
        SolverResult(
            question_number=2,
            selected_option="A",  # Different answer
            explanation="2 + 2 = 3",
            confidence=0.0,
            processing_time_ms=5000.0,
            status="solved"
        )
    ]
    
    report = validation_engine.validate_batch(results, questions)
    
    # Should detect duplicates despite case difference
    duplicate_issues = [
        issue for issue in report.issues
        if issue.issue_type == "duplicate_inconsistency"
    ]
    assert len(duplicate_issues) > 0, "Should detect duplicates regardless of case"


# ── Validation Report Generation Tests ────────────────────────────────────────

def test_validation_report_structure(validation_engine, sample_question, sample_solved_result):
    """Test validation report has correct structure."""
    report = validation_engine.validate_batch([sample_solved_result], [sample_question])
    
    # Check report structure
    assert hasattr(report, 'total_questions'), "Report should have total_questions"
    assert hasattr(report, 'issues'), "Report should have issues"
    assert hasattr(report, 'flagged_questions'), "Report should have flagged_questions"
    assert hasattr(report, 'average_confidence'), "Report should have average_confidence"
    
    # Check types
    assert isinstance(report.total_questions, int), "total_questions should be int"
    assert isinstance(report.issues, list), "issues should be list"
    assert isinstance(report.flagged_questions, set), "flagged_questions should be set"
    assert isinstance(report.average_confidence, float), "average_confidence should be float"


def test_validation_report_with_multiple_questions(validation_engine):
    """Test validation report with multiple questions."""
    questions = [
        Question(
            number=i,
            text=f"Question {i}",
            options=[
                QuestionOption(label="A", text="Option A"),
                QuestionOption(label="B", text="Option B")
            ],
            page_number=1,
            has_image=False,
            question_type="factual"
        )
        for i in range(1, 6)
    ]
    
    results = [
        SolverResult(
            question_number=i,
            selected_option="A",
            explanation=f"The answer to question {i} is A.",
            confidence=0.0,
            processing_time_ms=5000.0,
            status="solved"
        )
        for i in range(1, 6)
    ]
    
    report = validation_engine.validate_batch(results, questions)
    
    assert report.total_questions == 5, "Should have 5 questions"
    assert 0.0 <= report.average_confidence <= 1.0, "Average confidence should be in valid range"


def test_validation_report_with_low_confidence_questions(validation_engine):
    """Test validation report flags low confidence questions."""
    question = Question(
        number=1,
        text="What is the answer?",
        options=[
            QuestionOption(label="A", text="Option A"),
            QuestionOption(label="B", text="Option B")
        ],
        page_number=1,
        has_image=False,
        question_type="factual"
    )
    
    # Create result with conditions that lead to low confidence
    result = SolverResult(
        question_number=1,
        selected_option="A",
        explanation="Maybe A.",  # Short + uncertainty
        confidence=0.0,
        processing_time_ms=5000.0,
        status="solved"
    )
    
    report = validation_engine.validate_batch([result], [question])
    
    # Should be flagged for low confidence
    assert 1 in report.flagged_questions, "Low confidence question should be flagged"
    
    # Should have low_confidence issue
    low_conf_issues = [
        issue for issue in report.issues
        if issue.issue_type == "low_confidence"
    ]
    assert len(low_conf_issues) > 0, "Should have low_confidence issue"


def test_validation_report_average_confidence_calculation(validation_engine):
    """Test average confidence is calculated correctly."""
    questions = [
        Question(
            number=1,
            text="Question 1",
            options=[QuestionOption(label="A", text="A")],
            page_number=1,
            has_image=False,
            question_type="factual"
        ),
        Question(
            number=2,
            text="Question 2",
            options=[QuestionOption(label="A", text="A")],
            page_number=1,
            has_image=False,
            question_type="factual"
        )
    ]
    
    # Create results with known confidence factors
    results = [
        SolverResult(
            question_number=1,
            selected_option="A",
            explanation="This is a very detailed explanation that should increase confidence "
                       "because it provides thorough reasoning and analysis of the question.",
            confidence=0.0,
            processing_time_ms=5000.0,
            status="solved"
        ),
        SolverResult(
            question_number=2,
            selected_option="A",
            explanation="Short.",  # Short explanation
            confidence=0.0,
            processing_time_ms=5000.0,
            status="solved"
        )
    ]
    
    report = validation_engine.validate_batch(results, questions)
    
    # Calculate expected average manually
    conf1 = validation_engine.calculate_confidence(results[0], questions[0])
    conf2 = validation_engine.calculate_confidence(results[1], questions[1])
    expected_avg = (conf1 + conf2) / 2
    
    assert abs(report.average_confidence - expected_avg) < 0.001, \
        f"Average confidence should be {expected_avg:.4f}, got {report.average_confidence:.4f}"


def test_validation_report_with_empty_results(validation_engine):
    """Test validation report with empty results list."""
    report = validation_engine.validate_batch([], [])
    
    assert report.total_questions == 0, "Should have 0 questions"
    assert len(report.issues) == 0, "Should have no issues"
    assert len(report.flagged_questions) == 0, "Should have no flagged questions"
    assert report.average_confidence == 0.0, "Average confidence should be 0.0"


# ── Invalid Option Detection Tests ────────────────────────────────────────────

def test_invalid_option_detection(validation_engine, sample_question):
    """Test detection of invalid answer options."""
    result = SolverResult(
        question_number=1,
        selected_option="E",  # Invalid - question only has A, B, C, D
        explanation="The answer is E.",
        confidence=0.0,
        processing_time_ms=5000.0,
        status="solved"
    )
    
    issues = validation_engine.validate_answer(result, sample_question)
    
    # Should have invalid_option issue
    invalid_issues = [
        issue for issue in issues
        if issue.issue_type == "invalid_option"
    ]
    assert len(invalid_issues) > 0, "Should detect invalid option"
    assert invalid_issues[0].severity == "critical", "Invalid option should be critical"


def test_valid_option_no_issue(validation_engine, sample_question):
    """Test valid option does not create invalid_option issue."""
    result = SolverResult(
        question_number=1,
        selected_option="B",  # Valid option
        explanation="The answer is B because 2 + 2 equals 4.",
        confidence=0.0,
        processing_time_ms=5000.0,
        status="solved"
    )
    
    issues = validation_engine.validate_answer(result, sample_question)
    
    # Should not have invalid_option issue
    invalid_issues = [
        issue for issue in issues
        if issue.issue_type == "invalid_option"
    ]
    assert len(invalid_issues) == 0, "Valid option should not create invalid_option issue"


# ── Edge Cases and Error Handling ─────────────────────────────────────────────

def test_validation_with_missing_question(validation_engine):
    """Test validation handles missing question gracefully."""
    result = SolverResult(
        question_number=999,  # Question doesn't exist
        selected_option="A",
        explanation="Answer is A.",
        confidence=0.0,
        processing_time_ms=5000.0,
        status="solved"
    )
    
    question = Question(
        number=1,  # Different number
        text="Question 1",
        options=[QuestionOption(label="A", text="A")],
        page_number=1,
        has_image=False,
        question_type="factual"
    )
    
    # Should not crash
    report = validation_engine.validate_batch([result], [question])
    assert isinstance(report, ValidationReport), "Should return valid report"


def test_validation_with_none_selected_option(validation_engine, sample_question):
    """Test validation handles None selected_option."""
    result = SolverResult(
        question_number=1,
        selected_option=None,
        explanation="Could not determine answer.",
        confidence=0.0,
        processing_time_ms=5000.0,
        status="unsolvable"
    )
    
    # Should not crash
    issues = validation_engine.validate_answer(result, sample_question)
    assert isinstance(issues, list), "Should return list of issues"


def test_validation_with_empty_explanation(validation_engine, sample_question):
    """Test validation handles empty explanation."""
    result = SolverResult(
        question_number=1,
        selected_option="B",
        explanation="",
        confidence=0.0,
        processing_time_ms=5000.0,
        status="solved"
    )
    
    # Should not crash
    confidence = validation_engine.calculate_confidence(result, sample_question)
    assert 0.0 <= confidence <= 1.0, "Should return valid confidence"
    
    issues = validation_engine.validate_answer(result, sample_question)
    assert isinstance(issues, list), "Should return list of issues"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
