#!/usr/bin/env python3
"""
数据库迁移脚本 - 重命名 deep_dive → deep_research

将 resources 和 signals 表中的 deep_dive_* 字段重命名为 deep_research_*
"""

import os
import sys


def migrate_postgresql():
    """PostgreSQL 迁移"""
    import psycopg2

    # 从环境变量获取数据库连接信息
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise RuntimeError("DATABASE_URL 环境变量未设置")

    conn = psycopg2.connect(db_url)

    cursor = conn.cursor()

    print("=" * 60)
    print("Deep Research 字段重命名迁移 (PostgreSQL)")
    print("=" * 60)

    # 需要重命名的字段映射
    renames = [
        ("deep_dive", "deep_research"),
        ("deep_dive_generated_at", "deep_research_generated_at"),
        ("deep_dive_tokens", "deep_research_tokens"),
        ("deep_dive_cost", "deep_research_cost"),
        ("deep_dive_strategy", "deep_research_strategy"),
        ("deep_dive_sources", "deep_research_sources"),
        ("deep_dive_metadata", "deep_research_metadata"),
    ]

    tables = ["resources", "signals"]

    try:
        for table in tables:
            print(f"\n📋 处理表: {table}")

            # 检查表是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                )
            """, (table,))

            if not cursor.fetchone()[0]:
                print(f"  ⏭️  表 {table} 不存在，跳过")
                continue

            # 获取当前列名
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
            """, (table,))
            columns = [row[0] for row in cursor.fetchall()]

            for old_name, new_name in renames:
                if old_name in columns and new_name not in columns:
                    print(f"  🔄 {old_name} → {new_name}")
                    cursor.execute(f"ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name}")
                elif new_name in columns:
                    print(f"  ✅ {new_name} 已存在")
                elif old_name not in columns:
                    print(f"  ➕ 添加新列 {new_name}")
                    # 根据字段类型添加
                    if new_name == "deep_research":
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {new_name} TEXT")
                    elif new_name == "deep_research_generated_at":
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {new_name} TIMESTAMP")
                    elif new_name in ("deep_research_tokens",):
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {new_name} INTEGER")
                    elif new_name == "deep_research_cost":
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {new_name} REAL")
                    elif new_name == "deep_research_strategy":
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {new_name} VARCHAR(20)")
                    else:
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {new_name} TEXT")

        conn.commit()
        print("\n✅ 迁移成功!")
        return True

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


def migrate_docker():
    """通过 Docker 执行迁移"""
    import subprocess

    print("=" * 60)
    print("Deep Research 字段重命名迁移 (via Docker)")
    print("=" * 60)

    renames = [
        ("deep_dive", "deep_research"),
        ("deep_dive_generated_at", "deep_research_generated_at"),
        ("deep_dive_tokens", "deep_research_tokens"),
        ("deep_dive_cost", "deep_research_cost"),
        ("deep_dive_strategy", "deep_research_strategy"),
        ("deep_dive_sources", "deep_research_sources"),
        ("deep_dive_metadata", "deep_research_metadata"),
    ]

    tables = ["resources", "signals"]

    for table in tables:
        print(f"\n📋 处理表: {table}")

        for old_name, new_name in renames:
            # 检查旧列是否存在
            check_cmd = f"""
                docker exec signal-db psql -U signal_user -d signal_db -t -c "
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = '{table}' AND column_name = '{old_name}'
                "
            """
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

            if old_name in result.stdout:
                # 旧列存在，执行重命名
                rename_cmd = f"""
                    docker exec signal-db psql -U signal_user -d signal_db -c "
                        ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name}
                    "
                """
                print(f"  🔄 {old_name} → {new_name}")
                subprocess.run(rename_cmd, shell=True)
            else:
                # 检查新列是否存在
                check_new_cmd = f"""
                    docker exec signal-db psql -U signal_user -d signal_db -t -c "
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name = '{table}' AND column_name = '{new_name}'
                    "
                """
                result_new = subprocess.run(check_new_cmd, shell=True, capture_output=True, text=True)

                if new_name in result_new.stdout:
                    print(f"  ✅ {new_name} 已存在")
                else:
                    print(f"  ⏭️  {old_name} 不存在，跳过")

    print("\n✅ 迁移完成!")
    return True


if __name__ == "__main__":
    # 优先使用 Docker 方式
    try:
        import subprocess
        result = subprocess.run(
            "docker ps --format '{{.Names}}' | grep signal-db",
            shell=True, capture_output=True, text=True
        )
        if "signal-db" in result.stdout:
            success = migrate_docker()
        else:
            success = migrate_postgresql()
    except Exception as e:
        print(f"Error: {e}")
        success = False

    sys.exit(0 if success else 1)
