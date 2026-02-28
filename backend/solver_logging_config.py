"""
Comprehensive logging configuration for AI Question Solver modules.

This module provides structured logging with:
- AI solver response tracking (question, answer, confidence, processing time, model)
- User correction tracking (original and corrected answers)
- Approval action tracking (user_id, timestamp)
- Log rotation and retention policies
- Session-specific and system-wide logging
"""
import logging
import logging.handlers
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


# Log retention settings
LOG_RETENTION_DAYS = 30
MAX_LOG_SIZE_MB = 100
BACKUP_COUNT = 5


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs for machine parsing."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'session_id'):
            log_data['session_id'] = record.session_id
        if hasattr(record, 'question_number'):
            log_data['question_number'] = record.question_number
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'event_type'):
            log_data['event_type'] = record.event_type
        if hasattr(record, 'data'):
            log_data['data'] = record.data
        
        return json.dumps(log_data)


class SolverLogger:
    """
    Comprehensive logging system for AI Question Solver.
    
    Provides specialized logging methods for:
    - AI solver responses
    - User corrections
    - Approval actions
    - System events
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize solver logger.
        
        Args:
            session_id: Optional session ID for session-specific logging
        """
        self.session_id = session_id
        self.logger = logging.getLogger(f"solver.{session_id}" if session_id else "solver")
        
        # Set up handlers if not already configured
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up log handlers with rotation."""
        # Create logs directory
        log_dir = "backend/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Main solver log with rotation
        main_log_path = os.path.join(log_dir, "solver_main.log")
        main_handler = logging.handlers.RotatingFileHandler(
            main_log_path,
            maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
            backupCount=BACKUP_COUNT
        )
        main_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(main_handler)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        # Set encoding to UTF-8 for Windows compatibility
        if hasattr(console_handler.stream, 'reconfigure'):
            try:
                console_handler.stream.reconfigure(encoding='utf-8')
            except Exception:
                pass  # Ignore if reconfigure fails
        self.logger.addHandler(console_handler)
        
        # Set log level
        self.logger.setLevel(logging.INFO)
        
        # Session-specific handlers
        if self.session_id:
            self._setup_session_handlers()
    
    def _setup_session_handlers(self):
        """Set up session-specific log handlers."""
        session_log_dir = f"backend/solver_sessions/{self.session_id}/logs"
        os.makedirs(session_log_dir, exist_ok=True)
        
        # AI solver responses log (structured JSON)
        solver_responses_path = os.path.join(session_log_dir, "solver_responses.jsonl")
        solver_responses_handler = logging.FileHandler(solver_responses_path)
        solver_responses_handler.setFormatter(StructuredFormatter())
        solver_responses_handler.addFilter(lambda record: hasattr(record, 'event_type') and record.event_type == 'solver_response')
        self.logger.addHandler(solver_responses_handler)
        
        # User corrections log (structured JSON)
        corrections_path = os.path.join(session_log_dir, "user_corrections.jsonl")
        corrections_handler = logging.FileHandler(corrections_path)
        corrections_handler.setFormatter(StructuredFormatter())
        corrections_handler.addFilter(lambda record: hasattr(record, 'event_type') and record.event_type == 'user_correction')
        self.logger.addHandler(corrections_handler)
        
        # Approval actions log (structured JSON)
        approvals_path = os.path.join(session_log_dir, "approvals.jsonl")
        approvals_handler = logging.FileHandler(approvals_path)
        approvals_handler.setFormatter(StructuredFormatter())
        approvals_handler.addFilter(lambda record: hasattr(record, 'event_type') and record.event_type == 'approval_action')
        self.logger.addHandler(approvals_handler)
        
        # Extraction log
        extraction_handler = logging.FileHandler(
            os.path.join(session_log_dir, "extraction.log")
        )
        extraction_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(extraction_handler)
        
        # Validation log
        validation_handler = logging.FileHandler(
            os.path.join(session_log_dir, "validation.log")
        )
        validation_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(validation_handler)
        
        # Errors log (ERROR level only)
        errors_handler = logging.FileHandler(
            os.path.join(session_log_dir, "errors.log")
        )
        errors_handler.setLevel(logging.ERROR)
        errors_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(exc_info)s'
        ))
        self.logger.addHandler(errors_handler)
    
    def log_solver_response(
        self,
        question_number: int,
        question_text: str,
        selected_answer: Optional[str],
        explanation: str,
        confidence: float,
        processing_time_ms: float,
        model_used: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """
        Log AI solver response with all details.
        
        Args:
            question_number: Question number
            question_text: Full question text
            selected_answer: Selected answer option (A-E) or None
            explanation: AI explanation
            confidence: Confidence score (0.0-1.0)
            processing_time_ms: Processing time in milliseconds
            model_used: Name of AI model used
            status: Status (solved, unsolvable, timeout, error)
            error_message: Optional error message
        """
        log_data = {
            "question_number": question_number,
            "question_text": question_text[:200] + "..." if len(question_text) > 200 else question_text,
            "selected_answer": selected_answer,
            "explanation": explanation[:500] + "..." if len(explanation) > 500 else explanation,
            "confidence": round(confidence, 3),
            "processing_time_ms": round(processing_time_ms, 2),
            "model_used": model_used,
            "status": status,
            "error_message": error_message
        }
        
        # Create log record with extra fields
        extra = {
            'session_id': self.session_id,
            'question_number': question_number,
            'event_type': 'solver_response',
            'data': log_data
        }
        
        self.logger.info(
            f"[SOLVER_RESPONSE] Q{question_number}: {status} - "
            f"Answer: {selected_answer}, Confidence: {confidence:.2f}, "
            f"Time: {processing_time_ms:.0f}ms, Model: {model_used}",
            extra=extra
        )
    
    def log_user_correction(
        self,
        question_number: int,
        original_answer: Optional[str],
        corrected_answer: str,
        user_id: str,
        note: Optional[str] = None
    ):
        """
        Log user correction with original and corrected answers.
        
        Args:
            question_number: Question number
            original_answer: Original AI answer
            corrected_answer: User-corrected answer
            user_id: ID of user making correction
            note: Optional note explaining correction
        """
        log_data = {
            "question_number": question_number,
            "original_answer": original_answer,
            "corrected_answer": corrected_answer,
            "user_id": user_id,
            "note": note,
            "timestamp": datetime.now().isoformat()
        }
        
        extra = {
            'session_id': self.session_id,
            'question_number': question_number,
            'user_id': user_id,
            'event_type': 'user_correction',
            'data': log_data
        }
        
        self.logger.info(
            f"[USER_CORRECTION] Q{question_number}: {original_answer} -> {corrected_answer} "
            f"by user {user_id}",
            extra=extra
        )
    
    def log_approval_action(
        self,
        user_id: str,
        action: str,
        total_questions: int,
        solved_count: int,
        manual_corrections: int,
        average_confidence: float,
        flagged_questions: list
    ):
        """
        Log approval action with user_id and timestamp.
        
        Args:
            user_id: ID of user performing approval
            action: Action type (approve, reject, etc.)
            total_questions: Total number of questions
            solved_count: Number of solved questions
            manual_corrections: Number of manual corrections
            average_confidence: Average confidence score
            flagged_questions: List of flagged question numbers
        """
        log_data = {
            "user_id": user_id,
            "action": action,
            "total_questions": total_questions,
            "solved_count": solved_count,
            "manual_corrections": manual_corrections,
            "average_confidence": round(average_confidence, 3),
            "flagged_questions": flagged_questions,
            "timestamp": datetime.now().isoformat()
        }
        
        extra = {
            'session_id': self.session_id,
            'user_id': user_id,
            'event_type': 'approval_action',
            'data': log_data
        }
        
        self.logger.info(
            f"[APPROVAL_ACTION] {action} by user {user_id} - "
            f"{solved_count}/{total_questions} solved, "
            f"{manual_corrections} corrections, "
            f"avg confidence: {average_confidence:.2f}",
            extra=extra
        )
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, extra={'session_id': self.session_id, **kwargs})
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, extra={'session_id': self.session_id, **kwargs})
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, extra={'session_id': self.session_id, **kwargs})
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, extra={'session_id': self.session_id, **kwargs})


def setup_solver_logging(session_id: str = None):
    """
    Configure logging for solver modules.
    
    Args:
        session_id: Optional session ID for session-specific logs
        
    Returns:
        SolverLogger instance
    """
    return SolverLogger(session_id)


def get_logger(module_name: str):
    """
    Get logger for specific module.
    
    Args:
        module_name: Name of the module
        
    Returns:
        Logger instance
    """
    return logging.getLogger(module_name)


def cleanup_old_logs(retention_days: int = LOG_RETENTION_DAYS):
    """
    Clean up log files older than retention period.
    
    Args:
        retention_days: Number of days to retain logs
    """
    logger = logging.getLogger("solver.cleanup")
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    # Clean up main logs directory
    log_dir = "backend/logs"
    if os.path.exists(log_dir):
        for filename in os.listdir(log_dir):
            filepath = os.path.join(log_dir, filename)
            if os.path.isfile(filepath):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_mtime < cutoff_date:
                    try:
                        os.remove(filepath)
                        logger.info(f"Removed old log file: {filename}")
                    except Exception as e:
                        logger.error(f"Failed to remove log file {filename}: {e}")
    
    # Clean up session logs
    sessions_dir = "backend/solver_sessions"
    if os.path.exists(sessions_dir):
        for session_id in os.listdir(sessions_dir):
            session_dir = os.path.join(sessions_dir, session_id)
            if os.path.isdir(session_dir):
                # Check session.json modification time
                session_file = os.path.join(session_dir, "session.json")
                if os.path.exists(session_file):
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(session_file))
                    if file_mtime < cutoff_date:
                        try:
                            import shutil
                            shutil.rmtree(session_dir)
                            logger.info(f"Removed old session directory: {session_id}")
                        except Exception as e:
                            logger.error(f"Failed to remove session directory {session_id}: {e}")
