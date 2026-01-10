# Input: Session, 模型类列表
# Output: 批量数据库操作工具
# Position: 数据库批量操作层，优化插入和更新性能
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

from typing import List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class BatchDBOperator:
    """
    批量数据库操作工具

    优化点：
    - 批量插入（而非逐条插入）
    - 使用批量提交减少 I/O
    - 自动处理重复和错误
    """

    def __init__(self, batch_size: int = 50):
        """
        Args:
            batch_size: 批量操作大小（默认 50）
        """
        self.batch_size = batch_size

    async def bulk_insert(
        self,
        db: Session,
        items: List[Any],
        skip_duplicates: bool = True,
        skip_fields: Optional[List[str]] = None,
    ) -> dict:
        """
        批量插入数据

        Args:
            db: 数据库会话
            items: 待插入的模型实例列表
            skip_duplicates: 是否跳过重复项（基于唯一键）
            skip_fields: 检查重复时跳过的字段列表

        Returns:
            统计信息 {"inserted": int, "skipped": int, "failed": int}
        """
        stats = {"inserted": 0, "skipped": 0, "failed": 0}

        if not items:
            return stats

        # 分批处理
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i+self.batch_size]

            for item in batch:
                try:
                    # 检查重复（如果需要）
                    if skip_duplicates:
                        # 尝试检查 URL 唯一键（如果存在）
                        if hasattr(item, 'url'):
                            existing = db.query(item.__class__).filter(
                                item.__class__.url == item.url
                            ).first()
                            if existing:
                                stats["skipped"] += 1
                                continue
                        elif hasattr(item, 'url_hash'):
                            existing = db.query(item.__class__).filter(
                                item.__class__.url_hash == item.url_hash
                            ).first()
                            if existing:
                                stats["skipped"] += 1
                                continue

                    # 插入
                    db.add(item)
                    stats["inserted"] += 1

                except Exception as e:
                    logger.error(f"[BatchDB] Insert error: {e}")
                    stats["failed"] += 1

            # 批量提交
            try:
                db.commit()
                logger.debug(f"[BatchDB] Batch committed: {i+1}-{min(i+self.batch_size, len(items))}/{len(items)}")
            except Exception as e:
                db.rollback()
                logger.error(f"[BatchDB] Batch commit error: {e}")
                raise

        logger.info(f"[BatchDB] Bulk insert completed: {stats}")
        return stats

    async def bulk_insert_resources(
        self,
        db: Session,
        resources: List[Any],
    ) -> dict:
        """
        批量插入 Resource（专门优化）

        Args:
            db: 数据库会话
            resources: Resource 实例列表

        Returns:
            统计信息
        """
        stats = {"inserted": 0, "skipped": 0, "failed": 0}

        if not resources:
            return stats

        # 批量查询已存在的 URL hash
        url_hashes = [r.url_hash for r in resources]
        if url_hashes:
            # 使用 IN 查询优化
            from app.models.resource import Resource
            existing = db.query(Resource.url_hash).filter(
                Resource.url_hash.in_(url_hashes)
            ).all()
            existing_hashes = set(e[0] for e in existing)

            # 过滤掉已存在的
            new_resources = [r for r in resources if r.url_hash not in existing_hashes]
            stats["skipped"] = len(resources) - len(new_resources)
        else:
            new_resources = resources

        # 批量插入
        for i in range(0, len(new_resources), self.batch_size):
            batch = new_resources[i:i+self.batch_size]

            try:
                db.add_all(batch)
                db.commit()
                stats["inserted"] += len(batch)
                logger.debug(f"[BatchDB] Inserted resources: {i+1}-{min(i+self.batch_size, len(new_resources))}/{len(new_resources)}")
            except Exception as e:
                db.rollback()
                logger.error(f"[BatchDB] Resources batch error: {e}")
                stats["failed"] += len(batch)

        logger.info(f"[BatchDB] Bulk insert resources: {stats}")
        return stats

    async def bulk_update(
        self,
        db: Session,
        model_class: Any,
        items: List[dict],
        key_field: str = "id",
    ) -> dict:
        """
        批量更新数据

        Args:
            db: 数据库会话
            model_class: 模型类
            items: 待更新数据字典列表 [{"id": 1, "field": value}, ...]
            key_field: 主键字段名

        Returns:
            统计信息
        """
        stats = {"updated": 0, "failed": 0}

        if not items:
            return stats

        for i in range(0, len(items), self.batch_size):
            batch = items[i:i+self.batch_size]

            for item_data in batch:
                try:
                    # 查找记录
                    key_value = item_data.get(key_field)
                    if not key_value:
                        stats["failed"] += 1
                        continue

                    instance = db.query(model_class).filter(
                        getattr(model_class, key_field) == key_value
                    ).first()

                    if instance:
                        # 更新字段
                        for field, value in item_data.items():
                            if field != key_field and hasattr(instance, field):
                                setattr(instance, field, value)

                        stats["updated"] += 1
                    else:
                        stats["failed"] += 1

                except Exception as e:
                    logger.error(f"[BatchDB] Update error: {e}")
                    stats["failed"] += 1

            # 批量提交
            try:
                db.commit()
                logger.debug(f"[BatchDB] Batch update committed: {i+1}-{min(i+self.batch_size, len(items))}/{len(items)}")
            except Exception as e:
                db.rollback()
                logger.error(f"[BatchDB] Batch update commit error: {e}")
                raise

        logger.info(f"[BatchDB] Bulk update completed: {stats}")
        return stats

    async def bulk_upsert(
        self,
        db: Session,
        model_class: Any,
        items: List[dict],
        index_elements: List[str],
        update_fields: List[str],
    ) -> dict:
        """
        批量插入或更新（Upsert）

        注意：需要 PostgreSQL 支持 ON CONFLICT

        Args:
            db: 数据库会话
            model_class: 模型类
            items: 数据列表
            index_elements: 唯一索引字段列表
            update_fields: 冲突时更新的字段列表

        Returns:
            统计信息
        """
        stats = {"inserted": 0, "updated": 0, "failed": 0}

        try:
            # 构建 insert 语句
            stmt = insert(model_class.__table__)

            # 分批执行
            for i in range(0, len(items), self.batch_size):
                batch = items[i:i+self.batch_size]

                try:
                    # 执行 upsert
                    stmt = stmt.values(batch)
                    update_dict = {f: getattr(stmt.inserted, f) for f in update_fields}
                    stmt = stmt.on_conflict_do_update(
                        index_elements=index_elements,
                        set_=update_dict,
                    )

                    db.execute(stmt)
                    db.commit()

                    # 统计（简化版，假设都成功）
                    stats["inserted"] += len(batch)

                except Exception as e:
                    db.rollback()
                    logger.error(f"[BatchDB] Upsert batch error: {e}")
                    stats["failed"] += len(batch)

        except Exception as e:
            logger.error(f"[BatchDB] Upsert error (may not be supported): {e}")
            # 降级到普通批量插入
            stats = await self.bulk_insert(
                db,
                [model_class(**item) for item in items],
                skip_duplicates=True,
            )

        logger.info(f"[BatchDB] Bulk upsert completed: {stats}")
        return stats


# 全局实例
batch_db = BatchDBOperator(batch_size=50)
