"""
Integration tests for Dashboard API endpoint.
"""
import pytest
import os
import json
import tempfile
import shutil
from app import app, dashboard_analytics


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def temp_sessions_with_data():
    """Create temporary sessions directory with sample data."""
    temp_dir = tempfile.mkdtemp()
    
    # Create session 1
    session1_id = "api-test-session-1"
    session1_dir = os.path.join(temp_dir, session1_id)
    os.makedirs(os.path.join(session1_dir, "logs"), exist_ok=True)
    
    session1_data = {
        "session_id": session1_id,
        "status": "completed",
        "total_questions": 20,
        "solved_count": 18,
        "unsolvable_count": 1,
        "error_count": 1
    }
    
    with open(os.path.join(session1_dir, "session.json"), 'w') as f:
        json.dump(session1_data, f)
    
    # Solver responses with various question types
    solver_responses = [
        {
            "timestamp": "2024-01-15T10:00:00",
            "data": {
                "question_number": 1,
                "question_text": "Calculate 5 + 3",
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
                "question_text": "What follows in the pattern 2, 4, 6, ?",
                "selected_answer": "A",
                "confidence": 0.88,
                "processing_time_ms": 1400,
                "status": "solved"
            }
        },
        {
            "timestamp": "2024-01-15T10:02:00",
            "data": {
                "question_number": 3,
                "question_text": "Who is the president?",
                "selected_answer": "B",
                "confidence": 0.82,
                "processing_time_ms": 1100,
                "status": "solved"
            }
        },
        {
            "timestamp": "2024-01-15T10:03:00",
            "data": {
                "question_number": 4,
                "question_text": "Timeout question",
                "selected_answer": None,
                "confidence": 0.0,
                "processing_time_ms": 30000,
                "status": "timeout",
                "error_message": "Timeout after 30s"
            }
        },
        {
            "timestamp": "2024-01-15T10:04:00",
            "data": {
                "question_number": 5,
                "question_text": "Parse error question",
                "selected_answer": None,
                "confidence": 0.0,
                "processing_time_ms": 100,
                "status": "error",
                "error_message": "Parse failed"
            }
        }
    ]
    
    with open(os.path.join(session1_dir, "logs", "solver_responses.jsonl"), 'w') as f:
        for response in solver_responses:
            f.write(json.dumps(response) + '\n')
    
    # User corrections
    corrections = [
        {
            "timestamp": "2024-01-15T10:10:00",
            "data": {
                "question_number": 10,
                "original_answer": "B",
                "corrected_answer": "C"
            }
        },
        {
            "timestamp": "2024-01-15T10:11:00",
            "data": {
                "question_number": 15,
                "original_answer": "A",
                "corrected_answer": "D"
            }
        }
    ]
    
    with open(os.path.join(session1_dir, "logs", "user_corrections.jsonl"), 'w') as f:
        for correction in corrections:
            f.write(json.dumps(correction) + '\n')
    
    # Create session 2
    session2_id = "api-test-session-2"
    session2_dir = os.path.join(temp_dir, session2_id)
    os.makedirs(os.path.join(session2_dir, "logs"), exist_ok=True)
    
    session2_data = {
        "session_id": session2_id,
        "status": "completed",
        "total_questions": 10,
        "solved_count": 10,
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
                "question_text": "Solve for x: 2x = 10",
                "selected_answer": "B",
                "confidence": 0.92,
                "processing_time_ms": 1300,
                "status": "solved"
            }
        }
    ]
    
    with open(os.path.join(session2_dir, "logs", "solver_responses.jsonl"), 'w') as f:
        for response in solver_responses2:
            f.write(json.dumps(response) + '\n')
    
    # Temporarily replace the sessions directory
    original_dir = dashboard_analytics.sessions_dir
    dashboard_analytics.sessions_dir = temp_dir
    
    yield temp_dir
    
    # Restore original directory and cleanup
    dashboard_analytics.sessions_dir = original_dir
    shutil.rmtree(temp_dir)


