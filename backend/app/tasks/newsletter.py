# Input: Resource 表（本周高分内容）, Newsletter 模型, LLM 客户端
# Output: Newsletter 记录（Markdown 格式周刊）
# Position: 周刊生成任务，每周五自动触发生成本周技术情报周刊
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, extract

from app.database import SessionLocal
from app.models.resource import Resource
from app.models.newsletter import Newsletter
from app.utils.llm import llm_client

# 配置日志
logger = logging.getLogger(__name__)


def get_week_range(date: Optional[datetime] = None) -> tuple[datetime, datetime]:
    """
    获取指定日期所在的自然周范围（周一到周日）

    Args:
        date: 参考日期，默认为当前时间

    Returns:
        (week_start, week_end) 元组，都是 datetime 对象
    """
    if date is None:
        date = datetime.now()

    # 获取本周一（weekday() == 0 代表周一）
    week_start = date - timedelta(days=date.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    # 获取本周日
    week_end = week_start + timedelta(days=6)
    week_end = week_end.replace(hour=23, minute=59, second=59, microsecond=999999)

    return week_start, week_end


def get_week_number(date: Optional[datetime] = None) -> tuple[int, int]:
    """
    获取指定日期的年份和周数

    Args:
        date: 参考日期，默认为当前时间

    Returns:
        (year, week_number) 元组
    """
    if date is None:
        date = datetime.now()

    # 使用 ISO 周数标准
    iso_calendar = date.isocalendar()
    year = iso_calendar[0]
    week_number = iso_calendar[1]

    return year, week_number


def fetch_weekly_top_resources(
    week_start: datetime,
    week_end: datetime,
    min_score: int = 70,
    max_per_domain: int = 10,
) -> Dict[str, List[Resource]]:
    """
    从数据库获取本周高分内容，按分类分组

    策略：
    - 筛选条件：published_at 在本周内，score >= min_score，status = 'published'
    - 每个分类最多取 max_per_domain 条，按 score 降序
    - 优先使用 is_featured = True 的内容

    Args:
        week_start: 周初时间（周一 00:00:00）
        week_end: 周末时间（周日 23:59:59）
        min_score: 最低评分阈值，默认 70
        max_per_domain: 每个分类最多取多少条，默认 10

    Returns:
        按分类分组的资源字典：{"人工智能": [Resource, ...], "软件编程": [...]}
    """
    db = SessionLocal()
    try:
        # 查询本周内的高分内容
        resources = (
            db.query(Resource)
            .filter(
                and_(
                    Resource.published_at >= week_start,
                    Resource.published_at <= week_end,
                    Resource.score >= min_score,
                    Resource.status == "published",
                )
            )
            .order_by(Resource.score.desc(), Resource.published_at.desc())
            .all()
        )

        # 按分类分组
        domain_groups: Dict[str, List[Resource]] = {
            "人工智能": [],
            "软件编程": [],
            "产品设计": [],
            "商业科技": [],
        }

        for resource in resources:
            domain = resource.domain or "其他"
            if domain in domain_groups:
                # 限制每个分类最多 max_per_domain 条
                if len(domain_groups[domain]) < max_per_domain:
                    domain_groups[domain].append(resource)

        # 统计信息
        total_count = sum(len(resources) for resources in domain_groups.values())
        logger.info(f"[Newsletter] 本周共找到 {total_count} 条高分内容")

        return domain_groups

    finally:
        db.close()


def fetch_featured_resources(
    week_start: datetime,
    week_end: datetime,
    limit: int = 20,
) -> List[Resource]:
    """
    获取本周精选内容（score >= 85 的内容）

    Args:
        week_start: 周初时间
        week_end: 周末时间
        limit: 最多返回多少条，默认 20

    Returns:
        精选资源列表（按 score 降序）
    """
    db = SessionLocal()
    try:
        featured = (
            db.query(Resource)
            .filter(
                and_(
                    Resource.published_at >= week_start,
                    Resource.published_at <= week_end,
                    Resource.is_featured == True,
                    Resource.status == "published",
                )
            )
            .order_by(Resource.score.desc(), Resource.published_at.desc())
            .limit(limit)
            .all()
        )

        logger.info(f"[Newsletter] 本周共找到 {len(featured)} 条精选内容")
        return featured

    finally:
        db.close()


def extract_key_quotes(
    resources: List[Resource],
    max_per_resource: int = 2,
    total_limit: int = 15,
) -> List[Dict[str, str]]:
    """
    从高分资源中提取金句

    优先使用 key_quotes_zh，如果没有则使用 key_quotes

    Args:
        resources: 资源列表
        max_per_resource: 每个资源最多取几条金句
        total_limit: 总共最多返回多少条金句

    Returns:
        金句列表：[{"quote": "...", "source": "...", "url": "..."}, ...]
    """
    quotes = []

    for resource in resources:
        # 优先使用中文金句
        resource_quotes = resource.key_quotes_zh or resource.key_quotes or []

        if resource_quotes and isinstance(resource_quotes, list):
            for i, quote in enumerate(resource_quotes[:max_per_resource]):
                if len(quotes) >= total_limit:
                    break

                quotes.append({
                    "quote": quote,
                    "source": resource.title_translated or resource.title,
                    "url": resource.url,
                })

        if len(quotes) >= total_limit:
            break

    return quotes


async def generate_weekly_overview(
    domain_groups: Dict[str, List[Resource]],
    featured: List[Resource],
) -> str:
    """
    使用 LLM 生成本周技术情报综述

    Args:
        domain_groups: 按分类分组的内容
        featured: 精选内容列表

    Returns:
        Markdown 格式的综述文本
    """
    # 统计信息
    total_count = sum(len(resources) for resources in domain_groups.values())
    domain_summary = {}
    for domain, resources in domain_groups.items():
        if resources:
            avg_score = sum(r.score for r in resources) / len(resources)
            top_score = resources[0].score
            domain_summary[domain] = {
                "count": len(resources),
                "avg_score": round(avg_score, 1),
                "top_score": top_score,
            }

    # 构建摘要信息
    summary_info = {
        "total_count": total_count,
        "featured_count": len(featured),
        "domain_summary": domain_summary,
    }

    # LLM Prompt
    system_prompt = """你是 Signal Hunter 的技术情报主编，负责撰写每周技术情报综述。

你的任务是：
1. 基于提供的统计数据，总结本周技术趋势
2. 突出重点领域（人工智能、软件编程、产品设计、商业科技）
3. 提炼关键洞察（2-3段）
4. 风格：专业、简洁、有洞察力（避免废话）

要求：
- 使用 Markdown 格式
- 每段 2-3 句话，总长度控制在 200-300 字
- 突出跨领域融合趋势（如 AI + 编程、AI + 产品设计）
- 避免泛泛而谈，要有具体观察"""

    user_prompt = f"""请基于以下数据生成本周技术情报综述：

**本周数据统计：**
- 总内容数：{summary_info['total_count']} 条
- 精选内容数：{summary_info['featured_count']} 条

**各领域数据：**
"""

    for domain, stats in domain_summary.items():
        user_prompt += f"- {domain}：{stats['count']} 条（平均分 {stats['avg_score']}，最高分 {stats['top_score']}）\n"

    user_prompt += """
**输出要求：**
1. 开篇：本周整体趋势（1段，50字）
2. 领域亮点：各领域关键进展（3-4段，每段50-60字）
3. 跨领域趋势：AI 融合观察（1段，60字）
4. 风格参考科技媒体（如 36氪、极客公园）

请直接输出 Markdown 文本，不要包含任何解释性文字。"""

    try:
        overview = await llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
        )

        return overview.strip()

    except Exception as e:
        logger.error(f"[Newsletter] LLM 生成综述失败: {e}")
        # Fallback：返回固定模板
        return f"""## 本周技术情报综述

本周共收录 {summary_info['total_count']} 条优质技术信号，精选 {summary_info['featured_count']} 条重磅内容。

人工智能领域持续领跑，大模型应用场景不断拓展；软件编程领域涌现出多个优秀开发工具；产品设计领域更注重 AI 原生体验；商业科技领域关注可持续发展与技术创新的平衡。

**本周核心趋势：** AI Agent 技术从概念验证走向落地应用，开发者工具生态快速进化。

*注：本周综述为自动生成，更多细节请查看各分类精选内容。*"""


