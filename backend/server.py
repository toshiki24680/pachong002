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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
    total_time: str
    status: str
    runtime: str
    crawl_timestamp: datetime = Field(default_factory=datetime.utcnow)

class CrawlerConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_url: str = "http://xiao8.lodsve.com:6007/x8login"
    crawl_interval: int = 50  # seconds
    max_concurrent: int = 10
    headless: bool = True
    timeout: int = 30
    retry_count: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CrawlerStats(BaseModel):
    total_accounts: int
    active_accounts: int
    total_records: int
    last_update: datetime
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
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(self.config.timeout)
        
    def login(self):
        """Login to the website"""
        try:
            self.driver.get(self.config.target_url)
            
            # Wait for login page to load
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
                            total_time=cols[8].get_text(strip=True),
                            status=cols[9].get_text(strip=True),
                            runtime=cols[10].get_text(strip=True) if len(cols) > 10 else ""
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
        """Accumulate count data with previous records"""
        try:
            for new_item in new_data:
                # Check if we have previous data for this item
                key = f"{new_item.account_username}_{new_item.sequence_number}_{new_item.ip}"
                
                if key in self.last_data:
                    last_item = self.last_data[key]
                    # If current count is less than last count, accumulate
                    if new_item.count_current < last_item.count_current:
                        new_item.count_current += last_item.count_current
                
                # Update last data
                self.last_data[key] = new_item
                
        except Exception as e:
            logger.error(f"Error accumulating data: {str(e)}")
    
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
                # Accumulate data
                self.accumulate_data(data_list)
                
                # Save to database
                await self.save_data(data_list)
                
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

# Crawler Data Management
@api_router.get("/crawler/data", response_model=List[CrawlerData])
async def get_crawler_data(account_username: Optional[str] = None):
    query = {}
    if account_username:
        query["account_username"] = account_username
    
    data = await db.crawler_data.find(query).sort("crawl_timestamp", -1).to_list(1000)
    return [CrawlerData(**item) for item in data]

@api_router.get("/crawler/data/export")
async def export_crawler_data(account_username: Optional[str] = None):
    """Export crawler data as CSV"""
    query = {}
    if account_username:
        query["account_username"] = account_username
    
    data = await db.crawler_data.find(query).sort("crawl_timestamp", -1).to_list(10000)
    
    if not data:
        raise HTTPException(status_code=404, detail="No data found")
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            "账号": item["account_username"],
            "序号": item["sequence_number"],
            "IP": item["ip"],
            "类型": item["type"],
            "命名": item["name"],
            "等级": item["level"],
            "门派": item["guild"],
            "绝技": item["skill"],
            "次数": f"{item['count_current']}/{item['count_total']}",
            "总时间": item["total_time"],
            "状态": item["status"],
            "运行时间": item["runtime"],
            "爬取时间": item["crawl_timestamp"]
        } for item in data
    ])
    
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

# Crawler Control
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
        
        # Start scheduler
        if not scheduler.running:
            scheduler.add_job(
                crawl_all_accounts,
                IntervalTrigger(seconds=50),
                id='crawler_job',
                replace_existing=True
            )
            scheduler.start()
            
        return {"message": "Crawler started successfully"}
        
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