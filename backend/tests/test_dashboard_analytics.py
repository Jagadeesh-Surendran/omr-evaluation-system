"""
Tests for Dashboard Analytics module.
"""
import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime
from dashboard_analytics import DashboardAnalytics


@pytest.fixture
def temp_sessions_dir():
    """Create a temporary sessions directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_session_data(temp_sessions_dir):
    """Create sample session data for testing."""
    # Create session 1
    session1_id = "test-session-1"
    session1_dir = os.path.join(temp_sessions_dir, session1_id)
    os.makedirs(os.path.join(session1_dir, "logs"), exist_ok=True)
    
    # Session metadata
    session1_data = {
        "session_id": session1_id,
        "status": "completed",
        "total_questions": 10,
        "solved_count": 8,
        "unsolvable_count": 1,
        "error_count": 1
    }
    
    with open(os.path.join(session1_dir, "session.json"), 'w') as f:
        json.dump(session1_data, f)
    
    # Solver responses
    solver_responses = [
        {
            "timestamp": "2024-01-15T10:00:00",
            "data": {
                "question_number": 1,
                "question_text": "What is 2+2?",
                "selected_answer": "C",
                "confidence": 0.95,
                "processing_time_ms": 1200,
                "status": "solved"
            }
        },
        {
            "timestamp": "2024-01-15T10:01:00",
            "data": {
                "question_number": 2,
                "question_text": "Calculate the integral",
                "selected_answer": "A",
                "confidence": 0.85,
                "processing_time_ms": 1500,
                "status": "solved"
            }
        },
        {
            "timestamp": "2024-01-15T10:02:00",
            "data": {
                "question_number": 3,
                "question_text": "Timeout question",
                "selected_answer": None,
                "confidence": 0.0,
                "processing_time_ms": 30000,
                "status": "timeout",
                "error_message": "Timeout after 30s"
            }
        }
    ]
    
    with open(os.path.join(session1_dir, "logs", "solver_responses.jsonl"), 'w') as f:
        for response in solver_responses:
            f.write(json.dumps(response) + '\n')
    
    # User corrections
    corrections = [
        {
            "timestamp": "2024-01-15T10:05:00",
            "data": {
                "question_number": 5,
                "original_answer": "B",
                "corrected_answer": "C"
            }
        }
    ]
    
    with open(os.path.join(session1_dir, "logs", "user_corrections.jsonl"), 'w') as f:
        for correction in corrections:
            f.write(json.dumps(correction) + '\n')
    
    # Create session 2
    session2_id = "test-session-2"
    session2_dir = os.path.join(temp_sessions_dir, session2_id)
    os.makedirs(os.path.join(session2_dir, "logs"), exist_ok=True)
    
    session2_data = {
        "session_id": session2_id,
        "status": "completed",
        "total_questions": 5,
        "solved_count": 5,
        "unsolvable_count": 0,
        "error_count": 0
    }
    
    with open(os.path.join(session2_dir, "session.json"), 'w') as f:
        json.dump(session2_data, f)
    
    solver_responses2 = [
        {
            "timestamp": "2024-01-16T10:00:00",
            "data": {
                "question_number": 1,
                "question_text": "What follows in the sequence?",
                "selected_answer": "B",
                "confidence": 0.90,
                "processing_time_ms": 1100,
                "status": "solved"
            }
        }
    ]
    
    with open(os.path.join(session2_dir, "logs", "solver_responses.jsonl"), 'w') as f:
        for response in solver_responses2:
            f.write(json.dumps(response) + '\n')
    
    return temp_sessions_dir


def test_dashboard_initialization(temp_sessions_dir):
    """Test DashboardAnalytics initialization."""
    analytics = DashboardAnalytics(temp_sessions_dir)
    assert analytics.sessions_dir == temp_sessions_dir


def test_get_all_session_ids(sample_session_data):
    """Test getting all session IDs."""
    analytics = DashboardAnalytics(sample_session_data)
    session_ids = analytics._get_all_session_ids()
    
    assert len(session_ids) == 2
    assert "test-session-1" in session_ids
    assert "test-session-2" in session_ids


def test_load_session_data(sample_session_data):
    """Test loading session metadata."""
    analytics = DashboardAnalytics(sample_session_data)
    session_data = analytics._load_session_data("test-session-1")
    
    assert session_data is not None
    assert session_data["session_id"] == "test-session-1"
    assert session_data["total_questions"] == 10
    assert session_data["solved_count"] == 8


def test_load_solver_responses(sample_session_data):
    """Test loading solver responses."""
    analytics = DashboardAnalytics(sample_session_data)
    responses = analytics._load_solver_responses("test-session-1")
    
    assert len(responses) == 3
    assert responses[0]["data"]["question_number"] == 1
    assert responses[0]["data"]["confidence"] == 0.95


def test_load_user_corrections(sample_session_data):
    """Test loading user corrections."""
    analytics = DashboardAnalytics(sample_session_data)
    corrections = analytics._load_user_corrections("test-session-1")
    
    assert len(corrections) == 1
    assert corrections[0]["data"]["question_number"] == 5
    assert corrections[0]["data"]["corrected_answer"] == "C"


def test_infer_question_type():
    """Test question type inference."""
    analytics = DashboardAnalytics()
    
    # Math questions
    assert analytics._infer_question_type("Calculate 2+2") == "math"
    assert analytics._infer_question_type("Solve the equation x + 5 = 10") == "math"
    assert analytics._infer_question_type("What is the integral of x^2?") == "math"
    
    # Logical questions
    assert analytics._infer_question_type("What follows in the sequence?") == "logical"
    assert analytics._infer_question_type("If A then B, therefore...") == "logical"
    assert analytics._infer_question_type("Deduce the pattern") == "logical"
    
    # Factual questions
    assert analytics._infer_question_type("What is the capital of France?") == "factual"
    assert analytics._infer_question_type("Who wrote Hamlet?") == "factual"
    
    # Unknown
    assert analytics._infer_question_type("") == "unknown"


def test_calculate_accuracy_trends():
    """Test accuracy trends calculation."""
    analytics = DashboardAnalytics()
    
    confidence_by_date = {
        "2024-01-15": [0.95, 0.85, 0.90],
        "2024-01-16": [0.88, 0.92]
    }
    
    trends = analytics._calculate_accuracy_trends(confidence_by_date)
    
    assert len(trends) == 2
    assert trends[0]["date"] == "2024-01-15"
    assert trends[0]["avg_confidence"] == 0.9
    assert trends[0]["question_count"] == 3
    assert trends[1]["date"] == "2024-01-16"
    assert trends[1]["avg_confidence"] == 0.9


def test_empty_dashboard(temp_sessions_dir):
    """Test empty dashboard when no sessions exist."""
    analytics = DashboardAnalytics(temp_sessions_dir)
    dashboard = analytics.get_dashboard_data()
    
    assert dashboard["overview"]["total_sessions"] == 0
    assert dashboard["overview"]["total_questions"] == 0
    assert dashboard["overview"]["total_solved"] == 0
    assert len(dashboard["accuracy_trends"]) == 0
    assert len(dashboard["failure_patterns"]) == 0


def test_get_dashboard_data(sample_session_data):
    """Test complete dashboard data generation."""
    analytics = DashboardAnalytics(sample_session_data)
    dashboard = analytics.get_dashboard_data()
    
    # Check overview
    assert dashboard["overview"]["total_sessions"] == 2
    assert dashboard["overview"]["total_questions"] == 15  # 10 + 5
    assert dashboard["overview"]["total_solved"] == 13  # 8 + 5
    assert dashboard["overview"]["total_unsolvable"] == 1
    assert dashboard["overview"]["total_errors"] == 1
    assert dashboard["overview"]["total_corrections"] == 1
    assert dashboard["overview"]["overall_accuracy"] > 0
    assert dashboard["overview"]["correction_rate"] > 0
    
    # Check accuracy trends
    assert len(dashboard["accuracy_trends"]) > 0
    assert "date" in dashboard["accuracy_trends"][0]
    assert "avg_confidence" in dashboard["accuracy_trends"][0]
    
    # Check failure patterns
    assert len(dashboard["failure_patterns"]) > 0
    assert dashboard["failure_patterns"][0]["pattern"] == "Timeout after 30s"
    assert dashboard["failure_patterns"][0]["count"] == 1
    
    # Check model performance by type
    assert "math" in dashboard["model_performance_by_type"]
    assert "logical" in dashboard["model_performance_by_type"]
    
    # Check generated_at timestamp
    assert "generated_at" in dashboard
    assert dashboard["generated_at"] is not None


def test_model_performance_calculation(sample_session_data):
    """Test model performance metrics calculation."""
    analytics = DashboardAnalytics(sample_session_data)
    dashboard = analytics.get_dashboard_data()
    
    model_perf = dashboard["model_performance_by_type"]
    
    # Math questions should have data
    if "math" in model_perf:
        math_stats = model_perf["math"]
        assert "total" in math_stats
        assert "solved" in math_stats
        assert "avg_confidence" in math_stats
        assert "avg_processing_time_ms" in math_stats
        assert math_stats["total"] > 0


def test_dashboard_with_missing_files(temp_sessions_dir):
    """Test dashboard handles missing log files gracefully."""
    # Create session with missing log files
    session_id = "incomplete-session"
    session_dir = os.path.join(temp_sessions_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    session_data = {
        "session_id": session_id,
        "status": "completed",
        "total_questions": 5,
        "solved_count": 5,
        "unsolvable_count": 0,
        "error_count": 0
    }
    
    with open(os.path.join(session_dir, "session.json"), 'w') as f:
        json.dump(session_data, f)
    
    # Don't create log files
    
    analytics = DashboardAnalytics(temp_sessions_dir)
    dashboard = analytics.get_dashboard_data()
    
    # Should still generate dashboard without errors
    assert dashboard["overview"]["total_sessions"] == 1
    assert dashboard["overview"]["total_questions"] == 5


def test_dashboard_requirement_14_5_comprehensive(sample_session_data):
    """
    Comprehensive test for Requirement 14.5: Dashboard showing solver statistics.
    
    Validates that dashboard includes:
    - Total questions across all sessions
    - Accuracy trends over time
    - Common failure patterns
    - Model performance by question type
    """
    analytics = DashboardAnalytics(sample_session_data)
    dashboard = analytics.get_dashboard_data()
    
    # Requirement 14.5: Total questions
    assert "overview" in dashboard
    assert "total_questions" in dashboard["overview"]
    assert dashboard["overview"]["total_questions"] > 0
    
    # Requirement 14.5: Accuracy trends
    assert "accuracy_trends" in dashboard
    assert isinstance(dashboard["accuracy_trends"], list)
    if len(dashboard["accuracy_trends"]) > 0:
        trend = dashboard["accuracy_trends"][0]
        assert "date" in trend
        assert "avg_confidence" in trend
        assert "question_count" in trend
    
    # Requirement 14.5: Common failure patterns
    assert "failure_patterns" in dashboard
    assert isinstance(dashboard["failure_patterns"], list)
    if len(dashboard["failure_patterns"]) > 0:
        pattern = dashboard["failure_patterns"][0]
        assert "pattern" in pattern
        assert "count" in pattern
    
    # Requirement 14.5: Model performance by question type
    assert "model_performance_by_type" in dashboard
    assert isinstance(dashboard["model_performance_by_type"], dict)
    
    # Verify dashboard has timestamp
    assert "generated_at" in dashboard
    assert dashboard["generated_at"] is not None


def test_dashboard_accuracy_trends_calculation(sample_session_data):
    """Test that accuracy trends are calculated correctly over time."""
    analytics = DashboardAnalytics(sample_session_data)
    dashboard = analytics.get_dashboard_data()
    
    trends = dashboard["accuracy_trends"]
    
    # Should have trends for different dates
    assert len(trends) > 0
    
    # Each trend should have required fields
    for trend in trends:
        assert "date" in trend
        assert "avg_confidence" in trend
        assert "question_count" in trend
        
        # Confidence should be between 0 and 1
        assert 0.0 <= trend["avg_confidence"] <= 1.0
        
        # Question count should be positive
        assert trend["question_count"] > 0


def test_dashboard_failure_patterns_aggregation(sample_session_data):
    """Test that failure patterns are aggregated correctly."""
    analytics = DashboardAnalytics(sample_session_data)
    dashboard = analytics.get_dashboard_data()
    
    failure_patterns = dashboard["failure_patterns"]
    
    # Should have at least one failure pattern from sample data
    assert len(failure_patterns) > 0
    
    # Verify pattern structure
    for pattern in failure_patterns:
        assert "pattern" in pattern
        assert "count" in pattern
        assert isinstance(pattern["count"], int)
        assert pattern["count"] > 0


def test_dashboard_model_performance_by_type(sample_session_data):
    """Test that model performance is calculated per question type."""
    analytics = DashboardAnalytics(sample_session_data)
    dashboard = analytics.get_dashboard_data()
    
    model_perf = dashboard["model_performance_by_type"]
    
    # Should have performance data for different question types
    assert len(model_perf) > 0
    
    # Verify structure for each question type
    for qtype, stats in model_perf.items():
        assert "total" in stats
        assert "solved" in stats
        assert "avg_confidence" in stats
        assert "avg_processing_time_ms" in stats
        
        # Verify data types and ranges
        assert isinstance(stats["total"], int)
        assert isinstance(stats["solved"], int)
        assert stats["solved"] <= stats["total"]
        
        if stats["solved"] > 0:
            assert 0.0 <= stats["avg_confidence"] <= 1.0
        
        assert stats["avg_processing_time_ms"] >= 0.0


def test_dashboard_overall_accuracy_calculation(sample_session_data):
    """Test that overall accuracy is calculated correctly."""
    analytics = DashboardAnalytics(sample_session_data)
    dashboard = analytics.get_dashboard_data()
    
    overview = dashboard["overview"]
    
    # Calculate expected accuracy
    total_questions = overview["total_questions"]
    total_solved = overview["total_solved"]
    
    if total_questions > 0:
        expected_accuracy = (total_solved / total_questions) * 100
        assert overview["overall_accuracy"] == pytest.approx(expected_accuracy, abs=0.01)
    else:
        assert overview["overall_accuracy"] == 0.0


def test_dashboard_correction_rate_calculation(sample_session_data):
    """Test that correction rate is calculated correctly."""
    analytics = DashboardAnalytics(sample_session_data)
    dashboard = analytics.get_dashboard_data()
    
    overview = dashboard["overview"]
    
    # Calculate expected correction rate
    total_questions = overview["total_questions"]
    total_corrections = overview["total_corrections"]
    
    if total_questions > 0:
        expected_rate = (total_corrections / total_questions) * 100
        assert overview["correction_rate"] == pytest.approx(expected_rate, abs=0.01)
    else:
        assert overview["correction_rate"] == 0.0


def test_dashboard_with_multiple_sessions(temp_sessions_dir):
    """Test dashboard aggregates data from multiple sessions correctly."""
    # Create 3 sessions with different characteristics
    for i in range(1, 4):
        session_id = f"multi-session-{i}"
        session_dir = os.path.join(temp_sessions_dir, session_id)
        os.makedirs(os.path.join(session_dir, "logs"), exist_ok=True)
        
        session_data = {
            "session_id": session_id,
            "status": "completed",
            "total_questions": 10 * i,
            "solved_count": 8 * i,
            "unsolvable_count": i,
            "error_count": i
        }
        
        with open(os.path.join(session_dir, "session.json"), 'w') as f:
            json.dump(session_data, f)
        
        # Create solver responses
        solver_responses = [
            {
                "timestamp": f"2024-01-{15+i}T10:00:00",
                "data": {
                    "question_number": j,
                    "question_text": f"Question {j}",
                    "selected_answer": "A",
                    "confidence": 0.8 + (j * 0.01),
                    "processing_time_ms": 1000.0,
                    "status": "solved"
                }
            }
            for j in range(1, 4)
        ]
        
        with open(os.path.join(session_dir, "logs", "solver_responses.jsonl"), 'w') as f:
            for response in solver_responses:
                f.write(json.dumps(response) + '\n')
    
    analytics = DashboardAnalytics(temp_sessions_dir)
    dashboard = analytics.get_dashboard_data()
    
    # Verify aggregation
    assert dashboard["overview"]["total_sessions"] == 3
    assert dashboard["overview"]["total_questions"] == 10 + 20 + 30  # 60
    assert dashboard["overview"]["total_solved"] == 8 + 16 + 24  # 48
    assert dashboard["overview"]["total_unsolvable"] == 1 + 2 + 3  # 6
    assert dashboard["overview"]["total_errors"] == 1 + 2 + 3  # 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
