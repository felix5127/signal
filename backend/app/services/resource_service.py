# Input: 数据库 Session, 筛选参数
# Output: 资源列表、详情、搜索结果
# Position: Resource Service 层，封装资源相关业务逻辑
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

"""
Resource 业务逻辑层

封装资源相关的所有业务操作：
- 查询与筛选
- 搜索
- 统计
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.resource import Resource
from app.utils.cache import cache_result, make_resources_list_key, make_resources_stats_key


class ResourceService:
    """资源服务类"""

    def __init__(self, db: Session):
        self.db = db

    def get_resources(
        self,
        type: Optional[str] = None,
        domain: Optional[str] = None,
        lang: Optional[str] = None,
        time_filter: Optional[str] = None,
        min_score: Optional[float] = None,
        featured: Optional[bool] = None,
        sort: str = "default",
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取资源列表（封装筛选逻辑）"""
        query = self.db.query(Resource).filter(Resource.status == "published")

        # 应用筛选
        if type:
            query = query.filter(Resource.type == type)
        if domain:
            query = query.filter(Resource.domain == domain)
        if lang:
            query = query.filter(Resource.language == lang)
        if featured is not None:
            query = query.filter(Resource.is_featured == featured)
        if min_score is not None:
            query = query.filter(Resource.score >= min_score * 10)

        # 时间筛选
        if time_filter:
            from datetime import datetime, timedelta
            time_map = {
                "1d": timedelta(days=1),
                "1w": timedelta(weeks=1),
                "1m": timedelta(days=30),
                "3m": timedelta(days=90),
                "1y": timedelta(days=365),
            }
            if time_filter in time_map:
                start_time = datetime.now() - time_map[time_filter]
                query = query.filter(Resource.published_at >= start_time)

        total = query.count()

        # 排序
        if sort == "time":
            query = query.order_by(Resource.published_at.desc())
        elif sort == "score":
            query = query.order_by(Resource.score.desc())
        else:
            query = query.order_by(
                Resource.is_featured.desc(),
                Resource.score.desc(),
                Resource.published_at.desc(),
            )

        # 分页
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
        }

    def search_resources(
        self,
        keyword: str,
        type: Optional[str] = None,
        domain: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """全文搜索"""
        query = self.db.query(Resource).filter(Resource.status == "published")

        # 搜索条件
        search_conditions = [
            Resource.title.ilike(f"%{keyword}%"),
            Resource.title_translated.ilike(f"%{keyword}%"),
            Resource.one_sentence_summary.ilike(f"%{keyword}%"),
            Resource.summary.ilike(f"%{keyword}%"),
        ]
        query = query.filter(or_(*search_conditions))

        # 其他筛选
        if type:
            query = query.filter(Resource.type == type)
        if domain:
            query = query.filter(Resource.domain == domain)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
        }
