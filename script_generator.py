"""口播文案生成模块（二阶段）：
   阶段1 - 用 DeepSeek 从大量资讯里筛选 Top N
   阶段2 - 对选中的 Top N 抓全文+评论，再让 DeepSeek 写深度口播稿
"""

import json
import os
import glob
from openai import OpenAI
from config import (
    TOP_NEWS_COUNT,
    TARGET_DURATION_SECONDS,
    OUTPUT_DIR,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
)


# ============== 阶段 1：筛选 Top N ==============

SELECTION_PROMPT = """你是 AI 资讯筛选专家。从下面这批资讯中，挑出今日最值得做深度报道的 Top {top_n} 条。

筛选标准（按优先级）：
1. 重大模型/产品发布、技术突破、行业大事
2. 颠覆性的应用案例（"以前要 XX 现在只要 YY"）
3. 真正的"行业 watershed moment"
4. 优先选择能引起讨论、有故事性的话题

排除：
- 软文、PR 稿、纯学术 paper
- 安全漏洞类、负面消极内容
- 与近期已报道过的话题重复

{history_hint}

输出严格的 JSON 格式（无其他内容）：
{{
  "selected_indices": [资讯编号列表，0-based]
}}"""


def _select_top_articles(articles: list[dict], history_titles: list[str]) -> list[int]:
    """阶段1：让 DeepSeek 选 Top N 资讯的 index"""
    history_hint = ""
    if history_titles:
        history_hint = (
            "以下是近期已报道过的话题，避免重复：\n"
            + "\n".join(f"- {t}" for t in history_titles[:30])
        )

    formatted = []
    for i, a in enumerate(articles):
        formatted.append(f"[{i}] {a['title']}  (来源: {a['source']}, {a['summary'][:80]})")

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    resp = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=1024,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SELECTION_PROMPT.format(top_n=TOP_NEWS_COUNT, history_hint=history_hint)},
            {"role": "user", "content": "候选资讯：\n\n" + "\n".join(formatted)},
        ],
    )
    data = _parse_json_response(resp.choices[0].message.content)
    indices = data.get("selected_indices", [])
    # 兜底：若返回不合理，前 N 条
    if not indices or len(indices) < TOP_NEWS_COUNT:
        indices = list(range(min(TOP_NEWS_COUNT, len(articles))))
    return indices[:TOP_NEWS_COUNT]


# ============== 阶段 2：深度口播稿 ==============

DEEP_SCRIPT_PROMPT = """你是 AI 播客主持人「伊恩」的专属文案编剧。

# 主持人人设：伊恩（节目品牌 IP：AstraX —— 一只来自宇宙的小星星）
- 伊恩是节目主持人，AstraX 这只小星星是节目形象
- **气质：聪明、清醒、有锐度，懂技术但不卖弄，讲到关键处会兴奋**
- 第一人称用「我」，称呼听众为「你」
- 风格：观点清晰、敢下结论、善于把复杂事讲简单、不油腔滑调、不说官话
- **避免**：网络化口头禅（"你品你细品"、"好家伙"、"绝了"、"yyds"）；不刻意装可爱；不装疯卖傻

# 节目定位
《伊恩 AI 小报》——伊恩主持，每天一份带音频的 AI 资讯简报，**深度优先**。

# 输入说明
你会收到 {top_n} 条已经过初筛的精选资讯，每条都带有：
- 标题、来源、链接、原始摘要
- **【正文】**：抓取的原文全文（这是最重要的素材，必须基于此展开，不能仅凭标题想象）
- **【网友热评】**（如有）：来自 Reddit / Hacker News 的高赞评论原文（英文也要参考）

# 核心要求

## 1. 内容必须基于原文
**严禁仅凭标题展开想象。** 你必须：
- 引用原文中的具体数据、案例、人物语录
- 提取 2-3 个原文里的细节作为论据
- 如有评论，引用 1-2 条网友的代表性观点（"Reddit 上有人说..."、"HN 高赞评论指出..."）

## 2. 钩子开场（黄金 3 秒）
每条资讯开头必须有钩子（悬念/反常识/痛点/对比型，从原文具体细节切入）。
**禁止**："今天第一条..." / "据报道..." / "近日..."

## 3. 主播立场
表达鲜明观点，但有理有据。
- ✅ "我觉得这事被严重低估了，原因有三点"
- ✅ "原文里有个细节最值得品——XX"
- ❌ "好家伙" / "绝了" / "宝子们" / 卖弄装可爱

## 4. 故事化叙事
找出新闻背后的「主角」「冲突」「博弈」。把"事件"讲成"故事"，把"公司"讲成"人物"。

## 5. 信息密度（每条必须包含，不要标注小标题）
- **核心事实**：原文讲了什么（精准、有数据、有引述）
- **争议焦点**：网友/业内有什么不同看法（如有评论数据）
- **行业冲击**：谁是赢家谁慌了
- **对你的影响**：普通人/开发者/打工人会怎么被影响
- **主播洞察**：你（伊恩）独到的判断

## 6. 金句收尾
每条结尾一句"能截图发朋友圈"的金句，30字内，有反差感、有锐度。

## 7. 节奏与时长
- **每条资讯口播 2.5-3.5 分钟**（约 600-840 字），让内容真正讲透
- 总时长目标 {duration} 秒（约 {word_count} 字），硬上限 1500 秒（25 分钟）
- 口语化、有节奏、多用短句和自然停顿
- 资讯间用克制的过渡："下一条"、"再来看"、"另一件值得关注的事"
- 英文资讯必须翻译为中文（专有名词如 Claude/GPT-5/Agent 可保留英文）
- **整体定位**：硅谷 101 / OnBoard! 主持人的语气——专业、清醒、敢下结论但不油腻

# 输出格式（严格 JSON）

{{
  "title": "本期标题（15字内，要勾人）",
  "opening": "开场白：'你好你好，我是伊恩，欢迎来到今天的《伊恩 AI 小报》。' 风格的简短开场，预告今日 5 条料的核心，30秒以内",
  "segments": [
    {{
      "news_title": "本条标题（简短、有钩子）",
      "script": "完整口播文案：钩子 → 原文细节 → 网友观点 → 主播洞察 → 金句。可直接朗读的口语文本，无任何 markdown。每段 600-840 字。",
      "golden_quote": "本条金句（一句话，能截图发朋友圈，30字内）",
      "summary": "文字阅读版快读摘要（200-300字，书面语，独立于口播稿）",
      "keywords": ["关键词1", "关键词2", "关键词3"],
      "source": "来源",
      "source_link": "原文链接URL"
    }}
  ],
  "ending": "结尾：'好了，今天的《伊恩 AI 小报》就到这里。' 可点出本期最值得复盘的一条，引导关注/订阅，30秒内。不要'拜拜'、'明天见呀'这种轻浮措辞",
  "total_word_count": 预估总字数（整数）
}}"""


