"""
Unit tests for session statistics calculation.
"""
import pytest
import time
from session_manager import SessionManager, SessionState
from question_parser import Question, QuestionOption
from ai_solver import SolverResult


@pytest.fixture
def session_manager():
    """Create a SessionManager instance for testing."""
    return SessionManager()


@pytest.fixture
def sample_questions():
    """Create sample questions for testing."""
    questions = []
    
    # Math question
    questions.append(Question(
        number=1,
        text="What is 2 + 2?",
        options=[
            QuestionOption(label="A", text="3"),
            QuestionOption(label="B", text="4"),
            QuestionOption(label="C", text="5"),
        ],
        page_number=1,
        has_image=False,
        question_type="math"
    ))
    
    # Logical question
    questions.append(Question(
        number=2,
        text="If all A are B, and all B are C, then all A are C?",
        options=[
            QuestionOption(label="A", text="True"),
            QuestionOption(label="B", text="False"),
        ],
        page_number=1,
        has_image=False,
        question_type="logical"
    ))
    
    # Factual question
    questions.append(Question(
        number=3,
        text="What is the capital of France?",
        options=[
            QuestionOption(label="A", text="London"),
            QuestionOption(label="B", text="Paris"),
            QuestionOption(label="C", text="Berlin"),
        ],
        page_number=2,
        has_image=False,
        question_type="factual"
    ))
    
    # Visual question
    questions.append(Question(
        number=4,
        text="What shape is shown in the image?",
        options=[
            QuestionOption(label="A", text="Circle"),
            QuestionOption(label="B", text="Square"),
            QuestionOption(label="C", text="Triangle"),
        ],
        page_number=2,
        has_image=True,
        question_type="visual"
    ))
    
    # Unknown type question
    questions.append(Question(
        number=5,
        text="Random question",
        options=[
            QuestionOption(label="A", text="Option A"),
            QuestionOption(label="B", text="Option B"),
        ],
        page_number=3,
        has_image=False,
        question_type=None
    ))
    
    return questions


@pytest.fixture
def sample_results():
    """Create sample solver results for testing."""
    results = {}
    
    # High confidence result
    results[1] = SolverResult(
        question_number=1,
        selected_option="B",
        explanation="2 + 2 equals 4",
        confidence=0.95,
        processing_time_ms=1500.0,
        status="solved"
    )
    
    # Medium confidence result
    results[2] = SolverResult(
        question_number=2,
        selected_option="A",
        explanation="This is a valid logical deduction",
        confidence=0.75,
        processing_time_ms=2000.0,
        status="solved"
    )
    
    # Low confidence result
    results[3] = SolverResult(
        question_number=3,
        selected_option="B",
        explanation="Paris is the capital of France",
        confidence=0.55,
        processing_time_ms=1800.0,
        status="solved"
    )
    
    # Unsolvable result
    results[4] = SolverResult(
        question_number=4,
        selected_option=None,
        explanation="Cannot determine shape from image",
        confidence=0.0,
        processing_time_ms=3000.0,
        status="unsolvable"
    )
    
    # Error result
    results[5] = SolverResult(
        question_number=5,
        selected_option=None,
        explanation="",
        confidence=0.0,
        processing_time_ms=500.0,
        status="error",
        error_message="Connection timeout"
    )
    
    return results


def test_calculate_average_confidence_with_solved_questions(session_manager, sample_questions, sample_results):
    """Test average confidence calculation with solved questions."""
    # Create session
    session = SessionState(
        session_id="test-session-1",
        status="completed",
        pdf_path="/tmp/test.pdf",
        total_questions=5,
        processed_count=5,
        solved_count=3,
        unsolvable_count=1,
        error_count=1,
        questions=sample_questions,
        results=sample_results
    )
    
    # Calculate average confidence
    avg_confidence = session_manager._calculate_average_confidence(session)
    
    # Expected: (0.95 + 0.75 + 0.55) / 3 = 0.75
    assert avg_confidence == pytest.approx(0.75, abs=0.01)


def test_calculate_average_confidence_with_no_solved_questions(session_manager):
    """Test average confidence calculation with no solved questions."""
    # Create session with no solved questions
    session = SessionState(
        session_id="test-session-2",
        status="completed",
        pdf_path="/tmp/test.pdf",
        total_questions=2,
        processed_count=2,
        solved_count=0,
        unsolvable_count=1,
        error_count=1,
        results={
            1: SolverResult(
                question_number=1,
                selected_option=None,
                explanation="Cannot solve",
                confidence=0.0,
                processing_time_ms=1000.0,
                status="unsolvable"
            ),
            2: SolverResult(
                question_number=2,
                selected_option=None,
                explanation="",
                confidence=0.0,
                processing_time_ms=500.0,
                status="error"
            )
        }
    )
    
    # Calculate average confidence
    avg_confidence = session_manager._calculate_average_confidence(session)
    
    # Expected: 0.0 (no solved questions)
    assert avg_confidence == 0.0


