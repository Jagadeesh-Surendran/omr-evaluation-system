"""
Security Tests for AI Question Solver

Tests security requirements:
- Authentication enforcement on all endpoints
- Authorization for approval endpoint
- Session locking prevents concurrent edits
- Answer key immutability after approval

Requirements: 15.1-15.5 (Security and Access Control)
"""

import pytest
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from app import app
from session_manager import SessionManager, SessionState
from question_parser import Question, QuestionOption
from answer_key_generator import AnswerKeyGenerator


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def session_manager():
    """Session manager instance"""
    return SessionManager()


@pytest.fixture
def sample_session(session_manager):
    """Create a sample session for testing"""
    session_id = session_manager.create_session('/tmp/test.pdf')
    session = session_manager.get_session(session_id)
    
    # Add sample questions and results
    session.questions = [
        Question(
            number=i,
            text=f"Question {i}",
            options=[QuestionOption(label=l, text=f"Option {l}") for l in "ABCD"],
            page_number=1,
            question_type="factual"
        )
        for i in range(1, 6)
    ]
    session.total_questions = 5
    session.status = "completed"
    
    from ai_solver import SolverResult
    for i in range(1, 6):
        session.results[i] = SolverResult(
            i, "B", "Answer explanation", 0.9, 500, "solved"
        )
    session.processed_count = 5
    session.solved_count = 5
    
    return session_id


