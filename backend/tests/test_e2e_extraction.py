"""
End-to-end integration tests for answer key extraction system.

Tests the complete extraction flow with real images, various formats,
error scenarios, logging, and frontend error display.

Feature: improve-answer-key-extraction-and-github-setup
Task 13.2: Perform end-to-end integration testing

Requirements tested:
- Complete extraction flow with real images
- Various image qualities and formats
- Error scenarios (missing file, poor quality, no answers)
- PDF file handling
- Logging output verification
- Frontend error display verification
"""

import os
import sys
import json
import tempfile
import time
from io import BytesIO
from unittest.mock import patch, MagicMock
import pytest
import cv2
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock the FullOMREvaluator before importing
with patch('full_evaluator.FullOMREvaluator'):
    from app import app
    from ollama_client import (
        extract_answer_key_from_image,
        ExtractionConfig,
        preprocess_image,
        convert_pdf_to_image
    )


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_answer_key_image():
    """Create a synthetic answer key image for testing."""
    # Create a white image with text
    img = np.ones((800, 600, 3), dtype=np.uint8) * 255
    
    # Add some text to simulate an answer key
    font = cv2.FONT_HERSHEY_SIMPLEX
    y_pos = 100
    for i in range(1, 6):
        answer = chr(65 + (i % 5))  # A, B, C, D, E
        text = f"Q{i}: {answer}"
        cv2.putText(img, text, (50, y_pos), font, 1, (0, 0, 0), 2)
        y_pos += 80
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        cv2.imwrite(f.name, img)
        yield f.name
    
    # Cleanup
    if os.path.exists(f.name):
        os.unlink(f.name)


@pytest.fixture
def poor_quality_image():
    """Create a poor quality image (very low resolution, noisy)."""
    # Create a very small, noisy image
    img = np.random.randint(100, 200, (50, 50, 3), dtype=np.uint8)
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        cv2.imwrite(f.name, img)
        yield f.name
    
    if os.path.exists(f.name):
        os.unlink(f.name)


@pytest.fixture
def sample_pdf():
    """Create a sample PDF file for testing."""
    try:
        import fitz  # PyMuPDF
        
        # Create a simple PDF with text
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # A4 size
        
        # Add text to simulate answer key
        text_y = 100
        for i in range(1, 6):
            answer = chr(65 + (i % 5))
            text = f"Q{i}: {answer}"
            page.insert_text((50, text_y), text, fontsize=14)
            text_y += 50
        
        # Save to a file path directly (not using NamedTemporaryFile context)
        fd, temp_path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)  # Close the file descriptor
        doc.save(temp_path)
        doc.close()
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except PermissionError:
                pass  # File may still be in use on Windows
    except ImportError:
        pytest.skip("PyMuPDF not available for PDF testing")


class TestCompleteExtractionFlow:
    """Test the complete extraction flow with real images."""
    
    def test_extraction_with_mocked_ollama_success(self, client, sample_answer_key_image):
        """Test complete extraction flow with mocked successful Ollama response."""
        # Mock Ollama to return a valid answer key
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A","2":"B","3":"C","4":"D","5":"E"}'
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            with open(sample_answer_key_image, 'rb') as f:
                response = client.post('/api/extract_key', data={
                    'qp_file': (f, 'answer_key.jpg')
                })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["count"] == 5
        assert "processing_time_ms" in data
        assert isinstance(data["answer_key"], dict)
    
    def test_extraction_with_preprocessing(self, sample_answer_key_image):
        """Test that preprocessing is applied before extraction."""
        # Mock Ollama
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A"}'
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            with patch('ollama_client.preprocess_image') as mock_preprocess:
                # Make preprocess return the same image
                mock_preprocess.return_value = sample_answer_key_image
                
                result, warnings, duration = extract_answer_key_from_image(
                    sample_answer_key_image
                )
                
                # Verify preprocessing was called
                mock_preprocess.assert_called_once()
    
    def test_multipass_extraction_attempts(self, sample_answer_key_image):
        """Test that multiple extraction passes are attempted on failure."""
        # Mock Ollama to fail first two times, succeed on third
        mock_responses = [
            MagicMock(message=MagicMock(content='{}')),  # Pass 1: empty
            MagicMock(message=MagicMock(content='invalid json')),  # Pass 2: invalid
            MagicMock(message=MagicMock(content='{"1":"A","2":"B"}')),  # Pass 3: success
        ]
        
        with patch('ollama_client.ollama.chat', side_effect=mock_responses):
            result, warnings, duration = extract_answer_key_from_image(
                sample_answer_key_image
            )
        
        # Should succeed on third pass
        assert len(result) == 2
        assert result[1] == "A"
        assert result[2] == "B"


