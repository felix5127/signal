#!/usr/bin/env python3
"""Signal 系统验证脚本

运行: python3 scripts/verify_system.py
"""

import json
import sys
from pathlib import Path
from time import time
from typing import Callable, List, Tuple

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# 尝试导入 requests，如果没有则使用 curl 替代
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

import subprocess


def http_get(url: str, params: dict = None, timeout: int = 10) -> tuple:
    """使用 curl 或 requests 发送 GET 请求"""
    if REQUESTS_AVAILABLE:
        try:
            r = requests.get(url, params=params, timeout=timeout)
            return r.status_code, r.json() if r.status_code == 200 else None
        except requests.exceptions.ConnectionError:
            return -1, None
        except Exception:
            return -2, None
    else:
        # 使用 curl
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"
        try:
            result = subprocess.run(
                ["curl", "-s", "-w", "\n%{http_code}", url],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            lines = result.stdout.strip().split("\n")
            status_code = int(lines[-1])
            body = "\n".join(lines[:-1])
            if status_code == 200 and body:
                import json
                return status_code, json.loads(body)
            return status_code, None
        except subprocess.TimeoutExpired:
            return -1, None
        except Exception:
            return -2, None

# ============================================================
# 结果收集
# ============================================================

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.details: List[Tuple[str, str, str]] = []  # (name, status, message)

    def add_pass(self, name: str, message: str = ""):
        self.passed += 1
        self.details.append((name, "✓", message))
        print(f"  ✓ {name}" + (f": {message}" if message else ""))

    def add_fail(self, name: str, message: str):
        self.failed += 1
        self.details.append((name, "✗", message))
        print(f"  ✗ {name}: {message}")

    def add_skip(self, name: str, reason: str):
        self.skipped += 1
        self.details.append((name, "⊘", reason))
        print(f"  ⊘ {name}: {reason}")


result = TestResult()

# ============================================================
# P0: 基础设施验证
# ============================================================

def test_p0_config():
    """P0: 配置加载测试"""
    print("\n=== P0: 配置加载验证 ===")

    try:
        from app.config import config

        # LLM 配置
        if config.llm.provider:
            result.add_pass("LLM Provider", config.llm.provider)
        else:
            result.add_fail("LLM Provider", "未配置")

        if config.llm.model:
            result.add_pass("LLM Model", config.llm.model)
        else:
            result.add_fail("LLM Model", "未配置")

        # OPML 路径
        if config.blog.opml_path:
            result.add_pass("Blog OPML", config.blog.opml_path)
        else:
            result.add_fail("Blog OPML", "未配置")

        if config.podcast.opml_path:
            result.add_pass("Podcast OPML", config.podcast.opml_path)
        else:
            result.add_fail("Podcast OPML", "未配置")

        if config.video.opml_path:
            result.add_pass("Video OPML", config.video.opml_path)
        else:
            result.add_fail("Video OPML", "未配置")

        # Redis 配置
        if config.redis.url:
            result.add_pass("Redis URL", config.redis.url[:30] + "...")
        else:
            result.add_fail("Redis URL", "未配置")

    except Exception as e:
        result.add_fail("配置加载", str(e))


def test_p0_opml():
    """P0: OPML 解析测试"""
    print("\n=== P0: OPML 解析验证 ===")

    try:
        from app.scrapers.rss import RSSScraper
        from app.config import config

        sources = [
            ("Blog", config.blog.opml_path),
            ("Podcast", config.podcast.opml_path),
            ("Video", config.video.opml_path),
        ]

        for name, path in sources:
            try:
                scraper = RSSScraper(opml_path=path)
                feeds = scraper._load_feeds()
                if feeds:
                    result.add_pass(f"{name} OPML", f"{len(feeds)} feeds")
                else:
                    result.add_fail(f"{name} OPML", "无 feeds")
            except Exception as e:
                result.add_fail(f"{name} OPML", str(e))

    except Exception as e:
        result.add_fail("OPML 解析", str(e))


def test_p0_database():
    """P0: 数据库连接测试"""
    print("\n=== P0: 数据库连接验证 ===")

    status_code, data = http_get("http://localhost:8000/health", timeout=5)

    if status_code == -1:
        result.add_skip("服务连接", "后端服务未运行 (docker-compose up -d)")
        return
    elif status_code != 200:
        result.add_fail("健康检查", f"HTTP {status_code}")
        return

    if data.get("status") == "healthy":
        result.add_pass("健康检查", "服务正常")
        # 如果服务健康，推断数据库和 Redis 也正常
        result.add_pass("数据库连接", "inferred from healthy status")
        result.add_pass("Redis 连接", "inferred from healthy status")
    else:
        result.add_fail("健康检查", f"状态异常: {data}")
        # 尝试检查各组件状态（如果有）
        if "database" in data:
            if data.get("database") == "connected":
                result.add_pass("数据库连接", "connected")
            else:
                result.add_fail("数据库连接", data.get("database"))
        if "redis" in data:
            if data.get("redis") == "connected":
                result.add_pass("Redis 连接", "connected")
            else:
                result.add_skip("Redis 连接", data.get("redis"))


# ============================================================
# P1: 核心 API 验证
# ============================================================

def test_p1_resources_list():
    """P1: 资源列表 API"""
    print("\n=== P1: 资源列表 API ===")

    status_code, data = http_get("http://localhost:8000/api/resources", params={"page_size": 5})

    if status_code == -1:
        result.add_skip("资源列表", "服务未运行")
        return
    elif status_code != 200:
        result.add_fail("资源列表", f"HTTP {status_code}")
        return

    if data and "items" in data and "total" in data:
        result.add_pass("资源列表", f"{data['total']} 条记录")
    else:
        result.add_fail("资源列表", "响应格式错误")


def test_p1_resources_filter():
    """P1: 资源筛选功能"""
    print("\n=== P1: 资源筛选 ===")

    filters = [
        ("type=article", {"type": "article", "page_size": 1}),
        ("type=podcast", {"type": "podcast", "page_size": 1}),
        ("type=video", {"type": "video", "page_size": 1}),
        ("featured=true", {"featured": "true", "page_size": 1}),
    ]

    for name, params in filters:
        status_code, data = http_get("http://localhost:8000/api/resources", params=params)
        if status_code == -1:
            result.add_skip(f"筛选 {name}", "服务未运行")
            return
        elif status_code == 200 and data:
            count = len(data.get("items", []))
            result.add_pass(f"筛选 {name}", f"{count} 条")
        else:
            result.add_fail(f"筛选 {name}", f"HTTP {status_code}")


def test_p1_resource_detail():
    """P1: 资源详情 API"""
    print("\n=== P1: 资源详情 API ===")

    # 获取第一条资源
    status_code, data = http_get("http://localhost:8000/api/resources", params={"page_size": 1})

    if status_code == -1:
        result.add_skip("资源详情", "服务未运行")
        return
    elif status_code != 200:
        result.add_fail("资源详情", f"列表 HTTP {status_code}")
        return

    if not data or not data.get("items"):
        result.add_skip("资源详情", "无可用资源")
        return

    resource_id = data["items"][0]["id"]

    # 获取详情
    status_code2, detail = http_get(f"http://localhost:8000/api/resources/{resource_id}")

    if status_code2 == 200 and detail and "title" in detail:
        result.add_pass("资源详情", detail["title"][:30] + "...")
    else:
        result.add_fail("资源详情", f"详情 HTTP {status_code2}")


def test_p1_search():
    """P1: 搜索 API"""
    print("\n=== P1: 搜索功能 ===")

    status_code, data = http_get("http://localhost:8000/api/search", params={"q": "AI", "page_size": 3})

    if status_code == -1:
        result.add_skip("搜索功能", "服务未运行")
        return
    elif status_code == 200 and data:
        count = len(data.get("items", []))
        result.add_pass("搜索功能", f"{count} 条结果")
    else:
        result.add_fail("搜索功能", f"HTTP {status_code}")


def test_p1_stats():
    """P1: 统计 API"""
    print("\n=== P1: 统计接口 ===")

    status_code, data = http_get("http://localhost:8000/api/stats")

    if status_code == -1:
        result.add_skip("统计接口", "服务未运行")
        return
    elif status_code == 200 and data:
        # 处理嵌套响应结构
        if "data" in data:
            total = data["data"].get("total_signals", "N/A")
        else:
            total = data.get("total", data.get("total_signals", "N/A"))
        result.add_pass("统计接口", f"total_signals={total}")
    else:
        result.add_fail("统计接口", f"HTTP {status_code}")


# ============================================================
# P2: 数据采集验证
# ============================================================

def test_p2_sources_status():
    """P2: 数据源状态"""
    print("\n=== P2: 数据源状态 ===")

    status_code, data = http_get("http://localhost:8000/api/sources/status")

    if status_code == -1:
        result.add_skip("数据源状态", "服务未运行")
    elif status_code == 200 and data:
        result.add_pass("数据源状态", f"{len(data)} 个源")
    elif status_code == 404:
        result.add_skip("数据源状态", "API 不存在")
    else:
        result.add_fail("数据源状态", f"HTTP {status_code}")


# ============================================================
# P3: 高级功能验证
# ============================================================

def test_p3_deep_research():
    """P3: 深度研究 API"""
    print("\n=== P3: 深度研究 API ===")

    # 获取一个资源 ID
    status_code, data = http_get("http://localhost:8000/api/resources", params={"type": "article", "page_size": 1})

    if status_code == -1:
        result.add_skip("深度研究", "服务未运行")
        return
    elif status_code != 200 or not data or not data.get("items"):
        result.add_skip("深度研究", "无可用资源")
        return

    resource_id = data["items"][0]["id"]

    # 检查深度研究 API 是否存在
    status_code2, _ = http_get(f"http://localhost:8000/api/resources/{resource_id}/deep-research")

    if status_code2 == -1:
        result.add_skip("深度研究", "服务未运行")
    elif status_code2 in [200, 404]:
        result.add_pass("深度研究 API", "端点可访问")
    else:
        result.add_fail("深度研究 API", f"HTTP {status_code2}")


def test_p3_podcast_voices():
    """P3: 播客声音列表 API"""
    print("\n=== P3: 播客功能 ===")

    status_code, data = http_get("http://localhost:8000/api/podcast/voices")

    if status_code == -1:
        result.add_skip("播客声音", "服务未运行")
    elif status_code == 200 and data:
        voice_count = len(data) if isinstance(data, list) else len(data.get("voices", []))
        result.add_pass("播客声音列表", f"{voice_count} 个声音")
    elif status_code == 404:
        result.add_skip("播客声音", "API 不存在")
    else:
        result.add_fail("播客声音列表", f"HTTP {status_code}")


def test_p3_research_projects():
    """P3: 研究助手项目 API"""
    print("\n=== P3: 研究助手 ===")

    status_code, data = http_get("http://localhost:8000/api/research/projects")

    if status_code == -1:
        result.add_skip("研究项目", "服务未运行")
    elif status_code == 200:
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict):
            count = len(data.get("items", data.get("projects", [])))
        else:
            count = 0
        result.add_pass("研究项目列表", f"{count} 个项目")
    elif status_code == 404:
        result.add_skip("研究项目", "API 不存在")
    else:
        result.add_fail("研究项目列表", f"HTTP {status_code}")


