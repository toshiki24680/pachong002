#!/bin/bash

# 小八爬虫管理系统 - 一键部署脚本
# 支持 macOS 系统

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "\n${BLUE}==================== $1 ====================${NC}\n"
}

# 检查操作系统
check_os() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "此脚本仅支持 macOS 系统"
        exit 1
    fi
    print_success "检测到 macOS 系统"
}

# 检查并安装 Homebrew
install_homebrew() {
    if ! command -v brew &> /dev/null; then
        print_info "正在安装 Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        print_success "Homebrew 安装完成"
    else
        print_success "Homebrew 已安装"
    fi
}

# 安装系统依赖
install_dependencies() {
    print_info "正在安装系统依赖..."
    
    # 更新 brew
    brew update
    
    # 安装 Python
    if ! command -v python3 &> /dev/null; then
        print_info "正在安装 Python..."
        brew install python@3.11
    else
        print_success "Python 已安装"
    fi
    
    # 安装 Node.js
    if ! command -v node &> /dev/null; then
        print_info "正在安装 Node.js..."
        brew install node
    else
        print_success "Node.js 已安装"
    fi
    
    # 安装 MongoDB
    if ! command -v mongod &> /dev/null; then
        print_info "正在安装 MongoDB..."
        brew tap mongodb/brew
        brew install mongodb-community
    else
        print_success "MongoDB 已安装"
    fi
    
    # 安装 Chrome（如果需要）
    if ! command -v "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" &> /dev/null; then
        print_warning "建议安装 Google Chrome 浏览器以获得最佳爬虫体验"
        read -p "是否安装 Google Chrome? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            brew install --cask google-chrome
        fi
    else
        print_success "Google Chrome 已安装"
    fi
    
    print_success "系统依赖安装完成"
}

# 创建项目目录
create_project() {
    PROJECT_DIR="$HOME/xiaoba-crawler"
    
    if [ -d "$PROJECT_DIR" ]; then
        print_warning "项目目录已存在，是否删除重新创建?"
        read -p "删除现有项目? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
        else
            print_error "取消安装"
            exit 1
        fi
    fi
    
    print_info "创建项目目录: $PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"/{backend,frontend}
    cd "$PROJECT_DIR"
    
    print_success "项目目录创建完成"
}

# 设置后端
setup_backend() {
    print_info "设置后端环境..."
    cd "$PROJECT_DIR/backend"
    
    # 创建 requirements.txt
    cat > requirements.txt << 'EOF'
fastapi==0.110.1
uvicorn==0.25.0
python-dotenv>=1.0.1
pymongo==4.5.0
pydantic>=2.6.4
motor==3.3.1
requests>=2.31.0
pandas>=2.2.0
numpy>=1.26.0
selenium>=4.15.0
beautifulsoup4>=4.12.2
apscheduler>=3.10.4
websockets>=11.0.3
aiofiles>=23.2.1
openpyxl>=3.1.2
webdriver-manager>=4.0.2
python-multipart>=0.0.9
starlette>=0.37.2
boto3>=1.34.129
requests-oauthlib>=2.0.0
cryptography>=42.0.8
email-validator>=2.2.0
pyjwt>=2.10.1
passlib>=1.7.4
tzdata>=2024.2
pytest>=8.0.0
python-jose>=3.3.0
jq>=1.6.0
typer>=0.9.0
EOF
    
    # 创建 .env 文件
    cat > .env << 'EOF'
MONGO_URL=mongodb://localhost:27017
DB_NAME=xiaoba_crawler
EOF
    
    # 创建虚拟环境
    print_info "创建Python虚拟环境..."
    python3 -m venv venv
    
    # 激活虚拟环境并安装依赖
    print_info "安装Python依赖包..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "后端环境设置完成"
}

