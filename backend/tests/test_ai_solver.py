"""
test_ai_solver.py
-----------------
Unit tests for ai_solver.py module.
Tests the AISolver class including prompt building, response parsing,
and question solving with mocked Ollama responses.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

from ai_solver import AISolver, SolverConfig, SolverResult, ModelSelector
from question_parser import Question, QuestionOption


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_question(number: int = 1, question_type: str = "factual", has_image: bool = False) -> Question:
    """Create a test Question object."""
    return Question(
        number=number,
        text="What is the capital of France?",
        options=[
            QuestionOption(label="A", text="London"),
            QuestionOption(label="B", text="Paris"),
            QuestionOption(label="C", text="Berlin"),
            QuestionOption(label="D", text="Madrid"),
        ],
        page_number=1,
        has_image=has_image,
        image_data=None,
        question_type=question_type
    )


def _make_ollama_response(content: str):
    """Build a mock return value that matches ollama.chat() structure."""
    return {"message": {"content": content}}


# ── Tests for _build_prompt ───────────────────────────────────────────────────

class TestBuildPrompt:
    
    def test_prompt_includes_question_text(self):
        """Prompt should include the question text."""
        solver = AISolver()
        question = _make_question()
        prompt = solver._build_prompt(question)
        
        assert "What is the capital of France?" in prompt
    
    def test_prompt_includes_all_options(self):
        """Prompt should include all answer options."""
        solver = AISolver()
        question = _make_question()
        prompt = solver._build_prompt(question)
        
        assert "A) London" in prompt
        assert "B) Paris" in prompt
        assert "C) Berlin" in prompt
        assert "D) Madrid" in prompt
    
    def test_prompt_includes_instructions(self):
        """Prompt should include solving instructions."""
        solver = AISolver()
        question = _make_question()
        prompt = solver._build_prompt(question)
        
        assert "ANSWER:" in prompt
        assert "EXPLANATION:" in prompt
        assert "Instructions:" in prompt


# ── Tests for _parse_ai_response ──────────────────────────────────────────────

class TestParseAIResponse:
    
    def test_parse_valid_structured_response(self):
        """Should parse a properly formatted response."""
        solver = AISolver()
        question = _make_question()
        response = """ANSWER: B
EXPLANATION: Paris is the capital and largest city of France."""
        
        option, explanation = solver._parse_ai_response(response, question)
        
        assert option == "B"
        assert "Paris" in explanation
    
    def test_parse_response_with_brackets(self):
        """Should parse response with answer in brackets."""
        solver = AISolver()
        question = _make_question()
        response = """ANSWER: [B]
EXPLANATION: Paris is the capital of France."""
        
        option, explanation = solver._parse_ai_response(response, question)
        
        assert option == "B"
    
    def test_parse_invalid_option_returns_none(self):
        """Should return None if option not in question."""
        solver = AISolver()
        question = _make_question()
        response = """ANSWER: Z
EXPLANATION: Invalid option."""
        
        option, explanation = solver._parse_ai_response(response, question)
        
        assert option is None
    
    def test_parse_malformed_response_returns_none(self):
        """Should return None for malformed response."""
        solver = AISolver()
        question = _make_question()
        response = "This is just random text without structure."
        
        option, explanation = solver._parse_ai_response(response, question)
        
        assert option is None
        assert len(explanation) > 0  # Should still return some explanation
    
    def test_parse_multiline_explanation(self):
        """Should handle multi-line explanations."""
        solver = AISolver()
        question = _make_question()
        response = """ANSWER: B