async def generate_newsletter_content(
    domain_groups: Dict[str, List[Resource]],
    featured: List[Resource],
    year: int,
    week_number: int,
) -> str:
    """
    生成完整的周刊 Markdown 内容

    Args:
        domain_groups: 按分类分组的内容
        featured: 精选内容
        year: 年份
        week_number: 周数

    Returns:
        完整的 Markdown 周刊内容
    """
    # 1. 生成综述
    overview = await generate_weekly_overview(domain_groups, featured)

    # 2. 构建完整周刊
    content = f"""# Signal Hunter 周刊 {year}年第{week_number}周

> 📅 出版日期：{datetime.now().strftime('%Y-%m-%d')}
> 📊 本周收录：{sum(len(r) for r in domain_groups.values())} 条优质信号
> ⭐ 精选内容：{len(featured)} 条

---

{overview}

---

## 📌 本周 Top 资源（评分 ≥ 85）

"""

    # 3. Top 资源列表（评分 >= 85）
    for i, resource in enumerate(featured[:20], 1):
        title = resource.title_translated or resource.title
        summary = resource.one_sentence_summary_zh or resource.one_sentence_summary or resource.summary_zh or resource.summary
        score_badge = "⭐" if resource.is_featured else ""

        content += f"""### {i}. {title} {score_badge}

**评分：** {resource.score}/100
**分类：** {resource.domain or '未分类'}
**来源：** {resource.source_name}
**阅读时间：** {resource.read_time} 分钟

{summary}

👉 [阅读全文]({resource.url})

---

"""

    # 4. 各分类精选内容
    domain_order = ["人工智能", "软件编程", "产品设计", "商业科技"]
    domain_emoji = {
        "人工智能": "🤖",
        "软件编程": "💻",
        "产品设计": "🎨",
        "商业科技": "💼",
    }

    for domain in domain_order:
        resources = domain_groups.get(domain, [])
        if not resources:
            continue

        content += f"""## {domain_emoji.get(domain, '')} {domain}精选

"""

        for i, resource in enumerate(resources[:10], 1):
            title = resource.title_translated or resource.title
            summary = resource.one_sentence_summary_zh or resource.one_sentence_summary

            content += f"""### {i}. {title}

**评分：** {resource.score}/100
**来源：** {resource.source_name}
**标签：** {', '.join(resource.tags[:5]) if resource.tags else '无'}

{summary}

👉 [阅读全文]({resource.url})

---

"""

    # 5. 金句摘录
    all_resources = []
    for resources in domain_groups.values():
        all_resources.extend(resources)

    quotes = extract_key_quotes(all_resources, max_per_resource=2, total_limit=15)

    if quotes:
        content += """## 💡 本周金句

"""
        for quote in quotes[:10]:
            content += f"""> {quote['quote']}
>
> —— [{quote['source']}]({quote['url']})

---

"""

    # 6. 周刊结尾
    content += f"""---

## 📬 订阅与反馈

- 🌐 网站：[Signal Hunter](https://signal.felixwithai.com)
- 💬 反馈：欢迎在 GitHub 提出建议
- 📧 邮箱：hello@felixwithai.com

**感谢阅读本期周刊！**

---

*本周刊由 AI Signal Hunter 自动生成，收录本周最值得阅读的技术情报。*
"""

    return content


