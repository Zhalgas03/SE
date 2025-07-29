#!/usr/bin/env python3
"""
Comprehensive test script to verify voting endpoint security and validation.
Tests all edge cases and error conditions.
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5001"

def test_invalid_trip_ids():
    """Test various invalid trip ID formats"""
    print("🧪 Testing Invalid Trip ID Formats")
    print("=" * 40)
    
    invalid_trip_ids = [
        "123",  # Integer instead of UUID
        "invalid-uuid",  # Invalid UUID format
        "12345678-1234-1234-1234-123456789012",  # Invalid UUID
        "",  # Empty string
        None,  # None value
        "abc-def-ghi",  # Invalid format
    ]
    
    for trip_id in invalid_trip_ids:
        print(f"\n🔍 Testing trip_id: {trip_id}")
        
        # Test status endpoint
        response = requests.get(f"{BASE_URL}/api/votes/status/{trip_id}")
        print(f"  Status endpoint: {response.status_code} - {response.text[:100]}")
        
        # Test vote endpoint
        response = requests.post(f"{BASE_URL}/api/votes/{trip_id}", 
                               json={"value": 1},
                               headers={"Content-Type": "application/json"})
        print(f"  Vote endpoint: {response.status_code} - {response.text[:100]}")
        
        # Test start endpoint
        response = requests.post(f"{BASE_URL}/api/votes/start/{trip_id}")
        print(f"  Start endpoint: {response.status_code} - {response.text[:100]}")

def test_invalid_request_data():
    """Test invalid request data scenarios"""
    print("\n🧪 Testing Invalid Request Data")
    print("=" * 40)
    
    # Test with valid UUID but invalid request data
    valid_uuid = "00000000-0000-0000-0000-000000000000"
    
    test_cases = [
        # No JSON data
        (None, "No Content-Type header"),
        # Empty JSON
        ({}, "Empty JSON object"),
        # Missing value field
        ({"other_field": "test"}, "Missing value field"),
        # Invalid value types
        ({"value": "yes"}, "String instead of integer"),
        ({"value": 0}, "Invalid vote value"),
        ({"value": 2}, "Invalid vote value"),
        ({"value": -2}, "Invalid vote value"),
        ({"value": None}, "None value"),
    ]
    
    for data, description in test_cases:
        print(f"\n🔍 Testing: {description}")
        
        headers = {"Content-Type": "application/json"} if data is not None else {}
        body = json.dumps(data) if data is not None else ""
        
        response = requests.post(f"{BASE_URL}/api/votes/{valid_uuid}", 
                               data=body,
                               headers=headers)
        print(f"  Response: {response.status_code} - {response.text[:100]}")

def test_authentication_requirements():
    """Test authentication requirements"""
    print("\n🧪 Testing Authentication Requirements")
    print("=" * 40)
    
    valid_uuid = "00000000-0000-0000-0000-000000000000"
    
    # Test endpoints without authentication
    endpoints = [
        f"/api/votes/status/{valid_uuid}",
        f"/api/votes/{valid_uuid}",
        f"/api/votes/start/{valid_uuid}",
    ]
    
    for endpoint in endpoints:
        print(f"\n🔍 Testing: {endpoint}")
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"  Response: {response.status_code} - {response.text[:100]}")
    
    # Test guest endpoint (should work without auth)
    print(f"\n🔍 Testing: /api/votes/guest/{valid_uuid}")
    response = requests.post(f"{BASE_URL}/api/votes/guest/{valid_uuid}",
                           json={"value": 1},
                           headers={"Content-Type": "application/json"})
    print(f"  Response: {response.status_code} - {response.text[:100]}")

def test_valid_uuid_format():
    """Test with valid UUID format"""
    print("\n🧪 Testing Valid UUID Format")
    print("=" * 40)
    
    valid_uuid = "00000000-0000-0000-0000-000000000000"
    
    print(f"🔍 Testing with valid UUID: {valid_uuid}")
    
    # Test status endpoint
    response = requests.get(f"{BASE_URL}/api/votes/status/{valid_uuid}")
    print(f"  Status endpoint: {response.status_code} - {response.text[:100]}")
    
    # Test vote endpoint with valid data
    response = requests.post(f"{BASE_URL}/api/votes/{valid_uuid}",
                           json={"value": 1},
                           headers={"Content-Type": "application/json"})
    print(f"  Vote endpoint: {response.status_code} - {response.text[:100]}")

def main():
    print("🔒 Comprehensive Voting Endpoint Security Test")
    print("=" * 60)
    
    try:
        test_invalid_trip_ids()
        test_invalid_request_data()
        test_authentication_requirements()
        test_valid_uuid_format()
        
        print("\n✅ All tests completed!")
        print("\n📋 Expected Results:")
        print("- Invalid trip IDs should return 400 with clear error messages")
        print("- Invalid request data should return 400 with clear error messages")
        print("- Missing authentication should return 401")
        print("- Valid UUIDs should return appropriate responses (404 for non-existent trips)")
        
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    main() 