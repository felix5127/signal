#!/bin/bash

# 一键准备Cloudflare部署
# 自动完成所有必需的配置

set -e  # 遇到错误立即退出

echo "🚀 Signal - 部署准备脚本"
echo "======================================"
echo ""

# Step 1: 初始化Git
echo "📋 Step 1: 初始化 Git 仓库..."
if [ ! -d .git ]; then
    git init
    echo "  ✅ Git仓库已初始化"
else
    echo "  ℹ️  Git仓库已存在,跳过"
fi
echo ""

# Step 2: 创建 .gitignore
echo "📝 Step 2: 创建 .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.so
.Python
env/
venv/
*.egg-info/
.pytest_cache/

# Node
node_modules/
.next/
out/
.pnpm-store/
npm-debug.log*

# Environment
.env
.env.local
.env.*.local

# Database
backend/data/*.db
backend/data/*.db-shm
backend/data/*.db-wal

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Build
dist/
build/
EOF
echo "  ✅ .gitignore 已创建"
echo ""

# Step 3: 创建前端生产环境配置
echo "🎨 Step 3: 创建前端生产配置..."
cat > frontend/.env.production << 'EOF'
# 部署到Railway后,将此URL替换为实际的后端地址
# 格式: https://your-backend.railway.app
NEXT_PUBLIC_API_URL=https://REPLACE_ME_WITH_RAILWAY_BACKEND_URL
EOF
echo "  ✅ frontend/.env.production 已创建"
echo "  ⚠️  部署后端后,需要编辑此文件替换 NEXT_PUBLIC_API_URL"
echo ""

# Step 4: 提交到Git
echo "📦 Step 4: 提交所有文件到Git..."
git add .
git status --short
echo ""

read -p "是否提交所有更改? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git commit -m "feat: prepare for Cloudflare Pages + Railway deployment

- Add production docker-compose config
- Update CORS for Cloudflare Pages
- Add deployment guide and scripts
- Configure frontend for production build
"
    echo "  ✅ 已提交到本地Git仓库"
else
    echo "  ⏭️  跳过提交"
fi
echo ""

# Step 5: 提示下一步
echo "======================================"
echo "✅ 部署准备完成!"
echo "======================================"
echo ""
echo "📋 下一步操作:"
echo ""
echo "1️⃣  推送到GitHub:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/signal-hunter.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "2️⃣  部署后端到Railway:"
echo "   - 访问 https://railway.app"
echo "   - 用GitHub登录"
echo "   - Deploy from GitHub repo"
echo "   - 选择 signal-hunter 仓库"
echo "   - 配置环境变量 (OPENAI_API_KEY, TAVILY_API_KEY)"
echo "   - 添加Volume: /app/data (1GB)"
echo "   - 获取后端URL"
echo ""
echo "3️⃣  更新前端配置:"
echo "   编辑 frontend/.env.production"
echo "   将 NEXT_PUBLIC_API_URL 改为 Railway 后端URL"
echo "   提交并推送: git add . && git commit -m 'Update backend URL' && git push"
echo ""
echo "4️⃣  部署前端到Cloudflare Pages:"
echo "   - 访问 https://dash.cloudflare.com"
echo "   - Workers & Pages → Create → Connect to Git"
echo "   - 选择 signal-hunter 仓库"
echo "   - 配置构建命令: cd frontend && npm install && npm run build"
echo "   - 添加环境变量: NEXT_PUBLIC_API_URL"
echo ""
echo "📖 详细步骤请查看: CLOUDFLARE_DEPLOYMENT_GUIDE.md"
echo ""