# 创建后端代码
create_backend_code() {
    print_info "创建后端代码..."
    cd "$PROJECT_DIR/backend"
    
    # 创建 server.py（这里包含完整的后端代码）
    cat > server.py << 'EOF'
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
import random

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
        # Return empty CSV with headers if no data
        df = pd.DataFrame(columns=[
            "账号", "序号", "IP", "类型", "命名", "等级", "门派", "绝技", 
            "次数", "总时间", "状态", "运行时间", "爬取时间"
        ])
    else:
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

# Add mock data generation
@api_router.post("/crawler/mock-data")
async def generate_mock_data():
    """Generate mock data for demonstration"""
    try:
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
EOF
    
    print_success "后端代码创建完成"
}

# 设置前端
setup_frontend() {
    print_info "设置前端环境..."
    cd "$PROJECT_DIR/frontend"
    
    # 初始化React项目
    print_info "创建React应用..."
    npx create-react-app . --template typescript --yes
    
    # 安装额外依赖
    print_info "安装前端依赖..."
    npm install axios tailwindcss postcss autoprefixer @craco/craco
    
    # 初始化Tailwind CSS
    npx tailwindcss init -p
    
    # 创建Tailwind配置
    cat > tailwind.config.js << 'EOF'
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOF
    
    # 创建craco配置
    cat > craco.config.js << 'EOF'
module.exports = {
  style: {
    postcss: {
      plugins: [
        require('tailwindcss'),
        require('autoprefixer'),
      ],
    },
  },
}
EOF
    
    # 创建.env文件
    cat > .env << 'EOF'
REACT_APP_BACKEND_URL=http://localhost:8001
EOF
    
    # 修改package.json的scripts
    npm pkg set scripts.start="craco start"
    npm pkg set scripts.build="craco build"
    npm pkg set scripts.test="craco test"
    
    print_success "前端环境设置完成"
}

