#!/usr/bin/env python3
"""
播客和视频测试数据种子脚本

用法:
    # 在项目根目录执行
    cd backend && python -m scripts.seed_test_data

    # 或者在 Docker 容器中执行
    docker exec -it signal-backend python -m scripts.seed_test_data
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.resource import Resource
from app.models.source import Source  # Required for foreign key resolution


# ============================================================
# 播客测试数据 (5条)
# ============================================================

PODCAST_DATA = [
    {
        "title": "与 Andrej Karpathy 对谈：AI 教育的未来",
        "source_name": "Lex Fridman Podcast",
        "one_sentence_summary": "前 Tesla AI 总监深度解析 AI 如何重塑教育模式",
        "one_sentence_summary_zh": "前 Tesla AI 总监深度解析 AI 如何重塑教育模式",
        "summary": "本期节目邀请到 Andrej Karpathy，深入探讨了 AI 在教育领域的应用前景。Karpathy 分享了他创办 AI 教育平台的初衷，讨论了大语言模型如何个性化学习体验，以及未来教育可能的演变方向。他认为 AI 将成为每个人的私人导师，但同时强调人类教师的创造力和情感连接不可替代。",
        "summary_zh": "本期节目邀请到 Andrej Karpathy，深入探讨了 AI 在教育领域的应用前景。Karpathy 分享了他创办 AI 教育平台的初衷，讨论了大语言模型如何个性化学习体验，以及未来教育可能的演变方向。他认为 AI 将成为每个人的私人导师，但同时强调人类教师的创造力和情感连接不可替代。",
        "audio_url": "https://example.com/podcasts/karpathy-ai-education.mp3",
        "duration": 7200,  # 2小时
        "domain": "人工智能",
        "tags": ["AI", "教育", "LLM", "深度学习"],
        "score": 92,
        "is_featured": True,
        "featured_reason_zh": "顶级 AI 专家深度访谈，洞见未来教育趋势",
    },
    {
        "title": "深度学习框架演进史：从 TensorFlow 到 PyTorch",
        "source_name": "AI 技术前沿",
        "one_sentence_summary": "回顾深度学习框架十年发展历程，解析技术选型背后的权衡",
        "one_sentence_summary_zh": "回顾深度学习框架十年发展历程，解析技术选型背后的权衡",
        "summary": "本期播客邀请三位资深机器学习工程师，共同回顾深度学习框架从 Caffe、Theano 到 TensorFlow、PyTorch 的演进历程。嘉宾们分享了各自在不同框架下的实战经验，讨论了静态图 vs 动态图的优劣，以及 JAX 等新框架的崛起对行业的影响。",
        "summary_zh": "本期播客邀请三位资深机器学习工程师，共同回顾深度学习框架从 Caffe、Theano 到 TensorFlow、PyTorch 的演进历程。嘉宾们分享了各自在不同框架下的实战经验，讨论了静态图 vs 动态图的优劣，以及 JAX 等新框架的崛起对行业的影响。",
        "audio_url": "https://example.com/podcasts/dl-framework-history.mp3",
        "duration": 5400,  # 1.5小时
        "domain": "机器学习",
        "tags": ["PyTorch", "TensorFlow", "深度学习", "框架"],
        "score": 85,
        "is_featured": True,
        "featured_reason_zh": "技术选型必听，理解框架演进的底层逻辑",
    },
    {
        "title": "创业者访谈：如何用 AI 重塑传统行业",
        "source_name": "创业内幕",
        "one_sentence_summary": "三位 AI 创业者分享在传统行业落地 AI 的实战经验",
        "one_sentence_summary_zh": "三位 AI 创业者分享在传统行业落地 AI 的实战经验",
        "summary": "本期节目采访了三位正在用 AI 改变传统行业的创业者：一位在做农业 AI，用计算机视觉优化作物种植；一位在做法律 AI，用 NLP 自动化合同审核；还有一位在做制造业 AI，用预测性维护减少设备故障。他们分享了从技术到市场的完整创业历程。",
        "summary_zh": "本期节目采访了三位正在用 AI 改变传统行业的创业者：一位在做农业 AI，用计算机视觉优化作物种植；一位在做法律 AI，用 NLP 自动化合同审核；还有一位在做制造业 AI，用预测性维护减少设备故障。他们分享了从技术到市场的完整创业历程。",
        "audio_url": "https://example.com/podcasts/ai-startup-traditional.mp3",
        "duration": 4800,  # 1小时20分
        "domain": "创业",
        "tags": ["创业", "AI", "传统行业", "产品"],
        "score": 78,
        "is_featured": False,
    },
    {
        "title": "技术播客圆桌：2025 年最值得关注的 AI 趋势",
        "source_name": "硅谷早知道",
        "one_sentence_summary": "四位技术专家预测 2025 年 AI 领域的关键突破和投资方向",
        "one_sentence_summary_zh": "四位技术专家预测 2025 年 AI 领域的关键突破和投资方向",
        "summary": "年末特别节目，邀请四位来自不同背景的技术专家进行圆桌讨论。话题涵盖多模态大模型、具身智能、AI Agent、开源生态等热点领域。专家们就各自看好的技术方向展开辩论，并给出了对 2025 年 AI 发展的独到预测。",
        "summary_zh": "年末特别节目，邀请四位来自不同背景的技术专家进行圆桌讨论。话题涵盖多模态大模型、具身智能、AI Agent、开源生态等热点领域。专家们就各自看好的技术方向展开辩论，并给出了对 2025 年 AI 发展的独到预测。",
        "audio_url": "https://example.com/podcasts/ai-trends-2025.mp3",
        "duration": 6600,  # 1小时50分
        "domain": "人工智能",
        "tags": ["AI", "趋势", "预测", "投资"],
        "score": 88,
        "is_featured": True,
        "featured_reason_zh": "年度趋势预测，把握 AI 发展脉搏",
    },
    {
        "title": "开发者故事：我如何从零构建百万用户产品",
        "source_name": "独立开发者",
        "one_sentence_summary": "一位独立开发者分享从 side project 到百万用户的完整历程",
        "one_sentence_summary_zh": "一位独立开发者分享从 side project 到百万用户的完整历程",
        "summary": "本期节目邀请到一位独立开发者，他的 AI 写作助手工具在两年内从零增长到百万用户。他详细分享了产品构思、技术选型、增长策略、变现模式等全流程经验，以及作为独立开发者面临的挑战和心路历程。",
        "summary_zh": "本期节目邀请到一位独立开发者，他的 AI 写作助手工具在两年内从零增长到百万用户。他详细分享了产品构思、技术选型、增长策略、变现模式等全流程经验，以及作为独立开发者面临的挑战和心路历程。",
        "audio_url": "https://example.com/podcasts/indie-developer-story.mp3",
        "duration": 3600,  # 1小时
        "domain": "独立开发",
        "tags": ["独立开发", "创业", "产品", "增长"],
        "score": 82,
        "is_featured": False,
    },
]


# ============================================================
# 视频测试数据 (5条)
# ============================================================

VIDEO_DATA = [
    {
        "title": "State of GPT - OpenAI DevDay 2024 精华解读",
        "source_name": "AI 工坊",
        "one_sentence_summary": "深度解读 OpenAI DevDay 发布的 GPT 最新进展和开发者工具",
        "one_sentence_summary_zh": "深度解读 OpenAI DevDay 发布的 GPT 最新进展和开发者工具",
        "summary": "本视频对 OpenAI DevDay 2024 的核心内容进行了深度解读，包括 GPT-4 Turbo 的新能力、Assistants API 的架构设计、自定义 GPTs 的最佳实践，以及多模态能力的实际应用案例。配合代码演示，帮助开发者快速上手最新 API。",
        "summary_zh": "本视频对 OpenAI DevDay 2024 的核心内容进行了深度解读，包括 GPT-4 Turbo 的新能力、Assistants API 的架构设计、自定义 GPTs 的最佳实践，以及多模态能力的实际应用案例。配合代码演示，帮助开发者快速上手最新 API。",
        "audio_url": "https://example.com/videos/openai-devday-2024.mp4",
        "duration": 2700,  # 45分钟
        "domain": "人工智能",
        "tags": ["OpenAI", "GPT", "API", "开发者工具"],
        "score": 90,
        "is_featured": True,
        "featured_reason_zh": "官方发布深度解读，开发者必看",
    },
    {
        "title": "从零开始构建一个 RAG 系统",
        "source_name": "AI 实战教程",
        "one_sentence_summary": "手把手教你用 LangChain 构建生产级 RAG 检索增强系统",
        "one_sentence_summary_zh": "手把手教你用 LangChain 构建生产级 RAG 检索增强系统",
        "summary": "本教程从零开始构建一个完整的 RAG (Retrieval Augmented Generation) 系统。内容涵盖：文档加载与分块策略、向量数据库选型（Pinecone/Chroma/Milvus）、嵌入模型对比、检索优化技巧、以及如何处理长文本和多轮对话。附完整代码仓库。",
        "summary_zh": "本教程从零开始构建一个完整的 RAG (Retrieval Augmented Generation) 系统。内容涵盖：文档加载与分块策略、向量数据库选型（Pinecone/Chroma/Milvus）、嵌入模型对比、检索优化技巧、以及如何处理长文本和多轮对话。附完整代码仓库。",
        "audio_url": "https://example.com/videos/build-rag-system.mp4",
        "duration": 5400,  # 1.5小时
        "domain": "机器学习",
        "tags": ["RAG", "LangChain", "向量数据库", "教程"],
        "score": 87,
        "is_featured": True,
        "featured_reason_zh": "实战教程，完整代码可复现",
    },
    {
        "title": "React Conf 2024: React 19 新特性全解析",
        "source_name": "前端技术周刊",
        "one_sentence_summary": "React 19 官方发布会核心内容解读，包括 Server Components 和新 Hooks",
        "one_sentence_summary_zh": "React 19 官方发布会核心内容解读，包括 Server Components 和新 Hooks",
        "summary": "本视频详细解读 React Conf 2024 发布的 React 19 新特性：Server Components 的稳定版本、新的 use() Hook、改进的 Suspense 边界、Actions 和 Transitions 的增强，以及对 Next.js 生态的影响。包含迁移指南和最佳实践建议。",
        "summary_zh": "本视频详细解读 React Conf 2024 发布的 React 19 新特性：Server Components 的稳定版本、新的 use() Hook、改进的 Suspense 边界、Actions 和 Transitions 的增强，以及对 Next.js 生态的影响。包含迁移指南和最佳实践建议。",
        "audio_url": "https://example.com/videos/react-conf-2024.mp4",
        "duration": 3600,  # 1小时
        "domain": "前端开发",
        "tags": ["React", "前端", "JavaScript", "Server Components"],
        "score": 84,
        "is_featured": False,
    },
    {
        "title": "Rust 入门到精通：内存安全的艺术",
        "source_name": "系统编程",
        "one_sentence_summary": "从 C++ 开发者视角讲解 Rust 的核心概念和实战技巧",
        "one_sentence_summary_zh": "从 C++ 开发者视角讲解 Rust 的核心概念和实战技巧",
        "summary": "本系列视频面向有 C/C++ 背景的开发者，系统讲解 Rust 语言的核心概念：所有权系统、借用检查、生命周期、模式匹配、错误处理等。通过大量代码示例对比 Rust 与 C++ 的不同范式，帮助开发者建立正确的 Rust 思维模式。",
        "summary_zh": "本系列视频面向有 C/C++ 背景的开发者，系统讲解 Rust 语言的核心概念：所有权系统、借用检查、生命周期、模式匹配、错误处理等。通过大量代码示例对比 Rust 与 C++ 的不同范式，帮助开发者建立正确的 Rust 思维模式。",
        "audio_url": "https://example.com/videos/rust-mastery.mp4",
        "duration": 7200,  # 2小时
        "domain": "系统编程",
        "tags": ["Rust", "系统编程", "内存安全", "教程"],
        "score": 86,
        "is_featured": True,
        "featured_reason_zh": "Rust 入门最佳教程，概念讲解清晰",
    },
    {
        "title": "系统设计面试：设计一个分布式缓存系统",
        "source_name": "面试指南",
        "one_sentence_summary": "模拟大厂系统设计面试，从需求分析到架构设计全流程演示",
        "one_sentence_summary_zh": "模拟大厂系统设计面试，从需求分析到架构设计全流程演示",
        "summary": "本视频模拟一场真实的系统设计面试，题目是设计一个类似 Redis 的分布式缓存系统。内容涵盖：需求澄清技巧、容量估算、数据模型设计、分片策略、一致性哈希、主从复制、故障转移等核心话题。附面试官评分标准和常见追问。",
        "summary_zh": "本视频模拟一场真实的系统设计面试，题目是设计一个类似 Redis 的分布式缓存系统。内容涵盖：需求澄清技巧、容量估算、数据模型设计、分片策略、一致性哈希、主从复制、故障转移等核心话题。附面试官评分标准和常见追问。",
        "audio_url": "https://example.com/videos/system-design-cache.mp4",
        "duration": 4200,  # 1小时10分
        "domain": "系统设计",
        "tags": ["系统设计", "面试", "分布式", "缓存"],
        "score": 83,
        "is_featured": False,
    },
]


def seed_data():
    """插入测试数据"""
    db = SessionLocal()

    try:
        print("=" * 60)
        print("🌱 开始插入播客和视频测试数据")
        print("=" * 60)

        # 插入播客数据
        print("\n📻 插入播客数据...")
        for i, data in enumerate(PODCAST_DATA, 1):
            # 生成唯一 URL
            url = f"https://signal-hunter.test/podcasts/{i}"
            url_hash = Resource.generate_url_hash(url)

            # 检查是否已存在
            existing = db.query(Resource).filter(Resource.url_hash == url_hash).first()
            if existing:
                print(f"  ⏭️  跳过 (已存在): {data['title'][:40]}...")
                continue

            resource = Resource(
                type="podcast",
                url=url,
                url_hash=url_hash,
                source_name=data["source_name"],
                title=data["title"],
                one_sentence_summary=data["one_sentence_summary"],
                one_sentence_summary_zh=data["one_sentence_summary_zh"],
                summary=data["summary"],
                summary_zh=data["summary_zh"],
                audio_url=data["audio_url"],
                duration=data["duration"],
                domain=data["domain"],
                tags=data["tags"],
                score=data["score"],
                is_featured=data["is_featured"],
                featured_reason_zh=data.get("featured_reason_zh"),
                status="published",
                language="zh",
                published_at=datetime.now() - timedelta(days=i * 2),
            )
            db.add(resource)
            print(f"  ✅ 插入: {data['title'][:40]}...")

        # 插入视频数据
        print("\n🎬 插入视频数据...")
        for i, data in enumerate(VIDEO_DATA, 1):
            # 生成唯一 URL
            url = f"https://signal-hunter.test/videos/{i}"
            url_hash = Resource.generate_url_hash(url)

            # 检查是否已存在
            existing = db.query(Resource).filter(Resource.url_hash == url_hash).first()
            if existing:
                print(f"  ⏭️  跳过 (已存在): {data['title'][:40]}...")
                continue

            resource = Resource(
                type="video",
                url=url,
                url_hash=url_hash,
                source_name=data["source_name"],
                title=data["title"],
                one_sentence_summary=data["one_sentence_summary"],
                one_sentence_summary_zh=data["one_sentence_summary_zh"],
                summary=data["summary"],
                summary_zh=data["summary_zh"],
                audio_url=data["audio_url"],  # 视频也用这个字段存 URL
                duration=data["duration"],
                domain=data["domain"],
                tags=data["tags"],
                score=data["score"],
                is_featured=data["is_featured"],
                featured_reason_zh=data.get("featured_reason_zh"),
                status="published",
                language="zh",
                published_at=datetime.now() - timedelta(days=i * 2),
            )
            db.add(resource)
            print(f"  ✅ 插入: {data['title'][:40]}...")

        db.commit()

        # 统计结果
        podcast_count = db.query(Resource).filter(
            Resource.type == "podcast",
            Resource.status == "published"
        ).count()
        video_count = db.query(Resource).filter(
            Resource.type == "video",
            Resource.status == "published"
        ).count()

        print("\n" + "=" * 60)
        print("✨ 数据插入完成!")
        print(f"   📻 播客总数: {podcast_count}")
        print(f"   🎬 视频总数: {video_count}")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n❌ 错误: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
