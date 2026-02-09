"""
[INPUT]: 依赖 database, embedding_service, tavily, models/research
[OUTPUT]: 对外提供工具定义和执行函数
[POS]: agents/research/ 的工具层，被 sdk_service.py 消费
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import asyncio
import os
import structlog
from typing import Any

from app.database import SessionLocal
from app.models.research import ResearchSource, ResearchOutput

logger = structlog.get_logger()

# 合法的输出类型
VALID_OUTPUT_TYPES = {"report", "mindmap"}


# ============================================================
# 工具定义 (Anthropic Messages API tool format)
# ============================================================
RESEARCH_TOOLS = [
    {
        "name": "search_vectors",
        "description": (
            "在项目源材料中进行语义搜索，基于向量相似度查找最相关的文本片段。"
            "适合查找与查询语义相近的内容，即使措辞不同也能找到。"
            "优先使用此工具搜索项目内已有材料。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索查询文本"},
                "project_id": {"type": "string", "description": "项目 ID"},
                "top_k": {"type": "integer", "description": "返回结果数量", "default": 5},
            },
            "required": ["query", "project_id"],
        },
    },
    {
        "name": "search_fulltext",
        "description": (
            "在项目源材料中进行全文关键词搜索。"
            "适合精确匹配特定术语、名称或短语。"
            "与 search_vectors 互补: 向量搜索找语义相近的内容，全文搜索找精确匹配。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "project_id": {"type": "string", "description": "项目 ID"},
                "limit": {"type": "integer", "description": "返回结果数量", "default": 10},
            },
            "required": ["query", "project_id"],
        },
    },
    {
        "name": "tavily_search",
        "description": (
            "搜索互联网获取最新信息。"
            "当项目源材料不足以回答问题时使用。"
            "返回网页标题、URL 和内容摘要。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索查询"},
                "max_results": {"type": "integer", "description": "最大结果数", "default": 5},
                "search_depth": {"type": "string", "description": "搜索深度: basic 或 advanced", "default": "basic"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_source_content",
        "description": (
            "读取指定源材料的完整内容。"
            "当搜索返回的片段不够详细，需要查看完整文本时使用。"
            "需要提供 source_id（从搜索结果中获取）。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "source_id": {"type": "string", "description": "源材料 ID"},
                "project_id": {"type": "string", "description": "项目 ID"},
            },
            "required": ["source_id", "project_id"],
        },
    },
    {
        "name": "save_output",
        "description": (
            "将生成的报告或思维导图保存到项目数据库中。"
            "报告使用 Markdown 格式，思维导图使用 Mermaid 代码。"
            "保存后用户可以在 Studio 面板的输出列表中查看。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "output_type": {"type": "string", "description": "输出类型: report 或 mindmap"},
                "title": {"type": "string", "description": "输出标题"},
                "content": {"type": "string", "description": "输出内容 (Markdown 或 Mermaid)"},
            },
            "required": ["project_id", "output_type", "title", "content"],
        },
    },
]


# ============================================================
# 工具执行函数
# ============================================================
async def execute_tool(name: str, args: dict[str, Any]) -> str:
    """统一的工具执行入口"""
    handlers = {
        "search_vectors": _search_vectors,
        "search_fulltext": _search_fulltext,
        "tavily_search": _tavily_search,
        "read_source_content": _read_source_content,
        "save_output": _save_output,
    }

    handler = handlers.get(name)
    if not handler:
        return f"未知工具: {name}"

    try:
        return await handler(args)
    except Exception as e:
        # 服务端记录完整错误，返回给 LLM 的信息脱敏
        logger.error("tool.execution.failed", tool=name, error=str(e), exc_info=True)
        return f"工具 {name} 执行失败，请稍后重试。"


def _escape_like(s: str) -> str:
    """转义 ILIKE 通配符 (%, _, \\)"""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# ============================================================
# search_vectors — pgvector 语义搜索
# ============================================================
async def _search_vectors(args: dict) -> str:
    from app.agents.embeddings.bailian_embedding import embedding_service

    query = args["query"]
    project_id = args["project_id"]
    top_k = args.get("top_k", 5)

    # 异步生成查询向量
    query_embedding = await embedding_service.embed_query(query)

    # 同步 DB 查询放到线程池
    def _sync_query():
        from sqlalchemy import text as sa_text

        db = SessionLocal()
        try:
            sql = sa_text("""
                SELECT
                    se.source_id,
                    se.chunk_index,
                    se.chunk_text,
                    1 - (se.embedding <=> :query_embedding::vector) AS similarity,
                    rs.title AS source_title,
                    rs.source_type,
                    rs.original_url
                FROM source_embeddings se
                JOIN research_sources rs ON se.source_id = rs.id
                WHERE rs.project_id = :project_id::uuid
                  AND 1 - (se.embedding <=> :query_embedding::vector) >= 0.6
                ORDER BY se.embedding <=> :query_embedding::vector
                LIMIT :top_k
            """)

            result = db.execute(sql, {
                "query_embedding": str(query_embedding),
                "project_id": project_id,
                "top_k": top_k,
            })

            lines = [f"向量搜索 '{query}' 的结果:\n"]
            count = 0
            for row in result:
                count += 1
                similarity = round(float(row.similarity), 3)
                lines.append(f"[{count}] {row.source_title or '未命名'} (相似度: {similarity})")
                if row.original_url:
                    lines.append(f"    URL: {row.original_url}")
                lines.append(f"    内容: {row.chunk_text[:800]}")
                lines.append("")

            if count == 0:
                return f"未找到与 '{query}' 相关的项目材料。"

            return "\n".join(lines)
        finally:
            db.close()

    return await asyncio.to_thread(_sync_query)


# ============================================================
# search_fulltext — PostgreSQL ILIKE 搜索
# ============================================================
async def _search_fulltext(args: dict) -> str:
    query = args["query"]
    project_id = args["project_id"]
    limit = args.get("limit", 10)

    def _sync_query():
        from sqlalchemy import text as sa_text

        db = SessionLocal()
        try:
            sql = sa_text("""
                SELECT
                    rs.id AS source_id,
                    rs.title,
                    rs.source_type,
                    rs.original_url,
                    SUBSTRING(rs.full_text FROM 1 FOR 1000) AS excerpt
                FROM research_sources rs
                WHERE rs.project_id = :project_id::uuid
                  AND rs.processing_status = 'completed'
                  AND (
                      rs.full_text ILIKE :pattern ESCAPE '\\'
                      OR rs.title ILIKE :pattern ESCAPE '\\'
                      OR rs.summary ILIKE :pattern ESCAPE '\\'
                  )
                LIMIT :limit
            """)

            escaped = _escape_like(query)
            result = db.execute(sql, {
                "project_id": project_id,
                "pattern": f"%{escaped}%",
                "limit": limit,
            })

            lines = [f"全文搜索 '{query}' 的结果:\n"]
            count = 0
            for row in result:
                count += 1
                lines.append(f"[{count}] {row.title or '未命名'}")
                if row.original_url:
                    lines.append(f"    URL: {row.original_url}")
                if row.excerpt:
                    lines.append(f"    摘录: {row.excerpt[:500]}")
                lines.append("")

            if count == 0:
                return f"未找到包含 '{query}' 的源材料。"

            return "\n".join(lines)
        finally:
            db.close()

    return await asyncio.to_thread(_sync_query)


# ============================================================
# tavily_search — 网络搜索 (原生异步，无需 to_thread)
# ============================================================
async def _tavily_search(args: dict) -> str:
    from tavily import AsyncTavilyClient

    query = args["query"]
    max_results = args.get("max_results", 5)
    search_depth = args.get("search_depth", "basic")

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Tavily API Key 未配置。"

    client = AsyncTavilyClient(api_key=api_key)
    response = await client.search(
        query=query,
        max_results=max_results,
        search_depth=search_depth,
    )

    results = response.get("results", [])
    if not results:
        return f"网络搜索 '{query}' 未找到相关结果。"

    lines = [f"网络搜索 '{query}' 的结果 ({len(results)} 条):\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.get('title', '无标题')}")
        lines.append(f"    URL: {r.get('url', '')}")
        lines.append(f"    {r.get('content', '')[:600]}")
        lines.append("")

    return "\n".join(lines)


# ============================================================
# read_source_content — 读取源材料全文
# ============================================================
async def _read_source_content(args: dict) -> str:
    source_id = args["source_id"]
    project_id = args["project_id"]

    def _sync_read():
        db = SessionLocal()
        try:
            source = (
                db.query(ResearchSource)
                .filter(
                    ResearchSource.id == source_id,
                    ResearchSource.project_id == project_id,
                )
                .first()
            )

            if not source:
                return f"源材料 {source_id} 未找到或不属于当前项目。"

            content = source.full_text or source.summary or "该源材料暂无内容。"

            header = f"## {source.title or '未命名'}\n"
            if source.original_url:
                header += f"URL: {source.original_url}\n"
            header += f"类型: {source.source_type} | 状态: {source.processing_status}\n\n"

            max_chars = 30000
            if len(content) > max_chars:
                content = content[:max_chars] + f"\n\n... (内容已截断，总长 {len(content)} 字符)"

            return header + content
        finally:
            db.close()

    return await asyncio.to_thread(_sync_read)


# ============================================================
# save_output — 保存报告/思维导图
# ============================================================
async def _save_output(args: dict) -> str:
    project_id = args["project_id"]
    output_type = args["output_type"]
    title = args["title"]
    content = args["content"]

    # 验证 output_type
    if output_type not in VALID_OUTPUT_TYPES:
        return f"无效的 output_type: {output_type}，必须是 {VALID_OUTPUT_TYPES} 之一。"

    def _sync_save():
        db = SessionLocal()
        try:
            output = ResearchOutput(
                project_id=project_id,
                output_type=output_type,
                title=title,
                content=content,
                content_format="markdown" if output_type == "report" else "mermaid",
            )
            db.add(output)
            db.commit()
            db.refresh(output)
            return f"已保存 {output_type}: {title} (ID: {output.id})"
        except Exception as e:
            db.rollback()
            logger.error("tool.save_output.failed", error=str(e))
            return "保存失败，请重试。"
        finally:
            db.close()

    return await asyncio.to_thread(_sync_save)