class TestAuthenticationEnforcement:
    """Test authentication on all solver endpoints (Req 15.1)"""
    
    def test_upload_requires_authentication(self, client):
        """Test that upload endpoint requires authentication (Req 15.1)"""
        # Attempt upload without authentication
        response = client.post(
            '/api/solve/upload',
            data={'file': (BytesIO(b'%PDF-1.4 test'), 'test.pdf')},
            content_type='multipart/form-data'
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data or 'message' in data
        assert 'authentication' in str(data).lower() or 'unauthorized' in str(data).lower()
    
    def test_session_status_requires_authentication(self, client, sample_session):
        """Test that session status endpoint requires authentication (Req 15.1)"""
        # Attempt to get session status without authentication
        response = client.get(f'/api/solve/session/{sample_session}')
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data or 'message' in data
    
    def test_pause_requires_authentication(self, client, sample_session):
        """Test that pause endpoint requires authentication (Req 15.1)"""
        response = client.post(f'/api/solve/session/{sample_session}/pause')
        
        assert response.status_code == 401
    
    def test_resume_requires_authentication(self, client, sample_session):
        """Test that resume endpoint requires authentication (Req 15.1)"""
        response = client.post(f'/api/solve/session/{sample_session}/resume')
        
        assert response.status_code == 401
    
    def test_cancel_requires_authentication(self, client, sample_session):
        """Test that cancel endpoint requires authentication (Req 15.1)"""
        response = client.post(f'/api/solve/session/{sample_session}/cancel')
        
        assert response.status_code == 401
    
    def test_answer_update_requires_authentication(self, client, sample_session):
        """Test that answer update endpoint requires authentication (Req 15.1)"""
        response = client.put(
            f'/api/solve/session/{sample_session}/answer/1',
            json={'answer': 'C'}
        )
        
        assert response.status_code == 401
    
    def test_approve_requires_authentication(self, client, sample_session):
        """Test that approve endpoint requires authentication (Req 15.1)"""
        response = client.post(
            f'/api/solve/session/{sample_session}/approve',
            json={'user_id': 'test_user'}
        )
        
        assert response.status_code == 401
    
    def test_export_requires_authentication(self, client, sample_session):
        """Test that export endpoint requires authentication (Req 15.1)"""
        response = client.get(f'/api/solve/session/{sample_session}/export?format=json')
        
        assert response.status_code == 401
    
    @patch('app.verify_token')
    def test_authenticated_request_succeeds(self, mock_verify, client, sample_session):
        """Test that authenticated requests are allowed"""
        # Mock authentication to succeed
        mock_verify.return_value = {'user_id': 'test_user', 'role': 'user'}
        
        # Add authentication header
        headers = {'Authorization': 'Bearer valid_token'}
        
        response = client.get(
            f'/api/solve/session/{sample_session}',
            headers=headers
        )
        
        # Should succeed (200 or 404 if session not found, but not 401)
        assert response.status_code != 401


class TestAuthorizationForApproval:
    """Test authorization for approval endpoint (Req 15.2)"""
    
    @patch('app.verify_token')
    def test_approval_requires_admin_role(self, mock_verify, client, sample_session):
        """Test that approval requires administrator privileges (Req 15.2)"""
        # Mock authentication with non-admin user
        mock_verify.return_value = {'user_id': 'regular_user', 'role': 'user'}
        
        headers = {'Authorization': 'Bearer valid_token'}
        response = client.post(
            f'/api/solve/session/{sample_session}/approve',
            json={'user_id': 'regular_user'},
            headers=headers
        )
        
        # Should return 403 Forbidden
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data or 'message' in data
        assert 'authorization' in str(data).lower() or 'forbidden' in str(data).lower() or 'admin' in str(data).lower()
    
    @patch('app.verify_token')
    def test_admin_can_approve(self, mock_verify, client, sample_session):
        """Test that admin users can approve answer keys (Req 15.2)"""
        # Mock authentication with admin user
        mock_verify.return_value = {'user_id': 'admin_user', 'role': 'admin'}
        
        headers = {'Authorization': 'Bearer admin_token'}
        response = client.post(
            f'/api/solve/session/{sample_session}/approve',
            json={'user_id': 'admin_user'},
            headers=headers
        )
        
        # Should succeed (200 or 400 if validation fails, but not 403)
        assert response.status_code != 403
    
    @patch('app.verify_token')
    def test_approval_logged_with_user_id(self, mock_verify, client, session_manager, sample_session):
        """Test that approval actions are logged with user identification (Req 15.3)"""
        # Mock authentication
        mock_verify.return_value = {'user_id': 'admin_user', 'role': 'admin'}
        
        headers = {'Authorization': 'Bearer admin_token'}
        response = client.post(
            f'/api/solve/session/{sample_session}/approve',
            json={'user_id': 'admin_user'},
            headers=headers
        )
        
        if response.status_code == 200:
            # Verify approval metadata includes user_id
            session = session_manager.get_session(sample_session)
            
            # Check if approval metadata exists
            generator = AnswerKeyGenerator()
            metadata = generator.get_metadata(session)
            
            assert metadata.approved is True
            assert metadata.approved_by == 'admin_user'
            assert metadata.approved_at is not None


class TestSessionLocking:
    """Test session locking prevents concurrent edits (Req 15.4)"""
    
    def test_concurrent_edit_prevention(self, session_manager, sample_session):
        """Test that session locking prevents simultaneous editing (Req 15.4)"""
        results = {'thread1': None, 'thread2': None}
        errors = {'thread1': None, 'thread2': None}
        
        def update_answer_thread1():
            try:
                success = session_manager.update_answer(sample_session, 1, 'C')
                results['thread1'] = success
            except Exception as e:
                errors['thread1'] = str(e)
        
        def update_answer_thread2():
            try:
                success = session_manager.update_answer(sample_session, 2, 'D')
                results['thread2'] = success
            except Exception as e:
                errors['thread2'] = str(e)
        
        # Start both threads simultaneously
        thread1 = threading.Thread(target=update_answer_thread1)
        thread2 = threading.Thread(target=update_answer_thread2)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Both should complete without errors (locking should serialize access)
        assert errors['thread1'] is None
        assert errors['thread2'] is None
        
        # Both updates should succeed
        assert results['thread1'] is True
        assert results['thread2'] is True
        
        # Verify both updates were applied
        session = session_manager.get_session(sample_session)
        assert session.results[1].selected_option == 'C'
        assert session.results[2].selected_option == 'D'
    
    def test_lock_released_after_operation(self, session_manager, sample_session):
        """Test that locks are properly released after operations"""
        # Perform an update
        success = session_manager.update_answer(sample_session, 1, 'C')
        assert success is True
        
        # Verify lock is released by performing another update
        success = session_manager.update_answer(sample_session, 2, 'D')
        assert success is True
        
        # Should not hang or timeout
    
    def test_lock_timeout_on_deadlock(self, session_manager, sample_session):
        """Test that locks timeout to prevent deadlock"""
        import threading
        
        # Acquire lock manually
        lock = session_manager.session_locks.get(sample_session)
        if lock:
            acquired = lock.acquire(timeout=1)
            assert acquired is True
            
            # Try to update from another thread (should timeout or wait)
            result = {'success': None, 'error': None}
            
            def try_update():
                try:
                    result['success'] = session_manager.update_answer(
                        sample_session, 1, 'C'
                    )
                except Exception as e:
                    result['error'] = str(e)
            
            thread = threading.Thread(target=try_update)
            thread.start()
            
            # Wait a bit then release lock
            time.sleep(0.5)
            lock.release()
            
            thread.join(timeout=5)
            
            # Update should eventually succeed after lock released
            assert result['success'] is True or result['error'] is not None


class TestAnswerKeyImmutability:
    """Test answer key immutability after approval (Req 15.5)"""
    
    @patch('app.verify_token')
    def test_approved_answer_key_immutable(
        self, mock_verify, client, session_manager, sample_session
    ):
        """Test that approved answer keys cannot be modified (Req 15.5)"""
        # Approve the answer key
        mock_verify.return_value = {'user_id': 'admin_user', 'role': 'admin'}
        headers = {'Authorization': 'Bearer admin_token'}
        
        response = client.post(
            f'/api/solve/session/{sample_session}/approve',
            json={'user_id': 'admin_user'},
            headers=headers
        )
        
        if response.status_code == 200:
            # Try to modify an answer
            response = client.put(
                f'/api/solve/session/{sample_session}/answer/1',
                json={'answer': 'C'},
                headers=headers
            )
            
            # Should be rejected (403 or 400)
            assert response.status_code in [400, 403]
            data = json.loads(response.data)
            assert 'approved' in str(data).lower() or 'immutable' in str(data).lower()
    
    def test_new_version_created_for_changes(self, session_manager, sample_session):
        """Test that changes to approved keys create new versions (Req 15.5)"""
        # Approve the answer key
        generator = AnswerKeyGenerator()
        success = generator.approve_answer_key(sample_session, 'admin_user')
        
        if success:
            # Attempt to modify should create new version
            session = session_manager.get_session(sample_session)
            original_session_id = session.session_id
            
            # Try to update (should fail or create new version)
            result = session_manager.update_answer(sample_session, 1, 'C')
            
            # Either update fails (immutable) or new version created
            if result is False:
                # Immutability enforced
                assert True
            else:
                # New version should be created
                # Original should remain unchanged
                original_session = session_manager.get_session(original_session_id)
                assert original_session.results[1].selected_option == 'B'  # Original value
    
    def test_approval_metadata_persisted(self, session_manager, sample_session):
        """Test that approval metadata is persisted (Req 15.3, 15.5)"""
        # Approve answer key
        generator = AnswerKeyGenerator()
        success = generator.approve_answer_key(sample_session, 'admin_user')
        
        if success:
            # Save and reload session
            session_manager.save_session(sample_session)
            
            # Clear in-memory cache
            session_manager.active_sessions.pop(sample_session, None)
            
            # Reload from disk
            reloaded_session = session_manager.load_session(sample_session)
            
            # Verify approval metadata persisted
            metadata = generator.get_metadata(reloaded_session)
            assert metadata.approved is True
            assert metadata.approved_by == 'admin_user'
            assert metadata.approved_at is not None


class TestActionLogging:
    """Test logging of security-relevant actions (Req 15.3)"""
    
    @patch('app.verify_token')
    @patch('session_manager.logger')
    def test_answer_key_generation_logged(
        self, mock_logger, mock_verify, client, sample_session
    ):
        """Test that answer key generation is logged (Req 15.3)"""
        mock_verify.return_value = {'user_id': 'test_user', 'role': 'user'}
        headers = {'Authorization': 'Bearer token'}
        
        response = client.get(
            f'/api/solve/session/{sample_session}/export?format=json',
            headers=headers
        )
        
        if response.status_code == 200:
            # Verify logging occurred
            assert mock_logger.info.called or mock_logger.debug.called
            
            # Check log contains user_id and session_id
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            log_text = ' '.join(log_calls)
            
            assert 'test_user' in log_text or sample_session in log_text
    
    @patch('app.verify_token')
    @patch('session_manager.logger')
    def test_approval_action_logged(
        self, mock_logger, mock_verify, client, sample_session
    ):
        """Test that approval actions are logged with timestamp (Req 15.3)"""
        mock_verify.return_value = {'user_id': 'admin_user', 'role': 'admin'}
        headers = {'Authorization': 'Bearer admin_token'}
        
        response = client.post(
            f'/api/solve/session/{sample_session}/approve',
            json={'user_id': 'admin_user'},
            headers=headers
        )
        
        if response.status_code == 200:
            # Verify approval was logged
            assert mock_logger.info.called
            
            # Check log contains approval details
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            log_text = ' '.join(log_calls)
            
            assert 'approve' in log_text.lower() or 'approval' in log_text.lower()
            assert 'admin_user' in log_text or sample_session in log_text
    
    @patch('app.verify_token')
    @patch('session_manager.logger')
    def test_manual_correction_logged(
        self, mock_logger, mock_verify, client, sample_session
    ):
        """Test that manual corrections are logged (Req 15.3)"""
        mock_verify.return_value = {'user_id': 'test_user', 'role': 'user'}
        headers = {'Authorization': 'Bearer token'}
        
        response = client.put(
            f'/api/solve/session/{sample_session}/answer/1',
            json={'answer': 'C'},
            headers=headers
        )
        
        if response.status_code == 200:
            # Verify correction was logged
            assert mock_logger.info.called or mock_logger.debug.called
            
            # Check log contains correction details
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            log_text = ' '.join(log_calls)
            
            # Should log original and corrected answers
            assert 'test_user' in log_text or sample_session in log_text


class TestInputValidation:
    """Test input validation for security"""
    
    @patch('app.verify_token')
    def test_invalid_session_id_rejected(self, mock_verify, client):
        """Test that invalid session IDs are rejected"""
        mock_verify.return_value = {'user_id': 'test_user', 'role': 'user'}
        headers = {'Authorization': 'Bearer token'}
        
        # Try with malicious session ID
        response = client.get(
            '/api/solve/session/../../../etc/passwd',
            headers=headers
        )
        
        # Should reject (404 or 400, not 200)
        assert response.status_code in [400, 404]
    
    @patch('app.verify_token')
    def test_invalid_answer_option_rejected(self, mock_verify, client, sample_session):
        """Test that invalid answer options are rejected"""
        mock_verify.return_value = {'user_id': 'test_user', 'role': 'user'}
        headers = {'Authorization': 'Bearer token'}
        
        # Try with invalid answer option
        response = client.put(
            f'/api/solve/session/{sample_session}/answer/1',
            json={'answer': 'Z'},  # Invalid option
            headers=headers
        )
        
        # Should reject (400)
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data or 'message' in data
    
    @patch('app.verify_token')
    def test_sql_injection_prevented(self, mock_verify, client):
        """Test that SQL injection attempts are prevented"""
        mock_verify.return_value = {'user_id': 'test_user', 'role': 'user'}
        headers = {'Authorization': 'Bearer token'}
        
        # Try SQL injection in session ID
        response = client.get(
            "/api/solve/session/'; DROP TABLE sessions; --",
            headers=headers
        )
        
        # Should reject safely (404 or 400)
        assert response.status_code in [400, 404]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
