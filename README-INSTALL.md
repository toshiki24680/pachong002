# 🚀 小八爬虫管理系统 - Mac一键部署指南

## 📋 快速开始

### 1️⃣ 下载安装脚本
```bash
# 在终端中运行以下命令下载安装脚本
curl -o install.sh https://raw.githubusercontent.com/your-repo/xiaoba-crawler/main/install.sh

# 或者手动创建install.sh文件，复制完整脚本内容
```

### 2️⃣ 运行一键安装
```bash
# 给脚本执行权限
chmod +x install.sh

# 运行安装脚本
./install.sh
```

### 3️⃣ 等待安装完成
脚本会自动完成以下操作：
- ✅ 检查并安装 Homebrew
- ✅ 安装 Python、Node.js、MongoDB
- ✅ 创建项目目录和文件
- ✅ 配置前后端环境
- ✅ 安装所有依赖包
- ✅ 创建管理脚本

### 4️⃣ 启动系统
```bash
# 安装完成后，进入项目目录
cd ~/xiaoba-crawler

# 启动系统
./start.sh
```

## 🎯 使用方法

### 访问系统
- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8001

### 主要功能
1. **启动爬虫**: 点击"启动爬虫"按钮
2. **生成演示数据**: 点击"生成演示数据"查看效果
3. **查看数据**: 在"数据面板"查看爬取结果
4. **账号管理**: 在"账号管理"查看和测试账号
5. **导出数据**: 点击"导出CSV"下载数据

### 管理命令
```bash
cd ~/xiaoba-crawler

# 启动系统
./start.sh

# 停止系统
./stop.sh

# 查看状态
./status.sh
```

## 🔧 预设账号
系统会自动创建以下测试账号：
- KR666 (密码: 69203532xX)
- KR777 (密码: 69203532xX)
- KR888 (密码: 69203532xX)
- KR999 (密码: 69203532xX)
- KR000 (密码: 69203532xX)

## 📊 系统特性
- 🕐 50秒间隔自动爬取
- 📱 实时WebSocket更新
- 📈 数据累计功能
- 📋 CSV导出
- 🎛️ 直观管理界面
- 🔄 多账号并发支持

## ❓ 故障排除

### 端口被占用
```bash
# 检查端口占用
lsof -i :3000
lsof -i :8001

# 停止占用进程
kill -9 <PID>
```

### MongoDB连接失败
```bash
# 重启MongoDB
brew services restart mongodb/brew/mongodb-community

# 检查MongoDB状态
brew services list | grep mongodb
```

### 重新安装
```bash
# 删除现有项目
rm -rf ~/xiaoba-crawler

# 重新运行安装脚本
./install.sh
```

## 🎉 完成！
安装完成后，您就可以使用完整的小八爬虫管理系统了！

系统包含：
- ✅ 多账号管理
- ✅ 实时数据监控  
- ✅ 自动数据累计
- ✅ CSV导出功能
- ✅ WebSocket实时更新
- ✅ 现代化Web界面