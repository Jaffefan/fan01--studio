"""资讯抓取模块：从多个 RSS 源抓取最新 AI 资讯"""

import sys
import io
import re

# 修复 Windows 终端 GBK 编码无法输出 emoji 的问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import feedparser
from datetime import datetime, timezone, timedelta
from config import RSS_FEEDS, MAX_ARTICLES_PER_FEED


def fetch_all(only_today: bool = True) -> list[dict]:
    """
    从 RSS 源 + 社交平台（Hacker News / Reddit / GitHub）抓取文章。
    返回去重合并后的文章列表，交给 script_generator 选 Top 5。
    """
    all_articles = []

    # --- RSS 源 ---
    print("📡 抓取 RSS 资讯...\n")
    for feed_config in RSS_FEEDS:
        try:
            items = _fetch_single_feed(feed_config)
            all_articles.extend(items)
            print(f"  ✓ {feed_config['name']}: 获取到 {len(items)} 篇文章")
        except Exception as e:
            print(f"  ✗ {feed_config['name']}: 抓取失败 - {e}")

    # 过滤今天的 RSS 资讯
    if only_today:
        today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
        before_count = len(all_articles)
        all_articles = [a for a in all_articles if a["date"] == today]
        print(f"\n📅 过滤当天 RSS 资讯: {before_count} → {len(all_articles)} 篇")

    # --- 社交平台源（last30days）---
    print()
    try:
        from fetcher_social import fetch_social
        social_articles = fetch_social(only_today=only_today)
        all_articles.extend(social_articles)
    except Exception as e:
        print(f"  ⚠️ 社交平台抓取失败（跳过）: {e}")

    # 全局去重 + 按时间排序
    all_articles = _deduplicate(all_articles)
    all_articles.sort(key=lambda x: x["published"], reverse=True)

    print(f"\n📋 共 {len(all_articles)} 篇待筛选资讯（RSS + 社交平台合并）")
    return all_articles


def _fetch_single_feed(feed_config: dict) -> list[dict]:
    """抓取单个 RSS 源"""
    feed = feedparser.parse(feed_config["url"])

    articles = []
    for entry in feed.entries[:MAX_ARTICLES_PER_FEED]:
        published_iso = _parse_time(entry)
        date_str = published_iso[:10]  # YYYY-MM-DD

        summary_html = entry.get("summary", "") or entry.get("description", "")
        summary = _strip_html(summary_html)
        image_url = _extract_image(entry, summary_html)

        articles.append({
            "title": entry.get("title", "无标题"),
            "summary": summary[:500],
            "link": entry.get("link", ""),
            "published": published_iso,
            "date": date_str,
            "source": feed_config["name"],
            "lang": feed_config["lang"],
            "image_url": image_url,
        })

    return articles


def _extract_image(entry, summary_html: str) -> str | None:
    """从 RSS 条目中提取图片 URL"""
    # 1) media_thumbnail
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        url = entry.media_thumbnail[0].get("url")
        if url:
            return url
    # 2) media_content
    if hasattr(entry, "media_content") and entry.media_content:
        url = entry.media_content[0].get("url")
        if url:
            return url
    # 3) enclosures
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image"):
                return enc.get("href") or enc.get("url")
    # 4) 从 summary HTML 中找第一个 <img>
    if summary_html:
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary_html)
        if match:
            return match.group(1)
    return None


def _deduplicate(articles: list[dict]) -> list[dict]:
    """按标题去重"""
    seen = set()
    unique = []
    for a in articles:
        key = re.sub(r"\s+", "", a["title"])[:15]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique


def _parse_time(entry) -> str:
    """解析 RSS 条目的发布时间"""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        return dt.isoformat()
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        return dt.isoformat()
    return datetime.now(timezone.utc).isoformat()


def _strip_html(text: str) -> str:
    """去除 HTML 标签"""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


if __name__ == "__main__":
    print("正在抓取 AI 资讯...\n")
    articles = fetch_all(only_today=False)
    print("\n--- 最新 10 条 ---")
    for i, a in enumerate(articles[:10], 1):
        print(f"  {i}. [{a['source']}] {a['title']}")
        print(f"     {a['summary'][:60]}...")
        print()
