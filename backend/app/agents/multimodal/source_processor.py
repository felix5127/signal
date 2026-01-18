"""
[INPUT]: 依赖 tingwu_client, embeddings/bailian_embedding, storage_service
[OUTPUT]: 对外提供 SourceProcessor 类，处理各类源材料
[POS]: multimodal 的源材料处理器
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import logging
import httpx
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.research import ResearchSource, SourceEmbedding
from app.agents.multimodal.tingwu_client import tingwu_client, TranscriptionResult
from app.agents.embeddings.bailian_embedding import embedding_service, TextSplitter
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)


# ============================================================
# 类型定义
# ============================================================

class ProcessingStatus(str, Enum):
    """处理状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingResult:
    """处理结果"""
    source_id: UUID
    status: ProcessingStatus
    full_text: Optional[str] = None
    summary: Optional[str] = None
    chunk_count: int = 0
    error: Optional[str] = None


# ============================================================
# 源材料处理器
# ============================================================

class SourceProcessor:
    """
    源材料处理器

    功能:
    - 处理 URL: 抓取网页内容
    - 处理音频: 调用听悟 API 转写
    - 处理视频: 调用听悟 API 转写
    - 处理 PDF: 提取文本内容
    - 生成嵌入向量

    使用示例:
    ```python
    processor = SourceProcessor()

    # 处理源材料
    result = await processor.process_source(source_id)
    print(result.full_text)
    ```
    """

    # URL 内容提取配置
    JINA_READER_URL = "https://r.jina.ai/"

    def __init__(self):
        """初始化处理器"""
        self.splitter = TextSplitter()

    async def process_source(
        self,
        source_id: UUID,
        db: Optional[Session] = None,
    ) -> ProcessingResult:
        """
        处理源材料

        Args:
            source_id: 源材料 ID
            db: 数据库会话

        Returns:
            处理结果
        """
        should_close = db is None
        if db is None:
            db = SessionLocal()

        try:
            # 获取源材料
            source = db.query(ResearchSource).filter(
                ResearchSource.id == source_id
            ).first()

            if not source:
                return ProcessingResult(
                    source_id=source_id,
                    status=ProcessingStatus.FAILED,
                    error="Source not found",
                )

            # 更新状态为处理中
            source.processing_status = ProcessingStatus.PROCESSING.value
            db.commit()

            # 根据类型处理
            if source.source_type == "url":
                result = await self._process_url(source)
            elif source.source_type in ("audio", "video"):
                result = await self._process_media(source)
            elif source.source_type == "pdf":
                result = await self._process_pdf(source)
            elif source.source_type == "text":
                result = await self._process_text(source)
            else:
                result = ProcessingResult(
                    source_id=source_id,
                    status=ProcessingStatus.FAILED,
                    error=f"Unsupported source type: {source.source_type}",
                )

            # 更新源材料
            if result.status == ProcessingStatus.COMPLETED:
                source.full_text = result.full_text
                source.summary = result.summary
                source.processing_status = ProcessingStatus.COMPLETED.value

                # 生成嵌入向量
                await self._generate_embeddings(source, db)

            else:
                source.processing_status = ProcessingStatus.FAILED.value

            db.commit()
            return result

        except Exception as e:
            logger.error(f"Failed to process source {source_id}: {e}")
            if source:
                source.processing_status = ProcessingStatus.FAILED.value
                db.commit()

            return ProcessingResult(
                source_id=source_id,
                status=ProcessingStatus.FAILED,
                error=str(e),
            )

        finally:
            if should_close:
                db.close()

    async def _process_url(self, source: ResearchSource) -> ProcessingResult:
        """
        处理 URL 类型源材料

        Args:
            source: 源材料对象

        Returns:
            处理结果
        """
        if not source.original_url:
            return ProcessingResult(
                source_id=source.id,
                status=ProcessingStatus.FAILED,
                error="No URL provided",
            )

        try:
            # 使用 Jina Reader 提取内容
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.JINA_READER_URL}{source.original_url}",
                    headers={"Accept": "text/plain"},
                )
                response.raise_for_status()
                content = response.text

            # 清理内容
            content = self._clean_text(content)

            # 提取标题 (如果没有)
            if not source.title:
                lines = content.split("\n")
                for line in lines[:10]:
                    line = line.strip()
                    if line and len(line) > 5 and len(line) < 200:
                        source.title = line
                        break

            # 生成摘要 (取前 500 字)
            summary = content[:500] + "..." if len(content) > 500 else content

            return ProcessingResult(
                source_id=source.id,
                status=ProcessingStatus.COMPLETED,
                full_text=content,
                summary=summary,
            )

        except Exception as e:
            logger.error(f"Failed to process URL: {e}")
            return ProcessingResult(
                source_id=source.id,
                status=ProcessingStatus.FAILED,
                error=str(e),
            )

    async def _process_media(self, source: ResearchSource) -> ProcessingResult:
        """
        处理音频/视频类型源材料

        Args:
            source: 源材料对象

        Returns:
            处理结果
        """
        if not tingwu_client.is_available:
            return ProcessingResult(
                source_id=source.id,
                status=ProcessingStatus.FAILED,
                error="Tingwu API not configured",
            )

        # 获取文件 URL
        file_url = None
        if source.file_path:
            # 从 R2 获取预签名 URL
            file_url = await storage_service.get_presigned_url(source.file_path)

        if not file_url:
            return ProcessingResult(
                source_id=source.id,
                status=ProcessingStatus.FAILED,
                error="No file URL available",
            )

        try:
            # 调用听悟转写
            result = await tingwu_client.transcribe(
                file_url=file_url,
                file_type=source.source_type,
            )

            if result.error:
                return ProcessingResult(
                    source_id=source.id,
                    status=ProcessingStatus.FAILED,
                    error=result.error,
                )

            # 生成摘要 (取前 500 字)
            summary = result.full_text[:500] + "..." if len(result.full_text) > 500 else result.full_text

            return ProcessingResult(
                source_id=source.id,
                status=ProcessingStatus.COMPLETED,
                full_text=result.full_text,
                summary=summary,
            )

        except Exception as e:
            logger.error(f"Failed to transcribe media: {e}")
            return ProcessingResult(
                source_id=source.id,
                status=ProcessingStatus.FAILED,
                error=str(e),
            )

    async def _process_pdf(self, source: ResearchSource) -> ProcessingResult:
        """
        处理 PDF 类型源材料

        使用 PyPDF2 提取 PDF 文本内容。

        Args:
            source: 源材料对象

        Returns:
            处理结果
        """
        if not source.file_path:
            return ProcessingResult(
                source_id=source.id,
                status=ProcessingStatus.FAILED,
                error="No file path provided",
            )

        try:
            # 从 R2 下载 PDF 文件
            file_bytes = await storage_service.download_file(source.file_path)
            if not file_bytes:
                return ProcessingResult(
                    source_id=source.id,
                    status=ProcessingStatus.FAILED,
                    error="Failed to download PDF file",
                )

            # 使用 PyPDF2 提取文本
            import io
            try:
                from PyPDF2 import PdfReader
            except ImportError:
                logger.error("PyPDF2 not installed, falling back to pdfplumber")
                try:
                    import pdfplumber
                    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                        text_parts = []
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text_parts.append(page_text)
                        content = "\n\n".join(text_parts)
                except ImportError:
                    return ProcessingResult(
                        source_id=source.id,
                        status=ProcessingStatus.FAILED,
                        error="Neither PyPDF2 nor pdfplumber is installed",
                    )
            else:
                # PyPDF2 方式提取
                pdf_file = io.BytesIO(file_bytes)
                reader = PdfReader(pdf_file)

                text_parts = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                content = "\n\n".join(text_parts)

            if not content or len(content.strip()) < 10:
                return ProcessingResult(
                    source_id=source.id,
                    status=ProcessingStatus.FAILED,
                    error="No text content extracted from PDF",
                )

            # 清理文本
            content = self._clean_text(content)

            # 提取标题 (如果没有)
            if not source.title:
                lines = content.split("\n")
                for line in lines[:10]:
                    line = line.strip()
                    if line and len(line) > 5 and len(line) < 200:
                        source.title = line
                        break

            # 生成摘要
            summary = content[:500] + "..." if len(content) > 500 else content

            logger.info(f"Extracted {len(content)} chars from PDF: {source.file_path}")

            return ProcessingResult(
                source_id=source.id,
                status=ProcessingStatus.COMPLETED,
                full_text=content,
                summary=summary,
            )

        except Exception as e:
            logger.error(f"Failed to process PDF: {e}")
            return ProcessingResult(
                source_id=source.id,
                status=ProcessingStatus.FAILED,
                error=str(e),
            )

    async def _process_text(self, source: ResearchSource) -> ProcessingResult:
        """
        处理纯文本类型源材料

        Args:
            source: 源材料对象

        Returns:
            处理结果
        """
        if not source.full_text:
            return ProcessingResult(
                source_id=source.id,
                status=ProcessingStatus.FAILED,
                error="No text content",
            )

        # 文本已经在数据库中，只需生成摘要
        content = source.full_text
        summary = content[:500] + "..." if len(content) > 500 else content

        return ProcessingResult(
            source_id=source.id,
            status=ProcessingStatus.COMPLETED,
            full_text=content,
            summary=summary,
        )

    async def _generate_embeddings(
        self,
        source: ResearchSource,
        db: Session,
    ) -> int:
        """
        生成嵌入向量

        Args:
            source: 源材料对象
            db: 数据库会话

        Returns:
            生成的向量数量
        """
        if not source.full_text:
            return 0

        if not embedding_service.is_available:
            logger.warning("Embedding service not available, skipping")
            return 0

        try:
            # 分块
            chunks = self.splitter.split_text(
                source.full_text,
                chunk_size=1000,
                overlap=100,
            )

            if not chunks:
                return 0

            # 批量生成嵌入
            embeddings = await embedding_service.embed_texts(chunks)

            # 存储到数据库
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                source_embedding = SourceEmbedding(
                    source_id=source.id,
                    chunk_index=i,
                    chunk_text=chunk,
                    embedding=embedding,
                )
                db.add(source_embedding)

            db.commit()

            logger.info(f"Generated {len(embeddings)} embeddings for source {source.id}")
            return len(embeddings)

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return 0

    def _clean_text(self, text: str) -> str:
        """
        清理文本

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        return text.strip()


# ============================================================
# 单例
# ============================================================

source_processor = SourceProcessor()
