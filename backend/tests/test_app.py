import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import io
import json
from app import app as flask_app, parse_answer_key_csv, generate_insights


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client


# ── /api/evaluate ─────────────────────────────────────────────────────────────

def test_evaluate_missing_omr_files(client):
    """Submitting without OMR files should return 400."""
    response = client.post('/api/evaluate')
    assert response.status_code == 400
    assert b"No OMR files uploaded" in response.data


def test_evaluate_missing_csv(client):
    """Submitting without answer key CSV should return 400."""
    data = {
        'omr_files': (io.BytesIO(b"fake_jpeg_data"), 'mock_omr.jpg'),
    }
    response = client.post('/api/evaluate', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert b"Answer Key CSV" in response.data


def test_evaluate_invalid_csv(client):
    """Submitting a CSV with no parseable Q→answer rows should return 400."""
    data = {
        'omr_files': (io.BytesIO(b"fake_jpeg_data"), 'mock_omr.jpg'),
        'answer_key_csv': (io.BytesIO(b"header_only_row_here"), 'key.csv'),
    }
    response = client.post('/api/evaluate', data=data, content_type='multipart/form-data')
    assert response.status_code == 400


def test_evaluate_with_mock_files(client):
    """
    The evaluation endpoint should gracefully handle a bad/undecodable image
    by assigning a 0 score and returning 200 with the correct structure.
    """
    data = {
        'omr_files': (io.BytesIO(b"not_a_real_image"), 'mock_omr.jpg'),
        'answer_key_csv': (io.BytesIO(b"1,A\n2,B\n3,C\n"), 'key.csv'),
    }
    response = client.post('/api/evaluate', data=data, content_type='multipart/form-data')
    assert response.status_code == 200

    json_data = json.loads(response.data)
    assert 'students' in json_data
    assert 'insights' in json_data
    assert 'average_score' in json_data
    assert len(json_data['students']) == 1
    assert json_data['students'][0]['score'] == 0  # Graceful fallback


# ── /api/link_db ──────────────────────────────────────────────────────────────

def test_link_db_no_file(client):
    """Calling link_db without a DB file should return 400."""
    response = client.post('/api/link_db')
    assert response.status_code == 400


def test_link_db_no_results(client):
    """Calling link_db with an empty results list should return 400."""
    data = {
        'db_file': (io.BytesIO(b"1,Alice\n2,Bob\n"), 'students.csv'),
        'current_results': '[]',
    }
    response = client.post('/api/link_db', data=data, content_type='multipart/form-data')
    assert response.status_code == 400


def test_link_db_success(client):
    """link_db should correctly map student names by row position."""
    current = json.dumps([
        {"id": "CAND-1000", "name": "Unknown", "score": 80, "question_details": []},
        {"id": "CAND-1001", "name": "Unknown", "score": 60, "question_details": []},
    ])
    data = {
        'db_file': (io.BytesIO(b"1,Alice Sharma\n2,Bob Patel\n"), 'students.csv'),
        'current_results': current,
    }
    response = client.post('/api/link_db', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert json_data['students'][0]['name'] == 'Alice Sharma'
    assert json_data['students'][1]['name'] == 'Bob Patel'


def test_link_db_partial_mapping(client):
    """If DB has fewer names than results, remaining students keep old name."""
    current = json.dumps([
        {"id": "CAND-1000", "name": "Unknown", "score": 80, "question_details": []},
        {"id": "CAND-1001", "name": "Unknown", "score": 60, "question_details": []},
        {"id": "CAND-1002", "name": "Unknown", "score": 40, "question_details": []},
    ])
    data = {
        'db_file': (io.BytesIO(b"1,Alice Sharma\n"), 'students.csv'),
        'current_results': current,
    }
    response = client.post('/api/link_db', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert json_data['students'][0]['name'] == 'Alice Sharma'
    assert json_data['students'][1]['name'] == 'Unknown'  # Unchanged


# ── /api/export ───────────────────────────────────────────────────────────────

def test_export_results_csv(client):
    """Export endpoint should return a valid CSV file."""
    payload = {
        "results": [
            {"id": "CAND-1000", "name": "Alice", "score": 90, "filename": "a.jpg",
             "student_id": "1000", "question_details": []},
            {"id": "CAND-1001", "name": "Bob",   "score": 70, "filename": "b.jpg",
             "student_id": "1001", "question_details": []},
        ]
    }
    response = client.post('/api/export',
                           data=json.dumps(payload),
                           content_type='application/json')
    assert response.status_code == 200
    assert b"Candidate ID" in response.data
    assert b"Alice" in response.data
    assert b"Bob" in response.data


def test_export_results_empty(client):
    """Export with empty results still returns 200 with just the header row."""
    payload = {"results": []}
    response = client.post('/api/export',
                           data=json.dumps(payload),
                           content_type='application/json')
    assert response.status_code == 200
    assert b"Candidate ID" in response.data


def test_export_no_data(client):
    """Export with no payload should return 400."""
    response = client.post('/api/export',
                           data=json.dumps({}),
                           content_type='application/json')
    assert response.status_code == 400


# ── parse_answer_key_csv unit tests ──────────────────────────────────────────

def test_parse_answer_key_csv_basic():
    """Standard format '1,A\\n2,B' is parsed correctly."""
    csv = io.BytesIO(b"1,A\n2,B\n3,C\n4,D\n5,A\n")
    key = parse_answer_key_csv(csv)
    assert key == {0: 0, 1: 1, 2: 2, 3: 3, 4: 0}


def test_parse_answer_key_csv_with_header():
    """A header row containing 'Q'/'ANSWER' tokens is silently skipped."""
    csv = io.BytesIO(b"Q,ANSWER\n1,A\n2,B\n")
    key = parse_answer_key_csv(csv)
    assert key == {0: 0, 1: 1}


def test_parse_answer_key_csv_lowercase_option():
    """Lowercase answer letters ('a','b') should be handled (uppercased)."""
    csv = io.BytesIO(b"1,a\n2,b\n")
    key = parse_answer_key_csv(csv)
    assert key == {0: 0, 1: 1}


def test_parse_answer_key_csv_duplicate_raises():
    """Duplicate question number must raise ValueError."""
    csv = io.BytesIO(b"1,A\n1,B\n2,C\n")
    with pytest.raises(ValueError, match="Duplicate"):
        parse_answer_key_csv(csv)


def test_parse_answer_key_csv_empty_raises():
    """Completely empty or header-only CSV must raise ValueError."""
    csv = io.BytesIO(b"no_data_here\n")
    with pytest.raises(ValueError):
        parse_answer_key_csv(csv)


# ── generate_insights unit tests ─────────────────────────────────────────────

def _make_students(scores, correct_map=None):
    """Helper: build a minimal students list for generate_insights."""
    students = []
    for i, s in enumerate(scores):
        qd = []
        if correct_map:
            for q, is_c in correct_map.get(i, {}).items():
                qd.append({
                    "question_number": q,
                    "is_correct": is_c,
                    "marked_answer": "A" if is_c else "B",
                })
        students.append({"id": f"S{i}", "name": f"Student{i}", "score": s,
                         "question_details": qd})
    return students


def test_generate_insights_low_average():
    """Average < 40% should warn about low performance."""
    students = _make_students([30, 20, 35])
    insights = generate_insights(students, avg_score=28, highest_score=35)
    assert any("low" in i.lower() or "very" in i.lower() for i in insights)


def test_generate_insights_outstanding():
    """Average ≥ 80% should praise performance."""
    students = _make_students([90, 95, 85])
    insights = generate_insights(students, avg_score=90, highest_score=95)
    assert any("outstanding" in i.lower() or "90" in i for i in insights)


def test_generate_insights_top_performer():
    """Insights must include the top performer's score."""
    students = _make_students([80, 100])
    insights = generate_insights(students, avg_score=90, highest_score=100)
    assert any("100" in i for i in insights)


def test_generate_insights_is_list():
    """generate_insights must always return a list."""
    students = _make_students([50])
    result = generate_insights(students, avg_score=50, highest_score=50)
    assert isinstance(result, list)
    assert len(result) > 0
