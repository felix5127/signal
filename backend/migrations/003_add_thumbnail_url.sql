-- ============================================================
-- Migration: Add thumbnail_url column
-- Version: 003
-- Date: 2026-01-29
-- Description: 添加 thumbnail_url 字段用于存储播客/视频缩略图
-- ============================================================

-- 添加 thumbnail_url 字段到 resources 表
ALTER TABLE resources ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;

-- 添加注释
COMMENT ON COLUMN resources.thumbnail_url IS '缩略图/封面 URL (播客/视频)';