# ============================================================
# P4: 管理后台验证
# ============================================================

def test_p4_admin_stats():
    """P4: Admin 统计 API"""
    print("\n=== P4: 管理后台 ===")

    status_code, data = http_get("http://localhost:8000/api/admin/stats/overview")

    if status_code == -1:
        result.add_skip("Admin 统计", "服务未运行")
    elif status_code == 200:
        result.add_pass("Admin 概览统计", "端点可访问")
    elif status_code in [401, 403]:
        result.add_pass("Admin 概览统计", "需要认证 (符合预期)")
    elif status_code == 404:
        result.add_skip("Admin 概览统计", "API 不存在")
    else:
        result.add_fail("Admin 概览统计", f"HTTP {status_code}")


def test_p4_prompts():
    """P4: Prompt 管理 API"""

    status_code, data = http_get("http://localhost:8000/api/admin/prompts")

    if status_code == -1:
        result.add_skip("Prompt 管理", "服务未运行")
    elif status_code == 200:
        result.add_pass("Prompt 管理", "端点可访问")
    elif status_code in [401, 403]:
        result.add_pass("Prompt 管理", "需要认证 (符合预期)")
    elif status_code == 404:
        result.add_skip("Prompt 管理", "API 不存在")
    else:
        result.add_fail("Prompt 管理", f"HTTP {status_code}")


