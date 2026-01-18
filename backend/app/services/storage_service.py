"""
[INPUT]: 依赖 boto3, config.py, hashlib, mimetypes
[OUTPUT]: 对外提供 StorageService 类，支持 R2/S3 文件上传、下载、预签名 URL
[POS]: services/ 的文件存储服务，被 api/upload, processors/multimodal 消费
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import hashlib
import mimetypes
import uuid
from datetime import datetime
from typing import Optional, BinaryIO, Dict, Any
from pathlib import Path
import logging

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from app.config import config

logger = logging.getLogger(__name__)


# ============================================================
# 配置常量
# ============================================================
class StorageConfig:
    """存储服务配置"""

    # R2 配置 (从环境变量读取)
    ENDPOINT_URL: str = config.r2_endpoint_url or ""
    ACCESS_KEY_ID: str = config.r2_access_key_id or ""
    SECRET_ACCESS_KEY: str = config.r2_secret_access_key or ""
    BUCKET_NAME: str = config.r2_bucket_name or "signal-research"
    PUBLIC_URL: str = config.r2_public_url or ""

    # 上传限制
    MAX_FILE_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_TYPES: Dict[str, list] = {
        "document": [".pdf", ".doc", ".docx", ".txt", ".md"],
        "audio": [".mp3", ".wav", ".m4a", ".ogg", ".flac"],
        "video": [".mp4", ".webm", ".mov", ".avi", ".mkv"],
        "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    }

    # 预签名 URL 过期时间 (秒)
    PRESIGNED_UPLOAD_EXPIRY: int = 3600  # 1 小时
    PRESIGNED_DOWNLOAD_EXPIRY: int = 86400  # 24 小时


# ============================================================
# 存储服务
# ============================================================
class StorageService:
    """
    Cloudflare R2 / S3 兼容存储服务

    功能:
    - 文件上传 (直接上传 / 预签名上传)
    - 文件下载 (直接下载 / 预签名 URL)
    - 文件删除
    - 文件元数据查询

    目录结构:
    - research/{project_id}/sources/{source_id}/{filename}
    - research/{project_id}/outputs/{output_id}/{filename}
    - research/{project_id}/podcasts/{podcast_id}/{filename}
    """

    def __init__(self):
        """初始化 S3 客户端"""
        self._client = None
        self._initialized = False

    def _ensure_client(self) -> boto3.client:
        """懒加载 S3 客户端"""
        if self._client is None:
            if not StorageConfig.ENDPOINT_URL:
                logger.warning("R2 endpoint URL not configured, storage service disabled")
                return None

            try:
                self._client = boto3.client(
                    "s3",
                    endpoint_url=StorageConfig.ENDPOINT_URL,
                    aws_access_key_id=StorageConfig.ACCESS_KEY_ID,
                    aws_secret_access_key=StorageConfig.SECRET_ACCESS_KEY,
                    config=BotoConfig(
                        signature_version="s3v4",
                        retries={"max_attempts": 3, "mode": "adaptive"},
                    ),
                )
                self._initialized = True
                logger.info(f"Storage service initialized with bucket: {StorageConfig.BUCKET_NAME}")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                return None

        return self._client

    @property
    def is_available(self) -> bool:
        """检查存储服务是否可用"""
        return self._ensure_client() is not None

    # ========== 文件路径生成 ==========

    def generate_path(
        self,
        project_id: str,
        category: str,
        filename: str,
        entity_id: Optional[str] = None,
    ) -> str:
        """
        生成存储路径

        Args:
            project_id: 研究项目 ID
            category: 分类 (sources, outputs, podcasts)
            filename: 原始文件名
            entity_id: 实体 ID (可选，默认生成 UUID)

        Returns:
            存储路径，如 research/{project_id}/sources/{entity_id}/{filename}
        """
        entity_id = entity_id or str(uuid.uuid4())
        # 清理文件名，保留扩展名
        safe_filename = self._sanitize_filename(filename)
        return f"research/{project_id}/{category}/{entity_id}/{safe_filename}"

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除危险字符"""
        # 只保留文件名和扩展名
        name = Path(filename).name
        # 替换危险字符
        for char in ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]:
            name = name.replace(char, "_")
        return name

    # ========== 文件验证 ==========

    def validate_file(
        self,
        filename: str,
        file_size: int,
        allowed_category: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        验证文件是否允许上传

        Args:
            filename: 文件名
            file_size: 文件大小 (字节)
            allowed_category: 允许的文件类别 (document, audio, video, image)

        Returns:
            (是否有效, 错误信息)
        """
        # 检查文件大小
        if file_size > StorageConfig.MAX_FILE_SIZE:
            max_mb = StorageConfig.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File size exceeds maximum limit of {max_mb}MB"

        # 检查文件扩展名
        ext = Path(filename).suffix.lower()
        if allowed_category:
            allowed = StorageConfig.ALLOWED_TYPES.get(allowed_category, [])
            if ext not in allowed:
                return False, f"File type {ext} not allowed for {allowed_category}"
        else:
            # 检查是否在任何允许类型中
            all_allowed = []
            for types in StorageConfig.ALLOWED_TYPES.values():
                all_allowed.extend(types)
            if ext not in all_allowed:
                return False, f"File type {ext} not allowed"

        return True, ""

    # ========== 文件上传 ==========

    async def upload_file(
        self,
        file: BinaryIO,
        path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        上传文件到 R2

        Args:
            file: 文件对象
            path: 存储路径
            content_type: MIME 类型
            metadata: 自定义元数据

        Returns:
            {
                "success": bool,
                "path": str,
                "url": str,
                "size": int,
                "etag": str,
                "error": str (if failed)
            }
        """
        client = self._ensure_client()
        if client is None:
            return {"success": False, "error": "Storage service not available"}

        try:
            # 读取文件内容
            file_content = file.read()
            file_size = len(file_content)

            # 推断 content_type
            if not content_type:
                content_type, _ = mimetypes.guess_type(path)
                content_type = content_type or "application/octet-stream"

            # 计算 MD5
            md5_hash = hashlib.md5(file_content).hexdigest()

            # 上传参数
            extra_args = {
                "ContentType": content_type,
                "Metadata": {
                    "md5": md5_hash,
                    "uploaded_at": datetime.utcnow().isoformat(),
                    **(metadata or {}),
                },
            }

            # 执行上传
            response = client.put_object(
                Bucket=StorageConfig.BUCKET_NAME,
                Key=path,
                Body=file_content,
                **extra_args,
            )

            # 构建公开 URL
            public_url = self._get_public_url(path)

            logger.info(f"File uploaded: {path} ({file_size} bytes)")

            return {
                "success": True,
                "path": path,
                "url": public_url,
                "size": file_size,
                "etag": response.get("ETag", "").strip('"'),
                "content_type": content_type,
            }

        except ClientError as e:
            error_msg = str(e)
            logger.error(f"Upload failed: {path} - {error_msg}")
            return {"success": False, "path": path, "error": error_msg}

    async def upload_from_bytes(
        self,
        content: bytes,
        path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        从字节数据上传文件

        Args:
            content: 文件内容 (bytes)
            path: 存储路径
            content_type: MIME 类型
            metadata: 自定义元数据

        Returns:
            上传结果
        """
        from io import BytesIO

        file = BytesIO(content)
        return await self.upload_file(file, path, content_type, metadata)

    # ========== 预签名上传 ==========

    def generate_presigned_upload_url(
        self,
        path: str,
        content_type: str,
        expires_in: int = StorageConfig.PRESIGNED_UPLOAD_EXPIRY,
    ) -> Dict[str, Any]:
        """
        生成预签名上传 URL (客户端直传)

        Args:
            path: 存储路径
            content_type: 文件 MIME 类型
            expires_in: 过期时间 (秒)

        Returns:
            {
                "success": bool,
                "upload_url": str,
                "path": str,
                "expires_in": int,
                "error": str (if failed)
            }
        """
        client = self._ensure_client()
        if client is None:
            return {"success": False, "error": "Storage service not available"}

        try:
            url = client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": StorageConfig.BUCKET_NAME,
                    "Key": path,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )

            return {
                "success": True,
                "upload_url": url,
                "path": path,
                "content_type": content_type,
                "expires_in": expires_in,
            }

        except ClientError as e:
            error_msg = str(e)
            logger.error(f"Generate presigned upload URL failed: {path} - {error_msg}")
            return {"success": False, "path": path, "error": error_msg}

    # ========== 文件下载 ==========

    async def download_file(self, path: str) -> Dict[str, Any]:
        """
        下载文件

        Args:
            path: 存储路径

        Returns:
            {
                "success": bool,
                "content": bytes,
                "content_type": str,
                "size": int,
                "error": str (if failed)
            }
        """
        client = self._ensure_client()
        if client is None:
            return {"success": False, "error": "Storage service not available"}

        try:
            response = client.get_object(
                Bucket=StorageConfig.BUCKET_NAME,
                Key=path,
            )

            content = response["Body"].read()

            return {
                "success": True,
                "content": content,
                "content_type": response.get("ContentType", "application/octet-stream"),
                "size": len(content),
                "etag": response.get("ETag", "").strip('"'),
            }

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                return {"success": False, "error": "File not found"}
            logger.error(f"Download failed: {path} - {e}")
            return {"success": False, "error": str(e)}

    def generate_presigned_download_url(
        self,
        path: str,
        expires_in: int = StorageConfig.PRESIGNED_DOWNLOAD_EXPIRY,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        生成预签名下载 URL

        Args:
            path: 存储路径
            expires_in: 过期时间 (秒)
            filename: 下载时的文件名 (可选)

        Returns:
            {
                "success": bool,
                "download_url": str,
                "expires_in": int,
                "error": str (if failed)
            }
        """
        client = self._ensure_client()
        if client is None:
            return {"success": False, "error": "Storage service not available"}

        try:
            params = {
                "Bucket": StorageConfig.BUCKET_NAME,
                "Key": path,
            }

            # 设置下载文件名
            if filename:
                params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'

            url = client.generate_presigned_url(
                ClientMethod="get_object",
                Params=params,
                ExpiresIn=expires_in,
            )

            return {
                "success": True,
                "download_url": url,
                "path": path,
                "expires_in": expires_in,
            }

        except ClientError as e:
            error_msg = str(e)
            logger.error(f"Generate presigned download URL failed: {path} - {error_msg}")
            return {"success": False, "path": path, "error": error_msg}

    # ========== 文件删除 ==========

    async def delete_file(self, path: str) -> Dict[str, Any]:
        """
        删除文件

        Args:
            path: 存储路径

        Returns:
            {
                "success": bool,
                "path": str,
                "error": str (if failed)
            }
        """
        client = self._ensure_client()
        if client is None:
            return {"success": False, "error": "Storage service not available"}

        try:
            client.delete_object(
                Bucket=StorageConfig.BUCKET_NAME,
                Key=path,
            )

            logger.info(f"File deleted: {path}")
            return {"success": True, "path": path}

        except ClientError as e:
            error_msg = str(e)
            logger.error(f"Delete failed: {path} - {error_msg}")
            return {"success": False, "path": path, "error": error_msg}

    async def delete_folder(self, prefix: str) -> Dict[str, Any]:
        """
        删除文件夹 (所有以 prefix 开头的文件)

        Args:
            prefix: 路径前缀

        Returns:
            {
                "success": bool,
                "deleted_count": int,
                "error": str (if failed)
            }
        """
        client = self._ensure_client()
        if client is None:
            return {"success": False, "error": "Storage service not available"}

        try:
            # 列出所有匹配的对象
            paginator = client.get_paginator("list_objects_v2")
            pages = paginator.paginate(
                Bucket=StorageConfig.BUCKET_NAME,
                Prefix=prefix,
            )

            deleted_count = 0
            for page in pages:
                objects = page.get("Contents", [])
                if not objects:
                    continue

                # 批量删除
                delete_request = {
                    "Objects": [{"Key": obj["Key"]} for obj in objects]
                }
                client.delete_objects(
                    Bucket=StorageConfig.BUCKET_NAME,
                    Delete=delete_request,
                )
                deleted_count += len(objects)

            logger.info(f"Folder deleted: {prefix} ({deleted_count} files)")
            return {"success": True, "deleted_count": deleted_count}

        except ClientError as e:
            error_msg = str(e)
            logger.error(f"Delete folder failed: {prefix} - {error_msg}")
            return {"success": False, "error": error_msg}

    # ========== 文件信息 ==========

    async def get_file_info(self, path: str) -> Dict[str, Any]:
        """
        获取文件信息

        Args:
            path: 存储路径

        Returns:
            {
                "success": bool,
                "exists": bool,
                "size": int,
                "content_type": str,
                "last_modified": str,
                "metadata": dict,
                "error": str (if failed)
            }
        """
        client = self._ensure_client()
        if client is None:
            return {"success": False, "error": "Storage service not available"}

        try:
            response = client.head_object(
                Bucket=StorageConfig.BUCKET_NAME,
                Key=path,
            )

            return {
                "success": True,
                "exists": True,
                "path": path,
                "size": response.get("ContentLength", 0),
                "content_type": response.get("ContentType", ""),
                "last_modified": response.get("LastModified", "").isoformat()
                if response.get("LastModified")
                else None,
                "etag": response.get("ETag", "").strip('"'),
                "metadata": response.get("Metadata", {}),
            }

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey"):
                return {"success": True, "exists": False, "path": path}
            logger.error(f"Get file info failed: {path} - {e}")
            return {"success": False, "error": str(e)}

    # ========== 辅助方法 ==========

    def _get_public_url(self, path: str) -> str:
        """获取文件的公开 URL"""
        if StorageConfig.PUBLIC_URL:
            return f"{StorageConfig.PUBLIC_URL.rstrip('/')}/{path}"
        return f"{StorageConfig.ENDPOINT_URL}/{StorageConfig.BUCKET_NAME}/{path}"


# ============================================================
# 全局实例
# ============================================================
storage_service = StorageService()