# 创建前端代码
create_frontend_code() {
    print_info "创建前端代码..."
    cd "$PROJECT_DIR/frontend/src"
    
    # 更新index.css
    cat > index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto",
        "Oxygen", "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans",
        "Helvetica Neue", sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

code {
    font-family: source-code-pro, Menlo, Monaco, Consolas, "Courier New",
        monospace;
}
EOF
    
    # 创建App.css
    cat > App.css << 'EOF'
.App {
    text-align: center;
}

.App-logo {
    height: 40vmin;
    pointer-events: none;
}

@media (prefers-reduced-motion: no-preference) {
    .App-logo {
        animation: App-logo-spin infinite 20s linear;
    }
}

.App-header {
    background-color: #0f0f10;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: calc(10px + 2vmin);
    color: white;
}

.App-link {
    color: #61dafb;
}

@keyframes App-logo-spin {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}
EOF
    
    # 创建主要的App.js
    cat > App.js << 'EOF'
import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [crawlerData, setCrawlerData] = useState([]);
  const [crawlerStats, setCrawlerStats] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [crawlerStatus, setCrawlerStatus] = useState('stopped');
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  // WebSocket连接
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const wsUrl = `${BACKEND_URL.replace('http', 'ws')}/api/crawler/ws`;
        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
          console.log('WebSocket连接已建立');
          setWsConnected(true);
        };

        wsRef.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'crawler_update') {
              console.log('收到实时更新:', data);
              fetchCrawlerData();
              fetchCrawlerStats();
            }
          } catch (err) {
            console.error('处理WebSocket消息失败:', err);
          }
        };

        wsRef.current.onclose = () => {
          console.log('WebSocket连接已关闭');
          setWsConnected(false);
          // 自动重连
          setTimeout(connectWebSocket, 3000);
        };

        wsRef.current.onerror = (error) => {
          console.error('WebSocket错误:', error);
          setWsConnected(false);
        };
      } catch (err) {
        console.error('WebSocket连接失败:', err);
        setWsConnected(false);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // 获取爬虫数据
  const fetchCrawlerData = async () => {
    try {
      const response = await axios.get(`${API}/crawler/data`);
      setCrawlerData(response.data);
    } catch (err) {
      console.error('获取爬虫数据失败:', err);
      setError('获取爬虫数据失败');
    }
  };

  // 获取爬虫统计信息
  const fetchCrawlerStats = async () => {
    try {
      const response = await axios.get(`${API}/crawler/status`);
      setCrawlerStats(response.data);
      setCrawlerStatus(response.data.crawl_status);
    } catch (err) {
      console.error('获取爬虫统计失败:', err);
      setError('获取爬虫统计失败');
    }
  };

  // 获取账号列表
  const fetchAccounts = async () => {
    try {
      const response = await axios.get(`${API}/crawler/accounts`);
      setAccounts(response.data);
    } catch (err) {
      console.error('获取账号列表失败:', err);
      setError('获取账号列表失败');
    }
  };

  // 启动爬虫
  const startCrawler = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/crawler/start`);
      setCrawlerStatus('running');
      setError(null);
      await fetchCrawlerStats();
    } catch (err) {
      console.error('启动爬虫失败:', err);
      setError('启动爬虫失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 停止爬虫
  const stopCrawler = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/crawler/stop`);
      setCrawlerStatus('stopped');
      setError(null);
      await fetchCrawlerStats();
    } catch (err) {
      console.error('停止爬虫失败:', err);
      setError('停止爬虫失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 生成模拟数据
  const generateMockData = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/crawler/mock-data`);
      setError(null);
      await fetchCrawlerData();
      await fetchCrawlerStats();
      alert('模拟数据生成成功！');
    } catch (err) {
      console.error('生成模拟数据失败:', err);
      setError('生成模拟数据失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 测试账号
  const testAccount = async (username) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/crawler/test/${username}`);
      alert(`测试结果: ${response.data.test_result === 'success' ? '成功' : '失败'}`);
      await fetchAccounts();
    } catch (err) {
      console.error('测试账号失败:', err);
      setError('测试账号失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 导出CSV
  const exportCsv = async () => {
    try {
      const response = await axios.get(`${API}/crawler/data/export`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'crawler_data.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('导出CSV失败:', err);
      setError('导出CSV失败');
    }
  };

  // 页面加载时获取数据
  useEffect(() => {
    fetchCrawlerData();
    fetchCrawlerStats();
    fetchAccounts();
    
    // 定期刷新数据
    const interval = setInterval(() => {
      fetchCrawlerData();
      fetchCrawlerStats();
    }, 30000); // 每30秒刷新一次

    return () => clearInterval(interval);
  }, []);

  // 格式化时间
  const formatTime = (timestamp) => {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleString('zh-CN');
  };

  // 获取状态样式
  const getStatusStyle = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 头部 */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-3xl font-bold text-gray-900">小八爬虫管理系统</h1>
              <div className="ml-4 flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {wsConnected ? '实时连接' : '连接断开'}
                </span>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={crawlerStatus === 'running' ? stopCrawler : startCrawler}
                disabled={loading}
                className={`px-4 py-2 rounded-md font-medium ${
                  crawlerStatus === 'running'
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {loading ? '处理中...' : crawlerStatus === 'running' ? '停止爬虫' : '启动爬虫'}
              </button>
              <button
                onClick={generateMockData}
                disabled={loading}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
              >
                生成演示数据
              </button>
              <button
                onClick={exportCsv}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                导出CSV
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
            <button
              onClick={() => setError(null)}
              className="float-right font-bold text-red-700 hover:text-red-900"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* 标签页 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'dashboard'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              数据面板
            </button>
            <button
              onClick={() => setActiveTab('accounts')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'accounts'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              账号管理
            </button>
          </nav>
        </div>
      </div>

      {/* 主要内容 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* 统计卡片 */}
            {crawlerStats && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                          <span className="text-white font-bold">总</span>
                        </div>
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">总账号数</dt>
                          <dd className="text-lg font-medium text-gray-900">{crawlerStats.total_accounts}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                          <span className="text-white font-bold">活</span>
                        </div>
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">活跃账号</dt>
                          <dd className="text-lg font-medium text-gray-900">{crawlerStats.active_accounts}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                          <span className="text-white font-bold">记</span>
                        </div>
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">总记录数</dt>
                          <dd className="text-lg font-medium text-gray-900">{crawlerStats.total_records}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          crawlerStats.crawl_status === 'running' ? 'bg-green-500' : 'bg-red-500'
                        }`}>
                          <span className="text-white font-bold">状</span>
                        </div>
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">爬虫状态</dt>
                          <dd className="text-lg font-medium text-gray-900">
                            {crawlerStats.crawl_status === 'running' ? '运行中' : '已停止'}
                          </dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 数据表格 */}
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">爬虫数据</h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  最新爬取的数据记录，每50秒自动更新
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">账号</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">序号</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">类型</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">命名</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">等级</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">门派</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">绝技</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">次数/总次数</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">总时间</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">运行时间</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {crawlerData.map((item, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {item.account_username}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.sequence_number}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.ip}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.level}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.guild}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.skill}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className="font-medium text-blue-600">
                            {item.count_current}/{item.count_total}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.total_time}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            item.status === '在线' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.runtime}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {crawlerData.length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-gray-500">暂无数据，点击"生成演示数据"查看效果</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'accounts' && (
          <div className="space-y-6">
            {/* 账号列表 */}
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">账号管理</h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  管理爬虫账号，查看状态和测试连接
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">用户名</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">最后爬取时间</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">创建时间</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {accounts.map((account) => (
                      <tr key={account.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {account.username}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusStyle(account.status)}`}>
                            {account.status === 'active' ? '活跃' : account.status === 'inactive' ? '非活跃' : '错误'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatTime(account.last_crawl)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatTime(account.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => testAccount(account.username)}
                            disabled={loading}
                            className="text-blue-600 hover:text-blue-900 mr-4"
                          >
                            测试
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {accounts.length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-gray-500">暂无账号，点击"启动爬虫"自动创建默认账号</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
EOF
    
    print_success "前端代码创建完成"
}

# 启动MongoDB
start_mongodb() {
    print_info "启动MongoDB服务..."
    
    # 检查MongoDB是否已在运行
    if brew services list | grep mongodb-community | grep started > /dev/null; then
        print_success "MongoDB已在运行"
    else
        brew services start mongodb/brew/mongodb-community
        print_success "MongoDB启动完成"
    fi
    
    # 等待MongoDB启动
    sleep 3
    
    # 验证MongoDB连接
    if mongosh --eval "db.adminCommand('ismaster')" > /dev/null 2>&1; then
        print_success "MongoDB连接验证成功"
    else
        print_warning "MongoDB连接验证失败，但继续安装..."
    fi
}

# 创建启动脚本
create_scripts() {
    print_info "创建管理脚本..."
    cd "$PROJECT_DIR"
    
    # 创建启动脚本
    cat > start.sh << 'EOF'
#!/bin/bash

PROJECT_DIR="$HOME/xiaoba-crawler"
cd "$PROJECT_DIR"

echo "🚀 启动小八爬虫管理系统..."

# 启动MongoDB
echo "启动MongoDB..."
brew services start mongodb/brew/mongodb-community

# 启动后端
echo "启动后端服务..."
cd backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!

# 等待后端启动
sleep 5

# 启动前端
echo "启动前端服务..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo "✅ 系统启动完成！"
echo "前端地址: http://localhost:3000"
echo "后端地址: http://localhost:8001"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待用户中断
wait $BACKEND_PID $FRONTEND_PID
EOF

    # 创建停止脚本
    cat > stop.sh << 'EOF'
#!/bin/bash

echo "🛑 停止小八爬虫管理系统..."

# 停止所有相关进程
pkill -f "uvicorn server:app"
pkill -f "npm start"
pkill -f "react-scripts start"

echo "✅ 系统已停止"
EOF

    # 创建状态检查脚本
    cat > status.sh << 'EOF'
#!/bin/bash

echo "📊 小八爬虫管理系统状态"
echo "========================="

# 检查MongoDB
if brew services list | grep mongodb-community | grep started > /dev/null; then
    echo "✅ MongoDB: 运行中"
else
    echo "❌ MongoDB: 未运行"
fi

# 检查后端
if pgrep -f "uvicorn server:app" > /dev/null; then
    echo "✅ 后端服务: 运行中"
else
    echo "❌ 后端服务: 未运行"
fi

# 检查前端
if pgrep -f "react-scripts start" > /dev/null; then
    echo "✅ 前端服务: 运行中"
else
    echo "❌ 前端服务: 未运行"
fi

echo ""
echo "如果所有服务都在运行，请访问: http://localhost:3000"
EOF

    # 给脚本执行权限
    chmod +x start.sh stop.sh status.sh
    
    print_success "管理脚本创建完成"
}

# 测试安装
test_installation() {
    print_step "测试安装"
    
    cd "$PROJECT_DIR"
    
    # 测试后端
    print_info "测试后端安装..."
    cd backend
    source venv/bin/activate
    python -c "
import fastapi
import uvicorn
import selenium
import pandas
print('✅ 后端依赖检查通过')
"
    
    # 测试前端
    print_info "测试前端安装..."
    cd ../frontend
    if [ -f "package.json" ]; then
        print_success "前端配置检查通过"
    else
        print_error "前端配置检查失败"
    fi
}

# 显示使用说明
show_usage() {
    print_step "安装完成"
    
    print_success "🎉 小八爬虫管理系统安装完成！"
    echo ""
    
    print_info "📁 项目目录: $PROJECT_DIR"
    print_info "🌐 前端地址: http://localhost:3000"
    print_info "🔌 后端地址: http://localhost:8001"
    echo ""
    
    print_info "📝 使用说明:"
    echo "  启动系统: cd $PROJECT_DIR && ./start.sh"
    echo "  停止系统: cd $PROJECT_DIR && ./stop.sh"
    echo "  查看状态: cd $PROJECT_DIR && ./status.sh"
    echo ""
    
    print_info "🔧 功能说明:"
    echo "  • 多账号管理 (KR666, KR777, KR888, KR999, KR000)"
    echo "  • 50秒间隔自动爬取"
    echo "  • 实时数据监控"
    echo "  • 数据累计功能"
    echo "  • CSV导出"
    echo "  • WebSocket实时更新"
    echo ""
    
    read -p "是否现在启动系统? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PROJECT_DIR"
        ./start.sh
    else
        print_info "稍后可运行以下命令启动系统:"
        print_info "cd $PROJECT_DIR && ./start.sh"
    fi
}

# 主函数
main() {
    clear
    echo -e "${BLUE}"
    cat << 'EOF'
 __  _  _           ____         
 \ \/ \(_) __ _  _  ( __ ) __ _ 
  \  // / / _` |/ ) / _  |/ _` |
  /  \ \ | (_| | \ ( (_| | (_| |
 /_/\_\/_|\__,_|\  )\__,_|\__,_|
小八爬虫管理系统 - 一键部署脚本
EOF
    echo -e "${NC}\n"
    
    print_info "开始安装小八爬虫管理系统..."
    echo ""
    
    # 检查操作系统
    print_step "Step 1: 检查环境"
    check_os
    
    # 安装Homebrew
    print_step "Step 2: 安装Homebrew"
    install_homebrew
    
    # 安装依赖
    print_step "Step 3: 安装系统依赖"
    install_dependencies
    
    # 创建项目
    print_step "Step 4: 创建项目结构"
    create_project
    
    # 设置后端
    print_step "Step 5: 设置后端环境"
    setup_backend
    create_backend_code
    
    # 设置前端
    print_step "Step 6: 设置前端环境"
    setup_frontend
    create_frontend_code
    
    # 启动MongoDB
    print_step "Step 7: 启动数据库"
    start_mongodb
    
    # 创建管理脚本
    print_step "Step 8: 创建管理脚本"
    create_scripts
    
    # 测试安装
    print_step "Step 9: 测试安装"
    test_installation
    
    # 显示使用说明
    show_usage
}

# 运行主函数
main "$@"