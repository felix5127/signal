# Input: 网站 URL
# Output: 网站 Favicon URL
# Position: 工具类，用于获取网站图标
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

from urllib.parse import urlparse
from typing import Optional


class FaviconFetcher:
    """获取网站 Favicon 的工具类"""

    @staticmethod
    def get_favicon(url: str, size: int = 64) -> str:
        """
        获取网站的 Favicon URL

        使用 DuckDuckGo 的 favicon 服务（稳定可靠）

        Args:
            url: 网站 URL
            size: 图标尺寸（默认 64x64）

        Returns:
            Favicon URL
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc

            if not domain:
                return ""

            # DuckDuckGo Favicon Service（推荐，速度快）
            ddg_favicon = f"https://icons.duckduckgo.com/ip3/{domain}.ico"

            return ddg_favicon

        except Exception as e:
            print(f"Error parsing URL {url}: {e}")
            return ""

    @staticmethod
    def get_google_favicon(url: str, size: int = 64) -> str:
        """
        使用 Google 服务获取 Favicon（备用方案）

        Args:
            url: 网站 URL
            size: 图标尺寸

        Returns:
            Favicon URL
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc

            if not domain:
                return ""

            # Google Favicon Service
            google_favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz={size}"

            return google_favicon

        except Exception as e:
            print(f"Error parsing URL {url}: {e}")
            return ""

    @staticmethod
    def get_favicon_with_fallback(url: str, size: int = 64) -> str:
        """
        获取 Favicon，带降级方案

        优先使用 DuckDuckGo，失败时使用 Google

        Args:
            url: 网站 URL
            size: 图标尺寸

        Returns:
            Favicon URL
        """
        favicon_url = FaviconFetcher.get_favicon(url, size)

        # 如果 DuckDuckGo 失败，使用 Google
        if not favicon_url:
            favicon_url = FaviconFetcher.get_google_favicon(url, size)

        return favicon_url
