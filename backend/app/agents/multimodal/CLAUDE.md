# backend/app/agents/multimodal/
> L2 | 父级: backend/app/agents/CLAUDE.md

## 职责
多模态处理服务，包含音频转写、视频处理和源材料处理器。

## 成员清单
tingwu_client.py: 阿里云听悟 API 客户端，语音/视频转写
source_processor.py: 源材料处理器，统一处理 URL/音频/视频/PDF/文本

## 模块详情

### tingwu_client.py
- **TingwuClient**: 听悟语音转写客户端
  - create_task(): 创建转写任务
  - get_task_status(): 查询任务状态
  - wait_for_result(): 等待并获取结果
  - transcribe(): 便捷方法 (创建+等待)
- **数据结构**:
  - TranscriptSegment: 转写片段 (text/start_time/end_time/speaker)
  - TranscriptionResult: 转写结果 (full_text/segments/duration_ms)

### source_processor.py
- **SourceProcessor**: 源材料统一处理器
  - process_source(): 处理任意类型源材料
  - _process_url(): URL → 抓取内容
  - _process_media(): 音频/视频 → 听悟转写
  - _process_pdf(): PDF → 文本提取 (TODO)
  - _process_text(): 纯文本 → 直接使用
  - _generate_embeddings(): 生成向量嵌入

## 数据流
```
源材料上传
    ↓
SourceProcessor.process_source()
    ├── URL → Jina Reader 抓取
    ├── 音频/视频 → TingwuClient 转写
    ├── PDF → 文本提取
    └── 文本 → 直接使用
    ↓
生成嵌入向量 (BailianEmbeddingService)
    ↓
存储到 SourceEmbedding 表
```

## 配置
环境变量:
- TINGWU_API_KEY: 听悟 API Key
- TINGWU_APP_KEY: 听悟 App Key

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
