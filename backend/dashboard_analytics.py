"""
Dashboard Analytics module for aggregating solver statistics across all sessions.
"""
import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from solver_logging_config import get_logger

logger = get_logger("dashboard_analytics")


class DashboardAnalytics:
    """Aggregates and analyzes solver statistics across all sessions."""
    
    def __init__(self, sessions_dir: str = None):
        """
        Initialize DashboardAnalytics.
        
        Args:
            sessions_dir: Path to solver sessions directory
        """
        if sessions_dir is None:
            # Default path - check if we're in backend directory or parent
            if os.path.exists("solver_sessions"):
                sessions_dir = "solver_sessions"
            else:
                sessions_dir = os.path.join("backend", "solver_sessions")
        
        self.sessions_dir = sessions_dir
        logger.info("[DASHBOARD_ANALYTICS] Initialized")
    
    def get_dashboard_data(self) -> dict:
        """
        Aggregates data from all sessions to provide dashboard statistics.
        
        Returns:
            Dictionary with comprehensive dashboard statistics
        """
        logger.info("[DASHBOARD_ANALYTICS] Generating dashboard data")
        
        # Get all session IDs
        session_ids = self._get_all_session_ids()
        
        if not session_ids:
            logger.warning("[DASHBOARD_ANALYTICS] No sessions found")
            return self._empty_dashboard()
        
        logger.info(f"[DASHBOARD_ANALYTICS] Found {len(session_ids)} sessions")
        
        # Aggregate data from all sessions
        total_questions = 0
        total_solved = 0
        total_unsolvable = 0
        total_errors = 0
        total_corrections = 0
        
        # For accuracy trends
        confidence_by_date = defaultdict(list)
        
        # For failure patterns
        failure_patterns = defaultdict(int)
        
        # For model performance by question type
        model_performance = defaultdict(lambda: {
            "total": 0,
            "solved": 0,
            "confidence_sum": 0.0,
            "avg_confidence": 0.0,
            "avg_processing_time_ms": 0.0,
            "processing_times": []
        })
        
        # Process each session
        for session_id in session_ids:
            session_data = self._load_session_data(session_id)
            if not session_data:
                continue
            
            # Aggregate basic counts
            total_questions += session_data.get("total_questions", 0)
            total_solved += session_data.get("solved_count", 0)
            total_unsolvable += session_data.get("unsolvable_count", 0)
            total_errors += session_data.get("error_count", 0)
            
            # Load solver responses for detailed analysis
            solver_responses = self._load_solver_responses(session_id)
            
            # Load user corrections
            user_corrections = self._load_user_corrections(session_id)
            total_corrections += len(user_corrections)
            
            # Analyze solver responses
            for response in solver_responses:
                data = response.get("data", {})
                timestamp = response.get("timestamp", "")
                
                # Extract date for trends
                try:
                    date = datetime.fromisoformat(timestamp).date()
                    confidence = data.get("confidence", 0.0)
                    if confidence > 0:
                        confidence_by_date[str(date)].append(confidence)
                except (ValueError, AttributeError):
                    pass
                
                # Track failure patterns
                status = data.get("status", "")
                if status in ["timeout", "unsolvable", "error"]:
                    error_msg = data.get("error_message", status)
                    failure_patterns[error_msg] += 1
                
                # Track model performance by question type
                # Note: We need to infer question type from question text or use session metadata
                question_text = data.get("question_text", "")
                question_type = self._infer_question_type(question_text)
                
                model_performance[question_type]["total"] += 1
                if status == "solved":
                    model_performance[question_type]["solved"] += 1
                    confidence = data.get("confidence", 0.0)
                    model_performance[question_type]["confidence_sum"] += confidence
                    
                processing_time = data.get("processing_time_ms", 0.0)
                model_performance[question_type]["processing_times"].append(processing_time)
        
        # Calculate accuracy trends
        accuracy_trends = self._calculate_accuracy_trends(confidence_by_date)
        
        # Calculate average confidence and processing times for each question type
        for qtype, stats in model_performance.items():
            if stats["solved"] > 0:
                stats["avg_confidence"] = round(stats["confidence_sum"] / stats["solved"], 4)
            if stats["processing_times"]:
                stats["avg_processing_time_ms"] = round(
                    sum(stats["processing_times"]) / len(stats["processing_times"]), 2
                )
            # Remove intermediate data
            del stats["confidence_sum"]
            del stats["processing_times"]
        
        # Get top failure patterns
        top_failures = sorted(
            failure_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  # Top 10 failure patterns
        
        # Build dashboard data
        dashboard = {
            "overview": {
                "total_sessions": len(session_ids),
                "total_questions": total_questions,
                "total_solved": total_solved,
                "total_unsolvable": total_unsolvable,
                "total_errors": total_errors,
                "total_corrections": total_corrections,
                "overall_accuracy": round(
                    (total_solved / total_questions * 100) if total_questions > 0 else 0.0,
                    2
                ),
                "correction_rate": round(
                    (total_corrections / total_questions * 100) if total_questions > 0 else 0.0,
                    2
                )
            },
            "accuracy_trends": accuracy_trends,
            "failure_patterns": [
                {"pattern": pattern, "count": count}
                for pattern, count in top_failures
            ],
            "model_performance_by_type": dict(model_performance),
            "generated_at": datetime.now().isoformat()
        }
        
        logger.info(
            f"[DASHBOARD_ANALYTICS] Dashboard generated: "
            f"{total_questions} questions across {len(session_ids)} sessions"
        )
        
        return dashboard
    
    def _get_all_session_ids(self) -> List[str]:
        """
        Gets all session IDs from the sessions directory.
        
        Returns:
            List of session IDs
        """
        try:
            if not os.path.exists(self.sessions_dir):
                return []
            
            # List all directories in sessions directory
            session_ids = [
                d for d in os.listdir(self.sessions_dir)
                if os.path.isdir(os.path.join(self.sessions_dir, d))
            ]
            
            return session_ids
        except Exception as e:
            logger.error(f"[DASHBOARD_ANALYTICS] Error listing sessions: {e}")
            return []
    
    def _load_session_data(self, session_id: str) -> Optional[dict]:
        """
        Loads session metadata from session.json.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dictionary or None if not found
        """
        try:
            session_file = os.path.join(self.sessions_dir, session_id, "session.json")
            if not os.path.exists(session_file):
                return None
            
            with open(session_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[DASHBOARD_ANALYTICS] Error loading session {session_id}: {e}")
            return None
    
    def _load_solver_responses(self, session_id: str) -> List[dict]:
        """
        Loads solver responses from solver_responses.jsonl.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of solver response dictionaries
        """
        try:
            responses_file = os.path.join(
                self.sessions_dir, session_id, "logs", "solver_responses.jsonl"
            )
            if not os.path.exists(responses_file):
                return []
            
            responses = []
            with open(responses_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        responses.append(json.loads(line))
            
            return responses
        except Exception as e:
            logger.error(
                f"[DASHBOARD_ANALYTICS] Error loading solver responses for {session_id}: {e}"
            )
            return []
    
    def _load_user_corrections(self, session_id: str) -> List[dict]:
        """
        Loads user corrections from user_corrections.jsonl.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of user correction dictionaries
        """
        try:
            corrections_file = os.path.join(
                self.sessions_dir, session_id, "logs", "user_corrections.jsonl"
            )
            if not os.path.exists(corrections_file):
                return []
            
            corrections = []
            with open(corrections_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        corrections.append(json.loads(line))
            
            return corrections
        except Exception as e:
            logger.error(
                f"[DASHBOARD_ANALYTICS] Error loading user corrections for {session_id}: {e}"
            )
            return []
    
    def _infer_question_type(self, question_text: str) -> str:
        """
        Infers question type from question text using keyword analysis.
        
        Args:
            question_text: The question text
            
        Returns:
            Question type: "math", "logical", "factual", or "unknown"
        """
        if not question_text:
            return "unknown"
        
        text_lower = question_text.lower()
        
        # Math keywords
        math_keywords = [
            "calculate", "solve", "equation", "sum", "difference", "product",
            "quotient", "integral", "derivative", "algebra", "geometry",
            "trigonometry", "calculus", "+", "-", "×", "÷", "=", "√"
        ]
        
        # Logical keywords
        logical_keywords = [
            "pattern", "sequence", "next", "follows", "logic", "reasoning",
            "deduce", "infer", "conclude", "if", "then", "therefore"
        ]
        
        # Check for math
        if any(keyword in text_lower for keyword in math_keywords):
            return "math"
        
        # Check for logical
        if any(keyword in text_lower for keyword in logical_keywords):
            return "logical"
        
        # Default to factual
        return "factual"
    
    def _calculate_accuracy_trends(self, confidence_by_date: Dict[str, List[float]]) -> List[dict]:
        """
        Calculates accuracy trends over time from confidence scores.
        
        Args:
            confidence_by_date: Dictionary mapping dates to lists of confidence scores
            
        Returns:
            List of trend data points with date and average confidence
        """
        trends = []
        
        for date_str in sorted(confidence_by_date.keys()):
            confidences = confidence_by_date[date_str]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            trends.append({
                "date": date_str,
                "avg_confidence": round(avg_confidence, 4),
                "question_count": len(confidences)
            })
        
        return trends
    
    def _empty_dashboard(self) -> dict:
        """
        Returns an empty dashboard structure when no sessions exist.
        
        Returns:
            Empty dashboard dictionary
        """
        return {
            "overview": {
                "total_sessions": 0,
                "total_questions": 0,
                "total_solved": 0,
                "total_unsolvable": 0,
                "total_errors": 0,
                "total_corrections": 0,
                "overall_accuracy": 0.0,
                "correction_rate": 0.0
            },
            "accuracy_trends": [],
            "failure_patterns": [],
            "model_performance_by_type": {},
            "generated_at": datetime.now().isoformat()
        }
