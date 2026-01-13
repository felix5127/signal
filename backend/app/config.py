# Input: config.yaml, 环境变量 (.env)
# Output: 全局配置对象
# Position: 配置中心，为所有模块提供配置参数
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import os
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class HackerNewsConfig(BaseSettings):
    """Hacker News 数据源配置"""
    enabled: bool = True
    score_threshold: int = 80
    keywords: List[str] = Field(
        default_factory=lambda: ["AI", "LLM", "GPT", "ML", "model", "neural"]
    )
    max_items: int = 500


class GitHubConfig(BaseSettings):
    """GitHub 数据源配置"""
    enabled: bool = False
    min_stars_today: int = 50
    max_items: int = 100
    languages: List[str] = Field(
        default_factory=lambda: ["Python", "JavaScript", "TypeScript", "Rust", "Go", "Java"]
    )
    exclude_patterns: List[str] = Field(
        default_factory=lambda: ["awesome-", "cheatsheet", "tutorial-", "learn-", "resources"]
    )
    orgs_whitelist: List[str] = Field(
        default_factory=lambda: ["openai", "anthropics", "google", "meta-llama", "microsoft"]
    )


class HuggingFaceConfig(BaseSettings):
    """Hugging Face 数据源配置"""
    enabled: bool = False
    min_likes: int = 10
    min_downloads: int = 100
    max_items: int = 50  # 每次抓取最大条数
    tasks: List[str] = Field(
        default_factory=lambda: ["text-generation", "image-generation", "text-to-image"]
    )


class TwitterConfig(BaseSettings):
    """Twitter 数据源配置 (XGo.ing 服务)"""
    enabled: bool = False
    accounts: List[str] = Field(default_factory=list)  # 兼容旧配置，可手动指定账号
    keywords: List[str] = Field(
        default_factory=lambda: ["AI", "LLM", "GPT", "ML", "model"]
    )
    max_items_per_account: int = 10
    # XGo.ing 相关配置
    use_xgoing: bool = True  # 是否使用 XGo.ing 服务 (从 OPML 读取)
    opml_path: str = "BestBlog/BestBlogs_RSS_Twitters.opml"  # Twitter OPML 文件路径


class ArXivConfig(BaseSettings):
    """ArXiv 数据源配置"""
    enabled: bool = False
    categories: List[str] = Field(
        default_factory=lambda: ["cs.AI", "cs.LG", "cs.CL", "cs.CV"]
    )
    keywords: List[str] = Field(
        default_factory=lambda: ["LLM", "GPT", "transformer"]
    )
    days_back: int = 7
    max_results: int = 50


class ProductHuntConfig(BaseSettings):
    """Product Hunt 数据源配置"""
    enabled: bool = False
    min_upvotes: int = 100
    categories: List[str] = Field(
        default_factory=lambda: ["AI", "Developer Tools", "Productivity"]
    )
    days_back: int = 7
    max_results: int = 50


class BlogConfig(BaseSettings):
    """博客/文章 RSS 数据源配置"""
    enabled: bool = False
    opml_path: str = "/app/BestBlog/BestBlogs_RSS_Articles.opml"  # OPML 文件路径
    feeds: List[str] = Field(default_factory=list)  # RSS feed URL 列表（可选，OPML优先）
    keywords: List[str] = Field(
        default_factory=lambda: ["AI", "LLM", "GPT"]
    )
    max_items_per_feed: int = 3  # 每个 feed 最多 3 条，16 源 × 3 = 48 篇/次

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # 允许额外字段


class PodcastConfig(BaseSettings):
    """播客数据源配置"""
    enabled: bool = True  # 启用播客抓取
    opml_path: str = "/app/BestBlog/BestBlogs_RSS_Podcasts.opml"  # OPML 文件路径
    max_items_per_feed: int = 2  # 每个 feed 最多抓取条目数（控制每日总量）
    max_duration_seconds: int = 7200  # 最大音频时长（秒），默认 2 小时
    transcribe_enabled: bool = True  # 是否启用转写
    max_daily_items: int = 5  # 每日最多处理播客数（控制转写成本）

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # 允许额外字段


