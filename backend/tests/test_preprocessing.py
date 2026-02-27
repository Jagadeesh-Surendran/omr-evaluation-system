"""
test_preprocessing.py
---------------------
Unit tests for image preprocessing functionality in ollama_client.py.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import pytest
import numpy as np
import cv2

import ollama_client


# ── Helpers ───────────────────────────────────────────────────────────────────

def _create_test_image(width=800, height=600):
    """Create a test image with some text-like patterns."""
    img = np.ones((height, width, 3), dtype=np.uint8) * 200
    # Add some text-like patterns
    cv2.rectangle(img, (100, 100), (300, 150), (0, 0, 0), -1)
    cv2.rectangle(img, (100, 200), (300, 250), (50, 50, 50), -1)
    return img


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestPreprocessImage:

    def test_preprocess_creates_temp_file(self):
        """Preprocessing should create a temporary file."""
        # Create a temporary test image
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        img = _create_test_image()
        cv2.imwrite(tmp.name, img)
        tmp.close()
        
        try:
            # Preprocess the image
            preprocessed_path = ollama_client.preprocess_image(tmp.name)
            
            # Verify the preprocessed file exists
            assert os.path.exists(preprocessed_path)
            assert preprocessed_path != tmp.name
            assert "_preprocessed" in preprocessed_path
            
            # Cleanup
            os.unlink(preprocessed_path)
        finally:
            os.unlink(tmp.name)

    def test_preprocess_resizes_large_image(self):
        """Images wider than target_width should be resized."""
        # Create a large test image
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        img = _create_test_image(width=2000, height=1500)
        cv2.imwrite(tmp.name, img)
        tmp.close()
        
        try:
            # Preprocess with target width of 1024
            preprocessed_path = ollama_client.preprocess_image(tmp.name, target_width=1024)
            
            # Load the preprocessed image and check dimensions
            processed_img = cv2.imread(preprocessed_path)
            height, width = processed_img.shape[:2]
            
            assert width == 1024, f"Expected width 1024, got {width}"
            # Check aspect ratio is maintained (approximately)
            expected_height = int(1024 * (1500 / 2000))
            assert abs(height - expected_height) <= 1, f"Aspect ratio not maintained: {height} vs {expected_height}"
            
            # Cleanup
            os.unlink(preprocessed_path)
        finally:
            os.unlink(tmp.name)

    def test_preprocess_keeps_small_image_size(self):
        """Images smaller than target_width should not be upscaled."""
        # Create a small test image
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        img = _create_test_image(width=800, height=600)
        cv2.imwrite(tmp.name, img)
        tmp.close()
        
        try:
            # Preprocess with target width of 1024
            preprocessed_path = ollama_client.preprocess_image(tmp.name, target_width=1024)
            
            # Load the preprocessed image and check dimensions
            processed_img = cv2.imread(preprocessed_path)
            height, width = processed_img.shape[:2]
            
            # Should keep original dimensions (or close to it)
            assert width <= 800, f"Small image should not be upscaled: {width}"
            
            # Cleanup
            os.unlink(preprocessed_path)
        finally:
            os.unlink(tmp.name)

    def test_preprocess_converts_to_grayscale(self):
        """Preprocessed image should be grayscale."""
        # Create a color test image
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        img = _create_test_image()
        cv2.imwrite(tmp.name, img)
        tmp.close()
        
        try:
            # Preprocess the image
            preprocessed_path = ollama_client.preprocess_image(tmp.name)
            
            # Load the preprocessed image
            processed_img = cv2.imread(preprocessed_path)
            
            # Check if it's grayscale (all channels should be equal)
            if len(processed_img.shape) == 3:
                # If it has 3 channels, they should all be equal (grayscale saved as BGR)
                assert np.allclose(processed_img[:,:,0], processed_img[:,:,1])
                assert np.allclose(processed_img[:,:,1], processed_img[:,:,2])
            else:
                # Or it should be a 2D array
                assert len(processed_img.shape) == 2
            
            # Cleanup
            os.unlink(preprocessed_path)
        finally:
            os.unlink(tmp.name)

    def test_preprocess_invalid_image_raises_error(self):
        """Preprocessing an invalid image should raise an error."""
        # Create a temporary file with invalid image data
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.write(b"not an image")
        tmp.close()
        
        try:
            with pytest.raises(ValueError, match="Could not load image"):
                ollama_client.preprocess_image(tmp.name)
        finally:
            os.unlink(tmp.name)

    def test_preprocess_logs_timing(self):
        """Preprocessing should log timing information."""
        # Create a test image
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        img = _create_test_image()
        cv2.imwrite(tmp.name, img)
        tmp.close()
        
        try:
            # Clear the log file
            if os.path.exists(ollama_client.LOG_PATH):
                with open(ollama_client.LOG_PATH, 'w') as f:
                    f.write("")
            
            # Preprocess the image
            preprocessed_path = ollama_client.preprocess_image(tmp.name)
            
            # Check that log contains preprocessing entries
            with open(ollama_client.LOG_PATH, 'r') as f:
                log_content = f.read()
            
            assert "[PREPROCESSING]" in log_content
            assert "Starting preprocessing" in log_content
            assert "Image enhancement completed" in log_content
            assert "ms" in log_content  # Should log timing in milliseconds
            
            # Cleanup
            os.unlink(preprocessed_path)
        finally:
            os.unlink(tmp.name)

    def test_preprocess_enhances_contrast(self):
        """Preprocessing should enhance image contrast."""
        # Create a low-contrast test image
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        img = np.ones((600, 800, 3), dtype=np.uint8) * 128  # Mid-gray
        cv2.imwrite(tmp.name, img)
        tmp.close()
        
        try:
            # Preprocess the image
            preprocessed_path = ollama_client.preprocess_image(tmp.name)
            
            # Load both images
            original = cv2.imread(tmp.name, cv2.IMREAD_GRAYSCALE)
            processed = cv2.imread(preprocessed_path, cv2.IMREAD_GRAYSCALE)
            
            # The processed image should be different from the original
            assert not np.array_equal(original, processed), "Preprocessing should modify the image"
            
            # Cleanup
            os.unlink(preprocessed_path)
        finally:
            os.unlink(tmp.name)
