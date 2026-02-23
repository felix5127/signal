// 全局常量定义
// 来源名称映射 - 所有组件共用的单一真相源

export const SOURCE_NAMES: Record<string, string> = {
  // 技术社区
  hn: 'Hacker News',
  github: 'GitHub',
  huggingface: 'Hugging Face',
  arxiv: 'ArXiv',
  producthunt: 'Product Hunt',

  // 社交媒体
  twitter: 'Twitter / X',

  // 视频平台
  youtube: 'YouTube',
  bilibili: 'Bilibili',
  vimeo: 'Vimeo',

  // 音频平台
  spotify: 'Spotify',
  apple_podcasts: 'Apple Podcasts',

  // AI 公司
  openai: 'OpenAI',

  // 通用类型
  blog: '博客',
  podcast: '播客',

  // 播客节目名（直接映射）
  'Lex Fridman Podcast': 'Lex Fridman Podcast',
  '硅谷早知道': '硅谷早知道',
  'AI 技术前沿': 'AI 技术前沿',
}
