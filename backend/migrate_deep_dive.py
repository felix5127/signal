#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加 Deep Research 字段

为 signals 表添加以下字段：
- deep_dive (TEXT): 深度研究报告
- deep_dive_generated_at (DATETIME): 生成时间
- deep_dive_tokens (INTEGER): Token 消耗
- deep_dive_cost (REAL): 成本
- deep_dive_strategy (VARCHAR(20)): 策略
- deep_dive_sources (TEXT): 引用来源（JSON）
- deep_dive_metadata (TEXT): 元数据（JSON）
"""

import sqlite3
import sys
from pathlib import Path

# 数据库路径
DB_PATH = Path(__file__).parent / "data" / "signals.db"


def migrate():
    """执行迁移"""

    print("=" * 60)
    print("Deep Research 数据库迁移")
    print("=" * 60)

    if not DB_PATH.exists():
        print(f"\n❌ 数据库不存在: {DB_PATH}")
        print("请先运行应用以创建数据库")
        return False

    print(f"\n📁 数据库路径: {DB_PATH}")

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 检查 signals 表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='signals'"
        )
        if not cursor.fetchone():
            print("\n❌ signals 表不存在")
            return False

        # 检查是否已经迁移过
        cursor.execute("PRAGMA table_info(signals)")
        columns = [col[1] for col in cursor.fetchall()]

        if "deep_dive" in columns:
            print("\n✅ 数据库已经包含 Deep Research 字段，无需迁移")
            return True

        print("\n🔧 开始添加字段...")

        # 添加新字段
        migrations = [
            "ALTER TABLE signals ADD COLUMN deep_dive TEXT",
            "ALTER TABLE signals ADD COLUMN deep_dive_generated_at DATETIME",
            "ALTER TABLE signals ADD COLUMN deep_dive_tokens INTEGER",
            "ALTER TABLE signals ADD COLUMN deep_dive_cost REAL",
            "ALTER TABLE signals ADD COLUMN deep_dive_strategy VARCHAR(20)",
            "ALTER TABLE signals ADD COLUMN deep_dive_sources TEXT",
            "ALTER TABLE signals ADD COLUMN deep_dive_metadata TEXT",
        ]

        for i, sql in enumerate(migrations, 1):
            print(f"  [{i}/{len(migrations)}] {sql}")
            cursor.execute(sql)

        conn.commit()

        print("\n✅ 迁移成功!")

        # 验证
        cursor.execute("PRAGMA table_info(signals)")
        new_columns = [col[1] for col in cursor.fetchall()]

        required_columns = [
            "deep_dive",
            "deep_dive_generated_at",
            "deep_dive_tokens",
            "deep_dive_cost",
            "deep_dive_strategy",
            "deep_dive_sources",
            "deep_dive_metadata",
        ]

        missing = set(required_columns) - set(new_columns)
        if missing:
            print(f"\n⚠️  警告: 缺少字段 {missing}")
            return False

        print(f"\n📊 当前表结构（共 {len(new_columns)} 个字段）:")
        for col in new_columns[-7:]:  # 显示最后7个字段
            print(f"  - {col}")

        return True

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
