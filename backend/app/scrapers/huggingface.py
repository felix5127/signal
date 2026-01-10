# Input: Hugging Face API (Models + Datasets API)
# Output: RawSignal 列表（经规则预筛的 HF 热门模型/数据集）
# Position: Hugging Face 数据源爬虫，实现规则预筛（Likes + Downloads + Task）
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import logging
from datetime import datetime, timedelta
from typing import List, Optional

import httpx

from app.config import config

logger = logging.getLogger(__name__)
from app.scrapers.base import BaseScraper, RawSignal


class HuggingFaceScraper(BaseScraper):
    """
    Hugging Face 模型/数据集爬虫

    数据源：Hugging Face API (Models API + Datasets API)
    规则预筛：
    1. Likes > min_likes (default: 10)
    2. Downloads > min_downloads (default: 100)
    3. Task in whitelist (text-generation, image-generation, etc.)

    这一步过滤掉约 70% 的噪音，减少后续 LLM 调用成本
    """

    BASE_URL = "https://huggingface.co/api"

    def __init__(self):
        super().__init__(source_name="huggingface")
        self.min_likes = config.huggingface.min_likes
        self.min_downloads = config.huggingface.min_downloads
        self.tasks = config.huggingface.tasks
        self.max_items = config.huggingface.max_items  # 使用配置中的 max_items

    def _passes_rule_filter_model(self, model: dict) -> bool:
        """
        模型规则预筛逻辑

        条件（AND）：
        1. Likes >= min_likes
        2. Downloads >= min_downloads
        3. Task 在白名单中（可选）
        4. 不是私有模型

        Args:
            model: Hugging Face model 数据

        Returns:
            是否通过规则过滤
        """
        # 1. 检查 likes
        likes = model.get("likes", 0)
        if likes < self.min_likes:
            return False

        # 2. 检查 downloads
        downloads = model.get("downloads", 0)
        if downloads < self.min_downloads:
            return False

        # 3. 检查是否私有
        if model.get("private", False):
            return False

        # 4. Task 白名单检查（如果配置了 tasks）
        if self.tasks:
            # pipeline_tag 表示模型的任务类型
            pipeline_tag = model.get("pipeline_tag", "")
            if pipeline_tag and pipeline_tag not in self.tasks:
                return False

        return True

    def _passes_rule_filter_dataset(self, dataset: dict) -> bool:
        """
        数据集规则预筛逻辑

        条件（AND）：
        1. Likes >= min_likes
        2. Downloads >= min_downloads (最近30天)
        3. 不是私有数据集

        Args:
            dataset: Hugging Face dataset 数据

        Returns:
            是否通过规则过滤
        """
        # 1. 检查 likes
        likes = dataset.get("likes", 0)
        if likes < self.min_likes:
            return False

        # 2. 检查 downloads (注意：datasets API 返回的是 downloads 字段)
        downloads = dataset.get("downloads", 0)
        if downloads < self.min_downloads:
            return False

        # 3. 检查是否私有
        if dataset.get("private", False):
            return False

        return True

    def _convert_model_to_raw_signal(self, model: dict) -> RawSignal:
        """
        转换 HF model 为 RawSignal

        Args:
            model: Hugging Face model 数据

        Returns:
            RawSignal 对象
        """
        # 构建 URL
        model_id = model.get("id", "")  # e.g., "openai/whisper-large-v3"
        url = f"https://huggingface.co/{model_id}"

        # 获取创建时间
        created_at = None
        if model.get("createdAt"):
            try:
                created_at = datetime.fromisoformat(
                    model["createdAt"].replace("Z", "+00:00")
                )
            except ValueError as e:
                logger.debug(f"Failed to parse model createdAt: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error parsing model createdAt: {e}")

        # 获取描述（可能在 cardData 中）
        description = ""
        card_data = model.get("cardData", {})
        if isinstance(card_data, dict):
            description = card_data.get("summary", "") or card_data.get(
                "description", ""
            )

        # 构建标题
        title = f"{model_id}: {description}" if description else model_id

        return RawSignal(
            source=self.source_name,
            source_id=model_id,
            url=url,
            title=title,
            content=None,
            source_created_at=created_at,
            metadata={
                "model_id": model_id,
                "likes": model.get("likes", 0),
                "downloads": model.get("downloads", 0),
                "pipeline_tag": model.get("pipeline_tag", ""),
                "tags": model.get("tags", []),
                "author": model.get("author", ""),
                "library_name": model.get("library_name", ""),
                "type": "model",
            },
        )

    def _convert_dataset_to_raw_signal(self, dataset: dict) -> RawSignal:
        """
        转换 HF dataset 为 RawSignal

        Args:
            dataset: Hugging Face dataset 数据

        Returns:
            RawSignal 对象
        """
        # 构建 URL
        dataset_id = dataset.get("id", "")
        url = f"https://huggingface.co/datasets/{dataset_id}"

        # 获取创建时间
        created_at = None
        if dataset.get("createdAt"):
            try:
                created_at = datetime.fromisoformat(
                    dataset["createdAt"].replace("Z", "+00:00")
                )
            except ValueError as e:
                logger.debug(f"Failed to parse dataset createdAt: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error parsing dataset createdAt: {e}")

        # 获取描述
        description = dataset.get("description", "")
        card_data = dataset.get("cardData", {})
        if isinstance(card_data, dict) and not description:
            description = card_data.get("summary", "") or card_data.get(
                "description", ""
            )

        # 构建标题
        title = f"{dataset_id}: {description}" if description else dataset_id

        return RawSignal(
            source=self.source_name,
            source_id=dataset_id,
            url=url,
            title=title,
            content=None,
            source_created_at=created_at,
            metadata={
                "dataset_id": dataset_id,
                "likes": dataset.get("likes", 0),
                "downloads": dataset.get("downloads", 0),
                "tags": dataset.get("tags", []),
                "author": dataset.get("author", ""),
                "type": "dataset",
            },
        )

    async def scrape(self) -> List[RawSignal]:
        """
        抓取 Hugging Face 模型和数据集并规则预筛

        流程：
        1. 抓取更多热门模型（按 likes 排序）
        2. 抓取更多热门数据集（按 likes 排序）
        3. 规则预筛（Likes + Downloads + Task）
        4. 按 likes 排序，取前 max_items 条
        5. 转换为 RawSignal

        Returns:
            RawSignal 列表（已通过规则预筛，按 likes 排序）
        """
        all_candidates = []  # 存储 (likes, type, signal) 元组用于排序

        async with httpx.AsyncClient() as client:
            # ========== 1. 抓取模型 ==========
            try:
                print("[HuggingFace] Fetching models...")

                # 获取更多数据，确保过滤后有足够的高质量内容
                fetch_limit = self.max_items * 3

                models_url = f"{self.BASE_URL}/models"
                params = {
                    "sort": "likes",  # 按 likes 排序
                    "direction": -1,  # 降序
                    "limit": fetch_limit,
                    "full": "true",  # 获取完整信息
                }

                resp = await client.get(models_url, params=params, timeout=30.0)
                resp.raise_for_status()
                models = resp.json()

                print(f"[HuggingFace] Fetched {len(models)} models")

                # 规则预筛
                for model in models:
                    if self._passes_rule_filter_model(model):
                        signal = self._convert_model_to_raw_signal(model)
                        likes = model.get("likes", 0)
                        all_candidates.append((likes, "model", signal))

            except Exception as e:
                print(f"[HuggingFace] Model fetch failed: {e}")

            # ========== 2. 抓取数据集 ==========
            try:
                print("[HuggingFace] Fetching datasets...")

                fetch_limit = self.max_items * 2

                datasets_url = f"{self.BASE_URL}/datasets"
                params = {
                    "sort": "likes",
                    "direction": -1,
                    "limit": fetch_limit,
                    "full": "true",
                }

                resp = await client.get(datasets_url, params=params, timeout=30.0)
                resp.raise_for_status()
                datasets = resp.json()

                print(f"[HuggingFace] Fetched {len(datasets)} datasets")

                # 规则预筛
                for dataset in datasets:
                    if self._passes_rule_filter_dataset(dataset):
                        signal = self._convert_dataset_to_raw_signal(dataset)
                        likes = dataset.get("likes", 0)
                        all_candidates.append((likes, "dataset", signal))

            except Exception as e:
                print(f"[HuggingFace] Dataset fetch failed: {e}")

        # 按 likes 降序排序，取前 max_items 条
        all_candidates.sort(key=lambda x: x[0], reverse=True)
        signals = [signal for _, _, signal in all_candidates[:self.max_items]]

        # 统计模型和数据集数量
        model_count = sum(1 for _, t, _ in all_candidates if t == "model")
        dataset_count = sum(1 for _, t, _ in all_candidates if t == "dataset")

        print(
            f"[HuggingFace] {len(all_candidates)} items passed filter "
            f"({model_count} models, {dataset_count} datasets), "
            f"returning top {len(signals)} by likes "
            f"(likes range: {all_candidates[0][0] if all_candidates else 0} - "
            f"{all_candidates[-1][0] if all_candidates else 0})"
        )

        return signals
