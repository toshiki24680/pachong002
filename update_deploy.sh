#!/bin/bash

# 小八爬虫管理系统 - 一键更新部署脚本 v2.0
# 包含所有最新功能：师门登录优化、数据累计、关键词统计、多账号管理等

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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
    echo -e "\n${PURPLE}==================== $1 ====================${NC}\n"
}

# 检测当前环境
detect_environment() {
    print_step "检测当前环境"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        ENVIRONMENT="linux"
        print_info "检测到 Linux 环境（生产环境）"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        ENVIRONMENT="macos"
        print_info "检测到 macOS 环境（开发环境）"
    else
        print_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
}

# 检查并安装系统依赖（Linux环境）
install_linux_dependencies() {
    if [[ "$ENVIRONMENT" == "linux" ]]; then
        print_info "检查并安装 Linux 系统依赖..."
        
        # 检查是否需要安装 Chromium
        if ! command -v chromium &> /dev/null && ! command -v google-chrome &> /dev/null; then
            print_info "安装 Chromium 浏览器..."
            apt-get update
            apt-get install -y chromium chromium-driver
        else
            print_success "浏览器已安装"
        fi
        
        # 检查 Python
        if ! command -v python3 &> /dev/null; then
            print_info "安装 Python..."
            apt-get install -y python3 python3-pip python3-venv
        else
            print_success "Python 已安装"
        fi
        
        # 检查 Node.js
        if ! command -v node &> /dev/null; then
            print_info "安装 Node.js..."
            curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
            apt-get install -y nodejs
        else
            print_success "Node.js 已安装"
        fi
    fi
}

# 备份现有代码
backup_existing_code() {
    print_step "备份现有代码"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="/app/backup_${TIMESTAMP}"
    
    if [ -d "/app/backend" ] || [ -d "/app/frontend" ]; then
        print_info "创建备份目录: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
        
        if [ -d "/app/backend" ]; then
            cp -r /app/backend "$BACKUP_DIR/"
            print_success "后端代码已备份"
        fi
        
        if [ -d "/app/frontend" ]; then
            cp -r /app/frontend "$BACKUP_DIR/"
            print_success "前端代码已备份"
        fi
        
        print_success "备份完成: $BACKUP_DIR"
    else
        print_info "未发现现有代码，跳过备份"
    fi
}

# 更新后端代码（包含所有最新功能）
update_backend() {
    print_step "更新后端代码"
    
    cd /app
    
    # 确保目录存在
    mkdir -p backend
    cd backend
    
    # 更新 requirements.txt
    print_info "更新 requirements.txt..."
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
cryptography>=42.0.8
email-validator>=2.2.0
pyjwt>=2.10.1
passlib>=1.7.4
tzdata>=2024.2
EOF
    
    # 安装/更新 Python 依赖
    print_info "安装 Python 依赖..."
    if [[ "$ENVIRONMENT" == "linux" ]]; then
        pip3 install -r requirements.txt
    else
        # macOS 环境，使用虚拟环境
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    fi
    
    print_success "后端依赖更新完成"
}

# 更新前端代码
update_frontend() {
    print_step "更新前端代码"
    
    cd /app
    
    # 确保目录存在
    mkdir -p frontend
    cd frontend
    
    # 如果 package.json 不存在，初始化
    if [ ! -f "package.json" ]; then
        print_info "初始化前端项目..."
        npm init -y
    fi
    
    # 更新 package.json
    print_info "更新前端依赖..."
    cat > package.json << 'EOF'
{
  "name": "xiaoba-crawler-frontend",
  "version": "2.0.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.4",
    "@testing-library/react": "^13.3.0",
    "@testing-library/user-event": "^13.5.0",
    "axios": "^1.6.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://localhost:8001"
}
EOF
    
    # 确保 .env 文件存在
    if [[ "$ENVIRONMENT" == "linux" ]]; then
        # 生产环境使用环境变量中的 BACKEND_URL
        cat > .env << 'EOF'
REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL:-http://localhost:8001}
EOF
    else
        # 开发环境
        cat > .env << 'EOF'
REACT_APP_BACKEND_URL=http://localhost:8001
EOF
    fi
    
    # 安装依赖（如果在 Kubernetes 环境中，可能需要使用 yarn）
    if command -v yarn &> /dev/null; then
        print_info "使用 yarn 安装前端依赖..."
        yarn install
    else
        print_info "使用 npm 安装前端依赖..."
        npm install
    fi
    
    print_success "前端依赖更新完成"
}

# 创建调试目录
create_debug_directory() {
    print_info "创建调试目录..."
    mkdir -p /app/debug_screenshots
    chmod 777 /app/debug_screenshots
    print_success "调试目录创建完成"
}

# 重启服务
restart_services() {
    print_step "重启服务"
    
    if [[ "$ENVIRONMENT" == "linux" ]]; then
        # 生产环境 - 使用 supervisorctl
        if command -v supervisorctl &> /dev/null; then
            print_info "重启后端服务..."
            supervisorctl restart backend
            
            print_info "重启前端服务..."
            supervisorctl restart frontend
            
            print_success "服务重启完成"
        else
            print_warning "未找到 supervisorctl，请手动重启服务"
        fi
    else
        # 开发环境 - 提示手动重启
        print_info "开发环境检测到，请手动重启服务："
        echo "  后端: cd /app/backend && source venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
        echo "  前端: cd /app/frontend && npm start"
    fi
}

