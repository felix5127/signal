# design/
> L2 | 父级: ../CLAUDE.md

## 职责
技术设计方案文档目录，存放各模块的详细技术设计文档。

## 成员清单
FRONTEND_COMPONENTS.md: 研究助手前端组件技术方案，三栏布局/核心组件/SSE流式/状态管理
AGENT_SYSTEM.md: Agent 系统技术方案 - DeepAgents 集成/Middleware/PostgresBackend/Tools/Skills 设计
MULTIMODAL_PROCESSING.md: 多模态处理技术方案 - 听悟 音频转写 + 通义千问 Omni 视频理解 (可选) + FFmpeg/yt-dlp 预处理
PODCAST_GENERATION.md: 播客生成技术方案 - OutlineAgent/DialogueAgent 双Agent架构 + 百炼 CosyVoice TTS 集成 + 多角色对话策略 + Skill 设计

## 设计规范

### 文档结构
1. 目录索引
2. 架构设计 (布局/层级)
3. 组件接口定义 (Props/Types)
4. Hook 设计 (输入/输出/副作用)
5. 状态管理 (Store 结构)
6. 代码示例 (TypeScript/React)

### 命名规范
- 文件名: `{MODULE}_COMPONENTS.md` / `{MODULE}_API.md` / `{MODULE}_ARCHITECTURE.md`
- 使用大写下划线命名

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
