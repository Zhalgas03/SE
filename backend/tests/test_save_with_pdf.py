#!/usr/bin/env python3
"""
Test script for the save-with-pdf endpoint
"""

import requests
import json
import base64
import os

def test_save_with_pdf():
    """Test the save-with-pdf endpoint"""
    
    # Test data
    test_data = {
        "name": "Test Trip with PDF",
        "date_start": "2025-07-10",
        "date_end": "2025-07-15",
        "pdf_base64": "data:application/pdf;base64,JVBERi0xLjQKJcOkw7zDtsO8DQoxIDAgb2JqDQo8PA0KL1R5cGUgL0NhdGFsb2cNCi9QYWdlcyAyIDAgUg0KPj4NCmVuZG9iag0KMiAwIG9iag0KPDwNCi9UeXBlIC9QYWdlcw0KL0NvdW50IDENCi9LaWRzIFsgMyAwIFIgXQ0KPj4NCmVuZG9iag0KMyAwIG9iag0KPDwNCi9UeXBlIC9QYWdlDQovUGFyZW50IDIgMCBSDQovUmVzb3VyY2VzIDw8DQovRm9udCA8PA0KL0YxIDQgMCBSDQo+Pg0KPj4NCi9Db250ZW50cyA1IDAgUg0KL01lZGlhQm94IFsgMCAwIDYxMiA3OTIgXQ0KPj4NCmVuZG9iag0KNCAwIG9iag0KPDwNCi9UeXBlIC9Gb250DQovU3VidHlwZSAvVHlwZTENCi9CYXNlRm9udCAvSGVsdmV0aWNhDQovRW5jb2RpbmcgL1dpbkFuc2lFbmNvZGluZw0KPj4NCmVuZG9iag0KNSAwIG9iag0KPDwNCi9MZW5ndGggNDQNCj4+DQpzdHJlYW0NCkJUCjcwIDUwIFRECi9GMSAxMiBUZgooSGVsbG8gV29ybGQhKSBUagpFVAplbmRzdHJlYW0NCmVuZG9iag0KeHJlZg0KMCA2DQowMDAwMDAwMDAwIDY1NTM1IGYNCjAwMDAwMDAwMTAgMDAwMDAgbg0KMDAwMDAwMDA3OSAwMDAwMCBuDQowMDAwMDAwMTczIDAwMDAwIG4NCjAwMDAwMDAzMDEgMDAwMDAgbg0KMDAwMDAwMDM4MCAwMDAwMCBuDQp0cmFpbGVyDQo8PA0KL1NpemUgNg0KL1Jvb3QgMSAwIFINCj4+DQpzdGFydHhyZWYNCjQ5Mg0KJSVFT0Y="
    }
    
    # First, get a JWT token (you'll need to login first)
    print("🔍 Testing save-with-pdf endpoint")
    print("=" * 50)
    
    # Test without authentication
    print("1. Testing without authentication...")
    response = requests.post(
        "http://localhost:5001/api/trips/save-with-pdf",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    # Test with invalid data
    print("\n2. Testing with invalid data...")
    invalid_data = {"name": "Test"}
    response = requests.post(
        "http://localhost:5001/api/trips/save-with-pdf",
        json=invalid_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    # Test with non-JSON data
    print("\n3. Testing with non-JSON data...")
    response = requests.post(
        "http://localhost:5001/api/trips/save-with-pdf",
        data="not json",
        headers={"Content-Type": "text/plain"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    print("\n✅ Test completed!")
    print("\nTo test with authentication:")
    print("1. Login to get a JWT token")
    print("2. Add Authorization: Bearer <token> header")
    print("3. Send the same test request")

if __name__ == "__main__":
    test_save_with_pdf() 