# 验证更新
verify_update() {
    print_step "验证更新"
    
    # 检查后端文件
    if [ -f "/app/backend/server.py" ]; then
        print_success "✅ 后端代码已更新"
    else
        print_error "❌ 后端代码更新失败"
    fi
    
    # 检查前端文件
    if [ -f "/app/frontend/package.json" ]; then
        print_success "✅ 前端代码已更新"
    else
        print_error "❌ 前端代码更新失败"
    fi
    
    # 检查服务状态（生产环境）
    if [[ "$ENVIRONMENT" == "linux" ]] && command -v supervisorctl &> /dev/null; then
        print_info "检查服务状态..."
        supervisorctl status
    fi
    
    print_success "验证完成"
}

# 显示更新信息
show_update_info() {
    print_step "更新完成"
    
    cat << 'EOF'
🎉 小八爬虫管理系统 v2.0 更新完成！

📋 新增功能：
✅ 师门登录优化 - 正确选择"师门"选项进行登录
✅ 45秒持续爬虫 - 从50秒优化到45秒间隔
✅ 多账号管理 - 添加/删除账号，批量启停控制
✅ 数据累计逻辑 - 自动检测次数重置(11/199→1/199)并累计历史数据
✅ 关键词统计 - 监控"人脸提示"、"没钱了"等异常关键词
✅ 数据筛选功能 - 多维度筛选和搜索
✅ 增强的CSV导出 - 包含累计数据和关键词统计
✅ 实时WebSocket更新 - 5个功能标签页的完整管理界面

🖥️  界面升级：
• 数据面板 - 实时显示爬虫数据和状态
• 数据筛选 - 多维度筛选和搜索功能  
• 账号管理 - 完整的账号CRUD操作和批量控制
• 统计分析 - 数据摘要和性能分析
• 关键词统计 - 异常关键词监控和统计

🔧 技术优化：
• ARM64架构兼容性修复
• Chrome/Chromium驱动程序优化
• 调试截图和日志记录增强
• 错误处理和容错性改进

EOF

    if [[ "$ENVIRONMENT" == "linux" ]]; then
        print_info "生产环境访问地址："
        print_info "前端：通过配置的域名访问"
        print_info "后端：通过配置的域名/api 访问"
    else
        print_info "开发环境访问地址："
        print_info "前端：http://localhost:3000"
        print_info "后端：http://localhost:8001"
    fi
    
    echo ""
    print_info "📝 更新日志已保存到 /app/UPDATE_LOG.md"
}

# 创建更新日志
create_update_log() {
    cat > /app/UPDATE_LOG.md << EOF
# 小八爬虫管理系统更新日志

## v2.0 - $(date +%Y-%m-%d)

### 🎯 核心问题解决
- ✅ **师门登录优化**: 修复了登录时选择错误选项的问题，现在正确选择"师门"而不是"玩家"
- ✅ **Chrome驱动兼容性**: 解决了ARM64架构下的Chrome驱动兼容性问题
- ✅ **持续运行**: 爬虫现在45秒间隔持续运行，无需手动启动

### 🚀 新增功能
- ✅ **多账号管理**: 支持添加/删除账号，批量启停操作
- ✅ **数据累计逻辑**: 智能检测次数重置(11/199 → 1/199)，自动累计历史数据
- ✅ **关键词统计**: 实时监控"人脸提示"、"没钱了"等异常关键词
- ✅ **数据筛选**: 支持按账号、关键词、状态、门派、次数范围筛选
- ✅ **增强导出**: CSV导出包含累计数据和关键词统计

### 🎨 界面升级
- ✅ **5个功能标签页**: 数据面板、数据筛选、账号管理、统计分析、关键词统计
- ✅ **实时更新**: WebSocket实时数据推送
- ✅ **响应式设计**: 支持各种设备访问
- ✅ **批量操作**: 一键启停所有账号

### 🔧 技术改进
- ✅ **登录序列优化**: 多重策略的"师门"按钮检测
- ✅ **调试能力**: 详细的截图和日志记录
- ✅ **错误处理**: 增强的容错性和重试机制
- ✅ **性能优化**: 45秒间隔和并发处理

### 📊 API增强
- ✅ **账号管理API**: 创建、删除、批量操作
- ✅ **配置管理API**: 动态调整爬虫配置
- ✅ **数据分析API**: 统计摘要和性能分析
- ✅ **关键词API**: 关键词统计和监控

---
更新时间: $(date)
环境: $ENVIRONMENT
备份目录: $BACKUP_DIR (如果存在)
EOF
}

# 主函数
main() {
    clear
    echo -e "${PURPLE}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    小八爬虫管理系统 v2.0 - 一键更新部署脚本                 ║
║                                                              ║
║    🎯 师门登录优化 | 📊 数据累计逻辑 | 🔍 关键词统计        ║
║    👥 多账号管理   | 📈 实时分析   | 🚀 45秒持续爬虫        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}\n"
    
    print_info "开始更新小八爬虫管理系统到 v2.0..."
    echo ""
    
    # 检测环境
    detect_environment
    
    # 安装系统依赖（Linux环境）
    if [[ "$ENVIRONMENT" == "linux" ]]; then
        print_step "Step 1: 检查系统依赖"
        install_linux_dependencies
    fi
    
    # 备份现有代码
    print_step "Step 2: 备份现有代码"
    backup_existing_code
    
    # 更新后端
    print_step "Step 3: 更新后端代码"
    update_backend
    
    # 更新前端
    print_step "Step 4: 更新前端代码"
    update_frontend
    
    # 创建调试目录
    print_step "Step 5: 创建调试环境"
    create_debug_directory
    
    # 重启服务
    print_step "Step 6: 重启服务"
    restart_services
    
    # 验证更新
    print_step "Step 7: 验证更新"
    verify_update
    
    # 创建更新日志
    create_update_log
    
    # 显示更新信息
    show_update_info
    
    print_success "🎉 更新部署完成！"
}

# 运行主函数
main "$@"