async def generate_weekly_newsletter(
    target_date: Optional[datetime] = None,
    min_score: int = 70,
    force_regenerate: bool = False,
) -> Optional[Newsletter]:
    """
    生成周刊的核心函数

    流程：
    1. 计算本周时间范围（周一到周日）
    2. 查询本周高分内容（按分类分组）
    3. 查询本周精选内容（score >= 85）
    4. 调用 LLM 生成综述
    5. 组装完整周刊 Markdown
    6. 存储到 Newsletter 表（去重检查）

    Args:
        target_date: 目标日期（默认为当前时间）
        min_score: 最低评分阈值（默认 70）
        force_regenerate: 是否强制重新生成（忽略已存在）

    Returns:
        生成的 Newsletter 对象，如果已存在且不强制重新生成则返回 None
    """
    # 1. 计算本周时间范围
    week_start, week_end = get_week_range(target_date)
    year, week_number = get_week_number(target_date)

    logger.info(f"[Newsletter] 开始生成 {year} 年第 {week_number} 周周刊")
    logger.info(f"[Newsletter] 时间范围：{week_start.date()} ~ {week_end.date()}")

    # 2. 检查是否已存在
    db = SessionLocal()
    try:
        existing = (
            db.query(Newsletter)
            .filter(
                and_(
                    Newsletter.year == year,
                    Newsletter.week_number == week_number,
                )
            )
            .first()
        )

        if existing and not force_regenerate:
            logger.info(f"[Newsletter] {year}年第{week_number}周周刊已存在，跳过生成")
            return None

        if existing and force_regenerate:
            logger.info(f"[Newsletter] 强制重新生成 {year}年第{week_number}周周刊")
            db.delete(existing)
            db.commit()

    finally:
        db.close()

    # 3. 获取本周内容
    domain_groups = fetch_weekly_top_resources(week_start, week_end, min_score=min_score)
    featured = fetch_featured_resources(week_start, week_end)

    # 检查是否有足够内容
    total_count = sum(len(resources) for resources in domain_groups.values())
    if total_count == 0:
        logger.warning(f"[Newsletter] 本周没有找到符合条件的内容，跳过生成")
        return None

    # 4. 生成周刊内容
    logger.info(f"[Newsletter] 开始生成周刊 Markdown（{total_count} 条内容）")
    content = await generate_newsletter_content(
        domain_groups=domain_groups,
        featured=featured,
        year=year,
        week_number=week_number,
    )

    # 5. 收集 resource_ids
    resource_ids = []
    for resources in domain_groups.values():
        for resource in resources:
            resource_ids.append(resource.id)

    # 6. 保存到数据库
    db = SessionLocal()
    newsletter_id = None
    try:
        newsletter = Newsletter(
            title=Newsletter.generate_title(year, week_number),
            year=year,
            week_number=week_number,
            content=content,
            resource_ids=resource_ids,
            published_at=datetime.now(),
        )

        db.add(newsletter)
        db.commit()
        db.refresh(newsletter)
        newsletter_id = newsletter.id

        logger.info(
            f"[Newsletter] ✅ 周刊生成成功：{newsletter.title} "
            f"({total_count} 条内容, {len(featured)} 条精选)"
        )

        return newsletter  # 返回对象供调用者立即使用

    except Exception as e:
        db.rollback()
        logger.error(f"[Newsletter] ❌ 保存周刊失败: {e}")
        raise

    # 注意：不关闭会话，让调用者在处理完对象后再关闭


