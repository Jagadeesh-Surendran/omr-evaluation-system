"""
AI Solver module for solving questions using AI models.
"""
from dataclasses import dataclass
from typing import Optional, Tuple
import time
import ollama
from solver_logging_config import get_logger
from question_parser import Question

logger = get_logger("ai_solver")


@dataclass
class SolverConfig:
    """Configuration for AI solver."""
    timeout_seconds: int = 30
    max_retries: int = 2
    retry_backoff_base: float = 2.0
    min_confidence_threshold: float = 0.6


@dataclass
class SolverResult:
    """Result from solving a single question."""
    question_number: int
    selected_option: Optional[str]  # A, B, C, D, E or None
    explanation: str
    confidence: float
    processing_time_ms: float
    status: str  # "solved", "unsolvable", "timeout", "error"
    error_message: Optional[str] = None


class ModelSelector:
    """Selects appropriate AI model for question type."""
    
    def __init__(self):
        """Initialize ModelSelector with model mappings."""
        # Map question types to optimal models
        self.model_map = {
            "math": "llama3.2:latest",
            "logical": "llama3.2:latest",
            "factual": "llama3.2:latest",
            "visual": "moondream:latest"
        }
        self.default_model = "llama3.2:latest"
        logger.info("[MODEL_SELECTOR] Initialized with model mappings")
        logger.debug(f"[MODEL_SELECTOR] Model map: {self.model_map}")
    
    def select_model(self, question: Question) -> str:
        """
        Returns model name based on question type.
        
        Args:
            question: Question object with question_type field
            
        Returns:
            Model name string (e.g., "llama3.2:latest")
        """
        # Check if question has image - use vision model
        if question.has_image:
            model = self.model_map.get("visual", self.default_model)
            logger.info(
                f"[MODEL_SELECTOR] Q{question.number}: Selected vision model '{model}' "
                f"(has_image=True)"
            )
            return model
        
        # Select based on question type
        question_type = question.question_type or "factual"
        model = self.model_map.get(question_type, self.default_model)
        
        logger.info(
            f"[MODEL_SELECTOR] Q{question.number}: Selected model '{model}' "
            f"for type '{question_type}'"
        )
        
        return model
    
    def is_model_available(self, model_name: str) -> bool:
        """
        Checks if model is available in Ollama.
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if model is available, False otherwise
        """
        try:
            # Query Ollama for available models
            models_response = ollama.list()
            
            # Extract model names from response
            available_models = []
            if hasattr(models_response, 'models'):
                available_models = [m.model for m in models_response.models]
            elif isinstance(models_response, dict) and 'models' in models_response:
                available_models = [m['model'] for m in models_response['models']]
            
            # Check if requested model is in the list
            is_available = model_name in available_models
            
            if is_available:
                logger.debug(f"[MODEL_SELECTOR] Model '{model_name}' is available")
            else:
                logger.warning(
                    f"[MODEL_SELECTOR] Model '{model_name}' not found. "
                    f"Available models: {available_models}"
                )
            
            return is_available
            
        except Exception as e:
            logger.error(f"[MODEL_SELECTOR] Error checking model availability: {e}")
            return False
    
    def select_model_with_fallback(self, question: Question) -> str:
        """
        Selects model with fallback logic when model unavailable.
        
        Args:
            question: Question object
            
        Returns:
            Available model name (falls back to default if needed)
        """
        # Get preferred model
        preferred_model = self.select_model(question)
        
        # Check if preferred model is available
        if self.is_model_available(preferred_model):
            return preferred_model
        
        # Fallback to default model
        logger.warning(
            f"[MODEL_SELECTOR] Q{question.number}: Preferred model '{preferred_model}' "
            f"unavailable, falling back to '{self.default_model}'"
        )
        
        # Check if default model is available
        if self.is_model_available(self.default_model):
            return self.default_model
        
        # If even default is unavailable, return preferred anyway
        # (will fail later with clear error message)
        logger.error(
            f"[MODEL_SELECTOR] Q{question.number}: Default model '{self.default_model}' "
            f"also unavailable! Returning '{preferred_model}' anyway."
        )
        return preferred_model



