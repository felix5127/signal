# 播客生成模块技术方案

> 版本: 1.1 | 日期: 2026-01-17 | 状态: 设计中

---

## 目录

1. [模块概述](#1-模块概述)
2. [播客生成架构](#2-播客生成架构)
3. [TTS 集成](#3-tts-集成)
4. [播客 Skill 设计](#4-播客-skill-设计)
5. [数据模型](#5-数据模型)
6. [API 设计](#6-api-设计)
7. [代码示例](#7-代码示例)
8. [成本估算](#8-成本估算)
9. [部署考量](#9-部署考量)

---

## 1. 模块概述

### 1.1 功能定位

将研究报告、文章摘要转化为对话式播客音频，模拟两位主持人的自然讨论。

### 1.2 核心能力

| 能力 | 描述 |
|------|------|
| **大纲生成** | 基于源材料生成结构化播客大纲 |
| **对话生成** | 生成自然流畅的多角色对话脚本 |
| **语音合成** | 使用百炼 CosyVoice 合成多角色音频 |
| **音频合并** | 将多段音频合成完整播客 |

### 1.3 设计原则

```
简洁 > 功能 > 扩展
- 最少的 Agent 数量，最大的功能覆盖
- 流水线式处理，每步可独立测试
- 成本控制优先，避免 token 浪费
```

---

## 2. 播客生成架构

### 2.1 整体流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      Podcast Generation Pipeline                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────┐│
│   │  Source  │────▶│ Outline  │────▶│ Dialogue │────▶│  TTS   ││
│   │  Input   │     │  Agent   │     │  Agent   │     │ Engine ││
│   └──────────┘     └──────────┘     └──────────┘     └────────┘│
│        │                │                │                │     │
│        ▼                ▼                ▼                ▼     │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────┐│
│   │ Research │     │ Outline  │     │ Dialogue │     │ Audio  ││
│   │ Report   │     │   JSON   │     │  Script  │     │  MP3   ││
│   └──────────┘     └──────────┘     └──────────┘     └────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 大纲生成 Agent

#### 职责
分析源材料，生成结构化播客大纲。

#### 输入
```python
class OutlineInput(BaseModel):
    """大纲生成器输入"""
    source_content: str          # 源材料 (研究报告/文章摘要)
    source_title: str            # 源标题
    target_duration: int = 600   # 目标时长 (秒)，默认 10 分钟
    style: str = "casual"        # 风格: casual/formal/debate
    language: str = "zh"         # 语言: zh/en
```

#### 输出
```python
class OutlineSection(BaseModel):
    """大纲段落"""
    section_id: str              # 段落ID (intro/main_1/conclusion 等)
    title: str                   # 段落标题
    key_points: List[str]        # 关键点列表
    duration_seconds: int        # 预估时长
    speaker_ratio: Dict[str, float]  # 发言比例 {"host_a": 0.6, "host_b": 0.4}

class PodcastOutline(BaseModel):
    """播客大纲"""
    title: str                   # 播客标题
    description: str             # 播客描述
    sections: List[OutlineSection]  # 段落列表
    total_duration: int          # 总时长预估
    metadata: Dict[str, Any]     # 扩展元数据
```

#### Prompt 设计

```python
OUTLINE_SYSTEM_PROMPT = """
你是一位资深播客策划人，擅长将复杂技术内容转化为引人入胜的对话节目。

任务：为给定的源材料生成播客大纲。

要求：
1. 开场 (intro): 30-60 秒，抛出核心问题，吸引听众
2. 主体 (main_*): 3-5 个段落，每段 2-3 分钟，深入讨论
3. 结尾 (conclusion): 60-90 秒，总结观点，留下悬念

风格指南：
- casual: 朋友聊天，轻松幽默
- formal: 专业访谈，严谨客观
- debate: 观点交锋，互相挑战

输出格式：严格 JSON，遵循 PodcastOutline schema。
"""

OUTLINE_USER_PROMPT = """
源标题：{title}
目标时长：{duration} 秒
风格：{style}
语言：{language}

源内容：
---
{content}
---

请生成播客大纲。
"""
```

#### Agent 实现

```python
class OutlineAgent:
    """
    [INPUT]: 依赖 LLMClient, OutlineInput
    [OUTPUT]: 对外提供 generate() -> PodcastOutline
    [POS]: podcast_agents/ 的大纲规划器，被 PodcastService 调用
    [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def generate(self, input: OutlineInput) -> PodcastOutline:
        """生成播客大纲"""
        prompt = OUTLINE_USER_PROMPT.format(
            title=input.source_title,
            duration=input.target_duration,
            style=input.style,
            language=input.language,
            content=input.source_content[:8000]  # 截断避免 token 溢出
        )

        result = await self.llm.call_json(
            system_prompt=OUTLINE_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.7
        )

        return PodcastOutline(**result)
```

### 2.3 对话生成 Agent

#### 职责
基于大纲生成自然对话脚本，支持多角色。

#### 输入
```python
class DialogueInput(BaseModel):
    """对话生成器输入"""
    outline: PodcastOutline        # 播客大纲
    source_content: str            # 源材料 (用于补充细节)
    host_profiles: List[HostProfile]  # 主持人人设

class HostProfile(BaseModel):
    """主持人人设"""
    id: str                        # 角色ID (host_a/host_b)
    name: str                      # 角色名称
    persona: str                   # 人设描述
    voice_id: str                  # CosyVoice 音色 ID
```

#### 输出
```python
class DialogueTurn(BaseModel):
    """对话回合"""
    speaker_id: str                # 发言者ID
    text: str                      # 发言内容
    emotion: str = "neutral"       # 情感标记: neutral/excited/thoughtful
    pause_after: float = 0.5       # 后置停顿 (秒)

class DialogueSection(BaseModel):
    """对话段落"""
    section_id: str                # 对应大纲段落ID
    turns: List[DialogueTurn]      # 对话回合列表

class PodcastDialogue(BaseModel):
    """完整对话脚本"""
    sections: List[DialogueSection]  # 段落列表
    word_count: int                  # 总字数
    estimated_duration: int          # 预估时长 (秒)
```

#### 多角色对话策略

**1. 角色分工**

```python
DEFAULT_HOST_PROFILES = [
    HostProfile(
        id="host_a",
        name="小明",
        persona="技术背景深厚，善于解释复杂概念，语气稳重专业",
        voice_id="longxiaochun"  # CosyVoice 龙小淳 - 成熟稳重男声
    ),
    HostProfile(
        id="host_b",
        name="小红",
        persona="产品思维敏锐，善于追问和举例，语气活泼好奇",
        voice_id="longwan"  # CosyVoice 龙婉 - 温柔亲和女声
    )
]
```

**2. 对话模式**

```
模式 A: 主讲 + 追问
  host_a: [讲解核心概念]
  host_b: [追问/举例/类比]
  host_a: [深入解释]

模式 B: 观点交锋
  host_a: [提出观点 A]
  host_b: [提出反驳/补充]
  host_a: [回应/综合]

模式 C: 轮流主导
  host_a: [主导第一段]
  host_b: [主导第二段]
```

**3. 自然度增强**

```python
NATURAL_MARKERS = {
    "opening": ["嗯，", "说到这个，", "你看，", "其实，"],
    "agreement": ["对对对，", "没错，", "确实是这样，"],
    "transition": ["那接下来，", "说到这里，", "讲完这个，"],
    "thinking": ["让我想想...", "这个问题很好，"],
    "surprise": ["哇，这个厉害！", "真的假的？", "这个有意思，"],
}
```

#### Prompt 设计

```python
DIALOGUE_SYSTEM_PROMPT = """
你是一位播客脚本作家，擅长写出自然流畅的双人对话。

主持人 A ({host_a_name}): {host_a_persona}
主持人 B ({host_b_name}): {host_b_persona}

规则：
1. 每句话不超过 50 字，适合朗读
2. 使用口语化表达，避免书面语
3. 加入自然的语气词和过渡词
4. 每 3-4 个回合切换一次主导者
5. 保持信息密度，避免无意义的客套

情感标记：
- neutral: 平静陈述
- excited: 兴奋强调
- thoughtful: 沉思停顿

输出格式：严格 JSON，遵循 PodcastDialogue schema。
"""

DIALOGUE_USER_PROMPT = """
播客大纲：
{outline_json}

源材料摘要：
{source_summary}

请按大纲生成完整对话脚本。
"""
```

### 2.4 Agent 编排

```python
class PodcastPipeline:
    """
    [INPUT]: 依赖 OutlineAgent, DialogueAgent, TTSEngine
    [OUTPUT]: 对外提供 generate() -> PodcastResult
    [POS]: podcast/ 的流水线编排器，被 PodcastService 调用
    [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
    """

    def __init__(self):
        self.outline_agent = OutlineAgent(llm_client)
        self.dialogue_agent = DialogueAgent(llm_client)
        self.tts_engine = CosyVoiceTTSEngine()

    async def generate(
        self,
        source: str,
        title: str,
        duration: int = 600,
        progress_callback: Optional[Callable] = None
    ) -> PodcastResult:
        """
        完整播客生成流水线

        Steps:
        1. 生成大纲 (10%)
        2. 生成对话脚本 (30%)
        3. TTS 合成 (50%)
        4. 音频合并 (10%)
        """
        # Step 1: 大纲生成
        await self._report_progress(progress_callback, 5, "正在分析源材料...")
        outline = await self.outline_agent.generate(OutlineInput(
            source_content=source,
            source_title=title,
            target_duration=duration
        ))
        await self._report_progress(progress_callback, 10, "大纲生成完成")

        # Step 2: 对话生成
        await self._report_progress(progress_callback, 15, "正在创作对话脚本...")
        dialogue = await self.dialogue_agent.generate(DialogueInput(
            outline=outline,
            source_content=source,
            host_profiles=DEFAULT_HOST_PROFILES
        ))
        await self._report_progress(progress_callback, 30, "对话脚本完成")

        # Step 3: TTS 合成
        await self._report_progress(progress_callback, 35, "正在合成语音...")
        audio_segments = await self.tts_engine.synthesize_dialogue(
            dialogue=dialogue,
            host_profiles=DEFAULT_HOST_PROFILES,
            progress_callback=lambda p: self._report_progress(
                progress_callback, 35 + int(p * 0.5), f"语音合成中 ({int(p*100)}%)"
            )
        )
        await self._report_progress(progress_callback, 85, "语音合成完成")

        # Step 4: 音频合并
        await self._report_progress(progress_callback, 90, "正在合并音频...")
        final_audio = await self._merge_audio(audio_segments)
        await self._report_progress(progress_callback, 100, "播客生成完成")

        return PodcastResult(
            audio_url=final_audio.url,
            duration=final_audio.duration,
            outline=outline,
            dialogue=dialogue,
            cost=self._calculate_cost(dialogue)
        )
```

---

## 3. TTS 集成

### 3.1 百炼 CosyVoice 集成

#### 技术规格

| 参数 | 值 |
|------|-----|
| 平台 | 阿里云百炼 |
| 模型 | CosyVoice |
| 采样率 | 22.05kHz / 44.1kHz |
| 格式 | MP3 / WAV / PCM |
| 延迟 | 流式输出，低延迟 |
| 支持语言 | 中文优化，多语种支持 |
| 成本 | ¥2/万字符 |

> **选型理由**: 用户已有百炼平台账号，CosyVoice 支持多音色，中文语音质量优秀。

#### 核心配置

```python
# config/cosyvoice.py

COSYVOICE_CONFIG = {
    "model": "cosyvoice-v1",
    "output_format": "mp3",
    "sample_rate": 22050,       # 22.05kHz

    "voice_settings": {
        "speed": 1.0,             # 语速 (0.5-2.0)
        "volume": 100,            # 音量 (0-100)
        "pitch": 0,               # 音调调整 (-500 到 500)
    },

    # 中文优化参数
    "zh_optimization": {
        "speed": 0.95,            # 中文稍慢更自然
        "enable_emotion": True    # 启用情感表达
    }
}
```

### 3.2 声音角色配置

```python
class VoiceProfile(BaseModel):
    """声音角色配置"""
    voice_id: str           # CosyVoice 音色 ID
    name: str               # 显示名称
    language: str           # 主要语言
    gender: str             # male/female
    age: str                # young/middle/senior
    style: str              # 风格描述

# CosyVoice 预置音色
# 文档: https://help.aliyun.com/document_detail/dashscope-cosyvoice

VOICE_PROFILES = {
    # 中文男声
    "zh_male_professional": VoiceProfile(
        voice_id="longxiaochun",        # 龙小淳 - 男声，成熟稳重
        name="小明",
        language="zh",
        gender="male",
        age="middle",
        style="专业、稳重、有磁性"
    ),

    # 中文女声
    "zh_female_lively": VoiceProfile(
        voice_id="longwan",             # 龙婉 - 女声，温柔亲和
        name="小红",
        language="zh",
        gender="female",
        age="young",
        style="活泼、好奇、亲和力强"
    ),

    # 中文男声 (备选)
    "zh_male_narrator": VoiceProfile(
        voice_id="longshu",             # 龙舒 - 男声，沉稳大气
        name="主持人A",
        language="zh",
        gender="male",
        age="middle",
        style="沉稳、专业、播音腔"
    ),

    # 中文女声 (备选)
    "zh_female_conversational": VoiceProfile(
        voice_id="longxiaoxia",         # 龙小夏 - 女声，活泼自然
        name="主持人B",
        language="zh",
        gender="female",
        age="young",
        style="自然、对话感、温暖"
    )
}
```

> **注意**: CosyVoice 提供多种预置音色，可根据播客风格选择合适的组合。
> 详细音色列表请参考百炼平台文档。

### 3.3 音频合成流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     TTS Synthesis Pipeline                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   DialogueTurn[]                                                 │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────────────────────────────────────┐           │
│   │              Text Preprocessing                  │           │
│   │  - 分句断行                                      │           │
│   │  - 添加 SSML 标记 (停顿/重音)                    │           │
│   │  - 情感映射到 voice_settings                     │           │
│   └─────────────────────────────────────────────────┘           │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────────────────────────────────────┐           │
│   │              Parallel TTS Requests               │           │
│   │  - 按 speaker 分组                              │           │
│   │  - 并发调用 CosyVoice API                        │           │
│   │  - 速率限制: 按百炼账号 QPS                      │           │
│   └─────────────────────────────────────────────────┘           │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────────────────────────────────────┐           │
│   │              Audio Post-processing               │           │
│   │  - 添加段间静音 (pydub)                          │           │
│   │  - 音量标准化 (-16 LUFS)                        │           │
│   │  - 淡入淡出处理                                  │           │
│   └─────────────────────────────────────────────────┘           │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────────────────────────────────────┐           │
│   │              Segment Concatenation               │           │
│   │  - 按对话顺序拼接                               │           │
│   │  - 段落间添加过渡音效                            │           │
│   │  - 开头/结尾添加 jingle                          │           │
│   └─────────────────────────────────────────────────┘           │
│        │                                                         │
│        ▼                                                         │
│   Final MP3 (44.1kHz, 128kbps)                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### TTS Engine 实现

```python
class CosyVoiceTTSEngine:
    """
    [INPUT]: 依赖 dashscope SDK, pydub
    [OUTPUT]: 对外提供 synthesize_dialogue() -> List[AudioSegment]
    [POS]: tts/ 的 CosyVoice 引擎实现，被 PodcastPipeline 调用
    [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
    """

    def __init__(self):
        import dashscope
        dashscope.api_key = config.dashscope_api_key
        self.rate_limiter = AsyncRateLimiter(max_rate=10)  # 按账号 QPS

    async def synthesize_dialogue(
        self,
        dialogue: PodcastDialogue,
        host_profiles: List[HostProfile],
        progress_callback: Optional[Callable] = None
    ) -> List[AudioSegment]:
        """
        合成完整对话音频

        策略：
        1. 按 speaker 分组，减少 voice 切换开销
        2. 并发请求，受速率限制
        3. 流式返回，节省内存
        """
        voice_map = {p.id: p.voice_id for p in host_profiles}
        segments = []
        total_turns = sum(len(s.turns) for s in dialogue.sections)
        processed = 0

        for section in dialogue.sections:
            for turn in section.turns:
                # 预处理文本
                text = self._preprocess_text(turn.text, turn.emotion)

                # 获取声音设置
                voice_settings = self._get_voice_settings(turn.emotion)

                # 调用 API (带速率限制)
                async with self.rate_limiter:
                    audio = await self._generate_speech(
                        text=text,
                        voice_id=voice_map[turn.speaker_id],
                        voice_settings=voice_settings
                    )

                # 添加后置静音
                audio_with_pause = self._add_pause(audio, turn.pause_after)
                segments.append(audio_with_pause)

                # 进度回调
                processed += 1
                if progress_callback:
                    await progress_callback(processed / total_turns)

        return segments

    def _preprocess_text(self, text: str, emotion: str) -> str:
        """文本预处理：添加语气标记"""
        # CosyVoice 使用自然语言情感表达
        if emotion == "excited":
            return f'{text}！'
        elif emotion == "thoughtful":
            return f'嗯...{text}'
        return text

    def _get_voice_settings(self, emotion: str) -> Dict:
        """根据情感调整声音参数"""
        base = COSYVOICE_CONFIG["voice_settings"].copy()

        if emotion == "excited":
            base["speed"] = 1.1       # 稍快
            base["pitch"] = 50        # 稍高
        elif emotion == "thoughtful":
            base["speed"] = 0.9       # 稍慢
            base["pitch"] = -20       # 稍低

        return base

    async def _generate_speech(
        self,
        text: str,
        voice_id: str,
        voice_settings: Dict
    ) -> bytes:
        """调用 CosyVoice API"""
        from dashscope.audio.tts import SpeechSynthesizer

        result = SpeechSynthesizer.call(
            model="cosyvoice-v1",
            voice=voice_id,
            text=text,
            format="mp3",
            sample_rate=COSYVOICE_CONFIG["sample_rate"],
            **voice_settings
        )

        if result.status_code != 200:
            raise RuntimeError(f"TTS 合成失败: {result.message}")

        return result.get_audio_data()

    def _add_pause(self, audio: bytes, pause_seconds: float) -> AudioSegment:
        """添加后置静音"""
        from pydub import AudioSegment
        import io

        segment = AudioSegment.from_mp3(io.BytesIO(audio))
        silence = AudioSegment.silent(duration=int(pause_seconds * 1000))
        return segment + silence
```

### 3.4 音频后处理

```python
class AudioPostProcessor:
    """音频后处理器"""

    def merge_segments(
        self,
        segments: List[AudioSegment],
        intro_jingle: Optional[str] = None,
        outro_jingle: Optional[str] = None,
        section_divider: Optional[str] = None
    ) -> AudioSegment:
        """合并音频片段"""
        from pydub import AudioSegment

        final = AudioSegment.empty()

        # 添加开场 jingle
        if intro_jingle:
            jingle = AudioSegment.from_file(intro_jingle)
            final += jingle + AudioSegment.silent(duration=500)

        # 合并所有片段
        for segment in segments:
            final += segment

        # 添加结尾 jingle
        if outro_jingle:
            jingle = AudioSegment.from_file(outro_jingle)
            final += AudioSegment.silent(duration=500) + jingle

        # 音量标准化
        final = self._normalize_loudness(final)

        # 淡入淡出
        final = final.fade_in(500).fade_out(1000)

        return final

    def _normalize_loudness(
        self,
        audio: AudioSegment,
        target_lufs: float = -16.0
    ) -> AudioSegment:
        """音量标准化 (简化版)"""
        # 实际生产环境应使用 pyloudnorm 进行精确 LUFS 标准化
        change_in_dBFS = target_lufs - audio.dBFS
        return audio.apply_gain(change_in_dBFS)

    def export(
        self,
        audio: AudioSegment,
        output_path: str,
        format: str = "mp3",
        bitrate: str = "128k"
    ) -> str:
        """导出音频文件"""
        audio.export(
            output_path,
            format=format,
            bitrate=bitrate,
            tags={
                "title": "Signal Hunter Podcast",
                "artist": "AI Generated",
                "album": "Signal Hunter",
            }
        )
        return output_path
```

---

## 4. 播客 Skill 设计

### 4.1 SKILL.md 格式

```markdown
# podcast - 播客生成 Skill

## 触发条件
- 用户输入包含 "生成播客"、"转成播客"、"做成音频" 等关键词
- 研究报告完成后，用户选择"导出为播客"

## 输入参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| source_id | int | 是 | - | 源材料 ID (research_output.id) |
| duration | int | 否 | 600 | 目标时长 (秒) |
| style | string | 否 | "casual" | 风格: casual/formal/debate |
| language | string | 否 | "zh" | 语言: zh/en |
| voice_preset | string | 否 | "default" | 声音预设 |

## 执行步骤

1. **验证源材料**
   - 检查 source_id 存在
   - 检查源材料字数 > 500

2. **生成大纲**
   - 调用 OutlineAgent
   - 保存大纲到 podcast_tasks

3. **生成对话**
   - 调用 DialogueAgent
   - 保存脚本到 podcast_tasks

4. **语音合成**
   - 调用 CosyVoiceTTSEngine
   - 实时更新进度

5. **音频合并**
   - 调用 AudioPostProcessor
   - 上传到 R2

6. **保存结果**
   - 更新 podcast_tasks 状态
   - 创建 podcast_episodes 记录

## 输出格式

```json
{
  "success": true,
  "data": {
    "episode_id": "uuid",
    "audio_url": "https://r2.example.com/podcast/xxx.mp3",
    "duration": 623,
    "outline": { ... },
    "cost": {
      "llm_tokens": 5000,
      "tts_characters": 12000,
      "total_usd": 0.85
    }
  }
}
```

## 错误处理

| 错误码 | 说明 | 恢复策略 |
|--------|------|----------|
| PODCAST_001 | 源材料不存在 | 提示用户选择有效源 |
| PODCAST_002 | 源材料过短 | 提示最低字数要求 |
| PODCAST_003 | TTS 配额耗尽 | 提示升级套餐或明天重试 |
| PODCAST_004 | 生成超时 | 自动重试或拆分任务 |

## 成本控制

- 每日限额: 10 次/用户
- 单次上限: 30 分钟
- 预估成本: $0.08-0.15/分钟

## 使用示例

```
用户: 把这篇研究报告转成播客
助手: 好的，我来帮你生成播客。

[调用 podcast skill]
- 源材料: "GPT-5 技术分析报告"
- 预估时长: 10 分钟
- 预估成本: $0.85

生成中...
[进度条: 正在创作大纲 20%]
[进度条: 正在编写对话 45%]
[进度条: 正在合成语音 80%]
[进度条: 正在合并音频 95%]

完成！播客已生成：
- 时长: 10:23
- 文件: [下载链接]
- 播放: [在线播放器]
```
```

### 4.2 Skill 注册配置

```python
# skills/podcast/__init__.py

SKILL_CONFIG = {
    "name": "podcast",
    "display_name": "播客生成",
    "description": "将研究报告转换为双人对话式播客",
    "version": "1.0.0",
    "author": "Signal Hunter",

    "triggers": [
        {"type": "keyword", "patterns": ["生成播客", "转成播客", "做成音频"]},
        {"type": "action", "name": "export_podcast"},
    ],

    "parameters": {
        "source_id": {"type": "int", "required": True},
        "duration": {"type": "int", "default": 600, "min": 60, "max": 1800},
        "style": {"type": "enum", "values": ["casual", "formal", "debate"], "default": "casual"},
        "language": {"type": "enum", "values": ["zh", "en"], "default": "zh"},
    },

    "limits": {
        "daily_per_user": 10,
        "max_duration_seconds": 1800,
        "max_source_words": 50000,
    },

    "cost_model": {
        "base_usd": 0.05,
        "per_minute_usd": 0.08,
    }
}
```

---

## 5. 数据模型

### 5.1 数据库表设计

```sql
-- ============================================================================
-- 播客任务表
-- ============================================================================
CREATE TABLE podcast_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(64) UNIQUE NOT NULL,        -- 唯一任务ID

    -- 关联
    user_id INTEGER REFERENCES users(id),        -- 用户ID
    source_id INTEGER NOT NULL,                  -- 源材料ID (research_output.id)
    source_type VARCHAR(20) NOT NULL,            -- research_report/article/resource

    -- 配置
    target_duration INTEGER DEFAULT 600,         -- 目标时长 (秒)
    style VARCHAR(20) DEFAULT 'casual',          -- casual/formal/debate
    language VARCHAR(10) DEFAULT 'zh',           -- zh/en
    voice_preset VARCHAR(50) DEFAULT 'default',  -- 声音预设

    -- 生成结果
    outline JSONB,                               -- 大纲 JSON
    dialogue JSONB,                              -- 对话脚本 JSON

    -- 状态
    status VARCHAR(20) DEFAULT 'pending',        -- pending/processing/completed/failed
    progress INTEGER DEFAULT 0,                  -- 0-100
    current_step VARCHAR(50),                    -- 当前步骤
    error_message TEXT,                          -- 错误信息

    -- 成本
    llm_tokens INTEGER DEFAULT 0,                -- LLM token 消耗
    tts_characters INTEGER DEFAULT 0,            -- TTS 字符数
    cost_usd DECIMAL(10, 4) DEFAULT 0,           -- 总成本 (USD)

    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- 索引
    INDEX idx_podcast_tasks_user_id (user_id),
    INDEX idx_podcast_tasks_status (status),
    INDEX idx_podcast_tasks_created_at (created_at DESC)
);

-- ============================================================================
-- 播客剧集表
-- ============================================================================
CREATE TABLE podcast_episodes (
    id SERIAL PRIMARY KEY,
    episode_id UUID DEFAULT gen_random_uuid(),   -- 公开 ID

    -- 关联
    task_id INTEGER REFERENCES podcast_tasks(id),
    user_id INTEGER REFERENCES users(id),

    -- 内容
    title VARCHAR(500) NOT NULL,                 -- 播客标题
    description TEXT,                            -- 播客描述

    -- 音频
    audio_url TEXT NOT NULL,                     -- 音频文件 URL (R2)
    audio_format VARCHAR(10) DEFAULT 'mp3',      -- mp3/wav
    duration INTEGER NOT NULL,                   -- 实际时长 (秒)
    file_size INTEGER,                           -- 文件大小 (bytes)

    -- 元数据
    outline JSONB,                               -- 大纲 (冗余存储)
    word_count INTEGER,                          -- 对话总字数
    host_profiles JSONB,                         -- 主持人配置

    -- 统计
    play_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,

    -- 状态
    is_public BOOLEAN DEFAULT FALSE,             -- 是否公开

    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),

    -- 索引
    INDEX idx_podcast_episodes_user_id (user_id),
    INDEX idx_podcast_episodes_episode_id (episode_id),
    INDEX idx_podcast_episodes_created_at (created_at DESC)
);

-- ============================================================================
-- 声音配置表
-- ============================================================================
CREATE TABLE voice_profiles (
    id SERIAL PRIMARY KEY,

    -- 基础信息
    voice_id VARCHAR(100) NOT NULL,              -- CosyVoice 音色 ID
    name VARCHAR(100) NOT NULL,                  -- 显示名称
    language VARCHAR(10) NOT NULL,               -- zh/en
    gender VARCHAR(10) NOT NULL,                 -- male/female

    -- 描述
    description TEXT,                            -- 声音描述
    sample_url TEXT,                             -- 试听音频 URL

    -- 配置
    default_settings JSONB,                      -- 默认声音设置

    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    is_premium BOOLEAN DEFAULT FALSE,            -- 是否高级声音

    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_voice_profiles_language (language),
    INDEX idx_voice_profiles_is_active (is_active)
);
```

### 5.2 SQLAlchemy 模型

```python
# models/podcast.py
"""
[INPUT]: 依赖 database.py (Base), sqlalchemy
[OUTPUT]: 对外提供 PodcastTask, PodcastEpisode, VoiceProfile ORM 模型
[POS]: models/ 的播客相关模型，被 PodcastService 消费
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Index, Float, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class PodcastTask(Base):
    """播客生成任务"""
    __tablename__ = "podcast_tasks"

    id = Column(Integer, primary_key=True)
    task_id = Column(String(64), unique=True, nullable=False, index=True)

    # 关联
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    source_id = Column(Integer, nullable=False)
    source_type = Column(String(20), nullable=False)  # research_report/article/resource

    # 配置
    target_duration = Column(Integer, default=600)
    style = Column(String(20), default="casual")
    language = Column(String(10), default="zh")
    voice_preset = Column(String(50), default="default")

    # 生成结果
    outline = Column(JSON)
    dialogue = Column(JSON)

    # 状态
    status = Column(String(20), default="pending", index=True)
    progress = Column(Integer, default=0)
    current_step = Column(String(50))
    error_message = Column(Text)

    # 成本
    llm_tokens = Column(Integer, default=0)
    tts_characters = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # 关系
    episode = relationship("PodcastEpisode", back_populates="task", uselist=False)

    __table_args__ = (
        Index("idx_podcast_tasks_user_status", "user_id", "status"),
    )


class PodcastEpisode(Base):
    """播客剧集"""
    __tablename__ = "podcast_episodes"

    id = Column(Integer, primary_key=True)
    episode_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)

    # 关联
    task_id = Column(Integer, ForeignKey("podcast_tasks.id"))
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    # 内容
    title = Column(String(500), nullable=False)
    description = Column(Text)

    # 音频
    audio_url = Column(Text, nullable=False)
    audio_format = Column(String(10), default="mp3")
    duration = Column(Integer, nullable=False)
    file_size = Column(Integer)

    # 元数据
    outline = Column(JSON)
    word_count = Column(Integer)
    host_profiles = Column(JSON)

    # 统计
    play_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)

    # 状态
    is_public = Column(Boolean, default=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    task = relationship("PodcastTask", back_populates="episode")

    __table_args__ = (
        Index("idx_podcast_episodes_created", "created_at"),
    )


class VoiceProfile(Base):
    """声音配置"""
    __tablename__ = "voice_profiles"

    id = Column(Integer, primary_key=True)

    voice_id = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    language = Column(String(10), nullable=False, index=True)
    gender = Column(String(10), nullable=False)

    description = Column(Text)
    sample_url = Column(Text)

    default_settings = Column(JSON)

    is_active = Column(Boolean, default=True, index=True)
    is_premium = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.now)
```

---

## 6. API 设计

### 6.1 端点概览

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/podcast/generate` | 创建播客生成任务 |
| GET | `/api/podcast/tasks/{task_id}` | 获取任务状态 |
| GET | `/api/podcast/tasks/{task_id}/stream` | SSE 进度流 |
| GET | `/api/podcast/episodes` | 获取用户播客列表 |
| GET | `/api/podcast/episodes/{episode_id}` | 获取播客详情 |
| DELETE | `/api/podcast/episodes/{episode_id}` | 删除播客 |
| GET | `/api/podcast/voices` | 获取可用声音列表 |
| POST | `/api/podcast/voices/preview` | 预览声音效果 |

### 6.2 接口定义

```python
# api/podcast.py
"""
[INPUT]: 依赖 FastAPI, PodcastService, Pydantic schemas
[OUTPUT]: 对外提供 /api/podcast/* 端点
[POS]: api/ 的播客管理接口，被前端调用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.services.podcast_service import PodcastService
from app.auth import get_current_user

router = APIRouter(prefix="/api/podcast", tags=["podcast"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class GeneratePodcastRequest(BaseModel):
    """生成播客请求"""
    source_id: int = Field(..., description="源材料 ID")
    source_type: str = Field(default="research_report", description="源类型")
    duration: int = Field(default=600, ge=60, le=1800, description="目标时长 (秒)")
    style: str = Field(default="casual", pattern="^(casual|formal|debate)$")
    language: str = Field(default="zh", pattern="^(zh|en)$")
    voice_preset: str = Field(default="default")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: int
    current_step: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    # 完成后的结果
    episode_id: Optional[str] = None
    audio_url: Optional[str] = None
    duration: Optional[int] = None
    cost_usd: Optional[float] = None


class EpisodeResponse(BaseModel):
    """播客剧集响应"""
    episode_id: str
    title: str
    description: Optional[str]
    audio_url: str
    duration: int
    file_size: Optional[int]
    outline: Optional[dict]
    word_count: Optional[int]
    play_count: int
    is_public: bool
    created_at: datetime


class VoiceResponse(BaseModel):
    """声音配置响应"""
    voice_id: str
    name: str
    language: str
    gender: str
    description: Optional[str]
    sample_url: Optional[str]
    is_premium: bool


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/generate", response_model=TaskStatusResponse)
async def generate_podcast(
    request: GeneratePodcastRequest,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    创建播客生成任务

    Returns:
        task_id 用于跟踪进度
    """
    service = PodcastService(db)

    # 检查每日限额
    daily_count = await service.get_user_daily_count(user.id)
    if daily_count >= 10:
        raise HTTPException(
            status_code=429,
            detail="已达到每日生成限额 (10次/天)"
        )

    # 创建任务
    task = await service.create_task(
        user_id=user.id,
        source_id=request.source_id,
        source_type=request.source_type,
        target_duration=request.duration,
        style=request.style,
        language=request.language,
        voice_preset=request.voice_preset
    )

    # 后台执行
    background_tasks.add_task(service.execute_pipeline, task.task_id)

    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status,
        progress=task.progress,
        current_step=task.current_step,
        error_message=None,
        created_at=task.created_at,
        started_at=None,
        completed_at=None
    )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """获取任务状态"""
    service = PodcastService(db)
    task = await service.get_task(task_id, user.id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    response = TaskStatusResponse(
        task_id=task.task_id,
        status=task.status,
        progress=task.progress,
        current_step=task.current_step,
        error_message=task.error_message,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at
    )

    # 如果完成，附加结果
    if task.status == "completed" and task.episode:
        response.episode_id = str(task.episode.episode_id)
        response.audio_url = task.episode.audio_url
        response.duration = task.episode.duration
        response.cost_usd = task.cost_usd

    return response


@router.get("/tasks/{task_id}/stream")
async def stream_task_progress(
    task_id: str,
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    SSE 进度流

    Returns:
        Server-Sent Events stream
    """
    service = PodcastService(db)

    async def event_generator():
        while True:
            task = await service.get_task(task_id, user.id)

            if not task:
                yield f"data: {json.dumps({'error': '任务不存在'})}\n\n"
                break

            yield f"data: {json.dumps({
                'status': task.status,
                'progress': task.progress,
                'current_step': task.current_step
            })}\n\n"

            if task.status in ["completed", "failed"]:
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.get("/episodes", response_model=List[EpisodeResponse])
async def list_episodes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """获取用户播客列表"""
    service = PodcastService(db)
    episodes = await service.list_episodes(
        user_id=user.id,
        page=page,
        page_size=page_size
    )

    return [EpisodeResponse(
        episode_id=str(ep.episode_id),
        title=ep.title,
        description=ep.description,
        audio_url=ep.audio_url,
        duration=ep.duration,
        file_size=ep.file_size,
        outline=ep.outline,
        word_count=ep.word_count,
        play_count=ep.play_count,
        is_public=ep.is_public,
        created_at=ep.created_at
    ) for ep in episodes]


@router.get("/episodes/{episode_id}", response_model=EpisodeResponse)
async def get_episode(
    episode_id: str,
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """获取播客详情"""
    service = PodcastService(db)
    episode = await service.get_episode(episode_id, user.id)

    if not episode:
        raise HTTPException(status_code=404, detail="播客不存在")

    return EpisodeResponse(
        episode_id=str(episode.episode_id),
        title=episode.title,
        description=episode.description,
        audio_url=episode.audio_url,
        duration=episode.duration,
        file_size=episode.file_size,
        outline=episode.outline,
        word_count=episode.word_count,
        play_count=episode.play_count,
        is_public=episode.is_public,
        created_at=episode.created_at
    )


@router.delete("/episodes/{episode_id}")
async def delete_episode(
    episode_id: str,
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """删除播客"""
    service = PodcastService(db)
    success = await service.delete_episode(episode_id, user.id)

    if not success:
        raise HTTPException(status_code=404, detail="播客不存在")

    return {"success": True}


@router.get("/voices", response_model=List[VoiceResponse])
async def list_voices(
    language: Optional[str] = Query(default=None, pattern="^(zh|en)$"),
    db = Depends(get_db)
):
    """获取可用声音列表"""
    service = PodcastService(db)
    voices = await service.list_voices(language=language)

    return [VoiceResponse(
        voice_id=v.voice_id,
        name=v.name,
        language=v.language,
        gender=v.gender,
        description=v.description,
        sample_url=v.sample_url,
        is_premium=v.is_premium
    ) for v in voices]


@router.post("/voices/preview")
async def preview_voice(
    voice_id: str,
    text: str = Query(default="你好，这是一段测试语音。", max_length=200),
    db = Depends(get_db)
):
    """预览声音效果"""
    service = PodcastService(db)
    audio_url = await service.preview_voice(voice_id, text)

    return {"audio_url": audio_url}
```

---

## 7. 代码示例

### 7.1 完整 PodcastService 实现

```python
# services/podcast_service.py
"""
[INPUT]: 依赖 PodcastPipeline, models/podcast, R2Storage
[OUTPUT]: 对外提供播客生成业务逻辑
[POS]: services/ 的播客管理服务，被 api/podcast 调用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Callable

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.podcast import PodcastTask, PodcastEpisode, VoiceProfile
from app.processors.podcast.pipeline import PodcastPipeline
from app.storage.r2 import R2Storage


class PodcastService:
    """播客生成服务"""

    def __init__(self, db: Session):
        self.db = db
        self.pipeline = PodcastPipeline()
        self.storage = R2Storage()

    # ========================================================================
    # 任务管理
    # ========================================================================

    async def create_task(
        self,
        user_id: int,
        source_id: int,
        source_type: str,
        target_duration: int = 600,
        style: str = "casual",
        language: str = "zh",
        voice_preset: str = "default"
    ) -> PodcastTask:
        """创建播客生成任务"""
        task_id = f"podcast_{user_id}_{int(time.time())}"

        task = PodcastTask(
            task_id=task_id,
            user_id=user_id,
            source_id=source_id,
            source_type=source_type,
            target_duration=target_duration,
            style=style,
            language=language,
            voice_preset=voice_preset,
            status="pending",
            progress=0
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return task

    async def get_task(self, task_id: str, user_id: int) -> Optional[PodcastTask]:
        """获取任务"""
        return self.db.query(PodcastTask).filter(
            PodcastTask.task_id == task_id,
            PodcastTask.user_id == user_id
        ).first()

    async def get_user_daily_count(self, user_id: int) -> int:
        """获取用户今日生成次数"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        return self.db.query(PodcastTask).filter(
            PodcastTask.user_id == user_id,
            PodcastTask.created_at >= today
        ).count()

    async def update_task_progress(
        self,
        task_id: str,
        progress: int,
        current_step: str
    ):
        """更新任务进度"""
        task = self.db.query(PodcastTask).filter(
            PodcastTask.task_id == task_id
        ).first()

        if task:
            task.progress = progress
            task.current_step = current_step
            self.db.commit()

    # ========================================================================
    # 播客生成
    # ========================================================================

    async def execute_pipeline(self, task_id: str):
        """执行播客生成流水线"""
        task = self.db.query(PodcastTask).filter(
            PodcastTask.task_id == task_id
        ).first()

        if not task:
            return

        try:
            # 更新状态
            task.status = "processing"
            task.started_at = datetime.now()
            self.db.commit()

            # 加载源材料
            source_content = await self._load_source(task.source_id, task.source_type)
            source_title = await self._get_source_title(task.source_id, task.source_type)

            # 进度回调
            async def progress_callback(progress: int, step: str):
                await self.update_task_progress(task_id, progress, step)

            # 执行流水线
            result = await self.pipeline.generate(
                source=source_content,
                title=source_title,
                duration=task.target_duration,
                style=task.style,
                language=task.language,
                voice_preset=task.voice_preset,
                progress_callback=progress_callback
            )

            # 上传音频到 R2
            audio_key = f"podcast/{task.user_id}/{uuid.uuid4()}.mp3"
            audio_url = await self.storage.upload(
                key=audio_key,
                data=result.audio_data,
                content_type="audio/mpeg"
            )

            # 创建 Episode
            episode = PodcastEpisode(
                task_id=task.id,
                user_id=task.user_id,
                title=result.outline.title,
                description=result.outline.description,
                audio_url=audio_url,
                duration=result.duration,
                file_size=len(result.audio_data),
                outline=result.outline.dict(),
                word_count=result.dialogue.word_count,
                host_profiles=[p.dict() for p in result.host_profiles]
            )
            self.db.add(episode)

            # 更新任务
            task.status = "completed"
            task.progress = 100
            task.current_step = "完成"
            task.completed_at = datetime.now()
            task.outline = result.outline.dict()
            task.dialogue = result.dialogue.dict()
            task.llm_tokens = result.cost.llm_tokens
            task.tts_characters = result.cost.tts_characters
            task.cost_usd = result.cost.total_usd

            self.db.commit()

        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.now()
            self.db.commit()
            raise

    async def _load_source(self, source_id: int, source_type: str) -> str:
        """加载源材料内容"""
        if source_type == "research_report":
            from app.models.research import ResearchOutput
            output = self.db.query(ResearchOutput).filter(
                ResearchOutput.id == source_id
            ).first()
            return output.content if output else ""

        elif source_type == "resource":
            from app.models.resource import Resource
            resource = self.db.query(Resource).filter(
                Resource.id == source_id
            ).first()
            if resource:
                return f"{resource.title}\n\n{resource.summary or ''}\n\n{resource.content_markdown or ''}"
            return ""

        return ""

    async def _get_source_title(self, source_id: int, source_type: str) -> str:
        """获取源材料标题"""
        if source_type == "research_report":
            from app.models.research import ResearchOutput
            output = self.db.query(ResearchOutput).filter(
                ResearchOutput.id == source_id
            ).first()
            return output.title if output else "未命名"

        elif source_type == "resource":
            from app.models.resource import Resource
            resource = self.db.query(Resource).filter(
                Resource.id == source_id
            ).first()
            return resource.title if resource else "未命名"

        return "未命名"

    # ========================================================================
    # 剧集管理
    # ========================================================================

    async def list_episodes(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> List[PodcastEpisode]:
        """获取用户播客列表"""
        offset = (page - 1) * page_size

        return self.db.query(PodcastEpisode).filter(
            PodcastEpisode.user_id == user_id
        ).order_by(
            PodcastEpisode.created_at.desc()
        ).offset(offset).limit(page_size).all()

    async def get_episode(
        self,
        episode_id: str,
        user_id: int
    ) -> Optional[PodcastEpisode]:
        """获取播客详情"""
        return self.db.query(PodcastEpisode).filter(
            PodcastEpisode.episode_id == episode_id,
            PodcastEpisode.user_id == user_id
        ).first()

    async def delete_episode(self, episode_id: str, user_id: int) -> bool:
        """删除播客"""
        episode = await self.get_episode(episode_id, user_id)

        if not episode:
            return False

        # 删除 R2 文件
        await self.storage.delete(episode.audio_url)

        # 删除数据库记录
        self.db.delete(episode)
        self.db.commit()

        return True

    # ========================================================================
    # 声音管理
    # ========================================================================

    async def list_voices(
        self,
        language: Optional[str] = None
    ) -> List[VoiceProfile]:
        """获取可用声音列表"""
        query = self.db.query(VoiceProfile).filter(
            VoiceProfile.is_active == True
        )

        if language:
            query = query.filter(VoiceProfile.language == language)

        return query.all()

    async def preview_voice(self, voice_id: str, text: str) -> str:
        """预览声音"""
        from app.processors.podcast.tts import CosyVoiceTTSEngine

        engine = CosyVoiceTTSEngine()
        audio_data = await engine._generate_speech(
            text=text,
            voice_id=voice_id,
            voice_settings={}
        )

        # 临时上传 (1小时过期)
        key = f"podcast/preview/{uuid.uuid4()}.mp3"
        url = await self.storage.upload(
            key=key,
            data=audio_data,
            content_type="audio/mpeg",
            expires_in=3600
        )

        return url
```

### 7.2 使用示例

```python
# 示例：从研究报告生成播客

from app.services.podcast_service import PodcastService
from app.database import SessionLocal

async def demo_generate_podcast():
    db = SessionLocal()
    service = PodcastService(db)

    # 1. 创建任务
    task = await service.create_task(
        user_id=1,
        source_id=42,           # 研究报告 ID
        source_type="research_report",
        target_duration=600,    # 10 分钟
        style="casual",         # 轻松聊天风格
        language="zh"           # 中文
    )

    print(f"任务创建成功: {task.task_id}")

    # 2. 执行流水线 (实际会在后台执行)
    await service.execute_pipeline(task.task_id)

    # 3. 获取结果
    task = await service.get_task(task.task_id, user_id=1)

    if task.status == "completed":
        print(f"播客生成成功!")
        print(f"音频URL: {task.episode.audio_url}")
        print(f"时长: {task.episode.duration} 秒")
        print(f"成本: ${task.cost_usd:.2f}")
    else:
        print(f"生成失败: {task.error_message}")


# 运行示例
import asyncio
asyncio.run(demo_generate_podcast())
```

---

## 8. 成本估算

### 8.1 成本构成

| 组件 | 单价 | 10分钟播客用量 | 成本 |
|------|------|----------------|------|
| **LLM (大纲)** | ¥0.008/1K tokens (Kimi K2) | ~2K tokens | ¥0.016 |
| **LLM (对话)** | ¥0.032/1K tokens (Kimi K2) | ~8K tokens | ¥0.26 |
| **TTS (CosyVoice)** | ~¥0.20/1K chars | ~3K chars | ¥0.60 |
| **存储 (R2)** | $0.015/GB | ~10MB | ¥0.001 |
| **总计** | - | - | **~¥0.88** |

> **成本说明**: CosyVoice 定价 ¥2/万字符，10分钟播客约 3000 字符，TTS 成本约 ¥0.60。

### 8.2 优化策略

```
1. LLM Token 优化
   - 限制源材料长度 (8000 字)
   - 使用 kimi-k2-turbo-preview 生成对话 (高速版)
   - 缓存相似源材料的大纲

2. TTS 成本优化
   - 合并连续同声音段落
   - 使用更短的过渡语
   - 提供"简洁模式"选项

3. 批量优化
   - 百炼平台包月套餐
   - 预购资源包
```

---

## 9. 部署考量

### 9.1 资源需求

| 资源 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB |
| 磁盘 | 20 GB | 50 GB |
| 网络 | 100 Mbps | 1 Gbps |

### 9.2 扩展策略

```
1. 水平扩展
   - 独立部署 TTS Worker
   - 使用 Redis 任务队列
   - 按需扩展 Worker 实例

2. 缓存层
   - 缓存常用声音模型
   - 缓存音频片段 (重复内容)
   - CDN 加速音频分发

3. 降级策略
   - TTS 服务不可用时切换备选
   - 高峰期限制并发生成数
   - 优先队列 (付费用户优先)
```

### 9.3 监控指标

| 指标 | 阈值 | 告警 |
|------|------|------|
| 任务等待时间 | > 5 min | 警告 |
| TTS 延迟 | > 2s/sentence | 警告 |
| 生成失败率 | > 5% | 严重 |
| 每日成本 | > $100 | 警告 |

---

## 附录 A: 依赖安装

```bash
# Python 依赖
pip install dashscope pydub aiofiles

# 系统依赖 (音频处理)
apt-get install ffmpeg

# 或 macOS
brew install ffmpeg
```

## 附录 B: 配置示例

```yaml
# config.yaml

podcast:
  enabled: true

  # 默认配置
  default_duration: 600
  default_style: casual
  default_language: zh

  # 限额
  daily_limit_per_user: 10
  max_duration_seconds: 1800

  # 成本控制
  max_cost_per_episode: 5.0  # 人民币

  # TTS (百炼 CosyVoice)
  tts:
    provider: cosyvoice
    model: cosyvoice-v1
    sample_rate: 22050
    rate_limit: 10  # req/s

  # 存储
  storage:
    bucket: signal-hunter-podcast
    region: auto
```

---

**[PROTOCOL]**: 变更时更新此文档，然后检查 docs/CLAUDE.md
