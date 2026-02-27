"""
Unit tests for multi-pass extraction functionality.

Tests the refactored extract_answer_key_from_image() function with
configuration support, multi-pass extraction, and structured logging.
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import ollama_client
from ollama_client import ExtractionConfig, extract_answer_key_from_image


def _make_ollama_response(content: str):
    """Helper to create a mock Ollama response."""
    mock_response = MagicMock()
    mock_response.message.content = content
    return mock_response


class TestMultiPassExtraction:
    """Test multi-pass extraction with configuration."""

    def test_accepts_config_parameter(self):
        """Test that the function accepts an optional config parameter."""
        # Create a temporary test image
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            config = ExtractionConfig(
                max_extraction_passes=2,
                enable_preprocessing=False
            )
            
            with patch("ollama_client.ollama.chat", return_value=_make_ollama_response('{"1":"A"}')):
                result, warnings, processing_time = extract_answer_key_from_image(img_path, config=config)
            
            assert isinstance(result, dict)
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    def test_uses_default_config_when_none_provided(self):
        """Test that default config is used when none is provided."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            with patch("ollama_client.ollama.chat", return_value=_make_ollama_response('{"1":"A"}')):
                result, warnings, processing_time = extract_answer_key_from_image(img_path)
            
            assert isinstance(result, dict)
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    def test_respects_max_extraction_passes(self):
        """Test that the function respects max_extraction_passes config."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            config = ExtractionConfig(
                max_extraction_passes=1,
                enable_preprocessing=False
            )
            
            # Mock to fail on first call
            with patch("ollama_client.ollama.chat", return_value=_make_ollama_response("invalid")):
                result, warnings, processing_time = extract_answer_key_from_image(img_path, config=config)
            
            # Should return empty dict after 1 failed pass
            assert result == {}
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    def test_early_exit_on_success(self):
        """Test that extraction exits early on first successful pass."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            config = ExtractionConfig(
                max_extraction_passes=3,
                enable_preprocessing=False
            )
            
            call_count = 0
            def mock_chat(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                return _make_ollama_response('{"1":"A","2":"B"}')
            
            with patch("ollama_client.ollama.chat", side_effect=mock_chat):
                result, warnings, processing_time = extract_answer_key_from_image(img_path, config=config)
            
            # Should succeed on first pass and not make additional calls
            assert result == {1: "A", 2: "B"}
            assert call_count == 1
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    def test_validates_results_before_returning(self):
        """Test that results are validated before being returned."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            config = ExtractionConfig(enable_preprocessing=False)
            
            # Return invalid data that should be filtered out
            invalid_json = '{"1":"A","2":"X","-1":"B","3":"C"}'
            
            with patch("ollama_client.ollama.chat", return_value=_make_ollama_response(invalid_json)):
                result, warnings, processing_time = extract_answer_key_from_image(img_path, config=config)
            
            # Should only contain valid entries (1:A and 3:C)
            # Invalid answer "X" and negative question "-1" should be filtered
            assert result == {1: "A", 3: "C"}
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    def test_preprocessing_can_be_disabled(self):
        """Test that preprocessing can be disabled via config."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            config = ExtractionConfig(enable_preprocessing=False)
            
            with patch("ollama_client.ollama.chat", return_value=_make_ollama_response('{"1":"A"}')):
                with patch("ollama_client.preprocess_image") as mock_preprocess:
                    result, warnings, processing_time = extract_answer_key_from_image(img_path, config=config)
                    
                    # Preprocessing should not be called
                    mock_preprocess.assert_not_called()
            
            assert result == {1: "A"}
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    def test_uses_configured_dpi_for_pdf(self):
        """Test that PDF conversion uses configured DPI."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"fake pdf data")
            pdf_path = tmp.name

        try:
            config = ExtractionConfig(
                min_dpi_for_pdf=300,
                enable_preprocessing=False
            )
            
            with patch("ollama_client.convert_pdf_to_image") as mock_convert:
                mock_convert.return_value = "/tmp/fake_converted.jpg"
                
                with patch("ollama_client.ollama.chat", return_value=_make_ollama_response('{"1":"A"}')):
                    with patch("os.path.exists", return_value=True):
                        with patch("os.remove"):
                            result, warnings, processing_time = extract_answer_key_from_image(pdf_path, config=config)
                
                # Should call convert_pdf_to_image with configured DPI
                mock_convert.assert_called_once_with(pdf_path, dpi=300)
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

    def test_uses_configured_target_width(self):
        """Test that preprocessing uses configured target width."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            config = ExtractionConfig(
                target_image_width=2048,
                enable_preprocessing=True
            )
            
            with patch("ollama_client.preprocess_image") as mock_preprocess:
                mock_preprocess.return_value = "/tmp/fake_preprocessed.jpg"
                
                with patch("ollama_client.ollama.chat", return_value=_make_ollama_response('{"1":"A"}')):
                    with patch("os.path.exists", return_value=True):
                        with patch("os.remove"):
                            result, warnings, processing_time = extract_answer_key_from_image(img_path, config=config)
                
                # Should call preprocess_image with configured width
                mock_preprocess.assert_called_once_with(img_path, target_width=2048)
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    def test_uses_fallback_model_on_last_pass(self):
        """Test that fallback model is used on the last pass when configured."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            config = ExtractionConfig(
                max_extraction_passes=3,
                primary_model="moondream",
                fallback_model="llava",
                enable_preprocessing=False
            )
            
            call_count = 0
            models_used = []
            
            def mock_chat(model=None, messages=None, **kwargs):
                nonlocal call_count
                call_count += 1
                models_used.append(model)
                # Fail on first two passes, succeed on third (fallback)
                if call_count < 3:
                    return _make_ollama_response("invalid")
                else:
                    return _make_ollama_response('{"1":"A","2":"B"}')
            
            with patch("ollama_client.ollama.chat", side_effect=mock_chat):
                result, warnings, processing_time = extract_answer_key_from_image(img_path, config=config)
            
            # Should make 3 calls total
            assert call_count == 3
            # First two passes should use primary model
            assert models_used[0] == "moondream"
            assert models_used[1] == "moondream"
            # Last pass should use fallback model
            assert models_used[2] == "llava"
            # Should succeed with fallback model
            assert result == {1: "A", 2: "B"}
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    def test_no_fallback_when_not_configured(self):
        """Test that no fallback model is used when not configured."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            config = ExtractionConfig(
                max_extraction_passes=3,
                primary_model="moondream",
                fallback_model=None,  # No fallback configured
                enable_preprocessing=False
            )
            
            call_count = 0
            models_used = []
            
            def mock_chat(model=None, messages=None, **kwargs):
                nonlocal call_count
                call_count += 1
                models_used.append(model)
                return _make_ollama_response("invalid")
            
            with patch("ollama_client.ollama.chat", side_effect=mock_chat):
                result, warnings, processing_time = extract_answer_key_from_image(img_path, config=config)
            
            # Should make 3 calls total (all with primary model)
            assert call_count == 3
            # All passes should use primary model
            assert all(model == "moondream" for model in models_used)
            # Should fail and return empty dict
            assert result == {}
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    def test_fallback_model_logs_correctly(self):
        """Test that fallback model usage is logged correctly."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            config = ExtractionConfig(
                max_extraction_passes=2,
                primary_model="moondream",
                fallback_model="llava",
                enable_preprocessing=False
            )
            
            def mock_chat(model=None, messages=None, **kwargs):
                # Fail on first pass, succeed on second (fallback)
                if model == "moondream":
                    return _make_ollama_response("invalid")
                else:
                    return _make_ollama_response('{"1":"A"}')
            
            with patch("ollama_client.ollama.chat", side_effect=mock_chat):
                with patch("ollama_client.log_debug") as mock_log:
                    result, warnings, processing_time = extract_answer_key_from_image(img_path, config=config)
                    
                    # Check that fallback model usage was logged
                    log_calls = [str(call) for call in mock_log.call_args_list]
                    fallback_logged = any("fallback model" in str(call).lower() for call in log_calls)
                    assert fallback_logged, "Fallback model usage should be logged"
            
            assert result == {1: "A"}
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    def test_fallback_model_early_exit_on_primary_success(self):
        """Test that fallback model is not used if primary model succeeds early."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            config = ExtractionConfig(
                max_extraction_passes=3,
                primary_model="moondream",
                fallback_model="llava",
                enable_preprocessing=False
            )
            
            call_count = 0
            models_used = []
            
            def mock_chat(model=None, messages=None, **kwargs):
                nonlocal call_count
                call_count += 1
                models_used.append(model)
                # Succeed on first pass
                return _make_ollama_response('{"1":"A","2":"B"}')
            
            with patch("ollama_client.ollama.chat", side_effect=mock_chat):
                result, warnings, processing_time = extract_answer_key_from_image(img_path, config=config)
            
            # Should only make 1 call (early exit on success)
            assert call_count == 1
            # Should only use primary model
            assert models_used[0] == "moondream"
            # Fallback model should never be used
            assert "llava" not in models_used
            assert result == {1: "A", 2: "B"}
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

    def test_uses_fallback_model_on_last_pass(self):
        """Test that fallback model is used on the last pass when configured."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            config = ExtractionConfig(
                max_extraction_passes=3,
                primary_model="moondream",
                fallback_model="llava",
                enable_preprocessing=False
            )
            
            call_count = 0
            models_used = []
            
            def mock_chat(model=None, messages=None, **kwargs):
                nonlocal call_count
                call_count += 1
                models_used.append(model)
                # Fail on first two passes, succeed on third (fallback)
                if call_count < 3:
                    return _make_ollama_response("invalid")
                else:
                    return _make_ollama_response('{"1":"A","2":"B"}')
            
            with patch("ollama_client.ollama.chat", side_effect=mock_chat):
                result, warnings, processing_time = extract_answer_key_from_image(img_path, config=config)
            
            # Should make 3 calls total
            assert call_count == 3
            # First two passes should use primary model
            assert models_used[0] == "moondream"
            assert models_used[1] == "moondream"
            # Last pass should use fallback model
            assert models_used[2] == "llava"
            # Should succeed with fallback model
            assert result == {1: "A", 2: "B"}
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    def test_no_fallback_when_not_configured(self):
        """Test that no fallback model is used when not configured."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            config = ExtractionConfig(
                max_extraction_passes=3,
                primary_model="moondream",
                fallback_model=None,  # No fallback configured
                enable_preprocessing=False
            )
            
            call_count = 0
            models_used = []
            
            def mock_chat(model=None, messages=None, **kwargs):
                nonlocal call_count
                call_count += 1
                models_used.append(model)
                return _make_ollama_response("invalid")
            
            with patch("ollama_client.ollama.chat", side_effect=mock_chat):
                result, warnings, processing_time = extract_answer_key_from_image(img_path, config=config)
            
            # Should make 3 calls total (all with primary model)
            assert call_count == 3
            # All passes should use primary model
            assert all(model == "moondream" for model in models_used)
            # Should fail and return empty dict
            assert result == {}
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    def test_fallback_model_logs_correctly(self):
        """Test that fallback model usage is logged correctly."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            config = ExtractionConfig(
                max_extraction_passes=2,
                primary_model="moondream",
                fallback_model="llava",
                enable_preprocessing=False
            )
            
            def mock_chat(model=None, messages=None, **kwargs):
                # Fail on first pass, succeed on second (fallback)
                if model == "moondream":
                    return _make_ollama_response("invalid")
                else:
                    return _make_ollama_response('{"1":"A"}')
            
            with patch("ollama_client.ollama.chat", side_effect=mock_chat):
                with patch("ollama_client.log_debug") as mock_log:
                    result, warnings, processing_time = extract_answer_key_from_image(img_path, config=config)
                    
                    # Check that fallback model usage was logged
                    log_calls = [str(call) for call in mock_log.call_args_list]
                    fallback_logged = any("fallback model" in str(call).lower() for call in log_calls)
                    assert fallback_logged, "Fallback model usage should be logged"
            
            assert result == {1: "A"}
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    def test_fallback_model_early_exit_on_primary_success(self):
        """Test that fallback model is not used if primary model succeeds early."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            img_path = tmp.name

        try:
            config = ExtractionConfig(
                max_extraction_passes=3,
                primary_model="moondream",
                fallback_model="llava",
                enable_preprocessing=False
            )
            
            call_count = 0
            models_used = []
            
            def mock_chat(model=None, messages=None, **kwargs):
                nonlocal call_count
                call_count += 1
                models_used.append(model)
                # Succeed on first pass
                return _make_ollama_response('{"1":"A","2":"B"}')
            
            with patch("ollama_client.ollama.chat", side_effect=mock_chat):
                result, warnings, processing_time = extract_answer_key_from_image(img_path, config=config)
            
            # Should only make 1 call (early exit on success)
            assert call_count == 1
            # Should only use primary model
            assert models_used[0] == "moondream"
            # Fallback model should never be used
            assert "llava" not in models_used
            assert result == {1: "A", 2: "B"}
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)
