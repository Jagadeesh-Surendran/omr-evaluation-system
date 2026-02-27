"""
Unit tests for /api/extract_key endpoint error handling.

Tests the enhanced error handling in the /api/extract_key endpoint
with proper HTTP status codes and structured error responses.
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
from io import BytesIO

import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock the FullOMREvaluator before importing app
with patch('full_evaluator.FullOMREvaluator'):
    from app import app, ERROR_MESSAGES


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestExtractKeyEndpoint:
    """Test /api/extract_key endpoint error handling."""

    def test_no_file_returns_400(self, client):
        """Test that missing file returns 400 with structured error."""
        response = client.post('/api/extract_key')
        assert response.status_code == 400
        data = response.get_json()
        assert data == ERROR_MESSAGES["no_file"]

    def test_empty_filename_returns_400(self, client):
        """Test that empty filename returns 400."""
        response = client.post('/api/extract_key', data={'qp_file': (BytesIO(b''), '')})
        assert response.status_code == 400

    def test_extraction_failure_returns_422(self, client):
        """Test that extraction failure (no answers) returns 422."""
        # Mock extract_answer_key_from_image to return empty dict
        with patch('app.extract_answer_key_from_image') as mock_extract:
            mock_extract.return_value = ({}, [], 100.0)
            
            response = client.post('/api/extract_key', data={
                'qp_file': (BytesIO(b'fake image data'), 'test.jpg')
            })
            
            assert response.status_code == 422
            data = response.get_json()
            assert data == ERROR_MESSAGES["extraction_failed"]

    def test_file_not_found_returns_404(self, client):
        """Test that FileNotFoundError returns 404."""
        with patch('app.extract_answer_key_from_image') as mock_extract:
            mock_extract.side_effect = FileNotFoundError("File not found")
            
            response = client.post('/api/extract_key', data={
                'qp_file': (BytesIO(b'fake image data'), 'test.jpg')
            })
            
            assert response.status_code == 404
            data = response.get_json()
            assert data == ERROR_MESSAGES["file_not_found"]

    def test_ollama_connection_error_returns_500(self, client):
        """Test that Ollama connection error returns 500."""
        with patch('app.extract_answer_key_from_image') as mock_extract:
            mock_extract.side_effect = Exception("ollama connection refused")
            
            response = client.post('/api/extract_key', data={
                'qp_file': (BytesIO(b'fake image data'), 'test.jpg')
            })
            
            assert response.status_code == 500
            data = response.get_json()
            assert data["error_type"] == "service_unavailable"
            assert "ollama" in data["error"].lower()

    def test_generic_processing_error_returns_500(self, client):
        """Test that generic processing error returns 500."""
        with patch('app.extract_answer_key_from_image') as mock_extract:
            mock_extract.side_effect = Exception("Some random error")
            
            response = client.post('/api/extract_key', data={
                'qp_file': (BytesIO(b'fake image data'), 'test.jpg')
            })
            
            assert response.status_code == 500
            data = response.get_json()
            assert data == ERROR_MESSAGES["processing_error"]

    def test_successful_extraction_returns_200_with_metadata(self, client):
        """Test that successful extraction returns 200 with metadata."""
        with patch('app.extract_answer_key_from_image') as mock_extract:
            mock_extract.return_value = (
                {1: "A", 2: "B", 3: "C"},
                ["Only 3 answers extracted (< 5)"],
                1234.56
            )
            
            response = client.post('/api/extract_key', data={
                'qp_file': (BytesIO(b'fake image data'), 'test.jpg')
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            # JSON converts integer keys to strings
            assert data["answer_key"] == {"1": "A", "2": "B", "3": "C"}
            assert data["count"] == 3
            assert data["warnings"] == ["Only 3 answers extracted (< 5)"]
            assert data["processing_time_ms"] == 1234.56

    def test_successful_extraction_without_warnings(self, client):
        """Test successful extraction with no warnings."""
        with patch('app.extract_answer_key_from_image') as mock_extract:
            mock_extract.return_value = (
                {i: "A" for i in range(1, 11)},  # 10 answers
                [],  # No warnings
                500.0
            )
            
            response = client.post('/api/extract_key', data={
                'qp_file': (BytesIO(b'fake image data'), 'test.jpg')
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert data["count"] == 10
            assert data["warnings"] == []
            assert data["processing_time_ms"] == 500.0

    def test_unexpected_error_returns_500(self, client):
        """Test that unexpected errors return 500 with generic message."""
        with patch('app.extract_answer_key_from_image') as mock_extract:
            mock_extract.side_effect = RuntimeError("Unexpected error")
            
            response = client.post('/api/extract_key', data={
                'qp_file': (BytesIO(b'fake image data'), 'test.jpg')
            })
            
            assert response.status_code == 500
            data = response.get_json()
            assert data["error_type"] == "processing_error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
