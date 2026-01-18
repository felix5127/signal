"""
[INPUT]: 依赖 dashscope, config.py, tiktoken
[OUTPUT]: 对外提供 BailianEmbeddingService 类，支持百炼 通用文本向量-v3
[POS]: agents/embeddings/ 的嵌入服务，被向量搜索工具消费
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import dashscope
from dashscope import TextEmbedding

from app.config import config

logger = logging.getLogger(__name__)


# ============================================================
# 配置
# ============================================================
@dataclass
class EmbeddingConfig:
    """嵌入配置"""
    model: str = "text-embedding-v3"  # 百炼 通用文本向量-v3
    dimension: int = 512  # 默认 512 维，可选 256/128/64
    batch_size: int = 25  # 每批最大数量
    max_tokens_per_text: int = 8192  # 每段文本最大 token


# ============================================================
# 嵌入服务
# ============================================================
class BailianEmbeddingService:
    """
    百炼 通用文本向量-v3 嵌入服务

    支持:
    - 单文本嵌入
    - 批量嵌入
    - 多维度 (512/256/128/64)

    使用示例:
    ```python
    service = BailianEmbeddingService()

    # 单文本
    embedding = await service.embed_text("这是一段测试文本")

    # 批量
    embeddings = await service.embed_texts([
        "文本1",
        "文本2",
        "文本3",
    ])
    ```
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        dimension: int = 512,
    ):
        """
        初始化服务

        Args:
            api_key: 百炼 API Key，默认从环境变量读取
            dimension: 向量维度 (512/256/128/64)
        """
        self.api_key = api_key or config.dashscope_api_key or ""
        self.dimension = dimension
        self.config = EmbeddingConfig(dimension=dimension)
        self._initialized = False

    def _ensure_init(self):
        """确保初始化"""
        if not self._initialized:
            if not self.api_key:
                raise ValueError("DashScope API key not configured. Set DASHSCOPE_API_KEY environment variable.")
            dashscope.api_key = self.api_key
            self._initialized = True

    @property
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return bool(self.api_key)

    async def embed_text(self, text: str) -> List[float]:
        """
        嵌入单个文本

        Args:
            text: 输入文本

        Returns:
            向量列表
        """
        self._ensure_init()

        try:
            response = TextEmbedding.call(
                model=self.config.model,
                input=text,
                dimension=self.dimension,
            )

            if response.status_code != 200:
                raise Exception(f"Embedding API error: {response.code} - {response.message}")

            embedding = response.output["embeddings"][0]["embedding"]
            logger.debug(f"Embedded text ({len(text)} chars) -> {len(embedding)} dims")

            return embedding

        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量嵌入文本

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        self._ensure_init()

        if not texts:
            return []

        embeddings = []

        # 分批处理
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]

            try:
                response = TextEmbedding.call(
                    model=self.config.model,
                    input=batch,
                    dimension=self.dimension,
                )

                if response.status_code != 200:
                    raise Exception(f"Embedding API error: {response.code} - {response.message}")

                batch_embeddings = [
                    item["embedding"]
                    for item in response.output["embeddings"]
                ]
                embeddings.extend(batch_embeddings)

                logger.debug(f"Embedded batch {i//self.config.batch_size + 1}: {len(batch)} texts")

            except Exception as e:
                logger.error(f"Batch embedding error: {e}")
                raise

        return embeddings

    async def embed_query(self, query: str) -> List[float]:
        """
        嵌入查询 (与 embed_text 相同，语义区分)

        Args:
            query: 查询文本

        Returns:
            向量
        """
        return await self.embed_text(query)

    async def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        嵌入文档列表 (与 embed_texts 相同，语义区分)

        Args:
            documents: 文档列表

        Returns:
            向量列表
        """
        return await self.embed_texts(documents)


# ============================================================
# 文本分块器
# ============================================================
class TextSplitter:
    """
    文本分块器

    支持:
    - 按 token 数分块
    - 重叠分块
    - 保留段落边界

    使用示例:
    ```python
    splitter = TextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(long_text)
    ```
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separator: str = "\n\n",
    ):
        """
        初始化分块器

        Args:
            chunk_size: 每块大小 (字符数)
            chunk_overlap: 重叠大小
            separator: 分隔符
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def split_text(self, text: str) -> List[str]:
        """
        分割文本

        Args:
            text: 输入文本

        Returns:
            分块列表
        """
        if not text:
            return []

        # 首先按分隔符分割
        splits = text.split(self.separator)
        splits = [s.strip() for s in splits if s.strip()]

        # 合并小块
        chunks = []
        current_chunk = []
        current_length = 0

        for split in splits:
            split_length = len(split)

            if current_length + split_length > self.chunk_size and current_chunk:
                # 保存当前块
                chunks.append(self.separator.join(current_chunk))

                # 计算重叠
                overlap_text = ""
                overlap_length = 0
                for item in reversed(current_chunk):
                    if overlap_length + len(item) <= self.chunk_overlap:
                        overlap_text = item + self.separator + overlap_text
                        overlap_length += len(item) + len(self.separator)
                    else:
                        break

                # 开始新块 (带重叠)
                if overlap_text:
                    current_chunk = [overlap_text.strip()]
                    current_length = len(overlap_text)
                else:
                    current_chunk = []
                    current_length = 0

            current_chunk.append(split)
            current_length += split_length + len(self.separator)

        # 保存最后一块
        if current_chunk:
            chunks.append(self.separator.join(current_chunk))

        return chunks

    def split_by_sentences(self, text: str) -> List[str]:
        """
        按句子分割 (保持语义完整)

        Args:
            text: 输入文本

        Returns:
            分块列表
        """
        import re

        # 句子分隔符
        sentence_endings = re.compile(r'(?<=[。！？.!?])\s*')
        sentences = sentence_endings.split(text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0

            current_chunk.append(sentence)
            current_length += sentence_length + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks


# ============================================================
# 全局实例
# ============================================================
embedding_service = BailianEmbeddingService()
text_splitter = TextSplitter()
