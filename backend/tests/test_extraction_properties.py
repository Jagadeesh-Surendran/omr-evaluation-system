"""
test_extraction_properties.py
------------------------------
Property-based tests for answer key extraction system using Hypothesis.

These tests verify universal properties that should hold across all valid inputs.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import pytest
import numpy as np
import cv2
from hypothesis import given, settings, strategies as st

import ollama_client


# ── Test Image Generation Strategies ─────────────────────────────────────────

def create_test_image(width: int, height: int) -> np.ndarray:
    """
    Create a test image with specified dimensions.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        
    Returns:
        BGR image as numpy array
    """
    # Create a simple test image with some patterns
    img = np.ones((height, width, 3), dtype=np.uint8) * 200
    
    # Add some text-like patterns to make it realistic
    if width > 100 and height > 100:
        cv2.rectangle(img, (50, 50), (min(width-50, 200), min(height-50, 150)), (0, 0, 0), -1)
    
    return img


@st.composite
def image_dimensions(draw):
    """
    Strategy for generating valid image dimensions.
    
    Generates width and height values that represent realistic image sizes.
    """
    width = draw(st.integers(min_value=100, max_value=4000))
    height = draw(st.integers(min_value=100, max_value=4000))
    return width, height


# ── Property Tests ────────────────────────────────────────────────────────────

# Feature: improve-answer-key-extraction-and-github-setup, Property 6: Image Dimension Normalization
# **Validates: Requirements 2.3**
@settings(max_examples=100, deadline=None)
@given(dimensions=image_dimensions())
def test_property_6_image_dimension_normalization(dimensions):
    """
    Property 6: Image Dimension Normalization
    
    For any input image, after preprocessing, the image dimensions should match 
    the configured target dimensions (default 1024px width with maintained aspect ratio).
    
    This property verifies that:
    1. Images wider than target_width are resized to target_width
    2. Images narrower than target_width maintain their original width
    3. Aspect ratio is preserved during resizing
    4. The preprocessed image file exists and is readable
    """
    width, height = dimensions
    target_width = 1024
    
    # Create a temporary test image with the generated dimensions
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img = create_test_image(width, height)
    cv2.imwrite(tmp.name, img)
    tmp.close()
    
    try:
        # Preprocess the image
        preprocessed_path = ollama_client.preprocess_image(tmp.name, target_width=target_width)
        
        # Verify the preprocessed file exists
        assert os.path.exists(preprocessed_path), \
            f"Preprocessed file should exist at {preprocessed_path}"
        
        # Load the preprocessed image
        processed_img = cv2.imread(preprocessed_path)
        assert processed_img is not None, \
            f"Preprocessed image should be readable"
        
        # Get the dimensions of the preprocessed image
        processed_height, processed_width = processed_img.shape[:2]
        
        # Property: Images wider than target_width should be resized to target_width
        if width > target_width:
            assert processed_width == target_width, \
                f"Image wider than {target_width}px should be resized to {target_width}px, " \
                f"but got {processed_width}px (original: {width}px)"
            
            # Property: Aspect ratio should be maintained
            original_aspect_ratio = height / width
            processed_aspect_ratio = processed_height / processed_width
            
            # Allow small rounding errors (within 2% or 0.002 absolute, whichever is larger)
            # This accounts for integer rounding in pixel dimensions
            aspect_ratio_diff = abs(original_aspect_ratio - processed_aspect_ratio)
            max_allowed_diff = max(original_aspect_ratio * 0.02, 0.002)
            
            assert aspect_ratio_diff <= max_allowed_diff, \
                f"Aspect ratio should be maintained. Original: {original_aspect_ratio:.4f}, " \
                f"Processed: {processed_aspect_ratio:.4f}, Diff: {aspect_ratio_diff:.4f}"
        
        # Property: Images narrower than target_width should maintain their width
        else:
            assert processed_width <= width, \
                f"Image narrower than {target_width}px should not be upscaled. " \
                f"Original: {width}px, Processed: {processed_width}px"
        
        # Cleanup preprocessed file
        os.unlink(preprocessed_path)
        
    finally:
        # Cleanup original test file
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


# Feature: improve-answer-key-extraction-and-github-setup, Property 8: Original File Preservation
# **Validates: Requirements 2.5**
@settings(max_examples=100, deadline=None)
@given(dimensions=image_dimensions())
def test_property_8_original_file_preservation(dimensions):
    """
    Property 8: Original File Preservation
    
    For any input file, after extraction completes (success or failure), 
    the original file should remain unmodified and any temporary files 
    should be cleaned up.
    
    This property verifies that:
    1. Original file content is unchanged after extraction
    2. Original file modification time is unchanged
    3. Temporary preprocessed files are cleaned up
    4. Temporary PDF conversion files are cleaned up (if applicable)
    5. Cleanup happens even when extraction fails
    """
    width, height = dimensions
    
    # Create a temporary test image with the generated dimensions
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img = create_test_image(width, height)
    cv2.imwrite(tmp.name, img)
    tmp.close()
    
    try:
        # Get original file properties before extraction
        original_size = os.path.getsize(tmp.name)
        original_mtime = os.path.getmtime(tmp.name)
        
        # Read original file content
        with open(tmp.name, 'rb') as f:
            original_content = f.read()
        
        # Get the directory where temporary files would be created
        temp_dir = os.path.dirname(tmp.name)
        base_name = os.path.basename(tmp.name)
        name_without_ext = os.path.splitext(base_name)[0]
        
        # Expected temporary file paths
        expected_preprocessed_path = os.path.join(temp_dir, f"{name_without_ext}_preprocessed.jpg")
        expected_pdf_conversion_path = tmp.name + "_converted.jpg"
        
        # Track files before extraction
        files_before = set(os.listdir(temp_dir))
        
        # Attempt extraction (will fail because it's not a real question paper, but that's OK)
        # We're testing file preservation, not extraction success
        try:
            result, warnings, processing_time = ollama_client.extract_answer_key_from_image(tmp.name)
        except Exception:
            # Extraction may fail, but cleanup should still happen
            pass
        
        # Property 1: Original file should still exist
        assert os.path.exists(tmp.name), \
            "Original file should still exist after extraction"
        
        # Property 2: Original file size should be unchanged
        current_size = os.path.getsize(tmp.name)
        assert current_size == original_size, \
            f"Original file size changed: was {original_size}, now {current_size}"
        
        # Property 3: Original file content should be unchanged
        with open(tmp.name, 'rb') as f:
            current_content = f.read()
        assert current_content == original_content, \
            "Original file content should be unchanged after extraction"
        
        # Property 4: Original file modification time should be unchanged
        # (allowing small tolerance for filesystem timestamp precision)
        current_mtime = os.path.getmtime(tmp.name)
        assert abs(current_mtime - original_mtime) < 1.0, \
            f"Original file modification time changed: was {original_mtime}, now {current_mtime}"
        
        # Property 5: Temporary preprocessed file should be cleaned up
        assert not os.path.exists(expected_preprocessed_path), \
            f"Temporary preprocessed file should be cleaned up: {expected_preprocessed_path}"
        
        # Property 6: Temporary PDF conversion file should be cleaned up (if it was created)
        assert not os.path.exists(expected_pdf_conversion_path), \
            f"Temporary PDF conversion file should be cleaned up: {expected_pdf_conversion_path}"
        
        # Property 7: No new files should remain in the directory
        # (except for files that might be created by other processes)
        files_after = set(os.listdir(temp_dir))
        new_files = files_after - files_before
        
        # Filter out the original test file itself
        new_files.discard(base_name)
        
        # Filter out files that are not related to our extraction process
        # (e.g., .bin files created by Hypothesis or other processes)
        extraction_related_files = {
            f for f in new_files 
            if (name_without_ext in f and f.endswith(('.jpg', '.png', '.jpeg')))
        }
        
        # There should be no extraction-related files remaining
        assert len(extraction_related_files) == 0, \
            f"Temporary extraction files were not cleaned up: {extraction_related_files}"
        
    finally:
        # Cleanup original test file
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)