def test_calculate_correction_percentage_with_corrections(session_manager, sample_questions):
    """Test correction percentage calculation with manual corrections."""
    # Create session with 2 corrections out of 5 questions
    session = SessionState(
        session_id="test-session-3",
        status="completed",
        pdf_path="/tmp/test.pdf",
        total_questions=5,
        processed_count=5,
        questions=sample_questions,
        user_corrections={
            1: "C",  # Corrected from B to C
            3: "A"   # Corrected from B to A
        }
    )
    
    # Calculate correction percentage
    correction_pct = session_manager._calculate_correction_percentage(session)
    
    # Expected: (2 / 5) * 100 = 40.0%
    assert correction_pct == 40.0


def test_calculate_correction_percentage_with_no_corrections(session_manager, sample_questions):
    """Test correction percentage calculation with no corrections."""
    # Create session with no corrections
    session = SessionState(
        session_id="test-session-4",
        status="completed",
        pdf_path="/tmp/test.pdf",
        total_questions=5,
        processed_count=5,
        questions=sample_questions,
        user_corrections={}
    )
    
    # Calculate correction percentage
    correction_pct = session_manager._calculate_correction_percentage(session)
    
    # Expected: 0.0%
    assert correction_pct == 0.0


def test_calculate_correction_percentage_with_zero_questions(session_manager):
    """Test correction percentage calculation with zero questions."""
    # Create session with no questions
    session = SessionState(
        session_id="test-session-5",
        status="pending",
        pdf_path="/tmp/test.pdf",
        total_questions=0,
        user_corrections={}
    )
    
    # Calculate correction percentage
    correction_pct = session_manager._calculate_correction_percentage(session)
    
    # Expected: 0.0%
    assert correction_pct == 0.0


def test_calculate_question_type_distribution(session_manager, sample_questions):
    """Test question type distribution calculation."""
    # Create session
    session = SessionState(
        session_id="test-session-6",
        status="completed",
        pdf_path="/tmp/test.pdf",
        total_questions=5,
        questions=sample_questions
    )
    
    # Calculate distribution
    distribution = session_manager._calculate_question_type_distribution(session)
    
    # Expected: 1 math, 1 logical, 1 factual, 1 visual, 1 unknown
    assert distribution["math"]["count"] == 1
    assert distribution["math"]["percentage"] == 20.0
    
    assert distribution["logical"]["count"] == 1
    assert distribution["logical"]["percentage"] == 20.0
    
    assert distribution["factual"]["count"] == 1
    assert distribution["factual"]["percentage"] == 20.0
    
    assert distribution["visual"]["count"] == 1
    assert distribution["visual"]["percentage"] == 20.0
    
    assert distribution["unknown"]["count"] == 1
    assert distribution["unknown"]["percentage"] == 20.0


def test_calculate_question_type_distribution_with_no_questions(session_manager):
    """Test question type distribution with no questions."""
    # Create session with no questions
    session = SessionState(
        session_id="test-session-7",
        status="pending",
        pdf_path="/tmp/test.pdf",
        total_questions=0,
        questions=[]
    )
    
    # Calculate distribution
    distribution = session_manager._calculate_question_type_distribution(session)
    
    # Expected: all zeros
    for qtype in ["math", "logical", "factual", "visual", "unknown"]:
        assert distribution[qtype]["count"] == 0
        assert distribution[qtype]["percentage"] == 0.0


