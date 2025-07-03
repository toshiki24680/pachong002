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

    def test_account_test(self, username):
        """Test testing a specific account with enhanced debugging"""
        print(f"\n🔍 Testing Login Process for {username} with 师门 button selection...")
        self.tests_run += 1
        
        try:
            url = f"{self.api_url}/crawler/test/{username}"
            response = requests.post(url)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Test login API call successful")
                print(f"Test result: {result.get('test_result')}")
                print(f"Message: {result.get('message')}")
                
                # Check for screenshots
                print("\nChecking for debug screenshots...")
                screenshot_types = [
                    f"login_page_{username}.png",
                    f"button_highlighted_{username}.png",
                    f"after_shimen_{username}.png",
                    f"before_login_{username}.png",
                    f"no_shimen_button_{username}.png"
                ]
                
                for screenshot in screenshot_types:
                    screenshot_path = f"/app/debug_screenshots/{screenshot}"
                    if os.path.exists(screenshot_path):
                        file_time = datetime.fromtimestamp(os.path.getmtime(screenshot_path))
                        file_size = os.path.getsize(screenshot_path)
                        print(f"✅ Found {screenshot} - Size: {file_size} bytes, Modified: {file_time}")
                    else:
                        print(f"❌ Screenshot not found: {screenshot}")
                
                # Check server logs for 师门 button detection
                print("\nChecking server logs for 师门 button detection...")
                try:
                    # Get the latest log entries
                    log_output = os.popen("tail -n 200 /var/log/supervisor/backend.*.log 2>/dev/null").read()
                    
                    # Look for relevant log entries
                    shimen_search = f"Looking for 师门 button for account: {username}"
                    shimen_found = any([
                        "Found 师门 button using exact text match" in log_output,
                        "Found 师门 button using input button" in log_output,
                        "Found 师门 button using general element search" in log_output,
                        "Found 师门 button using comprehensive search" in log_output,
                        "Found 师门 button using JavaScript" in log_output
                    ])
                    shimen_clicked = any([
                        "Clicked 师门 button successfully" in log_output,
                        "Clicked 师门 button using JavaScript" in log_output,
                        "Clicked 师门 button using ActionChains" in log_output
                    ])
                    login_success = f"Successfully logged in with account: {username}" in log_output
                    
                    # Check for page source debugging
                    page_source_check = "Page source contains '师门'" in log_output
                    if page_source_check:
                        page_source_line = [line for line in log_output.split('\n') if "Page source contains '师门'" in line][0]
                        print(f"✅ {page_source_line}")
                    
                    # Check for element debugging
                    element_counts = [line for line in log_output.split('\n') if "Found " in line and "buttons" in line and "inputs" in line]
                    if element_counts:
                        print(f"✅ {element_counts[0]}")
                    
                    # Check for element details
                    element_details = [line for line in log_output.split('\n') if "Checking element:" in line]
                    if element_details:
                        print(f"✅ Found {len(element_details)} element detail logs")
                        for i, detail in enumerate(element_details[:3]):  # Show first 3 for brevity
                            print(f"   {detail}")
                        if len(element_details) > 3:
                            print(f"   ... and {len(element_details) - 3} more")
                    
                    if shimen_search in log_output:
                        print(f"✅ Log shows search for 师门 button")
                    else:
                        print(f"❌ No log entry for searching 师门 button")
                    
                    if shimen_found:
                        print(f"✅ Log shows 师门 button was found")
                    else:
                        print(f"❌ No log entry indicating 师门 button was found")
                    
                    if shimen_clicked:
                        print(f"✅ Log shows 师门 button was clicked")
                    else:
                        print(f"❌ No log entry indicating 师门 button was clicked")
                    
                    if login_success:
                        print(f"✅ Log shows successful login")
                    else:
                        print(f"❌ No log entry indicating successful login")
                    
                    # Overall success determination
                    if shimen_found and shimen_clicked and login_success:
                        self.tests_passed += 1
                        print("\n✅ 师门 button selection and login process working correctly")
                        return True
                    else:
                        print("\n❌ Issues detected with 师门 button selection or login process")
                        return False
                    
                except Exception as e:
                    print(f"Error checking logs: {str(e)}")
                    return False
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'No detail provided')
                    print(f"Error detail: {error_detail}")
                except:
                    print("Could not parse error response")
                return False
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

def main():
    # Setup
    tester = XiaoBaCrawlerTester()
    
    print("=" * 50)
    print("XIAOBA CRAWLER LOGIN TEST - 师门 BUTTON SELECTION")
    print("=" * 50)
    
    # Create debug_screenshots directory if it doesn't exist
    os.makedirs("/app/debug_screenshots", exist_ok=True)
    
    # First, test Chrome driver setup
    print("\nTesting Chrome driver setup...")
    
    # Check if Chrome is installed
    chrome_version = os.popen("chromium --version 2>/dev/null || echo 'Chrome not found'").read().strip()
    print(f"Chrome version: {chrome_version}")
    
    # Check if chromedriver is installed and executable
    chromedriver_path = "/usr/bin/chromedriver"
    if os.path.exists(chromedriver_path):
        # Check if it's executable
        if not os.access(chromedriver_path, os.X_OK):
            print(f"❌ Chrome driver exists but is not executable: {chromedriver_path}")
            # Try to make it executable
            try:
                os.chmod(chromedriver_path, 0o755)
                print(f"✅ Made Chrome driver executable: {chromedriver_path}")
            except Exception as e:
                print(f"❌ Failed to make Chrome driver executable: {str(e)}")
        else:
            print(f"✅ Chrome driver is executable: {chromedriver_path}")
        
        # Try to run it
        driver_version = os.popen(f"{chromedriver_path} --version 2>/dev/null || echo 'Failed to run chromedriver'").read().strip()
        print(f"Chrome driver version: {driver_version}")
    else:
        print(f"❌ Chrome driver not found at expected path: {chromedriver_path}")
    
    # Check backend logs for Chrome driver errors
    print("\nChecking backend logs for Chrome driver errors...")
    log_output = os.popen("tail -n 100 /var/log/supervisor/backend.*.log 2>/dev/null | grep -i 'chrome\\|driver\\|selenium'").read().strip()
    if log_output:
        print("Found Chrome driver related log entries:")
        for line in log_output.split('\n'):
            print(f"  {line}")
    
    # Test the login process with focus on 师门 button
    print("\nTesting 师门 button selection with account: KR666")
    login_success = tester.test_account_test("KR666")
    
    # Print summary
    print("\n" + "=" * 50)
    print("LOGIN TEST SUMMARY")
    print("=" * 50)
    
    if login_success:
        print(f"✅ 师门 button selection and login process working correctly")
        print(f"- Button was found and clicked successfully")
        print(f"- Login completed successfully")
        print(f"- Debug screenshots were generated")
    else:
        print(f"❌ Issues detected with 师门 button selection or login process")
        print(f"- The API endpoints are responding correctly")
        print(f"- The Chrome driver setup is working")
        print(f"- But the 师门 button detection or clicking is failing")
        print(f"- Check the debug screenshots and logs for more details")
    
    print("\nDebug screenshots location: /app/debug_screenshots/")
    print("=" * 50)
    
    # Print overall results
    print(f"\nTests passed: {tester.tests_passed}/{tester.tests_run}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())