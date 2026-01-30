# dashboard/
> L2 | 父级: admin/CLAUDE.md

## 职责
Admin Dashboard "一页总览仪表盘"，让管理员一眼看清系统全貌。

## 核心痛点解决
1. **实时任务状态** - 三色状态灯 + Pipeline 运行指示器
2. **数据采集量** - 核心指标卡片 + 今日漏斗
3. **处理进度** - 处理队列卡片（待翻译/待转写）
4. **系统健康** - 系统健康 Hero 组件

## 成员清单

### 入口组件
**index.tsx**: Dashboard 主入口
- 职责: 编排所有子组件布局
- 导出: default AdminDashboard + 所有子组件
- 布局: 响应式网格，最大宽度 7xl

### 数据层
**hooks/useDashboardData.ts**: 数据获取 Hook
- 职责: 并行获取所有统计 API，管理刷新状态
- 导出: useDashboardData()
- 刷新间隔: 30 秒
- API: 8 个端点并行请求

### Hero 区域
**SystemHealthHero.tsx**: 系统健康指示器
- 职责: 三色状态灯 + 服务状态 + 数据源汇总
- Props: pipelineStatus, sourceHealth
- 样式: 呼吸动画 + 状态颜色映射

**PipelineStatusCard.tsx**: Pipeline 状态卡片
- 职责: 运行状态 + 下次运行倒计时 + 处理队列
- Props: pipelineStatus
- 特性: 实时倒计时更新（每秒）

### 漏斗区域
**CollectionFunnel.tsx**: 采集漏斗可视化
- 职责: 今日数据流转可视化
- Props: todayFunnel
- 展示: 抓取 → 规则过滤 → 去重 → LLM过滤 → 保存

### 指标卡片
**MetricCard.tsx**: 通用指标卡片
- 职责: 可复用的指标展示
- Props: icon, label, value, subValue, color
- 颜色: indigo/green/amber/blue/purple

**ProcessingQueueCard.tsx**: 处理队列卡片
- 职责: 待翻译/待转写数量展示
- Props: pipelineStatus

### 图表卡片
**StatusDistributionCard.tsx**: 状态分布卡片
- 职责: 资源状态进度条分布
- Props: overview

**DailyTrendChart.tsx**: 近 7 日趋势图表
- 职责: 柱状图展示采集趋势
- Props: daily stats array

### 质量监控卡片
**DataQualityCard.tsx**: 数据完整率卡片
- 职责: 播客/视频/文章完整率
- Props: dataQuality

**SourceHealthCard.tsx**: RSS 源健康卡片
- 职责: 数据源健康三色汇总 + 问题源列表
- Props: sourceHealth

**TranscriptionCard.tsx**: 转写成功率卡片
- 职责: 播客/视频转写进度
- Props: transcription

## 布局结构

```
┌─────────────────────────────────────────────────────────────────┐
│ 头部: 标题 + 刷新按钮                                             │
├────────────────────┬────────────────────────────────────────────┤
│ SystemHealthHero   │ PipelineStatusCard                         │
│ (1/3)              │ (2/3)                                      │
├────────────────────┴────────────────────────────────────────────┤
│ CollectionFunnel (全宽)                                          │
├──────────────┬──────────────┬──────────────┬──────────────────-─┤
│ MetricCard   │ MetricCard   │ MetricCard   │ MetricCard         │
│ 资源总数      │ 今日采集      │ 平均评分      │ 信号源数量          │
├──────────────┴──────────────┼──────────────┴──────────────────-─┤
│ StatusDistributionCard      │ DailyTrendChart                   │
│ (1/2)                       │ (1/2)                              │
├─────────────────────────────┼────────────────────┬───────────────┤
│ DataQualityCard             │ SourceHealthCard   │TranscriptionCard│
│ (1/3)                       │ (1/3)              │(1/3)           │
└─────────────────────────────┴────────────────────┴───────────────┘
```

## API 依赖
| 端点 | 用途 |
|------|------|
| /api/admin/stats/overview | 总览数据 |
| /api/admin/stats/pipeline-status | Pipeline 状态 |
| /api/admin/stats/today-funnel | 今日漏斗 |
| /api/admin/stats/daily | 近 7 日趋势 |
| /api/admin/stats/score-distribution | 评分分布 |
| /api/admin/stats/data-quality | 数据完整率 |
| /api/admin/stats/source-health | 数据源健康 |
| /api/admin/stats/transcription | 转写统计 |

## 设计规范

### 状态灯动画
- 健康: 绿色 + 呼吸动画 + 辉光阴影
- 降级: 黄色 + 呼吸动画 + 辉光阴影
- 异常: 红色 + 呼吸动画 + 辉光阴影

### 刷新机制
- 自动刷新: 30 秒间隔
- 手动刷新: 按钮 + loading 状态
- 显示: 最后刷新时间

### 响应式
- 桌面: 多列网格
- 平板: 2 列
- 移动端: 单列

[PROTOCOL]: 变更时更新此头部，然后检查 admin/CLAUDE.md
