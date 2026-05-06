"""社交平台资讯抓取模块：使用 last30days 从 Hacker News、Reddit 等平台获取 AI 资讯"""

import sys
import json
import subprocess
import re
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# last30days 脚本路径：优先使用 vendor 进项目的版本（CI 友好），回退到本地 ~/.claude
_PROJECT_VENDOR = Path(__file__).parent / "last30days_vendor" / "scripts" / "last30days.py"
_LOCAL_SKILL = Path.home() / ".claude" / "skills" / "last30days" / "scripts" / "last30days.py"
LAST30DAYS_SCRIPT = _PROJECT_VENDOR if _PROJECT_VENDOR.exists() else _LOCAL_SKILL

# 免费可用的源（无需 API key）
FREE_SOURCES = "hackernews,reddit,github"

# 搜索话题
SEARCH_TOPICS = [
    "artificial intelligence AI LLM",
    "GPT Claude Gemini model release",
    "AI agent automation",
]


def fetch_social(only_today: bool = True) -> list[dict]:
    """从 Hacker News、Reddit、GitHub 抓取 AI 资讯"""
    all_articles = []

    print("🌐 抓取社交平台资讯 (last30days)...\n")

    for topic in SEARCH_TOPICS:
        try:
            items = _run_last30days(topic)
            all_articles.extend(items)
            print(f"  ✓ 话题「{topic[:30]}」: 获取到 {len(items)} 条")
        except Exception as e:
            print(f"  ✗ 话题「{topic[:30]}」: 失败 - {e}")

    # 过滤今天 / 近期的（社交平台时间戳不稳定，宽松过滤）
    if only_today:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        yesterday = (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
                     .strftime("%Y-%m-%d"))
        all_articles = [
            a for a in all_articles
            if a["date"] >= yesterday  # 保留昨天+今天（时区容差）
        ]

    # 去重
    all_articles = _deduplicate(all_articles)

    # 按互动量排序（Hacker News 点数、Reddit 上票数等）
    all_articles.sort(key=lambda x: x.get("engagement", 0), reverse=True)

    print(f"\n  共获取 {len(all_articles)} 条社交平台资讯")
    return all_articles


def _run_last30days(topic: str) -> list[dict]:
    """调用 last30days.py 搜索并解析 JSON 输出"""
    result = subprocess.run(
        [
            sys.executable,
            str(LAST30DAYS_SCRIPT),
            topic,
            "--emit=json",
            f"--search={FREE_SOURCES}",
            "--quick",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr[:300])

    # 找到 JSON 块（stdout 可能混有进度信息）
    stdout = result.stdout.strip()
    # 尝试直接解析
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        # 从输出中提取第一个完整 JSON 对象
        match = re.search(r'\{[\s\S]+\}', stdout)
        if not match:
            raise RuntimeError("last30days 输出中未找到 JSON")
        data = json.loads(match.group())

    return _parse_report(data)


def _parse_report(data: dict) -> list[dict]:
    """将 last30days JSON Report 转换为标准文章格式"""
    articles = []
    seen_urls = set()

    # 优先用 ranked_candidates（已排序），不够则补 items_by_source
    ranked = data.get("ranked_candidates", [])
    raw_items = []
    for src_items in data.get("items_by_source", {}).values():
        raw_items.extend(src_items)

    # ranked_candidates 里只有 id/score，需配合 items_by_source 拿详情
    # 直接用 items_by_source，按 engagement_score 排序
    raw_items.sort(key=lambda x: x.get("engagement_score") or 0, reverse=True)

    for item in raw_items:
        title = (item.get("title") or "").strip()
        url = item.get("url", "")
        if not title or not url or url in seen_urls:
            continue
        seen_urls.add(url)

        snippet = item.get("snippet") or item.get("body") or ""
        source_name = item.get("source", "social")
        engagement = 0
        eng = item.get("engagement")
        if isinstance(eng, dict):
            engagement = eng.get("score") or eng.get("points") or eng.get("upvotes") or 0
        elif isinstance(eng, (int, float)):
            engagement = eng

        published_at = item.get("published_at") or datetime.now(timezone.utc).isoformat()
        date_str = published_at[:10]

        # 从 metadata 里找图片（Reddit 有 thumbnail，HN 通常没有）
        image_url = None
        meta = item.get("metadata") or {}
        for key in ("thumbnail", "preview_url", "image_url", "image", "og_image"):
            val = meta.get(key)
            if val and isinstance(val, str) and val.startswith("http"):
                image_url = val
                break

        # 抽取热门评论（Reddit/HN 在 metadata 中可能含 comments / top_comments）
        top_comments = _extract_top_comments(meta)

        articles.append({
            "title": title,
            "summary": snippet[:500],
            "link": url,
            "published": published_at,
            "date": date_str,
            "source": _source_label(source_name),
            "lang": "en",
            "engagement": engagement,
            "score": item.get("local_rank_score") or 0,
            "image_url": image_url,
            "top_comments": top_comments,
        })

    return articles


def _extract_top_comments(meta: dict) -> list[str]:
    """从 last30days metadata 抽取最多 5 条高赞评论文本"""
    comments_raw = (
        meta.get("comments")
        or meta.get("top_comments")
        or meta.get("replies")
        or []
    )
    if not isinstance(comments_raw, list):
        return []
    out = []
    for c in comments_raw[:8]:
        if isinstance(c, str):
            text = c
        elif isinstance(c, dict):
            text = c.get("text") or c.get("body") or c.get("content") or ""
        else:
            text = ""
        text = (text or "").strip()
        if text and len(text) > 10:
            out.append(text[:300])
        if len(out) >= 5:
            break
    return out


def _source_label(source: str) -> str:
    mapping = {
        "hackernews": "Hacker News",
        "reddit": "Reddit",
        "github": "GitHub",
        "bluesky": "Bluesky",
    }
    return mapping.get(source.lower(), source.capitalize())


def _deduplicate(articles: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for a in articles:
        key = re.sub(r"\s+", "", a["title"])[:20]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique


if __name__ == "__main__":
    articles = fetch_social(only_today=False)
    print(f"\n--- Top 10 社交平台资讯 ---")
    for i, a in enumerate(articles[:10], 1):
        print(f"  {i}. [{a['source']}] {a['title']}")
        print(f"     互动: {a.get('engagement', 0)}  |  {a['summary'][:60]}...")
        print()