def generate_script(articles: list[dict]) -> dict:
    """二阶段口播脚本生成"""
    history_titles = _load_history_titles()

    # 阶段 1：筛选
    print("  🔎 阶段 1：DeepSeek 筛选 Top N...")
    top_indices = _select_top_articles(articles, history_titles)
    selected = [articles[i] for i in top_indices if i < len(articles)]
    print(f"  ✓ 筛选完成，挑了 {len(selected)} 条")
    for i, a in enumerate(selected, 1):
        print(f"     {i}. {a['title'][:50]}")

    # 阶段 1.5：抓原文全文（按需）
    print("\n  📖 阶段 1.5：抓取原文全文...")
    try:
        from article_enricher import enrich_articles
        enrich_articles(selected)
    except Exception as e:
        print(f"     ⚠️ 抓取异常（继续用 summary）: {e}")
        for a in selected:
            a.setdefault("full_body", a.get("summary", ""))

    # 阶段 2：深度生成
    print("\n  ✍️ 阶段 2：DeepSeek 写深度口播稿...")
    word_count = TARGET_DURATION_SECONDS * 4
    user_text = _format_for_deep_prompt(selected)

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    resp = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=16384,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": DEEP_SCRIPT_PROMPT.format(
                top_n=TOP_NEWS_COUNT,
                duration=TARGET_DURATION_SECONDS,
                word_count=word_count,
            )},
            {"role": "user", "content": user_text},
        ],
    )

    script = _parse_json_response(resp.choices[0].message.content)
    _enrich_with_source_meta(script, selected)
    return script


def _format_for_deep_prompt(articles: list[dict]) -> str:
    """为深度生成提供资讯素材：包含原文 + 评论"""
    lines = ["以下是今天精选的 5 条资讯，请基于原文和评论写深度口播稿：\n"]
    for i, a in enumerate(articles, 1):
        lines.append(f"========== 资讯 {i} ==========")
        lines.append(f"标题: {a['title']}")
        lines.append(f"来源: {a['source']} ({a.get('lang', 'zh')})")
        lines.append(f"链接: {a['link']}")
        lines.append(f"摘要: {a.get('summary', '')[:300]}")
        body = a.get("full_body", "") or a.get("summary", "")
        if body:
            lines.append(f"\n【正文】\n{body[:3500]}")
        comments = a.get("top_comments", [])
        if comments:
            lines.append("\n【网友热评】")
            for j, c in enumerate(comments[:5], 1):
                lines.append(f"  评论{j}: {c[:280]}")
        lines.append("")
    return "\n".join(lines)


def _enrich_with_source_meta(script: dict, articles: list[dict]) -> None:
    """根据 source_link 匹配回原始文章，把 image_url 等塞进 segment"""
    by_url = {a.get("link"): a for a in articles if a.get("link")}
    for seg in script.get("segments", []):
        link = seg.get("source_link") or seg.get("link") or ""
        meta = by_url.get(link)
        if meta:
            seg["image_url"] = meta.get("image_url")
            seg["original_summary"] = meta.get("summary")


def _load_history_titles() -> list[str]:
    """读取最近 7 天已报道的资讯标题"""
    titles = []
    pattern = os.path.join(OUTPUT_DIR, "script_*.json")
    for filepath in sorted(glob.glob(pattern))[-7:]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for seg in data.get("segments", []):
                titles.append(seg.get("news_title", ""))
        except Exception:
            continue
    return titles


def _parse_json_response(text: str) -> dict:
    """从 AI 回复中提取 JSON"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
        raise ValueError(f"无法解析 AI 返回的 JSON:\n{text[:200]}")
