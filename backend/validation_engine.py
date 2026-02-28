"""
Validation Engine module for validating AI-generated answers.
"""
from dataclasses import dataclass, field
from typing import List, Set, Optional
import re
from solver_logging_config import get_logger
from question_parser import Question
from ai_solver import SolverResult

logger = get_logger("validation_engine")


@dataclass
class ValidationIssue:
    """Represents a validation problem."""
    question_number: int
    severity: str  # "critical", "warning", "info"
    issue_type: str  # "invalid_option", "explanation_mismatch", "uncertainty", etc.
    description: str


@dataclass
class ValidationReport:
    """Complete validation results."""
    total_questions: int
    issues: List[ValidationIssue] = field(default_factory=list)
    flagged_questions: Set[int] = field(default_factory=set)
    average_confidence: float = 0.0


class ValidationEngine:
    """Validates AI-generated answers for consistency."""
    
    def __init__(self):
        """Initialize ValidationEngine."""
        self.logger = logger
        
        # Uncertainty phrases to detect in explanations
        self.uncertainty_phrases = [
            "possibly", "might be", "unclear", "not sure", "maybe",
            "could be", "perhaps", "uncertain", "probably", "likely",
            "seems to", "appears to", "may be", "cannot determine",
            "difficult to say", "hard to tell", "not clear"
        ]
        
        logger.info("[VALIDATION_ENGINE] Initialized")
    
    def calculate_confidence(self, result: SolverResult, question: Question) -> float:
        """
        Calculates confidence score based on multiple factors.
        
        Factors considered:
        - Explanation quality (length, specificity)
        - Uncertainty indicators in text
        - Processing time (very fast or very slow = lower confidence)
        - Result status
        
        Args:
            result: SolverResult with answer and explanation
            question: Question object for context
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        logger.debug(
            f"[VALIDATION] Q{result.question_number}: Calculating confidence score"
        )
        
        # Start with base confidence
        confidence = 0.7
        
        # Check result status
        if result.status != "solved":
            logger.debug(
                f"[VALIDATION] Q{result.question_number}: Status '{result.status}' - "
                f"returning 0.0 confidence"
            )
            return 0.0
        
        # Factor 1: Explanation quality (length and specificity)
        explanation_length = len(result.explanation)
        
        if explanation_length < 20:
            # Very short explanation - lower confidence
            confidence -= 0.2
            logger.debug(
                f"[VALIDATION] Q{result.question_number}: Short explanation "
                f"({explanation_length} chars) - reducing confidence by 0.2"
            )
        elif explanation_length > 100:
            # Detailed explanation - higher confidence
            confidence += 0.1
            logger.debug(
                f"[VALIDATION] Q{result.question_number}: Detailed explanation "
                f"({explanation_length} chars) - increasing confidence by 0.1"
            )
        
        # Factor 2: Uncertainty indicators
        if self._detect_uncertainty(result.explanation):
            confidence -= 0.3
            logger.debug(
                f"[VALIDATION] Q{result.question_number}: Uncertainty detected - "
                f"reducing confidence by 0.3"
            )
        
        # Factor 3: Processing time
        # Very fast (< 1s) or very slow (> 25s) suggests issues
        processing_time_s = result.processing_time_ms / 1000.0
        
        if processing_time_s < 1.0:
            # Too fast - might be a cached or superficial response
            confidence -= 0.15
            logger.debug(
                f"[VALIDATION] Q{result.question_number}: Very fast processing "
                f"({processing_time_s:.2f}s) - reducing confidence by 0.15"
            )
        elif processing_time_s > 25.0:
            # Very slow - might indicate difficulty
            confidence -= 0.1
            logger.debug(
                f"[VALIDATION] Q{result.question_number}: Slow processing "
                f"({processing_time_s:.2f}s) - reducing confidence by 0.1"
            )
        
        # Ensure confidence is in valid range [0.0, 1.0]
        confidence = max(0.0, min(1.0, confidence))
        
        logger.info(
            f"[VALIDATION] Q{result.question_number}: Calculated confidence: {confidence:.2f}"
        )
        
        return confidence
    
    def validate_answer(self, result: SolverResult, question: Question) -> List[ValidationIssue]:
        """
        Validates a single answer for logical consistency.
        
        Checks:
        - Selected option exists in question
        - Explanation doesn't contradict answer
        - No uncertainty phrases in explanation
        
        Args:
            result: SolverResult to validate
            question: Question object with options
            
        Returns:
            List of ValidationIssue objects (empty if no issues)
        """
        logger.debug(
            f"[VALIDATION] Q{result.question_number}: Validating answer"
        )
        
        issues = []
        
        # Skip validation for non-solved questions
        if result.status != "solved":
            logger.debug(
                f"[VALIDATION] Q{result.question_number}: Skipping validation "
                f"(status: {result.status})"
            )
            return issues
        
        # Check 1: Selected option exists in question's option list
        valid_options = [opt.label for opt in question.options]
        
        if result.selected_option not in valid_options:
            issue = ValidationIssue(
                question_number=result.question_number,
                severity="critical",
                issue_type="invalid_option",
                description=f"Selected option '{result.selected_option}' is not in "
                           f"valid options {valid_options}"
            )
            issues.append(issue)
            logger.warning(
                f"[VALIDATION] Q{result.question_number}: Invalid option detected - "
                f"'{result.selected_option}' not in {valid_options}"
            )
        
        # Check 2: Detect uncertainty phrases in explanation
        if self._detect_uncertainty(result.explanation):
            issue = ValidationIssue(
                question_number=result.question_number,
                severity="warning",
                issue_type="uncertainty",
                description="Explanation contains uncertainty phrases indicating low confidence"
            )
            issues.append(issue)
            logger.info(
                f"[VALIDATION] Q{result.question_number}: Uncertainty detected in explanation"
            )
        
        # Check 3: Verify explanation discusses the selected option
        if result.selected_option and not self._check_explanation_match(
            result.selected_option,
            result.explanation,
            question.options
        ):
            issue = ValidationIssue(
                question_number=result.question_number,
                severity="warning",
                issue_type="explanation_mismatch",
                description=f"Explanation does not clearly discuss selected option "
                           f"'{result.selected_option}'"
            )
            issues.append(issue)
            logger.info(
                f"[VALIDATION] Q{result.question_number}: Explanation mismatch detected"
            )
        
        if issues:
            logger.info(
                f"[VALIDATION] Q{result.question_number}: Found {len(issues)} validation issues"
            )
        else:
            logger.debug(
                f"[VALIDATION] Q{result.question_number}: No validation issues found"
            )
        
        return issues
    
    def validate_batch(
        self,
        results: List[SolverResult],
        questions: List[Question]
    ) -> ValidationReport:
        """
        Validates all answers and detects cross-question issues.
        
        Checks:
        - Duplicate questions with different answers
        - Consistency patterns
        - Low confidence answers (< 0.6)
        
        Args:
            results: List of SolverResult objects
            questions: List of Question objects
            
        Returns:
            ValidationReport with all issues and statistics
        """
        logger.info(
            f"[VALIDATION] Starting batch validation for {len(results)} results"
        )
        
        # Create question lookup by number
        question_map = {q.number: q for q in questions}
        
        # Initialize report
        report = ValidationReport(
            total_questions=len(results),
            issues=[],
            flagged_questions=set(),
            average_confidence=0.0
        )
        
        # Track confidence scores for average calculation
        confidence_scores = []
        
        # Track question text to detect duplicates
        question_text_map = {}  # question_text -> [(question_number, answer)]
        
        # Step 1: Validate each answer individually and calculate confidence
        for result in results:
            question = question_map.get(result.question_number)
            
            if not question:
                logger.warning(
                    f"[VALIDATION] Q{result.question_number}: Question not found in map"
                )
                continue
            
            # Calculate confidence score
            confidence = self.calculate_confidence(result, question)
            confidence_scores.append(confidence)
            
            # Update result with calculated confidence
            result.confidence = confidence
            
            # Check for low confidence (< 0.6)
            if confidence < 0.6:
                issue = ValidationIssue(
                    question_number=result.question_number,
                    severity="warning",
                    issue_type="low_confidence",
                    description=f"Low confidence score: {confidence:.2f} (< 0.6) - "
                               f"requires mandatory review"
                )
                report.issues.append(issue)
                report.flagged_questions.add(result.question_number)
                
                logger.info(
                    f"[VALIDATION] Q{result.question_number}: Flagged for low confidence "
                    f"({confidence:.2f})"
                )
            
            # Validate individual answer
            answer_issues = self.validate_answer(result, question)
            report.issues.extend(answer_issues)
            
            # Flag question if it has any issues
            if answer_issues:
                report.flagged_questions.add(result.question_number)
            
            # Track question text for duplicate detection
            # Normalize text for comparison (lowercase, strip whitespace)
            normalized_text = question.text.lower().strip()
            
            if normalized_text not in question_text_map:
                question_text_map[normalized_text] = []
            
            question_text_map[normalized_text].append(
                (result.question_number, result.selected_option)
            )
        
        # Step 2: Check for duplicate questions with different answers
        for question_text, occurrences in question_text_map.items():
            if len(occurrences) > 1:
                # Multiple questions with same text
                answers = [answer for _, answer in occurrences]
                unique_answers = set(answers)
                
                if len(unique_answers) > 1:
                    # Different answers for same question - flag all occurrences
                    question_numbers = [qnum for qnum, _ in occurrences]
                    
                    for qnum in question_numbers:
                        issue = ValidationIssue(
                            question_number=qnum,
                            severity="critical",
                            issue_type="duplicate_inconsistency",
                            description=f"Duplicate question with inconsistent answers. "
                                       f"Questions {question_numbers} have same text but "
                                       f"different answers: {list(unique_answers)}"
                        )
                        report.issues.append(issue)
                        report.flagged_questions.add(qnum)
                    
                    logger.warning(
                        f"[VALIDATION] Duplicate questions detected: {question_numbers} "
                        f"with different answers: {list(unique_answers)}"
                    )
        
        # Step 3: Calculate average confidence
        if confidence_scores:
            report.average_confidence = sum(confidence_scores) / len(confidence_scores)
        
        logger.info(
            f"[VALIDATION] Batch validation complete: "
            f"{len(report.issues)} issues, "
            f"{len(report.flagged_questions)} flagged questions, "
            f"average confidence: {report.average_confidence:.2f}"
        )
        
        return report
    
    def _detect_uncertainty(self, explanation: str) -> bool:
        """
        Detects uncertainty phrases in explanation.
        
        Args:
            explanation: Explanation text to check
            
        Returns:
            True if uncertainty detected, False otherwise
        """
        explanation_lower = explanation.lower()
        
        for phrase in self.uncertainty_phrases:
            if phrase in explanation_lower:
                logger.debug(
                    f"[VALIDATION] Uncertainty phrase detected: '{phrase}'"
                )
                return True
        
        return False
    
    def _check_explanation_match(
        self,
        selected: str,
        explanation: str,
        options: List
    ) -> bool:
        """
        Verifies explanation discusses the selected option.
        
        Args:
            selected: Selected option label (A, B, C, D, E)
            explanation: Explanation text
            options: List of QuestionOption objects
            
        Returns:
            True if explanation matches selected answer, False otherwise
        """
        explanation_lower = explanation.lower()
        
        # Check if the selected option label is mentioned
        if f"option {selected.lower()}" in explanation_lower:
            return True
        
        # Check if the selected option label appears standalone
        # Look for patterns like "A)", "A.", "A:", "A is", "A -"
        option_patterns = [
            f"{selected.lower()})",
            f"{selected.lower()}.",
            f"{selected.lower()}:",
            f"{selected.lower()} is",
            f"{selected.lower()} -",
            f"answer {selected.lower()}",
            f"choice {selected.lower()}"
        ]
        
        for pattern in option_patterns:
            if pattern in explanation_lower:
                return True
        
        # Find the selected option's text
        selected_option_text = None
        for opt in options:
            if opt.label == selected:
                selected_option_text = opt.text
                break
        
        # Check if key words from the selected option appear in explanation
        if selected_option_text:
            # Extract significant words (> 3 chars) from option text
            option_words = [
                word.lower() for word in re.findall(r'\b\w+\b', selected_option_text)
                if len(word) > 3
            ]
            
            # If at least 2 significant words from the option appear in explanation,
            # consider it a match
            matches = sum(1 for word in option_words if word in explanation_lower)
            
            if matches >= min(2, len(option_words)):
                return True
        
        # No clear match found
        return False
