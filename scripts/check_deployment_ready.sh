#!/bin/bash

# Cloudflare + Railway 部署前检查脚本
# 用途: 验证所有必需配置是否就绪

echo "🚀 AI Signal Hunter - 部署前检查"
echo "================================"
echo ""

ERRORS=0
WARNINGS=0

# 检查1: Git仓库
echo "📋 检查 Git 配置..."
if [ -d .git ]; then
    echo "  ✅ Git仓库已初始化"

    # 检查是否有远程仓库
    if git remote -v | grep -q "origin"; then
        REMOTE_URL=$(git remote get-url origin)
        echo "  ✅ 远程仓库已配置: $REMOTE_URL"
    else
        echo "  ⚠️  未配置远程仓库 (需要推送到GitHub)"
        WARNINGS=$((WARNINGS+1))
    fi
else
    echo "  ❌ Git仓库未初始化"
    echo "     运行: git init && git add . && git commit -m 'Initial commit'"
    ERRORS=$((ERRORS+1))
fi
echo ""

# 检查2: 环境变量
echo "🔑 检查环境变量..."
if [ -f .env ]; then
    echo "  ✅ .env 文件存在"

    # 检查必需的环境变量
    if grep -q "OPENAI_API_KEY=" .env && ! grep -q "OPENAI_API_KEY=$" .env; then
        echo "  ✅ OPENAI_API_KEY 已配置"
    else
        echo "  ❌ OPENAI_API_KEY 未配置或为空"
        ERRORS=$((ERRORS+1))
    fi

    if grep -q "TAVILY_API_KEY=" .env && ! grep -q "TAVILY_API_KEY=$" .env; then
        echo "  ✅ TAVILY_API_KEY 已配置"
    else
        echo "  ❌ TAVILY_API_KEY 未配置或为空"
        ERRORS=$((ERRORS+1))
    fi

    if grep -q "GITHUB_TOKEN=" .env; then
        echo "  ⚠️  GITHUB_TOKEN 已配置 (可选)"
    else
        echo "  ⚠️  GITHUB_TOKEN 未配置 (可选,GitHub数据源需要)"
        WARNINGS=$((WARNINGS+1))
    fi
else
    echo "  ❌ .env 文件不存在"
    echo "     运行: cp .env.example .env && 编辑填入API密钥"
    ERRORS=$((ERRORS+1))
fi
echo ""

# 检查3: Docker配置
echo "🐳 检查 Docker 配置..."
if [ -f backend/Dockerfile ]; then
    echo "  ✅ backend/Dockerfile 存在"
else
    echo "  ❌ backend/Dockerfile 缺失"
    ERRORS=$((ERRORS+1))
fi

if [ -f frontend/Dockerfile ]; then
    echo "  ✅ frontend/Dockerfile 存在"
else
    echo "  ❌ frontend/Dockerfile 缺失"
    ERRORS=$((ERRORS+1))
fi

if [ -f docker-compose.prod.yml ]; then
    echo "  ✅ docker-compose.prod.yml 存在"
else
    echo "  ⚠️  docker-compose.prod.yml 不存在 (已自动生成)"
    WARNINGS=$((WARNINGS+1))
fi
echo ""

# 检查4: Next.js配置
echo "⚛️  检查 Next.js 配置..."
if [ -f frontend/next.config.js ]; then
    if grep -q "output.*standalone" frontend/next.config.js; then
        echo "  ✅ Next.js standalone模式已启用"
    else
        echo "  ⚠️  Next.js standalone模式未启用"
        echo "     需要在 next.config.js 中添加: output: 'standalone'"
        WARNINGS=$((WARNINGS+1))
    fi
else
    echo "  ❌ frontend/next.config.js 不存在"
    ERRORS=$((ERRORS+1))
fi
echo ""

# 检查5: CORS配置
echo "🌐 检查 CORS 配置..."
if grep -q "pages.dev" backend/app/main.py; then
    echo "  ✅ Cloudflare Pages域名已添加到CORS"
else
    echo "  ⚠️  Cloudflare Pages域名未添加到CORS"
    echo "     需要在 backend/app/main.py 中添加: https://*.pages.dev"
    WARNINGS=$((WARNINGS+1))
fi
echo ""

# 检查6: 前端环境变量
echo "🎨 检查前端配置..."
if [ -f frontend/.env.production ]; then
    echo "  ✅ frontend/.env.production 存在"
    if grep -q "NEXT_PUBLIC_API_URL" frontend/.env.production; then
        echo "  ✅ NEXT_PUBLIC_API_URL 已配置"
    else
        echo "  ⚠️  NEXT_PUBLIC_API_URL 未配置"
        WARNINGS=$((WARNINGS+1))
    fi
else
    echo "  ⚠️  frontend/.env.production 不存在"
    echo "     部署后需要在Cloudflare Pages中配置环境变量"
    WARNINGS=$((WARNINGS+1))
fi
echo ""

# 检查7: 数据库
echo "💾 检查数据库..."
if [ -f backend/data/signals.db ]; then
    DB_SIZE=$(du -h backend/data/signals.db | cut -f1)
    echo "  ✅ 数据库文件存在 (大小: $DB_SIZE)"
else
    echo "  ⚠️  数据库文件不存在 (首次部署会自动创建)"
    WARNINGS=$((WARNINGS+1))
fi
echo ""

# 总结
echo "================================"
echo "📊 检查结果汇总"
echo "================================"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "🎉 所有检查通过! 可以开始部署了!"
    echo ""
    echo "📋 下一步:"
    echo "  1. 推送代码到GitHub: git push origin main"
    echo "  2. 访问 https://railway.app 部署后端"
    echo "  3. 访问 https://dash.cloudflare.com 部署前端"
    echo "  4. 参考 CLOUDFLARE_DEPLOYMENT_GUIDE.md 完整步骤"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  发现 $WARNINGS 个警告,但可以继续部署"
    echo ""
    echo "📋 建议修复警告后再部署,或在部署过程中配置"
    echo "  参考 CLOUDFLARE_DEPLOYMENT_GUIDE.md"
    exit 0
else
    echo "❌ 发现 $ERRORS 个错误和 $WARNINGS 个警告"
    echo ""
    echo "🛠️  请先修复错误再部署:"
    echo "  - 配置缺失的环境变量"
    echo "  - 初始化Git仓库"
    echo "  - 检查Docker配置文件"
    echo ""
    echo "📖 详细指南: CLOUDFLARE_DEPLOYMENT_GUIDE.md"
    exit 1
fi
