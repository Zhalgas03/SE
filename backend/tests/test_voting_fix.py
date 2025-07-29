#!/usr/bin/env python3
"""
Comprehensive test script to verify voting endpoints work correctly after the JSON parsing fix.
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:5001"

def test_endpoint(method, url, headers=None, data=None, expected_status=200, description=""):
    """Test an endpoint and return success status"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        print(f"🎯 {description}")
        print(f"   URL: {method} {url}")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == expected_status:
            print(f"   ✅ SUCCESS")
            return True
        else:
            print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def main():
    print("🧪 COMPREHENSIVE VOTING ENDPOINT TEST")
    print("=" * 50)
    
    # Test 1: Basic test endpoint (no auth required)
    print("\n1️⃣ Testing basic endpoint...")
    success1 = test_endpoint(
        "GET", 
        f"{BASE_URL}/api/votes/test",
        description="Basic test endpoint"
    )
    
    # Test 2: Vote status endpoint (auth required - will fail but should not crash)
    print("\n2️⃣ Testing vote status endpoint...")
    success2 = test_endpoint(
        "GET", 
        f"{BASE_URL}/api/votes/status/7fdbb665-9b68-4ede-aa87-7b0a5303f9c1",
        expected_status=401,
        description="Vote status endpoint (should fail auth but not crash)"
    )
    
    # Test 3: Start voting session endpoint (auth required - will fail but should not crash)
    print("\n3️⃣ Testing start voting session endpoint...")
    success3 = test_endpoint(
        "POST", 
        f"{BASE_URL}/api/votes/start/7fdbb665-9b68-4ede-aa87-7b0a5303f9c1",
        expected_status=401,
        description="Start voting session endpoint (should fail auth but not crash)"
    )
    
    # Test 4: Vote submission endpoint (auth required - will fail but should not crash)
    print("\n4️⃣ Testing vote submission endpoint...")
    success4 = test_endpoint(
        "POST", 
        f"{BASE_URL}/api/votes/7fdbb665-9b68-4ede-aa87-7b0a5303f9c1",
        data={"value": 1},
        expected_status=401,
        description="Vote submission endpoint (should fail auth but not crash)"
    )
    
    # Test 5: Guest vote endpoint (no auth required)
    print("\n5️⃣ Testing guest vote endpoint...")
    success5 = test_endpoint(
        "POST", 
        f"{BASE_URL}/api/votes/guest/7fdbb665-9b68-4ede-aa87-7b0a5303f9c1",
        data={"value": 1},
        expected_status=201,
        description="Guest vote endpoint"
    )
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    tests = [
        ("Basic endpoint", success1),
        ("Vote status endpoint", success2),
        ("Start voting session endpoint", success3),
        ("Vote submission endpoint", success4),
        ("Guest vote endpoint", success5)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The voting system is working correctly.")
        print("✅ The JSON parsing fix resolved the 400 errors.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 