# 后端 Docker 镜像（包含 Playwright）
# 多阶段构建优化镜像大小

# ============================================
# 构建阶段
# ============================================
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy AS builder

WORKDIR /build

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖到临时目录
RUN pip install --user --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器
ENV PATH=/root/.local/bin:$PATH
RUN python -m playwright install chromium

# ============================================
# 运行阶段
# ============================================
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

WORKDIR /app

# 从构建阶段复制已安装的包
COPY --from=builder /root/.local /root/.local

# 确保 Python 能找到已安装的包
ENV PATH=/root/.local/bin:$PATH

# 复制应用代码
COPY app ./app

# 复制 BestBlog OPML 配置文件
COPY BestBlog ./BestBlog

# 保持 root 用户运行（容器内安全隔离）

# 暴露端口
EXPOSE 8000

# 健康检查（改进版）
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