class VideoConfig(BaseSettings):
    """视频数据源配置"""
    enabled: bool = True  # 启用视频抓取
    opml_path: str = "/app/BestBlog/BestBlogs_RSS_Videos.opml"  # OPML 文件路径
    max_items_per_feed: int = 1  # 每个 feed 最多抓取条目数（控制每日总量）
    max_duration_seconds: int = 7200  # 最大视频时长（秒），默认 2 小时
    transcribe_enabled: bool = True  # 是否启用转写
    max_daily_items: int = 2  # 每日最多处理视频数（控制转写成本）
    # YouTube 特殊配置
    prefer_youtube_thumbnails: bool = True  # 是否使用 YouTube 高清缩略图

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # 允许额外字段


class TingwuConfig(BaseSettings):
    """通义听悟（Tingwu）配置"""
    api_key: str = Field(default="", alias="TINGWU_API_KEY")
    app_key: str = Field(default="", alias="TINGWU_APP_KEY")
    # API 端点
    base_url: str = "https://tingwu.aliyuncs.com"
    # 轮询配置
    poll_interval: int = 5  # 轮询间隔（秒）
    max_poll_attempts: int = 360  # 最大轮询次数（5秒 * 360 = 30分钟）
    # 转写配置
    language: str = "auto"  # 语言：auto/zh/en
    speaker_count: int = 2  # 说话人数量（用于区分不同说话人）

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class LLMConfig(BaseSettings):
    """LLM 配置"""
    provider: str = Field(default="openai", alias="LLM_PROVIDER")
    model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    base_url: Optional[str] = Field(default=None, alias="LLM_BASE_URL")  # 自定义API端点(OpenRouter/Ollama等)
    timeout: int = Field(default=30, alias="LLM_TIMEOUT")
    max_tokens: int = Field(default=8000, alias="LLM_MAX_TOKENS")
    temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    daily_token_limit: int = Field(default=5000000, alias="LLM_DAILY_TOKEN_LIMIT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @classmethod
    def __init_subclass__(cls):
        """Pydantic v2 兼容的初始化"""
        super().__init_subclass__()

    def model_post_init(self, __context) -> None:
        """模型初始化后自动去除字符串字段的前导/尾随空格"""
        if isinstance(self.provider, str):
            self.provider = self.provider.strip()
        if isinstance(self.model, str):
            self.model = self.model.strip()
        if isinstance(self.base_url, str):
            self.base_url = self.base_url.strip()


class OutputConfig(BaseSettings):
    """输出配置"""
    max_daily_items: int = 500
    summary_max_length: int = 200
    min_score: int = 3


class FilterConfig(BaseSettings):
    """过滤配置"""
    rule_filter_first: bool = True
    llm_filter_enabled: bool = True
    dedup_enabled: bool = True
    similarity_threshold: float = 0.7


class DeepResearchConfig(BaseSettings):
    """Deep Research 配置"""
    search_provider: str = "tavily"
    max_questions: int = 3
    max_searches_per_question: int = 2
    report_max_tokens: int = 2000
    max_cost_per_report: float = 0.10
    max_reports_per_day: int = 10
    cache_duration_hours: int = 24


class ScheduleConfig(BaseSettings):
    """定时任务配置"""
    interval_hours: int = 1


class RedisConfig(BaseSettings):
    """Redis 缓存配置"""
    enabled: bool = True
    url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    # 缓存过期时间（秒）
    ttl_resources_list: int = 300  # 5分钟
    ttl_resource_detail: int = 600  # 10分钟
    ttl_stats: int = 60  # 1分钟
    ttl_tags: int = 1800  # 30分钟
    # 缓存键前缀（避免多环境冲突）
    key_prefix: str = "signal:"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # 允许额外字段（兼容 yaml 配置）


class AppConfig(BaseSettings):
    """全局配置"""
    # 环境变量
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    producthunt_api_key: str = Field(default="", alias="PRODUCTHUNT_API_KEY")
    database_url: str = Field(
        default="sqlite:///./data/signals.db", alias="DATABASE_URL"
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Redis 缓存配置
    redis: RedisConfig = Field(default_factory=RedisConfig)

    # 子配置（从 config.yaml 加载）
    hackernews: HackerNewsConfig = Field(default_factory=HackerNewsConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    huggingface: HuggingFaceConfig = Field(default_factory=HuggingFaceConfig)
    twitter: TwitterConfig = Field(default_factory=TwitterConfig)
    arxiv: ArXivConfig = Field(default_factory=ArXivConfig)
    producthunt: ProductHuntConfig = Field(default_factory=ProductHuntConfig)
    blog: BlogConfig = Field(default_factory=BlogConfig)
    podcast: PodcastConfig = Field(default_factory=PodcastConfig)
    video: VideoConfig = Field(default_factory=VideoConfig)
    tingwu: TingwuConfig = Field(default_factory=TingwuConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    filter: FilterConfig = Field(default_factory=FilterConfig)
    deep_research: DeepResearchConfig = Field(default_factory=DeepResearchConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **data):
        """初始化时自动去除环境变量的前导/尾随空格"""
        # 去除字符串字段的空格
        for key in ["openai_api_key", "github_token", "tavily_api_key", "database_url", "log_level"]:
            if key in data and isinstance(data[key], str):
                data[key] = data[key].strip()
        super().__init__(**data)


def load_config() -> AppConfig:
    """
    加载配置文件和环境变量

    优先级：环境变量 > config.yaml
    """
    # 1. 先从环境变量加载基础配置
    config = AppConfig()

    # 2. 尝试加载 config.yaml
    config_path = Path("config.yaml")
    if not config_path.exists():
        # Docker 环境中可能在上级目录
        config_path = Path("../config.yaml")

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f)

            # 合并 YAML 配置到 Pydantic 模型
            if yaml_config:
                if "sources" in yaml_config:
                    sources = yaml_config["sources"]
                    if "hackernews" in sources:
                        config.hackernews = HackerNewsConfig(**sources["hackernews"])
                    if "github" in sources:
                        config.github = GitHubConfig(**sources["github"])
                    if "huggingface" in sources:
                        config.huggingface = HuggingFaceConfig(**sources["huggingface"])
                    if "twitter" in sources:
                        config.twitter = TwitterConfig(**sources["twitter"])
                    if "arxiv" in sources:
                        config.arxiv = ArXivConfig(**sources["arxiv"])
                    if "producthunt" in sources:
                        config.producthunt = ProductHuntConfig(**sources["producthunt"])
                    if "blog" in sources:
                        config.blog = BlogConfig(**sources["blog"])
                    if "podcast" in sources:
                        config.podcast = PodcastConfig(**sources["podcast"])
                    if "video" in sources:
                        config.video = VideoConfig(**sources["video"])
                # 通义听悟配置（从 yaml 或环境变量加载）
                if "tingwu" in yaml_config:
                    config.tingwu = TingwuConfig(**yaml_config["tingwu"])
                # ❌ 删除: LLM配置现在完全从环境变量读取 (LLM_PROVIDER, LLM_MODEL等)
                # if "llm" in yaml_config:
                #     config.llm = LLMConfig(**yaml_config["llm"])
                if "output" in yaml_config:
                    config.output = OutputConfig(**yaml_config["output"])
                if "filter" in yaml_config:
                    config.filter = FilterConfig(**yaml_config["filter"])
                if "deep_research" in yaml_config:
                    config.deep_research = DeepResearchConfig(**yaml_config["deep_research"])
                if "schedule" in yaml_config:
                    config.schedule = ScheduleConfig(**yaml_config["schedule"])
                # Redis 缓存配置
                if "redis" in yaml_config:
                    config.redis = RedisConfig(**yaml_config["redis"])

    # 3. 环境变量覆盖 Redis URL（Docker 部署需要）
    import os
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        if not hasattr(config, 'redis') or config.redis is None:
            config.redis = RedisConfig()
        config.redis.url = redis_url

    return config


# 全局配置实例
config = load_config()
