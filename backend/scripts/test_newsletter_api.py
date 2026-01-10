#!/usr/bin/env python3
"""
周刊 API 测试脚本

用法：
1. 启动后端：python backend/app/main.py
2. 运行测试：python backend/scripts/test_newsletter_api.py
"""

import requests
import json
from datetime import datetime

# API 基础地址
API_BASE = "http://localhost:8000"


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_list_newsletters():
    """测试获取周刊列表"""
    print_section("测试 1: 获取周刊列表")

    response = requests.get(f"{API_BASE}/api/newsletters?page_size=10")

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功获取周刊列表")
        print(f"   总数: {data['total']}")
        print(f"   当前页: {data['page']}")
        print(f"   每页数量: {data['page_size']}")
        print(f"   返回数量: {len(data['items'])}")

        if data['items']:
            print("\n   最新周刊:")
            for item in data['items'][:3]:
                print(f"   - {item['title']}")
                print(f"     📅 {item['published_at']}")
                print(f"     📊 {item['resource_count']}篇收录, ⭐{item['featured_count']}篇精选")
                print(f"     预览: {item['preview'][:50]}...")
        else:
            print("   ⚠️  暂无周刊，请先生成")
    else:
        print(f"❌ 失败: {response.text}")


def test_get_newsletter_detail():
    """测试获取周刊详情"""
    print_section("测试 2: 获取周刊详情")

    # 先获取列表，找到第一个周刊 ID
    list_response = requests.get(f"{API_BASE}/api/newsletters?page_size=1")

    if list_response.status_code != 200 or not list_response.json()['items']:
        print("⚠️  没有可用的周刊，跳过详情测试")
        return

    first_newsletter_id = list_response.json()['items'][0]['id']
    print(f"获取周刊 ID: {first_newsletter_id}")

    response = requests.get(f"{API_BASE}/api/newsletters/{first_newsletter_id}")

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功获取周刊详情")
        print(f"   标题: {data['title']}")
        print(f"   年份: {data['year']}")
        print(f"   周数: {data['week_number']}")
        print(f"   资源数: {data['resource_count']}")
        print(f"   精选数: {data['featured_count']}")
        print(f"   内容长度: {len(data['content'])} 字符")
        print(f"   关联资源: {len(data['resource_ids'])} 个")
        print(f"\n   内容预览:")
        print(f"   {data['content'][:200]}...")
    else:
        print(f"❌ 失败: {response.text}")


def test_create_newsletter():
    """测试手动生成周刊"""
    print_section("测试 3: 手动生成周刊")

    from datetime import datetime
    now = datetime.now()
    iso_calendar = now.isocalendar()
    current_year = iso_calendar[0]
    current_week = iso_calendar[1]

    print(f"当前: {current_year} 年第 {current_week} 周")

    # 尝试生成本周周刊（不强制）
    response = requests.post(
        f"{API_BASE}/api/newsletters",
        params={
            "year": current_year,
            "week_number": current_week,
            "force": False
        }
    )

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功生成周刊")
        print(f"   标题: {data['title']}")
        print(f"   年份: {data['year']}")
        print(f"   周数: {data['week_number']}")
        print(f"   资源数: {data['resource_count']}")
        print(f"   精选数: {data['featured_count']}")
    elif response.status_code == 400:
        print(f"⚠️  周刊已存在")
        print(f"   提示: 使用 force=true 强制重新生成")
    else:
        print(f"❌ 失败: {response.text}")


def test_force_regenerate():
    """测试强制重新生成"""
    print_section("测试 4: 强制重新生成周刊")

    from datetime import datetime
    now = datetime.now()
    iso_calendar = now.isocalendar()
    current_year = iso_calendar[0]
    current_week = iso_calendar[1]

    response = requests.post(
        f"{API_BASE}/api/newsletters",
        params={
            "year": current_year,
            "week_number": current_week,
            "force": True
        }
    )

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功强制重新生成周刊")
        print(f"   标题: {data['title']}")
        print(f"   资源数: {data['resource_count']}")
    else:
        print(f"❌ 失败: {response.text}")


def test_404_error():
    """测试 404 错误"""
    print_section("测试 5: 404 错误处理")

    response = requests.get(f"{API_BASE}/api/newsletters/99999")

    if response.status_code == 404:
        print("✅ 正确返回 404")
    else:
        print(f"❌ 错误: 期望 404，实际 {response.status_code}")


def main():
    """运行所有测试"""
    print("\n🚀 开始测试周刊 API\n")

    try:
        # 测试 1: 获取列表
        test_list_newsletters()

        # 测试 2: 获取详情（如果有周刊）
        test_get_newsletter_detail()

        # 测试 3: 手动生成（不强制）
        test_create_newsletter()

        # 询问是否强制重新生成
        print("\n" + "=" * 60)
        force = input("是否强制重新生成周刊？(y/N): ").strip().lower()
        if force == 'y':
            test_force_regenerate()
        else:
            print("跳过强制重新生成")

        # 测试 4: 错误处理
        test_404_error()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60 + "\n")

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 API，请确保后端已启动")
        print("   启动命令: python backend/app/main.py")


if __name__ == "__main__":
    main()
