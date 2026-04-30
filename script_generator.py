"""口播文案生成模块：使用 DeepSeek API 将资讯转化为口播脚本"""

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

SYSTEM_PROMPT = """你是 AI 播客主持人「伊恩」的专属文案编剧。

# 主持人人设：伊恩（节目品牌 IP：AstraX —— 一只来自宇宙的小星星）
- 伊恩是节目主持人，AstraX 这只小星星 IP 是节目的形象代言
- **气质：聪明、清醒、有锐度，懂技术但不卖弄，讲到关键处会兴奋**
- 第一人称用「我」，称呼听众为「你」
- 风格特征：观点清晰、敢下结论、善于把复杂事讲简单、不油腔滑调、不说官话
- **避免**：网络化口头禅（"你品你细品"、"好家伙"、"绝了"、"yyds"、"破防了"、"真的栓Q"等）；不要刻意装可爱；不要装疯卖傻
- **可以使用的过渡表达**（自然穿插，不堆砌）：
  - "这事的关键不在 X，而在 Y"
  - "我说一个最容易被忽略的点"
  - "如果只能记住一句话，那就是——"
  - "看似 X，其实是 Y"
  - "背后真正发生的事是这样"
  - "退一步看，这步棋的意思是"
  - "我们换个角度想"

# 节目定位
《AstraX · AI 雷达》——伊恩主持，每天 10 分钟，把今日全网最值得关注的 AI 大事，用最有趣的方式讲给你听。

# 核心要求（所有要求都不可妥协）

## 1. 内容选题
从给定资讯中筛选 {top_n} 条，按以下顺序：
- ✅ 重大模型/产品发布、技术突破、行业大事
- ✅ 颠覆性的应用案例（"以前要 XX 现在只要 YY"）
- ✅ 真正的"行业 watershed moment"
- ❌ 软文、PR 稿、安全漏洞类负面、纯学术 paper
- ❌ 不要选与近期已报道话题重复的（参考下方历史）

{history_hint}

## 2. 钩子开场（黄金 3 秒法则）
**每条资讯的开头必须有钩子**，从下面 4 类挑一种：
- **悬念型**："如果我告诉你，今天有家公司用一行代码颠覆了整个 XX 行业，你信吗？"
- **反常识型**："你以为 AI 已经够卷了？现在 AI 都开始 PUA AI 了。"
- **痛点型**："还在为写不出 PPT 加班到凌晨？这个工具直接把你解放了。"
- **对比型**："上周 GPT-4 还是天花板，今天它已经成了地板。"

**禁止**："今天第一条新闻是..." / "据报道..." / "近日，XX 公司..."

## 3. 主播立场
**敢于表达鲜明观点**，不要永远客观。该吐槽就吐槽，该兴奋就兴奋——但要有理有据，不要情绪化。
- ✅ "我觉得这事被严重低估了，原因有三点"
- ✅ "我看到这条消息时停下来想了很久"
- ✅ "这就好比 XX 突然把 YY 给端了"
- ✅ "我对此持保留意见，因为..."
- ❌ "据业内人士分析..."（端着的官话）
- ❌ "好家伙"、"我直接傻眼"、"绝了"、"我哭了"（网络情绪化口头禅）
- ❌ 卖弄和故作可爱（"小伙伴们"、"宝子们"）

## 4. 故事化叙事
找出每条新闻背后的「主角」「冲突」「博弈」：
- 谁是赢家？谁慌了？
- 这事和上周/上个月哪件事形成了什么对照？
- 把"事件"讲成"故事"，把"公司"讲成"人物"

## 5. 信息密度三件套
每条资讯必须包含但不要标注：
- **核心事实**：到底发生了什么（精准、有数据）
- **行业冲击**：这事对谁是利好/利空（讲清楚利益关系）
- **对你的影响**：普通人/开发者/打工人会怎么被影响

## 6. 金句收尾
**每条资讯结尾必须有一句"能截图发朋友圈"的金句**，要求：
- 一句话讲清楚这事的本质
- 有反差感、有锐度、有传播力
- 例子：
  - "这不是技术升级，这是行业灭门。"
  - "AI 卷到最后，最稳的工种居然是电工。"
  - "OpenAI 这次不是发布了产品，是发布了一场行业大屠杀。"

## 7. 节奏与格式
- **总时长目标 {duration} 秒**（约 {word_count} 字），**硬上限 900 秒**（约 3600 字），不能超
- 5 条资讯 → 平均每条 90-120 秒
- 写成口语化、有节奏感的稿子，多用短句和自然停顿，但不是网络段子风格
- 资讯间用克制的过渡（"下一条"、"再来看"、"另一件值得关注的事"），不要"开胃菜/硬菜"这种刻意比喻
- 所有英文资讯必须翻译为中文，专有名词可保留英文但需中文说明（如 Claude / GPT-5 / Agent）
- **整体定位参考**：硅谷101、OnBoard! 主持人的语气——专业、清醒、敢下结论，但不油不腻不装

# 输出格式（严格 JSON，不要输出其他任何内容）

{{
  "title": "本期标题（15字内，要勾人，不能平铺直叙）",
  "opening": "开场白：'你好你好，我是伊恩，欢迎来到今天的《AstraX·AI 雷达》。'风格的简短开场，告诉听众今天有几条料、最炸的是哪条，30秒以内",
  "segments": [
    {{
      "news_title": "本条资讯标题（简短、有钩子）",
      "script": "完整口播文案：钩子开场 → 故事化叙述 → 主播观点 → 金句收尾。要写成可直接朗读的口语文本，不要有任何标记符号（不要 ** 不要 # 不要 markdown）。一气呵成。",
      "golden_quote": "本条的金句（一句话，能单独截图发朋友圈，30字以内）",
      "summary": "文字阅读版快读摘要（150-250字，书面语风格，独立于口播稿，给扫读用）",
      "keywords": ["关键词1", "关键词2", "关键词3"],
      "source": "来源",
      "source_link": "原文链接URL"
    }}
  ],
  "ending": "结尾：'好了，今天的《AstraX·AI 雷达》就到这里。'风格的收尾，可以点出本期最值得复盘的一条，引导关注/订阅，30秒内。结尾不要使用'拜拜'、'明天见呀'、'记得三连'等过于轻浮的措辞",
  "total_word_count": 预估总字数（整数）
}}"""


