#!/usr/bin/env python3
"""
Simple test script to verify crawler functionality
"""
import requests
import json
import time

BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

def test_api_connection():
    """Test basic API connection"""
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"✓ API Connection: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ API Connection Failed: {e}")
        return False

def test_crawler_status():
    """Test crawler status endpoint"""
    try:
        response = requests.get(f"{API_BASE}/crawler/status")
        if response.status_code == 200:
            print(f"✓ Crawler Status: {response.json()}")
            return True
        else:
            print(f"✗ Crawler Status Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Crawler Status Error: {e}")
        return False

def test_crawler_accounts():
    """Test crawler accounts endpoint"""
    try:
        response = requests.get(f"{API_BASE}/crawler/accounts")
        if response.status_code == 200:
            accounts = response.json()
            print(f"✓ Crawler Accounts: Found {len(accounts)} accounts")
            for acc in accounts:
                print(f"  - {acc['username']}: {acc['status']}")
            return True
        else:
            print(f"✗ Crawler Accounts Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Crawler Accounts Error: {e}")
        return False

def test_start_crawler():
    """Test starting the crawler"""
    try:
        response = requests.post(f"{API_BASE}/crawler/start")
        if response.status_code == 200:
            print(f"✓ Crawler Started: {response.json()}")
            return True
        else:
            print(f"✗ Crawler Start Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Crawler Start Error: {e}")
        return False

def test_single_account():
    """Test a single account crawler"""
    try:
        response = requests.post(f"{API_BASE}/crawler/test/KR666")
        if response.status_code == 200:
            print(f"✓ Single Account Test: {response.json()}")
            return True
        else:
            print(f"✗ Single Account Test Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Single Account Test Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing XiaoBa Crawler System")
    print("=" * 50)
    
    # Test basic functionality
    if not test_api_connection():
        return
    
    if not test_crawler_status():
        return
    
    if not test_crawler_accounts():
        return
    
    # Test starting crawler
    print("\n📊 Testing Crawler Operations")
    print("-" * 30)
    
    if test_start_crawler():
        time.sleep(2)
        test_crawler_status()
    
    # Test single account
    print("\n🔍 Testing Single Account")
    print("-" * 30)
    test_single_account()
    
    print("\n✅ Testing Complete!")

if __name__ == "__main__":
    main()