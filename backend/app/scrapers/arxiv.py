# Input: ArXiv API (https://export.arxiv.org/api/query)
# Output: RawSignal 列表(最新AI相关论文)
# Position: ArXiv数据源爬虫,实现规则预筛(分类+关键词)
# 更新提醒:一旦我被更新,务必更新我的开头注释,以及所属的文件夹的md

from datetime import datetime, timedelta
from typing import List, Optional
import httpx
import xml.etree.ElementTree as ET

from app.config import config
from app.scrapers.base import BaseScraper, RawSignal


class ArXivScraper(BaseScraper):
    """
    ArXiv 论文爬虫

    数据源:ArXiv API (完全免费,无需API key)
    规则预筛:
    1. 分类过滤(cs.AI, cs.LG, cs.CL, cs.CV等)
    2. 关键词匹配(LLM, GPT, transformer等)
    3. 时间过滤(最近N天)

    ArXiv API是完全免费的学术资源
    """

    BASE_URL = "https://export.arxiv.org/api/query"

    def __init__(self):
        super().__init__(source_name="arxiv")
        self.categories = config.arxiv.categories
        self.keywords = [kw.lower() for kw in config.arxiv.keywords]
        self.max_results = config.arxiv.max_results
        self.days_back = config.arxiv.days_back

    def _build_search_query(self) -> str:
        """
        构建ArXiv API搜索查询

        Returns:
            搜索查询字符串
        """
        # 分类查询: cat:cs.AI OR cat:cs.LG OR cat:cs.CL
        category_query = " OR ".join([f"cat:{cat}" for cat in self.categories])

        # 关键词查询: all:LLM OR all:GPT OR all:transformer
        keyword_query = " OR ".join([f"all:{kw}" for kw in self.keywords])

        # 组合查询
        if self.keywords:
            return f"({category_query}) AND ({keyword_query})"
        else:
            return category_query

    def _matches_keywords(self, text: str) -> bool:
        """
        检查标题/摘要是否包含关键词

        Args:
            text: 标题或摘要

        Returns:
            是否匹配
        """
        if not self.keywords:
            return True

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)

    def _is_recent(self, published_date: datetime) -> bool:
        """
        检查论文是否在最近N天内发布

        Args:
            published_date: 发布日期

        Returns:
            是否为最近论文
        """
        from datetime import timezone
        # 使用UTC时间进行比较，确保时区一致
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_back)
        # 如果 published_date 没有时区信息，假设为 UTC
        if published_date.tzinfo is None:
            published_date = published_date.replace(tzinfo=timezone.utc)
        return published_date >= cutoff_date

    def _parse_arxiv_response(self, xml_content: str) -> List[dict]:
        """
        解析ArXiv API响应XML

        Args:
            xml_content: XML内容

        Returns:
            论文列表
        """
        papers = []

        try:
            root = ET.fromstring(xml_content)

            # Atom feed命名空间
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom",
            }

            # 解析每个entry
            for entry in root.findall("atom:entry", ns):
                title_elem = entry.find("atom:title", ns)
                summary_elem = entry.find("atom:summary", ns)
                published_elem = entry.find("atom:published", ns)
                updated_elem = entry.find("atom:updated", ns)
                id_elem = entry.find("atom:id", ns)

                # 提取作者
                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None:
                        authors.append(name_elem.text)

                # 提取分类
                categories = []
                for category in entry.findall("atom:category", ns):
                    term = category.get("term")
                    if term:
                        categories.append(term)

                # 提取PDF链接
                pdf_link = None
                for link in entry.findall("atom:link", ns):
                    if link.get("title") == "pdf":
                        pdf_link = link.get("href")
                        break

                if title_elem is None or id_elem is None:
                    continue

                # ArXiv ID (从URL中提取)
                # URL格式: http://arxiv.org/abs/2501.12345v1
                arxiv_id = id_elem.text.split("/")[-1] if "/" in id_elem.text else ""

                papers.append(
                    {
                        "title": title_elem.text.strip() if title_elem.text else "",
                        "summary": summary_elem.text.strip()
                        if summary_elem is not None and summary_elem.text
                        else "",
                        "published": published_elem.text
                        if published_elem is not None
                        else None,
                        "updated": updated_elem.text if updated_elem is not None else None,
                        "arxiv_id": arxiv_id,
                        "url": id_elem.text,
                        "pdf_url": pdf_link,
                        "authors": authors,
                        "categories": categories,
                    }
                )

        except Exception as e:
            print(f"[ArXiv] Failed to parse API response: {e}")

        return papers

    def _convert_to_raw_signal(self, paper: dict) -> RawSignal:
        """
        转换论文为RawSignal

        Args:
            paper: 论文数据

        Returns:
            RawSignal对象
        """
        # 解析发布时间
        created_at = None
        if paper.get("published"):
            try:
                # ArXiv格式: "2025-12-31T10:00:00Z"
                created_at = datetime.fromisoformat(
                    paper["published"].replace("Z", "+00:00")
                )
            except Exception as e:
                print(f"[ArXiv] Failed to parse timestamp: {e}")

        # 构建标题(包含主要作者)
        title = paper["title"]
        if paper.get("authors"):
            first_author = paper["authors"][0].split()[-1]  # 取姓氏
            title = f"{title} ({first_author} et al.)"

        return RawSignal(
            source=self.source_name,
            source_id=paper["arxiv_id"],
            url=paper["url"],
            title=title,
            content=paper["summary"],
            source_created_at=created_at,
            metadata={
                "arxiv_id": paper["arxiv_id"],
                "pdf_url": paper.get("pdf_url", ""),
                "authors": paper.get("authors", []),
                "categories": paper.get("categories", []),
                "updated": paper.get("updated", ""),
            },
        )

    async def scrape(self) -> List[RawSignal]:
        """
        抓取ArXiv最新论文

        流程:
        1. 构建搜索查询(分类+关键词)
        2. 调用ArXiv API获取结果
        3. 规则预筛(时间+关键词)
        4. 转换为RawSignal

        Returns:
            RawSignal列表(已通过规则预筛)
        """
        signals = []

        async with httpx.AsyncClient() as client:
            try:
                # 构建查询
                search_query = self._build_search_query()
                print(f"[ArXiv] Search query: {search_query}")

                # API参数
                params = {
                    "search_query": search_query,
                    "start": 0,
                    "max_results": self.max_results,
                    "sortBy": "submittedDate",  # 按提交日期排序
                    "sortOrder": "descending",  # 降序(最新在前)
                }

                # 调用API
                resp = await client.get(self.BASE_URL, params=params, timeout=30.0)
                resp.raise_for_status()
                xml_content = resp.text

                # 解析响应
                papers = self._parse_arxiv_response(xml_content)
                print(f"[ArXiv] Found {len(papers)} papers")

                # 规则预筛
                filtered_count = 0
                for paper in papers:
                    # 时间过滤
                    if paper.get("published"):
                        try:
                            pub_date = datetime.fromisoformat(
                                paper["published"].replace("Z", "+00:00")
                            )
                            if not self._is_recent(pub_date):
                                continue
                        except Exception:
                            continue

                    # 关键词二次确认(API查询已包含关键词,这里再确认一次)
                    full_text = f"{paper.get('title', '')} {paper.get('summary', '')}"
                    if not self._matches_keywords(full_text):
                        continue

                    signal = self._convert_to_raw_signal(paper)
                    signals.append(signal)
                    filtered_count += 1

                print(
                    f"[ArXiv] {filtered_count}/{len(papers)} papers passed filter "
                    f"(filter rate: {(1 - filtered_count/len(papers))*100:.1f}%)"
                )

            except Exception as e:
                print(f"[ArXiv] Scraping failed: {e}")

        return signals