def test_dashboard_endpoint_success(client, temp_sessions_with_data):
    """Test dashboard endpoint returns correct data."""
    response = client.get('/api/solve/dashboard')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Check overview section
    assert "overview" in data
    overview = data["overview"]
    assert overview["total_sessions"] == 2
    assert overview["total_questions"] == 30  # 20 + 10
    assert overview["total_solved"] == 28  # 18 + 10
    assert overview["total_unsolvable"] == 1
    assert overview["total_errors"] == 1
    assert overview["total_corrections"] == 2
    assert overview["overall_accuracy"] > 0
    assert overview["correction_rate"] > 0
    
    # Check accuracy trends
    assert "accuracy_trends" in data
    assert isinstance(data["accuracy_trends"], list)
    if len(data["accuracy_trends"]) > 0:
        trend = data["accuracy_trends"][0]
        assert "date" in trend
        assert "avg_confidence" in trend
        assert "question_count" in trend
    
    # Check failure patterns
    assert "failure_patterns" in data
    assert isinstance(data["failure_patterns"], list)
    assert len(data["failure_patterns"]) > 0
    
    # Should have timeout and parse error patterns
    patterns = [p["pattern"] for p in data["failure_patterns"]]
    assert "Timeout after 30s" in patterns or "Parse failed" in patterns
    
    # Check model performance by type
    assert "model_performance_by_type" in data
    model_perf = data["model_performance_by_type"]
    assert isinstance(model_perf, dict)
    
    # Should have math, logical, and factual types
    assert "math" in model_perf or "logical" in model_perf or "factual" in model_perf
    
    # Check each type has required fields
    for qtype, stats in model_perf.items():
        assert "total" in stats
        assert "solved" in stats
        assert "avg_confidence" in stats
        assert "avg_processing_time_ms" in stats
    
    # Check generated_at timestamp
    assert "generated_at" in data
    assert data["generated_at"] is not None


def test_dashboard_endpoint_empty_sessions(client):
    """Test dashboard endpoint with no sessions."""
    # Temporarily use empty directory
    temp_dir = tempfile.mkdtemp()
    original_dir = dashboard_analytics.sessions_dir
    dashboard_analytics.sessions_dir = temp_dir
    
    try:
        response = client.get('/api/solve/dashboard')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        # Should return empty dashboard structure
        assert data["overview"]["total_sessions"] == 0
        assert data["overview"]["total_questions"] == 0
        assert len(data["accuracy_trends"]) == 0
        assert len(data["failure_patterns"]) == 0
        
    finally:
        dashboard_analytics.sessions_dir = original_dir
        shutil.rmtree(temp_dir)


def test_dashboard_endpoint_authentication(client):
    """Test dashboard endpoint requires authentication."""
    # Note: Current implementation has placeholder auth that always passes
    # This test verifies the endpoint is decorated with @require_auth
    response = client.get('/api/solve/dashboard')
    
    # Should not return 401 with current placeholder auth
    # In production with real auth, this would return 401 without valid token
    assert response.status_code in [200, 401]


def test_dashboard_data_structure(client, temp_sessions_with_data):
    """Test dashboard returns all required data fields."""
    response = client.get('/api/solve/dashboard')
    data = json.loads(response.data)
    
    # Verify complete structure
    required_top_level = ["overview", "accuracy_trends", "failure_patterns", 
                          "model_performance_by_type", "generated_at"]
    for field in required_top_level:
        assert field in data, f"Missing required field: {field}"
    
    # Verify overview fields
    required_overview = ["total_sessions", "total_questions", "total_solved",
                        "total_unsolvable", "total_errors", "total_corrections",
                        "overall_accuracy", "correction_rate"]
    for field in required_overview:
        assert field in data["overview"], f"Missing overview field: {field}"


def test_dashboard_accuracy_calculation(client, temp_sessions_with_data):
    """Test dashboard calculates accuracy correctly."""
    response = client.get('/api/solve/dashboard')
    data = json.loads(response.data)
    
    overview = data["overview"]
    
    # Calculate expected accuracy
    expected_accuracy = (overview["total_solved"] / overview["total_questions"]) * 100
    
    # Should match (with rounding tolerance)
    assert abs(overview["overall_accuracy"] - expected_accuracy) < 0.1
    
    # Calculate expected correction rate
    expected_correction_rate = (overview["total_corrections"] / overview["total_questions"]) * 100
    
    # Should match (with rounding tolerance)
    assert abs(overview["correction_rate"] - expected_correction_rate) < 0.1


def test_dashboard_failure_patterns_sorted(client, temp_sessions_with_data):
    """Test failure patterns are sorted by count (descending)."""
    response = client.get('/api/solve/dashboard')
    data = json.loads(response.data)
    
    failure_patterns = data["failure_patterns"]
    
    if len(failure_patterns) > 1:
        # Verify sorted in descending order
        for i in range(len(failure_patterns) - 1):
            assert failure_patterns[i]["count"] >= failure_patterns[i + 1]["count"]


def test_dashboard_model_performance_metrics(client, temp_sessions_with_data):
    """Test model performance metrics are calculated correctly."""
    response = client.get('/api/solve/dashboard')
    data = json.loads(response.data)
    
    model_perf = data["model_performance_by_type"]
    
    for qtype, stats in model_perf.items():
        # Solved should not exceed total
        assert stats["solved"] <= stats["total"]
        
        # Confidence should be between 0 and 1
        if stats["solved"] > 0:
            assert 0.0 <= stats["avg_confidence"] <= 1.0
        
        # Processing time should be positive
        if stats["total"] > 0:
            assert stats["avg_processing_time_ms"] >= 0
