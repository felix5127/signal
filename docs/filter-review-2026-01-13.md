# HN Pipeline 筛选审查报告

> 生成时间: 2026-01-13
> 采集数量: 17 篇
> 通过数量: 4 篇 (23.5%)

---

## 一、通过的文章 (4篇)

| # | 标题 | 链接 | HN分数 | 匹配条件 |
|---|------|------|--------|----------|
| 2 | Cowork: Claude Code for the rest of your work | https://claude.com/blog/cowork-research-preview | 1035 | C (可用工具) |
| 4 | TimeCapsuleLLM: LLM trained only on data from 1800-1875 | https://github.com/haykgrigo3/TimeCapsuleLLM | 632 | A, C (新代码+可用) |
| 12 | Yolobox – Run AI coding agents with full sudo | https://github.com/finbarr/yolobox | 99 | A, C (新代码+可用) |
| 13 | Agent-of-empires: OpenCode and Claude Code session manager | https://github.com/njbrake/agent-of-empires | 98 | A, C (新代码+可用) |

---

## 二、被拒绝的文章 (13篇)

### 2.1 纯观点/评论文章 (2篇)

| # | 标题 | 链接 | HN分数 | 拒绝理由 |
|---|------|------|--------|----------|
| 1 | Don't fall into the anti-AI hype | https://antirez.com/news/158 | 1235 | 纯观点评论文章 |
| 6 | Anthropic made a mistake in cutting off third-party clients | https://archaeologist.dev/artifacts/anthropic | 319 | 纯观点评论文章 |

**说明**: 这两篇是关于 AI 的讨论/观点文章，没有新代码、新模型或可复现结果。

---

### 2.2 非 AI/LLM 内容 (4篇)

| # | 标题 | 链接 | HN分数 | 拒绝理由 |
|---|------|------|--------|----------|
| 5 | Postal Arbitrage | https://walzr.com/postal-arbitrage | 429 | 非AI/LLM内容 |
| 9 | Ai, Japanese chimpanzee who counted and painted dies at 49 | https://www.bbc.com/news/articles/cj9r3zl2ywyo | 184 | 非AI技术内容 |
| 11 | You are not required to close your `<p>`, `<li>`, `<img>`, or `<br>` tags | https://blog.novalistic.com/archives/2017/08/optional-end-tags-in-html/ | 167 | 非AI相关前端技术 |
| 16 | Show HN: An iOS budget app I've been maintaining since 2011 | https://primoco.me/en/ | 35 | 非AI/LLM内容 |

**说明**:
- #5 邮政套利，与 AI 无关
- #9 日本黑猩猩 Ai 去世新闻，名字叫 Ai 但不是 AI 技术
- #11 HTML 标签闭合规范，纯前端技术
- #16 iOS 预算 App，与 AI 无关

---

### 2.3 新闻报道（无技术内容）(3篇)

| # | 标题 | 链接 | HN分数 | 拒绝理由 |
|---|------|------|--------|----------|
| 7 | The chess bot on Delta Air Lines will destroy you (2024) | https://www.youtube.com/watch?v=c0mLhHDcY3I | 258 | 无新模型/代码/数据 |
| 8 | Google removes AI health summaries after investigation | https://arstechnica.com/ai/2026/01/google-removes-some-ai-health-summaries-after-investigation-finds-dangerous-flaws/ | 194 | 新闻报道无新模型或数据 |
| 14 | Superhuman AI exfiltrates emails | https://www.promptarmor.com/resources/superhuman-ai-exfiltrates-emails | 50 | 安全事件报道无新代码 |

**说明**: 这些是 AI 相关新闻，但没有发布新代码、新模型或可复现的技术内容。

---

### 2.4 个人教程/商业新闻 (2篇)

| # | 标题 | 链接 | HN分数 | 拒绝理由 |
|---|------|------|--------|----------|
| 3 | How to code Claude Code in 200 lines of code | https://www.mihaileric.com/The-Emperor-Has-No-Clothes/ | 808 | 个人博客教程无新发布 |
| 17 | Advancing Claude in healthcare and the life sciences | https://www.anthropic.com/news/healthcare-life-sciences | 31 | 纯商业合作新闻 |

**说明**:
- #3 个人博主的 Claude Code 实现教程，非权威来源
- #17 Anthropic 医疗合作新闻，无技术细节

---

### 2.5 领域排除 (EXCLUDED_DOMAINS) (1篇)

| # | 标题 | 链接 | HN分数 | 拒绝理由 |
|---|------|------|--------|----------|
| 10 | Show HN: AI in SolidWorks | https://www.trylad.com | 169 | 非核心领域: SolidWorks |

**说明**: 命中 EXCLUDED_DOMAINS 中的 "SolidWorks" 关键词，属于垂直行业 CAD AI，非核心 AI/LLM 领域。

---

### 2.6 其他 (1篇)

| # | 标题 | 链接 | HN分数 | 拒绝理由 |
|---|------|------|--------|----------|
| 15 | FOSS in times of war, scarcity and (adversarial) AI | https://fosdem.org/2026/schedule/event/FE7ULY-foss-in-times-of-war-scarcity-and-ai/ | 47 | (待确认) |

---

## 三、待审查问题

请检查以下文章是否被错误筛除：

1. **#1 Don't fall into the anti-AI hype** (HN 1235分) - 是否需要保留高分观点文章？
2. **#3 How to code Claude Code in 200 lines** (HN 808分) - 是否算有价值的技术教程？
3. **#6 Anthropic third-party clients** - 是否属于重要行业动态？
4. **#8 Google AI health summaries** - AI 安全相关新闻是否需要保留？
5. **#14 Superhuman AI exfiltrates emails** - AI 安全漏洞是否需要保留？

---

## 四、筛选规则说明

### 通过条件 (满足任一即可)
- **A**: 发布了新代码/新模型/新论文
- **B**: 披露了可复现实验结果
- **C**: 提供了可用工具/API/Demo
- **D**: 来自权威来源的高质量教育内容

### 排除条件
- 纯观点/评论/讨论类文章
- 新闻报道无技术细节
- 招聘/广告/营销内容
- 低质量入门教程
- EXCLUDED_DOMAINS 命中 (CAD, WebGL, 游戏引擎, 加密货币等)
