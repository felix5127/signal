# Cloudflare Pages + Railway 部署指南

**部署架构**:
- 前端 → Cloudflare Pages (免费,全球CDN)
- 后端 → Railway (Docker容器,持久化存储)
- 域名 → Cloudflare DNS (已有)

**预计成本**: $5-10/月 (仅Railway后端)
**部署时间**: 30-60分钟

---

## 📋 前置准备

### 必需账号
- [x] Cloudflare 账号 (已有域名)
- [ ] [Railway](https://railway.app) 账号 (GitHub登录)
- [ ] GitHub 仓库 (用于代码托管)

### 必需环境变量
```bash
OPENAI_API_KEY=sk-or-v1-xxx  # OpenRouter API Key
TAVILY_API_KEY=tvly-xxx      # Tavily Search API Key
GITHUB_TOKEN=ghp_xxx         # GitHub Personal Access Token (可选)
```

---

## Part 1: 后端部署到Railway (20分钟)

### Step 1.1: 准备GitHub仓库 (5分钟)

```bash
# 1. 初始化Git (如果还没有)
cd /Users/felix/Desktop/code/signal
git init
git add .
git commit -m "Initial commit: AI Signal Hunter v1.0"

# 2. 推送到GitHub
git remote add origin https://github.com/YOUR_USERNAME/signal-hunter.git
git branch -M main
git push -u origin main
```

### Step 1.2: 部署后端到Railway (10分钟)

1. **登录Railway Dashboard**
   - 访问 https://railway.app/dashboard
   - 用GitHub账号登录

2. **创建新项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 授权访问你的仓库
   - 选择 `signal-hunter` 仓库

3. **配置后端服务**
   - Railway会自动检测到 `backend/Dockerfile`
   - 点击创建的服务 → Settings → 修改:
     - **Name**: `signal-hunter-backend`
     - **Root Directory**: `backend`
     - **Dockerfile Path**: `Dockerfile`

4. **配置环境变量**
   - 点击 "Variables" 标签
   - 添加以下变量:
     ```
     OPENAI_API_KEY=sk-or-v1-xxx
     TAVILY_API_KEY=tvly-xxx
     GITHUB_TOKEN=ghp_xxx
     DATABASE_URL=sqlite:///./data/signals.db
     LOG_LEVEL=INFO
     ```

5. **配置持久化存储 (重要!)**
   - 点击 "Settings" → "Volumes"
   - 添加Volume:
     - Mount Path: `/app/data`
     - Size: 1 GB
   - 点击 "Add Volume"

6. **重新部署**
   - 点击 "Deployments" → "Deploy"
   - 等待构建完成 (~5-8分钟)

7. **获取后端URL**
   - 构建成功后,点击 "Settings" → "Domains"
   - 点击 "Generate Domain"
   - 复制生成的域名,例如: `signal-hunter-backend.railway.app`
   - **保存这个URL,稍后配置前端需要用到!**

### Step 1.3: 验证后端部署 (2分钟)

```bash
# 测试健康检查
curl https://signal-hunter-backend.railway.app/health

# 应该返回:
# {"status":"ok","database":"ok","scheduler":"running"}

# 测试API
curl https://signal-hunter-backend.railway.app/api/signals?limit=5

# 应该返回信号列表JSON
```

---

## Part 2: 前端部署到Cloudflare Pages (15分钟)

### Step 2.1: 配置前端环境变量

修改前端配置,指向Railway后端:

```bash
# 在项目根目录创建 .env.production
cat > /Users/felix/Desktop/code/signal/frontend/.env.production << 'EOF'
NEXT_PUBLIC_API_URL=https://signal-hunter-backend.railway.app
EOF

# 提交到Git
git add frontend/.env.production
git commit -m "Add production environment config"
git push
```

### Step 2.2: 部署到Cloudflare Pages (10分钟)

1. **登录Cloudflare Dashboard**
   - 访问 https://dash.cloudflare.com
   - 选择你的账号

2. **创建Pages项目**
   - 左侧菜单点击 "Workers & Pages"
   - 点击 "Create application"
   - 选择 "Pages" 标签 → "Connect to Git"

3. **连接GitHub仓库**
   - 授权Cloudflare访问GitHub
   - 选择 `signal-hunter` 仓库
   - 点击 "Begin setup"

4. **配置构建设置**
   ```
   Project name: signal-hunter
   Production branch: main

   Build settings:
   Framework preset: Next.js
   Build command: cd frontend && npm install && npm run build
   Build output directory: frontend/.next
   Root directory: (留空)

   Environment variables:
   NEXT_PUBLIC_API_URL = https://signal-hunter-backend.railway.app
   ```

5. **开始部署**
   - 点击 "Save and Deploy"
   - 等待构建完成 (~3-5分钟)
   - Cloudflare会自动分配一个域名: `signal-hunter.pages.dev`

### Step 2.3: 绑定自定义域名 (5分钟)

1. **添加自定义域名**
   - 在Pages项目页面,点击 "Custom domains"
   - 点击 "Set up a custom domain"
   - 输入你的域名,例如: `signal.your-domain.com`

2. **配置DNS**
   - Cloudflare会自动添加CNAME记录
   - 如果你的域名已在Cloudflare托管,会自动配置
   - 如果不是,需要添加CNAME记录:
     ```
     Type: CNAME
     Name: signal
     Target: signal-hunter.pages.dev
     Proxy: Enabled (橙色云朵)
     ```

3. **等待DNS生效**
   - 通常1-5分钟
   - 访问 `https://signal.your-domain.com` 测试

---

## Part 3: 最终配置与测试 (10分钟)

### Step 3.1: 更新后端CORS域名

回到 `backend/app/main.py`,将 `*.your-domain.com` 替换为实际域名:

```python
allow_origins=[
    "http://localhost:3000",
    "http://frontend:3000",
    "https://*.pages.dev",
    "https://signal.your-domain.com",  # 替换为实际域名
],
```

提交并推送:
```bash
git add backend/app/main.py
git commit -m "Update CORS for production domain"
git push
```

Railway会自动重新部署后端 (~2分钟)。

### Step 3.2: 完整功能测试

1. **访问前端**
   - 打开 `https://signal.your-domain.com`
   - 应该看到Signal列表

2. **测试核心功能**
   - [x] 查看Signal列表
   - [x] 点击Signal查看详情
   - [x] 点击"生成深度研究报告"
   - [x] 等待报告生成 (~60秒)
   - [x] 验证Markdown渲染 (表格、代码高亮)

3. **检查性能**
   - 前端加载速度: 应该很快 (Cloudflare CDN)
   - API响应时间: 应该<500ms
   - 报告生成: 30-60秒

---

## 🎯 常见问题与解决方案

### Q1: 前端部署失败 "Build exceeded maximum duration"

**原因**: Cloudflare Pages免费版构建限制20分钟

**解决**:
```bash
# 优化 package.json,使用 npm ci 替代 npm install
Build command: cd frontend && npm ci && npm run build
```

### Q2: 后端数据丢失

**原因**: 没有配置Volume持久化

**解决**:
确保Railway中配置了Volume:
- Settings → Volumes → Add Volume
- Mount Path: `/app/data`

### Q3: CORS错误

**原因**: 前端域名未添加到后端CORS白名单

**解决**:
检查 `backend/app/main.py` 中的 `allow_origins` 是否包含你的域名。

### Q4: 定时任务不运行

**原因**: Railway容器可能休眠 (免费版)

**解决**:
升级到Railway Hobby Plan ($5/月),或使用外部Cron服务定期ping。

---

## 💰 成本明细

### 免费额度
- Cloudflare Pages: **免费** (无限流量,无限请求)
- Cloudflare DNS: **免费** (已有域名)
- Railway: **$5 credit/月** (免费额度)

### 付费后
- Railway Hobby Plan: **$5/月起**
- Cloudflare Workers (如需): **$5/月**

**总计**: **$5-10/月** (仅后端费用)

---

## 🚀 部署后优化建议

### 1. 配置Cloudflare缓存
在Cloudflare Dashboard → Caching中:
- 启用 "Always Online"
- 配置缓存TTL
- 设置缓存规则

### 2. 启用Cloudflare分析
- 访问 "Analytics & Logs"
- 查看流量统计
- 监控性能指标

### 3. 配置Railway监控
- 安装Railway CLI: `npm install -g @railway/cli`
- 查看日志: `railway logs`
- 监控资源使用

### 4. 设置自动部署
- GitHub → Settings → Webhooks
- Cloudflare Pages和Railway都支持自动部署
- 推送到main分支即自动部署

---

## ✅ 部署检查清单

### 后端 (Railway)
- [ ] GitHub仓库已创建并推送
- [ ] Railway项目已创建
- [ ] 环境变量已配置 (3个必需)
- [ ] Volume持久化已配置 (1GB)
- [ ] 健康检查通过 (/health)
- [ ] 后端域名已获取并保存

### 前端 (Cloudflare Pages)
- [ ] .env.production已创建
- [ ] Cloudflare Pages项目已创建
- [ ] 构建设置已配置
- [ ] 自定义域名已绑定
- [ ] DNS记录已添加
- [ ] HTTPS证书已激活

### 功能测试
- [ ] 前端可正常访问
- [ ] Signal列表正常显示
- [ ] Signal详情页正常
- [ ] Deep Research功能可用
- [ ] Markdown渲染正确
- [ ] 跨域请求正常

---

## 🎉 完成!

部署完成后,你将拥有:
- ✅ 全球CDN加速的前端 (Cloudflare)
- ✅ 稳定可靠的后端API (Railway)
- ✅ 自定义域名 (你的域名)
- ✅ 自动HTTPS证书
- ✅ 持久化数据存储
- ✅ 自动部署流水线

**访问地址**: `https://signal.your-domain.com`

**下一步**:
- 测试所有功能
- 监控运行状态
- 根据需要优化性能

---

**生成时间**: 2025-12-30
**作者**: Claude Sonnet 4.5
**文档版本**: v1.0
