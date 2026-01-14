// Input: 用户交互（筛选、搜索）
// Output: 更新 URL 参数，触发数据重新加载
// Position: 前端筛选组件，提供交互式过滤功能
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

/**
 * [INPUT]: 依赖 Next.js useRouter/useSearchParams、React useState/useEffect、lucide-react 图标
 * [OUTPUT]: 对外提供筛选器组件，包含搜索框、下拉筛选和重置按钮
 * [POS]: components/ 的筛选组件，被首页消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect } from "react";
import { Input } from '@/lib/design-system/web/components/Input'
import { Search, Database, Star, Folder, ArrowUpDown, RotateCcw } from 'lucide-react'

export function FilterBar() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [search, setSearch] = useState(searchParams?.get("search") || "");
  const [source, setSource] = useState(searchParams?.get("source") || "");
  const [minScore, setMinScore] = useState(searchParams?.get("min_score") || "");
  const [category, setCategory] = useState(searchParams?.get("category") || "");
  const [sortBy, setSortBy] = useState(searchParams?.get("sort_by") || "created_at");

  // 更新 URL 参数
  const updateFilters = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams?.toString() || "");

    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }

    router.push(`/?${params.toString()}`);
  };

  return (
    <div className="bg-[var(--ds-bg)] rounded-2xl p-5 mb-6 border border-[var(--ds-border)]">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 mb-4">
        {/* 搜索框 */}
        <div>
          <label className="block text-xs font-medium text-[var(--ds-muted)] mb-1.5 flex items-center gap-1">
            <Search className="w-3 h-3" />
            搜索
          </label>
          <Input
            type="text"
            placeholder="输入标题关键词..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                updateFilters('search', search);
              }
            }}
            startAdornment={<Search className="w-4 h-4 text-[var(--ds-muted)]" />}
          />
        </div>

        {/* 数据源筛选 */}
        <div>
          <label className="block text-xs font-medium text-[var(--ds-muted)] mb-1.5 flex items-center gap-1">
            <Database className="w-3 h-3" />
            数据源
          </label>
          <select
            value={source}
            onChange={(e) => {
              setSource(e.target.value);
              updateFilters('source', e.target.value);
            }}
            className="w-full px-3 py-2 rounded-xl border border-[var(--ds-border)] bg-[var(--ds-bg)] text-[var(--ds-fg)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ds-ring)]"
          >
            <option value="">全部来源</option>
            <option value="hn">Hacker News</option>
            <option value="github">GitHub</option>
            <option value="huggingface">Hugging Face</option>
          </select>
        </div>

        {/* 最低评分 */}
        <div>
          <label className="block text-xs font-medium text-[var(--ds-muted)] mb-1.5 flex items-center gap-1">
            <Star className="w-3 h-3" />
            最低评分
          </label>
          <select
            value={minScore}
            onChange={(e) => {
              setMinScore(e.target.value);
              updateFilters('min_score', e.target.value);
            }}
            className="w-full px-3 py-2 rounded-xl border border-[var(--ds-border)] bg-[var(--ds-bg)] text-[var(--ds-fg)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ds-ring)]"
          >
            <option value="">全部评分</option>
            <option value="5">5星 (推荐)</option>
            <option value="4">4星+</option>
            <option value="3">3星+</option>
          </select>
        </div>

        {/* 分类筛选 */}
        <div>
          <label className="block text-xs font-medium text-[var(--ds-muted)] mb-1.5 flex items-center gap-1">
            <Folder className="w-3 h-3" />
            分类
          </label>
          <select
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              updateFilters('category', e.target.value);
            }}
            className="w-full px-3 py-2 rounded-xl border border-[var(--ds-border)] bg-[var(--ds-bg)] text-[var(--ds-fg)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ds-ring)]"
          >
            <option value="">全部分类</option>
            <option value="技术突破">技术突破</option>
            <option value="开源工具">开源工具</option>
            <option value="商业产品">商业产品</option>
            <option value="论文研究">论文研究</option>
            <option value="行业动态">行业动态</option>
          </select>
        </div>

        {/* 排序方式 */}
        <div>
          <label className="block text-xs font-medium text-[var(--ds-muted)] mb-1.5 flex items-center gap-1">
            <ArrowUpDown className="w-3 h-3" />
            排序
          </label>
          <select
            value={sortBy}
            onChange={(e) => {
              setSortBy(e.target.value);
              updateFilters('sort_by', e.target.value);
            }}
            className="w-full px-3 py-2 rounded-xl border border-[var(--ds-border)] bg-[var(--ds-bg)] text-[var(--ds-fg)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ds-ring)]"
          >
            <option value="created_at">最新发布</option>
            <option value="final_score">最高评分</option>
          </select>
        </div>
      </div>

      {/* 重置按钮 */}
      {(search || source || minScore || category || sortBy !== 'created_at') && (
        <button
          onClick={() => {
            setSearch('');
            setSource('');
            setMinScore('');
            setCategory('');
            setSortBy('created_at');
            router.push('/');
          }}
          className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--ds-surface-2)] border border-[var(--ds-border)] rounded-xl text-xs font-medium text-[var(--ds-fg)] hover:bg-[var(--ds-bg)] transition-all duration-200 hover:scale-[1.02] active:scale-[0.97]"
        >
          <RotateCcw className="w-3 h-3" />
          重置筛选
        </button>
      )}
    </div>
  );
}