EXPLANATION: Paris is the capital of France.
It is located in the north-central part of the country.
Paris is known for the Eiffel Tower."""
        
        option, explanation = solver._parse_ai_response(response, question)
        
        assert option == "B"
        assert "Eiffel Tower" in explanation


# ── Tests for solve_question ──────────────────────────────────────────────────

class TestSolveQuestion:
    
    @patch('ai_solver.ollama.chat')
    def test_solve_question_success(self, mock_chat):
        """Should successfully solve a question."""
        mock_chat.return_value = _make_ollama_response(
            "ANSWER: B\nEXPLANATION: Paris is the capital of France."
        )
        
        solver = AISolver()
        question = _make_question()
        result = solver.solve_question(question)
        
        assert result.status == "solved"
        assert result.selected_option == "B"
        assert "Paris" in result.explanation
        assert result.question_number == 1
        assert result.processing_time_ms > 0
    
    @patch('ai_solver.ollama.chat')
    def test_solve_question_unsolvable(self, mock_chat):
        """Should handle unsolvable questions."""
        mock_chat.return_value = _make_ollama_response(
            "I cannot determine the answer due to insufficient information."
        )
        
        solver = AISolver()
        question = _make_question()
        result = solver.solve_question(question)
        
        assert result.status == "unsolvable"
        assert result.selected_option is None
        assert "insufficient information" in result.explanation.lower()
    
    @patch('ai_solver.ollama.chat')
    def test_solve_question_retry_on_parse_failure(self, mock_chat):
        """Should retry when response parsing fails."""
        # First call returns malformed, second call returns valid
        mock_chat.side_effect = [
            _make_ollama_response("Invalid response"),
            _make_ollama_response("ANSWER: B\nEXPLANATION: Paris is correct.")
        ]
        
        solver = AISolver(SolverConfig(max_retries=2))
        question = _make_question()
        result = solver.solve_question(question)
        
        # Should succeed on retry
        assert result.status == "solved"
        assert result.selected_option == "B"
        assert mock_chat.call_count == 2
    
    @patch('ai_solver.ollama.chat')
    def test_solve_question_error_after_retries(self, mock_chat):
        """Should return error status after all retries fail."""
        mock_chat.side_effect = Exception("Connection error")
        
        solver = AISolver(SolverConfig(max_retries=2))
        question = _make_question()
        result = solver.solve_question(question)
        
        assert result.status == "error"
        assert result.selected_option is None
        assert "Connection error" in result.error_message
        assert mock_chat.call_count == 3  # Initial + 2 retries
    
    @patch('ai_solver.ollama.chat')
    def test_solve_question_timeout(self, mock_chat):
        """Should handle timeout errors."""
        mock_chat.side_effect = TimeoutError("Request timeout")
        
        solver = AISolver(SolverConfig(timeout_seconds=30))
        question = _make_question()
        result = solver.solve_question(question)
        
        assert result.status == "timeout"
        assert result.selected_option is None
        assert "Timeout" in result.error_message


# ── Tests for ModelSelector ───────────────────────────────────────────────────

class TestModelSelector:
    
    def test_select_model_for_math_question(self):
        """Should select math model for math questions."""
        selector = ModelSelector()
        question = _make_question(question_type="math")
        
        model = selector.select_model(question)
        
        assert model == "llama3.2:latest"
    
    def test_select_model_for_visual_question(self):
        """Should select vision model for questions with images."""
        selector = ModelSelector()
        question = _make_question(has_image=True)
        
        model = selector.select_model(question)
        
        assert model == "moondream:latest"
    
    def test_select_model_defaults_to_general(self):
        """Should use default model for unknown question types."""
        selector = ModelSelector()
        question = _make_question(question_type="unknown")
        
        model = selector.select_model(question)
        
        assert model == "llama3.2:latest"
    
    @patch('ai_solver.ollama.list')
    def test_is_model_available_true(self, mock_list):
        """Should return True when model is available."""
        mock_model = MagicMock()
        mock_model.model = "llama3.2:latest"
        mock_list.return_value = MagicMock(models=[mock_model])
        
        selector = ModelSelector()
        available = selector.is_model_available("llama3.2:latest")
        
        assert available is True
    
    @patch('ai_solver.ollama.list')
    def test_is_model_available_false(self, mock_list):
        """Should return False when model is not available."""
        mock_list.return_value = MagicMock(models=[])
        
        selector = ModelSelector()
        available = selector.is_model_available("nonexistent:latest")
        
        assert available is False
    
    @patch('ai_solver.ollama.list')
    def test_select_model_with_fallback_preferred_available(self, mock_list):
        """Should return preferred model when it's available."""
        mock_model = MagicMock()
        mock_model.model = "moondream:latest"
        mock_list.return_value = MagicMock(models=[mock_model])
        
        selector = ModelSelector()
        question = _make_question(has_image=True)  # Prefers moondream
        
        model = selector.select_model_with_fallback(question)
        
        assert model == "moondream:latest"
    
    @patch('ai_solver.ollama.list')
    def test_select_model_with_fallback_to_default(self, mock_list):
        """Should fallback to default model when preferred is unavailable."""
        # Only default model is available
        mock_model = MagicMock()
        mock_model.model = "llama3.2:latest"
        mock_list.return_value = MagicMock(models=[mock_model])
        
        selector = ModelSelector()
        question = _make_question(has_image=True)  # Prefers moondream (unavailable)
        
        model = selector.select_model_with_fallback(question)
        
        # Should fallback to default
        assert model == "llama3.2:latest"
    
    @patch('ai_solver.ollama.list')
    def test_select_model_with_fallback_no_models_available(self, mock_list):
        """Should return preferred model even when no models available (will fail later)."""
        # No models available
        mock_list.return_value = MagicMock(models=[])
        
        selector = ModelSelector()
        question = _make_question(has_image=True)  # Prefers moondream
        
        model = selector.select_model_with_fallback(question)
        
        # Should return preferred model anyway (will fail with clear error later)
        assert model == "moondream:latest"
    
    def test_select_model_for_logical_question(self):
        """Should select appropriate model for logical questions."""
        selector = ModelSelector()
        question = _make_question(question_type="logical")
        
        model = selector.select_model(question)
        
        assert model == "llama3.2:latest"
    
    def test_select_model_for_factual_question(self):
        """Should select appropriate model for factual questions."""
        selector = ModelSelector()
        question = _make_question(question_type="factual")
        
        model = selector.select_model(question)
        
        assert model == "llama3.2:latest"
    
    def test_visual_question_overrides_type(self):
        """Should prioritize vision model when question has image, regardless of type."""
        selector = ModelSelector()
        question = _make_question(question_type="math", has_image=True)
        
        model = selector.select_model(question)
        
        # Should select vision model even though type is math
        assert model == "moondream:latest"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
