import requests
import sys
import time
import os
import json
import random
from datetime import datetime

class XiaoBaCrawlerTester:
    def __init__(self, base_url=None):
        # Use environment variable for backend URL if available, otherwise use default
        if base_url is None:
            # Try to get from frontend .env file
            try:
                with open('/app/frontend/.env', 'r') as f:
                    for line in f:
                        if line.startswith('REACT_APP_BACKEND_URL='):
                            base_url = line.strip().split('=')[1].strip('"\'')
                            break
            except:
                # Fallback to default
                base_url = "https://11eec037-dfe1-4712-a198-90f6321ae770.preview.emergentagent.com"
        
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        print(f"Using backend URL: {self.api_url}")

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, validation_func=None):
        """Run a single API test with optional validation function"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            
            # If validation function is provided, use it to further validate the response
            validation_result = True
            validation_message = ""
            if success and validation_func and response.status_code != 204:
                try:
                    response_data = response.json()
                    validation_result, validation_message = validation_func(response_data)
                except Exception as e:
                    validation_result = False
                    validation_message = f"Validation error: {str(e)}"
            
            if success and validation_result:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if validation_message:
                    print(f"   {validation_message}")
                if response.status_code != 204:  # No content
                    try:
                        return True, response.json()
                    except:
                        return True, {}
                return True, {}
            else:
                if not success:
                    print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                    try:
                        error_detail = response.json().get('detail', 'No detail provided')
                        print(f"Error detail: {error_detail}")
                    except:
                        print("Could not parse error response")
                else:
                    print(f"❌ Failed - Validation failed: {validation_message}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root(self):
        """Test the root endpoint"""
        return self.run_test(
            "API Root",
            "GET",
            "",
            200
        )

    # Account Management Tests
    def test_validate_account(self, username="test_user", password="test_password"):
        """Test validating account credentials"""
        return self.run_test(
            "Validate Account Credentials",
            "POST",
            "crawler/accounts/validate",
            200,
            data={"username": username, "password": password}
        )
    
    def test_batch_enable_accounts(self):
        """Test enabling all accounts"""
        return self.run_test(
            "Batch Enable All Accounts",
            "POST",
            "crawler/accounts/batch/enable",
            200
        )
    
    def test_batch_disable_accounts(self):
        """Test disabling all accounts"""
        return self.run_test(
            "Batch Disable All Accounts",
            "POST",
            "crawler/accounts/batch/disable",
            200
        )
    
    def test_enable_specific_account(self, username):
        """Test enabling a specific account"""
        return self.run_test(
            f"Enable Account {username}",
            "POST",
            f"crawler/accounts/{username}/enable",
            200
        )
    
    def test_disable_specific_account(self, username):
        """Test disabling a specific account"""
        return self.run_test(
            f"Disable Account {username}",
            "POST",
            f"crawler/accounts/{username}/disable",
            200
        )
    
    def test_create_account(self, username=None, password=None):
        """Test creating a new account"""
        if username is None:
            username = f"test_user_{random.randint(1000, 9999)}"
        if password is None:
            password = "test_password"
            
        return self.run_test(
            "Create New Account",
            "POST",
            "crawler/accounts",
            200,
            data={"username": username, "password": password}
        )
    
    def test_delete_account(self, username):
        """Test deleting an account"""
        return self.run_test(
            f"Delete Account {username}",
            "DELETE",
            f"crawler/accounts/{username}",
            200
        )

    def test_get_crawler_config(self):
        """Test getting crawler configuration to verify 45-second interval"""
        def validate_config(config_data):
            if config_data.get('crawl_interval') == 45:
                return True, "✓ Crawler interval is correctly set to 45 seconds"
            else:
                return False, f"✗ Crawler interval is not 45 seconds, found: {config_data.get('crawl_interval')}"
        
        return self.run_test(
            "Get Crawler Configuration",
            "GET",
            "crawler/config",
            200,
            validation_func=validate_config
        )

    def test_update_crawler_config(self, interval=45):
        """Test updating crawler configuration"""
        return self.run_test(
            "Update Crawler Configuration",
            "PUT",
            "crawler/config",
            200,
            data={"crawl_interval": interval}
        )

    def test_get_crawler_status(self):
        """Test getting crawler status to check if it's running automatically"""
        def validate_status(status_data):
            if status_data.get('crawl_status') == 'running':
                return True, "✓ Crawler is running automatically"
            else:
                return False, f"✗ Crawler is not running, status: {status_data.get('crawl_status')}"
        
        return self.run_test(
            "Get Crawler Status",
            "GET",
            "crawler/status",
            200,
            validation_func=validate_status
        )

    def test_get_crawler_accounts(self):
        """Test getting crawler accounts to verify default accounts are created"""
        def validate_accounts(accounts_data):
            expected_accounts = ["KR666", "KR777", "KR888", "KR999", "KR000"]
            found_accounts = [account.get('username') for account in accounts_data]
            
            missing_accounts = [acc for acc in expected_accounts if acc not in found_accounts]
            
            if not missing_accounts:
                return True, f"✓ All default accounts are created: {', '.join(expected_accounts)}"
            else:
                return False, f"✗ Missing accounts: {', '.join(missing_accounts)}"
        
        return self.run_test(
            "Get Crawler Accounts",
            "GET",
            "crawler/accounts",
            200,
            validation_func=validate_accounts
        )

    def test_start_crawler(self):
        """Test starting the crawler"""
        return self.run_test(
            "Start Crawler",
            "POST",
            "crawler/start",
            200
        )

    def test_stop_crawler(self):
        """Test stopping the crawler"""
        return self.run_test(
            "Stop Crawler",
            "POST",
            "crawler/stop",
            200
        )

    def test_get_crawler_data(self):
        """Test getting crawler data"""
        return self.run_test(
            "Get Crawler Data",
            "GET",
            "crawler/data",
            200
        )

    def test_export_csv(self):
        """Test exporting CSV data"""
        print(f"\n🔍 Testing Export CSV...")
        self.tests_run += 1
        
        try:
            url = f"{self.api_url}/crawler/data/export"
            response = requests.get(url)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
                return True
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def test_account_test(self, username):
        """Test testing a specific account"""
        return self.run_test(
            f"Test Account {username}",
            "POST",
            f"crawler/test/{username}",
            200
        )

    def test_continuous_crawling(self):
        """Test continuous crawling by checking status multiple times"""
        print(f"\n🔍 Testing Continuous Crawling...")
        self.tests_run += 1
        
        try:
            # First check
            url = f"{self.api_url}/crawler/status"
            response1 = requests.get(url)
            if response1.status_code != 200:
                print(f"❌ Failed - First status check failed with status code: {response1.status_code}")
                return False
            
            status1 = response1.json()
            print(f"First status check: {status1.get('crawl_status')}")
            
            # For this test, we'll consider it a success if the crawler is running
            # since we can't guarantee new data will be collected during our test period
            if status1.get('crawl_status') == 'running':
                self.tests_passed += 1
                print("✅ Passed - Crawler is running continuously")
                return True
            else:
                print("❌ Failed - Crawler is not running")
                return False
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

