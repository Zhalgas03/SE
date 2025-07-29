#!/usr/bin/env python3
"""
Comprehensive unit tests for voting endpoints
Tests all edge cases: UUID validation, database existence checks, error handling, status codes
"""

import unittest
import uuid
import json
import requests
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.votes import validate_uuid, validate_trip_id, votes_bp
from flask import Flask
from flask_jwt_extended import JWTManager

class TestVotingValidation(unittest.TestCase):
    """Test UUID validation and trip_id validation functions"""
    
    def test_validate_uuid_valid(self):
        """Test valid UUID validation"""
        valid_uuid = str(uuid.uuid4())
        self.assertTrue(validate_uuid(valid_uuid))
    
    def test_validate_uuid_invalid_format(self):
        """Test invalid UUID format"""
        invalid_uuids = [
            "not-a-uuid",
            "12345678-1234-1234-1234-123456789012",  # Invalid format
            "550e8400-e29b-41d4-a716-4466554400000",  # Too long
            "550e8400-e29b-41d4-a716-44665544000",   # Too short
            "",
            None,
            123,
            [],
            {}
        ]
        
        for invalid_uuid in invalid_uuids:
            with self.subTest(uuid=invalid_uuid):
                self.assertFalse(validate_uuid(invalid_uuid))
    
    def test_validate_trip_id_valid(self):
        """Test valid trip_id validation"""
        valid_trip_id = str(uuid.uuid4())
        is_valid, error_msg = validate_trip_id(valid_trip_id)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_validate_trip_id_invalid(self):
        """Test invalid trip_id validation"""
        test_cases = [
            (None, "Trip ID is required"),
            ("", "Trip ID is required"),
            (123, "Trip ID must be a string"),
            ([], "Trip ID must be a string"),
            ({}, "Trip ID must be a string"),
            ("not-a-uuid", "Invalid trip ID format. Expected UUID format."),
            ("550e8400-e29b-41d4-a716-4466554400000", "Invalid trip ID format. Expected UUID format."),
        ]
        
        for trip_id, expected_error in test_cases:
            with self.subTest(trip_id=trip_id):
                is_valid, error_msg = validate_trip_id(trip_id)
                self.assertFalse(is_valid)
                self.assertEqual(error_msg, expected_error)


