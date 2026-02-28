"""
Session Manager module for managing solver session lifecycle.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import threading
import time
import uuid
import os
import json
import psutil
from solver_logging_config import get_logger
from question_parser import Question, QuestionParser
from ai_solver import AISolver, SolverResult
from validation_engine import ValidationEngine, ValidationReport

logger = get_logger("session_manager")


@dataclass
class SessionState:
    """Represents solver session state."""
    session_id: str
    status: str  # "pending", "queued", "processing", "paused", "completed", "cancelled", "error"
    pdf_path: str
    total_questions: int = 0
    processed_count: int = 0
    solved_count: int = 0
    unsolvable_count: int = 0
    error_count: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    questions: List[Question] = field(default_factory=list)
    results: Dict[int, SolverResult] = field(default_factory=dict)  # question_number -> result
    validation_report: Optional[ValidationReport] = None
    user_corrections: Dict[int, str] = field(default_factory=dict)  # question_number -> corrected_answer
    user_notes: Dict[int, str] = field(default_factory=dict)  # question_number -> note


class SessionManager:
    """Manages solver session lifecycle."""
    
    # Maximum concurrent sessions allowed
    MAX_CONCURRENT_SESSIONS = 2
    
    # Resource limits (percentage)
    CPU_CRITICAL_THRESHOLD = 90.0  # Reject new sessions if CPU > 90%
    MEMORY_CRITICAL_THRESHOLD = 90.0  # Reject new sessions if memory > 90%
    
    # Resource limits per session
    MAX_MEMORY_PER_SESSION_MB = 2048  # 2GB per session
    
    def __init__(self):
        """Initialize SessionManager."""
        self.active_sessions: Dict[str, SessionState] = {}
        self.session_locks: Dict[str, threading.Lock] = {}
        self.question_parser = QuestionParser()
        self.ai_solver = AISolver()
        self.validation_engine = ValidationEngine()
        
        # Session queue management
        self.session_queue: List[str] = []  # Queue of session IDs waiting to start
        self.queue_lock = threading.Lock()  # Lock for queue operations
        
        # Create sessions directory if it doesn't exist
        self.sessions_dir = os.path.join("backend", "solver_sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)
        
        logger.info("[SESSION_MANAGER] Initialized")
    
    def create_session(self, pdf_path: str) -> str:
        """
        Creates new solver session.
        
        Args:
            pdf_path: Path to the PDF file to process
            
        Returns:
            session_id: Unique identifier for the session
        """
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        logger.info(f"[SESSION_MANAGER] Creating session {session_id} for PDF: {pdf_path}")
        
        # Validate PDF path
        if not os.path.exists(pdf_path):
            logger.error(f"[SESSION_MANAGER] PDF file not found: {pdf_path}")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Create session state
        session = SessionState(
            session_id=session_id,
            status="pending",
            pdf_path=pdf_path
        )
        
        # Create session lock
        self.session_locks[session_id] = threading.Lock()
        
        # Store session
        self.active_sessions[session_id] = session
        
        # Create session directory
        session_dir = os.path.join(self.sessions_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        os.makedirs(os.path.join(session_dir, "logs"), exist_ok=True)
        
        logger.info(f"[SESSION_MANAGER] Session {session_id} created successfully")
        
        return session_id
    
    def start_processing(self, session_id: str) -> None:
        """
        Starts question solving process.
        Runs in background thread with progress updates.
        
        Args:
            session_id: Session identifier
        """
        logger.info(f"[SESSION_MANAGER] Starting processing for session {session_id}")
        
        # Get session
        session = self.get_session(session_id)
        if not session:
            logger.error(f"[SESSION_MANAGER] Session {session_id} not found")
            raise ValueError(f"Session {session_id} not found")
        
        # Check if already processing
        if session.status == "processing":
            logger.warning(f"[SESSION_MANAGER] Session {session_id} already processing")
            return
        
        # Check system resources
        resources_ok, error_msg = self.check_system_resources()
        if not resources_ok:
            logger.error(
                f"[SESSION_MANAGER] Cannot start session {session_id}: {error_msg}"
            )
            with self.session_locks[session_id]:
                session.status = "error"
            raise RuntimeError(error_msg)
        
        # Check concurrent session limit
        active_count = self._count_active_sessions()
        
        if active_count >= self.MAX_CONCURRENT_SESSIONS:
            # Add to queue
            logger.info(
                f"[SESSION_MANAGER] At capacity ({active_count}/{self.MAX_CONCURRENT_SESSIONS}), "
                f"queueing session {session_id}"
            )
            self._add_to_queue(session_id)
            return
        
        # Start background thread
        thread = threading.Thread(
            target=self._process_session,
            args=(session_id,),
            daemon=True
        )
        thread.start()
        
        logger.info(f"[SESSION_MANAGER] Background processing started for session {session_id}")
    
    def _process_session(self, session_id: str) -> None:
        """
        Background processing method for solving questions.
        
        Args:
            session_id: Session identifier
        """
        logger.info(f"[SESSION_MANAGER] Processing session {session_id}")
        
        try:
            # Get session with lock
            with self.session_locks[session_id]:
                session = self.active_sessions[session_id]
                session.status = "processing"
                session.start_time = time.time()
            
            # Step 1: Extract questions if not already done
            if not session.questions:
                logger.info(f"[SESSION_MANAGER] Extracting questions from PDF")
                questions = self.question_parser.extract_questions(session.pdf_path)
                
                with self.session_locks[session_id]:
                    session.questions = questions
                    session.total_questions = len(questions)
                
                logger.info(f"[SESSION_MANAGER] Extracted {len(questions)} questions")
            
            # Step 2: Process each question
            last_progress_time = time.time()
            last_checkpoint_count = 0
            
            for i, question in enumerate(session.questions):
                # Check for pause/cancel signals
                with self.session_locks[session_id]:
                    if session.status == "paused":
                        logger.info(f"[SESSION_MANAGER] Session {session_id} paused at question {i+1}")
                        self.save_session(session_id)
                        return
                    elif session.status == "cancelled":
                        logger.info(f"[SESSION_MANAGER] Session {session_id} cancelled at question {i+1}")
                        return
                
                # Skip if already processed
                if question.number in session.results:
                    logger.debug(f"[SESSION_MANAGER] Question {question.number} already processed, skipping")
                    continue
                
                # Solve question
                logger.info(f"[SESSION_MANAGER] Solving question {question.number} ({i+1}/{session.total_questions})")
                result = self.ai_solver.solve_question(question)
                
                # Store result
                with self.session_locks[session_id]:
                    session.results[question.number] = result
                    session.processed_count += 1
                    
                    # Update counts based on status
                    if result.status == "solved":
                        session.solved_count += 1
                    elif result.status == "unsolvable":
                        session.unsolvable_count += 1
                    elif result.status in ["error", "timeout"]:
                        session.error_count += 1
                
                # Emit progress update every 5 seconds
                current_time = time.time()
                if current_time - last_progress_time >= 5.0:
                    self._emit_progress(session_id)
                    last_progress_time = current_time
                
                # Checkpoint every 10 questions
                if session.processed_count - last_checkpoint_count >= 10:
                    logger.info(f"[SESSION_MANAGER] Checkpoint at {session.processed_count} questions")
                    self.save_session(session_id)
                    last_checkpoint_count = session.processed_count
            
            # Step 3: Run validation
            logger.info(f"[SESSION_MANAGER] Running validation for session {session_id}")
            validation_report = self.validation_engine.validate_batch(
                list(session.results.values()),
                session.questions
            )
            
            with self.session_locks[session_id]:
                session.validation_report = validation_report
                session.status = "completed"
                session.end_time = time.time()
            
            # Final save
            self.save_session(session_id)
            
            # Emit final progress
            self._emit_progress(session_id)
            
            # Start next queued session if any
            self._start_next_queued_session()
            
            logger.info(
                f"[SESSION_MANAGER] Session {session_id} completed: "
                f"{session.solved_count} solved, {session.unsolvable_count} unsolvable, "
                f"{session.error_count} errors"
            )
            
        except Exception as e:
            logger.error(f"[SESSION_MANAGER] Error processing session {session_id}: {e}")
            
            with self.session_locks[session_id]:
                session.status = "error"
                session.end_time = time.time()
            
            self.save_session(session_id)
            raise
    
    def pause_session(self, session_id: str) -> bool:
        """
        Pauses active session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successfully paused, False otherwise
        """
        logger.info(f"[SESSION_MANAGER] Pausing session {session_id}")
        
        # Get session
        session = self.get_session(session_id)
        if not session:
            logger.error(f"[SESSION_MANAGER] Session {session_id} not found")
            return False
        
        # Check if session is processing
        if session.status != "processing":
            logger.warning(
                f"[SESSION_MANAGER] Cannot pause session {session_id} "
                f"with status '{session.status}'"
            )
            return False
        
        # Set pause flag
        with self.session_locks[session_id]:
            session.status = "paused"
        
        logger.info(f"[SESSION_MANAGER] Session {session_id} paused")
        return True
    
    def resume_session(self, session_id: str) -> bool:
        """
        Resumes paused session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successfully resumed, False otherwise
        """
        logger.info(f"[SESSION_MANAGER] Resuming session {session_id}")
        
        # Get session
        session = self.get_session(session_id)
        if not session:
            logger.error(f"[SESSION_MANAGER] Session {session_id} not found")
            return False
        
        # Check if session is paused
        if session.status != "paused":
            logger.warning(
                f"[SESSION_MANAGER] Cannot resume session {session_id} "
                f"with status '{session.status}'"
            )
            return False
        
        # Resume processing
        self.start_processing(session_id)
        
        logger.info(f"[SESSION_MANAGER] Session {session_id} resumed")
        return True
    
    def cancel_session(self, session_id: str) -> bool:
        """
        Cancels session and discards results.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successfully cancelled, False otherwise
        """
        logger.info(f"[SESSION_MANAGER] Cancelling session {session_id}")
        
        # Get session
        session = self.get_session(session_id)
        if not session:
            logger.error(f"[SESSION_MANAGER] Session {session_id} not found")
            return False
        
        # Check if session can be cancelled
        if session.status in ["completed", "cancelled"]:
            logger.warning(
                f"[SESSION_MANAGER] Cannot cancel session {session_id} "
                f"with status '{session.status}'"
            )
            return False
        
        # Set cancel flag
        with self.session_locks[session_id]:
            session.status = "cancelled"
            session.end_time = time.time()
        
        # Remove from active sessions (discard results)
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # Remove session lock
        if session_id in self.session_locks:
            del self.session_locks[session_id]
        
        # Remove from queue if present
        self._remove_from_queue(session_id)
        
        # Start next queued session if any
        self._start_next_queued_session()
        
        # Clean up session directory (optional - could keep for debugging)
        # For now, we'll keep the directory but mark it as cancelled
        
        logger.info(f"[SESSION_MANAGER] Session {session_id} cancelled")
        return True
    
    def update_answer(self, session_id: str, question_num: int, new_answer: str, user_id: str = "unknown") -> bool:
        """
        Updates answer for specific question (manual correction).
        Marks as user-verified with confidence 1.0.
        
        Args:
            session_id: Session identifier
            question_num: Question number to update
            new_answer: New answer option (A, B, C, D, or E)
            user_id: ID of user making the correction
            
        Returns:
            True if successfully updated, False otherwise
        """
        logger.info(
            f"[SESSION_MANAGER] Updating answer for session {session_id}, "
            f"question {question_num} to '{new_answer}' by user {user_id}"
        )
        
        # Validate answer option
        if new_answer not in ['A', 'B', 'C', 'D', 'E']:
            logger.error(f"[SESSION_MANAGER] Invalid answer option: '{new_answer}'")
            return False
        
        # Get session
        session = self.get_session(session_id)
        if not session:
            logger.error(f"[SESSION_MANAGER] Session {session_id} not found")
            return False
        
        # Check if question exists in results
        if question_num not in session.results:
            logger.error(
                f"[SESSION_MANAGER] Question {question_num} not found in session results"
            )
            return False
        
        # Update answer with lock
        with self.session_locks[session_id]:
            result = session.results[question_num]
            original_answer = result.selected_option
            
            # Store original answer in corrections if not already there
            if question_num not in session.user_corrections:
                session.user_corrections[question_num] = new_answer
            
            # Update result
            result.selected_option = new_answer
            result.confidence = 1.0
            result.status = "solved"
            
            # Add note about manual verification
            if result.explanation:
                result.explanation = f"[MANUALLY VERIFIED] {result.explanation}"
            else:
                result.explanation = "[MANUALLY VERIFIED]"
        
        # Log user correction
        from solver_logging_config import SolverLogger
        solver_logger = SolverLogger(session_id)
        solver_logger.log_user_correction(
            question_number=question_num,
            original_answer=original_answer,
            corrected_answer=new_answer,
            user_id=user_id,
            note=None
        )
        
        # Save session
        self.save_session(session_id)
        
        logger.info(
            f"[SESSION_MANAGER] Answer updated for question {question_num} "
            f"in session {session_id}"
        )
        return True
    
    def add_note(self, session_id: str, question_num: int, note: str) -> bool:
        """
        Adds user note to specific question.
        
        Args:
            session_id: Session identifier
            question_num: Question number
            note: Note text
            
        Returns:
            True if successfully added, False otherwise
        """
        logger.info(
            f"[SESSION_MANAGER] Adding note for session {session_id}, "
            f"question {question_num}"
        )
        
        # Get session
        session = self.get_session(session_id)
        if not session:
            logger.error(f"[SESSION_MANAGER] Session {session_id} not found")
            return False
        
        # Check if question exists
        question_exists = any(q.number == question_num for q in session.questions)
        if not question_exists:
            logger.error(
                f"[SESSION_MANAGER] Question {question_num} not found in session"
            )
            return False
        
        # Add note with lock
        with self.session_locks[session_id]:
            session.user_notes[question_num] = note
        
        # Save session
        self.save_session(session_id)
        
        logger.info(
            f"[SESSION_MANAGER] Note added for question {question_num} "
            f"in session {session_id}"
        )
        return True
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """
        Retrieves session state.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionState object or None if not found
        """
        # Check active sessions first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Try to load from disk
        return self.load_session(session_id)
    
    def save_session(self, session_id: str) -> None:
        """
        Persists session state to disk.
        
        Args:
            session_id: Session identifier
        """
        logger.debug(f"[SESSION_MANAGER] Saving session {session_id}")
        
        # Get session
        session = self.active_sessions.get(session_id)
        if not session:
            logger.error(f"[SESSION_MANAGER] Session {session_id} not found in active sessions")
            return
        
        # Create session directory
        session_dir = os.path.join(self.sessions_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        try:
            # Save session state (without questions and results - saved separately)
            session_data = {
                "session_id": session.session_id,
                "status": session.status,
                "pdf_path": session.pdf_path,
                "total_questions": session.total_questions,
                "processed_count": session.processed_count,
                "solved_count": session.solved_count,
                "unsolvable_count": session.unsolvable_count,
                "error_count": session.error_count,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "user_corrections": session.user_corrections,
                "user_notes": session.user_notes
            }
            
            session_file = os.path.join(session_dir, "session.json")
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Save questions
            if session.questions:
                questions_data = []
                for q in session.questions:
                    q_data = {
                        "number": q.number,
                        "text": q.text,
                        "options": [
                            {
                                "label": opt.label,
                                "text": opt.text,
                                "has_image": opt.has_image
                            }
                            for opt in q.options
                        ],
                        "page_number": q.page_number,
                        "has_image": q.has_image,
                        "question_type": q.question_type
                    }
                    questions_data.append(q_data)
                
                questions_file = os.path.join(session_dir, "questions.json")
                with open(questions_file, 'w') as f:
                    json.dump(questions_data, f, indent=2)
            
            # Save results
            if session.results:
                results_data = {}
                for qnum, result in session.results.items():
                    results_data[str(qnum)] = {
                        "question_number": result.question_number,
                        "selected_option": result.selected_option,
                        "explanation": result.explanation,
                        "confidence": result.confidence,
                        "processing_time_ms": result.processing_time_ms,
                        "status": result.status,
                        "error_message": result.error_message
                    }
                
                results_file = os.path.join(session_dir, "results.json")
                with open(results_file, 'w') as f:
                    json.dump(results_data, f, indent=2)
            
            # Save validation report
            if session.validation_report:
                validation_data = {
                    "total_questions": session.validation_report.total_questions,
                    "issues": [
                        {
                            "question_number": issue.question_number,
                            "severity": issue.severity,
                            "issue_type": issue.issue_type,
                            "description": issue.description
                        }
                        for issue in session.validation_report.issues
                    ],
                    "flagged_questions": list(session.validation_report.flagged_questions),
                    "average_confidence": session.validation_report.average_confidence
                }
                
                validation_file = os.path.join(session_dir, "validation.json")
                with open(validation_file, 'w') as f:
                    json.dump(validation_data, f, indent=2)
            
            logger.debug(f"[SESSION_MANAGER] Session {session_id} saved successfully")
            
        except Exception as e:
            logger.error(f"[SESSION_MANAGER] Error saving session {session_id}: {e}")
            raise
    
    def load_session(self, session_id: str) -> Optional[SessionState]:
        """
        Loads session state from disk.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionState object or None if not found
        """
        logger.debug(f"[SESSION_MANAGER] Loading session {session_id}")
        
        session_dir = os.path.join(self.sessions_dir, session_id)
        session_file = os.path.join(session_dir, "session.json")
        
        # Check if session file exists
        if not os.path.exists(session_file):
            logger.warning(f"[SESSION_MANAGER] Session file not found: {session_file}")
            return None
        
        try:
            # Load session state
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Create session object
            session = SessionState(
                session_id=session_data["session_id"],
                status=session_data["status"],
                pdf_path=session_data["pdf_path"],
                total_questions=session_data["total_questions"],
                processed_count=session_data["processed_count"],
                solved_count=session_data["solved_count"],
                unsolvable_count=session_data["unsolvable_count"],
                error_count=session_data["error_count"],
                start_time=session_data.get("start_time"),
                end_time=session_data.get("end_time"),
                user_corrections=session_data.get("user_corrections", {}),
                user_notes=session_data.get("user_notes", {})
            )
            
            # Load questions
            questions_file = os.path.join(session_dir, "questions.json")
            if os.path.exists(questions_file):
                with open(questions_file, 'r') as f:
                    questions_data = json.load(f)
                
                from question_parser import QuestionOption
                questions = []
                for q_data in questions_data:
                    options = [
                        QuestionOption(
                            label=opt["label"],
                            text=opt["text"],
                            has_image=opt.get("has_image", False)
                        )
                        for opt in q_data["options"]
                    ]
                    
                    question = Question(
                        number=q_data["number"],
                        text=q_data["text"],
                        options=options,
                        page_number=q_data["page_number"],
                        has_image=q_data.get("has_image", False),
                        question_type=q_data.get("question_type")
                    )
                    questions.append(question)
                
                session.questions = questions
            
            # Load results
            results_file = os.path.join(session_dir, "results.json")
            if os.path.exists(results_file):
                with open(results_file, 'r') as f:
                    results_data = json.load(f)
                
                results = {}
                for qnum_str, result_data in results_data.items():
                    result = SolverResult(
                        question_number=result_data["question_number"],
                        selected_option=result_data.get("selected_option"),
                        explanation=result_data["explanation"],
                        confidence=result_data["confidence"],
                        processing_time_ms=result_data["processing_time_ms"],
                        status=result_data["status"],
                        error_message=result_data.get("error_message")
                    )
                    results[int(qnum_str)] = result
                
                session.results = results
            
            # Load validation report
            validation_file = os.path.join(session_dir, "validation.json")
            if os.path.exists(validation_file):
                with open(validation_file, 'r') as f:
                    validation_data = json.load(f)
                
                from validation_engine import ValidationIssue
                issues = [
                    ValidationIssue(
                        question_number=issue["question_number"],
                        severity=issue["severity"],
                        issue_type=issue["issue_type"],
                        description=issue["description"]
                    )
                    for issue in validation_data["issues"]
                ]
                
                validation_report = ValidationReport(
                    total_questions=validation_data["total_questions"],
                    issues=issues,
                    flagged_questions=set(validation_data["flagged_questions"]),
                    average_confidence=validation_data["average_confidence"]
                )
                
                session.validation_report = validation_report
            
            # Store in active sessions
            self.active_sessions[session_id] = session
            
            # Create session lock if not exists
            if session_id not in self.session_locks:
                self.session_locks[session_id] = threading.Lock()
            
            logger.debug(f"[SESSION_MANAGER] Session {session_id} loaded successfully")
            return session
            
        except Exception as e:
            logger.error(f"[SESSION_MANAGER] Error loading session {session_id}: {e}")
            return None
    
    def _emit_progress(self, session_id: str) -> None:
        """
        Emits progress update via WebSocket.
        
        Args:
            session_id: Session identifier
        """
        # Get session
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"[SESSION_MANAGER] Cannot emit progress for unknown session {session_id}")
            return
        
        # Calculate progress metrics
        elapsed_time = 0
        estimated_remaining = 0
        questions_per_minute = 0.0
        
        if session.start_time:
            elapsed_time = time.time() - session.start_time
            
            if session.processed_count > 0 and elapsed_time > 0:
                # Calculate questions per minute
                questions_per_minute = (session.processed_count / elapsed_time) * 60
                
                # Estimate remaining time
                remaining_questions = session.total_questions - session.processed_count
                if questions_per_minute > 0:
                    estimated_remaining = (remaining_questions / questions_per_minute) * 60
        
        # Calculate average confidence
        average_confidence = 0.0
        if session.results:
            confidence_scores = [
                r.confidence for r in session.results.values()
                if r.status == "solved"
            ]
            if confidence_scores:
                average_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # Build progress message
        progress_message = {
            "session_id": session_id,
            "status": session.status,
            "current_question": session.processed_count,
            "total_questions": session.total_questions,
            "processed_count": session.processed_count,
            "solved_count": session.solved_count,
            "unsolvable_count": session.unsolvable_count,
            "error_count": session.error_count,
            "elapsed_time_seconds": int(elapsed_time),
            "estimated_remaining_seconds": int(estimated_remaining),
            "average_confidence": round(average_confidence, 2),
            "questions_per_minute": round(questions_per_minute, 2)
        }
        
        # Emit via WebSocket using Flask-SocketIO
        try:
            from app import socketio
            socketio.emit('progress_update', progress_message)
            logger.debug(
                f"[SESSION_MANAGER] Emitted progress for {session_id}: "
                f"{session.processed_count}/{session.total_questions} questions"
            )
        except Exception as e:
            logger.warning(f"[SESSION_MANAGER] Failed to emit progress via WebSocket: {e}")
            # Fall back to logging
            logger.info(
                f"[SESSION_MANAGER] Progress for {session_id}: "
                f"{session.processed_count}/{session.total_questions} questions, "
                f"{questions_per_minute:.1f} q/min, "
                f"avg confidence: {average_confidence:.2f}"
            )
    
    def _count_active_sessions(self) -> int:
        """
        Counts the number of currently active (processing) sessions.
        
        Returns:
            Number of active sessions
        """
        count = 0
        for session in self.active_sessions.values():
            if session.status == "processing":
                count += 1
        return count
    
    def _add_to_queue(self, session_id: str) -> None:
        """
        Adds a session to the queue.
        
        Args:
            session_id: Session identifier
        """
        with self.queue_lock:
            if session_id not in self.session_queue:
                self.session_queue.append(session_id)
                logger.info(
                    f"[SESSION_MANAGER] Session {session_id} added to queue "
                    f"at position {len(self.session_queue)}"
                )
                
                # Update session status
                session = self.get_session(session_id)
                if session:
                    with self.session_locks[session_id]:
                        session.status = "queued"
                
                # Notify user of queue position
                self._emit_queue_notification(session_id)
    
    def _remove_from_queue(self, session_id: str) -> None:
        """
        Removes a session from the queue.
        
        Args:
            session_id: Session identifier
        """
        with self.queue_lock:
            if session_id in self.session_queue:
                self.session_queue.remove(session_id)
                logger.info(f"[SESSION_MANAGER] Session {session_id} removed from queue")
    
    def _start_next_queued_session(self) -> None:
        """
        Starts the next session from the queue if capacity is available.
        """
        with self.queue_lock:
            # Check if we have capacity
            active_count = self._count_active_sessions()
            
            if active_count >= self.MAX_CONCURRENT_SESSIONS:
                logger.debug(
                    f"[SESSION_MANAGER] No capacity to start queued session "
                    f"({active_count}/{self.MAX_CONCURRENT_SESSIONS})"
                )
                return
            
            # Get next session from queue
            if not self.session_queue:
                logger.debug("[SESSION_MANAGER] No sessions in queue")
                return
            
            next_session_id = self.session_queue.pop(0)
            logger.info(
                f"[SESSION_MANAGER] Starting queued session {next_session_id} "
                f"({len(self.session_queue)} remaining in queue)"
            )
        
        # Start the session (outside the lock to avoid deadlock)
        try:
            session = self.get_session(next_session_id)
            if session and session.status == "queued":
                # Update status to pending before starting
                with self.session_locks[next_session_id]:
                    session.status = "pending"
                
                # Start processing (this will check capacity again, but should pass now)
                thread = threading.Thread(
                    target=self._process_session,
                    args=(next_session_id,),
                    daemon=True
                )
                thread.start()
                
                logger.info(f"[SESSION_MANAGER] Queued session {next_session_id} started")
        except Exception as e:
            logger.error(f"[SESSION_MANAGER] Error starting queued session {next_session_id}: {e}")
    
    def get_queue_position(self, session_id: str) -> Optional[int]:
        """
        Gets the queue position for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Queue position (1-based) or None if not in queue
        """
        with self.queue_lock:
            try:
                position = self.session_queue.index(session_id) + 1  # 1-based position
                return position
            except ValueError:
                return None
    
    def _emit_queue_notification(self, session_id: str) -> None:
        """
        Emits queue position notification via WebSocket.
        
        Args:
            session_id: Session identifier
        """
        position = self.get_queue_position(session_id)
        
        if position is None:
            return
        
        # Build queue notification message
        queue_message = {
            "session_id": session_id,
            "status": "queued",
            "queue_position": position,
            "total_in_queue": len(self.session_queue),
            "message": f"Session queued at position {position}. Will start when capacity is available."
        }
        
        # Emit via WebSocket
        try:
            from app import socketio
            socketio.emit('queue_notification', queue_message)
            logger.debug(
                f"[SESSION_MANAGER] Emitted queue notification for {session_id}: "
                f"position {position}"
            )
        except Exception as e:
            logger.warning(f"[SESSION_MANAGER] Failed to emit queue notification via WebSocket: {e}")
            logger.info(
                f"[SESSION_MANAGER] Queue notification for {session_id}: "
                f"position {position}/{len(self.session_queue)}"
            )
    
    def check_system_resources(self) -> tuple[bool, Optional[str]]:
        """
        Checks if system resources are available for new session.
        
        Returns:
            Tuple of (resources_available, error_message)
            - resources_available: True if resources are sufficient
            - error_message: Error message if resources are insufficient, None otherwise
        """
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.CPU_CRITICAL_THRESHOLD:
                error_msg = (
                    f"System CPU usage is critically high ({cpu_percent:.1f}%). "
                    f"Cannot start new session."
                )
                logger.warning(f"[SESSION_MANAGER] {error_msg}")
                return False, error_msg
            
            # Check memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            if memory_percent > self.MEMORY_CRITICAL_THRESHOLD:
                error_msg = (
                    f"System memory usage is critically high ({memory_percent:.1f}%). "
                    f"Cannot start new session."
                )
                logger.warning(f"[SESSION_MANAGER] {error_msg}")
                return False, error_msg
            
            # Check available memory
            available_mb = memory.available / (1024 * 1024)
            if available_mb < self.MAX_MEMORY_PER_SESSION_MB:
                error_msg = (
                    f"Insufficient available memory ({available_mb:.0f}MB available, "
                    f"{self.MAX_MEMORY_PER_SESSION_MB}MB required per session). "
                    f"Cannot start new session."
                )
                logger.warning(f"[SESSION_MANAGER] {error_msg}")
                return False, error_msg
            
            logger.debug(
                f"[SESSION_MANAGER] System resources OK: "
                f"CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%, "
                f"Available {available_mb:.0f}MB"
            )
            return True, None
            
        except Exception as e:
            logger.error(f"[SESSION_MANAGER] Error checking system resources: {e}")
            # If we can't check resources, allow the session (fail open)
            return True, None
    
    def get_resource_stats(self) -> dict:
        """
        Gets current system resource statistics.
        
        Returns:
            Dictionary with CPU, memory, and disk usage statistics
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "memory_available_mb": round(memory.available / (1024 * 1024), 0),
                "memory_total_mb": round(memory.total / (1024 * 1024), 0),
                "disk_percent": round(disk.percent, 1),
                "disk_free_gb": round(disk.free / (1024 * 1024 * 1024), 1),
                "active_sessions": self._count_active_sessions(),
                "queued_sessions": len(self.session_queue)
            }
        except Exception as e:
            logger.error(f"[SESSION_MANAGER] Error getting resource stats: {e}")
            return {
                "error": str(e),
                "active_sessions": self._count_active_sessions(),
                "queued_sessions": len(self.session_queue)
            }
    
    def calculate_session_statistics(self, session_id: str) -> Optional[dict]:
        """
        Calculates comprehensive statistics for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session statistics or None if session not found
        """
        logger.debug(f"[SESSION_MANAGER] Calculating statistics for session {session_id}")
        
        # Get session
        session = self.get_session(session_id)
        if not session:
            logger.error(f"[SESSION_MANAGER] Session {session_id} not found")
            return None
        
        # Calculate average confidence
        avg_confidence = self._calculate_average_confidence(session)
        
        # Calculate manual correction percentage
        correction_percentage = self._calculate_correction_percentage(session)
        
        # Calculate question type distribution
        type_distribution = self._calculate_question_type_distribution(session)
        
        # Calculate processing time statistics
        time_stats = self._calculate_processing_time_statistics(session)
        
        # Build statistics dictionary
        statistics = {
            "session_id": session_id,
            "status": session.status,
            "total_questions": session.total_questions,
            "processed_count": session.processed_count,
            "solved_count": session.solved_count,
            "unsolvable_count": session.unsolvable_count,
            "error_count": session.error_count,
            "average_confidence": avg_confidence,
            "manual_correction_percentage": correction_percentage,
            "manual_corrections_count": len(session.user_corrections),
            "question_type_distribution": type_distribution,
            "processing_time_statistics": time_stats
        }
        
        logger.debug(
            f"[SESSION_MANAGER] Statistics calculated for session {session_id}: "
            f"avg_confidence={avg_confidence:.2f}, "
            f"correction_pct={correction_percentage:.1f}%"
        )
        
        return statistics
    
    def _calculate_average_confidence(self, session: SessionState) -> float:
        """
        Calculates average confidence across all solved questions in a session.
        
        Args:
            session: SessionState object
            
        Returns:
            Average confidence score (0.0 to 1.0)
        """
        # Get all solved questions
        solved_results = [
            result for result in session.results.values()
            if result.status == "solved"
        ]
        
        if not solved_results:
            return 0.0
        
        # Calculate average
        total_confidence = sum(result.confidence for result in solved_results)
        avg_confidence = total_confidence / len(solved_results)
        
        return round(avg_confidence, 4)
    
    def _calculate_correction_percentage(self, session: SessionState) -> float:
        """
        Calculates percentage of questions requiring manual correction.
        
        Args:
            session: SessionState object
            
        Returns:
            Percentage of questions with manual corrections (0.0 to 100.0)
        """
        if session.total_questions == 0:
            return 0.0
        
        # Count questions with user corrections
        correction_count = len(session.user_corrections)
        
        # Calculate percentage
        percentage = (correction_count / session.total_questions) * 100
        
        return round(percentage, 2)
    
    def _calculate_question_type_distribution(self, session: SessionState) -> dict:
        """
        Tracks question type distribution (math, logical, factual, visual).
        
        Args:
            session: SessionState object
            
        Returns:
            Dictionary with counts and percentages for each question type
        """
        # Initialize counters
        type_counts = {
            "math": 0,
            "logical": 0,
            "factual": 0,
            "visual": 0,
            "unknown": 0
        }
        
        # Count question types
        for question in session.questions:
            question_type = question.question_type or "unknown"
            if question_type in type_counts:
                type_counts[question_type] += 1
            else:
                type_counts["unknown"] += 1
        
        # Calculate percentages
        total = session.total_questions if session.total_questions > 0 else 1
        type_distribution = {}
        
        for qtype, count in type_counts.items():
            percentage = (count / total) * 100
            type_distribution[qtype] = {
                "count": count,
                "percentage": round(percentage, 2)
            }
        
        return type_distribution
    
    def _calculate_processing_time_statistics(self, session: SessionState) -> dict:
        """
        Calculates processing time statistics.
        
        Args:
            session: SessionState object
            
        Returns:
            Dictionary with total time, average time per question, and questions per minute
        """
        # Calculate total session time
        total_time_seconds = 0.0
        if session.start_time:
            end_time = session.end_time if session.end_time else time.time()
            total_time_seconds = end_time - session.start_time
        
        # Calculate average time per question
        avg_time_per_question = 0.0
        if session.processed_count > 0 and total_time_seconds > 0:
            avg_time_per_question = total_time_seconds / session.processed_count
        
        # Calculate questions per minute
        questions_per_minute = 0.0
        if total_time_seconds > 0 and session.processed_count > 0:
            questions_per_minute = (session.processed_count / total_time_seconds) * 60
        
        # Calculate average processing time from individual results
        avg_processing_time_ms = 0.0
        if session.results:
            processing_times = [
                result.processing_time_ms for result in session.results.values()
                if result.processing_time_ms > 0
            ]
            if processing_times:
                avg_processing_time_ms = sum(processing_times) / len(processing_times)
        
        # Calculate min and max processing times
        min_processing_time_ms = 0.0
        max_processing_time_ms = 0.0
        if session.results:
            processing_times = [
                result.processing_time_ms for result in session.results.values()
                if result.processing_time_ms > 0
            ]
            if processing_times:
                min_processing_time_ms = min(processing_times)
                max_processing_time_ms = max(processing_times)
        
        return {
            "total_time_seconds": round(total_time_seconds, 2),
            "average_time_per_question_seconds": round(avg_time_per_question, 2),
            "questions_per_minute": round(questions_per_minute, 2),
            "average_processing_time_ms": round(avg_processing_time_ms, 2),
            "min_processing_time_ms": round(min_processing_time_ms, 2),
            "max_processing_time_ms": round(max_processing_time_ms, 2)
        }


    def calculate_session_statistics(self, session_id: str) -> Optional[dict]:
        """
        Calculates comprehensive statistics for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session statistics or None if session not found
        """
        logger.debug(f"[SESSION_MANAGER] Calculating statistics for session {session_id}")

        # Get session
        session = self.get_session(session_id)
        if not session:
            logger.error(f"[SESSION_MANAGER] Session {session_id} not found")
            return None

        # Calculate average confidence
        avg_confidence = self._calculate_average_confidence(session)

        # Calculate manual correction percentage
        correction_percentage = self._calculate_correction_percentage(session)

        # Calculate question type distribution
        type_distribution = self._calculate_question_type_distribution(session)

        # Calculate processing time statistics
        time_stats = self._calculate_processing_time_statistics(session)

        # Build statistics dictionary
        statistics = {
            "session_id": session_id,
            "status": session.status,
            "total_questions": session.total_questions,
            "processed_count": session.processed_count,
            "solved_count": session.solved_count,
            "unsolvable_count": session.unsolvable_count,
            "error_count": session.error_count,
            "average_confidence": avg_confidence,
            "manual_correction_percentage": correction_percentage,
            "manual_corrections_count": len(session.user_corrections),
            "question_type_distribution": type_distribution,
            "processing_time_statistics": time_stats
        }

        logger.debug(
            f"[SESSION_MANAGER] Statistics calculated for session {session_id}: "
            f"avg_confidence={avg_confidence:.2f}, "
            f"correction_pct={correction_percentage:.1f}%"
        )

        return statistics

    def _calculate_average_confidence(self, session: SessionState) -> float:
        """
        Calculates average confidence across all solved questions in a session.

        Args:
            session: SessionState object

        Returns:
            Average confidence score (0.0 to 1.0)
        """
        # Get all solved questions
        solved_results = [
            result for result in session.results.values()
            if result.status == "solved"
        ]

        if not solved_results:
            return 0.0

        # Calculate average
        total_confidence = sum(result.confidence for result in solved_results)
        avg_confidence = total_confidence / len(solved_results)

        return round(avg_confidence, 4)

    def _calculate_correction_percentage(self, session: SessionState) -> float:
        """
        Calculates percentage of questions requiring manual correction.

        Args:
            session: SessionState object

        Returns:
            Percentage of questions with manual corrections (0.0 to 100.0)
        """
        if session.total_questions == 0:
            return 0.0

        # Count questions with user corrections
        correction_count = len(session.user_corrections)

        # Calculate percentage
        percentage = (correction_count / session.total_questions) * 100

        return round(percentage, 2)

    def _calculate_question_type_distribution(self, session: SessionState) -> dict:
        """
        Tracks question type distribution (math, logical, factual, visual).

        Args:
            session: SessionState object

        Returns:
            Dictionary with counts and percentages for each question type
        """
        # Initialize counters
        type_counts = {
            "math": 0,
            "logical": 0,
            "factual": 0,
            "visual": 0,
            "unknown": 0
        }

        # Count question types
        for question in session.questions:
            question_type = question.question_type or "unknown"
            if question_type in type_counts:
                type_counts[question_type] += 1
            else:
                type_counts["unknown"] += 1

        # Calculate percentages
        total = session.total_questions if session.total_questions > 0 else 1
        type_distribution = {}

        for qtype, count in type_counts.items():
            percentage = (count / total) * 100
            type_distribution[qtype] = {
                "count": count,
                "percentage": round(percentage, 2)
            }

        return type_distribution

    def _calculate_processing_time_statistics(self, session: SessionState) -> dict:
        """
        Calculates processing time statistics.

        Args:
            session: SessionState object

        Returns:
            Dictionary with total time, average time per question, and questions per minute
        """
        # Calculate total session time
        total_time_seconds = 0.0
        if session.start_time:
            end_time = session.end_time if session.end_time else time.time()
            total_time_seconds = end_time - session.start_time

        # Calculate average time per question
        avg_time_per_question = 0.0
        if session.processed_count > 0 and total_time_seconds > 0:
            avg_time_per_question = total_time_seconds / session.processed_count

        # Calculate questions per minute
        questions_per_minute = 0.0
        if total_time_seconds > 0 and session.processed_count > 0:
            questions_per_minute = (session.processed_count / total_time_seconds) * 60

        # Calculate average processing time from individual results
        avg_processing_time_ms = 0.0
        if session.results:
            processing_times = [
                result.processing_time_ms for result in session.results.values()
                if result.processing_time_ms > 0
            ]
            if processing_times:
                avg_processing_time_ms = sum(processing_times) / len(processing_times)

        # Calculate min and max processing times
        min_processing_time_ms = 0.0
        max_processing_time_ms = 0.0
        if session.results:
            processing_times = [
                result.processing_time_ms for result in session.results.values()
                if result.processing_time_ms > 0
            ]
            if processing_times:
                min_processing_time_ms = min(processing_times)
                max_processing_time_ms = max(processing_times)

        return {
            "total_time_seconds": round(total_time_seconds, 2),
            "average_time_per_question_seconds": round(avg_time_per_question, 2),
            "questions_per_minute": round(questions_per_minute, 2),
            "average_processing_time_ms": round(avg_processing_time_ms, 2),
            "min_processing_time_ms": round(min_processing_time_ms, 2),
            "max_processing_time_ms": round(max_processing_time_ms, 2)
        }

