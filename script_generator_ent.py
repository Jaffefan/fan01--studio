"""娱乐深度谈 — 口播脚本生成：每日 1 个事件，故事化深度讲述"""

import json, os, glob
from openai import OpenAI
from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL,
    ENT_OUTPUT_DIR, ENT_TARGET_DURATION,
)

# ════════════════════════ 阶段一：筛选 ════════════════════════

SELECTION_PROMPT_ENT = """你是娱乐产业内容编辑。从下面这批娱乐资讯中，挑出今天最适合做深度故事讲述的 1 条。

选择标准（按优先级）：
1. 事件本身有足够丰富的细节和背景可挖掘
2. 背后有值得追溯的历史脉络（"这事以前发生过类似的吗？怎么演变的？"）
3. 涉及多个行业/领域的交叉影响（游戏/影视/动漫/技术/商业）
4. 能引发听众好奇心，有"想听下去"的钩子

排除：
- 纯粹的口水战、明星八卦
- 包含色情、暴力、危害国家安全等不良信息的内容
- 一句话就能说完的简短资讯
- 营销软文、公司 PR 稿

{history_hint}

输出严格的 JSON：
{{"selected_index": 资讯编号（0-based）, "reason": "为什么选这条（一句话）"}}"""  # noqa: E501


# ════════════════════════ 阶段二：故事化写稿 ════════════════════════

STORY_SCRIPT_PROMPT = """你是「伊恩娱乐深度谈」的专属文案编剧。

# 节目定位
一个每日更新的娱乐产业深度播客。每天只讲 1 个事件，但把它讲透——
不只是"发生了什么"，更要追溯它的来龙去脉、前世今生。

# 主持人人设
- 像一个见识广、读过很多书的朋友在咖啡馆和你聊天
- 能把复杂的事情讲得清晰有趣
- 不端着、不说教、不装专业
- 偶尔会心一笑，但不是刻意搞笑
- 语速从容，不赶时间

# 写作风格
- 第一人称用「我」，称呼听众为「你」
- 像在讲一个引人入胜的故事，不是念新闻稿
- 多用具体细节、数字、场景描写
- 可以引用当事人原话、媒体报道原文
- 口语化但信息密度不低，不要空洞的套话

# 口播绝对禁止
- 涉及色情、暴力、危害国家安全等不良信息
- "我认为""我觉得""个人认为"等主观判断句式
- "这意味着""值得关注的是""不可否认"等说教句式
- "金句来了""总结一下""划重点"等元标签
- 网络流行语（"绝了""yyds""你品你细品"）
- markdown 符号（** # `）
- 任何政治立场或价值判断

# 内容结构（共 {word_count} 字，朗读约 {duration_min} 分钟）

## 1. 钩子开场（10%，约 {hook_words} 字）
用一个具体的场景、一个惊人的数字、或一个有趣的细节切入。
让听众第一秒就想知道"后来呢？"
禁止："今天我们来聊聊""欢迎大家收听""据报道"

## 2. 事件还原（30%，约 {event_words} 字）
完整讲述这件事的来龙去脉。
谁在什么时间做了什么？关键转折点是什么？
多用原文中的具体细节和数据。

## 3. 历史回响（35%，约 {history_words} 字）
追溯这件事的历史脉络。
以前发生过类似的事吗？当时是什么情况？后来怎么样了？
这个行业/领域是怎么一步步走到今天的？
这一部分是节目的灵魂——最能体现"深度"。

## 4. 余韵（25%，约 {ending_words} 字）
这件事之后可能会怎么发展？不同的人是怎么看的？
引用各方观点，但不做自己的判断。
用开放式的收尾，让听众听完有自己的思考。
不要"明天见""下期再见"等轻浮措辞——安静地结束就好。

# 输出格式（严格 JSON）
{{
  "title": "本期标题（故事化，8-15字，有诱惑力，像一本书的章节名）",
  "opening": "开场白：'你好，我是伊恩。' 一句简短招呼后直接进入故事。自然、松弛，不超过 30 秒。",
  "script": "完整口播文案。直接可朗读的口语文本，无任何 markdown，无任何元标签。{word_count} 字左右。",
  "summary": "文字阅读版摘要（200-350字，书面语）",
  "chapters": ["章节1标题", "章节2标题", "章节3标题"],
  "keywords": ["关键词", "关键词", "关键词"],
  "source": "来源",
  "source_link": "原文链接URL"
}}"""  # noqa: E501


