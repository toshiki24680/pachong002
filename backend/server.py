from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import asyncio
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pandas as pd
import io
import re
from bs4 import BeautifulSoup
import time
from concurrent.futures import ThreadPoolExecutor
import threading

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Global variables for crawler management
active_crawlers = {}
crawler_data = {}
scheduler = AsyncIOScheduler()
websocket_connections = set()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class CrawlerAccount(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password: str
    status: str = "inactive"  # active, inactive, error
    last_crawl: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CrawlerAccountCreate(BaseModel):
    username: str
    password: str

class CrawlerData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_username: str
    sequence_number: int
    ip: str
    type: str
    name: str
    level: int
    guild: str
    skill: str
    count_current: int
    count_total: int
    accumulated_count: int = 0  # Total accumulated count across resets
    total_time: str
    status: str
    runtime: str
    crawl_timestamp: datetime = Field(default_factory=datetime.utcnow)
    keywords_detected: Dict[str, int] = Field(default_factory=dict)  # Keyword counts

class KeywordStats(BaseModel):
    keyword: str
    total_count: int
    accounts_affected: List[str]
    last_seen: datetime

class CrawlerConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_url: str = "http://xiao8.lodsve.com:6007/x8login"
    crawl_interval: int = 45  # seconds - changed from 50 to 45
    max_concurrent: int = 10
    headless: bool = True
    timeout: int = 30
    retry_count: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CrawlerStats(BaseModel):
    total_accounts: int
    active_accounts: int
    total_records: int
    last_update: Optional[datetime] = None
    crawl_status: str

# Crawler Engine Class
class XiaoBaCrawler:
    def __init__(self, account: CrawlerAccount, config: CrawlerConfig):
        self.account = account
        self.config = config
        self.driver = None
        self.is_running = False
        self.last_data = {}
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        if self.config.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Use webdriver-manager to automatically manage ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            logger.error(f"Error setting up Chrome driver: {str(e)}")
            # Fallback to system chromium if available
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            self.driver = webdriver.Chrome(options=chrome_options)
            
        self.driver.set_page_load_timeout(self.config.timeout)
        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def login(self):
        """Login to the website with 师门 button selection"""
        try:
            self.driver.get(self.config.target_url)
            
            # Wait for login page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Take a screenshot for debugging
            try:
                self.driver.save_screenshot(f"/app/debug_screenshots/login_page_{self.account.username}.png")
                logger.info(f"Saved login page screenshot for {self.account.username}")
            except:
                pass
            
            # Wait a moment for page to fully load
            time.sleep(2)
            
            # First, click the "师门" button as required
            logger.info(f"Looking for 师门 button for account: {self.account.username}")
            师门_button = None
            
            # Enhanced strategies to find the 师门 button
            try:
                # Strategy 1: Look for button with exact text "师门"
                师门_button = WebDriverWait(self.driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[normalize-space(text())='师门']"))
                )
                logger.info("Found 师门 button using exact text match")
            except:
                try:
                    # Strategy 2: Look for input type button with value "师门"
                    师门_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@type='button' and @value='师门']"))
                    )
                    logger.info("Found 师门 button using input button")
                except:
                    try:
                        # Strategy 3: Look for any clickable element containing "师门"
                        师门_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '师门') and (name()='button' or name()='input' or name()='a' or name()='div')]"))
                        )
                        logger.info("Found 师门 button using general element search")
                    except:
                        try:
                            # Strategy 4: Look by class or other attributes that might indicate login type selection
                            buttons = self.driver.find_elements(By.TAG_NAME, "button")
                            inputs = self.driver.find_elements(By.TAG_NAME, "input")
                            all_elements = buttons + inputs
                            
                            for element in all_elements:
                                element_text = element.text.strip() if element.text else ""
                                element_value = element.get_attribute('value') or ""
                                
                                if "师门" in element_text or "师门" in element_value:
                                    师门_button = element
                                    logger.info(f"Found 师门 button using comprehensive search: {element.tag_name}")
                                    break
                        except Exception as e:
                            logger.warning(f"Error in comprehensive button search: {str(e)}")
            
            if 师门_button:
                try:
                    # Scroll to the button to ensure it's visible
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", 师门_button)
                    time.sleep(0.5)
                    
                    # Highlight the button for debugging
                    self.driver.execute_script("arguments[0].style.border='3px solid red';", 师门_button)
                    
                    # Try regular click first
                    师门_button.click()
                    logger.info("Clicked 师门 button successfully")
                    
                except Exception as click_error:
                    try:
                        # Try JavaScript click if regular click fails
                        self.driver.execute_script("arguments[0].click();", 师门_button)
                        logger.info("Clicked 师门 button using JavaScript")
                    except Exception as js_error:
                        logger.error(f"Failed to click 师门 button: regular={click_error}, js={js_error}")
                
                # Wait for the form to update after selecting 师门
                time.sleep(2)
                
                # Take another screenshot after clicking 师门
                try:
                    self.driver.save_screenshot(f"/app/debug_screenshots/after_shimen_{self.account.username}.png")
                    logger.info(f"Saved post-师门 screenshot for {self.account.username}")
                except:
                    pass
                    
            else:
                logger.error("Could not find 师门 button! This might cause login to fail.")
                # Take screenshot of the current page for debugging
                try:
                    self.driver.save_screenshot(f"/app/debug_screenshots/no_shimen_button_{self.account.username}.png")
                    logger.info(f"Saved no-师门-button screenshot for debugging")
                except:
                    pass
            
            # Wait for login form to be available after selecting 师门
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            
            # Fill in username and password
            username_field = self.driver.find_element(By.NAME, "username")
            password_field = self.driver.find_element(By.NAME, "password")
            
            username_field.clear()
            username_field.send_keys(self.account.username)
            
            password_field.clear()
            password_field.send_keys(self.account.password)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            login_button.click()
            
            # Wait for successful login - check if we're redirected or if login form disappears
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.current_url != self.config.target_url or 
                len(driver.find_elements(By.NAME, "username")) == 0
            )
            
            logger.info(f"Successfully logged in with account: {self.account.username}")
            return True
            
        except TimeoutException:
            logger.error(f"Login timeout for account: {self.account.username}")
            return False
        except Exception as e:
            logger.error(f"Login error for account {self.account.username}: {str(e)}")
            return False
    
    def parse_table_data(self):
        """Parse the table data from the current page"""
        try:
            # Wait for table to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Get table HTML
            table_html = self.driver.page_source
            soup = BeautifulSoup(table_html, 'html.parser')
            
            # Find the data table
            tables = soup.find_all('table')
            if not tables:
                logger.warning("No table found on the page")
                return []
            
            # Use the first table (assuming it's the data table)
            table = tables[0]
            rows = table.find_all('tr')
            
            data_list = []
            for i, row in enumerate(rows[1:], 1):  # Skip header row
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 10:  # Ensure we have enough columns
                    try:
                        # Parse count/total from format like "20/199"
                        count_text = cols[7].get_text(strip=True)
                        count_match = re.match(r'(\d+)/(\d+)', count_text)
                        count_current = int(count_match.group(1)) if count_match else 0
                        count_total = int(count_match.group(2)) if count_match else 0
                        
                        data_item = CrawlerData(
                            account_username=self.account.username,
                            sequence_number=int(cols[0].get_text(strip=True)),
                            ip=cols[1].get_text(strip=True),
                            type=cols[2].get_text(strip=True),
                            name=cols[3].get_text(strip=True),
                            level=int(cols[4].get_text(strip=True)) if cols[4].get_text(strip=True).isdigit() else 0,
                            guild=cols[5].get_text(strip=True),
                            skill=cols[6].get_text(strip=True),
                            count_current=count_current,
                            count_total=count_total,
                            accumulated_count=0,  # Will be set in accumulate_data
                            total_time=cols[8].get_text(strip=True),
                            status=cols[9].get_text(strip=True),
                            runtime=cols[10].get_text(strip=True) if len(cols) > 10 else "",
                            keywords_detected={}  # Will be set in accumulate_data
                        )
                        data_list.append(data_item)
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Error parsing row {i}: {str(e)}")
                        continue
            
            return data_list
            
        except TimeoutException:
            logger.error("Timeout waiting for table to load")
            return []
        except Exception as e:
            logger.error(f"Error parsing table data: {str(e)}")
            return []
    
    def accumulate_data(self, new_data: List[CrawlerData]):
        """Accumulate count data with previous records and detect keywords"""
        try:
            # Define keywords to track
            keywords_to_track = ["人脸提示", "没钱了", "网络异常", "系统维护", "账号异常", "登录失败"]
            
            for new_item in new_data:
                # Check if we have previous data for this item
                key = f"{new_item.account_username}_{new_item.sequence_number}_{new_item.ip}"
                
                # Initialize keyword detection
                new_item.keywords_detected = {}
                
                # Check all text fields for keywords
                text_fields = [
                    new_item.type, new_item.name, new_item.guild, 
                    new_item.skill, new_item.status, new_item.runtime,
                    new_item.total_time
                ]
                
                for keyword in keywords_to_track:
                    count = 0
                    for field in text_fields:
                        if field and keyword in str(field):
                            count += str(field).count(keyword)
                    if count > 0:
                        new_item.keywords_detected[keyword] = count
                
                # Handle data accumulation logic
                if key in self.last_data:
                    last_item = self.last_data[key]
                    
                    # Check if count has reset (current < last and significant difference)
                    if (new_item.count_current < last_item.count_current and 
                        last_item.count_current - new_item.count_current > 5):
                        # Count has reset, accumulate the previous count
                        new_item.accumulated_count = last_item.accumulated_count + last_item.count_current
                        logger.info(f"Count reset detected for {key}: {last_item.count_current} -> {new_item.count_current}, accumulated: {new_item.accumulated_count}")
                    else:
                        # Normal progression, keep previous accumulated count
                        new_item.accumulated_count = last_item.accumulated_count
                        
                        # If current count is still less than last, add the difference
                        if new_item.count_current < last_item.count_current:
                            new_item.accumulated_count += (last_item.count_current - new_item.count_current)
                else:
                    # First time seeing this item
                    new_item.accumulated_count = 0
                
                # Update last data
                self.last_data[key] = new_item
                
        except Exception as e:
            logger.error(f"Error accumulating data: {str(e)}")
    
    async def save_keyword_stats(self, data_list: List[CrawlerData]):
        """Save keyword statistics to database"""
        try:
            keyword_stats = {}
            
            for data_item in data_list:
                for keyword, count in data_item.keywords_detected.items():
                    if keyword not in keyword_stats:
                        keyword_stats[keyword] = {
                            "keyword": keyword,
                            "total_count": 0,
                            "accounts_affected": set(),
                            "last_seen": datetime.utcnow()
                        }
                    
                    keyword_stats[keyword]["total_count"] += count
                    keyword_stats[keyword]["accounts_affected"].add(data_item.account_username)
                    keyword_stats[keyword]["last_seen"] = datetime.utcnow()
            
            # Update keyword stats in database
            for keyword, stats in keyword_stats.items():
                # Convert set to list for JSON serialization
                stats["accounts_affected"] = list(stats["accounts_affected"])
                
                await db.keyword_stats.update_one(
                    {"keyword": keyword},
                    {"$set": stats, "$inc": {"total_count": stats["total_count"]}},
                    upsert=True
                )
            
            logger.info(f"Updated keyword stats for {len(keyword_stats)} keywords")
            
        except Exception as e:
            logger.error(f"Error saving keyword stats: {str(e)}")
    
    async def save_data(self, data_list: List[CrawlerData]):
        """Save crawler data to database"""
        try:
            for data_item in data_list:
                # Check if record already exists
                existing = await db.crawler_data.find_one({
                    "account_username": data_item.account_username,
                    "sequence_number": data_item.sequence_number,
                    "ip": data_item.ip
                })
                
                if existing:
                    # Update existing record
                    await db.crawler_data.update_one(
                        {"_id": existing["_id"]},
                        {"$set": data_item.dict()}
                    )
                else:
                    # Insert new record
                    await db.crawler_data.insert_one(data_item.dict())
                    
            logger.info(f"Saved {len(data_list)} records for account {self.account.username}")
            
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
    
    async def crawl_once(self):
        """Perform one crawl cycle"""
        try:
            if not self.driver:
                self.setup_driver()
                
            if not self.login():
                return False
                
            # Parse table data
            data_list = self.parse_table_data()
            
            if data_list:
                # Accumulate data and detect keywords
                self.accumulate_data(data_list)
                
                # Save to database
                await self.save_data(data_list)
                
                # Save keyword statistics
                await self.save_keyword_stats(data_list)
                
                # Update account status
                await db.crawler_accounts.update_one(
                    {"username": self.account.username},
                    {"$set": {"status": "active", "last_crawl": datetime.utcnow()}}
                )
                
                # Broadcast to websockets
                await broadcast_crawler_update(self.account.username, data_list)
                
                return True
            else:
                logger.warning(f"No data found for account {self.account.username}")
                return False
                
        except Exception as e:
            logger.error(f"Crawl error for account {self.account.username}: {str(e)}")
            await db.crawler_accounts.update_one(
                {"username": self.account.username},
                {"$set": {"status": "error"}}
            )
            return False
    
    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

