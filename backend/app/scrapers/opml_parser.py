# Input: OPML 文件路径 (XML 格式的 RSS 订阅列表)
# Output: 解析后的 RSS 源列表 [{"name": str, "url": str, "type": str, "username"?: str}]
# Position: 数据采集层的辅助模块，为 RSS Scraper 和 XGoing Scraper 提供订阅源解析能力
# 更新提醒: 一旦我被更新，务必更新开头注释及所属文件夹的 README.md

"""
OPML 解析器模块

解析 BestBlogs 提供的 OPML 订阅文件，提取 RSS 源信息。
支持以下文件:
- BestBlogs_RSS_Articles.opml (文章源)
- BestBlogs_RSS_Podcasts.opml (播客源)
- BestBlogs_RSS_Videos.opml (视频源)
- BestBlogs_RSS_Twitters.opml (Twitter 账号, 通过 XGo.ing 服务)
"""

import os
import re
import logging
from typing import List, Dict, Optional
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError

logger = logging.getLogger(__name__)


class OPMLParseError(Exception):
    """OPML 解析错误"""
    pass


def parse_opml(file_path: str, feed_type: Optional[str] = None) -> List[Dict[str, str]]:
    """
    解析 OPML 文件，返回 RSS 源列表

    Args:
        file_path: OPML 文件的绝对或相对路径
        feed_type: 源类型，如果为 None 则从文件名推断
                   可选值: article, podcast, video, twitter

    Returns:
        RSS 源列表，每个源包含:
        - name: 源名称
        - url: RSS 订阅 URL
        - type: 源类型 (article/podcast/video/twitter)

    Raises:
        OPMLParseError: 文件不存在、格式错误或解析失败

    Examples:
        >>> feeds = parse_opml("BestBlog/BestBlogs_RSS_Articles.opml")
        >>> print(feeds[0])
        {'name': '人人都是产品经理', 'url': 'https://...', 'type': 'article'}
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise OPMLParseError(f"OPML 文件不存在: {file_path}")

    # 推断源类型
    if feed_type is None:
        feed_type = _infer_type_from_filename(file_path)

    try:
        # 先读取文件内容到字符串，避免 macOS Docker 挂载时的 ElementTree 锁问题
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        root = ElementTree.fromstring(content)
    except ParseError as e:
        raise OPMLParseError(f"OPML 格式错误: {e}")
    except Exception as e:
        raise OPMLParseError(f"读取 OPML 文件失败: {e}")

    feeds = []

    # 递归查找所有 outline 元素（支持嵌套结构）
    for outline in root.iter('outline'):
        feed = _parse_outline(outline, feed_type)
        if feed:
            feeds.append(feed)

    logger.info(f"解析 OPML 完成: {file_path}, 共 {len(feeds)} 个源")
    return feeds


def _extract_twitter_username(name: str) -> Optional[str]:
    """
    从 OPML name 字段提取 Twitter 用户名

    Args:
        name: OPML 中的名称，格式如 "OpenAI(@OpenAI)" 或 "宝玉(@dotey)"

    Returns:
        用户名 (不带@)，如 "OpenAI" 或 "dotey"，提取失败返回 None
    """
    if not name:
        return None

    # 匹配 (@username) 模式
    match = re.search(r'\(@([^)]+)\)', name)
    if match:
        return match.group(1)

    return None


def _parse_outline(outline: ElementTree.Element, feed_type: str) -> Optional[Dict[str, str]]:
    """
    解析单个 outline 元素

    Args:
        outline: XML outline 元素
        feed_type: 源类型

    Returns:
        解析后的源信息字典，如果不是有效的 RSS 源则返回 None
        对于 Twitter 类型，额外包含 'username' 字段
    """
    # 获取 RSS URL (xmlUrl 是标准属性名)
    xml_url = outline.get('xmlUrl')
    if not xml_url:
        # 没有 xmlUrl 的是分类节点，跳过
        return None

    # 获取名称 (优先使用 text，其次 title)
    name = outline.get('text') or outline.get('title') or ''
    name = name.strip()

    # 如果名称为空，尝试从 URL 推断
    if not name:
        name = _extract_name_from_url(xml_url)

    result = {
        'name': name,
        'url': xml_url,
        'type': feed_type
    }

    # 对于 Twitter 类型，提取用户名
    if feed_type == 'twitter':
        username = _extract_twitter_username(name)
        if username:
            result['username'] = username

    return result


def _infer_type_from_filename(file_path: str) -> str:
    """
    从文件名推断源类型

    Args:
        file_path: 文件路径

    Returns:
        源类型: article, podcast, video, twitter
    """
    filename = os.path.basename(file_path).lower()

    if 'article' in filename:
        return 'article'
    elif 'podcast' in filename:
        return 'podcast'
    elif 'video' in filename:
        return 'video'
    elif 'twitter' in filename:
        return 'twitter'
    else:
        # 默认为文章类型
        return 'article'


def _extract_name_from_url(url: str) -> str:
    """
    从 URL 提取源名称（作为备选方案）

    Args:
        url: RSS 订阅 URL

    Returns:
        提取的名称
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        # 取域名的第一部分作为名称
        domain = parsed.netloc.split('.')[0]
        return domain if domain else 'Unknown'
    except Exception:
        return 'Unknown'


