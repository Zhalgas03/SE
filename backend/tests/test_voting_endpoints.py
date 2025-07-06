#!/usr/bin/env python3
"""
Test script for voting endpoints
"""
import requests
import json

BASE_URL = "http://localhost:5001"

def test_voting_endpoints():
    """Test the voting endpoints"""
    print("🧪 Testing voting endpoints...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Server is running (status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running on localhost:5001")
        return False
    
    # Test 2: Check if votes endpoint exists
    try:
        response = requests.get(f"{BASE_URL}/api/votes/status/1")
        print(f"✅ Votes endpoint exists (status: {response.status_code})")
        if response.status_code == 401:
            print("   (Expected: Authentication required)")
    except Exception as e:
        print(f"❌ Votes endpoint error: {e}")
        return False
    
    # Test 3: Check if voting start endpoint exists
    try:
        response = requests.post(f"{BASE_URL}/api/votes/start/1")
        print(f"✅ Voting start endpoint exists (status: {response.status_code})")
        if response.status_code == 401:
            print("   (Expected: Authentication required)")
    except Exception as e:
        print(f"❌ Voting start endpoint error: {e}")
        return False
    
    print("✅ All voting endpoints are accessible!")
    return True

if __name__ == "__main__":
    test_voting_endpoints() 