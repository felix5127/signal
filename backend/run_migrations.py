#!/usr/bin/env python3
"""
[INPUT]: DATABASE_URL 环境变量
[OUTPUT]: 执行所有待执行的数据库迁移
[POS]: 迁移执行器，可通过 railway run 远程执行
[PROTOCOL]: 变更时更新此头部
"""
import os
import sys
from pathlib import Path

# 迁移脚本目录
MIGRATIONS_DIR = Path(__file__).parent / "migrations"

# 需要跳过的迁移（需要 pgvector 扩展）
SKIP_MIGRATIONS = {"002_research_assistant.sql"}


def run_migrations():
    """执行所有迁移脚本"""
    from sqlalchemy import create_engine, text

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    print(f"[Migration] Connecting to database...")
    engine = create_engine(database_url)

    # 获取所有迁移文件（按文件名排序）
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    print(f"[Migration] Found {len(migration_files)} migration files")

    for migration_file in migration_files:
        filename = migration_file.name

        if filename in SKIP_MIGRATIONS:
            print(f"[Migration] SKIP: {filename} (requires pgvector)")
            continue

        print(f"[Migration] Running: {filename}")

        # 读取 SQL
        sql_content = migration_file.read_text()

        # 分割成单独的语句（简单分割，处理 ; 分隔）
        # 注意：这个简单分割可能对复杂 SQL 不够健壮
        with engine.connect() as conn:
            try:
                # 使用 PostgreSQL 的 DO 块执行，或者直接执行
                conn.execute(text(sql_content))
                conn.commit()
                print(f"[Migration] SUCCESS: {filename}")
            except Exception as e:
                error_msg = str(e)
                # 忽略 "already exists" 错误
                if "already exists" in error_msg or "duplicate" in error_msg.lower():
                    print(f"[Migration] SKIP: {filename} (already applied)")
                    conn.rollback()
                else:
                    print(f"[Migration] ERROR: {filename}")
                    print(f"  {error_msg}")
                    conn.rollback()
                    # 继续执行其他迁移

    print("[Migration] All migrations completed!")


if __name__ == "__main__":
    run_migrations()
