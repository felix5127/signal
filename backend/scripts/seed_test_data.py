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
        "transcript": """[00:00:00] Lex: 欢迎来到本期节目，今天我们非常荣幸邀请到 Andrej Karpathy。Andrej 是前 Tesla AI 总监，OpenAI 的创始成员之一，现在正在做 AI 教育相关的创业。Andrej，欢迎你。

[00:00:30] Andrej: 谢谢 Lex，很高兴来到这里。

[00:01:00] Lex: 让我们从头说起，你为什么决定离开 Tesla 和 OpenAI，转向教育领域？

[00:01:30] Andrej: 这是个很好的问题。我一直相信教育是人类进步的根本。在 Tesla 和 OpenAI 的工作让我意识到，AI 技术已经成熟到可以真正改变教育的程度了。

[00:02:30] Lex: 你说的 AI 改变教育，具体是指什么？

[00:03:00] Andrej: 想象一下，每个学生都有一个无限耐心的私人导师，它了解你的学习节奏，知道你的弱点在哪里，可以用最适合你的方式解释概念。这就是大语言模型可以做到的。

[00:05:00] Lex: 但很多人担心 AI 会取代人类教师，你怎么看？

[00:05:30] Andrej: 我认为不会。AI 擅长的是个性化、重复性的辅导工作。但人类教师的创造力、情感连接、激励学生的能力，这些是 AI 做不到的。最好的模式是人机协作。

[00:10:00] Lex: 能具体说说你正在做的教育平台吗？

[00:10:30] Andrej: 我们的核心理念是"learning by doing"。学生通过实际项目学习，AI 在旁边提供实时指导。比如学编程，不是看视频，而是直接写代码，遇到问题 AI 会像一个资深工程师一样给你提示。

[00:15:00] Lex: 这让我想到了苏格拉底式教学法。

[00:15:30] Andrej: 完全正确！苏格拉底式问答是最有效的教学方法之一，但它需要一对一的互动，传统教育做不到规模化。AI 让每个人都能享受到这种体验。

[00:20:00] Lex: 你觉得未来 5-10 年，教育会变成什么样？

[00:20:30] Andrej: 我认为会有三个大的变化。第一，个性化学习将成为主流；第二，学历的重要性会下降，技能证明会上升；第三，终身学习将成为常态，因为 AI 时代技能迭代太快了。

[00:30:00] Lex: 对于想进入 AI 领域的年轻人，你有什么建议？

[00:30:30] Andrej: 首先，打好数学基础，特别是线性代数和微积分。其次，动手实践比看论文更重要。最后，保持好奇心，AI 领域变化太快，需要持续学习的心态。

[00:45:00] Lex: 最后一个问题，你对 AI 的未来乐观吗？

[00:45:30] Andrej: 我是谨慎乐观的。AI 有巨大的潜力让世界变得更好，但我们需要负责任地发展它。教育是关键——只有让更多人理解 AI，我们才能做出正确的集体决策。

[00:50:00] Lex: 非常感谢 Andrej 的分享，这是一次很有启发的对话。

[00:50:30] Andrej: 谢谢 Lex，希望对听众有帮助。""",
        "chapters": [
            {"time": 0, "title": "开场介绍", "summary": "Lex 介绍嘉宾 Andrej Karpathy 的背景：前 Tesla AI 总监、OpenAI 创始成员、现在从事 AI 教育创业。"},
            {"time": 60, "title": "离开大厂的原因", "summary": "Andrej 解释为什么从 Tesla 和 OpenAI 转向教育领域，强调 AI 技术已经成熟到可以真正改变教育。"},
            {"time": 180, "title": "AI 如何改变教育", "summary": "讨论大语言模型作为私人导师的潜力，能够提供个性化学习体验。"},
            {"time": 300, "title": "AI 与人类教师的关系", "summary": "探讨 AI 是否会取代教师，结论是人机协作是最佳模式。"},
            {"time": 600, "title": "教育平台详解", "summary": "介绍 Andrej 正在做的教育平台，核心理念是 learning by doing。"},
            {"time": 900, "title": "苏格拉底式教学", "summary": "讨论 AI 如何实现大规模的苏格拉底式问答教学。"},
            {"time": 1200, "title": "教育的未来预测", "summary": "预测未来 5-10 年教育的三大变化：个性化、技能证明、终身学习。"},
            {"time": 1800, "title": "给年轻人的建议", "summary": "对想进入 AI 领域的年轻人的三点建议：数学基础、动手实践、保持好奇。"},
            {"time": 2700, "title": "AI 的未来展望", "summary": "Andrej 表达对 AI 未来的谨慎乐观态度，强调教育的重要性。"},
        ],
        "qa_pairs": [
            {"question": "Andrej 为什么离开 Tesla 和 OpenAI？", "answer": "他相信教育是人类进步的根本，AI 技术已经成熟到可以真正改变教育的程度，所以决定投身教育领域创业。", "timestamp": 90},
            {"question": "AI 会取代人类教师吗？", "answer": "不会完全取代。AI 擅长个性化、重复性的辅导工作，但人类教师的创造力、情感连接、激励学生的能力是 AI 做不到的。最好的模式是人机协作。", "timestamp": 330},
            {"question": "Andrej 的教育平台核心理念是什么？", "answer": "核心理念是 'learning by doing'——通过实际项目学习，AI 在旁边提供实时指导，而不是被动地看视频。", "timestamp": 630},
            {"question": "未来教育会有哪些变化？", "answer": "三大变化：1) 个性化学习将成为主流；2) 学历重要性下降，技能证明上升；3) 终身学习成为常态，因为 AI 时代技能迭代太快。", "timestamp": 1230},
            {"question": "对想进入 AI 领域的年轻人有什么建议？", "answer": "三点建议：1) 打好数学基础，特别是线性代数和微积分；2) 动手实践比看论文更重要；3) 保持好奇心，需要持续学习的心态。", "timestamp": 1830},
        ],
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
        "transcript": """[00:00:00] 主持人：欢迎收听 AI 技术前沿播客，我是主持人张明。今天我们请到三位资深机器学习工程师，一起聊聊深度学习框架的演进史。先请各位自我介绍。

[00:01:00] 嘉宾A（李华）：大家好，我是李华，在某大厂做 ML Infra，主要负责训练平台。用过几乎所有主流框架，从 Caffe 到现在的 PyTorch 2.0。

[00:01:30] 嘉宾B（王芳）：我是王芳，之前在 Google Brain 工作，TensorFlow 的早期用户。现在在创业公司做推荐系统。

[00:02:00] 嘉宾C（陈刚）：我是陈刚，学术背景出身，现在在一家 AI 研究院。主要关注 JAX 和函数式机器学习。

[00:03:00] 主持人：让我们从头说起。2012 年 AlexNet 之后，深度学习爆发，当时大家都用什么框架？

[00:03:30] 李华：那个年代主要是 Caffe 和 Theano。Caffe 是伯克利 BVLC 出的，配置文件是 protobuf 格式，写起来很痛苦。但它的速度很快，CNN 任务几乎都用它。

[00:05:00] 王芳：Theano 是蒙特利尔大学的作品，Python 接口，支持 GPU。学术界用的多。但它的符号计算太抽象了，debug 是噩梦。

[00:07:00] 主持人：后来 TensorFlow 和 PyTorch 出现，改变了整个格局。

[00:07:30] 王芳：TensorFlow 是 2015 年 Google 开源的。一出来就火了，因为 Google 的品牌效应，加上完整的生态——TensorBoard、TFServing、TFLite。

[00:10:00] 李华：但 TensorFlow 1.x 的静态图真的很难用。你要先定义完整的计算图，然后用 Session.run 执行。写个简单的 if-else 都要用 tf.cond。

[00:12:00] 陈刚：PyTorch 是 2016 年 Facebook 出的，基于 Torch。它最大的创新是动态图——define-by-run。代码就是计算图，调试用普通的 Python debugger 就行。

[00:15:00] 主持人：所以后来学术界几乎全转向 PyTorch 了？

[00:15:30] 陈刚：对，2018 年之后，新论文的代码基本都是 PyTorch。因为研究需要快速迭代，动态图太方便了。NeurIPS 上 PyTorch 的引用量超过 TensorFlow 就是从那时候开始的。

[00:18:00] 王芳：Google 也意识到问题了，所以推出了 TensorFlow 2.0，默认开启 Eager Execution，向 PyTorch 靠拢。但已经晚了，用户习惯很难改。

[00:22:00] 主持人：现在 JAX 又火起来了，陈刚你怎么看？

[00:22:30] 陈刚：JAX 是 Google 内部的另一个项目，主打函数式编程 + 可组合的变换。jit、grad、vmap 这些原语可以任意组合。对于需要高性能和数学推导的场景，比如物理仿真、科学计算，JAX 确实更优雅。

[00:25:00] 李华：从工程角度，JAX 还是太学术了。生态不如 PyTorch 完善，生产部署也没 TensorFlow 成熟。

[00:28:00] 主持人：如果现在新开一个项目，你们会选什么框架？

[00:28:30] 李华：大多数情况选 PyTorch。生态好，社区活跃，Hugging Face 全系列都支持。

[00:30:00] 王芳：如果是边缘部署或者移动端，TensorFlow 生态还是最强的。TFLite 的优化做得很好。

[00:32:00] 陈刚：纯研究或者需要高性能并行计算，我会选 JAX。特别是配合 TPU 用的时候。

[00:35:00] 主持人：最后聊聊 PyTorch 2.0 的 torch.compile，这是不是 PyTorch 的下一个大事件？

[00:35:30] 李华：绝对是。torch.compile 背后是 TorchDynamo 和 TorchInductor，能把动态图编译成高效的内核。既保留了易用性，又能拿到静态图的性能。这是吃掉两个世界的好处。

[00:40:00] 主持人：感谢三位的分享，今天的讨论非常精彩。下期我们聊大模型训练的分布式策略，敬请期待。""",
        "chapters": [
            {"time": 0, "title": "嘉宾介绍", "summary": "三位嘉宾自我介绍：李华（ML Infra）、王芳（前 Google Brain）、陈刚（AI 研究院）。"},
            {"time": 180, "title": "早期框架回顾", "summary": "回顾 2012 年 AlexNet 之后的框架生态：Caffe（伯克利）和 Theano（蒙特利尔）的特点与痛点。"},
            {"time": 420, "title": "TensorFlow 崛起", "summary": "2015 年 TensorFlow 开源，Google 品牌效应加完整生态，但静态图使用体验差。"},
            {"time": 720, "title": "PyTorch 革命", "summary": "2016 年 PyTorch 发布，动态图（define-by-run）成为学术界首选。"},
            {"time": 1080, "title": "TensorFlow 2.0 的挣扎", "summary": "Google 推出 TF 2.0 向 PyTorch 靠拢，但用户习惯难以改变。"},
            {"time": 1320, "title": "JAX 的崛起", "summary": "JAX 的函数式编程理念：jit、grad、vmap 可组合变换，适合科学计算。"},
            {"time": 1680, "title": "框架选择建议", "summary": "实用建议：通用场景选 PyTorch，边缘部署选 TensorFlow，纯研究选 JAX。"},
            {"time": 2100, "title": "PyTorch 2.0 展望", "summary": "torch.compile 的意义：TorchDynamo + TorchInductor 兼顾易用性和性能。"},
        ],
        "qa_pairs": [
            {"question": "早期深度学习主要用什么框架？", "answer": "主要是 Caffe 和 Theano。Caffe 速度快但配置文件写起来痛苦；Theano 是 Python 接口支持 GPU，但符号计算太抽象，debug 困难。", "timestamp": 210},
            {"question": "为什么学术界都转向 PyTorch？", "answer": "因为 PyTorch 的动态图（define-by-run）让代码就是计算图，调试用普通 Python debugger 就行，研究需要的快速迭代非常方便。", "timestamp": 900},
            {"question": "TensorFlow 和 PyTorch 各自的优势是什么？", "answer": "TensorFlow 在边缘部署和移动端生态最强，TFLite 优化做得好；PyTorch 生态完善、社区活跃，Hugging Face 全系列支持，适合大多数场景。", "timestamp": 1800},
            {"question": "JAX 适合什么场景？", "answer": "JAX 适合纯研究或需要高性能并行计算的场景，特别是物理仿真、科学计算，以及配合 TPU 使用时表现出色。", "timestamp": 1350},
            {"question": "PyTorch 2.0 的 torch.compile 有什么意义？", "answer": "torch.compile 基于 TorchDynamo 和 TorchInductor，能把动态图编译成高效内核，既保留易用性又能拿到静态图的性能，是两全其美的方案。", "timestamp": 2130},
        ],
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
        "transcript": """[00:00:00] 主持人：大家好，欢迎收听创业内幕。今天我们请到三位非常特别的创业者，他们都在用 AI 改变传统行业。先来认识一下。

[00:01:00] 嘉宾A（张伟）：我是张伟，农田智能的创始人。我们用无人机+计算机视觉帮农民优化种植决策。

[00:01:30] 嘉宾B（林晓）：我是林晓，合同智审的 CEO。我们用 NLP 技术自动化合同审核，主要服务律所和企业法务。

[00:02:00] 嘉宾C（王强）：我是王强，预知维护的联合创始人。我们做工业设备的预测性维护，用传感器数据预测设备故障。

[00:03:00] 主持人：张伟，农业 AI 听起来很酷，但农业是个传统行业，你们是怎么切入的？

[00:03:30] 张伟：农业确实传统，但痛点很明显——种什么、怎么种、什么时候收，这些决策现在主要靠经验。我们用无人机拍摄农田图像，AI 分析作物健康状况、病虫害、土壤含水量，给农民提供精准建议。

[00:06:00] 主持人：落地过程顺利吗？

[00:06:30] 张伟：一开始很难。农民不信任技术，觉得他们种了几十年地，凭什么听一个 APP 的。后来我们找到一个关键策略：先和种植大户合作，用数据证明效果——产量提升 15%，农药使用减少 30%。有了标杆案例，推广就容易多了。

[00:10:00] 主持人：林晓，法律行业应该更难切入吧？

[00:10:30] 林晓：法律行业最难的不是技术，是信任。律师对 AI 的准确性要求非常高，一个错误可能就是一场官司。我们的策略是做"辅助"而不是"替代"——AI 标记风险点，最终决策还是律师做。

[00:13:00] 主持人：你们的技术是怎么实现的？

[00:13:30] 林晓：核心是法律专用的 NLP 模型。我们和律所合作，用他们的历史合同训练模型。现在能识别 200 多种常见的合同风险条款，准确率超过 95%。

[00:17:00] 主持人：王强，工业预测性维护这个方向竞争激烈吗？

[00:17:30] 王强：竞争者不少，但大部分是传统工业公司的数字化转型部门。我们的优势是纯 AI 出身，算法更先进。我们能在故障发生前 7-14 天预警，准确率 92%。

[00:20:00] 主持人：客户买单吗？

[00:20:30] 王强：制造业老板最看重 ROI。一次意外停机可能损失几十万，我们的系统一年能避免十几次这样的损失。算下来，投资回报率超过 300%，客户很容易决策。

[00:25:00] 主持人：最后一个问题，给想进入传统行业的 AI 创业者什么建议？

[00:26:00] 张伟：一定要深入一线。我前三个月每天都在农田里，理解农民真正的需求。

[00:27:00] 林晓：找到行业里的"技术信任者"，他们会成为你的第一批客户和传播者。

[00:28:00] 王强：量化价值。传统行业老板不懂 AI，但他们懂钱。你要能清楚地告诉他，用你的产品能省多少钱、赚多少钱。

[00:30:00] 主持人：非常感谢三位的分享，今天的内容对想创业的朋友很有启发。我们下期再见。""",
        "chapters": [
            {"time": 0, "title": "嘉宾介绍", "summary": "三位创业者自我介绍：张伟（农田智能）、林晓（合同智审）、王强（预知维护）。"},
            {"time": 180, "title": "农业 AI 的切入点", "summary": "张伟介绍如何用无人机+计算机视觉优化农业种植决策。"},
            {"time": 360, "title": "农业落地策略", "summary": "先与种植大户合作建立标杆案例，用数据证明效果：产量提升 15%，农药减少 30%。"},
            {"time": 600, "title": "法律 AI 的信任挑战", "summary": "林晓讲述法律行业对准确性的高要求，采用'辅助而非替代'策略。"},
            {"time": 810, "title": "法律 NLP 技术实现", "summary": "用律所历史合同训练专用模型，能识别 200+ 种风险条款，准确率超 95%。"},
            {"time": 1020, "title": "工业预测维护市场", "summary": "王强介绍预测性维护的技术优势：提前 7-14 天预警，准确率 92%。"},
            {"time": 1230, "title": "ROI 驱动的销售", "summary": "制造业客户看重投资回报，系统 ROI 超过 300%，决策容易。"},
            {"time": 1500, "title": "给 AI 创业者的建议", "summary": "三位总结：深入一线、找技术信任者、量化价值。"},
        ],
        "qa_pairs": [
            {"question": "农业 AI 如何获得农民信任？", "answer": "先和种植大户合作建立标杆案例，用数据证明效果（产量提升 15%，农药使用减少 30%），有了成功案例后推广就容易多了。", "timestamp": 390},
            {"question": "法律 AI 的落地策略是什么？", "answer": "做'辅助'而不是'替代'——AI 标记风险点，最终决策还是律师做。这样既发挥 AI 效率，又保证了律师的专业判断。", "timestamp": 630},
            {"question": "工业预测维护的技术指标如何？", "answer": "能在故障发生前 7-14 天预警，准确率达到 92%。一次意外停机可能损失几十万，系统年投资回报率超过 300%。", "timestamp": 1050},
            {"question": "传统行业 AI 创业最重要的是什么？", "answer": "三点：1) 深入一线理解真实需求；2) 找到行业里的'技术信任者'作为第一批客户；3) 量化价值，用钱说话。", "timestamp": 1560},
        ],
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
        "transcript": """[00:00:00] 主持人：欢迎收听硅谷早知道年末特别节目。今天我们请到四位来自不同背景的技术专家，一起预测 2025 年最值得关注的 AI 趋势。

[00:01:00] 嘉宾A（周博士）：我是周博士，在某头部大厂研究院负责多模态大模型研发。

[00:01:30] 嘉宾B（Sarah）：我是 Sarah，在硅谷一家机器人公司做具身智能研究。

[00:02:00] 嘉宾C（李明）：我是李明，专注于 AI Agent 和 AutoML 领域的创业者。

[00:02:30] 嘉宾D（王教授）：我是王教授，在大学做 AI 安全和伦理研究，也关注开源生态。

[00:03:30] 主持人：开始第一个话题——多模态大模型。周博士，2024 年 GPT-4V、Gemini 大放异彩，2025 年会有什么突破？

[00:04:00] 周博士：我认为 2025 年多模态的重点会从"理解"转向"生成"。现在的模型能看懂图片、视频，但生成质量还不够。明年我们会看到真正好用的视频生成模型，长度从几秒延长到几分钟。

[00:07:00] 主持人：Sarah，具身智能呢？感觉一直在"即将爆发"。

[00:07:30] Sarah：哈哈，确实。但 2025 年可能真的是转折点。原因有三：第一，大模型给了机器人"大脑"；第二，仿真环境成熟了，训练成本大幅下降；第三，特斯拉 Optimus 等玩家在推动产业链成熟。我预测 2025 年会看到第一批商用人形机器人。

[00:12:00] 主持人：李明，AI Agent 现在是不是有点过热了？

[00:12:30] 李明：有泡沫，但方向没问题。2024 年大家做的 Agent 主要是 Demo 级别的，真正能在生产环境跑的很少。2025 年的关键词是"可靠性"——Agent 需要在企业场景稳定运行，这需要更好的错误处理、回滚机制、人类监督接口。

[00:17:00] 主持人：王教授，开源生态有什么看点？

[00:17:30] 王教授：开源模型正在追赶闭源。Llama 3、Mistral、Qwen 都很强。2025 年我预测会出现一个"开源 GPT-4 时刻"——开源模型在大部分任务上达到 GPT-4 水平。这会改变整个市场格局。

[00:22:00] 主持人：如果只能投资一个方向，你们会选哪个？

[00:22:30] 周博士：多模态基础设施，比如高质量多模态数据集、标注工具。

[00:23:30] Sarah：机器人零部件供应链，特别是传感器和执行器。

[00:24:30] 李明：垂直领域的 Agent 应用，比如法律、医疗、金融。

[00:25:30] 王教授：AI 安全和对齐技术。模型越强大，安全越重要，这块现在被严重低估。

[00:28:00] 主持人：最后，每人用一句话预测 2025 年 AI 最大的惊喜。

[00:28:30] 周博士：端到端的 AI 电影生成，从剧本到成片全自动。

[00:29:00] Sarah：第一个能做家务的消费级机器人开始预售。

[00:29:30] 李明：AI Agent 帮助完成的代码量超过人类程序员。

[00:30:00] 王教授：一个重大的 AI 安全事件，促使全球加快 AI 监管立法。

[00:32:00] 主持人：非常精彩的预测！让我们明年同一时间回来验证。感谢四位专家，也感谢听众朋友们的收听。新年快乐！""",
        "chapters": [
            {"time": 0, "title": "嘉宾介绍", "summary": "四位专家自我介绍：周博士（多模态大模型）、Sarah（具身智能）、李明（AI Agent）、王教授（AI 安全与开源）。"},
            {"time": 210, "title": "多模态大模型趋势", "summary": "周博士预测 2025 年多模态从'理解'转向'生成'，视频生成从几秒延长到几分钟。"},
            {"time": 420, "title": "具身智能转折点", "summary": "Sarah 认为大模型+仿真成熟+产业链推动，2025 年将看到第一批商用人形机器人。"},
            {"time": 720, "title": "AI Agent 的可靠性挑战", "summary": "李明指出 Agent 需要从 Demo 走向生产环境，关键词是可靠性、错误处理、人类监督。"},
            {"time": 1020, "title": "开源生态追赶", "summary": "王教授预测开源模型将达到'开源 GPT-4 时刻'，改变市场格局。"},
            {"time": 1320, "title": "投资方向讨论", "summary": "四位专家分享各自看好的投资方向：多模态基础设施、机器人供应链、垂直 Agent、AI 安全。"},
            {"time": 1680, "title": "2025 预测总结", "summary": "一句话预测：AI 电影生成、家务机器人预售、Agent 编码超人类、AI 安全事件促进监管。"},
        ],
        "qa_pairs": [
            {"question": "2025 年多模态大模型有什么突破？", "answer": "重点从'理解'转向'生成'，会出现真正好用的视频生成模型，长度从几秒延长到几分钟。", "timestamp": 240},
            {"question": "具身智能为什么 2025 年可能是转折点？", "answer": "三个原因：大模型给机器人'大脑'、仿真环境成熟使训练成本下降、Tesla Optimus 等推动产业链成熟。", "timestamp": 450},
            {"question": "AI Agent 在 2025 年的发展关键词是什么？", "answer": "'可靠性'——Agent 需要在企业场景稳定运行，需要更好的错误处理、回滚机制、人类监督接口。", "timestamp": 750},
            {"question": "开源模型 2025 年会有什么突破？", "answer": "会出现'开源 GPT-4 时刻'——开源模型在大部分任务上达到 GPT-4 水平，改变整个市场格局。", "timestamp": 1050},
            {"question": "专家们各自看好什么投资方向？", "answer": "周博士看好多模态基础设施；Sarah 看好机器人零部件供应链；李明看好垂直领域 Agent 应用；王教授看好 AI 安全和对齐技术。", "timestamp": 1350},
        ],
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
        "transcript": """[00:00:00] 主持人：欢迎收听独立开发者播客。今天的嘉宾是 WriteFlow 的创始人赵磊，一个人做出了百万用户的 AI 写作助手。赵磊，先介绍一下自己吧。

[00:01:00] 赵磊：大家好，我是赵磊，前大厂程序员，2022 年辞职开始独立开发。WriteFlow 是我的第三个产品，前两个都失败了。

[00:02:00] 主持人：前两个产品为什么失败了？

[00:02:30] 赵磊：第一个是做给程序员的代码片段管理工具，技术很酷但没人需要。第二个是做了一个 Notion 竞品，市场太卷，作为独立开发者根本拼不过。

[00:04:00] 主持人：WriteFlow 的灵感从哪来的？

[00:04:30] 赵磊：2022 年底 ChatGPT 出来的时候，我发现很多人用它来帮助写作，但体验很割裂——要切换窗口、复制粘贴。我想，如果把 AI 直接嵌入写作界面呢？就这么一个简单的想法。

[00:06:00] 主持人：技术选型是怎么考虑的？

[00:06:30] 赵磊：我选了最快的技术栈——Next.js + Vercel + Supabase。独立开发者最稀缺的是时间，不能在基础设施上花太多精力。数据库、认证、部署全部用现成的服务。

[00:09:00] 主持人：MVP 用了多长时间？

[00:09:30] 赵磊：两周。第一版非常简陋，只有一个编辑器和一个"帮我续写"的按钮。但这已经足够验证想法了。

[00:11:00] 主持人：第一批用户是怎么来的？

[00:11:30] 赵磊：Product Hunt 发布是转折点。我精心准备了发布，做了一个很酷的 demo 视频，选在周二发布（据说是最好的日子）。当天拿到了 Product Hunt 日榜第三，带来了第一批 5000 个用户。

[00:15:00] 主持人：后来是怎么增长到百万的？

[00:15:30] 赵磊：三个关键策略。第一是 SEO——我写了大量关于 AI 写作的博客文章，长尾词流量很稳定。第二是产品内的病毒增长——用户生成的内容可以分享，分享页有注册入口。第三是功能迭代——我每周都发布新功能，保持用户活跃度。

[00:20:00] 主持人：变现模式是什么？

[00:20:30] 赵磊：订阅制。免费版有 API 调用次数限制，Pro 版无限次。定价 $9.9/月，后来涨到 $12.9。现在付费用户大概 2 万多，月收入超过 25 万美金。

[00:24:00] 主持人：一个人怎么处理这么多事情？

[00:24:30] 赵磊：关键是自动化和外包。客服用 AI 自动回复处理 80% 的问题。设计外包给 Fiverr 上的设计师。我只专注于产品和增长。另外，学会说"不"——很多功能请求要拒绝，保持产品简洁。

[00:28:00] 主持人：对想做独立开发的人有什么建议？

[00:28:30] 赵磊：三点。第一，选对赛道比努力重要——要找有真实需求、竞争不太激烈的方向。第二，快速验证——两周内要能拿出 MVP。第三，坚持——我前两个产品失败后差点放弃，幸好坚持到了第三个。

[00:32:00] 主持人：最后一个问题，你现在最大的挑战是什么？

[00:32:30] 赵磊：保持动力。产品成功之后，有一段时间我迷失了方向。现在我在考虑组建小团队，从独立开发者转型为小公司。但这又是一个全新的挑战了。

[00:35:00] 主持人：非常感谢赵磊的分享，希望能给听众朋友们一些启发。我们下期再见！""",
        "chapters": [
            {"time": 0, "title": "嘉宾介绍", "summary": "赵磊介绍自己：前大厂程序员，2022 年辞职独立开发，WriteFlow 是第三个产品。"},
            {"time": 120, "title": "前两个失败的产品", "summary": "第一个产品技术酷但没需求，第二个市场太卷竞争不过大公司。"},
            {"time": 240, "title": "WriteFlow 的诞生", "summary": "ChatGPT 出来后发现用户需要更好的 AI 写作体验，于是把 AI 嵌入写作界面。"},
            {"time": 360, "title": "技术选型策略", "summary": "选择 Next.js + Vercel + Supabase，独立开发者应该用现成服务节省时间。"},
            {"time": 570, "title": "两周做出 MVP", "summary": "第一版只有编辑器和'帮我续写'按钮，但足够验证想法。"},
            {"time": 690, "title": "Product Hunt 发布", "summary": "精心准备发布，拿到日榜第三，带来首批 5000 用户。"},
            {"time": 930, "title": "增长策略", "summary": "三个关键：SEO 长尾词流量、产品内病毒增长、每周功能迭代。"},
            {"time": 1200, "title": "变现模式", "summary": "订阅制 $12.9/月，2 万多付费用户，月收入超 25 万美金。"},
            {"time": 1440, "title": "独立开发的效率秘诀", "summary": "自动化+外包：AI 客服、设计外包，专注产品和增长，学会说'不'。"},
            {"time": 1680, "title": "给独立开发者的建议", "summary": "三点：选对赛道、两周出 MVP、坚持到第三个产品。"},
            {"time": 1920, "title": "当前挑战", "summary": "保持动力是最大挑战，正在考虑组建小团队转型。"},
        ],
        "qa_pairs": [
            {"question": "前两个产品为什么失败？", "answer": "第一个是代码片段管理工具，技术酷但没人需要；第二个做 Notion 竞品，市场太卷，独立开发者拼不过大公司。", "timestamp": 150},
            {"question": "WriteFlow 的核心创新是什么？", "answer": "把 AI 直接嵌入写作界面，解决用户使用 ChatGPT 时需要切换窗口、复制粘贴的割裂体验。", "timestamp": 270},
            {"question": "为什么选择 Next.js + Vercel + Supabase？", "answer": "独立开发者最稀缺的是时间，不能在基础设施上花太多精力，要用现成服务——数据库、认证、部署全部外包给云服务。", "timestamp": 390},
            {"question": "Product Hunt 发布有什么技巧？", "answer": "精心准备发布：做一个很酷的 demo 视频，选在周二发布（据说是最好的日子）。", "timestamp": 690},
            {"question": "增长到百万用户的三个关键策略是什么？", "answer": "1) SEO——大量 AI 写作博客文章获取长尾流量；2) 产品内病毒增长——内容分享页有注册入口；3) 每周发布新功能保持用户活跃度。", "timestamp": 930},
            {"question": "独立开发者怎么处理那么多事情？", "answer": "关键是自动化和外包：AI 客服处理 80% 问题，设计外包给 Fiverr，只专注产品和增长，学会说'不'拒绝功能请求。", "timestamp": 1470},
        ],
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
                # 播客专用字段: 转录文本、章节、Q&A
                transcript=data.get("transcript"),
                chapters=data.get("chapters"),
                qa_pairs=data.get("qa_pairs"),
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


def reset_and_seed():
    """清除旧的测试数据后重新插入"""
    db = SessionLocal()

    try:
        print("=" * 60)
        print("🗑️  清除旧的测试数据...")
        print("=" * 60)

        # 删除测试 URL 的播客数据
        deleted_podcasts = db.query(Resource).filter(
            Resource.url.like("https://signal-hunter.test/podcasts/%")
        ).delete(synchronize_session=False)
        print(f"   📻 删除播客: {deleted_podcasts} 条")

        # 删除测试 URL 的视频数据
        deleted_videos = db.query(Resource).filter(
            Resource.url.like("https://signal-hunter.test/videos/%")
        ).delete(synchronize_session=False)
        print(f"   🎬 删除视频: {deleted_videos} 条")

        db.commit()
        print("✅ 清除完成\n")

    except Exception as e:
        db.rollback()
        print(f"\n❌ 清除错误: {e}")
        raise
    finally:
        db.close()

    # 重新插入
    seed_data()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="播客和视频测试数据种子脚本")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="清除旧的测试数据后重新插入"
    )
    args = parser.parse_args()

    if args.reset:
        reset_and_seed()
    else:
        seed_data()