class TestVotingEndpoints(unittest.TestCase):
    """Test voting endpoints with Flask test client"""
    
    def setUp(self):
        """Set up Flask test app"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['JWT_SECRET_KEY'] = 'test-secret'
        
        # Initialize JWT
        jwt = JWTManager(self.app)
        
        # Register blueprint
        self.app.register_blueprint(votes_bp)
        
        self.client = self.app.test_client()
        
        # Mock database connection
        self.db_patcher = patch('api.votes.get_db_connection')
        self.mock_db = self.db_patcher.start()
        
        # Mock cursor
        self.mock_cursor = MagicMock()
        self.mock_conn = MagicMock()
        self.mock_conn.cursor.return_value.__enter__.return_value = self.mock_cursor
        self.mock_db.return_value.__enter__.return_value = self.mock_conn
    
    def tearDown(self):
        """Clean up mocks"""
        self.db_patcher.stop()
    
    def test_test_endpoint(self):
        """Test the test endpoint"""
        response = self.client.get('/api/votes/test')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Voting endpoints are working')
    
    def test_get_vote_status_invalid_uuid(self):
        """Test vote status with invalid UUID"""
        invalid_trip_ids = [
            "not-a-uuid",
            "12345678-1234-1234-1234-123456789012",
            "",
            "550e8400-e29b-41d4-a716-4466554400000"
        ]
        
        for trip_id in invalid_trip_ids:
            with self.subTest(trip_id=trip_id):
                # Mock JWT authentication
                with patch('api.votes.get_jwt_identity', return_value='testuser'):
                    response = self.client.get(f'/api/votes/status/{trip_id}')
                    self.assertEqual(response.status_code, 400)
                    data = json.loads(response.data)
                    self.assertFalse(data['success'])
                    self.assertIn('Invalid trip ID format', data['message'])
    
    def test_get_vote_status_trip_not_found(self):
        """Test vote status when trip doesn't exist"""
        valid_trip_id = str(uuid.uuid4())
        
        # Mock JWT authentication
        with patch('api.votes.get_jwt_identity', return_value='testuser'):
            # Mock user found but trip not found
            self.mock_cursor.fetchone.side_effect = [
                {'id': 1},  # User found
                None        # Trip not found
            ]
            
            response = self.client.get(f'/api/votes/status/{valid_trip_id}')
            self.assertEqual(response.status_code, 404)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
            self.assertEqual(data['message'], 'Trip not found')
    
    def test_get_vote_status_user_not_found(self):
        """Test vote status when user doesn't exist"""
        valid_trip_id = str(uuid.uuid4())
        
        # Mock JWT authentication
        with patch('api.votes.get_jwt_identity', return_value='nonexistentuser'):
            # Mock user not found
            self.mock_cursor.fetchone.return_value = None
            
            response = self.client.get(f'/api/votes/status/{valid_trip_id}')
            self.assertEqual(response.status_code, 404)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
            self.assertEqual(data['message'], 'User not found')
    
    def test_get_vote_status_success_no_vote(self):
        """Test vote status when user hasn't voted"""
        valid_trip_id = str(uuid.uuid4())
        
        # Mock JWT authentication
        with patch('api.votes.get_jwt_identity', return_value='testuser'):
            # Mock user found, trip found, no vote
            self.mock_cursor.fetchone.side_effect = [
                {'id': 1},  # User found
                {'id': valid_trip_id, 'name': 'Test Trip'},  # Trip found
                None  # No vote
            ]
            
            response = self.client.get(f'/api/votes/status/{valid_trip_id}')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertFalse(data['hasVoted'])
            self.assertIsNone(data['voteValue'])
    
    def test_get_vote_status_success_has_vote(self):
        """Test vote status when user has voted"""
        valid_trip_id = str(uuid.uuid4())
        
        # Mock JWT authentication
        with patch('api.votes.get_jwt_identity', return_value='testuser'):
            # Mock user found, trip found, vote exists
            self.mock_cursor.fetchone.side_effect = [
                {'id': 1},  # User found
                {'id': valid_trip_id, 'name': 'Test Trip'},  # Trip found
                {'value': 1}  # Vote exists
            ]
            
            response = self.client.get(f'/api/votes/status/{valid_trip_id}')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertTrue(data['hasVoted'])
            self.assertEqual(data['voteValue'], 1)
    
    def test_vote_on_trip_invalid_uuid(self):
        """Test voting with invalid UUID"""
        invalid_trip_ids = [
            "not-a-uuid",
            "12345678-1234-1234-1234-123456789012",
            "",
            "550e8400-e29b-41d4-a716-4466554400000"
        ]
        
        for trip_id in invalid_trip_ids:
            with self.subTest(trip_id=trip_id):
                # Mock JWT authentication
                with patch('api.votes.get_jwt_identity', return_value='testuser'):
                    response = self.client.post(
                        f'/api/votes/{trip_id}',
                        json={'value': 1}
                    )
                    self.assertEqual(response.status_code, 400)
                    data = json.loads(response.data)
                    self.assertFalse(data['success'])
                    self.assertIn('Invalid trip ID format', data['message'])
    
    def test_vote_on_trip_invalid_request_data(self):
        """Test voting with invalid request data"""
        valid_trip_id = str(uuid.uuid4())
        
        # Mock JWT authentication
        with patch('api.votes.get_jwt_identity', return_value='testuser'):
            # Test non-JSON request
            response = self.client.post(
                f'/api/votes/{valid_trip_id}',
                data='not json'
            )
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
            self.assertEqual(data['message'], 'Request must be JSON')
            
            # Test empty JSON
            response = self.client.post(
                f'/api/votes/{valid_trip_id}',
                json={}
            )
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
            self.assertEqual(data['message'], 'No data provided')
            
            # Test missing value field
            response = self.client.post(
                f'/api/votes/{valid_trip_id}',
                json={'other_field': 'value'}
            )
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
            self.assertEqual(data['message'], "Missing 'value' field")
            
            # Test invalid vote value
            response = self.client.post(
                f'/api/votes/{valid_trip_id}',
                json={'value': 0}
            )
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
            self.assertEqual(data['message'], 'Vote must be +1 or -1')
            
            # Test invalid vote value type
            response = self.client.post(
                f'/api/votes/{valid_trip_id}',
                json={'value': 'yes'}
            )
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
            self.assertEqual(data['message'], 'Vote must be +1 or -1')
    
    def test_vote_on_trip_trip_not_found(self):
        """Test voting when trip doesn't exist"""
        valid_trip_id = str(uuid.uuid4())
        
        # Mock JWT authentication
        with patch('api.votes.get_jwt_identity', return_value='testuser'):
            # Mock user found but trip not found
            self.mock_cursor.fetchone.side_effect = [
                {'id': 1},  # User found
                None        # Trip not found
            ]
            
            response = self.client.post(
                f'/api/votes/{valid_trip_id}',
                json={'value': 1}
            )
            self.assertEqual(response.status_code, 404)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
            self.assertEqual(data['message'], 'Trip not found')
    
    def test_vote_on_trip_user_not_found(self):
        """Test voting when user doesn't exist"""
        valid_trip_id = str(uuid.uuid4())
        
        # Mock JWT authentication
        with patch('api.votes.get_jwt_identity', return_value='nonexistentuser'):
            # Mock user not found
            self.mock_cursor.fetchone.return_value = None
            
            response = self.client.post(
                f'/api/votes/{valid_trip_id}',
                json={'value': 1}
            )
            self.assertEqual(response.status_code, 404)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
            self.assertEqual(data['message'], 'User not found')
    
    def test_vote_on_trip_already_voted(self):
        """Test voting when user has already voted"""
        valid_trip_id = str(uuid.uuid4())
        
        # Mock JWT authentication
        with patch('api.votes.get_jwt_identity', return_value='testuser'):
            # Mock user found, trip found, voting rule found, but user already voted
            self.mock_cursor.fetchone.side_effect = [
                {'id': 1},  # User found
                {'id': valid_trip_id, 'name': 'Test Trip'},  # Trip found
                {'approval_threshold': 0.5, 'min_votes_required': 1},  # Voting rule found
                {'value': 1}  # User already voted
            ]
            
            response = self.client.post(
                f'/api/votes/{valid_trip_id}',
                json={'value': 1}
            )
            self.assertEqual(response.status_code, 409)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
            self.assertEqual(data['message'], 'You have already voted on this trip')
    
    def test_vote_on_trip_success(self):
        """Test successful voting"""
        valid_trip_id = str(uuid.uuid4())
        
        # Mock JWT authentication
        with patch('api.votes.get_jwt_identity', return_value='testuser'):
            # Mock successful voting flow
            self.mock_cursor.fetchone.side_effect = [
                {'id': 1},  # User found
                {'id': valid_trip_id, 'name': 'Test Trip'},  # Trip found
                {'approval_threshold': 0.5, 'min_votes_required': 1},  # Voting rule found
                None,  # User hasn't voted yet
                {'count': 1},  # Vote count
                {'sum': 1}  # Yes votes sum
            ]
            
            response = self.client.post(
                f'/api/votes/{valid_trip_id}',
                json={'value': 1}
            )
            self.assertEqual(response.status_code, 201)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual(data['message'], 'Vote submitted')
    
    def test_start_voting_session_invalid_uuid(self):
        """Test start voting session with invalid UUID"""
        invalid_trip_ids = [
            "not-a-uuid",
            "12345678-1234-1234-1234-123456789012",
            "",
            "550e8400-e29b-41d4-a716-4466554400000"
        ]
        
        for trip_id in invalid_trip_ids:
            with self.subTest(trip_id=trip_id):
                # Mock JWT authentication
                with patch('api.votes.get_jwt_identity', return_value='testuser'):
                    response = self.client.post(f'/api/votes/start/{trip_id}')
                    self.assertEqual(response.status_code, 400)
                    data = json.loads(response.data)
                    self.assertFalse(data['success'])
                    self.assertIn('Invalid trip ID format', data['message'])
    
    def test_start_voting_session_trip_not_found(self):
        """Test start voting session when trip doesn't exist"""
        valid_trip_id = str(uuid.uuid4())
        
        # Mock JWT authentication
        with patch('api.votes.get_jwt_identity', return_value='testuser'):
            # Mock user found but trip not found
            self.mock_cursor.fetchone.side_effect = [
                {'id': 1},  # User found
                None        # Trip not found or user doesn't own it
            ]
            
            response = self.client.post(f'/api/votes/start/{valid_trip_id}')
            self.assertEqual(response.status_code, 404)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
            self.assertEqual(data['message'], 'Trip not found or you don\'t have permission')
    
    def test_start_voting_session_success(self):
        """Test successful voting session start"""
        valid_trip_id = str(uuid.uuid4())
        
        # Mock JWT authentication
        with patch('api.votes.get_jwt_identity', return_value='testuser'):
            # Mock successful flow
            self.mock_cursor.fetchone.side_effect = [
                {'id': 1},  # User found
                {'id': valid_trip_id, 'name': 'Test Trip'}  # Trip found and user owns it
            ]
            
            response = self.client.post(f'/api/votes/start/{valid_trip_id}')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertIn('link', data)
            self.assertIn(valid_trip_id, data['link'])


