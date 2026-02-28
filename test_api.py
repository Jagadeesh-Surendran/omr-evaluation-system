#!/usr/bin/env python3
"""
API Testing Script for OMR Evaluation System
Tests all critical endpoints after frontend file upload changes
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_evaluate_batch_validation():
    """Test evaluate_batch endpoint with missing parameters"""
    print("\n=== Testing Evaluate Batch (Validation) ===")
    try:
        # Test with missing files
        response = requests.post(f"{BASE_URL}/api/evaluate_batch")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Should return 400 for missing files
        return response.status_code == 400
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_extract_key_validation():
    """Test extract_key endpoint with missing file"""
    print("\n=== Testing Extract Key (Validation) ===")
    try:
        response = requests.post(f"{BASE_URL}/api/extract_key")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Should return 400 for missing file
        return response.status_code == 400
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_export_validation():
    """Test export endpoint with empty results"""
    print("\n=== Testing Export (Validation) ===")
    try:
        data = {"results": []}
        response = requests.post(
            f"{BASE_URL}/api/export?format=csv",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        
        # Should handle empty results gracefully
        if response.status_code == 200:
            print(f"Response: CSV file generated")
            return True
        else:
            print(f"Response: {response.json()}")
            return response.status_code in [200, 400]
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_link_db_validation():
    """Test link_db endpoint with missing parameters"""
    print("\n=== Testing Link DB (Validation) ===")
    try:
        response = requests.post(f"{BASE_URL}/api/link_db")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Should return 400 for missing parameters
        return response.status_code == 400
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("OMR Evaluation System - API Test Suite")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health),
        ("Evaluate Batch Validation", test_evaluate_batch_validation),
        ("Extract Key Validation", test_extract_key_validation),
        ("Export Validation", test_export_validation),
        ("Link DB Validation", test_link_db_validation),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