# Helper Functions
async def broadcast_crawler_update(username: str, data_list: List[CrawlerData]):
    """Broadcast crawler updates to all connected WebSockets"""
    if websocket_connections:
        message = {
            "type": "crawler_update",
            "account": username,
            "data": [item.dict() for item in data_list],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = set()
        for websocket in websocket_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                disconnected.add(websocket)
        
        # Remove disconnected websockets
        websocket_connections -= disconnected

async def crawl_all_accounts():
    """Crawl all active accounts"""
    try:
        accounts = await db.crawler_accounts.find({"status": {"$ne": "disabled"}}).to_list(100)
        config = await get_crawler_config()
        
        tasks = []
        for account_data in accounts:
            account = CrawlerAccount(**account_data)
            crawler = XiaoBaCrawler(account, config)
            active_crawlers[account.username] = crawler
            
            # Create crawl task
            task = asyncio.create_task(crawler.crawl_once())
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Close all crawlers
        for crawler in active_crawlers.values():
            crawler.close()
        active_crawlers.clear()
        
        logger.info(f"Completed crawl cycle for {len(accounts)} accounts")
        
    except Exception as e:
        logger.error(f"Error in crawl_all_accounts: {str(e)}")

async def get_crawler_config():
    """Get crawler configuration"""
    config_data = await db.crawler_config.find_one()
    if config_data:
        return CrawlerConfig(**config_data)
    else:
        # Create default config
        config = CrawlerConfig()
        await db.crawler_config.insert_one(config.dict())
        return config

# API Routes
@api_router.get("/")
async def root():
    return {"message": "XiaoBa Crawler API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Crawler Account Management
@api_router.post("/crawler/accounts", response_model=CrawlerAccount)
async def create_crawler_account(account: CrawlerAccountCreate):
    account_obj = CrawlerAccount(**account.dict())
    await db.crawler_accounts.insert_one(account_obj.dict())
    return account_obj

@api_router.get("/crawler/accounts", response_model=List[CrawlerAccount])
async def get_crawler_accounts():
    accounts = await db.crawler_accounts.find().to_list(100)
    return [CrawlerAccount(**account) for account in accounts]

@api_router.delete("/crawler/accounts/{username}")
async def delete_crawler_account(username: str):
    result = await db.crawler_accounts.delete_one({"username": username})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account deleted successfully"}

# Batch Account Management
@api_router.post("/crawler/accounts/batch/enable")
async def enable_all_accounts():
    """Enable all accounts for crawling"""
    try:
        result = await db.crawler_accounts.update_many(
            {},
            {"$set": {"status": "inactive"}}
        )
        return {"message": f"Enabled {result.modified_count} accounts for crawling"}
    except Exception as e:
        logger.error(f"Error enabling all accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/crawler/accounts/batch/disable")
async def disable_all_accounts():
    """Disable all accounts from crawling"""
    try:
        result = await db.crawler_accounts.update_many(
            {},
            {"$set": {"status": "disabled"}}
        )
        return {"message": f"Disabled {result.modified_count} accounts from crawling"}
    except Exception as e:
        logger.error(f"Error disabling all accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/crawler/accounts/{username}/enable")
async def enable_account(username: str):
    """Enable a specific account for crawling"""
    try:
        result = await db.crawler_accounts.update_one(
            {"username": username},
            {"$set": {"status": "inactive"}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Account not found")
        return {"message": f"Account {username} enabled for crawling"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling account {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/crawler/accounts/{username}/disable")
async def disable_account(username: str):
    """Disable a specific account from crawling"""
    try:
        result = await db.crawler_accounts.update_one(
            {"username": username},
            {"$set": {"status": "disabled"}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Account not found")
        return {"message": f"Account {username} disabled from crawling"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling account {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced account creation with validation
@api_router.post("/crawler/accounts/validate")
async def validate_account(account: CrawlerAccountCreate):
    """Validate account credentials by attempting login"""
    try:
        # Check if account already exists
        existing = await db.crawler_accounts.find_one({"username": account.username})
        if existing:
            raise HTTPException(status_code=400, detail="Account already exists")
        
        # Test login
        config = await get_crawler_config()
        temp_account = CrawlerAccount(**account.dict())
        crawler = XiaoBaCrawler(temp_account, config)
        
        try:
            crawler.setup_driver()
            login_result = crawler.login()
            crawler.close()
            
            if login_result:
                # Create account if validation successful
                account_obj = CrawlerAccount(**account.dict())
                await db.crawler_accounts.insert_one(account_obj.dict())
                return {"message": "Account validated and created successfully", "account": account_obj}
            else:
                return {"message": "Account validation failed - login unsuccessful", "valid": False}
                
        except Exception as e:
            crawler.close()
            logger.error(f"Error validating account {account.username}: {str(e)}")
            return {"message": f"Account validation failed: {str(e)}", "valid": False}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in account validation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Crawler Data Management
@api_router.get("/crawler/data", response_model=List[CrawlerData])
async def get_crawler_data(
    account_username: Optional[str] = None,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    guild: Optional[str] = None,
    min_count: Optional[int] = None,
    max_count: Optional[int] = None,
    limit: Optional[int] = 1000
):
    """Get crawler data with optional filtering"""
    query = {}
    
    # Basic filters
    if account_username:
        query["account_username"] = account_username
    if status:
        query["status"] = status
    if guild:
        query["guild"] = guild
    
    # Count range filter
    if min_count is not None or max_count is not None:
        count_query = {}
        if min_count is not None:
            count_query["$gte"] = min_count
        if max_count is not None:
            count_query["$lte"] = max_count
        query["count_current"] = count_query
    
    # Keyword filter (search in multiple fields)
    if keyword:
        query["$or"] = [
            {"type": {"$regex": keyword, "$options": "i"}},
            {"name": {"$regex": keyword, "$options": "i"}},
            {"guild": {"$regex": keyword, "$options": "i"}},
            {"skill": {"$regex": keyword, "$options": "i"}},
            {"status": {"$regex": keyword, "$options": "i"}},
        ]
    
    data = await db.crawler_data.find(query).sort("crawl_timestamp", -1).to_list(limit)
    return [CrawlerData(**item) for item in data]

@api_router.get("/crawler/data/keywords", response_model=List[KeywordStats])
async def get_keyword_stats():
    """Get keyword statistics"""
    try:
        stats = await db.keyword_stats.find().sort("total_count", -1).to_list(100)
        return [KeywordStats(**stat) for stat in stats]
    except Exception as e:
        logger.error(f"Error getting keyword stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/crawler/data/summary")
async def get_data_summary():
    """Get summary statistics of crawler data"""
    try:
        # Get total counts
        total_records = await db.crawler_data.count_documents({})
        
        # Get active accounts
        active_accounts = await db.crawler_accounts.count_documents({"status": "active"})
        
        # Get keyword stats
        keyword_stats = await db.keyword_stats.find().sort("total_count", -1).to_list(10)
        
        # Get recent data (last 24 hours)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_records = await db.crawler_data.count_documents({
            "crawl_timestamp": {"$gte": last_24h}
        })
        
        # Get count accumulation stats
        pipeline = [
            {"$group": {
                "_id": None,
                "total_accumulated": {"$sum": "$accumulated_count"},
                "total_current": {"$sum": "$count_current"},
                "avg_accumulated": {"$avg": "$accumulated_count"}
            }}
        ]
        
        accumulation_stats = await db.crawler_data.aggregate(pipeline).to_list(1)
        
        return {
            "total_records": total_records,
            "active_accounts": active_accounts,
            "recent_records_24h": recent_records,
            "keyword_stats": keyword_stats,
            "accumulation_stats": accumulation_stats[0] if accumulation_stats else {
                "total_accumulated": 0,
                "total_current": 0,
                "avg_accumulated": 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting data summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/crawler/data/accounts-performance")
async def get_accounts_performance():
    """Get performance statistics for each account"""
    try:
        pipeline = [
            {"$group": {
                "_id": "$account_username",
                "total_records": {"$sum": 1},
                "total_accumulated": {"$sum": "$accumulated_count"},
                "total_current": {"$sum": "$count_current"},
                "avg_current": {"$avg": "$count_current"},
                "last_crawl": {"$max": "$crawl_timestamp"},
                "keywords_detected": {"$sum": {
                    "$cond": [
                        {"$isArray": {"$objectToArray": "$keywords_detected"}},
                        {"$size": {"$objectToArray": "$keywords_detected"}},
                        0
                    ]
                }}
            }},
            {"$sort": {"total_records": -1}}
        ]
        
        performance = await db.crawler_data.aggregate(pipeline).to_list(100)
        
        return performance
        
    except Exception as e:
        logger.error(f"Error getting accounts performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/crawler/data/export")
async def export_crawler_data(
    account_username: Optional[str] = None,
    include_keywords: bool = True,
    include_accumulated: bool = True
):
    """Export crawler data as CSV with enhanced features"""
    query = {}
    if account_username:
        query["account_username"] = account_username
    
    data = await db.crawler_data.find(query).sort("crawl_timestamp", -1).to_list(10000)
    
    if not data:
        # Return empty CSV with headers if no data
        columns = [
            "账号", "序号", "IP", "类型", "命名", "等级", "门派", "绝技", 
            "当前次数", "累计次数", "总次数", "总时间", "状态", "运行时间", "爬取时间"
        ]
        if include_keywords:
            columns.append("关键词检测")
        
        df = pd.DataFrame(columns=columns)
    else:
        # Convert to DataFrame with enhanced fields
        rows = []
        for item in data:
            row = {
                "账号": item["account_username"],
                "序号": item["sequence_number"],
                "IP": item["ip"],
                "类型": item["type"],
                "命名": item["name"],
                "等级": item["level"],
                "门派": item["guild"],
                "绝技": item["skill"],
                "当前次数": item["count_current"],
                "总次数": item["count_total"],
                "总时间": item["total_time"],
                "状态": item["status"],
                "运行时间": item["runtime"],
                "爬取时间": item["crawl_timestamp"]
            }
            
            if include_accumulated and "accumulated_count" in item:
                row["累计次数"] = item["accumulated_count"]
            
            if include_keywords and "keywords_detected" in item:
                keywords = item["keywords_detected"]
                if keywords:
                    keyword_str = "; ".join([f"{k}:{v}" for k, v in keywords.items()])
                    row["关键词检测"] = keyword_str
                else:
                    row["关键词检测"] = ""
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
    
    # Create CSV in memory
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=crawler_data.csv"}
    )

# Add mock data generation
@api_router.post("/crawler/mock-data")
async def generate_mock_data():
    """Generate mock data for demonstration"""
    try:
        import random
        
        accounts = ["KR666", "KR777", "KR888", "KR999", "KR000"]
        mock_data = []
        
        for account in accounts:
            for i in range(5):  # 5 records per account
                data_item = CrawlerData(
                    account_username=account,
                    sequence_number=i + 1,
                    ip=f"222.210.79.{115 + i}",
                    type=random.choice(["鬼砍", "剑客", "杀手"]),
                    name=f"测试角色{i+1}",
                    level=random.randint(80, 120),
                    guild=random.choice(["青帮", "无门派", "九雷剑", "五毒"]),
                    skill=random.choice(["0", "1", "2", "3"]),
                    count_current=random.randint(1, 50),
                    count_total=random.randint(100, 200),
                    total_time=f"{random.randint(1, 12)}/{random.randint(100, 200)}",
                    status=random.choice(["在线", "离线", "忙碌"]),
                    runtime=f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
                )
                mock_data.append(data_item)
        
        # Insert mock data
        for data_item in mock_data:
            await db.crawler_data.insert_one(data_item.dict())
        
        return {"message": f"Generated {len(mock_data)} mock data records"}
        
    except Exception as e:
        logger.error(f"Error generating mock data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
@api_router.post("/crawler/start")
async def start_crawler(background_tasks: BackgroundTasks):
    """Start the crawler with scheduled tasks"""
    try:
        # Initialize default accounts if none exist
        existing_accounts = await db.crawler_accounts.count_documents({})
        if existing_accounts == 0:
            default_accounts = [
                CrawlerAccountCreate(username="KR666", password="69203532xX"),
                CrawlerAccountCreate(username="KR777", password="69203532xX"),
                CrawlerAccountCreate(username="KR888", password="69203532xX"),
                CrawlerAccountCreate(username="KR999", password="69203532xX"),
                CrawlerAccountCreate(username="KR000", password="69203532xX")
            ]
            
            for account in default_accounts:
                account_obj = CrawlerAccount(**account.dict())
                await db.crawler_accounts.insert_one(account_obj.dict())
        
        # Get crawler config to use the correct interval
        config = await get_crawler_config()
        
        # Start scheduler
        if not scheduler.running:
            scheduler.add_job(
                crawl_all_accounts,
                IntervalTrigger(seconds=config.crawl_interval),
                id='crawler_job',
                replace_existing=True
            )
            scheduler.start()
            logger.info(f"Crawler started with {config.crawl_interval} second intervals")
            
        return {"message": f"Crawler started successfully with {config.crawl_interval} second intervals"}
        
    except Exception as e:
        logger.error(f"Error starting crawler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/crawler/stop")
async def stop_crawler():
    """Stop the crawler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            
        # Close all active crawlers
        for crawler in active_crawlers.values():
            crawler.close()
        active_crawlers.clear()
        
        return {"message": "Crawler stopped successfully"}
        
    except Exception as e:
        logger.error(f"Error stopping crawler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/crawler/status")
async def get_crawler_status():
    """Get crawler status"""
    try:
        total_accounts = await db.crawler_accounts.count_documents({})
        active_accounts = await db.crawler_accounts.count_documents({"status": "active"})
        total_records = await db.crawler_data.count_documents({})
        
        # Get latest update time
        latest_record = await db.crawler_data.find_one(sort=[("crawl_timestamp", -1)])
        last_update = latest_record["crawl_timestamp"] if latest_record else None
        
        stats = CrawlerStats(
            total_accounts=total_accounts,
            active_accounts=active_accounts,
            total_records=total_records,
            last_update=last_update,
            crawl_status="running" if scheduler.running else "stopped"
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting crawler status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/crawler/test/{username}")
async def test_crawler_account(username: str):
    """Test a specific crawler account"""
    try:
        account_data = await db.crawler_accounts.find_one({"username": username})
        if not account_data:
            raise HTTPException(status_code=404, detail="Account not found")
        
        account = CrawlerAccount(**account_data)
        config = await get_crawler_config()
        
        crawler = XiaoBaCrawler(account, config)
        result = await crawler.crawl_once()
        crawler.close()
        
        return {
            "username": username,
            "test_result": "success" if result else "failed",
            "message": "Test completed"
        }
        
    except Exception as e:
        logger.error(f"Error testing crawler account {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration Management
@api_router.get("/crawler/config", response_model=CrawlerConfig)
async def get_crawler_config_endpoint():
    """Get current crawler configuration"""
    try:
        config = await get_crawler_config()
        return config
    except Exception as e:
        logger.error(f"Error getting crawler config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/crawler/config")
async def update_crawler_config(config_update: dict):
    """Update crawler configuration and restart scheduler if needed"""
    try:
        # Get current config
        current_config = await get_crawler_config()
        
        # Update config in database
        await db.crawler_config.update_one(
            {"id": current_config.id},
            {"$set": config_update}
        )
        
        # If crawl_interval was changed and scheduler is running, restart it
        if "crawl_interval" in config_update and scheduler.running:
            scheduler.remove_job('crawler_job')
            new_config = await get_crawler_config()
            scheduler.add_job(
                crawl_all_accounts,
                IntervalTrigger(seconds=new_config.crawl_interval),
                id='crawler_job',
                replace_existing=True
            )
            logger.info(f"Restarted crawler with new interval: {new_config.crawl_interval} seconds")
            
        return {"message": "Configuration updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating crawler config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@api_router.websocket("/crawler/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.add(websocket)
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        websocket_connections.discard(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        websocket_connections.discard(websocket)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("Starting XiaoBa Crawler API")
    
    # Initialize default config if not exists
    config_exists = await db.crawler_config.count_documents({})
    if config_exists == 0:
        config = CrawlerConfig()
        await db.crawler_config.insert_one(config.dict())
        logger.info("Created default crawler configuration")
    
    # Auto-start the crawler for continuous operation
    try:
        # Initialize default accounts if none exist
        existing_accounts = await db.crawler_accounts.count_documents({})
        if existing_accounts == 0:
            default_accounts = [
                CrawlerAccountCreate(username="KR666", password="69203532xX"),
                CrawlerAccountCreate(username="KR777", password="69203532xX"),
                CrawlerAccountCreate(username="KR888", password="69203532xX"),
                CrawlerAccountCreate(username="KR999", password="69203532xX"),
                CrawlerAccountCreate(username="KR000", password="69203532xX")
            ]
            
            for account in default_accounts:
                account_obj = CrawlerAccount(**account.dict())
                await db.crawler_accounts.insert_one(account_obj.dict())
            logger.info("Created default crawler accounts")
        
        # Get crawler config to use the correct interval
        config = await get_crawler_config()
        
        # Start scheduler automatically
        if not scheduler.running:
            scheduler.add_job(
                crawl_all_accounts,
                IntervalTrigger(seconds=config.crawl_interval),
                id='crawler_job',
                replace_existing=True
            )
            scheduler.start()
            logger.info(f"Auto-started crawler with {config.crawl_interval} second intervals")
            
    except Exception as e:
        logger.error(f"Error auto-starting crawler: {str(e)}")
        # Don't raise exception to prevent server startup failure

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down XiaoBa Crawler API")
    
    # Stop scheduler
    if scheduler.running:
        scheduler.shutdown()
    
    # Close all crawlers
    for crawler in active_crawlers.values():
        crawler.close()
    active_crawlers.clear()
    
    # Close database connection
    client.close()