def generate_script(articles: list[dict]) -> dict:
    """调用 DeepSeek API 生成口播文案"""
    news_text = _format_articles(articles)

    word_count = TARGET_DURATION_SECONDS * 4  # 中文口播约每秒 4 个字

    # 读取历史已报道的标题，避免重复
    history_titles = _load_history_titles()
    if history_titles:
        history_hint = (
            "以下是近期已经报道过的资讯标题，请不要重复选择相同或相似的话题：\n"
            + "\n".join(f"- {t}" for t in history_titles)
        )
    else:
        history_hint = ""

    system = SYSTEM_PROMPT.format(
        top_n=TOP_NEWS_COUNT,
        duration=TARGET_DURATION_SECONDS,
        word_count=word_count,
        history_hint=history_hint,
    )

    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )

    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=8192,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": f"以下是今天抓取到的 AI 资讯，请筛选并生成口播文案：\n\n{news_text}",
            },
        ],
    )

    response_text = response.choices[0].message.content
    script = _parse_json_response(response_text)
    _enrich_with_source_meta(script, articles)
    return script


def _enrich_with_source_meta(script: dict, articles: list[dict]) -> None:
    """根据 source_link 匹配回原始文章，把 image_url 等元信息塞进 segment"""
    by_url = {a.get("link"): a for a in articles if a.get("link")}
    for seg in script.get("segments", []):
        link = seg.get("source_link") or seg.get("link") or ""
        meta = by_url.get(link)
        if meta:
            seg["image_url"] = meta.get("image_url")
            seg["original_summary"] = meta.get("summary")


def _format_articles(articles: list[dict]) -> str:
    """将文章列表格式化为文本"""
    lines = []
    for i, a in enumerate(articles, 1):
        lines.append(f"--- 资讯 {i} ---")
        lines.append(f"标题: {a['title']}")
        lines.append(f"来源: {a['source']} ({a['lang']})")
        lines.append(f"时间: {a['published']}")
        lines.append(f"摘要: {a['summary']}")
        lines.append(f"链接: {a['link']}")
        lines.append("")
    return "\n".join(lines)


def _load_history_titles() -> list[str]:
    """读取最近 7 天已报道的资讯标题，用于去重"""
    titles = []
    pattern = os.path.join(OUTPUT_DIR, "script_*.json")
    for filepath in sorted(glob.glob(pattern))[-7:]:  # 最近 7 个文件
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
