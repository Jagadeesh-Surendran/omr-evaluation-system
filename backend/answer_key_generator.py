"""
Answer Key Generator module for generating answer keys in multiple formats.
"""
from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime
import csv
import io
from solver_logging_config import get_logger

logger = get_logger("answer_key_generator")


@dataclass
class AnswerKeyMetadata:
    """Metadata for generated answer key."""
    session_id: str
    generation_time: str
    total_questions: int
    solved_count: int
    unsolvable_count: int
    manual_corrections: int
    average_confidence: float
    approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None


class AnswerKeyGenerator:
    """Generates answer keys in multiple formats."""
    
    def __init__(self):
        """Initialize the Answer Key Generator."""
        self.approved_sessions: Dict[str, AnswerKeyMetadata] = {}
    
    def generate_json(self, session) -> dict:
        """
        Generates JSON answer key compatible with OMR evaluation.
        
        Format: {0: 0, 1: 2, 2: 1, ...}  # question_idx -> option_idx (0-based)
        Includes metadata and unsolvable list.
        
        Args:
            session: SessionState object containing results
            
        Returns:
            dict: Answer key in JSON format with metadata
        """
        logger.info(f"Generating JSON answer key for session {session.session_id}")
        
        answer_key = {}
        unsolvable = []
        low_confidence = []
        
        # Convert results to 0-based indices
        for question_num, result in session.results.items():
            question_idx = question_num - 1  # Convert to 0-based
            
            # Check if there's a user correction first (overrides any status)
            if question_num in session.user_corrections:
                answer = session.user_corrections[question_num]
                # Convert answer option (A-E) to 0-based index (0-4)
                if answer and answer in ['A', 'B', 'C', 'D', 'E']:
                    option_idx = ord(answer) - ord('A')
                    answer_key[question_idx] = option_idx
                else:
                    logger.warning(f"Invalid user correction '{answer}' for question {question_num}")
                    unsolvable.append(question_num)
            elif result.status == "solved":
                answer = result.selected_option
                
                # Convert answer option (A-E) to 0-based index (0-4)
                if answer and answer in ['A', 'B', 'C', 'D', 'E']:
                    option_idx = ord(answer) - ord('A')
                    answer_key[question_idx] = option_idx
                    
                    # Track low confidence answers
                    if result.confidence < 0.6:
                        low_confidence.append(question_num)
                else:
                    logger.warning(f"Invalid answer option '{answer}' for question {question_num}")
                    unsolvable.append(question_num)
            else:
                # Mark unsolvable questions (only if not manually corrected)
                unsolvable.append(question_num)
        
        # Generate metadata
        metadata = self.get_metadata(session)
        
        result = {
            "answer_key": answer_key,
            "metadata": {
                "session_id": metadata.session_id,
                "generation_time": metadata.generation_time,
                "total_questions": metadata.total_questions,
                "solved_count": metadata.solved_count,
                "unsolvable_count": metadata.unsolvable_count,
                "manual_corrections": metadata.manual_corrections,
                "average_confidence": metadata.average_confidence,
                "approved": metadata.approved,
                "approved_by": metadata.approved_by,
                "approved_at": metadata.approved_at
            },
            "unsolvable": unsolvable,
            "low_confidence": low_confidence
        }
        
        logger.info(f"Generated JSON answer key with {len(answer_key)} answers, "
                   f"{len(unsolvable)} unsolvable, {len(low_confidence)} low confidence")
        
        return result
    
    def generate_csv(self, session) -> str:
        """
        Generates CSV export with columns:
        question_number, correct_answer, confidence, explanation, modified
        
        Args:
            session: SessionState object containing results
            
        Returns:
            str: CSV string
        """
        logger.info(f"Generating CSV export for session {session.session_id}")
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['question_number', 'correct_answer', 'confidence', 'explanation', 'modified'])
        
        # Write data rows
        for question_num in sorted(session.results.keys()):
            result = session.results[question_num]
            
            # Determine the correct answer
            if question_num in session.user_corrections:
                correct_answer = session.user_corrections[question_num]
                modified = 'Yes'
                confidence = 1.0  # User corrections have confidence 1.0
            elif result.status == "solved":
                correct_answer = result.selected_option or 'N/A'
                modified = 'No'
                confidence = result.confidence
            else:
                correct_answer = 'N/A'
                modified = 'No'
                confidence = 0.0
            
            # Get explanation
            explanation = result.explanation if result.status == "solved" else result.error_message or result.status
            
            # Clean explanation for CSV (remove newlines, limit length)
            explanation = explanation.replace('\n', ' ').replace('\r', ' ')
            if len(explanation) > 200:
                explanation = explanation[:197] + '...'
            
            writer.writerow([
                question_num,
                correct_answer,
                f"{confidence:.2f}",
                explanation,
                modified
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        logger.info(f"Generated CSV export with {len(session.results)} rows")
        
        return csv_content
    
    def generate_pdf_report(self, session, output_path: str) -> str:
        """
        Generates PDF report showing all questions with answers highlighted.
        Includes confidence scores and flags.
        
        Args:
            session: SessionState object containing results
            output_path: Path where PDF should be saved
            
        Returns:
            str: Path to generated PDF
        """
        logger.info(f"Generating PDF report for session {session.session_id}")
        
        # TODO: Implement PDF generation using reportlab or similar library
        # For now, create a placeholder text file
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("ANSWER KEY REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Session ID: {session.session_id}")
        report_lines.append(f"Generated: {datetime.now().isoformat()}")
        report_lines.append(f"Total Questions: {session.total_questions}")
        report_lines.append(f"Solved: {session.solved_count}")
        report_lines.append(f"Unsolvable: {session.unsolvable_count}")
        report_lines.append(f"Errors: {session.error_count}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Add questions and answers
        for question_num in sorted(session.results.keys()):
            result = session.results[question_num]
            question = next((q for q in session.questions if q.number == question_num), None)
            
            report_lines.append(f"Question {question_num}:")
            if question:
                report_lines.append(f"  Text: {question.text[:100]}...")
                report_lines.append(f"  Type: {question.question_type or 'unknown'}")
            
            if question_num in session.user_corrections:
                report_lines.append(f"  Answer: {session.user_corrections[question_num]} (MANUALLY CORRECTED)")
                report_lines.append(f"  Original AI Answer: {result.selected_option}")
                report_lines.append(f"  Confidence: 1.00 (user verified)")
            elif result.status == "solved":
                report_lines.append(f"  Answer: {result.selected_option}")
                report_lines.append(f"  Confidence: {result.confidence:.2f}")
                if result.confidence < 0.6:
                    report_lines.append(f"  FLAG: LOW CONFIDENCE")
            else:
                report_lines.append(f"  Status: {result.status}")
                if result.error_message:
                    report_lines.append(f"  Error: {result.error_message}")
            
            if question_num in session.user_notes:
                report_lines.append(f"  Note: {session.user_notes[question_num]}")
            
            report_lines.append("")
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"Generated PDF report at {output_path}")
        
        return output_path
    
    def get_metadata(self, session) -> AnswerKeyMetadata:
        """
        Extracts metadata from session state.
        
        Args:
            session: SessionState object
            
        Returns:
            AnswerKeyMetadata: Metadata object
        """
        # Calculate average confidence
        confidences = [
            result.confidence for result in session.results.values()
            if result.status == "solved"
        ]
        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Count manual corrections
        manual_corrections = len(session.user_corrections)
        
        # Check if approved
        approved_metadata = self.approved_sessions.get(session.session_id)
        
        metadata = AnswerKeyMetadata(
            session_id=session.session_id,
            generation_time=datetime.now().isoformat(),
            total_questions=session.total_questions,
            solved_count=session.solved_count,
            unsolvable_count=session.unsolvable_count,
            manual_corrections=manual_corrections,
            average_confidence=average_confidence,
            approved=approved_metadata.approved if approved_metadata else False,
            approved_by=approved_metadata.approved_by if approved_metadata else None,
            approved_at=approved_metadata.approved_at if approved_metadata else None
        )
        
        return metadata
    
    def approve_answer_key(self, session_id: str, user_id: str, session_state=None) -> bool:
        """
        Marks answer key as approved and immutable.
        Records approval metadata.
        
        Args:
            session_id: ID of the session to approve
            user_id: ID of the user approving the answer key
            session_state: Optional SessionState object for logging details
            
        Returns:
            bool: True if approval successful, False otherwise
        """
        logger.info(f"Approving answer key for session {session_id} by user {user_id}")
        
        # Check if already approved
        if session_id in self.approved_sessions:
            logger.warning(f"Session {session_id} is already approved")
            return False
        
        # Create approval metadata
        approval_metadata = AnswerKeyMetadata(
            session_id=session_id,
            generation_time=datetime.now().isoformat(),
            total_questions=0,  # Will be filled from session
            solved_count=0,
            unsolvable_count=0,
            manual_corrections=0,
            average_confidence=0.0,
            approved=True,
            approved_by=user_id,
            approved_at=datetime.now().isoformat()
        )
        
        self.approved_sessions[session_id] = approval_metadata
        
        # Log approval action
        from solver_logging_config import SolverLogger
        solver_logger = SolverLogger(session_id)
        
        # Extract details from session if provided
        total_questions = 0
        solved_count = 0
        manual_corrections = 0
        average_confidence = 0.0
        flagged_questions = []
        
        if session_state:
            total_questions = session_state.total_questions
            solved_count = session_state.solved_count
            manual_corrections = len(session_state.user_corrections)
            
            # Calculate average confidence
            confidences = [
                result.confidence for result in session_state.results.values()
                if result.status == "solved"
            ]
            average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Get flagged questions
            if session_state.validation_report:
                flagged_questions = list(session_state.validation_report.flagged_questions)
        
        solver_logger.log_approval_action(
            user_id=user_id,
            action="approve",
            total_questions=total_questions,
            solved_count=solved_count,
            manual_corrections=manual_corrections,
            average_confidence=average_confidence,
            flagged_questions=flagged_questions
        )
        
        logger.info(f"Answer key for session {session_id} approved successfully")
        
        return True