class AISolver:
    """Orchestrates AI-based question solving."""
    
    def __init__(self, config: Optional[SolverConfig] = None):
        """
        Initialize AISolver with configuration.
        
        Args:
            config: SolverConfig object, uses defaults if None
        """
        self.config = config or SolverConfig()
        self.model_selector = ModelSelector()
        logger.info("[AI_SOLVER] Initialized with config")
        logger.debug(f"[AI_SOLVER] Config: {self.config}")
    
    def _build_prompt(self, question: Question) -> str:
        """
        Constructs prompt for AI model.
        Includes question text, options, and instructions.
        
        Args:
            question: Question object with text and options
            
        Returns:
            Formatted prompt string
        """
        logger.debug(f"[AI_SOLVER] Q{question.number}: Building prompt")
        
        # Build options list
        options_text = []
        for option in question.options:
            options_text.append(f"{option.label}) {option.text}")
        
        options_str = "\n".join(options_text)
        
        # Construct structured prompt
        prompt = f"""You are solving a multiple-choice question. Analyze the question carefully and select the correct answer.

Question {question.number}: {question.text}

Options:
{options_str}

Instructions:
1. Read the question and all options carefully
2. Reason through the problem step by step
3. Select the single best answer
4. Provide a brief explanation for your choice

Response format:
ANSWER: [A/B/C/D/E]
EXPLANATION: [Your reasoning in 2-3 sentences]"""
        
        logger.debug(
            f"[AI_SOLVER] Q{question.number}: Prompt built "
            f"({len(prompt)} chars, {len(question.options)} options)"
        )
        
        return prompt

    
    def _parse_ai_response(self, response: str, question: Question) -> Tuple[Optional[str], str]:
        """
        Parses AI response to extract answer and explanation.
        Returns (selected_option, explanation)
        
        Args:
            response: Raw AI response text
            question: Question object for validation
            
        Returns:
            Tuple of (selected_option, explanation)
            selected_option is None if parsing fails
        """
        logger.debug(
            f"[AI_SOLVER] Q{question.number}: Parsing AI response "
            f"({len(response)} chars)"
        )
        
        selected_option = None
        explanation = ""
        
        try:
            # Split response into lines
            lines = response.strip().split('\n')
            
            # Extract ANSWER and EXPLANATION
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Look for ANSWER line
                if line.upper().startswith('ANSWER:'):
                    # Extract answer option (A, B, C, D, or E)
                    answer_part = line.split(':', 1)[1].strip()
                    # Get first character that's A-E
                    for char in answer_part.upper():
                        if char in ['A', 'B', 'C', 'D', 'E']:
                            selected_option = char
                            break
                
                # Look for EXPLANATION line
                elif line.upper().startswith('EXPLANATION:'):
                    # Get explanation text (rest of this line + remaining lines)
                    explanation = line.split(':', 1)[1].strip()
                    # Add remaining lines
                    if i + 1 < len(lines):
                        remaining = '\n'.join(lines[i+1:]).strip()
                        if remaining:
                            explanation = f"{explanation}\n{remaining}"
                    break
            
            # Validate selected option exists in question
            if selected_option:
                valid_options = [opt.label for opt in question.options]
                if selected_option not in valid_options:
                    logger.warning(
                        f"[AI_SOLVER] Q{question.number}: Selected option '{selected_option}' "
                        f"not in valid options {valid_options}"
                    )
                    selected_option = None
            
            # If no structured format found, try to extract from free text
            if not selected_option:
                logger.warning(
                    f"[AI_SOLVER] Q{question.number}: No structured ANSWER found, "
                    f"attempting free text extraction"
                )
                # Look for patterns like "The answer is A" or "Option B is correct"
                response_upper = response.upper()
                for opt in ['A', 'B', 'C', 'D', 'E']:
                    if f"ANSWER IS {opt}" in response_upper or f"OPTION {opt}" in response_upper:
                        selected_option = opt
                        explanation = response.strip()
                        break
            
            if selected_option:
                logger.info(
                    f"[AI_SOLVER] Q{question.number}: Parsed answer '{selected_option}' "
                    f"with explanation ({len(explanation)} chars)"
                )
            else:
                logger.error(
                    f"[AI_SOLVER] Q{question.number}: Failed to parse answer from response"
                )
                explanation = response.strip() if response else "No explanation provided"
            
            return selected_option, explanation
            
        except Exception as e:
            logger.error(
                f"[AI_SOLVER] Q{question.number}: Error parsing response: {e}"
            )
            return None, f"Parse error: {str(e)}"

    
    def solve_question(self, question: Question) -> SolverResult:
        """
        Solves a single question using appropriate AI model.
        Implements retry logic and timeout handling.
        Returns SolverResult with answer and metadata.
        
        Args:
            question: Question object to solve
            
        Returns:
            SolverResult with answer, explanation, and metadata
        """
        logger.info(f"[AI_SOLVER] Q{question.number}: Starting solve")
        start_time = time.time()
        
        # Select appropriate model
        model_name = self.model_selector.select_model_with_fallback(question)
        
        # Build prompt
        prompt = self._build_prompt(question)
        
        # Attempt to solve with retry logic
        last_error = None
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    # Exponential backoff
                    backoff_time = self.config.retry_backoff_base ** attempt
                    logger.info(
                        f"[AI_SOLVER] Q{question.number}: Retry {attempt}/{self.config.max_retries} "
                        f"after {backoff_time}s backoff"
                    )
                    time.sleep(backoff_time)
                
                logger.debug(
                    f"[AI_SOLVER] Q{question.number}: Calling Ollama with model '{model_name}' "
                    f"(attempt {attempt + 1}/{self.config.max_retries + 1})"
                )
                
                # Call Ollama with timeout
                response = ollama.chat(
                    model=model_name,
                    messages=[
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    options={
                        'timeout': self.config.timeout_seconds
                    }
                )
                
                # Extract response text
                response_text = ""
                if hasattr(response, 'message') and hasattr(response.message, 'content'):
                    response_text = response.message.content
                elif isinstance(response, dict) and 'message' in response:
                    response_text = response['message'].get('content', '')
                
                if not response_text:
                    raise ValueError("Empty response from AI model")
                
                logger.debug(
                    f"[AI_SOLVER] Q{question.number}: Received response "
                    f"({len(response_text)} chars)"
                )
                
                # Parse response
                selected_option, explanation = self._parse_ai_response(response_text, question)
                
                # Calculate processing time
                processing_time_ms = (time.time() - start_time) * 1000
                
                # Check if answer was successfully parsed
                if selected_option is None:
                    # Check if AI explicitly said it can't solve
                    if any(phrase in explanation.lower() for phrase in [
                        "cannot determine", "unable to solve", "insufficient information",
                        "not enough context", "cannot answer"
                    ]):
                        logger.info(
                            f"[AI_SOLVER] Q{question.number}: AI indicated unsolvable "
                            f"({processing_time_ms:.0f}ms)"
                        )
                        
                        result = SolverResult(
                            question_number=question.number,
                            selected_option=None,
                            explanation=explanation,
                            confidence=0.0,
                            processing_time_ms=processing_time_ms,
                            status="unsolvable",
                            error_message="AI could not determine answer"
                        )
                        
                        # Log solver response
                        from solver_logging_config import SolverLogger
                        solver_logger = SolverLogger()
                        solver_logger.log_solver_response(
                            question_number=question.number,
                            question_text=question.text,
                            selected_answer=None,
                            explanation=explanation,
                            confidence=0.0,
                            processing_time_ms=processing_time_ms,
                            model_used=model_name,
                            status="unsolvable",
                            error_message="AI could not determine answer"
                        )
                        
                        return result
                    else:
                        # Parse failure - will retry
                        raise ValueError(f"Failed to parse answer from response: {explanation}")
                
                # Success!
                logger.info(
                    f"[AI_SOLVER] Q{question.number}: Solved successfully "
                    f"(answer: {selected_option}, {processing_time_ms:.0f}ms)"
                )
                
                result = SolverResult(
                    question_number=question.number,
                    selected_option=selected_option,
                    explanation=explanation,
                    confidence=0.5,  # Placeholder, will be calculated by ValidationEngine
                    processing_time_ms=processing_time_ms,
                    status="solved",
                    error_message=None
                )
                
                # Log solver response
                from solver_logging_config import SolverLogger
                solver_logger = SolverLogger()
                solver_logger.log_solver_response(
                    question_number=question.number,
                    question_text=question.text,
                    selected_answer=selected_option,
                    explanation=explanation,
                    confidence=0.5,
                    processing_time_ms=processing_time_ms,
                    model_used=model_name,
                    status="solved"
                )
                
                return result
                
            except TimeoutError as e:
                logger.warning(
                    f"[AI_SOLVER] Q{question.number}: Timeout after {self.config.timeout_seconds}s "
                    f"(attempt {attempt + 1})"
                )
                last_error = e
                # Don't retry on timeout - mark as timeout immediately
                break
                
            except Exception as e:
                logger.warning(
                    f"[AI_SOLVER] Q{question.number}: Error on attempt {attempt + 1}: {e}"
                )
                last_error = e
                # Continue to retry
        
        # All retries failed
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Check if it was a timeout
        if isinstance(last_error, TimeoutError):
            logger.error(
                f"[AI_SOLVER] Q{question.number}: Timeout after {processing_time_ms:.0f}ms"
            )
            
            result = SolverResult(
                question_number=question.number,
                selected_option=None,
                explanation="",
                confidence=0.0,
                processing_time_ms=processing_time_ms,
                status="timeout",
                error_message=f"Timeout after {self.config.timeout_seconds}s"
            )
            
            # Log solver response
            from solver_logging_config import SolverLogger
            solver_logger = SolverLogger()
            solver_logger.log_solver_response(
                question_number=question.number,
                question_text=question.text,
                selected_answer=None,
                explanation="",
                confidence=0.0,
                processing_time_ms=processing_time_ms,
                model_used=model_name,
                status="timeout",
                error_message=f"Timeout after {self.config.timeout_seconds}s"
            )
            
            return result
        else:
            logger.error(
                f"[AI_SOLVER] Q{question.number}: Failed after {self.config.max_retries + 1} attempts "
                f"({processing_time_ms:.0f}ms)"
            )
            
            result = SolverResult(
                question_number=question.number,
                selected_option=None,
                explanation="",
                confidence=0.0,
                processing_time_ms=processing_time_ms,
                status="error",
                error_message=f"Solver error: {str(last_error)}"
            )
            
            # Log solver response
            from solver_logging_config import SolverLogger
            solver_logger = SolverLogger()
            solver_logger.log_solver_response(
                question_number=question.number,
                question_text=question.text,
                selected_answer=None,
                explanation="",
                confidence=0.0,
                processing_time_ms=processing_time_ms,
                model_used=model_name,
                status="error",
                error_message=str(last_error)
            )
            
            return result