# ============================================================
# Scheduler 调用包装函数（同步版本）
# ============================================================

def generate_newsletter_sync():
    """
    APScheduler 调用的同步包装函数

    每周五自动触发
    """
    import asyncio

    try:
        # 在新的事件循环中运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        newsletter = loop.run_until_complete(generate_weekly_newsletter())

        if newsletter:
            print(f"[Newsletter] ✅ 成功生成：{newsletter.title}")
        else:
            print("[Newsletter] ⚠️  本周无需生成（已存在或无内容）")

    except Exception as e:
        print(f"[Newsletter] ❌ 生成失败: {e}")
        logger.exception("[Newsletter] 生成异常")

    finally:
        loop.close()


# ============================================================
# 手动触发函数（用于测试）
# ============================================================

async def generate_newsletter_for_week(
    year: int,
    week_number: int,
    min_score: int = 70,
    force_regenerate: bool = True,
) -> Optional[Newsletter]:
    """
    为指定周生成周刊（手动触发，用于测试）

    Args:
        year: 年份
        week_number: 周数
        min_score: 最低评分
        force_regenerate: 是否强制重新生成

    Returns:
        Newsletter 对象
    """
    # 计算该周的周一
    from datetime import date
    jan_1 = date(year, 1, 1)
    # ISO 周数的周一
    week_start = datetime.fromisocalendar(year, week_number, 1)

    return await generate_weekly_newsletter(
        target_date=week_start,
        min_score=min_score,
        force_regenerate=force_regenerate,
    )
