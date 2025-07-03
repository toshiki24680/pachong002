from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import time
import logging
import os

def enhance_login_method(driver, account, config, logger):
    """Enhanced login method with better 师门 button detection"""
    try:
        driver.get(config.target_url)
        
        # Wait for login page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Take a screenshot for debugging
        try:
            driver.save_screenshot(f"/app/debug_screenshots/login_page_{account.username}.png")
            logger.info(f"Saved login page screenshot for {account.username}")
        except:
            pass
        
        # Wait a moment for page to fully load
        time.sleep(3)
        
        # First, click the "师门" button as required
        logger.info(f"Looking for 师门 button for account: {account.username}")
        师门_button = None
        
        # Enhanced strategies to find the 师门 button
        try:
            # Strategy 1: Look for button with exact text "师门"
            师门_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space(text())='师门']"))
            )
            logger.info("Found 师门 button using exact text match")
        except Exception as e:
            logger.info(f"Strategy 1 failed: {str(e)}")
            try:
                # Strategy 2: Look for input type button with value "师门"
                师门_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@type='button' and @value='师门']"))
                )
                logger.info("Found 师门 button using input button")
            except Exception as e:
                logger.info(f"Strategy 2 failed: {str(e)}")
                try:
                    # Strategy 3: Look for any clickable element containing "师门"
                    师门_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '师门') and (name()='button' or name()='input' or name()='a' or name()='div')]"))
                    )
                    logger.info("Found 师门 button using general element search")
                except Exception as e:
                    logger.info(f"Strategy 3 failed: {str(e)}")
                    try:
                        # Strategy 4: Look by class or other attributes that might indicate login type selection
                        # Get page source for debugging
                        page_source = driver.page_source
                        logger.info(f"Page source contains '师门': {'师门' in page_source}")
                        
                        # Try to find all buttons and links
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        inputs = driver.find_elements(By.TAG_NAME, "input")
                        links = driver.find_elements(By.TAG_NAME, "a")
                        divs = driver.find_elements(By.TAG_NAME, "div")
                        
                        logger.info(f"Found {len(buttons)} buttons, {len(inputs)} inputs, {len(links)} links, {len(divs)} divs")
                        
                        all_elements = buttons + inputs + links + divs
                        
                        for element in all_elements:
                            try:
                                element_text = element.text.strip() if element.text else ""
                                element_value = element.get_attribute('value') or ""
                                element_class = element.get_attribute('class') or ""
                                element_id = element.get_attribute('id') or ""
                                
                                logger.info(f"Checking element: {element.tag_name}, text: '{element_text}', value: '{element_value}', class: '{element_class}', id: '{element_id}'")
                                
                                if "师门" in element_text or "师门" in element_value:
                                    师门_button = element
                                    logger.info(f"Found 师门 button using comprehensive search: {element.tag_name}")
                                    break
                            except Exception as elem_e:
                                logger.warning(f"Error checking element: {str(elem_e)}")
                    except Exception as e:
                        logger.warning(f"Error in comprehensive button search: {str(e)}")
                        
                        # Last resort: Try JavaScript to find and click the button
                        try:
                            logger.info("Attempting to find 师门 button using JavaScript")
                            # Try to find elements with text containing 师门
                            elements_with_text = driver.execute_script("""
                                var elements = [];
                                var allElements = document.querySelectorAll('*');
                                for (var i = 0; i < allElements.length; i++) {
                                    if (allElements[i].textContent.includes('师门')) {
                                        elements.push(allElements[i]);
                                    }
                                }
                                return elements;
                            """)
                            
                            if elements_with_text:
                                logger.info(f"Found {len(elements_with_text)} elements with text containing 师门 using JavaScript")
                                师门_button = elements_with_text[0]
                            else:
                                logger.warning("No elements with text containing 师门 found using JavaScript")
                        except Exception as js_e:
                            logger.warning(f"Error in JavaScript search: {str(js_e)}")
        
        if 师门_button:
            try:
                # Scroll to the button to ensure it's visible
                driver.execute_script("arguments[0].scrollIntoView(true);", 师门_button)
                time.sleep(1)
                
                # Highlight the button for debugging
                driver.execute_script("arguments[0].style.border='3px solid red';", 师门_button)
                
                # Take a screenshot after highlighting
                try:
                    driver.save_screenshot(f"/app/debug_screenshots/button_highlighted_{account.username}.png")
                    logger.info(f"Saved button highlighted screenshot for {account.username}")
                except Exception as e:
                    logger.warning(f"Error saving highlighted button screenshot: {str(e)}")
                
                # Try regular click first
                try:
                    师门_button.click()
                    logger.info("Clicked 师门 button successfully")
                except Exception as click_error:
                    logger.warning(f"Regular click failed: {str(click_error)}")
                    # Try JavaScript click if regular click fails
                    try:
                        driver.execute_script("arguments[0].click();", 师门_button)
                        logger.info("Clicked 师门 button using JavaScript")
                    except Exception as js_error:
                        logger.error(f"JavaScript click failed: {str(js_error)}")
                        
                        # Last resort: Try ActionChains
                        try:
                            actions = ActionChains(driver)
                            actions.move_to_element(师门_button).click().perform()
                            logger.info("Clicked 师门 button using ActionChains")
                        except Exception as action_error:
                            logger.error(f"ActionChains click failed: {str(action_error)}")
            except Exception as e:
                logger.error(f"Error interacting with 师门 button: {str(e)}")
            
            # Wait for the form to update after selecting 师门
            time.sleep(2)
            
            # Take another screenshot after clicking 师门
            try:
                driver.save_screenshot(f"/app/debug_screenshots/after_shimen_{account.username}.png")
                logger.info(f"Saved post-师门 screenshot for {account.username}")
            except Exception as e:
                logger.warning(f"Error saving post-师门 screenshot: {str(e)}")
                
        else:
            logger.error("Could not find 师门 button! This might cause login to fail.")
            # Take screenshot of the current page for debugging
            try:
                driver.save_screenshot(f"/app/debug_screenshots/no_shimen_button_{account.username}.png")
                logger.info(f"Saved no-师门-button screenshot for debugging")
            except Exception as e:
                logger.warning(f"Error saving no-师门-button screenshot: {str(e)}")
        
        # Wait for login form to be available after selecting 师门
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        # Fill in username and password
        username_field = driver.find_element(By.NAME, "username")
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.clear()
        username_field.send_keys(account.username)
        
        password_field.clear()
        password_field.send_keys(account.password)
        
        # Take screenshot before clicking login
        try:
            driver.save_screenshot(f"/app/debug_screenshots/before_login_{account.username}.png")
            logger.info(f"Saved before-login screenshot for {account.username}")
        except Exception as e:
            logger.warning(f"Error saving before-login screenshot: {str(e)}")
        
        # Find and click login button - try multiple strategies
        login_clicked = False
        try:
            # Strategy 1: Look for submit button
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            login_button.click()
            login_clicked = True
            logger.info("Clicked login button using submit selector")
        except Exception as e:
            logger.info(f"Submit button click failed: {str(e)}")
            try:
                # Strategy 2: Look for button with login-related text
                login_button = driver.find_element(By.XPATH, "//button[contains(text(), '登录') or contains(text(), '登錄') or contains(text(), 'Login')]")
                login_button.click()
                login_clicked = True
                logger.info("Clicked login button using text search")
            except Exception as e:
                logger.info(f"Text button click failed: {str(e)}")
                try:
                    # Strategy 3: Look for input with login-related value
                    login_button = driver.find_element(By.XPATH, "//input[@value='登录' or @value='登錄' or @value='Login']")
                    login_button.click()
                    login_clicked = True
                    logger.info("Clicked login button using input value")
                except Exception as e:
                    logger.info(f"Input value button click failed: {str(e)}")
                    # Strategy 4: Find all buttons and look for login-related ones
                    try:
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        inputs = driver.find_elements(By.XPATH, "//input[@type='button' or @type='submit']")
                        
                        for element in buttons + inputs:
                            try:
                                text = element.text.strip() if element.text else ""
                                value = element.get_attribute('value') or ""
                                
                                if any(keyword in text.lower() or keyword in value.lower() for keyword in ['登录', '登錄', 'login', '确定', '提交']):
                                    element.click()
                                    login_clicked = True
                                    logger.info(f"Clicked login button using comprehensive search: {text or value}")
                                    break
                            except Exception as elem_e:
                                logger.warning(f"Error checking login element: {str(elem_e)}")
                    except Exception as e:
                        logger.error(f"Comprehensive login button search failed: {str(e)}")
        
        if not login_clicked:
            logger.error("Could not find login button!")
            try:
                driver.save_screenshot(f"/app/debug_screenshots/no_login_button_{account.username}.png")
            except Exception as e:
                logger.warning(f"Error saving no-login-button screenshot: {str(e)}")
            return False
        
        # Wait for successful login - check if we're redirected or if login form disappears
        WebDriverWait(driver, 10).until(
            lambda driver: driver.current_url != config.target_url or 
            len(driver.find_elements(By.NAME, "username")) == 0
        )
        
        logger.info(f"Successfully logged in with account: {account.username}")
        return True
        
    except TimeoutException:
        logger.error(f"Login timeout for account: {account.username}")
        return False
    except Exception as e:
        logger.error(f"Login error for account {account.username}: {str(e)}")
        return False