def generate_ent_script(articles: list[dict]) -> dict:
    """娱乐深度谈脚本生成：筛选 1 条 → 故事化深度写稿"""
    from article_enricher import enrich_articles

    # 阶段 1：选 1 条
    print("  🔎 阶段 1：从娱乐资讯中挑选今日故事...")
    history_titles = _load_ent_history_titles()
    history_hint = ""
    if history_titles:
        history_hint = "近期已报道过：\n" + "\n".join(f"- {t}" for t in history_titles[-10:])

    formatted = []
    for i, a in enumerate(articles):
        formatted.append(f"[{i}] {a['title']}  (来源: {a['source']}, {a['summary'][:80]})")

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat", max_tokens=512,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SELECTION_PROMPT_ENT.format(history_hint=history_hint)},
                {"role": "user", "content": "候选资讯：\n\n" + "\n".join(formatted)},
            ],
        )
        data = _parse_json(resp.choices[0].message.content)
        idx = data.get("selected_index", 0)
    except Exception as e:
        print(f"     ⚠️ 筛选失败: {e}，取第一条")
        idx = 0

    selected = articles[min(idx, len(articles) - 1)]
    print(f"  ✓ 选中: {selected['title'][:50]}")

    # 阶段 1.5：抓原文
    print("\n  📖 抓取原文全文...")
    try:
        enrich_articles([selected])
    except Exception as e:
        import traceback
        print(f"     ⚠️ 抓取异常: {e}")
        traceback.print_exc()
        selected.setdefault("full_body", selected.get("summary", ""))

    # 阶段 2：故事化写稿
    print("\n  ✍️ 阶段 2：DeepSeek 写故事化深度稿...")
    word_count = ENT_TARGET_DURATION * 4  # 中文 ~4 字/秒，20min = 4800 字
    duration_min = ENT_TARGET_DURATION // 60
    hook_words = int(word_count * 0.10)
    event_words = int(word_count * 0.30)
    history_words = int(word_count * 0.35)
    ending_words = int(word_count * 0.25)

    prompt = STORY_SCRIPT_PROMPT.format(
        word_count=word_count,
        duration_min=duration_min,
        hook_words=hook_words,
        event_words=event_words,
        history_words=history_words,
        ending_words=ending_words,
    )

    body = selected.get("full_body", "") or selected.get("summary", "")
    user_text = f"""今日事件：
标题: {selected['title']}
来源: {selected['source']}
链接: {selected['link']}

【原文/背景资料】
{body[:5000]}"""

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat", max_tokens=16384,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_text},
            ],
        )
        script = _parse_json(resp.choices[0].message.content)
    except Exception as e:
        import traceback
        print(f"  ❌ 脚本生成失败: {e}")
        traceback.print_exc()
        raise RuntimeError(f"DeepSeek 脚本生成失败: {e}")

    # Fill missing fields
    script.setdefault("source", selected.get("source", ""))
    script.setdefault("source_link", selected.get("link", ""))
    script.setdefault("image_url", selected.get("image_url"))
    script.setdefault("chapters", [])
    script.setdefault("keywords", [])

    return script


def _load_ent_history_titles() -> list[str]:
    titles = []
    pattern = os.path.join(ENT_OUTPUT_DIR, "script_ent_*.json")
    for fp in sorted(glob.glob(pattern))[-10:]:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            titles.append(data.get("title", ""))
        except Exception:
            continue
    return titles


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = [l for l in text.split("\n") if not l.strip().startswith("```")]
        text = "\n".join(lines)
    start, end = text.find("{"), text.rfind("}") + 1
    candidate = text[start:end] if (start != -1 and end > start) else text
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        try:
            from json_repair import repair_json
            repaired = repair_json(candidate, return_objects=True)
            if isinstance(repaired, dict) and repaired:
                return repaired
        except Exception:
            pass
        raise ValueError(f"无法解析 JSON:\n{candidate[:300]}")
