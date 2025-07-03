import requests
import sys
import time
from datetime import datetime

class XiaoBaCrawlerTester:
    def __init__(self, base_url="https://11eec037-dfe1-4712-a198-90f6321ae770.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response.status_code != 204:  # No content
                    try:
                        return success, response.json()
                    except:
                        return success, {}
                return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'No detail provided')
                    print(f"Error detail: {error_detail}")
                except:
                    print("Could not parse error response")
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

    def test_get_crawler_status(self):
        """Test getting crawler status"""
        return self.run_test(
            "Get Crawler Status",
            "GET",
            "crawler/status",
            200
        )

    def test_get_crawler_accounts(self):
        """Test getting crawler accounts"""
        return self.run_test(
            "Get Crawler Accounts",
            "GET",
            "crawler/accounts",
            200
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

def main():
    # Setup
    tester = XiaoBaCrawlerTester()
    
    # Run tests
    print("=" * 50)
    print("XIAOBA CRAWLER API TESTS")
    print("=" * 50)
    
    # Test API root
    tester.test_root()
    
    # Test getting crawler status
    success, status_data = tester.test_get_crawler_status()
    if success:
        print(f"Crawler Status: {status_data}")
    
    # Test getting accounts
    success, accounts_data = tester.test_get_crawler_accounts()
    if success:
        print(f"Found {len(accounts_data)} accounts")
        if accounts_data:
            print(f"First account: {accounts_data[0]['username']}")
    
    # Test getting crawler data
    success, crawler_data = tester.test_get_crawler_data()
    if success:
        print(f"Found {len(crawler_data)} data records")
    
    # Test starting crawler
    tester.test_start_crawler()
    
    # Wait a bit for crawler to start
    print("Waiting for crawler to start...")
    time.sleep(2)
    
    # Test getting updated status
    success, updated_status = tester.test_get_crawler_status()
    if success:
        print(f"Updated Crawler Status: {updated_status}")
    
    # Test account testing (if accounts exist)
    if success and accounts_data and len(accounts_data) > 0:
        test_username = accounts_data[0]['username']
        tester.test_account_test(test_username)
    
    # Test CSV export
    tester.test_export_csv()
    
    # Test stopping crawler
    tester.test_stop_crawler()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 50)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())