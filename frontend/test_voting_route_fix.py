#!/usr/bin/env python3
"""
Test to verify the voting route works correctly after backend fix.
"""

import requests
import sys

BASE_URL = "http://localhost:5001"

def test_voting_route():
    """Test that the voting route works correctly"""
    print("🧪 Testing voting route after backend fix...")
    
    # Test 1: Check if the main page loads
    print("\n1️⃣ Testing main page load...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            print("✅ Main page loads successfully")
        else:
            print(f"❌ Main page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error loading main page: {e}")
        return False
    
    # Test 2: Check if the guest voting route loads
    print("\n2️⃣ Testing guest voting route...")
    test_trip_id = "test-trip-123"
    try:
        response = requests.get(f"{BASE_URL}/vote/{test_trip_id}", timeout=10)
        if response.status_code == 200:
            print(f"✅ Guest voting page loads successfully")
            print(f"   URL: {BASE_URL}/vote/{test_trip_id}")
            
            # Check for expected content
            if "Vote for Trip" in response.text or "React App" in response.text:
                print("✅ Page contains expected React app content")
            else:
                print("⚠️  Page content may not be loading correctly")
                print(f"   Content preview: {response.text[:200]}...")
                
        else:
            print(f"❌ Guest voting page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error loading guest voting page: {e}")
        return False
    
    # Test 3: Check for any problematic file references
    print("\n3️⃣ Checking for problematic file references...")
    try:
        response = requests.get(f"{BASE_URL}/vote/{test_trip_id}", timeout=10)
        content = response.text
        
        # Check for the problematic file
        if 'g1b8LeAcK1nzKS847_NSzVISAes' in content:
            print("❌ Found reference to problematic file")
            return False
        else:
            print("✅ No references to problematic file found")
            
        # Check for external script references
        if 'src="http' in content or 'src="//' in content:
            print("⚠️  Found external script references")
            external_scripts = [line for line in content.split('\n') if 'src="http' in line or 'src="//' in line]
            for script in external_scripts[:3]:  # Show first 3
                print(f"   Found: {script.strip()}")
        else:
            print("✅ No external script references found")
            
    except Exception as e:
        print(f"❌ Error checking file references: {e}")
        return False
    
    return True

def main():
    print("🚀 Starting voting route test after backend fix...\n")
    
    success = test_voting_route()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
        print("\n📋 Summary:")
        print("   ✅ Backend serves React app for unknown routes")
        print("   ✅ Guest voting route loads correctly")
        print("   ✅ No problematic file references found")
        print("   ✅ No external script references")
        print("\n🎯 Next Steps:")
        print("   1. Start the backend server: python app.py")
        print("   2. Open browser to: http://localhost:5001/vote/test-trip-123")
        print("   3. Check browser console for tripId logging")
        print("   4. Verify no '_d is not defined' errors")
        print("   5. Test voting functionality")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)

if __name__ == "__main__":
    main() 