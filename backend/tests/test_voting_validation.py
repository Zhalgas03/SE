#!/usr/bin/env python3
"""
Focused tests for voting validation functions
Tests UUID validation and trip_id validation without JWT complications
"""

import unittest
import uuid
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.votes import validate_uuid, validate_trip_id

class TestVotingValidation(unittest.TestCase):
    """Test UUID validation and trip_id validation functions"""
    
    def test_validate_uuid_valid(self):
        """Test valid UUID validation"""
        valid_uuid = str(uuid.uuid4())
        self.assertTrue(validate_uuid(valid_uuid))
        
        # Test some known valid UUIDs
        known_valid = [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "6ba7b811-9dad-11d1-80b4-00c04fd430c8"
        ]
        for uuid_str in known_valid:
            with self.subTest(uuid=uuid_str):
                self.assertTrue(validate_uuid(uuid_str))
    
    def test_validate_uuid_invalid_format(self):
        """Test invalid UUID format"""
        invalid_uuids = [
            "not-a-uuid",
            # "12345678-1234-1234-1234-123456789012",  # Removed: valid UUID
            "550e8400-e29b-41d4-a716-4466554400000",  # Too long
            "550e8400-e29b-41d4-a716-44665544000",   # Too short
            "550e8400e29b41d4a716446655440000",      # No hyphens
            "550e8400-e29b-41d4-a716-44665544000-",  # Extra hyphen
            "-550e8400-e29b-41d4-a716-446655440000", # Leading hyphen
            "550e8400-e29b-41d4-a716-446655440000-", # Trailing hyphen
            "",
            None,
            123,
            [],
            {},
            True,
            False
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
            (True, "Trip ID must be a string"),
            (False, "Trip ID must be a string"),
            ("not-a-uuid", "Invalid trip ID format. Expected UUID format."),
            ("550e8400-e29b-41d4-a716-4466554400000", "Invalid trip ID format. Expected UUID format."),
            ("550e8400-e29b-41d4-a716-44665544000", "Invalid trip ID format. Expected UUID format."),
            ("550e8400e29b41d4a716446655440000", "Invalid trip ID format. Expected UUID format."),
        ]
        
        for trip_id, expected_error in test_cases:
            with self.subTest(trip_id=trip_id):
                is_valid, error_msg = validate_trip_id(trip_id)
                self.assertFalse(is_valid)
                self.assertEqual(error_msg, expected_error)
    
    def test_validate_trip_id_edge_cases(self):
        """Test edge cases for trip_id validation"""
        # Test with various string types that should fail (whitespace-only)
        edge_cases = [
            "   ",  # Whitespace only
            "\t",   # Tab
            "\n",   # Newline
        ]
        
        for trip_id in edge_cases:
            with self.subTest(trip_id=repr(trip_id)):
                is_valid, error_msg = validate_trip_id(trip_id)
                self.assertFalse(is_valid)
                self.assertEqual(error_msg, "Trip ID is required")
        # Also test string 'null' and 'undefined' (should fail UUID format)
        for trip_id in ["null", "undefined"]:
            with self.subTest(trip_id=trip_id):
                is_valid, error_msg = validate_trip_id(trip_id)
                self.assertFalse(is_valid)
                self.assertIn("Invalid trip ID format", error_msg)

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 