# Signal Hunter 周刊功能 - 快速验证清单

## 📋 验证前准备

### 1. 启动服务

```bash
# 终端 1：启动后端
cd /Users/felix/Desktop/code/signal/backend
python3 app/main.py

# 终端 2：启动前端
cd /Users/felix/Desktop/code/signal/frontend
npm run dev
```

### 2. 确认服务运行

- 后端：http://localhost:8000/docs （FastAPI 文档）
- 前端：http://localhost:3000 （Next.js 首页）

---

## ✅ 验证步骤

### Step 1: 后端 API 验证

#### 1.1 测试周刊列表 API
```bash
curl http://localhost:8000/api/newsletters
```

**预期结果**：
- 状态码：200
- 返回结构：`{ items: [], total: 0, page: 1, page_size: 10 }`
- 如果暂无周刊，items 为空数组

#### 1.2 手动生成测试周刊
```bash
curl -X POST "http://localhost:8000/api/newsletters?force=true"
```

**预期结果**：
- 状态码：200
- 返回完整的 NewsletterDetail 对象
- 包含 id, title, content 等字段

#### 1.3 再次获取列表
```bash
curl http://localhost:8000/api/newsletters
```

**预期结果**：
- items 包含刚才生成的周刊
- total = 1

#### 1.4 测试详情 API
```bash
# 使用步骤 1.2 返回的 ID
curl http://localhost:8000/api/newsletters/1
```

**预期结果**：
- 状态码：200
- content 字段包含完整的 Markdown 内容

#### 1.5 测试错误处理
```bash
# 测试 404
curl http://localhost:8000/api/newsletters/99999

# 预期：404 Not Found
```

---

### Step 2: 前端页面验证

#### 2.1 访问周刊列表页
```
http://localhost:3000/newsletters
```

**检查点**：
- ✅ 页面正常加载（无 404）
- ✅ 显示标题 "📰 技术周刊"
- ✅ 如果有周刊，显示卡片网格
- ✅ 如果无周刊，显示"暂无周刊"
- ✅ 底部显示说明文字

#### 2.2 点击周刊卡片
```
点击任意周刊卡片 → 跳转到详情页
```

**检查点**：
- ✅ URL 变为 `/newsletters/{id}`
- ✅ 显示完整周刊内容
- ✅ Markdown 格式正确渲染（标题、列表、链接）
- ✅ 返回按钮可点击

#### 2.3 检查导航链接
```
访问首页 http://localhost:3000
滚动到底部，查看导航栏
```

**检查点**：
- ✅ 显示"周刊"链接（带报纸图标）
- ✅ 点击后跳转到 `/newsletters`

---

### Step 3: 缓存验证

#### 3.1 首次访问（缓存未命中）
```bash
# 查看后端日志，应该看到：
# [Cache] MISS: newsletters:list:...
```

#### 3.2 二次访问（缓存命中）
```bash
# 再次访问同一页面，查看后端日志
# 应该看到：[Cache] HIT: newsletters:list:...
```

#### 3.3 缓存过期
- 等待 5 分钟（列表页）或 10 分钟（详情页）
- 再次访问，应该重新从数据库加载

---

### Step 4: 响应式设计验证

#### 4.1 桌面端（宽度 > 1024px）
- 网格布局：3 列
- 卡片间距适中

#### 4.2 平板端（768px < 宽度 < 1024px）
- 网格布局：2 列

#### 4.3 移动端（宽度 < 768px）
- 网格布局：1 列
- 卡片占满宽度
- 触摸友好

---

### Step 5: 暗色模式验证

#### 5.1 切换到暗色模式
```
（根据系统设置或浏览器扩展）
```

**检查点**：
- ✅ 背景变为深色
- ✅ 文字自动适配颜色
- ✅ Markdown 内容可读性良好
- ✅ 无颜色冲突

---

## 🧪 运行完整测试脚本

```bash
cd /Users/felix/Desktop/code/signal/backend
python3 scripts/test_newsletter_api.py
```

**预期输出**：
```
✅ 成功获取周刊列表
✅ 成功获取周刊详情
✅ 成功生成周刊
✅ 正确返回 404
```

---

## 📊 性能检查

### 前端性能
- 打开 DevTools → Network
- 刷新周刊列表页
- 检查：
  - DOMContentLoaded < 100ms
  - 页面完全加载 < 1s

### 后端性能
- 查看后端日志中的响应时间
- 首次访问：< 500ms（无缓存）
- 二次访问：< 50ms（有缓存）

---

## 🐛 常见问题排查

### 问题 1: 前端 404
**原因**：Next.js 未识别新页面
**解决**：
```bash
cd frontend
rm -rf .next
npm run dev
```

### 问题 2: 后端导入错误
**原因**：路径问题
**解决**：
```bash
cd backend
export PYTHONPATH=/Users/felix/Desktop/code/signal/backend:$PYTHONPATH
python3 app/main.py
```

### 问题 3: 周刊生成失败
**原因**：数据库中没有本周的资源
**解决**：
- 确保有 score >= 70 的资源
- 检查资源的 published_at 在本周范围内

### 问题 4: 缓存不工作
**原因**：Redis 未启动
**解决**：
```bash
# 检查 Redis
redis-cli ping

# 如果未启动，启动 Redis
brew services start redis
```

---

## ✅ 完成标准

所有验证通过后，应该能够：

1. ✅ 访问 `/newsletters` 查看所有周刊
2. ✅ 点击任意周刊查看完整内容
3. ✅ Markdown 格式正确渲染
4. ✅ 手动生成新周刊（通过 API）
5. ✅ 缓存机制工作正常
6. ✅ 错误处理正确（404/400/500）
7. ✅ 响应式布局适配移动端
8. ✅ 暗色模式兼容

---

## 📝 备注

- 周刊自动生成时间：每周五 17:00
- 缓存自动刷新：列表 5 分钟，详情 10 分钟
- 最低评分阈值：70 分
- 精选评分阈值：85 分

---

**验证通过后，周刊功能即可正式上线！** 🎉
