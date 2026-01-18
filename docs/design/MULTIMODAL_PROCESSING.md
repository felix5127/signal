# Signal Hunter - 多模态处理技术方案

> 版本: 1.1 | 日期: 2026-01-17 | 状态: 设计中

---

## 目录

1. [概述](#1-概述)
2. [音频处理架构](#2-音频处理架构)
3. [视频处理架构](#3-视频处理架构)
4. [处理流程图](#4-处理流程图)
5. [API 设计](#5-api-设计)
6. [代码示例](#6-代码示例)
7. [配置与环境变量](#7-配置与环境变量)
8. [成本控制与优化](#8-成本控制与优化)

---

## 1. 概述

### 1.1 设计目标

Signal Hunter 研究助手需要处理多种媒体格式的源材料，本方案设计统一的多模态处理架构，支持：

- **音频处理**: 播客、语音备忘录、会议录音转写
- **视频处理**: YouTube 视频、技术演讲、在线课程的理解与搜索

### 1.2 技术选型

| 类型 | 服务 | 选型理由 |
|------|------|----------|
| **音频转写** | 听悟 API | 用户已有账号，中文优化 |
| **视频理解** | 通义千问 Omni (可选) | 百炼全模态模型，优先级低 |
| **音频切片** | FFmpeg + pydub | 工业标准，跨平台支持 |
| **视频下载** | yt-dlp | 支持 1000+ 平台，持续维护 |

> **注意**: 视频理解为可选功能，优先使用音频转写覆盖大部分场景。

### 1.3 核心原则

```
极简设计: 每个处理器只做一件事
渐进增强: 优先完成核心功能，逐步添加高级特性
成本可控: 分级处理策略，避免不必要的 API 调用
容错优先: 任何步骤失败不影响整体流程
```

---

## 2. 音频处理架构

### 2.1 听悟 API 集成方案

#### 为什么选择听悟

| 特性 | 听悟 API | OpenAI Whisper | Groq Whisper |
|------|----------|----------------|--------------|
| 速度 | 2x 实时 | 1x 实时 | 10x 实时 |
| 价格 | ~¥0.015/分钟 | $0.006/分钟 | $0.000111/分钟 |
| 延迟 | 约 10 分钟 | 约 3-5 分钟 | <30秒 |
| 语言 | **中文优化** | 多语言 | 多语言 |
| 文件限制 | 无限制 (URL) | 25MB | 25MB |
| 已有账号 | ✅ 用户已有 | ❌ | ❌ |

> **选型理由**: 用户已有听悟账号，且听悟对中文优化效果更好，支持 URL 直传无文件限制。

#### 听悟 API 接口

```python
# 听悟 API 规格
# Endpoint: https://tingwu.aliyuncs.com
# 支持异步任务模式，适合长音频处理
# 文档: https://help.aliyun.com/document_detail/China-Tingwu

# Step 1: 创建转写任务
POST /openapi/tingwu/v2/tasks
{
    "AppKey": "your-app-key",
    "Input": {
        "FileUrl": "https://example.com/audio.mp3",
        # 或 SourceLanguage + Format 指定
    },
    "Parameters": {
        "Transcription": {
            "DiarizationEnabled": true,  # 说话人分离
            "Diarization": {
                "SpeakerCount": 2  # 预估说话人数
            }
        },
        "TranscriptionOutputLevel": 2,  # 详细级别
        "AutoChaptersEnabled": true      # 自动章节
    }
}

# Response
{
    "Code": "0",
    "Data": {
        "TaskId": "task-xxxxxx",
        "TaskKey": "key-xxxxxx"
    }
}

# Step 2: 轮询任务状态
GET /openapi/tingwu/v2/tasks/{TaskId}

# Response (完成后)
{
    "Code": "0",
    "Data": {
        "TaskId": "task-xxxxxx",
        "TaskStatus": "COMPLETED",
        "Result": {
            "Transcription": {
                "Text": "完整转写文本...",
                "Paragraphs": [
                    {
                        "ParagraphId": "p1",
                        "StartTime": 0,
                        "EndTime": 5200,
                        "Text": "第一段文本",
                        "SpeakerId": "speaker1"
                    },
                    ...
                ]
            },
            "Chapters": [
                {
                    "ChapterId": "c1",
                    "Headline": "章节标题",
                    "Summary": "章节摘要"
                }
            ]
        }
    }
}
```

### 2.2 长音频预处理策略 (FFmpeg)

#### 预处理原理

听悟支持 URL 直传无文件限制，但预处理仍有助于提升转写质量：

1. **预处理**: 转换为单声道、16kHz 采样率（语音最佳）
2. **格式统一**: 确保音频格式兼容性
3. **音质优化**: 降噪、音量归一化
4. **上传存储**: 预处理后上传到 R2，生成 URL 供听悟调用

#### 分片算法

```
输入: 原始音频文件 (任意时长)
  ↓
Step 1: FFmpeg 预处理
  - 转换格式: mp3 (高压缩比)
  - 采样率: 16000 Hz (语音标准)
  - 声道: 单声道 (mono)
  - 码率: 64kbps (语音足够)
  ↓
Step 2: 计算分片
  - 目标大小: 20MB (留 5MB buffer)
  - 目标时长: ~20分钟/片 (64kbps 约 10MB/10min)
  - 实际分片: ceil(总时长 / 20分钟)
  ↓
Step 3: 静音检测分割
  - FFmpeg silencedetect 找静音点
  - 在静音点附近切割 (±2秒容忍)
  - 重叠 2 秒 (避免丢词)
  ↓
Step 4: 并发转写
  - asyncio.gather + Semaphore(3)
  - 每片独立调用 Groq API
  ↓
Step 5: 合并结果
  - 按片序号排序
  - 去除重叠部分
  - 时间戳偏移校正
  ↓
输出: 完整转写文本 + 时间戳
```

#### FFmpeg 命令参考

```bash
# 1. 获取音频信息
ffprobe -v quiet -print_format json -show_format -show_streams input.mp3

# 2. 预处理：转单声道、降采样、压缩
ffmpeg -i input.mp3 -ac 1 -ar 16000 -b:a 64k output.mp3

# 3. 静音检测
ffmpeg -i input.mp3 -af silencedetect=noise=-30dB:d=0.5 -f null -

# 4. 按时间分割 (每 20 分钟)
ffmpeg -i input.mp3 -f segment -segment_time 1200 -c copy output_%03d.mp3

# 5. 智能分割 (在静音点)
ffmpeg -i input.mp3 -af "silenceremove=stop_periods=-1:stop_duration=0.5:stop_threshold=-30dB" \
       -f segment -segment_time 1200 output_%03d.mp3
```

### 2.3 转写任务队列设计

#### 任务状态机

```
┌─────────┐
│ pending │ ← 新建任务
└────┬────┘
     │ 开始处理
     ▼
┌─────────────┐
│ downloading │ ← 下载原始音频
└──────┬──────┘
       │ 下载完成
       ▼
┌────────────┐
│ processing │ ← FFmpeg 预处理 + 分片
└──────┬─────┘
       │ 分片完成
       ▼
┌─────────────┐
│ transcribing│ ← 调用听悟 API (异步任务)
└──────┬──────┘
       │ 转写完成
       ▼
┌──────────┐
│ merging  │ ← 合并分片结果
└────┬─────┘
     │ 合并完成
     ▼
┌───────────┐     ┌────────┐
│ completed │     │ failed │
└───────────┘     └────────┘
```

#### 队列数据模型

```sql
CREATE TABLE audio_transcription_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES research_sources(id) ON DELETE CASCADE,

    -- 任务信息
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,

    -- 音频信息
    audio_url TEXT NOT NULL,
    audio_duration INTEGER,          -- 秒
    audio_size INTEGER,              -- 字节

    -- 分片信息
    total_chunks INTEGER DEFAULT 1,
    processed_chunks INTEGER DEFAULT 0,
    chunk_results JSONB DEFAULT '[]',

    -- 转写结果
    transcript_text TEXT,
    transcript_segments JSONB,
    language VARCHAR(10),

    -- 错误处理
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_audio_tasks_status ON audio_transcription_tasks(status);
CREATE INDEX idx_audio_tasks_priority ON audio_transcription_tasks(priority DESC, created_at ASC);
```

#### 队列处理器

```python
# 队列配置
AUDIO_QUEUE_CONFIG = {
    "max_concurrent": 3,           # 最大并发任务数
    "chunk_concurrent": 5,         # 每任务最大并发分片数
    "retry_delay": 60,             # 重试延迟（秒）
    "max_retries": 3,              # 最大重试次数
    "priority_weights": {
        "user_request": 10,        # 用户主动请求
        "research_task": 5,        # 研究任务触发
        "scheduled": 1,            # 定时任务
    }
}
```

---

## 3. 视频处理架构 (可选)

> ⚠️ **优先级说明**: 视频理解为可选功能，优先使用音频转写覆盖大部分场景。
> 大多数视频内容可通过提取音轨 + 听悟转写获取文本内容。

### 3.1 通义千问 Omni 集成方案 (可选)

#### 为什么选择通义千问 Omni

| 特性 | 通义千问 Omni | Twelve Labs | Google Video AI |
|------|--------------|-------------|-----------------|
| 语义理解 | 全模态原生 | 原生支持 | 需要额外 LLM |
| 视频搜索 | LLM 对话 | 自然语言查询 | 不支持 |
| 摘要生成 | LLM 生成 | 内置 | 不支持 |
| 价格 | 按 token 计费 | $0.05/分钟 | $0.10/分钟 |
| 已有账号 | ✅ 百炼平台 | ❌ | ❌ |

> **选型理由**: 通义千问 Omni 是百炼平台的全模态模型，支持视频输入，可复用现有账号。

#### 通义千问 Omni API 接口

```python
# 通义千问 Omni API 规格
# 平台: 阿里云百炼
# 模型: qwen-omni-turbo (全模态，支持视频/音频/图像输入)
# 文档: https://help.aliyun.com/document_detail/dashscope

# ========================================
# 1. 视频理解 (直接对话)
# ========================================
from dashscope import MultiModalConversation

# 视频内容理解
response = MultiModalConversation.call(
    model="qwen-omni-turbo",
    messages=[
        {
            "role": "user",
            "content": [
                {"video": "https://example.com/video.mp4"},
                {"text": "请总结这个视频的主要内容，提取关键技术点"}
            ]
        }
    ]
)

# Response
{
    "output": {
        "text": "这个视频主要讲解了 Transformer 架构..."
    },
    "usage": {
        "input_tokens": 1500,
        "output_tokens": 300
    }
}

# ========================================
# 2. 视频问答
# ========================================
response = MultiModalConversation.call(
    model="qwen-omni-turbo",
    messages=[
        {
            "role": "user",
            "content": [
                {"video": "https://example.com/video.mp4"},
                {"text": "视频中提到了哪些 AI 模型？"}
            ]
        }
    ]
)

# ========================================
# 3. 视频片段定位 (需要配合时间戳)
# ========================================
# 注意: 通义千问 Omni 不像 Twelve Labs 有原生的视频搜索功能
# 可通过 LLM 对话方式实现类似效果

response = MultiModalConversation.call(
    model="qwen-omni-turbo",
    messages=[
        {
            "role": "user",
            "content": [
                {"video": "https://example.com/video.mp4"},
                {"text": "请找出视频中讲解 attention 机制的时间段"}
            ]
        }
    ]
)

# ========================================
# 4. 章节生成
# ========================================
response = MultiModalConversation.call(
    model="qwen-omni-turbo",
    messages=[
        {
            "role": "user",
            "content": [
                {"video": "https://example.com/video.mp4"},
                {"text": "请为这个视频生成章节标题和摘要"}
            ]
        }
    ]
)
```

> **注意**: 通义千问 Omni 的视频理解是通过 LLM 对话实现，不像 Twelve Labs 有专门的视频索引和搜索功能。
> 对于需要精确视频搜索的场景，建议优先使用音频转写 + 文本向量搜索。

### 3.2 YouTube 下载方案 (yt-dlp)

#### yt-dlp 特性

```
支持平台: YouTube, Bilibili, Vimeo, Twitter, TikTok 等 1000+
格式选择: 自动选择最佳质量，支持指定格式
字幕下载: 自动提取字幕（如有）
元数据: 标题、描述、时长、缩略图等
Cookie 支持: 登录态访问限制内容
代理支持: 应对地区限制
```

#### 下载策略

```python
# 下载配置
YT_DLP_CONFIG = {
    # 格式选择（优先级从高到低）
    "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",

    # 输出模板
    "outtmpl": "%(id)s.%(ext)s",

    # 字幕
    "writesubtitles": True,
    "writeautomaticsub": True,
    "subtitleslangs": ["zh", "zh-Hans", "en"],
    "subtitlesformat": "vtt",

    # 元数据
    "writethumbnail": True,
    "writeinfojson": True,

    # 限制
    "max_filesize": 2 * 1024 * 1024 * 1024,  # 2GB
    "socket_timeout": 30,

    # 重试
    "retries": 3,
    "fragment_retries": 3,
}

# 平台特定配置
PLATFORM_CONFIGS = {
    "youtube": {
        "extract_flat": False,
        "age_limit": 18,
    },
    "bilibili": {
        "format": "bestvideo+bestaudio/best",
        "cookies_from_browser": "chrome",  # Bilibili 可能需要登录
    },
    "twitter": {
        "format": "best",
    }
}
```

#### 下载流程

```
输入: 视频 URL
  ↓
Step 1: URL 解析
  - 识别平台 (youtube/bilibili/twitter/...)
  - 提取视频 ID
  - 检查缓存（是否已下载）
  ↓
Step 2: 元数据获取
  - yt-dlp --dump-json
  - 获取：标题、时长、缩略图、字幕列表
  - 检查时长限制（默认 2 小时）
  ↓
Step 3: 下载决策
  - 时长 > 限制 → 仅下载音轨
  - 有字幕 → 跳过转写，直接用字幕
  - 无字幕 → 下载视频，后续转写
  ↓
Step 4: 执行下载
  - 下载视频/音频文件
  - 下载字幕（如有）
  - 下载缩略图
  - 保存元数据 JSON
  ↓
Step 5: 后处理
  - 上传到 Cloudflare R2
  - 清理本地临时文件
  - 更新数据库状态
  ↓
输出: 媒体文件 URL + 元数据
```

### 3.3 视频理解和搜索功能

#### 功能矩阵

| 功能 | 实现方式 | 输入 | 输出 |
|------|----------|------|------|
| **转写** | 听悟 API (提取音轨) | 视频文件 | 时间戳文本 |
| **摘要** | 通义千问 Omni (可选) | 视频 URL | 章节摘要 |
| **搜索** | 向量搜索 (转写文本) | 自然语言查询 | 片段列表 |
| **问答** | 通义千问 Omni (可选) | 问题文本 | 答案 |
| **字幕** | yt-dlp (如有) | 视频 URL | VTT/SRT |

> **推荐策略**: 优先使用音频转写 + 向量搜索，视频理解作为可选增强。

#### 处理流程

```
视频 URL 输入
     ↓
┌────────────────────────────────────┐
│ Step 1: yt-dlp 下载               │
│ - 元数据获取                       │
│ - 检查现有字幕                     │
│ - 下载视频/音频                    │
└──────────────┬─────────────────────┘
               │
     ┌─────────┴─────────┐
     │                   │
     ▼                   ▼
┌──────────┐      ┌──────────────┐
│ 有字幕   │      │ 无字幕       │
│          │      │              │
│ 直接使用 │      │ 听悟 API     │
│ VTT 字幕 │      │ 转写音轨     │
└────┬─────┘      └──────┬───────┘
     │                   │
     └─────────┬─────────┘
               │
               ▼
┌────────────────────────────────────┐
│ Step 2: 内容理解 (可选)           │
│ - 通义千问 Omni 视频分析          │
│ - 生成章节摘要                     │
│ - 提取关键信息                     │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│ Step 3: 向量化与存储               │
│ - 转写文本向量化 (百炼嵌入)       │
│ - 构建文本搜索索引                 │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│ Step 4: 存储与服务                 │
│ - 视频文件 → R2                   │
│ - 转写文本 → PostgreSQL           │
│ - 向量索引 → PostgreSQL pgvector  │
│ - API 暴露搜索/问答接口           │
└────────────────────────────────────┘
```

---

## 4. 处理流程图

### 4.1 多模态处理总体架构

```
                                    ┌──────────────────┐
                                    │   用户/研究任务   │
                                    └────────┬─────────┘
                                             │
                              ┌──────────────┼──────────────┐
                              │              │              │
                              ▼              ▼              ▼
                      ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
                      │   音频源    │ │   视频源    │ │  文本/URL   │
                      │ (播客/录音) │ │ (YouTube等) │ │  (现有流程) │
                      └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
                             │               │               │
                             ▼               ▼               │
                      ┌─────────────────────────────────┐    │
                      │      多模态处理调度器            │    │
                      │      MultimodalDispatcher       │    │
                      └───────────────┬─────────────────┘    │
                                      │                      │
                    ┌─────────────────┼─────────────────┐    │
                    │                 │                 │    │
                    ▼                 ▼                 │    │
          ┌─────────────────┐ ┌─────────────────┐      │    │
          │   音频处理器    │ │   视频处理器    │      │    │
          │ AudioProcessor  │ │ VideoProcessor  │      │    │
          │                 │ │                 │      │    │
          │ - FFmpeg 预处理 │ │ - yt-dlp 下载   │      │    │
          │ - 听悟转写      │ │ - 通义千问 Omni │      │    │
          │ - 结果处理      │ │ - 向量索引      │      │    │
          └────────┬────────┘ └────────┬────────┘      │    │
                   │                   │               │    │
                   └─────────┬─────────┘               │    │
                             │                         │    │
                             ▼                         ▼    ▼
                   ┌───────────────────────────────────────────┐
                   │              统一内容存储                  │
                   │                                           │
                   │  ┌─────────────┐  ┌─────────────────────┐ │
                   │  │ PostgreSQL  │  │   Cloudflare R2     │ │
                   │  │             │  │                     │ │
                   │  │ - 元数据    │  │ - 原始媒体文件      │ │
                   │  │ - 转写文本  │  │ - 处理后的切片      │ │
                   │  │ - 向量索引  │  │ - 缩略图            │ │
                   │  └─────────────┘  └─────────────────────┘ │
                   └───────────────────────────────────────────┘
                                       │
                                       ▼
                   ┌───────────────────────────────────────────┐
                   │              下游消费者                    │
                   │                                           │
                   │  - Research Agent: RAG 检索转写内容       │
                   │  - Chat Service: 基于视频内容对话         │
                   │  - Search API: 视频语义搜索               │
                   │  - Podcast Generator: TTS 播放            │
                   └───────────────────────────────────────────┘
```

### 4.2 音频处理详细流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                         音频处理流水线                               │
│                         AudioPipeline                               │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 1: 输入验证                                                    │
│                                                                     │
│ if url.is_audio():          # mp3, wav, m4a, flac, ogg             │
│     audio_url = url                                                 │
│ elif url.is_video():        # mp4, webm                            │
│     audio_url = extract_audio(url)  # FFmpeg -vn                   │
│ else:                                                               │
│     raise UnsupportedFormatError                                    │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 2: 下载与预处理                                                │
│                                                                     │
│ # 下载                                                              │
│ local_path = download_to_temp(audio_url)                           │
│                                                                     │
│ # 获取音频信息                                                      │
│ info = ffprobe(local_path)  # duration, bitrate, sample_rate       │
│                                                                     │
│ # 预处理（统一格式）                                                │
│ processed = ffmpeg(                                                 │
│     input=local_path,                                               │
│     ac=1,              # 单声道                                     │
│     ar=16000,          # 16kHz                                     │
│     format='mp3',                                                   │
│     bitrate='64k'                                                   │
│ )                                                                   │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 3: 分片决策                                                    │
│                                                                     │
│ file_size = os.path.getsize(processed)                             │
│                                                                     │
│ if file_size <= 20 * 1024 * 1024:   # <= 20MB                      │
│     chunks = [processed]             # 单片处理                     │
│ else:                                                               │
│     # 静音检测                                                      │
│     silences = detect_silence(processed)                           │
│                                                                     │
│     # 计算分片点（在静音点附近）                                    │
│     split_points = calculate_split_points(                         │
│         duration=info.duration,                                     │
│         target_chunk_duration=20*60,  # 20分钟                     │
│         silences=silences,                                          │
│         overlap=2  # 2秒重叠                                       │
│     )                                                               │
│                                                                     │
│     # 执行分割                                                      │
│     chunks = split_audio(processed, split_points)                  │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 4: 听悟转写                                                    │
│                                                                     │
│ async def transcribe_audio(audio_url: str):                        │
│     # Step 1: 创建听悟任务                                          │
│     task = await tingwu_client.create_task(                        │
│         file_url=audio_url,                                         │
│         diarization_enabled=True,  # 说话人分离                     │
│         auto_chapters_enabled=True  # 自动章节                      │
│     )                                                               │
│                                                                     │
│     # Step 2: 轮询等待完成                                          │
│     while task.status != "COMPLETED":                              │
│         await asyncio.sleep(10)                                     │
│         task = await tingwu_client.get_task(task.task_id)          │
│                                                                     │
│     # Step 3: 获取结果                                              │
│     return {                                                        │
│         "text": task.result.transcription.text,                    │
│         "paragraphs": task.result.transcription.paragraphs,        │
│         "chapters": task.result.chapters                           │
│     }                                                               │
│                                                                     │
│ # 听悟支持长音频直传，无需分片                                      │
│ result = await transcribe_audio(audio_url)                                                                  │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 5: 结果合并                                                    │
│                                                                     │
│ def merge_transcripts(results, overlap_seconds=2):                 │
│     # 按 index 排序                                                 │
│     results.sort(key=lambda x: x["index"])                         │
│                                                                     │
│     full_text = ""                                                  │
│     all_segments = []                                               │
│     time_offset = 0                                                 │
│                                                                     │
│     for i, result in enumerate(results):                           │
│         # 跳过重叠部分（首片除外）                                  │
│         if i > 0:                                                   │
│             skip_until = overlap_seconds                            │
│             segments = [s for s in result["segments"]              │
│                        if s["start"] >= skip_until]                │
│         else:                                                       │
│             segments = result["segments"]                           │
│                                                                     │
│         # 调整时间戳                                                │
│         for seg in segments:                                        │
│             seg["start"] += time_offset                             │
│             seg["end"] += time_offset                               │
│             all_segments.append(seg)                                │
│             full_text += seg["text"] + " "                          │
│                                                                     │
│         # 更新偏移（减去重叠）                                      │
│         time_offset += result["duration"] - overlap_seconds        │
│                                                                     │
│     return {                                                        │
│         "text": full_text.strip(),                                  │
│         "segments": all_segments,                                   │
│         "duration": time_offset                                     │
│     }                                                               │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 6: 存储与输出                                                  │
│                                                                     │
│ # 存储到数据库                                                      │
│ source.full_text = transcript["text"]                              │
│ source.metadata["segments"] = transcript["segments"]               │
│ source.metadata["duration"] = transcript["duration"]               │
│ source.metadata["language"] = detected_language                    │
│ source.processing_status = "completed"                             │
│                                                                     │
│ # 生成向量嵌入（用于 RAG 检索）                                     │
│ chunks = split_text_for_embedding(transcript["text"])              │
│ embeddings = await embed_chunks(chunks)                            │
│ await save_embeddings(source.id, chunks, embeddings)               │
│                                                                     │
│ # 清理临时文件                                                      │
│ cleanup_temp_files([local_path, processed, *chunks])               │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 视频处理详细流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                         视频处理流水线                               │
│                         VideoPipeline                               │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 1: URL 解析与元数据获取                                        │
│                                                                     │
│ # 解析平台和视频 ID                                                 │
│ platform, video_id = parse_video_url(url)                          │
│                                                                     │
│ # 获取元数据（不下载）                                              │
│ metadata = yt_dlp.extract_info(url, download=False)                │
│                                                                     │
│ video_info = {                                                      │
│     "title": metadata["title"],                                     │
│     "duration": metadata["duration"],                               │
│     "thumbnail": metadata["thumbnail"],                             │
│     "description": metadata["description"],                         │
│     "subtitles": list(metadata.get("subtitles", {}).keys()),       │
│     "automatic_captions": list(metadata.get("automatic_captions",  │
│                                              {}).keys()),           │
│ }                                                                   │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 2: 处理策略决策                                                │
│                                                                     │
│ # 检查时长限制                                                      │
│ if video_info["duration"] > MAX_DURATION:                          │
│     raise VideoTooLongError(f"视频超过 {MAX_DURATION/3600} 小时")  │
│                                                                     │
│ # 决定处理策略                                                      │
│ strategy = {                                                        │
│     "download_video": True,                                         │
│     "use_existing_subtitles": False,                                │
│     "need_transcription": True,                                     │
│     "index_to_twelve_labs": True,                                   │
│ }                                                                   │
│                                                                     │
│ # 如果有字幕，跳过转写                                              │
│ preferred_langs = ["zh", "zh-Hans", "en"]                          │
│ if any(lang in video_info["subtitles"] for lang in preferred_langs):│
│     strategy["use_existing_subtitles"] = True                       │
│     strategy["need_transcription"] = False                          │
│ elif any(lang in video_info["automatic_captions"]                  │
│          for lang in preferred_langs):                              │
│     strategy["use_existing_subtitles"] = True                       │
│     strategy["need_transcription"] = False                          │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 3: 下载执行                                                    │
│                                                                     │
│ yt_dlp_opts = {                                                     │
│     "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",│
│     "outtmpl": f"{TEMP_DIR}/{video_id}.%(ext)s",                   │
│     "writesubtitles": strategy["use_existing_subtitles"],          │
│     "writeautomaticsub": strategy["use_existing_subtitles"],       │
│     "subtitleslangs": preferred_langs,                              │
│     "writethumbnail": True,                                         │
│     "postprocessors": [                                             │
│         {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},  │
│     ],                                                              │
│ }                                                                   │
│                                                                     │
│ result = yt_dlp.download(url, yt_dlp_opts)                         │
│                                                                     │
│ downloaded_files = {                                                │
│     "video": f"{TEMP_DIR}/{video_id}.mp4",                         │
│     "subtitle": f"{TEMP_DIR}/{video_id}.vtt" if subtitle else None,│
│     "thumbnail": f"{TEMP_DIR}/{video_id}.jpg",                     │
│ }                                                                   │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 4: 内容转写                                                    │
│                                                                     │
│ if strategy["use_existing_subtitles"]:                             │
│     # 解析字幕文件                                                  │
│     transcript = parse_vtt_subtitle(downloaded_files["subtitle"])  │
│                                                                     │
│ else:                                                               │
│     # 提取音轨                                                      │
│     audio_path = extract_audio(downloaded_files["video"])          │
│                                                                     │
│     # 上传到 R2 获取 URL                                            │
│     audio_url = await r2.upload(audio_path, key=f"audio/{video_id}.mp3") │
│                                                                     │
│     # 使用听悟转写                                                  │
│     transcript = await tingwu_client.transcribe(audio_url)          │
│                                                                     │
│ # transcript 格式:                                                  │
│ # {                                                                 │
│ #     "text": "完整文本...",                                        │
│ #     "segments": [                                                 │
│ #         {"start": 0.0, "end": 5.2, "text": "第一段"},            │
│ #         ...                                                       │
│ #     ]                                                             │
│ # }                                                                 │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 5: 视频理解 (可选，使用通义千问 Omni)                         │
│                                                                     │
│ if strategy["use_video_understanding"]:                            │
│     # 使用通义千问 Omni 进行视频理解                               │
│     from dashscope import MultiModalConversation                   │
│                                                                     │
│     # 生成章节摘要                                                  │
│     response = await MultiModalConversation.call(                  │
│         model="qwen-omni-turbo",                                    │
│         messages=[{                                                 │
│             "role": "user",                                         │
│             "content": [                                            │
│                 {"video": video_r2_url},                           │
│                 {"text": "请为这个视频生成章节标题和摘要"}         │
│             ]                                                       │
│         }]                                                          │
│     )                                                               │
│                                                                     │
│     summary = parse_qwen_response(response)                        │
│ else:                                                               │
│     # 跳过视频理解，仅使用转写文本                                 │
│     summary = None                                                               │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 6: 存储与输出                                                  │
│                                                                     │
│ # 上传媒体文件到 R2                                                 │
│ video_r2_url = await r2.upload(                                    │
│     downloaded_files["video"],                                      │
│     key=f"videos/{video_id}.mp4"                                   │
│ )                                                                   │
│ thumbnail_r2_url = await r2.upload(                                │
│     downloaded_files["thumbnail"],                                  │
│     key=f"thumbnails/{video_id}.jpg"                               │
│ )                                                                   │
│                                                                     │
│ # 存储到数据库                                                      │
│ source = ResearchSource(                                            │
│     source_type="video",                                            │
│     title=video_info["title"],                                      │
│     original_url=url,                                               │
│     file_path=video_r2_url,                                        │
│     full_text=transcript["text"],                                  │
│     metadata={                                                      │
│         "platform": platform,                                       │
│         "video_id": video_id,                                       │
│         "duration": video_info["duration"],                        │
│         "thumbnail_url": thumbnail_r2_url,                         │
│         "segments": transcript.get("paragraphs", []),              │
│         "chapters": summary if summary else None,                  │
│     },                                                              │
│     processing_status="completed",                                  │
│ )                                                                   │
│                                                                     │
│ # 生成向量嵌入                                                      │
│ await embed_and_save(source)                                       │
│                                                                     │
│ # 清理                                                              │
│ cleanup_temp_files(downloaded_files.values())                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. API 设计

### 5.1 音频处理 API

```python
# ========================================
# 音频转写 API
# ========================================

# POST /api/audio/transcribe
# 提交音频转写任务
"""
Request:
{
    "source_id": "uuid",            # 关联的 research_source ID
    "audio_url": "https://...",     # 音频 URL
    "language": "zh",               # 可选，语言提示
    "priority": 5                   # 可选，优先级 (1-10)
}

Response:
{
    "task_id": "uuid",
    "status": "pending",
    "estimated_duration": 120       # 预估处理时间（秒）
}
"""

# GET /api/audio/transcribe/{task_id}
# 查询转写任务状态
"""
Response:
{
    "task_id": "uuid",
    "status": "transcribing",       # pending/processing/transcribing/completed/failed
    "progress": 0.65,               # 0.0 - 1.0
    "processed_chunks": 3,
    "total_chunks": 5,
    "result": null                  # 完成后填充
}
"""

# GET /api/audio/transcribe/{task_id}/result
# 获取转写结果
"""
Response:
{
    "task_id": "uuid",
    "status": "completed",
    "result": {
        "text": "完整转写文本...",
        "language": "zh",
        "duration": 3600,
        "segments": [
            {"start": 0.0, "end": 5.2, "text": "第一段"},
            ...
        ]
    }
}
"""

# POST /api/audio/transcribe/{task_id}/cancel
# 取消转写任务
"""
Response:
{
    "task_id": "uuid",
    "status": "cancelled"
}
"""
```

### 5.2 视频处理 API

```python
# ========================================
# 视频处理 API
# ========================================

# POST /api/video/process
# 提交视频处理任务
"""
Request:
{
    "source_id": "uuid",            # 关联的 research_source ID
    "video_url": "https://youtube.com/watch?v=xxx",
    "options": {
        "transcribe": true,         # 是否转写
        "use_video_understanding": true,  # 是否启用视频理解 (通义千问 Omni，可选)
        "generate_summary": true,   # 是否生成摘要
        "max_duration": 7200        # 最大时长限制（秒）
    }
}

Response:
{
    "task_id": "uuid",
    "status": "pending",
    "video_info": {
        "title": "视频标题",
        "duration": 1800,
        "thumbnail": "https://..."
    }
}
"""

# GET /api/video/process/{task_id}
# 查询视频处理状态
"""
Response:
{
    "task_id": "uuid",
    "status": "indexing",           # pending/downloading/transcribing/indexing/completed/failed
    "progress": 0.8,
    "steps": {
        "download": "completed",
        "transcribe": "completed",
        "index": "in_progress",
        "summarize": "pending"
    }
}
"""

# POST /api/video/search
# 视频语义搜索 (基于通义千问 Omni，可选功能)
"""
Request:
{
    "query": "讲解 attention 机制的部分",
    "video_ids": ["uuid1", "uuid2"],  # 可选，限定搜索范围
    "threshold": "medium",          # low/medium/high
    "limit": 10
}

Response:
{
    "results": [
        {
            "video_id": "uuid",
            "video_title": "Transformer 详解",
            "score": 0.92,
            "start": 120.5,
            "end": 180.2,
            "text": "现在我们来看 attention 机制...",
            "thumbnail_url": "https://..."
        },
        ...
    ]
}
"""

# POST /api/video/{video_id}/ask
# 视频问答 (基于通义千问 Omni，可选功能)
"""
Request:
{
    "question": "这个视频主要讲了什么内容？"
}

Response:
{
    "answer": "这个视频主要讲解了 Transformer 架构...",
    "citations": [
        {"start": 0.0, "end": 30.0, "text": "今天我们来学习 Transformer..."},
        {"start": 120.5, "end": 150.0, "text": "Transformer 的核心是..."}
    ]
}
"""

# GET /api/video/{video_id}/chapters
# 获取视频章节摘要
"""
Response:
{
    "video_id": "uuid",
    "title": "Transformer 详解",
    "duration": 1800,
    "chapters": [
        {
            "start": 0,
            "end": 120,
            "title": "介绍",
            "summary": "本节介绍了 Transformer 的背景..."
        },
        {
            "start": 120,
            "end": 600,
            "title": "Self-Attention 机制",
            "summary": "详细讲解了 Self-Attention 的计算过程..."
        },
        ...
    ]
}
"""
```

### 5.3 统一多模态 API

```python
# ========================================
# 统一多模态处理 API
# ========================================

# POST /api/sources/upload
# 上传/添加源材料（自动识别类型）
"""
Request (multipart/form-data):
{
    "project_id": "uuid",
    "file": <binary>,               # 文件上传
    # 或
    "url": "https://...",           # URL 导入
    "title": "可选标题"
}

Response:
{
    "source_id": "uuid",
    "source_type": "video",         # url/pdf/audio/video/text
    "title": "自动识别的标题",
    "processing_task_id": "uuid",   # 异步处理任务 ID
    "status": "processing"
}
"""

# GET /api/sources/{source_id}/status
# 查询源材料处理状态
"""
Response:
{
    "source_id": "uuid",
    "source_type": "video",
    "status": "completed",          # pending/processing/completed/failed
    "processing_steps": {
        "download": {"status": "completed", "duration": 30},
        "transcribe": {"status": "completed", "duration": 120},
        "embed": {"status": "completed", "duration": 5}
    },
    "result": {
        "title": "视频标题",
        "duration": 1800,
        "word_count": 15000,
        "language": "zh"
    }
}
"""
```

---

## 6. 代码示例

### 6.1 听悟客户端

```python
"""
[INPUT]: 依赖 httpx，asyncio，阿里云 SDK
[OUTPUT]: 对外提供 TingwuClient 类
[POS]: processors/audio 的转写引擎，被 AudioProcessor 调用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import asyncio
import os
import hmac
import hashlib
import base64
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import httpx


@dataclass
class TranscriptParagraph:
    """转写段落"""
    paragraph_id: str
    start_time: int       # 毫秒
    end_time: int         # 毫秒
    text: str
    speaker_id: Optional[str] = None


@dataclass
class TranscriptChapter:
    """自动章节"""
    chapter_id: str
    headline: str
    summary: str


@dataclass
class TranscriptResult:
    """转写结果"""
    task_id: str
    text: str
    paragraphs: List[TranscriptParagraph]
    chapters: List[TranscriptChapter]


class TingwuClient:
    """
    听悟 API 客户端

    特性：
    - 异步任务模式
    - 支持 URL 直传 (无文件大小限制)
    - 说话人分离
    - 自动章节生成
    """

    # ============================================================
    # 配置
    # ============================================================

    BASE_URL = "https://tingwu.aliyuncs.com"
    API_VERSION = "v2"

    def __init__(
        self,
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        app_key: Optional[str] = None,
    ):
        self.access_key_id = access_key_id or os.getenv("TINGWU_ACCESS_KEY_ID")
        self.access_key_secret = access_key_secret or os.getenv("TINGWU_ACCESS_KEY_SECRET")
        self.app_key = app_key or os.getenv("TINGWU_APP_KEY")

        if not all([self.access_key_id, self.access_key_secret, self.app_key]):
            raise ValueError("听悟 API 凭证不完整")

        self.client = httpx.AsyncClient(base_url=self.BASE_URL, timeout=60.0)

    # ============================================================
    # 公开方法
    # ============================================================

    async def create_task(
        self,
        file_url: str,
        diarization_enabled: bool = True,
        speaker_count: int = 2,
        auto_chapters_enabled: bool = True,
    ) -> str:
        """
        创建转写任务

        Args:
            file_url: 音频文件 URL
            diarization_enabled: 是否启用说话人分离
            speaker_count: 预估说话人数
            auto_chapters_enabled: 是否自动生成章节

        Returns:
            task_id: 任务 ID
        """
        payload = {
            "AppKey": self.app_key,
            "Input": {
                "FileUrl": file_url,
            },
            "Parameters": {
                "Transcription": {
                    "DiarizationEnabled": diarization_enabled,
                    "Diarization": {
                        "SpeakerCount": speaker_count
                    }
                },
                "TranscriptionOutputLevel": 2,
                "AutoChaptersEnabled": auto_chapters_enabled,
            }
        }

        headers = self._sign_request("POST", f"/openapi/tingwu/{self.API_VERSION}/tasks")

        resp = await self.client.post(
            f"/openapi/tingwu/{self.API_VERSION}/tasks",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("Code") != "0":
            raise RuntimeError(f"创建任务失败: {data}")

        return data["Data"]["TaskId"]

    async def get_task(self, task_id: str) -> dict:
        """
        查询任务状态
        """
        headers = self._sign_request("GET", f"/openapi/tingwu/{self.API_VERSION}/tasks/{task_id}")

        resp = await self.client.get(
            f"/openapi/tingwu/{self.API_VERSION}/tasks/{task_id}",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()["Data"]

    async def wait_for_completion(
        self,
        task_id: str,
        poll_interval: int = 10,
        max_wait: int = 3600,
    ) -> TranscriptResult:
        """
        等待任务完成并返回结果
        """
        elapsed = 0
        while elapsed < max_wait:
            task = await self.get_task(task_id)
            status = task.get("TaskStatus")

            if status == "COMPLETED":
                return self._parse_result(task)
            elif status == "FAILED":
                raise RuntimeError(f"转写任务失败: {task.get('ErrorMessage')}")

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"任务超时: {task_id}")

    async def transcribe(
        self,
        file_url: str,
        **kwargs,
    ) -> TranscriptResult:
        """
        转写音频 (创建任务并等待完成)
        """
        task_id = await self.create_task(file_url, **kwargs)
        return await self.wait_for_completion(task_id)

    # ============================================================
    # 私有方法
    # ============================================================

    def _sign_request(self, method: str, path: str) -> dict:
        """生成签名请求头"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        nonce = os.urandom(8).hex()

        string_to_sign = f"{method}\n{path}\n{timestamp}\n{nonce}"
        signature = base64.b64encode(
            hmac.new(
                self.access_key_secret.encode(),
                string_to_sign.encode(),
                hashlib.sha256
            ).digest()
        ).decode()

        return {
            "x-acs-accesskey-id": self.access_key_id,
            "x-acs-timestamp": timestamp,
            "x-acs-signature-nonce": nonce,
            "x-acs-signature": signature,
            "Content-Type": "application/json",
        }

    def _parse_result(self, task: dict) -> TranscriptResult:
        """解析转写结果"""
        result = task.get("Result", {})
        transcription = result.get("Transcription", {})

        paragraphs = [
            TranscriptParagraph(
                paragraph_id=p.get("ParagraphId", ""),
                start_time=p.get("StartTime", 0),
                end_time=p.get("EndTime", 0),
                text=p.get("Text", ""),
                speaker_id=p.get("SpeakerId"),
            )
            for p in transcription.get("Paragraphs", [])
        ]

        chapters = [
            TranscriptChapter(
                chapter_id=c.get("ChapterId", ""),
                headline=c.get("Headline", ""),
                summary=c.get("Summary", ""),
            )
            for c in result.get("Chapters", [])
        ]

        return TranscriptResult(
            task_id=task.get("TaskId", ""),
            text=transcription.get("Text", ""),
            paragraphs=paragraphs,
            chapters=chapters,
        )

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
```

### 6.2 FFmpeg 音频处理器

```python
"""
[INPUT]: 依赖 ffmpeg-python，subprocess，tempfile
[OUTPUT]: 对外提供 AudioPreprocessor 类
[POS]: processors/audio 的预处理引擎，被 AudioPipeline 调用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import asyncio
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class AudioInfo:
    """音频信息"""
    duration: float        # 秒
    sample_rate: int       # Hz
    channels: int
    bitrate: int           # bps
    format: str
    file_size: int         # bytes


@dataclass
class SilenceSegment:
    """静音片段"""
    start: float
    end: float
    duration: float


class AudioPreprocessor:
    """
    FFmpeg 音频预处理器

    功能：
    - 格式转换
    - 采样率调整
    - 静音检测
    - 智能分片
    """

    # ============================================================
    # 配置
    # ============================================================

    # 预处理配置
    TARGET_SAMPLE_RATE = 16000  # 16kHz (语音标准)
    TARGET_CHANNELS = 1         # 单声道
    TARGET_BITRATE = "64k"      # 64kbps
    TARGET_FORMAT = "mp3"

    # 分片配置
    MAX_CHUNK_SIZE = 20 * 1024 * 1024  # 20MB
    TARGET_CHUNK_DURATION = 20 * 60    # 20分钟
    CHUNK_OVERLAP = 2                  # 2秒重叠

    # 静音检测配置
    SILENCE_THRESHOLD = "-30dB"
    SILENCE_MIN_DURATION = 0.5  # 秒

    # ============================================================
    # 公开方法
    # ============================================================

    async def get_audio_info(self, file_path: str) -> AudioInfo:
        """
        获取音频信息
        """
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path,
        ]

        result = await self._run_command(cmd)
        data = json.loads(result)

        # 获取音频流信息
        audio_stream = next(
            (s for s in data.get("streams", []) if s["codec_type"] == "audio"),
            {}
        )
        format_info = data.get("format", {})

        return AudioInfo(
            duration=float(format_info.get("duration", 0)),
            sample_rate=int(audio_stream.get("sample_rate", 0)),
            channels=int(audio_stream.get("channels", 0)),
            bitrate=int(format_info.get("bit_rate", 0)),
            format=format_info.get("format_name", ""),
            file_size=int(format_info.get("size", 0)),
        )

    async def preprocess(
        self,
        input_path: str,
        output_path: Optional[str] = None,
    ) -> str:
        """
        预处理音频：转单声道、降采样、压缩

        Returns:
            输出文件路径
        """
        if output_path is None:
            output_path = tempfile.mktemp(suffix=f".{self.TARGET_FORMAT}")

        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-ac", str(self.TARGET_CHANNELS),
            "-ar", str(self.TARGET_SAMPLE_RATE),
            "-b:a", self.TARGET_BITRATE,
            "-y",  # 覆盖输出
            output_path,
        ]

        await self._run_command(cmd)
        return output_path

    async def detect_silence(self, file_path: str) -> List[SilenceSegment]:
        """
        检测静音片段
        """
        cmd = [
            "ffmpeg",
            "-i", file_path,
            "-af", f"silencedetect=noise={self.SILENCE_THRESHOLD}:d={self.SILENCE_MIN_DURATION}",
            "-f", "null",
            "-",
        ]

        # silencedetect 输出到 stderr
        result = await self._run_command(cmd, capture_stderr=True)

        # 解析输出
        silences = []
        lines = result.split("\n")

        current_start = None
        for line in lines:
            if "silence_start:" in line:
                current_start = float(line.split("silence_start:")[1].strip())
            elif "silence_end:" in line and current_start is not None:
                parts = line.split("|")
                end = float(parts[0].split("silence_end:")[1].strip())
                duration = float(parts[1].split("silence_duration:")[1].strip())
                silences.append(SilenceSegment(
                    start=current_start,
                    end=end,
                    duration=duration,
                ))
                current_start = None

        return silences

    async def split_audio(
        self,
        file_path: str,
        output_dir: Optional[str] = None,
    ) -> List[Tuple[str, float, float]]:
        """
        智能分片音频

        Returns:
            List[(chunk_path, start_time, end_time)]
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()

        # 获取音频信息
        info = await self.get_audio_info(file_path)

        # 如果文件够小，不需要分片
        if info.file_size <= self.MAX_CHUNK_SIZE:
            return [(file_path, 0, info.duration)]

        # 检测静音点
        silences = await self.detect_silence(file_path)

        # 计算分片点
        split_points = self._calculate_split_points(
            duration=info.duration,
            silences=silences,
        )

        # 执行分割
        chunks = []
        for i, (start, end) in enumerate(split_points):
            output_path = os.path.join(output_dir, f"chunk_{i:03d}.{self.TARGET_FORMAT}")

            # 添加重叠
            actual_start = max(0, start - self.CHUNK_OVERLAP) if i > 0 else start
            actual_end = min(info.duration, end + self.CHUNK_OVERLAP)

            cmd = [
                "ffmpeg",
                "-i", file_path,
                "-ss", str(actual_start),
                "-to", str(actual_end),
                "-c", "copy",
                "-y",
                output_path,
            ]

            await self._run_command(cmd)
            chunks.append((output_path, actual_start, actual_end))

        return chunks

    async def extract_audio_from_video(
        self,
        video_path: str,
        output_path: Optional[str] = None,
    ) -> str:
        """
        从视频提取音轨
        """
        if output_path is None:
            output_path = tempfile.mktemp(suffix=f".{self.TARGET_FORMAT}")

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",  # 无视频
            "-ac", str(self.TARGET_CHANNELS),
            "-ar", str(self.TARGET_SAMPLE_RATE),
            "-b:a", self.TARGET_BITRATE,
            "-y",
            output_path,
        ]

        await self._run_command(cmd)
        return output_path

    # ============================================================
    # 私有方法
    # ============================================================

    def _calculate_split_points(
        self,
        duration: float,
        silences: List[SilenceSegment],
    ) -> List[Tuple[float, float]]:
        """
        计算分片点（在静音点附近）
        """
        target_duration = self.TARGET_CHUNK_DURATION
        points = []
        current_start = 0.0

        while current_start < duration:
            target_end = current_start + target_duration

            if target_end >= duration:
                # 最后一片
                points.append((current_start, duration))
                break

            # 在 target_end 附近找静音点
            best_silence = None
            min_distance = float("inf")

            for silence in silences:
                # 在目标点 ±30秒 范围内找静音
                if abs(silence.start - target_end) < 30:
                    distance = abs(silence.start - target_end)
                    if distance < min_distance:
                        min_distance = distance
                        best_silence = silence

            if best_silence:
                # 在静音中点分割
                split_point = best_silence.start + best_silence.duration / 2
            else:
                # 没有合适的静音点，直接在目标点分割
                split_point = target_end

            points.append((current_start, split_point))
            current_start = split_point

        return points

    async def _run_command(
        self,
        cmd: List[str],
        capture_stderr: bool = False,
    ) -> str:
        """
        运行命令
        """
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"命令失败: {stderr.decode()}")

        if capture_stderr:
            return stderr.decode()
        return stdout.decode()
```

### 6.3 通义千问 Omni 视频处理器 (可选)

```python
"""
[INPUT]: 依赖 dashscope SDK，asyncio
[OUTPUT]: 对外提供 QwenOmniClient 类
[POS]: processors/video 的视频理解引擎 (可选)，被 VideoProcessor 调用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from dashscope import MultiModalConversation


@dataclass
class VideoChapter:
    """视频章节"""
    title: str
    summary: str


@dataclass
class VideoAnalysis:
    """视频分析结果"""
    summary: str
    chapters: List[VideoChapter]
    key_points: List[str]


class QwenOmniClient:
    """
    通义千问 Omni 客户端

    功能：
    - 视频内容理解
    - 视频摘要生成
    - 视频问答
    - 章节提取

    注意：此为可选功能，优先使用音频转写覆盖大部分场景
    """

    # ============================================================
    # 配置
    # ============================================================

    MODEL = "qwen-omni-turbo"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY is required")

    # ============================================================
    # 公开方法
    # ============================================================

    async def analyze_video(
        self,
        video_url: str,
        prompt: str = "请总结这个视频的主要内容，提取关键技术点",
    ) -> str:
        """
        分析视频内容

        Args:
            video_url: 视频 URL
            prompt: 分析提示词

        Returns:
            分析结果文本
        """
        response = MultiModalConversation.call(
            model=self.MODEL,
            api_key=self.api_key,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"video": video_url},
                        {"text": prompt}
                    ]
                }
            ]
        )

        if response.status_code != 200:
            raise RuntimeError(f"视频分析失败: {response.message}")

        return response.output.text

    async def generate_chapters(
        self,
        video_url: str,
    ) -> List[VideoChapter]:
        """
        生成视频章节

        Args:
            video_url: 视频 URL

        Returns:
            章节列表
        """
        prompt = """请为这个视频生成章节标题和摘要，返回 JSON 格式：
[
    {"title": "章节标题", "summary": "章节摘要"},
    ...
]"""

        response = await self.analyze_video(video_url, prompt)

        # 解析 JSON 响应
        import json
        try:
            chapters_data = json.loads(response)
            return [
                VideoChapter(title=ch["title"], summary=ch["summary"])
                for ch in chapters_data
            ]
        except (json.JSONDecodeError, KeyError):
            # 如果无法解析，返回空列表
            return []

    async def ask(
        self,
        video_url: str,
        question: str,
    ) -> str:
        """
        视频问答

        Args:
            video_url: 视频 URL
            question: 问题文本

        Returns:
            答案文本
        """
        return await self.analyze_video(video_url, question)

    async def extract_key_points(
        self,
        video_url: str,
    ) -> List[str]:
        """
        提取关键信息点

        Args:
            video_url: 视频 URL

        Returns:
            关键信息列表
        """
        prompt = "请列出这个视频的关键信息点，每行一个，使用数字编号"
        response = await self.analyze_video(video_url, prompt)

        # 解析响应
        lines = response.strip().split("\n")
        key_points = []
        for line in lines:
            # 移除编号前缀
            cleaned = line.strip().lstrip("0123456789.、) ").strip()
            if cleaned:
                key_points.append(cleaned)

        return key_points

    async def full_analysis(
        self,
        video_url: str,
    ) -> VideoAnalysis:
        """
        完整视频分析

        Args:
            video_url: 视频 URL

        Returns:
            完整分析结果
        """
        prompt = """请对这个视频进行完整分析，返回 JSON 格式：
{
    "summary": "视频整体摘要",
    "chapters": [
        {"title": "章节标题", "summary": "章节摘要"}
    ],
    "key_points": ["关键点1", "关键点2"]
}"""

        response = await self.analyze_video(video_url, prompt)

        import json
        try:
            data = json.loads(response)
            chapters = [
                VideoChapter(title=ch["title"], summary=ch["summary"])
                for ch in data.get("chapters", [])
            ]
            return VideoAnalysis(
                summary=data.get("summary", ""),
                chapters=chapters,
                key_points=data.get("key_points", []),
            )
        except (json.JSONDecodeError, KeyError):
            # 回退到纯文本摘要
            return VideoAnalysis(
                summary=response,
                chapters=[],
                key_points=[],
            )
```

> **注意**: 通义千问 Omni 的视频理解是可选功能。对于大多数场景，
> 建议优先使用 `听悟 API` 转写音频 + 向量搜索，成本更低且覆盖面足够。

### 6.4 yt-dlp 下载器

```python
"""
[INPUT]: 依赖 yt_dlp，asyncio，tempfile
[OUTPUT]: 对外提供 VideoDownloader 类
[POS]: processors/video 的下载引擎，被 VideoProcessor 调用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import asyncio
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from functools import partial

import yt_dlp


@dataclass
class VideoMetadata:
    """视频元数据"""
    id: str
    title: str
    duration: int              # 秒
    description: str
    thumbnail: str
    uploader: str
    platform: str
    subtitles: List[str]       # 可用字幕语言
    auto_captions: List[str]   # 自动生成字幕语言


@dataclass
class DownloadResult:
    """下载结果"""
    video_path: Optional[str]
    audio_path: Optional[str]
    subtitle_path: Optional[str]
    thumbnail_path: Optional[str]
    metadata: VideoMetadata


class VideoDownloader:
    """
    yt-dlp 视频下载器

    支持：
    - YouTube, Bilibili, Vimeo, Twitter 等 1000+ 平台
    - 自动选择最佳质量
    - 字幕下载
    - 元数据提取
    """

    # ============================================================
    # 配置
    # ============================================================

    DEFAULT_OPTIONS = {
        # 格式选择
        "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",

        # 输出
        "outtmpl": "%(id)s.%(ext)s",

        # 字幕
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["zh", "zh-Hans", "zh-TW", "en"],
        "subtitlesformat": "vtt",

        # 缩略图
        "writethumbnail": True,

        # 限制
        "max_filesize": 2 * 1024 * 1024 * 1024,  # 2GB

        # 重试
        "retries": 3,
        "fragment_retries": 3,

        # 静默
        "quiet": True,
        "no_warnings": True,
    }

    PREFERRED_SUBTITLE_LANGS = ["zh", "zh-Hans", "en"]

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or tempfile.mkdtemp()
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    # ============================================================
    # 公开方法
    # ============================================================

    async def get_metadata(self, url: str) -> VideoMetadata:
        """
        获取视频元数据（不下载）
        """
        opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

        # 在线程池中运行（yt-dlp 是同步的）
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None,
            partial(self._extract_info, url, opts),
        )

        return VideoMetadata(
            id=info.get("id", ""),
            title=info.get("title", ""),
            duration=info.get("duration", 0),
            description=info.get("description", ""),
            thumbnail=info.get("thumbnail", ""),
            uploader=info.get("uploader", ""),
            platform=info.get("extractor", ""),
            subtitles=list(info.get("subtitles", {}).keys()),
            auto_captions=list(info.get("automatic_captions", {}).keys()),
        )

    async def download(
        self,
        url: str,
        download_video: bool = True,
        download_audio_only: bool = False,
        download_subtitles: bool = True,
    ) -> DownloadResult:
        """
        下载视频
        """
        # 先获取元数据
        metadata = await self.get_metadata(url)

        # 构建下载选项
        opts = self.DEFAULT_OPTIONS.copy()
        opts["outtmpl"] = os.path.join(self.output_dir, "%(id)s.%(ext)s")

        if download_audio_only:
            opts["format"] = "bestaudio[ext=m4a]/bestaudio"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

        if not download_subtitles:
            opts["writesubtitles"] = False
            opts["writeautomaticsub"] = False

        # 执行下载
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            partial(self._download, url, opts),
        )

        # 查找下载的文件
        video_path = self._find_file(metadata.id, [".mp4", ".webm", ".mkv"])
        audio_path = self._find_file(metadata.id, [".mp3", ".m4a", ".wav"])
        subtitle_path = self._find_subtitle(metadata.id)
        thumbnail_path = self._find_file(metadata.id, [".jpg", ".png", ".webp"])

        return DownloadResult(
            video_path=video_path,
            audio_path=audio_path,
            subtitle_path=subtitle_path,
            thumbnail_path=thumbnail_path,
            metadata=metadata,
        )

    async def download_audio_only(self, url: str) -> DownloadResult:
        """
        仅下载音轨
        """
        return await self.download(
            url,
            download_video=False,
            download_audio_only=True,
            download_subtitles=False,
        )

    # ============================================================
    # 私有方法
    # ============================================================

    def _extract_info(self, url: str, opts: Dict) -> Dict:
        """提取视频信息"""
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _download(self, url: str, opts: Dict) -> None:
        """下载视频"""
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    def _find_file(
        self,
        video_id: str,
        extensions: List[str],
    ) -> Optional[str]:
        """查找下载的文件"""
        for ext in extensions:
            path = os.path.join(self.output_dir, f"{video_id}{ext}")
            if os.path.exists(path):
                return path
        return None

    def _find_subtitle(self, video_id: str) -> Optional[str]:
        """查找字幕文件（按优先级）"""
        for lang in self.PREFERRED_SUBTITLE_LANGS:
            # 手动字幕
            path = os.path.join(self.output_dir, f"{video_id}.{lang}.vtt")
            if os.path.exists(path):
                return path
            # 自动字幕
            path = os.path.join(self.output_dir, f"{video_id}.{lang}.auto.vtt")
            if os.path.exists(path):
                return path
        return None

    def cleanup(self):
        """清理临时文件"""
        import shutil
        if self.output_dir and os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
```

---

## 7. 配置与环境变量

### 7.1 环境变量

```bash
# ============================================================
# 音频处理 (听悟 API)
# ============================================================

# 阿里云听悟 (用户已有)
TINGWU_ACCESS_KEY_ID=xxxxxxxx
TINGWU_ACCESS_KEY_SECRET=xxxxxxxx
TINGWU_APP_KEY=xxxxxxxx

# ============================================================
# 视频处理 (可选)
# ============================================================

# 阿里云百炼 - 通义千问 Omni (可选，视频理解)
DASHSCOPE_API_KEY=sk-xxxxxxxx

# ============================================================
# 存储
# ============================================================

# Cloudflare R2
R2_ACCOUNT_ID=xxxxxxxx
R2_ACCESS_KEY_ID=xxxxxxxx
R2_SECRET_ACCESS_KEY=xxxxxxxx
R2_BUCKET_NAME=signal-hunter-media

# ============================================================
# 系统配置
# ============================================================

# FFmpeg 路径（如果不在 PATH 中）
FFMPEG_PATH=/usr/local/bin/ffmpeg
FFPROBE_PATH=/usr/local/bin/ffprobe

# 临时文件目录
TEMP_DIR=/tmp/signal-hunter

# 并发限制
AUDIO_MAX_CONCURRENT=3
VIDEO_MAX_CONCURRENT=2
```

### 7.2 config.yaml 扩展

```yaml
# ============================================================
# 多模态处理配置
# ============================================================

multimodal:
  # 音频处理
  audio:
    # 听悟 API 配置
    tingwu:
      diarization_enabled: true      # 说话人分离
      default_speaker_count: 2       # 默认说话人数
      auto_chapters_enabled: true    # 自动章节
      transcription_level: 2         # 详细级别

    # FFmpeg 预处理
    preprocess:
      sample_rate: 16000
      channels: 1
      bitrate: "64k"
      format: "mp3"

    # 队列配置
    queue:
      max_concurrent: 3
      max_retries: 3
      retry_delay: 60  # 秒
      poll_interval: 10  # 秒

  # 视频处理
  video:
    # yt-dlp 配置
    download:
      max_resolution: 1080
      max_duration: 7200  # 秒 (2小时)
      preferred_formats: ["mp4", "webm"]
      subtitle_langs: ["zh", "zh-Hans", "en"]

    # 通义千问 Omni 配置 (可选)
    qwen_omni:
      model: "qwen-omni-turbo"
      enabled: false  # 默认关闭，按需启用

    # 处理策略
    processing:
      prefer_existing_subtitles: true
      use_video_understanding: false  # 可选，优先使用音频转写
      generate_chapters: true

    # 队列配置
    queue:
      max_concurrent: 2
      poll_interval: 10  # 秒
      max_wait: 3600  # 秒
```

---

## 8. 成本控制与优化

### 8.1 API 成本对比

| 服务 | 价格 | 示例 (1小时内容) | 备注 |
|------|------|------------------|------|
| **听悟 API** | ~¥0.015/分钟 | ¥0.90 | ✅ 用户已有 |
| 通义千问 Omni | 按 token 计费 | ~¥1-3 | 可选功能 |
| Groq Whisper | $0.000111/分钟 | $0.007 | 参考 |
| Twelve Labs | $0.05/分钟 | $3.00 | 参考 |

### 8.2 成本优化策略

```
┌─────────────────────────────────────────────────────────────────────┐
│                        成本控制层级                                  │
└─────────────────────────────────────────────────────────────────────┘

Level 1: 入口过滤
├── 时长限制: 默认 2 小时上限
├── 来源白名单: 仅处理信任源
└── 去重检测: 相同内容不重复处理

Level 2: 智能决策
├── 字幕优先: 有字幕则跳过转写 (节省 100%)
├── 按需理解: 通义千问 Omni 仅用于需要深度理解的视频
└── 降级策略: 非关键内容使用低成本方案

Level 3: 批量优化
├── 队列合并: 短音频合并后批量处理
├── 缓存复用: 相同内容共享转写结果
└── 峰谷调度: 低峰期处理非紧急任务

Level 4: 监控告警
├── 日预算限制: 超限自动暂停
├── 异常检测: 单任务成本异常告警
└── 使用报告: 每日成本汇总
```

### 8.3 配额与限制

```python
# 成本控制配置
COST_LIMITS = {
    # 每日预算（人民币）
    "daily_budget": {
        "tingwu": 50.00,        # ¥50/天
        "qwen_omni": 20.00,     # ¥20/天 (可选功能)
        "total": 100.00,        # ¥100/天
    },

    # 单任务限制
    "per_task": {
        "max_audio_duration": 2 * 3600,   # 2小时
        "max_video_duration": 2 * 3600,   # 2小时
    },

    # 速率限制
    "rate_limits": {
        "tingwu_concurrent_tasks": 5,     # 并发任务数
        "qwen_requests_per_minute": 30,   # 每分钟请求数
    },

    # 队列限制
    "queue": {
        "max_pending_audio": 100,
        "max_pending_video": 50,
        "max_concurrent_audio": 3,
        "max_concurrent_video": 2,
    },
}
```

### 8.4 降级策略

```
场景: 听悟 API 不可用
  ↓
降级: 标记待重试，等待服务恢复
  ↓
如果持续失败: 仅保存元数据，通知用户手动处理

场景: 通义千问 Omni 超预算
  ↓
降级: 跳过视频理解，仅使用音频转写
  ↓
功能: 文本搜索可用，视频理解不可用

场景: 视频时长超限
  ↓
降级: 仅下载音轨转写，不进行视频理解
  ↓
功能: 文本内容可用，视频理解不可用

场景: R2 存储不可用
  ↓
降级: 使用本地临时存储
  ↓
功能: 完整功能可用，但媒体文件需要清理
```

---

## 附录

### A. 依赖清单

```txt
# requirements.txt 新增

# 音频处理 (听悟)
httpx>=0.24.0
pydub>=0.25.1

# 视频处理 (通义千问 Omni - 可选)
dashscope>=1.14.0

# 视频下载
yt-dlp>=2024.1.0

# FFmpeg (系统依赖)
# apt-get install ffmpeg  # Linux
# brew install ffmpeg     # macOS
```

### B. Docker 配置

```dockerfile
# Dockerfile 新增

# 安装 FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
RUN pip install yt-dlp dashscope httpx pydub
```

### C. 文档更新协议

```
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

本文档更新时需同步:
1. /docs/CLAUDE.md - 添加 design/ 目录说明
2. /CLAUDE.md - 如有架构级变更
3. 相关代码文件的 L3 头部注释
```

---

*文档版本: 1.1 | 作者: Signal Hunter Team | 最后更新: 2026-01-17*