def test_calculate_processing_time_statistics(session_manager, sample_questions, sample_results):
    """Test processing time statistics calculation."""
    # Create session with timing information
    start_time = time.time() - 100  # Started 100 seconds ago
    end_time = time.time()
    
    session = SessionState(
        session_id="test-session-8",
        status="completed",
        pdf_path="/tmp/test.pdf",
        total_questions=5,
        processed_count=5,
        questions=sample_questions,
        results=sample_results,
        start_time=start_time,
        end_time=end_time
    )
    
    # Calculate statistics
    time_stats = session_manager._calculate_processing_time_statistics(session)
    
    # Verify total time
    assert time_stats["total_time_seconds"] == pytest.approx(100.0, abs=1.0)
    
    # Verify average time per question (100 seconds / 5 questions = 20 seconds)
    assert time_stats["average_time_per_question_seconds"] == pytest.approx(20.0, abs=1.0)
    
    # Verify questions per minute (5 questions / 100 seconds * 60 = 3.0 q/min)
    assert time_stats["questions_per_minute"] == pytest.approx(3.0, abs=0.5)
    
    # Verify average processing time (1500 + 2000 + 1800 + 3000 + 500) / 5 = 1760 ms
    assert time_stats["average_processing_time_ms"] == pytest.approx(1760.0, abs=10.0)
    
    # Verify min and max processing times
    assert time_stats["min_processing_time_ms"] == 500.0
    assert time_stats["max_processing_time_ms"] == 3000.0


def test_calculate_processing_time_statistics_with_no_results(session_manager, sample_questions):
    """Test processing time statistics with no results."""
    # Create session with no results
    session = SessionState(
        session_id="test-session-9",
        status="processing",
        pdf_path="/tmp/test.pdf",
        total_questions=5,
        processed_count=0,
        questions=sample_questions,
        results={},
        start_time=time.time()
    )
    
    # Calculate statistics
    time_stats = session_manager._calculate_processing_time_statistics(session)
    
    # Expected: zeros for most metrics
    assert time_stats["average_time_per_question_seconds"] == 0.0
    assert time_stats["questions_per_minute"] == 0.0
    assert time_stats["average_processing_time_ms"] == 0.0
    assert time_stats["min_processing_time_ms"] == 0.0
    assert time_stats["max_processing_time_ms"] == 0.0


def test_calculate_session_statistics_complete(session_manager, sample_questions, sample_results):
    """Test complete session statistics calculation."""
    # Create a complete session
    start_time = time.time() - 100
    end_time = time.time()
    
    session = SessionState(
        session_id="test-session-10",
        status="completed",
        pdf_path="/tmp/test.pdf",
        total_questions=5,
        processed_count=5,
        solved_count=3,
        unsolvable_count=1,
        error_count=1,
        questions=sample_questions,
        results=sample_results,
        start_time=start_time,
        end_time=end_time,
        user_corrections={1: "C", 3: "A"}
    )
    
    # Store session in manager
    session_manager.active_sessions[session.session_id] = session
    session_manager.session_locks[session.session_id] = __import__('threading').Lock()
    
    # Calculate statistics
    stats = session_manager.calculate_session_statistics(session.session_id)
    
    # Verify all statistics are present
    assert stats is not None
    assert stats["session_id"] == "test-session-10"
    assert stats["status"] == "completed"
    assert stats["total_questions"] == 5
    assert stats["processed_count"] == 5
    assert stats["solved_count"] == 3
    assert stats["unsolvable_count"] == 1
    assert stats["error_count"] == 1
    
    # Verify average confidence
    assert stats["average_confidence"] == pytest.approx(0.75, abs=0.01)
    
    # Verify correction percentage
    assert stats["manual_correction_percentage"] == 40.0
    assert stats["manual_corrections_count"] == 2
    
    # Verify question type distribution
    assert "question_type_distribution" in stats
    assert stats["question_type_distribution"]["math"]["count"] == 1
    assert stats["question_type_distribution"]["logical"]["count"] == 1
    assert stats["question_type_distribution"]["factual"]["count"] == 1
    assert stats["question_type_distribution"]["visual"]["count"] == 1
    assert stats["question_type_distribution"]["unknown"]["count"] == 1
    
    # Verify processing time statistics
    assert "processing_time_statistics" in stats
    assert stats["processing_time_statistics"]["total_time_seconds"] > 0
    assert stats["processing_time_statistics"]["questions_per_minute"] > 0


def test_calculate_session_statistics_nonexistent_session(session_manager):
    """Test statistics calculation for nonexistent session."""
    # Try to calculate statistics for nonexistent session
    stats = session_manager.calculate_session_statistics("nonexistent-session")
    
    # Expected: None
    assert stats is None


def test_calculate_session_statistics_empty_session(session_manager):
    """Test statistics calculation for empty session."""
    # Create empty session
    session = SessionState(
        session_id="test-session-11",
        status="pending",
        pdf_path="/tmp/test.pdf",
        total_questions=0,
        questions=[],
        results={}
    )
    
    # Store session in manager
    session_manager.active_sessions[session.session_id] = session
    session_manager.session_locks[session.session_id] = __import__('threading').Lock()
    
    # Calculate statistics
    stats = session_manager.calculate_session_statistics(session.session_id)
    
    # Verify statistics for empty session
    assert stats is not None
    assert stats["total_questions"] == 0
    assert stats["processed_count"] == 0
    assert stats["average_confidence"] == 0.0
    assert stats["manual_correction_percentage"] == 0.0
    assert stats["manual_corrections_count"] == 0


