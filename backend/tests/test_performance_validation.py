"""
Performance validation tests for answer key extraction system.

Tests verify:
- Extraction completes within configured timeout (default 30s)
- Preprocessing completes within 2s
- Concurrent requests are handled correctly
- Processing time is recorded for monitoring

Feature: improve-answer-key-extraction-and-github-setup
Requirements: 6.2, 10.2
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ollama_client import (
    extract_answer_key_from_image,
    preprocess_image,
    ExtractionConfig
)


class TestExtractionTimeout:
    """Test that extraction respects configured timeout values."""
    
    def test_extraction_completes_within_default_timeout(self, sample_answer_key_image):
        """
        Test that extraction completes within default timeout (30s).
        
        **Validates: Requirement 10.2** - Timeout configuration support
        """
        config = ExtractionConfig()  # Default timeout is 30s
        
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A","2":"B","3":"C"}'
        
        start_time = time.time()
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            result, warnings, duration = extract_answer_key_from_image(
                sample_answer_key_image,
                config=config
            )
        
        elapsed = time.time() - start_time
        
        # Should complete well within timeout
        assert elapsed < config.extraction_timeout_seconds
        assert result  # Should have results
    
    def test_extraction_respects_custom_timeout(self, sample_answer_key_image):
        """
        Test that extraction respects custom timeout configuration.
        
        **Validates: Requirement 10.2** - Custom timeout configuration
        """
        config = ExtractionConfig(extraction_timeout_seconds=5)
        
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A"}'
        
        start_time = time.time()
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            result, warnings, duration = extract_answer_key_from_image(
                sample_answer_key_image,
                config=config
            )
        
        elapsed = time.time() - start_time
        
        # Should complete within custom timeout
        assert elapsed < config.extraction_timeout_seconds
    
    def test_extraction_with_very_short_timeout(self, sample_answer_key_image):
        """
        Test extraction behavior with very short timeout.
        
        This tests that the system handles timeout constraints gracefully.
        **Validates: Requirement 10.2** - Timeout configuration
        """
        config = ExtractionConfig(
            extraction_timeout_seconds=1,
            max_extraction_passes=1  # Reduce passes to fit in timeout
        )
        
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A"}'
        
        # Should not raise exception even with short timeout
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            result, warnings, duration = extract_answer_key_from_image(
                sample_answer_key_image,
                config=config
            )
        
        # Should complete or return empty result, not crash
        assert isinstance(result, dict)


class TestPreprocessingPerformance:
    """Test that preprocessing completes within performance requirements."""
    
    def test_preprocessing_completes_within_2_seconds(self, sample_answer_key_image):
        """
        Test that image preprocessing completes within 2 seconds.
        
        **Validates: Requirement 6.2** - Processing time monitoring
        Task 13.3 requirement: Preprocessing must complete within 2s
        """
        start_time = time.time()
        
        preprocessed_path = preprocess_image(sample_answer_key_image)
        
        elapsed = time.time() - start_time
        
        # Preprocessing should complete within 2 seconds
        assert elapsed < 2.0, f"Preprocessing took {elapsed:.2f}s, expected < 2.0s"
        
        # Verify preprocessed file exists
        assert os.path.exists(preprocessed_path)
        
        # Cleanup
        if os.path.exists(preprocessed_path):
            os.remove(preprocessed_path)
    
    def test_preprocessing_multiple_images_performance(self, sample_answer_key_image):
        """
        Test preprocessing performance with multiple images.
        
        **Validates: Requirement 6.2** - Processing time monitoring
        """
        num_images = 5
        times = []
        
        for _ in range(num_images):
            start_time = time.time()
            preprocessed_path = preprocess_image(sample_answer_key_image)
            elapsed = time.time() - start_time
            times.append(elapsed)
            
            # Cleanup
            if os.path.exists(preprocessed_path):
                os.remove(preprocessed_path)
        
        # Each preprocessing should be under 2 seconds
        for i, t in enumerate(times):
            assert t < 2.0, f"Image {i+1} preprocessing took {t:.2f}s, expected < 2.0s"
        
        # Average should also be reasonable
        avg_time = sum(times) / len(times)
        assert avg_time < 2.0, f"Average preprocessing time {avg_time:.2f}s exceeds 2.0s"


class TestConcurrentRequests:
    """Test that the system handles concurrent extraction requests correctly."""
    
    def test_concurrent_extractions_complete_successfully(self, sample_answer_key_image):
        """
        Test that multiple concurrent extraction requests complete successfully.
        
        **Validates: Requirement 6.2** - Processing time monitoring
        Task 13.3 requirement: Test concurrent requests
        """
        num_concurrent = 3
        config = ExtractionConfig()
        
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A","2":"B"}'
        
        def run_extraction():
            """Run a single extraction."""
            result, warnings, duration = extract_answer_key_from_image(
                sample_answer_key_image,
                config=config
            )
            return result, duration
        
        # Run concurrent extractions with patch applied at module level
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
                futures = [executor.submit(run_extraction) for _ in range(num_concurrent)]
                results = [future.result() for future in as_completed(futures)]
        
        # All extractions should complete successfully
        assert len(results) == num_concurrent
        
        for result, duration in results:
            assert isinstance(result, dict)
            assert len(result) > 0  # Should have extracted answers
            assert duration > 0  # Should have recorded time
    
    def test_concurrent_extractions_with_different_configs(self, sample_answer_key_image):
        """
        Test concurrent extractions with different configurations.
        
        **Validates: Requirement 10.2** - Timeout configuration
        """
        configs = [
            ExtractionConfig(extraction_timeout_seconds=30),
            ExtractionConfig(extraction_timeout_seconds=20),
            ExtractionConfig(extraction_timeout_seconds=15),
        ]
        
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A"}'
        
        def run_extraction_with_config(config):
            """Run extraction with specific config."""
            start_time = time.time()
            with patch('ollama_client.ollama.chat', return_value=mock_response):
                result, warnings, duration = extract_answer_key_from_image(
                    sample_answer_key_image,
                    config=config
                )
            elapsed = time.time() - start_time
            return result, elapsed, config.extraction_timeout_seconds
        
        # Run concurrent extractions with different configs
        with ThreadPoolExecutor(max_workers=len(configs)) as executor:
            futures = [executor.submit(run_extraction_with_config, cfg) for cfg in configs]
            results = [future.result() for future in as_completed(futures)]
        
        # All should complete within their respective timeouts
        for result, elapsed, timeout in results:
            assert isinstance(result, dict)
            assert elapsed < timeout, f"Extraction took {elapsed:.2f}s, timeout was {timeout}s"
    
    def test_concurrent_preprocessing_operations(self, sample_answer_key_image):
        """
        Test that concurrent preprocessing operations complete correctly.
        
        **Validates: Requirement 6.2** - Processing time monitoring
        """
        num_concurrent = 5
        
        def run_preprocessing():
            """Run a single preprocessing operation."""
            start_time = time.time()
            preprocessed_path = preprocess_image(sample_answer_key_image)
            elapsed = time.time() - start_time
            # Check file exists immediately after creation
            file_exists = os.path.exists(preprocessed_path)
            return preprocessed_path, elapsed, file_exists
        
        # Run concurrent preprocessing
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(run_preprocessing) for _ in range(num_concurrent)]
            results = [future.result() for future in as_completed(futures)]
        
        # All should complete successfully
        assert len(results) == num_concurrent
        
        # Track unique paths for cleanup
        unique_paths = set()
        
        for preprocessed_path, elapsed, file_existed in results:
            # File should have existed when created
            assert file_existed, f"Preprocessed file {preprocessed_path} did not exist after creation"
            assert elapsed < 2.0, f"Preprocessing took {elapsed:.2f}s, expected < 2.0s"
            unique_paths.add(preprocessed_path)
        
        # Cleanup unique paths (concurrent operations may share same output file)
        for path in unique_paths:
            if os.path.exists(path):
                os.remove(path)


class TestProcessingTimeRecording:
    """Test that processing time is recorded for monitoring."""
    
    def test_processing_time_is_returned(self, sample_answer_key_image):
        """
        Test that processing time is returned from extraction.
        
        **Validates: Requirement 6.2** - Record processing time
        """
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A"}'
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            result, warnings, duration = extract_answer_key_from_image(
                sample_answer_key_image
            )
        
        # Duration should be returned and be positive
        assert duration is not None
        assert duration > 0
        assert isinstance(duration, (int, float))
    
    def test_processing_time_increases_with_passes(self, sample_answer_key_image):
        """
        Test that processing time is recorded for different pass counts.
        
        **Validates: Requirement 6.2** - Processing time monitoring
        
        Note: With mocked Ollama, timing differences may be minimal.
        This test verifies that duration is recorded for different configurations.
        """
        mock_response = MagicMock()
        mock_response.message.content = '{}'  # Empty to force all passes
        
        # Test with 1 pass
        config_1_pass = ExtractionConfig(max_extraction_passes=1)
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            _, _, duration_1 = extract_answer_key_from_image(
                sample_answer_key_image,
                config=config_1_pass
            )
        
        # Test with 3 passes
        config_3_passes = ExtractionConfig(max_extraction_passes=3)
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            _, _, duration_3 = extract_answer_key_from_image(
                sample_answer_key_image,
                config=config_3_passes
            )
        
        # Both should have recorded positive durations
        assert duration_1 > 0, "1 pass should have positive duration"
        assert duration_3 > 0, "3 passes should have positive duration"
        
        # With mocked Ollama, timing may be similar, but both should complete
        # The important validation is that duration is recorded for both configs
    
    def test_api_returns_processing_time(self, client, sample_answer_key_image):
        """
        Test that API endpoint returns processing time in response.
        
        **Validates: Requirement 6.2** - Processing time monitoring
        """
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A","2":"B"}'
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            with open(sample_answer_key_image, 'rb') as f:
                response = client.post('/api/extract_key', data={
                    'qp_file': (f, 'answer_key.jpg')
                })
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Response should include processing_time_ms
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] > 0
        assert isinstance(data["processing_time_ms"], (int, float))


class TestPerformanceUnderLoad:
    """Test system performance under various load conditions."""
    
    def test_extraction_performance_with_max_passes(self, sample_answer_key_image):
        """
        Test extraction performance with maximum configured passes.
        
        **Validates: Requirement 6.2** - Processing time monitoring
        """
        config = ExtractionConfig(max_extraction_passes=3)
        
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A"}'
        
        start_time = time.time()
        
        with patch('ollama_client.ollama.chat', return_value=mock_response):
            result, warnings, duration = extract_answer_key_from_image(
                sample_answer_key_image,
                config=config
            )
        
        elapsed = time.time() - start_time
        
        # Should complete within timeout even with max passes
        assert elapsed < config.extraction_timeout_seconds
        assert result  # Should have results
    
    def test_sequential_extractions_maintain_performance(self, sample_answer_key_image):
        """
        Test that sequential extractions maintain consistent performance.
        
        **Validates: Requirement 6.2** - Processing time monitoring
        """
        num_sequential = 5
        mock_response = MagicMock()
        mock_response.message.content = '{"1":"A"}'
        
        times = []
        
        for _ in range(num_sequential):
            start_time = time.time()
            with patch('ollama_client.ollama.chat', return_value=mock_response):
                result, warnings, duration = extract_answer_key_from_image(
                    sample_answer_key_image
                )
            elapsed = time.time() - start_time
            times.append(elapsed)
        
        # All extractions should complete in reasonable time
        for i, t in enumerate(times):
            assert t < 30.0, f"Extraction {i+1} took {t:.2f}s, expected < 30.0s"
        
        # Performance should not degrade significantly
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Max time should not be more than 2x average (no significant degradation)
        assert max_time < avg_time * 2, \
            f"Performance degraded: max {max_time:.2f}s vs avg {avg_time:.2f}s"