class TestGuestVoting(unittest.TestCase):
    """Test guest voting endpoint"""
    
    def setUp(self):
        """Set up Flask test app for guest voting"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.register_blueprint(votes_bp)
        self.client = self.app.test_client()
    
    def test_guest_vote_invalid_uuid(self):
        """Test guest voting with invalid UUID"""
        invalid_trip_ids = [
            "not-a-uuid",
            "12345678-1234-1234-1234-123456789012",
            "",
            "550e8400-e29b-41d4-a716-4466554400000"
        ]
        
        for trip_id in invalid_trip_ids:
            with self.subTest(trip_id=trip_id):
                response = self.client.post(
                    f'/api/votes/guest/{trip_id}',
                    json={'value': 1}
                )
                self.assertEqual(response.status_code, 400)
                data = json.loads(response.data)
                self.assertFalse(data['success'])
                self.assertIn('Invalid trip ID format', data['message'])
    
    def test_guest_vote_invalid_request(self):
        """Test guest voting with invalid request data"""
        valid_trip_id = str(uuid.uuid4())
        
        # Test non-JSON request
        response = self.client.post(
            f'/api/votes/guest/{valid_trip_id}',
            data='not json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Request must be JSON')
        
        # Test missing value
        response = self.client.post(
            f'/api/votes/guest/{valid_trip_id}',
            json={}
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Missing \'value\' field')
        
        # Test invalid vote value
        response = self.client.post(
            f'/api/votes/guest/{valid_trip_id}',
            json={'value': 0}
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Vote must be +1 or -1')
    
    def test_guest_vote_success(self):
        """Test successful guest voting"""
        valid_trip_id = str(uuid.uuid4())
        
        response = self.client.post(
            f'/api/votes/guest/{valid_trip_id}',
            json={'value': 1}
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Guest vote submitted')


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 