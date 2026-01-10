#!/usr/bin/env python3
"""
Railway 部署诊断脚本
用于检查服务是否能正常启动
"""
import os
import sys

def check_env_vars():
    """检查必需的环境变量"""
    print("=" * 60)
    print("检查环境变量...")
    print("=" * 60)

    required = {
        "OPENAI_API_KEY": "OpenAI/OpenRouter API Key",
        "DATABASE_URL": "数据库连接字符串",
    }

    optional = {
        "LLM_PROVIDER": "LLM 提供商 (openai/openrouter/kimi)",
        "LLM_MODEL": "LLM 模型名称",
        "LLM_BASE_URL": "LLM API 端点",
        "TAVILY_API_KEY": "Tavily 搜索 API Key",
        "GITHUB_TOKEN": "GitHub Token",
        "LOG_LEVEL": "日志级别",
    }

    issues = []

    # 检查必需变量
    for key, desc in required.items():
        value = os.getenv(key, "")
        if not value:
            print(f"❌ {key}: 未设置 ({desc})")
            issues.append(f"{key} 未设置")
        else:
            # 检查是否有前导/尾随空格
            if value != value.strip():
                print(f"⚠️  {key}: 有多余空格! [原值长度: {len(value)}, 去空格后: {len(value.strip())}]")
                issues.append(f"{key} 有多余空格")
            else:
                # 只显示前10个字符
                masked = value[:10] + "..." if len(value) > 10 else value
                print(f"✅ {key}: {masked}")

    print()

    # 检查可选变量
    for key, desc in optional.items():
        value = os.getenv(key, "")
        if not value:
            print(f"⚪ {key}: 未设置 ({desc}) - 可选")
        else:
            if value != value.strip():
                print(f"⚠️  {key}: 有多余空格! [原值: '{value}']")
                issues.append(f"{key} 有多余空格")
            else:
                print(f"✅ {key}: {value}")

    print()
    return issues


def check_imports():
    """检查关键依赖是否可导入"""
    print("=" * 60)
    print("检查 Python 依赖...")
    print("=" * 60)

    modules = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "httpx",
        "openai",
        "yaml",
    ]

    issues = []
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            issues.append(f"{module} 无法导入")

    print()
    return issues


def check_config():
    """检查配置加载"""
    print("=" * 60)
    print("检查配置加载...")
    print("=" * 60)

    issues = []
    try:
        from app.config import config

        print(f"✅ 配置加载成功")
        print(f"   LLM Provider: {config.llm.provider}")
        print(f"   LLM Model: {config.llm.model}")
        print(f"   LLM Base URL: {config.llm.base_url}")
        print(f"   Database URL: {config.database_url}")
        print(f"   API Key (前10字符): {config.openai_api_key[:10]}...")

        # 检查 API Key 是否有空格
        if config.openai_api_key != config.openai_api_key.strip():
            print(f"⚠️  API Key 有多余空格!")
            issues.append("API Key 有多余空格")

    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        issues.append(f"配置加载失败: {e}")

    print()
    return issues


def check_database():
    """检查数据库连接"""
    print("=" * 60)
    print("检查数据库连接...")
    print("=" * 60)

    issues = []
    try:
        from app.database import SessionLocal, init_db

        # 初始化数据库
        init_db()
        print("✅ 数据库初始化成功")

        # 测试连接
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ 数据库连接测试成功")

    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        import traceback
        traceback.print_exc()
        issues.append(f"数据库检查失败: {e}")

    print()
    return issues


def main():
    """主函数"""
    print("\n🔍 Railway 部署诊断工具\n")

    all_issues = []

    # 1. 检查环境变量
    issues = check_env_vars()
    all_issues.extend(issues)

    # 2. 检查依赖
    issues = check_imports()
    all_issues.extend(issues)

    # 3. 检查配置
    issues = check_config()
    all_issues.extend(issues)

    # 4. 检查数据库
    issues = check_database()
    all_issues.extend(issues)

    # 总结
    print("=" * 60)
    print("诊断结果")
    print("=" * 60)

    if not all_issues:
        print("✅ 所有检查通过! 服务应该可以正常启动。")
        print("\n下一步: 启动服务")
        print("  uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return 0
    else:
        print(f"❌ 发现 {len(all_issues)} 个问题:\n")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        print("\n请修复这些问题后再启动服务。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
