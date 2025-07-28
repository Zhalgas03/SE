#!/usr/bin/env python3
"""
Simplified tests for voting endpoints
Focuses on core validation and error handling without JWT complications
"""

import unittest
import uuid
import json
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.votes import validate_uuid, validate_trip_id, votes_bp
from flask import Flask
from flask_jwt_extended import JWTManager
from unittest.mock import patch, MagicMock

class TestVotingEndpointsSimple(unittest.TestCase):
    """Test voting endpoints with proper mocking"""
    
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
    
    def test_test_endpoint(self):
        """Test the test endpoint (no auth required)"""
        response = self.client.get('/api/votes/test')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Voting endpoints are working')
    
    def test_guest_vote_validation(self):
        """Test guest voting validation (no auth required)"""
        # Test invalid UUID
        response = self.client.post(
            '/api/votes/guest/not-a-uuid',
            json={'value': 1}
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Invalid trip ID format', data['message'])
        
        # Test valid UUID
        valid_trip_id = str(uuid.uuid4())
        response = self.client.post(
            f'/api/votes/guest/{valid_trip_id}',
            json={'value': 1}
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_guest_vote_request_validation(self):
        """Test guest voting request validation"""
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
        
        # Test empty JSON
        response = self.client.post(
            f'/api/votes/guest/{valid_trip_id}',
            json={}
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'No data provided')
        
        # Test missing value field
        response = self.client.post(
            f'/api/votes/guest/{valid_trip_id}',
            json={'other_field': 'value'}
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], "Missing 'value' field")
        
        # Test invalid vote value
        response = self.client.post(
            f'/api/votes/guest/{valid_trip_id}',
            json={'value': 0}
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Vote must be +1 or -1')
    
    def test_guest_vote_uuid_edge_cases(self):
        """Test guest voting with UUID edge cases"""
        edge_cases = [
            ("", 404),  # Empty string - Flask route not found
            ("not-a-uuid", 400),  # Invalid format
            ("550e8400-e29b-41d4-a716-4466554400000", 400),  # Too long
            ("550e8400-e29b-41d4-a716-44665544000", 400),   # Too short
        ]
        
        for trip_id, expected_status in edge_cases:
            with self.subTest(trip_id=trip_id):
                response = self.client.post(
                    f'/api/votes/guest/{trip_id}',
                    json={'value': 1}
                )
                self.assertEqual(response.status_code, expected_status)
                if expected_status == 400:
                    data = json.loads(response.data)
                    self.assertFalse(data['success'])
                    self.assertIn('Invalid trip ID format', data['message'])


class TestVotingValidationDirect(unittest.TestCase):
    """Test validation functions directly"""
    
    def test_validate_uuid_edge_cases(self):
        """Test UUID validation with edge cases"""
        # Valid UUIDs
        valid_uuids = [
            str(uuid.uuid4()),
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "12345678-1234-1234-1234-123456789012",  # This is actually valid
        ]
        
        for uuid_str in valid_uuids:
            with self.subTest(uuid=uuid_str):
                self.assertTrue(validate_uuid(uuid_str))
        
        # Invalid UUIDs
        invalid_uuids = [
            "not-a-uuid",
            "550e8400-e29b-41d4-a716-4466554400000",  # Too long
            "550e8400-e29b-41d4-a716-44665544000",   # Too short
            "550e8400e29b41d4a716446655440000",      # No hyphens
            "",
            None,
            123,
            [],
            {},
            True,
            False
        ]
        
        for uuid_str in invalid_uuids:
            with self.subTest(uuid=uuid_str):
                self.assertFalse(validate_uuid(uuid_str))
    
    def test_validate_trip_id_comprehensive(self):
        """Test trip_id validation comprehensively"""
        # Valid trip IDs
        valid_trip_ids = [
            str(uuid.uuid4()),
            "550e8400-e29b-41d4-a716-446655440000",
        ]
        
        for trip_id in valid_trip_ids:
            with self.subTest(trip_id=trip_id):
                is_valid, error_msg = validate_trip_id(trip_id)
                self.assertTrue(is_valid)
                self.assertIsNone(error_msg)
        
        # Invalid trip IDs
        test_cases = [
            (None, "Trip ID is required"),
            ("", "Trip ID is required"),
            ("   ", "Trip ID is required"),
            ("\t", "Trip ID is required"),
            ("\n", "Trip ID is required"),
            (123, "Trip ID must be a string"),
            ([], "Trip ID must be a string"),
            ({}, "Trip ID must be a string"),
            (True, "Trip ID must be a string"),
            (False, "Trip ID must be a string"),
            ("not-a-uuid", "Invalid trip ID format. Expected UUID format."),
            ("550e8400-e29b-41d4-a716-4466554400000", "Invalid trip ID format. Expected UUID format."),
            ("550e8400-e29b-41d4-a716-44665544000", "Invalid trip ID format. Expected UUID format."),
            ("550e8400e29b41d4a716446655440000", "Invalid trip ID format. Expected UUID format."),
            ("null", "Invalid trip ID format. Expected UUID format."),
            ("undefined", "Invalid trip ID format. Expected UUID format."),
        ]
        
        for trip_id, expected_error in test_cases:
            with self.subTest(trip_id=trip_id):
                is_valid, error_msg = validate_trip_id(trip_id)
                self.assertFalse(is_valid)
                self.assertEqual(error_msg, expected_error)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 