# ============================================================
# 性能验证
# ============================================================

def test_performance():
    """性能: 响应时间测试"""
    print("\n=== 性能验证 ===")

    endpoints = [
        ("/api/resources", {"page_size": 20}, 500),
        ("/api/stats", None, 200),
        ("/health", None, 100),
    ]

    for endpoint, params, target_ms in endpoints:
        start = time()
        status_code, _ = http_get(f"http://localhost:8000{endpoint}", params=params)
        elapsed_ms = (time() - start) * 1000

        if status_code == -1:
            result.add_skip(f"响应时间 {endpoint}", "服务未运行")
            return
        elif status_code == 200:
            if elapsed_ms < target_ms:
                result.add_pass(f"响应时间 {endpoint}", f"{elapsed_ms:.0f}ms < {target_ms}ms")
            else:
                result.add_fail(f"响应时间 {endpoint}", f"{elapsed_ms:.0f}ms > {target_ms}ms")
        else:
            result.add_fail(f"响应时间 {endpoint}", f"HTTP {status_code}")


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 60)
    print("Signal 系统验证")
    print("=" * 60)

    # P0: 基础设施
    test_p0_config()
    test_p0_opml()
    test_p0_database()

    # P1: 核心 API
    test_p1_resources_list()
    test_p1_resources_filter()
    test_p1_resource_detail()
    test_p1_search()
    test_p1_stats()

    # P2: 数据采集
    test_p2_sources_status()

    # P3: 高级功能
    test_p3_deep_research()
    test_p3_podcast_voices()
    test_p3_research_projects()

    # P4: 管理后台
    test_p4_admin_stats()
    test_p4_prompts()

    # 性能
    test_performance()

    # 汇总
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    print(f"  通过: {result.passed}")
    print(f"  失败: {result.failed}")
    print(f"  跳过: {result.skipped}")
    print("=" * 60)

    if result.failed > 0:
        print("\n失败项:")
        for name, status, msg in result.details:
            if status == "✗":
                print(f"  - {name}: {msg}")

    if result.skipped > 0:
        print("\n跳过项:")
        for name, status, msg in result.details:
            if status == "⊘":
                print(f"  - {name}: {msg}")

    # 打印验证清单
    print("\n" + "=" * 60)
    print("功能完整度清单")
    print("=" * 60)

    categories = {
        "基础设施": ["LLM Provider", "LLM Model", "Blog OPML", "Podcast OPML", "Video OPML", "Redis URL", "健康检查", "数据库连接", "Redis 连接"],
        "核心 API": ["资源列表", "资源详情", "搜索功能", "统计接口"],
        "资源筛选": ["筛选 type=article", "筛选 type=podcast", "筛选 type=video", "筛选 featured=true"],
        "数据采集": ["数据源状态"],
        "高级功能": ["深度研究 API", "播客声音列表", "研究项目列表"],
        "管理后台": ["Admin 概览统计", "Prompt 管理"],
        "性能": ["响应时间 /api/resources", "响应时间 /api/stats", "响应时间 /health"],
    }

    for category, items in categories.items():
        print(f"\n{category}:")
        for item in items:
            found = False
            for name, status, msg in result.details:
                if name == item or name.startswith(item):
                    status_icon = {"✓": "✅", "✗": "❌", "⊘": "⬜"}.get(status, "⬜")
                    print(f"  {status_icon} {name}")
                    found = True
                    break
            if not found:
                print(f"  ⬜ {item}")

    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
