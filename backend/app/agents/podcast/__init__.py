"""
[INPUT]: cosyvoice_client, outline_agent, dialogue_agent, synthesizer 模块
[OUTPUT]: 导出播客生成服务
[POS]: podcast 包入口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from app.agents.podcast.cosyvoice_client import CosyVoiceClient, cosyvoice_client
from app.agents.podcast.outline_agent import OutlineAgent
from app.agents.podcast.dialogue_agent import DialogueAgent
from app.agents.podcast.synthesizer import PodcastSynthesizer, podcast_synthesizer

__all__ = [
    "CosyVoiceClient",
    "cosyvoice_client",
    "OutlineAgent",
    "DialogueAgent",
    "PodcastSynthesizer",
    "podcast_synthesizer",
]