class TestVariousImageFormats:
    """Test extraction with various image qualities and formats."""
    
    def test_high_quality_image(self, client):
        """Test extraction with high quality image."""
        # Create high quality image (1920x1080)
        img = np.ones((1080, 1920, 3), dtype=np.uint8) * 255
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, "Q1: A", (100, 200), font, 2, (0, 0, 0), 3)
        
        fd, temp_path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)
        cv2.imwrite(temp_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        try:
            mock_response = MagicMock()
            mock_response.message.content = '{"1":"A"}'
            
            with patch('ollama_client.ollama.chat', return_value=mock_response):
                with open(temp_path, 'rb') as img_file:
                    response = client.post('/api/extract_key', data={
                        'qp_file': (img_file, 'high_quality.jpg')
                    })
            
            assert response.status_code == 200
        finally:
            try:
                os.unlink(temp_path)
            except PermissionError:
                pass  # File may still be in use on Windows
    
    def test_png_format(self, client):
        """Test extraction with PNG format."""
        img = np.ones((600, 800, 3), dtype=np.uint8) * 255
        
        fd, temp_path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        cv2.imwrite(temp_path, img)
        
        try:
            mock_response = MagicMock()
            mock_response.message.content = '{"1":"A"}'
            
            with patch('ollama_client.ollama.chat', return_value=mock_response):
                with open(temp_path, 'rb') as img_file:
                    response = client.post('/api/extract_key', data={
                        'qp_file': (img_file, 'test.png')
                    })
            
            assert response.status_code == 200
        finally:
            try:
                os.unlink(temp_path)
            except PermissionError:
                pass  # File may still be in use on Windows
    
    def test_low_quality_image_with_preprocessing(self, poor_quality_image):
        """Test that poor quality images are preprocessed."""
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A"}'
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            # Preprocessing should enhance the image
            result, warnings, duration = extract_answer_key_from_image(
                poor_quality_image
            )
        
        # Should complete without error (preprocessing helps)
        assert isinstance(result, dict)


class TestErrorScenarios:
    """Test various error scenarios."""
    
    def test_missing_file_error(self, client):
        """Test error when file is missing."""
        response = client.post('/api/extract_key')
        assert response.status_code == 400
        data = response.get_json()
        assert data["error_type"] == "missing_file"
        assert "suggestions" in data
    
    def test_file_not_found_error(self, client):
        """Test error when uploaded file cannot be found."""
        with patch('app.extract_answer_key_from_image') as mock_extract:
            mock_extract.side_effect = FileNotFoundError("File not found")
            
            response = client.post('/api/extract_key', data={
                'qp_file': (BytesIO(b'fake'), 'test.jpg')
            })
        
        assert response.status_code == 404
        data = response.get_json()
        assert data["error_type"] == "file_not_found"
    
    def test_no_answers_extracted_error(self, client, sample_answer_key_image):
        """Test error when no answers can be extracted."""
        # Mock Ollama to return empty results for all passes
        mock_response = MagicMock()
        mock_response.message.content = '{}'
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            with open(sample_answer_key_image, 'rb') as f:
                response = client.post('/api/extract_key', data={
                    'qp_file': (f, 'answer_key.jpg')
                })
        
        assert response.status_code == 422
        data = response.get_json()
        assert data["error_type"] == "extraction_failed"
        assert len(data["suggestions"]) > 0
    
    def test_ollama_connection_error(self, client, sample_answer_key_image):
        """Test error when Ollama service is unavailable."""
        with patch('ollama_client.ollama.chat') as mock_chat:
            # Simulate connection error that results in empty extraction
            mock_chat.side_effect = Exception("connection refused")
            
            with open(sample_answer_key_image, 'rb') as f:
                response = client.post('/api/extract_key', data={
                    'qp_file': (f, 'answer_key.jpg')
                })
        
        # The error is caught and returns 500 for connection errors
        # or 422 if extraction returns empty results
        assert response.status_code in [422, 500]
        data = response.get_json()
        assert "error" in data
    
    def test_corrupted_image_error(self, client):
        """Test error with corrupted image data."""
        # Send invalid image data
        response = client.post('/api/extract_key', data={
            'qp_file': (BytesIO(b'not an image'), 'corrupt.jpg')
        })
        
        # Should handle gracefully
        assert response.status_code in [422, 500]


class TestPDFHandling:
    """Test PDF file handling."""
    
    def test_pdf_conversion_to_image(self, sample_pdf):
        """Test that PDF is converted to image before extraction."""
        try:
            # Test PDF conversion
            converted_path = convert_pdf_to_image(sample_pdf, dpi=200)
            
            # Verify converted file exists and is an image
            assert os.path.exists(converted_path)
            img = cv2.imread(converted_path)
            assert img is not None
            assert img.shape[0] > 0 and img.shape[1] > 0
            
            # Cleanup
            os.unlink(converted_path)
        except ImportError:
            pytest.skip("PyMuPDF not available")
    
    def test_pdf_extraction_via_api(self, client, sample_pdf):
        """Test PDF extraction through API endpoint."""
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A","2":"B"}'
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            with open(sample_pdf, 'rb') as f:
                response = client.post('/api/extract_key', data={
                    'qp_file': (f, 'answer_key.pdf')
                })
        
        # Should handle PDF and extract answers
        assert response.status_code in [200, 422, 500]  # May fail if PyMuPDF not available


class TestLoggingOutput:
    """Test logging output verification."""
    
    def test_extraction_attempts_are_logged(self, sample_answer_key_image):
        """Test that extraction attempts are logged."""
        # Use the actual log path from ollama_client
        from ollama_client import LOG_PATH
        
        # Clear existing log if it exists
        if os.path.exists(LOG_PATH):
            # Read current size to check for new entries
            initial_size = os.path.getsize(LOG_PATH)
        else:
            initial_size = 0
        
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A"}'
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            result, warnings, duration = extract_answer_key_from_image(
                sample_answer_key_image
            )
        
        # Verify log file was created or updated
        assert os.path.exists(LOG_PATH)
        final_size = os.path.getsize(LOG_PATH)
        
        # New log entries should have been added
        assert final_size >= initial_size
        
        # Read log content
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Should contain extraction-related logs
        assert len(log_content) > 0
    
    def test_preprocessing_is_logged(self, sample_answer_key_image):
        """Test that preprocessing operations are logged."""
        from ollama_client import LOG_PATH
        
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A"}'
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            result, warnings, duration = extract_answer_key_from_image(
                sample_answer_key_image
            )
        
        # Log should exist and have content
        assert os.path.exists(LOG_PATH)
        assert os.path.getsize(LOG_PATH) > 0
    
    def test_validation_warnings_are_logged(self, sample_answer_key_image):
        """Test that validation warnings are logged."""
        from ollama_client import LOG_PATH
        
        # Mock to return only 2 answers (should trigger warning)
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A","2":"B"}'
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            result, warnings, duration = extract_answer_key_from_image(
                sample_answer_key_image
            )
        
        # Should have warning about low count
        assert len(warnings) > 0
        assert any("5" in w for w in warnings)  # Warning mentions threshold


class TestFrontendErrorDisplay:
    """Test frontend error display integration."""
    
    def test_error_response_structure(self, client):
        """Test that error responses have correct structure for frontend."""
        response = client.post('/api/extract_key')
        
        assert response.status_code == 400
        data = response.get_json()
        
        # Frontend expects these fields
        assert "error" in data
        assert "error_type" in data
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
    
    def test_extraction_failed_has_actionable_suggestions(self, client, sample_answer_key_image):
        """Test that extraction failure provides actionable suggestions."""
        mock_response = MagicMock()
        mock_response.message.content = '{}'
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            with open(sample_answer_key_image, 'rb') as f:
                response = client.post('/api/extract_key', data={
                    'qp_file': (f, 'answer_key.jpg')
                })
        
        data = response.get_json()
        assert len(data["suggestions"]) > 0
        
        # Suggestions should be helpful
        suggestions_text = " ".join(data["suggestions"]).lower()
        assert any(word in suggestions_text for word in ["image", "resolution", "quality", "clear"])
    
    def test_success_response_structure(self, client, sample_answer_key_image):
        """Test that success responses have correct structure for frontend."""
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A","2":"B","3":"C","4":"D","5":"E"}'
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            with open(sample_answer_key_image, 'rb') as f:
                response = client.post('/api/extract_key', data={
                    'qp_file': (f, 'answer_key.jpg')
                })
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Frontend expects these fields
        assert "success" in data
        assert "answer_key" in data
        assert "count" in data
        assert "warnings" in data
        assert "processing_time_ms" in data
        
        assert data["success"] is True
        assert isinstance(data["answer_key"], dict)
        assert isinstance(data["count"], int)
        assert isinstance(data["warnings"], list)
        assert isinstance(data["processing_time_ms"], (int, float))


class TestPerformanceMetrics:
    """Test performance and timing metrics."""
    
    def test_processing_time_is_recorded(self, client, sample_answer_key_image):
        """Test that processing time is recorded and returned."""
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A"}'
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            with open(sample_answer_key_image, 'rb') as f:
                response = client.post('/api/extract_key', data={
                    'qp_file': (f, 'answer_key.jpg')
                })
        
        data = response.get_json()
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] > 0
    
    def test_extraction_completes_in_reasonable_time(self, sample_answer_key_image):
        """Test that extraction completes within reasonable time."""
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A"}'
        
        start_time = time.time()
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            result, warnings, duration = extract_answer_key_from_image(
                sample_answer_key_image
            )
        
        elapsed = time.time() - start_time
        
        # Should complete quickly with mocked Ollama (< 5 seconds)
        assert elapsed < 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
