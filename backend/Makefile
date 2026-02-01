# Makefile for Signal Backend
# 便捷的开发工具命令

.PHONY: help install dev test lint format type-check clean run docker-build docker-up docker-down

# 默认目标
help:
	@echo "Signal Backend - 可用命令："
	@echo ""
	@echo "  make install         - 安装依赖"
	@echo "  make dev            - 开发模式运行"
	@echo "  make test           - 运行测试"
	@echo "  make test-cov       - 运行测试并生成覆盖率报告"
	@echo "  make lint           - 运行代码检查（ruff）"
	@echo "  make format         - 格式化代码（black + isort）"
	@echo "  make type-check     - 类型检查（mypy）"
	@echo "  make check          - 运行所有检查（lint + type-check + test）"
	@echo "  make clean          - 清理临时文件"
	@echo "  make run            - 运行应用"
	@echo "  make docker-build   - 构建Docker镜像"
	@echo "  make docker-up      - 启动Docker容器"
	@echo "  make docker-down    - 停止Docker容器"
	@echo "  make docker-logs    - 查看Docker日志"
	@echo ""

# 安装依赖
install:
	@echo "安装Python依赖..."
	pip install --upgrade pip
	pip install -r requirements.txt

# 开发模式
dev:
	@echo "启动开发服务器..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
test:
	@echo "运行测试..."
	pytest -v

# 运行测试并生成覆盖率报告
test-cov:
	@echo "运行测试并生成覆盖率报告..."
	pytest --cov=app --cov-report=html --cov-report=term-missing -v
	@echo "覆盖率报告: htmlcov/index.html"

# 代码检查
lint:
	@echo "运行代码检查（ruff）..."
	ruff check app/
	@echo "✅ Rinting完成"

# 格式化代码
format:
	@echo "格式化代码（black + isort）..."
	black app/
	isort app/
	@echo "✅ 格式化完成"

# 类型检查
type-check:
	@echo "运行类型检查（mypy）..."
	mypy app/
	@echo "✅ 类型检查完成"

# 运行所有检查
check: lint type-check test
	@echo ""
	@echo "✅ 所有检查通过！"

# 清理临时文件
clean:
	@echo "清理临时文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage
	@echo "✅ 清理完成"

# 运行应用
run:
	@echo "启动应用..."
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Docker构建
docker-build:
	@echo "构建Docker镜像..."
	docker-compose build

# Docker启动
docker-up:
	@echo "启动Docker容器..."
	docker-compose up -d

# Docker停止
docker-down:
	@echo "停止Docker容器..."
	docker-compose down

# Docker日志
docker-logs:
	docker-compose logs -f backend

# Docker重启
docker-restart:
	@echo "重启Docker容器..."
	docker-compose restart

# 数据库迁移（如果需要）
db-migrate:
	@echo "运行数据库迁移..."
	@echo "TODO: 添加迁移命令"

# 数据库回滚
db-rollback:
	@echo "回滚数据库迁移..."
	@echo "TODO: 添加回滚命令"

# 创建新的数据库迁移
db-create-migration:
	@echo "创建新的数据库迁移..."
	@echo "TODO: 添加创建迁移命令"

# 安装Playwright浏览器
playwright-install:
	@echo "安装Playwright浏览器..."
	playwright install chromium

# 代码质量报告
quality-report:
	@echo "生成代码质量报告..."
	@echo "=== Linting ==="
	-ruff check app/ --output-format=text
	@echo ""
	@echo "=== Type Checking ==="
	-mypy app/
	@echo ""
	@echo "=== Test Coverage ==="
	-pytest --cov=app --cov-report=term-missing
	@echo ""
	@echo "✅ 质量报告生成完成"
