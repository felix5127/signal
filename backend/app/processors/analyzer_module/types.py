# 数据结构定义
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class MainPoint:
    """主要观点"""
    point: str
    explanation: str

@dataclass
class AnalysisResult:
    """分析结果"""
    one_sentence_summary: str
    summary: str
    domain: str
    subdomain: str = None
    tags: List[str] = field(default_factory=list)
    main_points: List[MainPoint] = field(default_factory=list)
    key_quotes: List[str] = field(default_factory=list)
    score: int = 0
    improvements: str = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "oneSentenceSummary": self.one_sentence_summary,
            "summary": self.summary,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "tags": self.tags,
            "mainPoints": [{"point": p.point, "explanation": p.explanation} for p in self.main_points],
            "keyQuotes": self.key_quotes,
            "score": self.score,
            "improvements": self.improvements
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisResult":
        main_points = [
            MainPoint(point=p.get("point", ""), explanation=p.get("explanation", ""))
            for p in data.get("mainPoints", [])
        ]
        return cls(
            one_sentence_summary=data.get("oneSentenceSummary", ""),
            summary=data.get("summary", ""),
            domain=data.get("domain", ""),
            subdomain=data.get("aiSubcategory") or data.get("subdomain"),
            tags=data.get("tags", []),
            main_points=main_points,
            key_quotes=data.get("keyQuotes", []),
            score=data.get("score", 0),
            improvements=data.get("improvements")
        )
