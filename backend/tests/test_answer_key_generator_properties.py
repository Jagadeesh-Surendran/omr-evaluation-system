"""
test_answer_key_generator_properties.py
----------------------------------------
Property-based tests for answer_key_generator.py module.
Tests universal properties that should hold across all valid inputs.

**Validates: Requirements 7.1-7.5, 12.1-12.4, 12.6, 15.5**
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from hypothesis import given, settings, strategies as st, assume
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import csv
import io
import json

from answer_key_generator import AnswerKeyGenerator, AnswerKeyMetadata
from ai_solver import SolverResult
from question_parser import Question, QuestionOption
from strategies.question_strategies import question_strategy
from strategies.solver_strategies import solver_result_strategy, solved_result_strategy


# ── Mock SessionState ─────────────────────────────────────────────────────────

@dataclass
class MockSessionState:
    """Mock SessionState for property testing."""
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


# ── Hypothesis Strategies ─────────────────────────────────────────────────────

@st.composite
def session_state_strategy(draw):
    """Strategy for generating MockSessionState objects."""
    session_id = draw(st.text(min_size=5, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        blacklist_characters='\n\r\t'
    )))
    
    # Generate questions
    num_questions = draw(st.integers(min_value=1, max_value=20))
    questions = [draw(question_strategy()) for _ in range(num_questions)]
    
    # Assign sequential question numbers
    for i, q in enumerate(questions, start=1):
        q.number = i
    
    # Generate results for each question
    results = {}
    solved_count = 0
    unsolvable_count = 0
    error_count = 0
    
    for i in range(1, num_questions + 1):
        result = draw(solver_result_strategy(question_number=i))
        results[i] = result
        
        if result.status == "solved":
            solved_count += 1
        elif result.status in ["unsolvable", "timeout"]:
            unsolvable_count += 1
        elif result.status == "error":
            error_count += 1
    
    # Generate user corrections (for some questions)
    num_corrections = draw(st.integers(min_value=0, max_value=min(3, num_questions)))
    user_corrections = {}
    if num_corrections > 0:
        correction_indices = draw(st.lists(
            st.integers(min_value=1, max_value=num_questions),
            min_size=num_corrections,
            max_size=num_corrections,
            unique=True
        ))
        for idx in correction_indices:
            user_corrections[idx] = draw(st.sampled_from(['A', 'B', 'C', 'D', 'E']))
    
    return MockSessionState(
        session_id=session_id,
        status="completed",
        pdf_path="/test/path.pdf",
        total_questions=num_questions,
        processed_count=num_questions,
        solved_count=solved_count,
        unsolvable_count=unsolvable_count,
        error_count=error_count,
        questions=questions,
        results=results,
        user_corrections=user_corrections
    )


# ── Property 23: OMR Format Compatibility ─────────────────────────────────────

@given(session=session_state_strategy())
@settings(max_examples=100, deadline=60000)
def test_property_23_omr_format_compatibility(session):
    """
    **Property 23: OMR Format Compatibility**
    
    For any generated answer key, it must be in the format {question_idx: option_idx}
    with 0-based integer indices, compatible with the existing OMR evaluation system.
    
    **Validates: Requirements 7.1, 7.2**
    """
    generator = AnswerKeyGenerator()
    result = generator.generate_json(session)
    
    # Must have answer_key field
    assert "answer_key" in result
    answer_key = result["answer_key"]
    
    # Answer key must be a dict
    assert isinstance(answer_key, dict)
    
    # All keys must be 0-based integer indices
    for key in answer_key.keys():
        assert isinstance(key, int), f"Key {key} is not an integer"
        assert key >= 0, f"Key {key} is negative (not 0-based)"
        assert key < session.total_questions, f"Key {key} exceeds total questions"
    
    # All values must be 0-based integer indices (0-4 for A-E)
    for value in answer_key.values():
        assert isinstance(value, int), f"Value {value} is not an integer"
        assert 0 <= value <= 4, f"Value {value} is not in range 0-4 (A-E)"


# ── Property 24: Answer Key Metadata Completeness ─────────────────────────────

@given(session=session_state_strategy())
@settings(max_examples=100, deadline=60000)
def test_property_24_metadata_completeness(session):
    """
    **Property 24: Answer Key Metadata Completeness**
    
    For any generated answer key, the metadata must include total_questions,
    solved_count, unsolvable_count, and average_confidence fields.
    
    **Validates: Requirements 7.3**
    """
    generator = AnswerKeyGenerator()
    result = generator.generate_json(session)
    
    # Must have metadata field
    assert "metadata" in result
    metadata = result["metadata"]
    
    # Must be a dict
    assert isinstance(metadata, dict)
    
    # Required fields must be present
    required_fields = [
        "total_questions",
        "solved_count",
        "unsolvable_count",
        "average_confidence"
    ]
    
    for field in required_fields:
        assert field in metadata, f"Missing required field: {field}"
    
    # Validate field types and values
    assert isinstance(metadata["total_questions"], int)
    assert metadata["total_questions"] >= 0
    
    assert isinstance(metadata["solved_count"], int)
    assert metadata["solved_count"] >= 0
    
    assert isinstance(metadata["unsolvable_count"], int)
    assert metadata["unsolvable_count"] >= 0
    
    assert isinstance(metadata["average_confidence"], float)
    assert 0.0 <= metadata["average_confidence"] <= 1.0
    
    # Counts should sum correctly
    assert metadata["solved_count"] + metadata["unsolvable_count"] <= metadata["total_questions"]


# ── Property 25: CSV Export Format ────────────────────────────────────────────

@given(session=session_state_strategy())
@settings(max_examples=100, deadline=60000)
def test_property_25_csv_export_format(session):
    """
    **Property 25: CSV Export Format**
    
    For any CSV export, it must contain columns for question_number, correct_answer,
    confidence, and explanation, with one row per question.
    
    **Validates: Requirements 7.4**
    """
    generator = AnswerKeyGenerator()
    csv_content = generator.generate_csv(session)
    
    # Must be a non-empty string
    assert isinstance(csv_content, str)
    assert len(csv_content) > 0
    
    # Parse CSV
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    
    # Must have at least one row (header is handled by DictReader)
    assert len(rows) > 0
    
    # Required columns must be present
    required_columns = [
        "question_number",
        "correct_answer",
        "confidence",
        "explanation"
    ]
    
    for column in required_columns:
        assert column in rows[0], f"Missing required column: {column}"
    
    # Must have one row per question
    assert len(rows) == session.total_questions
    
    # Validate each row
    for row in rows:
        # question_number must be a valid integer
        assert row["question_number"].isdigit()
        q_num = int(row["question_number"])
        assert 1 <= q_num <= session.total_questions
        
        # correct_answer must be A-E or N/A
        assert row["correct_answer"] in ['A', 'B', 'C', 'D', 'E', 'N/A']
        
        # confidence must be a valid float between 0 and 1
        confidence = float(row["confidence"])
        assert 0.0 <= confidence <= 1.0
        
        # explanation must be present (can be empty string)
        assert "explanation" in row


# ── Property 26: Unsolvable Question Handling in Answer Key ───────────────────

@given(session=session_state_strategy())
@settings(max_examples=100, deadline=60000)
def test_property_26_unsolvable_question_handling(session):
    """
    **Property 26: Unsolvable Question Handling in Answer Key**
    
    For any answer key with unsolvable questions, those positions should be marked
    as null in the answer_key dict and included in a separate unsolvable list.
    
    **Validates: Requirements 7.5**
    """
    generator = AnswerKeyGenerator()
    result = generator.generate_json(session)
    
    # Must have unsolvable field
    assert "unsolvable" in result
    unsolvable_list = result["unsolvable"]
    
    # Must be a list
    assert isinstance(unsolvable_list, list)
    
    # Check that unsolvable questions are not in answer_key
    answer_key = result["answer_key"]
    
    for q_num in unsolvable_list:
        # Question number must be valid
        assert 1 <= q_num <= session.total_questions
        
        # Convert to 0-based index
        q_idx = q_num - 1
        
        # Should NOT be in answer_key (or if present, should be null)
        assert q_idx not in answer_key, \
            f"Unsolvable question {q_num} should not be in answer_key"
    
    # Verify that questions in unsolvable list actually have non-solved status
    for q_num in unsolvable_list:
        if q_num in session.results:
            result_obj = session.results[q_num]
            assert result_obj.status != "solved" or result_obj.selected_option is None, \
                f"Question {q_num} in unsolvable list but has status {result_obj.status}"


# ── Property 41: Multi-Format Export Compatibility ────────────────────────────

@given(session=session_state_strategy())
@settings(max_examples=50, deadline=60000)
def test_property_41_multi_format_export_compatibility(session):
    """
    **Property 41: Multi-Format Export Compatibility**
    
    For any completed session, the answer key should be exportable in JSON format
    (compatible with OMR system), CSV format (with required columns), and PDF
    report format.
    
    **Validates: Requirements 12.1, 12.2**
    """
    generator = AnswerKeyGenerator()
    
    # Test JSON export
    json_result = generator.generate_json(session)
    assert isinstance(json_result, dict)
    assert "answer_key" in json_result
    assert "metadata" in json_result
    
    # Verify JSON is serializable
    json_str = json.dumps(json_result)
    assert len(json_str) > 0
    
    # Test CSV export
    csv_content = generator.generate_csv(session)
    assert isinstance(csv_content, str)
    assert len(csv_content) > 0
    
    # Verify CSV is parseable
    reader = csv.DictReader(io.StringIO(csv_content))
    csv_rows = list(reader)
    assert len(csv_rows) == session.total_questions
    
    # Test PDF export (creates a text file for now)
    import tempfile
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    tmp_name = tmp.name
    tmp.close()  # Close before passing to generate_pdf_report
    
    try:
        pdf_path = generator.generate_pdf_report(session, tmp_name)
        assert os.path.exists(pdf_path)
        
        # Verify file has content
        with open(pdf_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert len(content) > 0
            assert session.session_id in content
    finally:
        # Cleanup
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


# ── Property 42: Manual Correction Indicators ─────────────────────────────────

@given(session=session_state_strategy())
@settings(max_examples=100, deadline=60000)
def test_property_42_manual_correction_indicators(session):
    """
    **Property 42: Manual Correction Indicators**
    
    For any answer key export where manual corrections were made, all export
    formats should include a "modified" indicator for corrected answers.
    
    **Validates: Requirements 12.4**
    """
    # Only test if there are manual corrections
    assume(len(session.user_corrections) > 0)
    
    generator = AnswerKeyGenerator()
    
    # Test JSON export
    json_result = generator.generate_json(session)
    metadata = json_result["metadata"]
    assert metadata["manual_corrections"] == len(session.user_corrections)
    
    # Test CSV export
    csv_content = generator.generate_csv(session)
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    
    # Check that modified column exists
    assert "modified" in rows[0]
    
    # Count modified rows
    modified_count = sum(1 for row in rows if row["modified"] == "Yes")
    assert modified_count == len(session.user_corrections)
    
    # Verify that corrected questions are marked as modified
    for q_num in session.user_corrections.keys():
        row = rows[q_num - 1]  # 0-based index
        assert row["modified"] == "Yes", \
            f"Question {q_num} was corrected but not marked as modified"
        assert row["confidence"] == "1.00", \
            f"Question {q_num} was corrected but confidence is not 1.00"


# ── Property 53: Answer Key Immutability After Approval ───────────────────────

@given(session=session_state_strategy())
@settings(max_examples=100, deadline=60000)
def test_property_53_immutability_after_approval(session):
    """
    **Property 53: Answer Key Immutability After Approval**
    
    For any approved answer key, it should be marked as immutable, and any
    subsequent changes should create a new version rather than modifying the
    approved version.
    
    **Validates: Requirements 15.5**
    """
    generator = AnswerKeyGenerator()
    
    # Approve the answer key
    result = generator.approve_answer_key(session.session_id, "test_user")
    assert result is True
    
    # Verify approval is recorded
    assert session.session_id in generator.approved_sessions
    approval = generator.approved_sessions[session.session_id]
    assert approval.approved is True
    assert approval.approved_by == "test_user"
    assert approval.approved_at is not None
    
    # Attempt to approve again should fail (immutability)
    result2 = generator.approve_answer_key(session.session_id, "another_user")
    assert result2 is False
    
    # Original approval should remain unchanged
    approval_after = generator.approved_sessions[session.session_id]
    assert approval_after.approved_by == "test_user"
    assert approval_after.approved_at == approval.approved_at


# ── Additional Property: JSON-CSV Consistency ──────────────────────────────────

@given(session=session_state_strategy())
@settings(max_examples=50, deadline=60000)
def test_property_json_csv_consistency(session):
    """
    **Additional Property: JSON-CSV Consistency**
    
    For any session, the JSON and CSV exports should contain consistent answer data.
    This ensures that different export formats represent the same answer key.
    
    **Validates: Requirements 12.1, 12.2**
    """
    generator = AnswerKeyGenerator()
    
    # Generate both formats
    json_result = generator.generate_json(session)
    csv_content = generator.generate_csv(session)
    
    # Parse CSV
    reader = csv.DictReader(io.StringIO(csv_content))
    csv_rows = list(reader)
    
    # Check consistency for each question
    for row in csv_rows:
        q_num = int(row["question_number"])
        q_idx = q_num - 1  # 0-based index
        
        if row["correct_answer"] != "N/A":
            # Question has an answer
            assert q_idx in json_result["answer_key"], \
                f"Question {q_num} has answer in CSV but not in JSON"
            
            # Convert CSV answer to index
            csv_answer_idx = ord(row["correct_answer"]) - ord('A')
            json_answer_idx = json_result["answer_key"][q_idx]
            
            assert csv_answer_idx == json_answer_idx, \
                f"Question {q_num}: CSV answer {row['correct_answer']} " \
                f"(idx {csv_answer_idx}) != JSON answer idx {json_answer_idx}"
        else:
            # Question is unsolvable
            assert q_idx not in json_result["answer_key"], \
                f"Question {q_num} is N/A in CSV but has answer in JSON"


# ── Additional Property: Metadata Accuracy ─────────────────────────────────────

@given(session=session_state_strategy())
@settings(max_examples=100, deadline=60000)
def test_property_metadata_accuracy(session):
    """
    **Additional Property: Metadata Accuracy**
    
    For any session, the metadata should accurately reflect the session statistics.
    
    **Validates: Requirements 7.3**
    """
    generator = AnswerKeyGenerator()
    metadata = generator.get_metadata(session)
    
    # Verify counts match session
    assert metadata.total_questions == session.total_questions
    assert metadata.solved_count == session.solved_count
    assert metadata.unsolvable_count == session.unsolvable_count
    assert metadata.manual_corrections == len(session.user_corrections)
    
    # Verify average confidence calculation
    solved_results = [
        r for r in session.results.values()
        if r.status == "solved"
    ]
    
    if solved_results:
        expected_avg = sum(r.confidence for r in solved_results) / len(solved_results)
        assert abs(metadata.average_confidence - expected_avg) < 0.01
    else:
        assert metadata.average_confidence == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