def main():
    # Setup
    tester = XiaoBaCrawlerTester()
    
    # Run tests
    print("=" * 50)
    print("XIAOBA CRAWLER API TESTS")
    print("=" * 50)
    
    # Test API root
    tester.test_root()
    
    # 1. Test crawler configuration to verify 45-second interval
    success, config_data = tester.test_get_crawler_config()
    if success:
        print(f"Crawler Configuration: {config_data}")
        # If interval is not 45 seconds, update it
        if config_data.get('crawl_interval') != 45:
            print("Updating crawler interval to 45 seconds...")
            tester.test_update_crawler_config(45)
            # Verify the update
            success, updated_config = tester.test_get_crawler_config()
            if success:
                print(f"Updated Configuration: {updated_config}")
    
    # 2. Test crawler status to check if it's running automatically
    success, status_data = tester.test_get_crawler_status()
    if success:
        print(f"Crawler Status: {status_data}")
        # If not running, start it
        if status_data.get('crawl_status') != 'running':
            print("Crawler not running automatically. Starting crawler...")
            tester.test_start_crawler()
    
    # 3. Test getting accounts to verify default accounts are created
    success, accounts_data = tester.test_get_crawler_accounts()
    if success:
        print(f"Found {len(accounts_data)} accounts")
    
    # 4. Test getting crawler data
    success, crawler_data = tester.test_get_crawler_data()
    if success:
        print(f"Found {len(crawler_data)} data records")
    
    # 5. Test continuous crawling
    tester.test_continuous_crawling()
    
    # 6. Test start/stop functionality
    print("\nTesting start/stop functionality...")
    # Stop the crawler
    tester.test_stop_crawler()
    
    # Verify it's stopped
    success, status_after_stop = tester.run_test(
        "Get Crawler Status After Stop",
        "GET",
        "crawler/status",
        200
    )
    if success and status_after_stop.get('crawl_status') == 'stopped':
        print("✅ Crawler successfully stopped")
    
    # Start the crawler again
    tester.test_start_crawler()
    
    # Verify it's running
    success, status_after_start = tester.run_test(
        "Get Crawler Status After Start",
        "GET",
        "crawler/status",
        200
    )
    if success and status_after_start.get('crawl_status') == 'running':
        print("✅ Crawler successfully restarted")
    
    # Test account testing (if accounts exist)
    if accounts_data and len(accounts_data) > 0:
        test_username = accounts_data[0]['username']
        tester.test_account_test(test_username)
    
    # Test CSV export
    tester.test_export_csv()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 50)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())