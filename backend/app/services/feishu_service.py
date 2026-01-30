"""
[INPUT]: 依赖 config.py 的飞书配置，依赖 httpx 的异步 HTTP 客户端
[OUTPUT]: 对外提供 FeishuService 类，支持飞书多维表格的 token 获取和记录写入
[POS]: services 的飞书 API 封装，被 DataTracker 调用进行数据追踪
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

飞书多维表格 API 服务:
- 获取 tenant_access_token (自动缓存，过期自动刷新)
- 批量新增记录 (最多 500 条/次)
- 异步写入，不阻塞主流程
- 失败容错，不影响 pipeline 正常运行
"""

import asyncio
import time
from typing import Optional

import httpx

from app.config import config


# ==============================================================================
#                             FEISHU SERVICE
# ==============================================================================

class FeishuService:
    """飞书多维表格 API 服务"""

    # API 端点
    TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    BATCH_CREATE_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
    CREATE_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"

    # 批量写入限制
    MAX_BATCH_SIZE = 500

    def __init__(self):
        self.app_id = config.feishu.app_id
        self.app_secret = config.feishu.app_secret
        self.app_token = config.feishu.app_token
        self.table_id = config.feishu.table_id
        self.enabled = config.feishu.enabled

        # Token 缓存
        self._token: Optional[str] = None
        self._token_expires_at: float = 0

    # --------------------------------------------------------------------------
    #                           TOKEN 管理
    # --------------------------------------------------------------------------

    async def get_tenant_token(self) -> Optional[str]:
        """
        获取 tenant_access_token (带缓存)

        飞书 token 有效期 2 小时，提前 5 分钟刷新
        """
        if not self.enabled:
            return None

        # 检查缓存
        if self._token and time.time() < self._token_expires_at - 300:
            return self._token

        # 请求新 token
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.TOKEN_URL,
                    json={
                        "app_id": self.app_id,
                        "app_secret": self.app_secret,
                    },
                )
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 0:
                    self._token = data.get("tenant_access_token")
                    # 飞书 token 默认 7200 秒 (2小时)
                    expire = data.get("expire", 7200)
                    self._token_expires_at = time.time() + expire
                    return self._token
                else:
                    print(f"[FeishuService] Token error: {data.get('msg')}")
                    return None

        except Exception as e:
            print(f"[FeishuService] Token request failed: {e}")
            return None

    # --------------------------------------------------------------------------
    #                           记录操作
    # --------------------------------------------------------------------------

    async def create_record(self, record: dict) -> bool:
        """
        新增单条记录

        Args:
            record: 记录字段，格式 {"字段名": 值}

        Returns:
            是否成功
        """
        if not self.enabled:
            return False

        token = await self.get_tenant_token()
        if not token:
            return False

        try:
            url = self.CREATE_URL.format(
                app_token=self.app_token,
                table_id=self.table_id,
            )

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json={"fields": record},
                )
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 0:
                    return True
                else:
                    print(f"[FeishuService] Create record error: {data.get('msg')}")
                    return False

        except Exception as e:
            print(f"[FeishuService] Create record failed: {e}")
            return False

    async def batch_create_records(self, records: list[dict]) -> int:
        """
        批量新增记录 (最多 500 条)

        Args:
            records: 记录列表，每条格式 {"字段名": 值}

        Returns:
            成功写入的记录数
        """
        if not self.enabled:
            return 0

        if not records:
            return 0

        token = await self.get_tenant_token()
        if not token:
            return 0

        success_count = 0

        # 分批处理
        for i in range(0, len(records), self.MAX_BATCH_SIZE):
            batch = records[i:i + self.MAX_BATCH_SIZE]
            batch_records = [{"fields": r} for r in batch]

            try:
                url = self.BATCH_CREATE_URL.format(
                    app_token=self.app_token,
                    table_id=self.table_id,
                )

                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        url,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                        },
                        json={"records": batch_records},
                    )
                    response.raise_for_status()
                    data = response.json()

                    if data.get("code") == 0:
                        created = len(data.get("data", {}).get("records", []))
                        success_count += created
                        print(f"[FeishuService] Batch created {created} records")
                    else:
                        print(f"[FeishuService] Batch create error: {data.get('msg')}")

            except Exception as e:
                print(f"[FeishuService] Batch create failed: {e}")

        return success_count


# ==============================================================================
#                             全局实例
# ==============================================================================

feishu_service = FeishuService()
