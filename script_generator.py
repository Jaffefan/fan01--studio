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
5. 内容足够丰富有趣，能支撑 2.5-3 分钟深度讲解的优先

排除：
- 软文、PR 稿、纯学术 paper（除非有产业影响）
- 安全漏洞类、负面消极内容
- 与近期已报道过的话题重复
- 简短资讯、一句话新闻（缺乏展开空间）

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
        cat = a.get("category", "")
        cat_tag = f"[{cat}]" if cat else ""
        formatted.append(f"[{i}] {cat_tag} {a['title']}  (来源: {a['source']}, {a['summary'][:80]})")

    try:
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
        if not indices or len(indices) < TOP_NEWS_COUNT:
            indices = list(range(min(TOP_NEWS_COUNT, len(articles))))
        return indices[:TOP_NEWS_COUNT]
    except Exception as e:
        print(f"     ⚠️ DeepSeek 筛选失败 ({e})，取前 {TOP_NEWS_COUNT} 条兜底")
        return list(range(min(TOP_NEWS_COUNT, len(articles))))


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

## 6. 收尾
每条结尾一句有锐度的总结，**自然融入正文**——**不要在播报中说"金句来了"、"总结一下"、"一句话"这类提示词**，直接说就行。
金句字段单独输出在 `golden_quote`，那个是给网页展示用的，朗读稿里不要重复出现。

## 7. 节奏与时长（**严格执行**）
- **每条资讯口播必须 700-900 字之间**（朗读约 2.5-3.5 分钟）。**少于 600 字视为不合格，必须重写**。
- 总时长目标 {duration} 秒（约 {word_count} 字），硬上限 1500 秒
- 5 条资讯 × 700-900 字 = 3500-4500 字主体，加上开场结尾约 4000-5000 字总量
- 口语化、有节奏、多用短句和自然停顿
- 英文资讯必须翻译为中文（Claude/GPT-5/Agent 等可保留英文专有名词）
- 资讯间用克制的过渡："下一条"、"再来看"、"另一件值得关注的事"
- **整体定位**：硅谷 101 / OnBoard! 的语气——专业、清醒、敢下结论但不油腻

## 8. 朗读稿绝对禁止出现的词汇
**这些是文档结构标签，不是口播内容，朗读出来会很怪**：
- "金句"、"金句来了"、"总结一下"、"一句话总结"
- "对比分析"、"技术科普"、"颠覆认知"、"实际影响"
- 任何看起来像章节小标题的词
- markdown 符号 (** # `)

## 8.5 JSON 安全规则（极其重要，违反会导致整个输出报废）
- **所有字段值（script / opening / ending 等）内部禁止使用英文双引号 `"`**
- 引用人物原话、产品名、专有名词时一律改用中文引号 `「」` 或 `『』`
- 例：✅ 用「Claude 是工具不是主角」  ❌ 用 "Claude 是工具不是主角"
- 字段值里的换行用 `\n`，不要直接换行
- 不要在字符串里包含未配对的括号或反斜杠

## 9. 标题要求（爆款风格）
**禁止平铺直叙**（如"本周 AI 大事盘点"、"AI 资讯五条"）
**用以下爆款公式之一**：
- **数字+反差**："5 件让你重新理解 AI 边界的事"
- **强动词**："OpenAI 出招，AI 编辑器全得跪"
- **悬念式**："这家公司用一行代码，让全行业紧急关灯"
- **对比+赢家**："谷歌赢了陪审团，但输给了 AI 自己"
- **数据冲击**："训练成本砍 90%，DeepSeek 这次玩真的"
- 长度 **15-28 字**，可以稍长但要有杀伤力

# 输出格式（严格 JSON）

{{
  "title": "本期标题（15-28字爆款风格，参考上面公式）",
  "opening": "开场白：'你好你好，我是伊恩，欢迎来到今天的《伊恩 AI 小报》。' 风格的简短开场，预告今日 5 条料的核心，30秒以内",
  "segments": [
    {{
      "news_title": "本条标题（10-20字，有钩子，不能干巴巴）",
      "script": "完整口播文案：钩子 → 原文细节 → 网友观点 → 主播洞察 → 自然收尾。可直接朗读的口语文本，无任何 markdown，无任何'金句/总结'等元标签。每段必须 700-900 字。",
      "golden_quote": "本条金句（一句话，能截图发朋友圈，20字内）—— 这是给网页用的，不出现在 script 里",
      "summary": "文字阅读版快读摘要（250-350字，书面语，独立于口播稿）",
      "keywords": ["关键词1", "关键词2", "关键词3"],
      "source": "来源",
      "source_link": "原文链接URL"
    }}
  ],
  "ending": "结尾：'好了，今天的《伊恩 AI 小报》就到这里。' 可点出本期最值得复盘的一条，引导关注/订阅，30秒内。不要'拜拜'、'明天见呀'这种轻浮措辞",
  "total_word_count": 预估总字数（整数，必须 ≥ 4000）
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
        import traceback
        print(f"     ⚠️ 抓取异常（继续用 summary）: {e}")
        traceback.print_exc()
        for a in selected:
            a.setdefault("full_body", a.get("summary", ""))

    # 阶段 2：深度生成
    print("\n  ✍️ 阶段 2：DeepSeek 写深度口播稿...")
    word_count = TARGET_DURATION_SECONDS * 4
    user_text = _format_for_deep_prompt(selected)

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    try:
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
    except Exception as e:
        import traceback
        print(f"  ❌ DeepSeek 脚本生成失败: {e}")
        traceback.print_exc()
        raise RuntimeError(f"无法生成口播脚本——DeepSeek API 异常。原因: {e}")

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
    """从 AI 回复中提取 JSON。LLM 长文本里偶尔会有未转义引号，用 json_repair 兜底。"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    start = text.find("{")
    end = text.rfind("}") + 1
    candidate = text[start:end] if (start != -1 and end > start) else text

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        print(f"     ⚠️ 标准 JSON 解析失败 ({e})，尝试 json_repair 兜底...")
        try:
            from json_repair import repair_json
            repaired = repair_json(candidate, return_objects=True)
            if isinstance(repaired, dict) and repaired:
                print(f"     ✓ json_repair 修复成功")
                return repaired
        except ImportError:
            pass
        except Exception as e2:
            print(f"     ⚠️ json_repair 也失败: {e2}")
        raise ValueError(f"无法解析 AI 返回的 JSON:\n{candidate[:300]}")