def test_statistics_include_all_required_fields(session_manager, sample_questions, sample_results):
    """
    Test that session statistics include all required fields per Requirement 14.2 and 14.3.
    
    Validates:
    - 14.2: Average confidence scores per session
    - 14.3: Percentage of questions requiring manual correction
    """
    # Create a complete session
    start_time = time.time() - 100
    end_time = time.time()
    
    session = SessionState(
        session_id="test-stats-complete",
        status="completed",
        pdf_path="/tmp/test.pdf",
        total_questions=5,
        processed_count=5,
        solved_count=3,
        unsolvable_count=1,
        error_count=1,
        questions=sample_questions,
        results=sample_results,
        start_time=start_time,
        end_time=end_time,
        user_corrections={1: "C", 3: "A"}
    )
    
    # Store session in manager
    session_manager.active_sessions[session.session_id] = session
    session_manager.session_locks[session.session_id] = __import__('threading').Lock()
    
    # Calculate statistics
    stats = session_manager.calculate_session_statistics(session.session_id)
    
    # Requirement 14.2: Average confidence scores per session
    assert "average_confidence" in stats
    assert isinstance(stats["average_confidence"], float)
    assert 0.0 <= stats["average_confidence"] <= 1.0
    
    # Requirement 14.3: Percentage of questions requiring manual correction
    assert "manual_correction_percentage" in stats
    assert isinstance(stats["manual_correction_percentage"], float)
    assert 0.0 <= stats["manual_correction_percentage"] <= 100.0
    assert "manual_corrections_count" in stats
    assert isinstance(stats["manual_corrections_count"], int)
    
    # Verify values are correct
    assert stats["average_confidence"] == pytest.approx(0.75, abs=0.01)
    assert stats["manual_correction_percentage"] == 40.0
    assert stats["manual_corrections_count"] == 2


def test_statistics_with_all_solved_questions(session_manager):
    """Test statistics when all questions are solved with high confidence."""
    questions = [
        Question(
            number=i,
            text=f"Question {i}",
            options=[QuestionOption(label="A", text="Option A")],
            page_number=1,
            question_type="factual"
        )
        for i in range(1, 6)
    ]
    
    results = {
        i: SolverResult(
            question_number=i,
            selected_option="A",
            explanation=f"Explanation {i}",
            confidence=0.9,
            processing_time_ms=1000.0,
            status="solved"
        )
        for i in range(1, 6)
    }
    
    session = SessionState(
        session_id="test-all-solved",
        status="completed",
        pdf_path="/tmp/test.pdf",
        total_questions=5,
        processed_count=5,
        solved_count=5,
        questions=questions,
        results=results,
        user_corrections={}
    )
    
    session_manager.active_sessions[session.session_id] = session
    session_manager.session_locks[session.session_id] = __import__('threading').Lock()
    
    stats = session_manager.calculate_session_statistics(session.session_id)
    
    # All solved with same confidence
    assert stats["average_confidence"] == 0.9
    # No corrections
    assert stats["manual_correction_percentage"] == 0.0
    assert stats["manual_corrections_count"] == 0