def parse_all_opml_files(base_dir: str = "BestBlog") -> Dict[str, List[Dict[str, str]]]:
    """
    解析所有 BestBlogs OPML 文件

    Args:
        base_dir: OPML 文件所在目录

    Returns:
        按类型分组的源列表:
        {
            'article': [...],
            'podcast': [...],
            'video': [...],
            'twitter': [...]
        }
    """
    opml_files = {
        'article': 'BestBlogs_RSS_Articles.opml',
        'podcast': 'BestBlogs_RSS_Podcasts.opml',
        'video': 'BestBlogs_RSS_Videos.opml',
        'twitter': 'BestBlogs_RSS_Twitters.opml'
    }

    result = {}

    for feed_type, filename in opml_files.items():
        file_path = os.path.join(base_dir, filename)
        try:
            feeds = parse_opml(file_path, feed_type)
            result[feed_type] = feeds
            logger.info(f"已加载 {feed_type} 源: {len(feeds)} 个")
        except OPMLParseError as e:
            logger.warning(f"解析 {filename} 失败: {e}")
            result[feed_type] = []

    return result


def get_all_feeds(base_dir: str = "BestBlog") -> List[Dict[str, str]]:
    """
    获取所有 OPML 文件中的全部 RSS 源

    Args:
        base_dir: OPML 文件所在目录

    Returns:
        所有源的合并列表
    """
    all_feeds = parse_all_opml_files(base_dir)

    merged = []
    for feeds in all_feeds.values():
        merged.extend(feeds)

    logger.info(f"共加载 {len(merged)} 个 RSS 源")
    return merged


# 便捷函数：按类型获取源
def get_article_feeds(base_dir: str = "BestBlog") -> List[Dict[str, str]]:
    """获取所有文章源"""
    file_path = os.path.join(base_dir, "BestBlogs_RSS_Articles.opml")
    return parse_opml(file_path, "article")


def get_podcast_feeds(base_dir: str = "BestBlog") -> List[Dict[str, str]]:
    """获取所有播客源"""
    file_path = os.path.join(base_dir, "BestBlogs_RSS_Podcasts.opml")
    return parse_opml(file_path, "podcast")


def get_video_feeds(base_dir: str = "BestBlog") -> List[Dict[str, str]]:
    """获取所有视频源"""
    file_path = os.path.join(base_dir, "BestBlogs_RSS_Videos.opml")
    return parse_opml(file_path, "video")


def get_twitter_feeds(base_dir: str = "BestBlog") -> List[Dict[str, str]]:
    """获取所有 Twitter 源"""
    file_path = os.path.join(base_dir, "BestBlogs_RSS_Twitters.opml")
    return parse_opml(file_path, "twitter")


if __name__ == "__main__":
    # 测试代码
    import sys

    logging.basicConfig(level=logging.INFO)

    # 确定项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "../../../"))
    base_dir = os.path.join(project_root, "BestBlog")

    print(f"项目根目录: {project_root}")
    print(f"OPML 目录: {base_dir}")
    print("-" * 50)

    # 测试解析各个文件
    try:
        articles = get_article_feeds(base_dir)
        print(f"文章源: {len(articles)} 个")
        if articles:
            print(f"  示例: {articles[0]}")
    except OPMLParseError as e:
        print(f"文章源解析失败: {e}")

    try:
        podcasts = get_podcast_feeds(base_dir)
        print(f"播客源: {len(podcasts)} 个")
        if podcasts:
            print(f"  示例: {podcasts[0]}")
    except OPMLParseError as e:
        print(f"播客源解析失败: {e}")

    try:
        videos = get_video_feeds(base_dir)
        print(f"视频源: {len(videos)} 个")
        if videos:
            print(f"  示例: {videos[0]}")
    except OPMLParseError as e:
        print(f"视频源解析失败: {e}")

    try:
        twitters = get_twitter_feeds(base_dir)
        print(f"Twitter 源: {len(twitters)} 个")
        if twitters:
            print(f"  示例: {twitters[0]}")
    except OPMLParseError as e:
        print(f"Twitter 源解析失败: {e}")

    print("-" * 50)
    print("解析测试完成！")
