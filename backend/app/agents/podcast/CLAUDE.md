# backend/app/agents/podcast/
> L2 | 父级: backend/app/agents/CLAUDE.md

## 职责
播客生成系统，包含大纲生成、对话生成、CosyVoice TTS 和音频合成。

## 成员清单
cosyvoice_client.py: 百炼 CosyVoice TTS 客户端，文本转语音
outline_agent.py: 大纲生成 Agent，根据研究内容生成播客结构
dialogue_agent.py: 对话生成 Agent，根据大纲生成双人对话脚本
synthesizer.py: 播客合成器，整合大纲/对话/TTS 流水线

## 模块详情

### cosyvoice_client.py
- **CosyVoiceClient**: TTS 客户端
  - synthesize_text(): 单段文本转语音
  - synthesize_dialogue(): 多段对话合成
  - VoicePreset: 预设音色枚举 (10+ 中英文音色)
- **音色推荐**:
  - 主持人: longxiaochun (温和男声)
  - 嘉宾: longxiaoxia (温柔女声)

### outline_agent.py
- **OutlineAgent**: 大纲生成
  - generate_outline(): 生成 PodcastOutline
- **PodcastOutline**: 大纲数据结构
  - title, description, hosts
  - sections: 章节列表
  - opening_hook, closing_cta

### dialogue_agent.py
- **DialogueAgent**: 对话生成
  - generate_dialogue(): 生成 PodcastDialogue
- **DialogueTurn**: 对话轮次
  - speaker, text, emotion

### synthesizer.py
- **PodcastSynthesizer**: 完整流水线
  - generate_podcast(): 同步生成
  - generate_podcast_stream(): 流式生成
- **PodcastProgress**: 进度反馈
  - phase, message, progress, data

## 数据流
```
研究内容
    ↓
OutlineAgent.generate_outline()
    ↓
PodcastOutline (标题/章节/要点)
    ↓
DialogueAgent.generate_dialogue()
    ↓
PodcastDialogue (对话轮次)
    ↓
CosyVoiceClient.synthesize_dialogue()
    ↓
播客音频 (MP3)
```

## 配置
环境变量:
- DASHSCOPE_API_KEY: 百炼 API Key (CosyVoice)

## 依赖
- ffmpeg: 音频合并
- dashscope: 百炼 SDK (可选)

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