def test_statistics_with_all_corrections(session_manager):
    """Test statistics when all questions require manual correction."""
    questions = [
        Question(
            number=i,
            text=f"Question {i}",
            options=[QuestionOption(label="A", text="Option A")],
            page_number=1,
            question_type="factual"
        )
        for i in range(1, 4)
    ]
    
    results = {
        i: SolverResult(
            question_number=i,
            selected_option="A",
            explanation=f"Explanation {i}",
            confidence=0.5,
            processing_time_ms=1000.0,
            status="solved"
        )
        for i in range(1, 4)
    }
    
    session = SessionState(
        session_id="test-all-corrections",
        status="completed",
        pdf_path="/tmp/test.pdf",
        total_questions=3,
        processed_count=3,
        solved_count=3,
        questions=questions,
        results=results,
        user_corrections={1: "B", 2: "C", 3: "D"}  # All corrected
    )
    
    session_manager.active_sessions[session.session_id] = session
    session_manager.session_locks[session.session_id] = __import__('threading').Lock()
    
    stats = session_manager.calculate_session_statistics(session.session_id)
    
    # 100% correction rate
    assert stats["manual_correction_percentage"] == 100.0
    assert stats["manual_corrections_count"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



def test_statistics_include_all_required_fields(session_manager, sample_questions, sample_results):
    """
    Test that session statistics include all required fields per Requirement 14.2 and 14.3.
    
    Validates:
    - 14.2: Average confidence scores per session
    - 14.3: Percentage of questions requiring manual correction
    """
    # Create a complete session
    start_time = time.time() - 100
    end_time = time.time()
    
    session = SessionState(
        session_id="test-stats-complete",
        status="completed",
        pdf_path="/tmp/test.pdf",
        total_questions=5,
        processed_count=5,
        solved_count=3,
        unsolvable_count=1,
        error_count=1,
        questions=sample_questions,
        results=sample_results,
        start_time=start_time,
        end_time=end_time,
        user_corrections={1: "C", 3: "A"}
    )
    
    # Store session in manager
    session_manager.active_sessions[session.session_id] = session
    session_manager.session_locks[session.session_id] = __import__('threading').Lock()
    
    # Calculate statisticassert stats["manual_corrections_count"] == 3
ions=3,
        processed_count=3,
        solved_count=3,
        questions=questions,
        results=results,
        user_corrections={1: "B", 2: "C", 3: "D"}  # All corrected
    )
    
    session_manager.active_sessions[session.session_id] = session
    session_manager.session_locks[session.session_id] = __import__('threading').Lock()
    
    stats = session_manager.calculate_session_statistics(session.session_id)
    
    # 100% correction rate
    assert stats["manual_correction_percentage"] == 100.0
    corrections",
        status="completed",
        pdf_path="/tmp/test.pdf",
        total_quests=[QuestionOption(label="A", text="Option A")],
            page_number=1,
            question_type="factual"
        )
        for i in range(1, 4)
    ]
    
    results = {
        i: SolverResult(
            question_number=i,
            selected_option="A",
            explanation=f"Explanation {i}",
            confidence=0.5,
            processing_time_ms=1000.0,
            status="solved"
        )
        for i in range(1, 4)
    }
    
    session = SessionState(
        session_id="test-all-     text=f"Question {i}",
            option('threading').Lock()
    
    stats = session_manager.calculate_session_statistics(session.session_id)
    
    # All solved with same confidence
    assert stats["average_confidence"] == 0.9
    # No corrections
    assert stats["manual_correction_percentage"] == 0.0
    assert stats["manual_corrections_count"] == 0


def test_statistics_with_all_corrections(session_manager):
    """Test statistics when all questions require manual correction."""
    questions = [
        Question(
            number=i,
       .session_locks[session.session_id] = __import__  confidence=0.9,
            processing_time_ms=1000.0,
            status="solved"
        )
        for i in range(1, 6)
    }
    
    session = SessionState(
        session_id="test-all-solved",
        status="completed",
        pdf_path="/tmp/test.pdf",
        total_questions=5,
        processed_count=5,
        solved_count=5,
        questions=questions,
        results=results,
        user_corrections={}
    )
    
    session_manager.active_sessions[session.session_id] = session
    session_manager     selected_option="A",
            explanation=f"Explanation {i}",
          corrections_count"] == 2


def test_statistics_with_all_solved_questions(session_manager):
    """Test statistics when all questions are solved with high confidence."""
    questions = [
        Question(
            number=i,
            text=f"Question {i}",
            options=[QuestionOption(label="A", text="Option A")],
            page_number=1,
            question_type="factual"
        )
        for i in range(1, 6)
    ]
    
    results = {
        i: SolverResult(
            question_number=i,
        correct
    assert stats["average_confidence"] == pytest.approx(0.75, abs=0.01)
    assert stats["manual_correction_percentage"] == 40.0
    assert stats["manual_sert isinstance(stats["manual_correction_percentage"], float)
    assert 0.0 <= stats["manual_correction_percentage"] <= 100.0
    assert "manual_corrections_count" in stats
    assert isinstance(stats["manual_corrections_count"], int)
    
    # Verify values arefidence"] <= 1.0
    
    # Requirement 14.3: Percentage of questions requiring manual correction
    assert "manual_correction_percentage" in stats
    asession
    assert "average_confidence" in stats
    assert isinstance(stats["average_confidence"], float)
    assert 0.0 <= stats["average_consion_statistics(session.session_id)
    
    # Requirement 14.2: Average confidence scores per ss
    stats = session_manager.calculate_ses