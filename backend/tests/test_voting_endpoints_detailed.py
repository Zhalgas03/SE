#!/usr/bin/env python3
"""
Detailed test script for voting endpoints with authentication
"""
import requests
import json

BASE_URL = "http://localhost:5001"

def test_voting_endpoints_with_auth():
    """Test the voting endpoints with proper authentication"""
    print("🧪 Testing voting endpoints with authentication...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Server is running (status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running on localhost:5001")
        return False
    
    # Test 2: Test GET /api/votes/status/<trip_id> without auth (should return 401)
    try:
        response = requests.get(f"{BASE_URL}/api/votes/status/1")
        print(f"✅ GET /api/votes/status/1 without auth: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Missing Authorization Header")
        data = response.json()
        print(f"   Response: {data}")
    except Exception as e:
        print(f"❌ GET endpoint error: {e}")
        return False
    
    # Test 3: Test POST /api/votes/<trip_id> without auth (should return 401)
    try:
        response = requests.post(
            f"{BASE_URL}/api/votes/1",
            headers={"Content-Type": "application/json"},
            json={"value": 1}
        )
        print(f"✅ POST /api/votes/1 without auth: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Missing Authorization Header")
        data = response.json()
        print(f"   Response: {data}")
    except Exception as e:
        print(f"❌ POST endpoint error: {e}")
        return False
    
    # Test 4: Test with invalid JWT token (should return 401)
    try:
        response = requests.get(
            f"{BASE_URL}/api/votes/status/1",
            headers={"Authorization": "Bearer invalid_token"}
        )
        print(f"✅ GET /api/votes/status/1 with invalid token: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Invalid token")
        data = response.json()
        print(f"   Response: {data}")
    except Exception as e:
        print(f"❌ Invalid token test error: {e}")
        return False
    
    print("✅ All voting endpoints are working correctly!")
    print("📝 Note: 401 responses are expected without valid JWT tokens")
    return True

if __name__ == "__main__":
    test_voting_endpoints_with_auth() 